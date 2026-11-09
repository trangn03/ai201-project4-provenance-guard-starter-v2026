"""
Measure what one run costs.

This system calls no paid API and uses no tokens: signal one is a model that
runs on your own machine. So its real cost is compute, in three forms:

    wall time    seconds a writer waits (client round trip, and the server's
                 own duration_ms from the run log)
    CPU time     seconds of processor the run used (cpu_ms from the run log).
                 torch uses several cores, so this can exceed wall time
    memory       what the server process holds once the model is loaded

    python tools/measure_cost.py                      3 launches, 10 warm runs each
    python tools/measure_cost.py --runs 10 --launches 3 --port 5002
    python tools/measure_cost.py --distribution       re-read the last run from the run log
                                                      and add its spread to the report

How it measures, so the number can be checked and repeated:

  1. It starts its OWN server (python app.py, debug off so there is no reloader
     process) on a spare port, so the first request really is a cold start.
  2. The first request after launch is timed on its own: that is where the
     model loads. Everything after it is a warm run.
  3. Each launch then sends --runs warm requests of one fixed ~110-word text,
     one at a time, each under its own creator_id (so the rate limiter, 6 a
     minute per creator, never interferes).
  4. On the last launch it also sends --runs short and --runs long texts, to
     show how cost moves with length. The model reads at most
     config.DETECTOR_MAX_TOKENS tokens, so a long text stops costing more.
  5. Client time is perf_counter around the HTTP call. Server time, CPU time
     and per-signal time are read back from logs/runs.jsonl by creator_id, not
     taken from the response, so the run log is what is being relied on.
  6. Memory is the working set of the process listening on the port, from
     `tasklist` (Windows only; skipped elsewhere), before and after the cold run.

Every request it sends also lands in logs/runs.jsonl under a creator_id that
starts with `cost_`, which keeps them separable from real use.
"""
import argparse
import csv
import io
import os
import re
import statistics
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))    # the project root, where config.py lives

import config
import runlog
from scenarios import PLAIN_HUMAN

sys.stdout.reconfigure(errors="replace")

SHORT = "We missed the last train, so we walked home along the canal."
MEDIUM = PLAIN_HUMAN
LONG = " ".join([PLAIN_HUMAN] * 5)


def listener_pid(port):
    """PID of the process listening on the port (Windows: netstat)."""
    out = subprocess.run(["netstat", "-ano", "-p", "tcp"], capture_output=True, text=True).stdout
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 5 and parts[3] == "LISTENING" and parts[1].endswith(f":{port}"):
            return int(parts[4])
    return None


def memory_mb(pid):
    """Working set in MB from tasklist, or None if it cannot be read."""
    if pid is None or sys.platform != "win32":
        return None
    out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
                         capture_output=True, text=True).stdout
    try:
        row = next(csv.reader(io.StringIO(out.strip())))
        return int("".join(ch for ch in row[-1] if ch.isdigit())) / 1024
    except (StopIteration, ValueError, IndexError):
        return None


def stop(proc, port):
    pid = listener_pid(port)
    for target in (pid, proc.pid):
        if target:
            subprocess.run(["taskkill", "/PID", str(target), "/F", "/T"],
                           capture_output=True, text=True)
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        pass


def launch(port):
    env = dict(os.environ, PORT=str(port), AI201_DEBUG="0")
    proc = subprocess.Popen([sys.executable, "app.py"], env=env, cwd=str(config.ROOT),
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = f"http://127.0.0.1:{port}"
    started = time.perf_counter()
    for _ in range(120):
        try:
            if requests.get(f"{url}/health", timeout=2).status_code == 200:
                return proc, url, time.perf_counter() - started
        except requests.RequestException:
            time.sleep(0.5)
    proc.kill()
    raise SystemExit("server did not come up")


def one_run(url, text, creator):
    t0 = time.perf_counter()
    resp = requests.post(f"{url}/submit", json={"text": text, "creator_id": creator}, timeout=180)
    client_ms = (time.perf_counter() - t0) * 1000
    if resp.status_code != 200:
        raise SystemExit(f"{creator}: status {resp.status_code} {resp.text[:200]}")
    return client_ms


def server_side(creator):
    """The run-log record for one creator_id: the server's own numbers."""
    records = [r for r in runlog.read() if r.get("creator_id") == creator]
    if len(records) != 1:
        raise SystemExit(f"{creator}: expected one run record, found {len(records)}")
    return records[0]


def measure(url, text, label, stamp, count, offset=0):
    rows = []
    for i in range(count):
        creator = f"cost_{stamp}_{label}_{offset + i}"
        client_ms = one_run(url, text, creator)
        rec = server_side(creator)
        rows.append({"client_ms": client_ms, "words": rec["input"]["words"],
                     "duration_ms": rec["duration_ms"], "cpu_ms": rec["cpu_ms"],
                     "model_ms": rec["model_ms"], "style_ms": rec["style_ms"],
                     "cold_start": rec["cold_start"]})
    return rows


def avg(rows, key):
    return statistics.mean(r[key] for r in rows)


def summary(rows):
    keys = ("client_ms", "duration_ms", "cpu_ms", "model_ms", "style_ms")
    return {k: (statistics.mean(r[k] for r in rows),
                statistics.median(r[k] for r in rows),
                min(r[k] for r in rows), max(r[k] for r in rows),
                statistics.pstdev(r[k] for r in rows)) for k in keys}


SPREAD_HEADING = "## Spread of the warm runs"


def distribution(stamp=None) -> tuple[str, str]:
    """
    The spread of the warm runs, rebuilt from the run log alone: mean, median,
    90th percentile, min and max, plus every run in the order it happened.

    A mean hides this. When the machine is busy, identical work takes many times
    longer, so one average can describe no actual run.
    """
    pattern = re.compile(r"^cost_(\d+)_(L\d+warm)_(\d+)$")
    found = []
    for r in runlog.read():
        m = pattern.match(r.get("creator_id") or "")
        if m:
            found.append((m.group(1), m.group(2), int(m.group(3)), r))
    if not found:
        raise SystemExit("no measurement runs (creator_id cost_*) in the run log")
    stamp = stamp or max(s for s, *_ in found)
    mine = sorted((x for x in found if x[0] == stamp), key=lambda x: (x[1], x[2]))

    def stats(values):
        v = sorted(values)
        p90 = v[min(len(v) - 1, int(0.9 * len(v)))]
        return (len(v), statistics.mean(v), statistics.median(v), p90, v[0], v[-1])

    wall = stats([x[3]["duration_ms"] for x in mine])
    cpu = stats([x[3]["cpu_ms"] for x in mine])
    lines = [SPREAD_HEADING, "",
             f"Rebuilt from `logs/runs.jsonl`, runs with `creator_id` `cost_{stamp}_L*warm_*`. "
             f"The same text was sent every time.", "",
             "| Measure (ms) | n | Mean | Median | 90th pct | Min | Max |", "|---|---|---|---|---|---|---|"]
    for name, s in (("Wall (server)", wall), ("CPU", cpu)):
        lines.append(f"| {name} | {s[0]} | {s[1]:.0f} | {s[2]:.0f} | {s[3]:.0f} | {s[4]:.0f} | {s[5]:.0f} |")
    lines += ["", f"Slowest warm run was **{wall[5] / wall[4]:.0f}x** the fastest on identical input.",
              "", "Every warm run, in order (wall ms / CPU ms):", ""]
    for launch in sorted({x[1] for x in mine}):
        seq = " ".join(f"{x[3]['duration_ms']:.0f}/{x[3]['cpu_ms']:.0f}" for x in mine if x[1] == launch)
        lines.append(f"- {launch}: {seq}")
    return stamp, "\n".join(lines) + "\n"


def append_distribution(report_path, stamp=None):
    """Add (or replace) the spread section at the end of a cost report."""
    _, section = distribution(stamp)
    text = report_path.read_text(encoding="utf-8")
    if SPREAD_HEADING in text:
        text = text[:text.index(SPREAD_HEADING)].rstrip() + "\n"
    report_path.write_text(text + "\n" + section, encoding="utf-8")
    return section


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--distribution", action="store_true",
                        help="add the spread of the last run's warm runs to its report; send nothing")
    parser.add_argument("--runs", type=int, default=10, help="warm runs per launch and per length")
    parser.add_argument("--launches", type=int, default=3, help="fresh server starts (cold starts)")
    parser.add_argument("--port", type=int, default=5002)
    parser.add_argument("--no-lengths", action="store_true",
                        help="skip the short and long text runs; measure only the medium text")
    args = parser.parse_args()

    if args.distribution:
        newest = max(config.RESULTS_DIR.glob("cost_*.md"), key=lambda p: p.stat().st_mtime, default=None)
        if newest is None:
            raise SystemExit("no results/cost_*.md report yet; run the measurement first")
        print(append_distribution(newest))
        print(f"Added to {newest}")
        return

    if listener_pid(args.port):
        raise SystemExit(f"port {args.port} is already in use; pick another with --port")

    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    launches = []
    extra = {}
    for n in range(1, args.launches + 1):
        proc, url, startup_s = launch(args.port)
        try:
            pid = listener_pid(args.port)
            mem_before = memory_mb(pid)
            cold = measure(url, MEDIUM, f"L{n}cold", stamp, 1)[0]
            mem_after = memory_mb(pid)
            warm = measure(url, MEDIUM, f"L{n}warm", stamp, args.runs)
            launches.append({"startup_s": startup_s, "cold": cold, "warm": warm,
                             "mem_before": mem_before, "mem_after": mem_after})
            print(f"launch {n}: startup {startup_s:.1f}s, cold run {cold['client_ms'] / 1000:.1f}s, "
                  f"warm mean {avg(warm, 'client_ms'):.0f} ms (n={len(warm)})")
            if n == args.launches and not args.no_lengths:
                extra["short"] = measure(url, SHORT, "short", stamp, args.runs)
                extra["long"] = measure(url, LONG, "long", stamp, args.runs)
        finally:
            stop(proc, args.port)

    all_warm = [r for l in launches for r in l["warm"]]
    stamp_h = datetime.now().strftime("%Y-%m-%d_%H%M")
    path = config.RESULTS_DIR / f"cost_{stamp_h}.md"
    config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    def line(name, s):
        return (f"| {name} | {s['client_ms'][0]:.0f} | {s['duration_ms'][0]:.0f} | "
                f"{s['cpu_ms'][0]:.0f} | {s['model_ms'][0]:.0f} | {s['style_ms'][0]:.1f} | "
                f"{s['client_ms'][2]:.0f}-{s['client_ms'][3]:.0f} |")

    out = []
    out.append(f"# Cost of one run - measured {datetime.now():%Y-%m-%d %H:%M}\n")
    out.append("This system calls no paid API and uses no tokens. The cost of a run is "
               "compute on the local machine: wall time, CPU time and memory.\n")
    out.append("## How it was measured\n")
    out.append(f"- `python tools/measure_cost.py --launches {args.launches} --runs {args.runs}` "
               f"(Python {sys.version.split()[0]}, {sys.platform}, model `{config.DETECTOR_MODEL}`, "
               f"`DETECTOR_MAX_TOKENS` {config.DETECTOR_MAX_TOKENS}).")
    out.append(f"- Each launch starts a fresh server, so the first request is a true cold start. "
               f"It is timed alone. {args.runs} warm runs of one fixed {launches[0]['warm'][0]['words']}-word "
               f"text follow, one at a time, each under its own `creator_id`.")
    out.append("- Client time is `perf_counter` around the HTTP call. Wall duration, CPU time and "
               "per-signal time come from the service's own run record in `logs/runs.jsonl` "
               "(`duration_ms`, `cpu_ms`, `model_ms`, `style_ms`), matched by `creator_id`.")
    out.append("- `cpu_ms` is process-wide CPU time over the request (`time.process_time`), valid "
               "because requests were sent one at a time. It can exceed wall time because torch "
               "uses several cores.")
    out.append("- Memory is the working set of the listening process from `tasklist`, before and "
               "after the cold run.\n")
    out.append("## Cold start (first run after launch)\n")
    out.append("| Launch | Server up (s) | Cold run, client (s) | Cold run CPU (s) | Memory before -> after (MB) |")
    out.append("|---|---|---|---|---|")
    fmt_mem = lambda m: "n/a" if m is None else f"{m:.0f}"
    for i, l in enumerate(launches, 1):
        out.append(f"| {i} | {l['startup_s']:.1f} | {l['cold']['client_ms'] / 1000:.1f} | "
                   f"{l['cold']['cpu_ms'] / 1000:.1f} | {fmt_mem(l['mem_before'])} -> {fmt_mem(l['mem_after'])} |")
    colds = [l["cold"]["client_ms"] / 1000 for l in launches]
    out.append(f"\nMean cold run: **{statistics.mean(colds):.1f} s** over {len(colds)} launches.\n")
    out.append("## Warm runs (milliseconds, mean unless noted)\n")
    out.append("| Set | Client | Wall (server) | CPU | Model signal | Style signal | Client min-max |")
    out.append("|---|---|---|---|---|---|---|")
    for i, l in enumerate(launches, 1):
        out.append(line(f"Launch {i}, medium, n={len(l['warm'])}", summary(l["warm"])))
    out.append(line(f"**All launches, medium, n={len(all_warm)}**", summary(all_warm)))
    if "short" in extra:
        out.append(line(f"Short ({extra['short'][0]['words']} words), n={len(extra['short'])}", summary(extra["short"])))
        out.append(line(f"Long ({extra['long'][0]['words']} words, truncated at the token limit), n={len(extra['long'])}", summary(extra["long"])))
    s = summary(all_warm)
    out.append("")
    out.append(f"**One warm run costs about {s['duration_ms'][0] / 1000:.2f} s of wall time and "
               f"{s['cpu_ms'][0] / 1000:.2f} s of CPU** (mean of {len(all_warm)}). "
               f"{s['model_ms'][0] / s['duration_ms'][0] * 100:.0f}% of it is the model signal; "
               f"the style signal is {s['style_ms'][0]:.1f} ms.\n")
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    append_distribution(path, stamp)
    print("\n" + path.read_text(encoding="utf-8"))
    print(f"run stamp: {stamp}")
    print(f"\nWrote {path}")


if __name__ == "__main__":
    main()
