# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Provenance Guard: an AI201 course assignment (units 7–9). It's a Flask web
service that scores submitted text for "likely AI-written" using two signals
(a local language model's perplexity, and hand-built stylometry), combines
them into one score, and maps that score to a label a reader sees. Unit 8
adds rate limiting and an attack set designed to exploit each signal's known
blind spot.

Most of the codebase is a deliberately incomplete starter: the TODOs in
`app.py`, `stylometry.py`, and `scoring.py` are student-facing assignment
work, not bugs. Don't "complete" them speculatively — follow whatever the
user is actually asking for, and preserve the milestone-by-milestone build
order described in their docstrings if adding to them.

## Commands

```bash
# Setup (first time)
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python test.py                     # environment check — run before anything else

python detector.py                 # one-time: downloads the ~550MB gpt2 model
python detector.py "some text"     # score one piece of text from the CLI
python stylometry.py "some text"   # print the style measures for one text

python app.py                      # run the service (http://127.0.0.1:5000)

# Unit 8 tooling (service must be running in another terminal)
python run_attacks.py --set path/to/attack_set              # full attack run
python run_attacks.py --set path/to/attack_set --id EV03    # one attack
python run_attacks.py --set path/to/attack_set --id EV03 --show   # print only, send nothing
python run_attacks.py --set path/to/attack_set --one-per-family --show
python run_attacks.py --flood 15                             # rate-limit check
python run_eval.py --label before                            # run scenarios.py, 3 trials each
```

There is no lint config and no formal test suite beyond `test.py` (an
environment/smoke check, not unit tests — it asserts `/ping` answers via
Flask's test client but doesn't test `/submit` or `/appeal` logic).

On Windows, `curl` in PowerShell is aliased to a different tool — use
`curl.exe` with the whole command on one line (see RUNNING.md for exact
syntax). Every helper script (`run_attacks.py`, `run_eval.py`, `test.py`)
reconfigures stdout/stderr with `errors="replace"` because Windows consoles
often can't print the Unicode in `--help` text — keep that pattern if adding
new CLI entry points.

## Architecture

Request flow through `/submit` (once built): `app.py` pulls `text` /
`creator_id` from the JSON body → `detector.model_signal(text)` (signal one)
and `stylometry.style_signal(text)` (signal two) each produce an independent
0–1 "how AI-like" score → `scoring.combine_signals(model_score, style_score)`
merges them into one 0–1 score → `scoring.score_to_label(score)` maps that to
a `(guess, label_text)` pair → `audit.log_decision(...)` writes one JSON line
per decision → the route returns `content_id`, `guess`, `confidence`,
`label`, and **both** raw signal scores (`model_score`, `style_score`) — the
unit 8 tooling reads those two fields directly off the response, so omitting
them breaks all downstream diagnostics, not just the README.

- **`config.py`** — the single place for every tunable: host/port/debug,
  model name, signal weights (`WEIGHT_MODEL_SIGNAL` / `WEIGHT_STYLE_SIGNAL`),
  label thresholds (`HUMAN_THRESHOLD` / `AI_THRESHOLD`), rate limits, paths.
  Treat values here as the intended single source of truth; don't hardcode
  thresholds or weights elsewhere.
- **`detector.py`** (signal one, given/working) — loads a HF causal LM
  (`gpt2` by default) lazily and caches it in module globals `_model` /
  `_tokenizer`; `model_signal` turns perplexity into a 0–1 score via a
  logistic curve centered on a perplexity midpoint. Blind spot: rewards
  "common words, short ordinary sentences" regardless of actual authorship —
  this is a load-bearing fact for how unit 8's `false_positive` attack family
  and `criteria.md` are framed, not an implementation bug.
- **`stylometry.py`** (signal two, stub) — three measures
  (`sentence_length_spread`, `type_token_ratio`, `punctuation_density`)
  combined by `style_signal`. It's pure text-shape analysis with no semantic
  understanding — cheap to fool with typos/sentence-splitting/pasted quotes
  by design. Both signals must point the same direction (higher = more
  likely AI) since `scoring.combine_signals` treats them identically.
- **`scoring.py`** (stub) — `combine_signals` is the single named
  combining-rule function (the README explicitly must cite
  `scoring.py::combine_signals`, and tooling/grading checks that claim
  against this file). `score_to_label` maps score → `(guess, label_text)`;
  all three labels (human / unsure / AI) must be reachable given the
  configured thresholds and weights — `label_ranges()` reports the bands.
- **`audit.py`** (given/working) — append-only JSONL log at
  `logs/audit.jsonl`. Three write paths: `log_decision` (every `/submit`,
  nine required fields always present even if `None`), `log_appeal` (moves
  status to `under_review`, never overwrites the original entry), and
  `log_rejection` (rate-limit or input rejections — logged specifically so a
  rejected flood of requests still leaves a trace instead of looking like
  silence). `entries_for(content_id)` backs `/appeal`'s existence check.
- **`app.py`** — Flask routes. `/ping` and `/log` are complete and must not
  be edited (`/ping` is the diagnostic control: if it fails, the service
  itself is broken, not the handler). `/submit` and `/appeal` are the
  student-built routes. The rate limiter is a no-op shim (`_LimiterOff`)
  until `config.RATE_LIMITING_ENABLED` is true, at which point real
  `flask_limiter.Limiter` wiring activates; the commented
  `@limiter.limit(...)` line above `submit` is meant to be uncommented
  independent of the flag flip. The rate-limit key function keys by
  `creator_id` when present in a dict JSON body, else falls back to the
  caller's IP — guard against non-dict JSON bodies there (a bare list/string
  payload has no `.get`).
- **`run_attacks.py`** / **`scenarios.py`** / **`run_eval.py`** (unit 8
  tooling, given/working) — `run_attacks.py` sends a CSV-defined attack set
  (`attacks.csv` + `attacks_malformed_requests.csv`) against the running
  service and writes `results/attack_run_<date>.md`; it auto-marks only the
  unambiguous case (5xx/crash) as BROKE and leaves everything else for human
  judgment, since "did this evasion work" depends on where thresholds are
  set. `scenarios.py` is where the student encodes what each of their five
  `criteria.md` criteria needs tested; `run_eval.py` runs those scenarios 3
  trials each (signal one is non-deterministic across runs) and writes
  `results/run_<date>.md`.

## Conventions specific to this repo

- `logs/` and `results/` are intentionally **not** gitignored — audit log
  entries and attack/eval reports are graded evidence and are meant to be
  committed.
- Numeric settings in `config.py` (weights, thresholds, rate limits) are
  write-up-relevant: the README (`README.md`) is expected to name and
  justify whatever values end up there, so changing them is a documented
  decision, not just a tweak.
- This is a paired/graded assignment repo with pinned commit hashes tracked
  externally for grading (see `.github/MAINTAINERS.md`) — never delete and
  recreate this repository, and never rewrite history (no force-push, no
  amending pushed commits, no `git filter-branch`/history rewrite) since that
  invalidates the hash baseline other tooling depends on.
