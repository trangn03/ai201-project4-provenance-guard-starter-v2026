"""
Send one short, varied session through the real service, so logs/runs.jsonl
holds an example of every kind of outcome with real numbers behind it.

    python tools/demo_session.py

It starts its own server twice on a spare port (debug off) and stops both:

  1. Normally, with the model working. First request is a cold start. Then a
     human-sounding text, an AI-sounding text, a plain text that lands in the
     unsure band, four kinds of bad input, and eight quick requests from one
     creator_id, which is enough to hit the rate limit.
  2. With the model deliberately unable to load (AI201_DETECTOR_MODEL set to a
     name that does not exist), then two requests that come back degraded.

Every request uses a creator_id starting `demo_`, so the records can be pulled
out of the log afterwards:

    python runlog.py --json | grep '"creator_id": "demo_'

What it cannot show is a crash of the route itself: there is no honest way to
make the live service raise an unhandled error without changing its code. That
path is covered by tests/test_runlog.py instead.
"""
import os
import subprocess
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))    # the project root

import config
from measure_cost import listener_pid, stop
from scenarios import CLEARLY_AI, CLEARLY_HUMAN, PLAIN_HUMAN

sys.stdout.reconfigure(errors="replace")

PORT = 5003
URL = f"http://127.0.0.1:{PORT}"
SHORT = "We missed the last train, so we walked home along the canal."


def start(extra_env=None):
    env = dict(os.environ, PORT=str(PORT), AI201_DEBUG="0", **(extra_env or {}))
    proc = subprocess.Popen([sys.executable, "app.py"], env=env, cwd=str(config.ROOT),
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(120):
        try:
            if requests.get(f"{URL}/health", timeout=2).status_code == 200:
                return proc
        except requests.RequestException:
            time.sleep(0.5)
    proc.kill()
    raise SystemExit("server did not come up")


def send(label, body):
    t0 = time.perf_counter()
    resp = requests.post(f"{URL}/submit", json=body, timeout=180)
    print(f"  {label:<34} -> {resp.status_code}  ({time.perf_counter() - t0:.1f}s)")
    return resp


def main():
    if listener_pid(PORT):
        raise SystemExit(f"port {PORT} is in use")

    print("Session 1: model working")
    proc = start()
    try:
        send("first request (cold start)", {"text": CLEARLY_HUMAN, "creator_id": "demo_cold_human"})
        send("AI-sounding text", {"text": CLEARLY_AI, "creator_id": "demo_ai"})
        send("plain text (unsure band)", {"text": PLAIN_HUMAN, "creator_id": "demo_plain"})
        send("empty text", {"text": "", "creator_id": "demo_empty"})
        send("too short", {"text": "hi there", "creator_id": "demo_short"})
        send("control character", {"text": "Hello there\x07 this has a bell inside it.", "creator_id": "demo_control"})
        send("text field missing", {"creator_id": "demo_missing"})
        send("body is a list, not an object", ["not", "an", "object"])
        for i in range(8):
            send(f"burst {i + 1}/8, one creator_id", {"text": SHORT, "creator_id": "demo_burst"})
    finally:
        stop(proc, PORT)

    print("Session 2: model unable to load")
    proc = start({"AI201_DETECTOR_MODEL": "does-not-exist-xyz"})
    try:
        send("AI-sounding text, no model", {"text": CLEARLY_AI, "creator_id": "demo_degraded_ai"})
        send("human-sounding text, no model", {"text": CLEARLY_HUMAN, "creator_id": "demo_degraded_human"})
    finally:
        stop(proc, PORT)
    print("Done. See: python runlog.py --last 20")


if __name__ == "__main__":
    main()
