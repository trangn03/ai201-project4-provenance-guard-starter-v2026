"""
Criterion 9.3: do the two logs agree, under concurrent load?

    python tools/reconcile_check.py                  starts its own server
    python tools/reconcile_check.py --url http://127.0.0.1:5000   uses a running one

8 clients send 5 requests each, all at the same time: 3 valid texts and 2 bad
inputs (an empty text and a too-short one) per client, 40 in all, each client
under its own creator_id so the per-creator rate limit is not what is measured.
One extra request is sent first, uncounted, so the model's slow first load does
not sit inside the concurrent burst.

Afterwards it checks, against logs/runs.jsonl and logs/audit.jsonl:

  1. exactly 40 run records exist for the burst's creator_ids (not 39, not 41);
  2. every line of the run log is valid JSON, anywhere in the file;
  3. every request that became a decision has exactly one run record and one
     audit entry, and they agree on content_id, guess, model_score, style_score.

It ends with a line the orchestrator reads:  RESULT records=40/40 malformed=0 agree=24/24
"""
import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))    # the project root

import audit
import config
import runlog
from measure_cost import launch, stop
from scenarios import CLEARLY_AI, CLEARLY_HUMAN, PLAIN_HUMAN

sys.stdout.reconfigure(errors="replace")

CLIENTS = 8
PER_CLIENT = [CLEARLY_AI, "", CLEARLY_HUMAN, "hi there", PLAIN_HUMAN]    # 3 valid, 2 bad
EXPECTED = CLIENTS * len(PER_CLIENT)


def one_client(url, stamp, c):
    creator = f"recon_{stamp}_c{c}"
    out = []
    for text in PER_CLIENT:
        resp = requests.post(f"{url}/submit", json={"text": text, "creator_id": creator}, timeout=300)
        out.append({"creator": creator, "status": resp.status_code,
                    "content_id": resp.json().get("content_id")})
    return out


def run(url):
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    requests.post(f"{url}/submit", json={"text": CLEARLY_HUMAN, "creator_id": f"recon_{stamp}_warmup"}, timeout=300)

    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=CLIENTS) as pool:
        sent = [r for batch in pool.map(lambda c: one_client(url, stamp, c), range(CLIENTS)) for r in batch]
    print(f"sent {len(sent)} requests from {CLIENTS} clients at once in {time.perf_counter() - started:.1f}s; "
          f"statuses: {sorted({r['status'] for r in sent})}")
    time.sleep(2)    # the record is written after the response goes out; let the last ones land

    prefix = f"recon_{stamp}_c"
    records = [r for r in runlog.read() if (r.get("creator_id") or "").startswith(prefix)]
    malformed = 0
    for line in runlog.path().read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                json.loads(line)
            except json.JSONDecodeError:
                malformed += 1

    decided = [r for r in sent if r["status"] == 200]
    agree, problems, sample = 0, [], []
    for r in decided:
        runs = [x for x in records if x.get("content_id") == r["content_id"]]
        audits = audit.entries_for(r["content_id"])
        if len(runs) != 1 or len(audits) != 1:
            problems.append(f"{r['content_id']}: {len(runs)} run records, {len(audits)} audit entries")
            continue
        run_rec, aud = runs[0], audits[0]
        same = (aud["content_id"] == run_rec["content_id"]
                and aud["guess"] == run_rec["output"]["guess"]
                and aud["model_score"] == run_rec["model_score"]
                and aud["style_score"] == run_rec["style_score"])
        if same:
            agree += 1
            if len(sample) < 3:
                sample.append((run_rec, aud))
        else:
            problems.append(f"{r['content_id']}: run record and audit entry disagree")

    per_client = {}
    for rec in records:
        per_client[rec["creator_id"]] = per_client.get(rec["creator_id"], 0) + 1
    print(f"run records per client: {sorted(per_client.values())} (each should be {len(PER_CLIENT)})")
    for p in problems:
        print("PROBLEM", p)
    print()
    print("Three decisions, run record then audit entry, as written:")
    for run_rec, aud in sample:
        print(json.dumps(run_rec, ensure_ascii=False))
        print(json.dumps(aud, ensure_ascii=False))
        print()
    print(f"RESULT records={len(records)}/{EXPECTED} malformed={malformed} agree={agree}/{len(decided)}")
    return len(records) == EXPECTED and malformed == 0 and agree == len(decided) and not problems


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--url", help="use a running service instead of starting one")
    parser.add_argument("--port", type=int, default=5004)
    args = parser.parse_args()
    if args.url:
        ok = run(args.url)
    else:
        proc, url, _ = launch(args.port)
        try:
            ok = run(url)
        finally:
            stop(proc, args.port)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
