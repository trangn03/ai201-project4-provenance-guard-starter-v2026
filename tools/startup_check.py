"""
Does preloading the libraries (the 9.2 fix) help, and what does it cost?

    python tools/startup_check.py              3 trials, about 10 minutes
    python tools/startup_check.py --trials 2

The before and after runs of the criteria happen at different times on a laptop
whose speed varies, so they cannot isolate one change. This can: it flips the
AI201_PRELOAD switch (config.PRELOAD_LIBRARIES) in the same session, alternating
off and on each trial so drift hits both equally, and measures four things:

  start-up, healthy server     seconds from launch until /health answers
  first request, healthy       the first normal request after launch (cold start)
  start-up, broken-model       seconds until /health answers with the model unable to load
  first request, broken-model  the first degraded request, which is what 9.2 measures

Every request is under a creator_id starting `startup_`. Output is also written to
results/startup_check.md.
"""
import argparse
import os
import statistics
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))    # the project root

import config
from measure_cost import listener_pid, stop
from scenarios import CLEARLY_AI, CLEARLY_HUMAN

sys.stdout.reconfigure(errors="replace")

PORT = 5008


def server(extra_env):
    env = dict(os.environ, PORT=str(PORT), AI201_DEBUG="0", PYTHONIOENCODING="utf-8", **extra_env)
    proc = subprocess.Popen([sys.executable, "app.py"], env=env, cwd=str(config.ROOT),
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = f"http://127.0.0.1:{PORT}"
    began = time.perf_counter()
    for _ in range(300):
        try:
            if requests.get(f"{url}/health", timeout=2).status_code == 200:
                return proc, url, time.perf_counter() - began
        except requests.RequestException:
            time.sleep(0.5)
    proc.kill()
    raise SystemExit("server did not come up")


def timed(url, text, creator):
    began = time.perf_counter()
    resp = requests.post(f"{url}/submit", json={"text": text, "creator_id": creator}, timeout=300)
    assert resp.status_code == 200, resp.text[:200]
    return time.perf_counter() - began


def one(flag, trial):
    row = {"flag": flag, "trial": trial}
    proc, url, up = server({"AI201_PRELOAD": flag, "AI201_DETECTOR_MODEL": "does-not-exist-xyz"})
    try:
        row["up_broken"] = up
        row["first_degraded"] = timed(url, CLEARLY_AI, f"startup_{flag}_t{trial}_deg1")
        row["second_degraded"] = timed(url, CLEARLY_HUMAN, f"startup_{flag}_t{trial}_deg2")
    finally:
        stop(proc, PORT)
    proc, url, up = server({"AI201_PRELOAD": flag})
    try:
        row["up_healthy"] = up
        row["first_normal"] = timed(url, CLEARLY_HUMAN, f"startup_{flag}_t{trial}_norm1")
        row["second_normal"] = timed(url, CLEARLY_AI, f"startup_{flag}_t{trial}_norm2")
    finally:
        stop(proc, PORT)
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--trials", type=int, default=3)
    args = parser.parse_args()
    if listener_pid(PORT):
        raise SystemExit(f"port {PORT} is in use")

    rows = []
    for trial in range(1, args.trials + 1):
        for flag in ("0", "1"):
            rows.append(one(flag, trial))
            r = rows[-1]
            print(f"trial {trial} preload={'on ' if flag == '1' else 'off'}: "
                  f"broken-model start-up {r['up_broken']:.1f}s, first degraded {r['first_degraded']:.1f}s, "
                  f"second {r['second_degraded']:.1f}s | healthy start-up {r['up_healthy']:.1f}s, "
                  f"first normal {r['first_normal']:.1f}s, second {r['second_normal']:.1f}s", flush=True)

    keys = [("up_healthy", "Start-up, healthy (s)"), ("first_normal", "First normal request (s)"),
            ("up_broken", "Start-up, model broken (s)"), ("first_degraded", "First degraded request (s)"),
            ("second_degraded", "Second degraded request (s)"), ("second_normal", "Second normal request (s)")]
    lines = [f"# Preload on or off, same session - {datetime.now():%Y-%m-%d %H:%M}", "",
             f"`python tools/startup_check.py --trials {args.trials}`: trials alternate off and on, "
             f"each with a fresh server for the broken-model case and another for the healthy case. "
             f"Times are client-side wall clock.", "",
             "| Measure | Preload off (each trial) | Off mean | Preload on (each trial) | On mean |",
             "|---|---|---|---|---|"]
    for key, name in keys:
        off = [r[key] for r in rows if r["flag"] == "0"]
        on = [r[key] for r in rows if r["flag"] == "1"]
        lines.append(f"| {name} | {', '.join(f'{x:.1f}' for x in off)} | **{statistics.mean(off):.1f}** | "
                     f"{', '.join(f'{x:.1f}' for x in on)} | **{statistics.mean(on):.1f}** |")
    text = "\n".join(lines) + "\n"
    (config.RESULTS_DIR / "startup_check.md").write_text(text, encoding="utf-8")
    print("\n" + text)


if __name__ == "__main__":
    main()
