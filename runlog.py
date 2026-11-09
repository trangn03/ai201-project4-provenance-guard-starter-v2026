"""
Structured run log: one JSON line per /submit request, in logs/runs.jsonl.

    python runlog.py              the last 15 runs, as a table
    python runlog.py --last 40    more of them
    python runlog.py --failures   only runs that did not end in a plain decision
    python runlog.py --json       the raw records, one per line

This is separate from the audit log on purpose. audit.jsonl is the record of
decisions and appeals, with a fixed nine-field shape other tooling reads. This
file is the record of RUNS: every request that reached /submit, including the
ones that never became a decision, with what came in, what went out, how long
each stage took, and which settings produced the answer. It is written even
when the route crashes, because a failure that shows up only as an absence is
one nobody finds.

Every record has the same named fields:

    timestamp      UTC, to the millisecond
    run_id         unique to this request
    content_id     the audit-log id when a decision was made, else null
    route, status_code
    outcome        decided | degraded | rejected | rate_limited | error
    creator_id
    input          {type, chars, words, preview}  (preview is cut to
                   config.RUN_LOG_INPUT_CHARS characters)
    output         {status_code, guess, confidence, label, error, message}
    duration_ms    the whole request, wall clock
    cpu_ms         CPU time the process used during the request (can exceed
                   duration_ms: torch uses several cores)
    model_ms       time inside signal one (null if it never ran)
    style_ms       time inside signal two (null if it never ran)
    cold_start     true if the model was not yet loaded when this run began
    model_score, style_score, combined_score
    degraded, degraded_reason
    exception      null, or {type, message, traceback} for an unhandled crash
    config         the settings that produced this answer: detector model,
                   thresholds and weights, so a later run can be compared
"""
import argparse
import json
import logging
import sys
import threading
import uuid
from datetime import datetime, timezone

import config

_lock = threading.Lock()
_log = logging.getLogger("provenance.runlog")

FAILURE_OUTCOMES = ("degraded", "rejected", "rate_limited", "error")


def path():
    """Read from config at call time so a test can point LOG_DIR elsewhere."""
    return config.LOG_DIR / config.RUN_LOG_NAME


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _describe_input(text):
    if isinstance(text, str):
        limit = config.RUN_LOG_INPUT_CHARS
        return {
            "type": "str",
            "chars": len(text),
            "words": len(text.split()),
            "preview": text[:limit],
        }
    # Missing, null, a number, a list: the type is the useful fact.
    return {"type": "missing" if text is None else type(text).__name__,
            "chars": None, "words": None, "preview": None}


def _outcome(status_code: int, body: dict) -> str:
    if status_code == 429:
        return "rate_limited"
    if status_code >= 500:
        return "error"
    if status_code >= 400:
        return "rejected"
    return "degraded" if body.get("degraded") else "decided"


def build_record(payload, status_code, body, extra, duration_ms, exc=None, trace=None) -> dict:
    """
    Assemble one record. Pure, so it can be tested without a request.

    `payload` is the parsed request body (anything, or None), `body` the JSON
    the route answered with (a dict, possibly empty), `extra` what the route
    noted along the way (stage timings, combined score, degraded reason).
    """
    payload = payload if isinstance(payload, dict) else {}
    body = body if isinstance(body, dict) else {}
    extra = extra or {}
    creator = payload.get("creator_id")

    exception = None
    if exc is not None:
        exception = {"type": type(exc).__name__, "message": str(exc)[:500],
                     "traceback": (trace or "")[-2000:]}

    return {
        "timestamp": _now(),
        "run_id": uuid.uuid4().hex,
        "content_id": body.get("content_id"),
        "route": "/submit",
        "status_code": status_code,
        "outcome": _outcome(status_code, body),
        "creator_id": creator if isinstance(creator, str) else None,
        "input": _describe_input(payload.get("text")),
        "output": {
            "status_code": status_code,
            "guess": body.get("guess"),
            "confidence": body.get("confidence"),
            "label": body.get("label"),
            "error": body.get("error"),
            "message": body.get("message"),
        },
        "duration_ms": None if duration_ms is None else round(duration_ms, 1),
        "cpu_ms": extra.get("cpu_ms"),
        "model_ms": extra.get("model_ms"),
        "style_ms": extra.get("style_ms"),
        "cold_start": extra.get("cold_start"),
        "model_score": body.get("model_score"),
        "style_score": body.get("style_score"),
        "combined_score": extra.get("combined_score"),
        "degraded": bool(body.get("degraded")),
        "degraded_reason": extra.get("degraded_reason"),
        "exception": exception,
        "config": {
            "detector_model": config.DETECTOR_MODEL,
            "human_threshold": config.HUMAN_THRESHOLD,
            "ai_threshold": config.AI_THRESHOLD,
            "weight_model": config.WEIGHT_MODEL_SIGNAL,
            "weight_style": config.WEIGHT_STYLE_SIGNAL,
        },
    }


def write(record: dict) -> bool:
    """
    Append one record. Never raises: a logging problem must not turn a good
    answer into a 500. If the write fails it is reported through `logging`
    (to stderr) and this returns False, so the failure is loud, not silent.
    """
    try:
        line = json.dumps(record, ensure_ascii=False, default=str)
        config.LOG_DIR.mkdir(parents=True, exist_ok=True)
        with _lock:
            with path().open("a", encoding="utf-8") as f:
                f.write(line + "\n")
        return True
    except Exception:  # noqa: BLE001 - see docstring
        _log.exception("could not write run record to %s", path())
        return False


def read(limit: int | None = None) -> list[dict]:
    """Read the log back, oldest first. A malformed line is skipped, not fatal."""
    p = path()
    if not p.exists():
        return []
    records = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records[-limit:] if limit else records


def _table(records: list[dict]) -> str:
    head = f"{'time (UTC)':<19} {'status':>6} {'outcome':<12} {'ms':>7} {'model':>7} {'style':>6}  input / why"
    rows = [head, "-" * len(head)]
    for r in records:
        out = r.get("output") or {}
        what = ((r.get("input") or {}).get("preview") or "").replace("\n", " ")[:34]
        why = r.get("outcome") != "decided"
        if r.get("exception"):
            what = f"{r['exception']['type']}: {r['exception']['message']}"[:60]
        elif r.get("degraded_reason"):
            what = r["degraded_reason"][:60]
        elif why and (out.get("message") or out.get("error")):
            what = (out.get("message") or out.get("error"))[:60]
        fmt = lambda v: "-" if v is None else f"{v:.0f}"
        rows.append(
            f"{(r.get('timestamp') or '')[:19].replace('T', ' '):<19} "
            f"{r.get('status_code', ''):>6} {r.get('outcome', ''):<12} "
            f"{fmt(r.get('duration_ms')):>7} {fmt(r.get('model_ms')):>7} "
            f"{fmt(r.get('style_ms')):>6}  {what}"
        )
    return "\n".join(rows)


def main():
    sys.stdout.reconfigure(errors="replace")
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--last", type=int, default=15)
    parser.add_argument("--failures", action="store_true",
                        help="only runs that did not end in a plain decision")
    parser.add_argument("--json", action="store_true", help="raw records")
    args = parser.parse_args()

    records = read()
    if args.failures:
        records = [r for r in records if r.get("outcome") in FAILURE_OUTCOMES]
    records = records[-args.last:]
    if not records:
        print(f"No runs in {path()} yet." if not path().exists() else "No matching runs.")
        return
    if args.json:
        for r in records:
            print(json.dumps(r, ensure_ascii=False))
    else:
        print(_table(records))
        print(f"\n{len(records)} shown from {path()}")


if __name__ == "__main__":
    main()
