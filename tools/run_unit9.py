"""
Run the five unit 9 criteria (9.1 to 9.5 in criteria.md), save the real output,
and fill in the run log.

    python tools/run_unit9.py            3 separate runs, about 25 minutes
    python tools/run_unit9.py --runs 1
    python tools/run_unit9.py --label after     keep this result set apart from an earlier one:
                                                results/unit9_after/ and results/unit9_run_log_after.md

Each run is a complete pass, started from scratch. What is run for each
criterion, and why that and not something cheaper:

  9.1  failure handling   tools/failure_check.py: nine kinds of failure
       triggered on purpose (real bad inputs, a real burst past the rate limit,
       an injected model failure and an injected route crash).
  9.2  degraded speed     a NEW server started with the model unable to load,
       then tools/degraded_check.py: 3 trials x 10 requests, 30 in all. A fresh
       server each run, so the slow first request is part of the measurement.
  9.3  logs agree         tools/reconcile_check.py against a live server: 40
       mixed requests from 8 clients at once, then both logs are compared.
  9.4  latency            tools/measure_cost.py: a fresh launch and 30 warm runs
       of one text, so there is a distribution and a 90th percentile.
  9.5  false positives    run_attacks.py on the false_positive family (FP01 to
       FP08) against a live server.

Every step's output is saved untouched to results/unit9/run<N>/<step>.txt, and
the table, with the evidence from run 1, is written to results/unit9_run_log.md.
A run is judged MET only if every one of the runs meets the target, which is how
the earlier units were judged.

Nothing else should be running while this does: 9.2 and 9.4 are timings.
"""
import argparse
import os
import re
import statistics
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))    # the project root

import config
import runlog
from measure_cost import distribution, listener_pid, stop

sys.stdout.reconfigure(errors="replace")

ROOT = config.ROOT
OUT = config.RESULTS_DIR / "unit9"
PORT = 5007
LABEL = ""
ENV = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")

CRITERIA = [
    ("9.1", "Every failure kind leaves a record", "9 of 9 kinds leave exactly one record with a reason"),
    ("9.2", "A degraded answer is quick", "median ≤ 1 s and max ≤ 3 s with the model unable to load"),
    ("9.3", "The two logs agree", "40 of 40 records, no bad lines, run and audit entries agree"),
    ("9.4", "A writer does not wait long", "90% of 30 warm runs ≤ 5 s wall and ≤ 3 s CPU"),
    ("9.5", "Plain human writing is not accused", "≤ 2 of 8 plain-human texts labelled AI"),
]


def step(run_dir, name, args, timeout=2400):
    """Run one command, save its whole output, return (exit code, text)."""
    print(f"    {name} ...", flush=True)
    started = time.time()
    proc = subprocess.run([sys.executable, *args], cwd=str(ROOT), env=ENV, timeout=timeout,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    text = proc.stdout.decode("utf-8", errors="replace")
    (run_dir / f"{name}.txt").write_text(
        f"$ python {' '.join(args)}\n(exit code {proc.returncode}, {time.time() - started:.0f}s)\n\n{text}",
        encoding="utf-8")
    return proc.returncode, text


def start_server(extra_env=None):
    env = dict(ENV, PORT=str(PORT), AI201_DEBUG="0", **(extra_env or {}))
    proc = subprocess.Popen([sys.executable, "app.py"], env=env, cwd=str(ROOT),
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = f"http://127.0.0.1:{PORT}"
    began = time.perf_counter()
    for _ in range(240):
        try:
            if requests.get(f"{url}/health", timeout=2).status_code == 200:
                return proc, url, time.perf_counter() - began
        except requests.RequestException:
            time.sleep(0.5)
    proc.kill()
    raise SystemExit("server did not come up")


def p90(values):
    v = sorted(values)
    return v[min(len(v) - 1, int(0.9 * len(v)))]


def records_for(prefix):
    return [r for r in runlog.read() if (r.get("creator_id") or "").startswith(prefix)]


def raw_lines(path, wanted):
    """The exact lines of runs.jsonl whose run_id is in `wanted`, in file order."""
    return [ln for ln in path.read_text(encoding="utf-8").splitlines()
            if any(f'"run_id": "{rid}"' in ln for rid in wanted)]


def one_run(n, evidence):
    run_dir = OUT / f"run{n}"
    run_dir.mkdir(parents=True, exist_ok=True)
    res = {}

    # 9.1 failure handling
    rc, out = step(run_dir, "9.1_failure_check", ["tools/failure_check.py"])
    m = re.search(r"RESULT kinds_ok=(\d+)/(\d+)", out)
    res["9.1"] = {"ok": int(m[1]), "of": int(m[2])} if m else None
    if n == 1:
        evidence["9.1"] = out
    step(run_dir, "unit_tests", ["-m", "unittest", "discover", "-s", "tests"])

    # 9.3 and 9.5 share one healthy server (9.3's warm-up request loads the model)
    proc, url, up = start_server()
    res["startup_s"] = up
    try:
        rc, out = step(run_dir, "9.3_reconcile", ["tools/reconcile_check.py", "--url", url])
        m = re.search(r"RESULT records=(\d+)/(\d+) malformed=(\d+) agree=(\d+)/(\d+)", out)
        res["9.3"] = ({"records": int(m[1]), "expected": int(m[2]), "malformed": int(m[3]),
                       "agree": int(m[4]), "decided": int(m[5])} if m else None)
        if n == 1:
            evidence["9.3"] = out

        rc, out = step(run_dir, "9.5_false_positives",
                       ["run_attacks.py", "--set", "attack_set", "--family", "false_positive",
                        "--label", f"unit9{LABEL}_run{n}", "--url", url])
        report = re.search(r"Wrote (\S*attack_run_\S+\.md)", out)
        rows = []
        if report:
            for line in (ROOT / report[1]).read_text(encoding="utf-8").splitlines():
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                if len(cells) >= 7 and re.fullmatch(r"FP\d\d", cells[0]):
                    rows.append(cells)
        res["9.5"] = {"accused": sum(r[5] == "ai" for r in rows), "of": len(rows)} if rows else None
        if n == 1 and rows:
            evidence["9.5"] = {"report": report[1], "rows": [f"| {' | '.join(r)} |" for r in rows],
                               "output": out}
    finally:
        stop(proc, PORT)

    # 9.2 a new server with the model unable to load
    # Unique per result set AND per moment: an earlier set used the same names, and a
    # lookup by prefix then returned both sets' records mixed together.
    tag = f"u9{LABEL}r{n}t{datetime.now():%H%M%S}"
    proc, url, up = start_server({"AI201_DETECTOR_MODEL": "does-not-exist-xyz"})
    res["startup_broken_s"] = up
    try:
        rc, out = step(run_dir, "9.2_degraded", ["tools/degraded_check.py", "--expect", "degraded",
                                                  "--trials", "3", "--tag", tag, "--url", url])
    finally:
        stop(proc, PORT)
    recs = records_for(f"degraded_degraded_{tag}_t")
    if recs:
        wall = [r["duration_ms"] for r in recs]
        res["9.2"] = {"n": len(recs), "median": statistics.median(wall), "max": max(wall),
                      "all_ok": rc == 0}
        if n == 1:
            by_time = sorted(recs, key=lambda r: r["timestamp"])
            middle = sorted(recs, key=lambda r: r["duration_ms"])[len(recs) // 2]
            picks = [by_time[0], middle, by_time[-1]]
            evidence["9.2"] = {"output": out, "run_ids": [r["run_id"] for r in picks]}
    else:
        res["9.2"] = None

    # 9.4 a fresh launch and 30 warm runs
    rc, out = step(run_dir, "9.4_cost", ["tools/measure_cost.py", "--launches", "1", "--runs", "30",
                                          "--no-lengths"], timeout=3600)
    m = re.search(r"run stamp: (\d+)", out)
    recs = records_for(f"cost_{m[1]}_L1warm_") if m else []
    if recs:
        wall = [r["duration_ms"] for r in recs]
        cpu = [r["cpu_ms"] for r in recs]
        res["9.4"] = {"n": len(recs), "p90_wall": p90(wall), "p90_cpu": p90(cpu),
                      "median_wall": statistics.median(wall)}
        if n == 1:
            fast = min(recs, key=lambda r: r["duration_ms"])
            slow = max(recs, key=lambda r: r["duration_ms"])
            evidence["9.4"] = {"spread": distribution(m[1])[1], "run_ids": [fast["run_id"], slow["run_id"]]}
    else:
        res["9.4"] = None
    return res


def cell(cid, r):
    if r is None:
        return "no result"
    if cid == "9.1":
        return f"{r['ok']} of {r['of']}"
    if cid == "9.2":
        return f"median {r['median'] / 1000:.1f} s, max {r['max'] / 1000:.1f} s"
    if cid == "9.3":
        bad = f", {r['malformed']} bad lines" if r["malformed"] else ""
        return f"{r['records']}/{r['expected']} records, {r['agree']}/{r['decided']} agree{bad}"
    if cid == "9.4":
        return f"p90 {r['p90_wall'] / 1000:.1f} s wall, {r['p90_cpu'] / 1000:.1f} s CPU"
    return f"{r['accused']} of {r['of']} accused"


def met(cid, r):
    if r is None:
        return False
    return {
        "9.1": lambda: r["ok"] == r["of"] == 9,
        "9.2": lambda: r["median"] <= 1000 and r["max"] <= 3000,
        "9.3": lambda: r["records"] == r["expected"] and r["malformed"] == 0 and r["agree"] == r["decided"],
        "9.4": lambda: r["p90_wall"] <= 5000 and r["p90_cpu"] <= 3000,
        "9.5": lambda: r["of"] == 8 and r["accused"] <= 2,
    }[cid]()


def git(*args):
    return subprocess.run(["git", *args], cwd=str(ROOT), capture_output=True, text=True).stdout.strip()


def fence(text, lang=""):
    return f"```{lang}\n{text.rstrip()}\n```"


def write_log(runs, evidence, started):
    log_path = runlog.path()
    lines = [f"# Run log, unit 9: the extension", "",
             f"- Run {started:%Y-%m-%d %H:%M} by `python tools/run_unit9.py --runs {len(runs)}` "
             f"(`tools/run_unit9.py::main`), commit `{git('rev-parse', '--short', 'HEAD')}`"
             f"{', with uncommitted changes' if git('status', '--porcelain') else ''}.",
             f"- Machine: 11th Gen Intel Core i5-1135G7, Windows, Python {sys.version.split()[0]}, "
             f"model `{config.DETECTOR_MODEL}`.",
             f"- {len(runs)} separate runs, each a complete pass of all five criteria from scratch. "
             f"A criterion is MET only if every run meets its target.",
             f"- Every step's output, untouched, is in `{OUT.relative_to(ROOT).as_posix()}/run1` to `run{len(runs)}`.", "",
             "| Criterion | Target | " + " | ".join(f"Run {i}" for i in range(1, len(runs) + 1)) + " | Verdict |",
             "|---|---|" + "---|" * len(runs) + "---|"]
    for cid, name, target in CRITERIA:
        cells = [cell(cid, run[cid]) for run in runs]
        verdict = "MET" if all(met(cid, run[cid]) for run in runs) else "MISSED"
        lines.append(f"| {cid} {name} | {target} | " + " | ".join(cells) + f" | {verdict} |")

    ups = [r["startup_s"] for r in runs if "startup_s" in r]
    lines += ["", f"Server start-up, seconds until `/health` answers (healthy server, one per run): "
              + ", ".join(f"{u:.1f}" for u in ups) + f"; mean {statistics.mean(ups):.1f}.", ""]
    lines += ["", "## What actually came back (run 1)", "",
              "Real output from run 1, unedited. Each block names the file and function that produced it.", ""]

    lines += ["### 9.1 Every failure kind leaves a record", "",
              "Produced by `tools/failure_check.py::main` (via `exercise`), which sends the requests through "
              "`app.py::submit`. The records are the lines `runlog.py::write` appended, built by "
              "`runlog.py::build_record` from the hooks in `app.py::_write_run`. The first two blocks "
              "are the summary the tool printed; the JSON lines are the records themselves.", "",
              fence(evidence["9.1"]), ""]

    ev = evidence.get("9.2")
    lines += ["### 9.2 A degraded answer is quick", "",
              "Produced by `tools/degraded_check.py::main` against a server started with "
              "`AI201_DETECTOR_MODEL=does-not-exist-xyz`. The fallback is `app.py::submit` calling "
              "`scoring.py::label_without_model`; the timings are `duration_ms` in the records "
              "`runlog.py::write` appended to `logs/runs.jsonl`. Below: what the tool printed, then the "
              "first request, the median request and the last request of the 30, as written.", ""]
    if ev:
        lines += [fence(ev["output"]), "", fence("\n".join(raw_lines(log_path, ev["run_ids"])), "json"), ""]

    lines += ["### 9.3 The two logs agree", "",
              "Produced by `tools/reconcile_check.py::main`. The run records are written by "
              "`runlog.py::write` and the audit entries by `audit.py::log_decision` (called from "
              "`app.py::submit`). Below: what the tool printed, ending with three decisions, each shown "
              "as its run record followed by its audit entry.", "", fence(evidence["9.3"]), ""]

    ev = evidence.get("9.4")
    lines += ["### 9.4 A writer does not wait long", "",
              "Produced by `tools/measure_cost.py::main`, with the spread computed by "
              "`tools/measure_cost.py::distribution` from `duration_ms` and `cpu_ms` in "
              "`logs/runs.jsonl` (`runlog.py::write`). Below: the spread of the 30 warm runs, then the "
              "fastest and the slowest run as written.", ""]
    if ev:
        lines += [fence(ev["spread"]), "", fence("\n".join(raw_lines(log_path, ev["run_ids"])), "json"), ""]

    ev = evidence.get("9.5")
    lines += ["### 9.5 Plain human writing is not accused", "",
              "Produced by `run_attacks.py::main`, which sends each text to `app.py::submit`; the label "
              "comes from `scoring.py::score_to_label`. Below: the eight false-positive rows of the "
              f"report it wrote (`{ev['report'] if ev else ''}`).", ""]
    if ev:
        lines += ["| ID | Family | Targeting | Status | Content ID | Guess | Score | Verdict |",
                  "|---|---|---|---|---|---|---|---|", *ev["rows"], ""]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--label", default="", help="keep this result set apart, e.g. before or after")
    args = parser.parse_args()
    global OUT, LABEL
    if args.label:
        LABEL = args.label
        OUT = config.RESULTS_DIR / f"unit9_{args.label}"
    if listener_pid(PORT):
        raise SystemExit(f"port {PORT} is in use")

    started = datetime.now()
    runs, evidence = [], {}
    for n in range(1, args.runs + 1):
        print(f"Run {n} of {args.runs}", flush=True)
        runs.append(one_run(n, evidence))
        print(f"  run {n} done: " + "; ".join(f"{cid} {cell(cid, runs[-1][cid])}" for cid, *_ in CRITERIA), flush=True)

    text = write_log(runs, evidence, started)
    path = config.RESULTS_DIR / (f"unit9_run_log_{LABEL}.md" if LABEL else "unit9_run_log.md")
    path.write_text(text, encoding="utf-8")
    print("\n" + text.split("## What actually came back")[0])
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
