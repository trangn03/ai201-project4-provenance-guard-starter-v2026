"""
Criterion 9.1: does every kind of failure leave exactly one run record, with a
reason?

    python tools/failure_check.py

It triggers nine kinds of failing request on purpose and, after each, counts
the records that appeared in the run log:

    empty text, text too short, a control character, `text` missing, a body that
    is not a JSON object, text over the size limit, a rate-limited request,
    a model that cannot load, and a crash inside the route.

Six are real bad inputs, and the rate limit is a real burst past the limiter.
The other two cannot be made to happen on a healthy service without changing
its code, so they are injected: signal one is replaced by a function that
raises, and signal two is replaced by one that raises an unhandled error. The
crash is raised with Flask's PROPAGATE_EXCEPTIONS on, which is how debug mode
behaves and the case where `after_request` would never run.

It runs the real app through Flask's test client, with the model replaced by a
stub for the kinds that do not test it (so nothing here loads gpt2) and the logs
pointed at a temp directory (so injected failures do not enter your real
logs/runs.jsonl). The records it prints are exactly what runlog.write wrote.

tests/test_runlog.py runs the same exercise as a unit test.
"""
import json
import sys
import tempfile
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))    # the project root

import app as app_module
import config
import runlog

sys.stdout.reconfigure(errors="replace")

TEXT = "We missed the last train, so we walked home along the canal."
KINDS = 9


def _reason(record):
    out = record["output"]
    return (out["message"] or record["degraded_reason"]
            or (record["exception"] or {}).get("message") or "")


def exercise(client):
    """
    Trigger the nine kinds and return one dict per kind:
    {kind, ok, problem, status, record}. The caller must already have pointed
    config.LOG_DIR / config.AUDIT_LOG somewhere disposable.
    """
    limiter = app_module.limiter
    limiter_was = getattr(limiter, "enabled", None)
    counter = [0]

    def who():
        counter[0] += 1
        return f"failure_check_{counter[0]}"

    def post(body):
        return lambda: client.post("/submit", json=body)

    def submit(text=TEXT, creator=None):
        return client.post("/submit", json={"text": text, "creator_id": creator or who()})

    def model_cannot_load():
        with mock.patch("detector.model_signal", side_effect=RuntimeError("model could not be loaded")):
            return submit()

    def crash_in_route():
        with mock.patch.dict(app_module.app.config, {"PROPAGATE_EXCEPTIONS": True}):
            with mock.patch("stylometry.style_signal", side_effect=RuntimeError("unhandled error in the route")):
                try:
                    submit()
                except RuntimeError:
                    pass        # propagated out of Flask, as in debug mode; the record must still exist

    def burst_prep():
        limiter.enabled = True
        for _ in range(config.RATE_LIMIT_PER_MINUTE):
            submit(creator="failure_check_rate")    # the ones the limiter allows

    kinds = [
        ("empty text", None, post({"text": "", "creator_id": "failure_check_a"})),
        ("text too short", None, post({"text": "hi there", "creator_id": "failure_check_b"})),
        ("control character", None, post({"text": "Hello there\x07 this has a bell in it.", "creator_id": "failure_check_c"})),
        ("text missing", None, post({"creator_id": "failure_check_d"})),
        ("body not a JSON object", None, post(["not", "an", "object"])),
        ("text over the size limit", None, lambda: submit("word " * 5000)),
        ("rate limited", burst_prep, lambda: submit(creator="failure_check_rate")),
        ("model cannot load", None, model_cannot_load),
        ("crash inside the route", None, crash_in_route),
    ]

    results = []
    try:
        for name, prep, send in kinds:
            if prep:
                prep()
            before = len(runlog.read())
            send()
            fresh = runlog.read()[before:]
            problem = None
            if len(fresh) != 1:
                problem = f"{len(fresh)} records, wanted exactly 1"
            elif not _reason(fresh[0]):
                problem = "record has no reason"
            elif fresh[0]["outcome"] == "decided":
                problem = "recorded as a plain decision"
            results.append({"kind": name, "ok": problem is None, "problem": problem,
                            "status": fresh[0]["status_code"] if fresh else None,
                            "record": fresh[0] if len(fresh) == 1 else None})
    finally:
        if limiter_was is not None:
            limiter.enabled = limiter_was
    return results


def main():
    app_module.app.logger.disabled = True
    with tempfile.TemporaryDirectory() as tmp:
        with mock.patch.object(config, "LOG_DIR", Path(tmp)), \
             mock.patch.object(config, "AUDIT_LOG", Path(tmp) / "audit.jsonl"), \
             mock.patch("detector.model_signal", return_value=0.5):
            results = exercise(app_module.app.test_client())

    print("kind                       status  outcome       reason")
    print("-" * 78)
    for r in results:
        rec = r["record"]
        outcome = rec["outcome"] if rec else "-"
        reason = (_reason(rec) if rec else r["problem"])[:34]
        print(f"{r['kind']:<26} {str(r['status']):>6}  {outcome:<12}  {reason}"
              f"{'' if r['ok'] else '   <-- ' + str(r['problem'])}")
    print()
    print("The records, as runlog.write wrote them:")
    for r in results:
        if r["record"]:
            print(json.dumps(r["record"], ensure_ascii=False))
    ok = sum(r["ok"] for r in results)
    print()
    print(f"RESULT kinds_ok={ok}/{KINDS}")
    sys.exit(0 if ok == KINDS else 1)


if __name__ == "__main__":
    main()
