"""
Shape B check: when signal one cannot run, does /submit still answer, never
accuse, and leave a log entry that says why?

scenarios.py can't express this: the service has to be STARTED with the model
broken (see DEGRADED_MODE.md), and the evidence is in the audit log as well as
the response. Service must be running:

    python tools/degraded_check.py --expect degraded [--trials 3]   # model broken
    python tools/degraded_check.py --expect normal   [--trials 3]   # model working

With --expect degraded, every submission must: return 200, say degraded=true
with model_score null, never come back guess "ai", carry a reduced confidence,
and have an audit entry with degraded=true and a reason. With --expect normal,
the same submissions must come back degraded=false with both scores present
and no degraded fields in the log, so the new path has not leaked into the
old one.
"""
import argparse
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))    # the project root, where config.py lives

import config
from scenarios import CLEARLY_AI, CLEARLY_HUMAN, PLAIN_HUMAN

sys.stdout.reconfigure(errors="replace")

TEXTS = [
    ("clearly AI", CLEARLY_AI),            # would be "ai" with both signals
    ("clearly human", CLEARLY_HUMAN),
    ("plain human", PLAIN_HUMAN),
    ("market", "I went to the market on Saturday and bought way too many peaches."),
    ("meeting", "The meeting ran long again. Nobody had read the notes beforehand."),
    ("bike", "My brother fixed the bike chain with a paperclip and a lot of swearing."),
    ("train", "We missed the last train, so we walked home along the canal."),
    ("soup", "The soup needed more salt, but everyone ate it anyway."),
    ("cat", "Our cat knocked the plant off the shelf for the third time this week."),
    ("letter", "I still have the first letter she sent me, folded in a drawer."),
]


def check_one(url, expect, trial, i, name, text):
    """Return a list of problems for one submission (empty means it passed)."""
    resp = requests.post(f"{url}/submit", json={
        "text": text, "creator_id": f"degraded_{expect}_t{trial}_{i}"}, timeout=120)
    if resp.status_code != 200:
        return [f"status {resp.status_code}, wanted 200"]
    body = resp.json()
    log = requests.get(f"{url}/log?limit=5000", timeout=30).json()["entries"]
    mine = [e for e in log if e.get("content_id") == body.get("content_id")]
    entry = mine[0] if len(mine) == 1 else None

    problems = []
    if entry is None:
        return [f"{len(mine)} audit entries for this content_id, wanted 1"]
    if expect == "degraded":
        if body.get("degraded") is not True:
            problems.append("response degraded is not true")
        if body.get("model_score") is not None:
            problems.append("model_score should be null")
        if body.get("guess") == "ai":
            problems.append("degraded answer accused the writer (guess 'ai')")
        if entry.get("degraded") is not True or not entry.get("degraded_reason"):
            problems.append("audit entry missing degraded flag or reason")
        if entry.get("model_score") is not None:
            problems.append("audit model_score should be null")
    else:
        if body.get("degraded") is not False:
            problems.append("response degraded is not false")
        if body.get("model_score") is None:
            problems.append("model_score missing")
        if "degraded" in entry or "degraded_reason" in entry:
            problems.append("normal audit entry carries degraded fields")
    return problems


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--expect", choices=["degraded", "normal"], required=True)
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument("--url", default=f"http://{config.HOST}:{config.PORT}")
    args = parser.parse_args()

    total_bad = 0
    for trial in range(1, args.trials + 1):
        ok = 0
        for i, (name, text) in enumerate(TEXTS, 1):
            problems = check_one(args.url, args.expect, trial, i, name, text)
            ok += not problems
            for p in problems:
                print(f"  trial {trial} #{i} ({name}): FAIL {p}")
        total_bad += len(TEXTS) - ok
        print(f"trial {trial}: {ok}/{len(TEXTS)} behaved as '{args.expect}'")
    sys.exit(1 if total_bad else 0)


if __name__ == "__main__":
    main()
