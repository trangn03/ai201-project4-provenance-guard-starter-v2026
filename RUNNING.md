# Running Provenance Guard

**Path B: local, with logs.** This system runs on your own machine, started by one command, and records every run in a log you can read back. It is not hosted, and cannot be on a free host (see [Why not hosted](#why-not-hosted)).

```bash
python app.py
```

That is the whole start command. Run it from the project folder after the one-time setup below. It listens on `http://127.0.0.1:5000`.

---

## What the environment needs

| Need | Value |
|---|---|
| Python | **3.11, 3.12 or 3.13. Not 3.14.** Tested on 3.11.9 |
| OS | Tested on Windows 11. The commands below give the macOS/Linux form too, but I have not run those |
| Memory | The service holds about **490 MB** once the model is loaded (Windows working set, measured at 482 to 503 MB). Tested on a machine with 7.6 GB |
| Disk | The model is **526 MB** on disk. `torch` is the other large install |
| Network | Needed once: to install packages and to download the model (it ran about 28 s on my connection). After that it works offline |
| Accounts or keys | None. Nothing here calls a hosted service |
| Model | `gpt2`, downloaded automatically by `python detector.py` into `%USERPROFILE%\.cache\huggingface\hub` (`~/.cache/huggingface/hub` elsewhere) |

**Pinned dependencies.** `requirements.txt` pins each package with a lower and an upper bound. A clean install on 2026-11-08 resolved to these exact versions, and all 49 tests pass on them:

| Package | Allowed by `requirements.txt` | Installed in the clean test |
|---|---|---|
| flask | >=3.0,<4.0 | 3.1.3 |
| flask-limiter | >=3.5,<4.0 | 3.12 |
| requests | >=2.31,<3.0 | 2.34.2 |
| transformers | >=4.44,<5.0 | 4.57.6 |
| torch | >=2.2,<3.0 | 2.15.0 (CPU build) |
| gunicorn | >=21.2,<24.0 | 23.0.0 (installed, not used) |

Pulled in by those: numpy 2.4.6, tokenizers 0.22.2, huggingface_hub 0.36.2, safetensors 0.8.0, Werkzeug 3.1.9. My working copy ran `torch` 2.14.1 and also passes everything.

---

## Set up (once)

**1. A virtual environment and the packages.**

PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Git Bash: `source .venv/Scripts/activate`. macOS/Linux: `source .venv/bin/activate`. The install took **387 seconds** (6.5 minutes) here, almost all of it `torch`.

**2. Check the environment.**

```bash
python test.py
```

On a machine that has never downloaded the model, the real output is:

```
[WARN] Detector model
         Not downloaded yet (~550 MB). Run `python detector.py` once BEFORE
8 passed, 0 failed, 1 to look at, 0 skipped
```

That warning is expected. Everything else should read `[PASS]`.

**3. Download the model.**

```bash
python detector.py
```

It downloads gpt2 (about 28 s here, 526 MB) and scores a sample. The last lines:

```
Loading gpt2 (first run downloads ~550 MB)…
perplexity     12.5
model_signal   0.8864   (higher = more likely AI)
```

Two warnings appear above that and are harmless: one says Windows cannot create symlinks without Developer Mode (the model is simply stored without them), and one says an optional download accelerator is not installed. After this, `python test.py` reads `9 passed`.

---

## Start it

```bash
python app.py
```

What you should see (the banner prints twice, because debug mode starts a second process that restarts the server):

```
Provenance Guard on http://127.0.0.1:5000
  detector model:  gpt2
  rate limiting:   ON
  audit log:       <this folder>\logs\audit.jsonl

 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
 * Restarting with stat
Provenance Guard on http://127.0.0.1:5000
...
Loading torch and transformers (10 to 15 seconds) so the first request is not slow ...
 * Debugger is active!
```

**It takes 10 to 20 seconds before it answers** in most starts (18 s in the test below). Across the twelve starts I timed I saw 10 to 21 s in ten of them, and 50 s and 60 s in the other two; I did not find out why. That is the preload of `torch` and `transformers`; it is deliberate, and it moves a wait that would otherwise land on the first request. Set `AI201_PRELOAD=0` to turn it off and start in about a second, at the price of a slow first request.

The model weights load on the first `/submit`, not at start-up: **3 to 8 seconds** with the preload on in my tests. `GET /health` shows `"detector_loaded": false` until then. Stop the server with Ctrl+C.

**If port 5000 is busy** (`Address already in use`), set `PORT`: `$env:PORT = "5001"` in PowerShell, `PORT=5001 python app.py` in bash. Be careful: on Windows a second server can sometimes bind a port that is already taken, and requests then go to whichever answers, which looks like your changes not working. Check `GET /health` for `detector_model` if in doubt. All the real output on this page was captured with `PORT=5001`, because 5000 was in use on my machine; the responses are identical.

---

## Check that it works

Two terminals. The server runs in the first. In the second:

> **On Windows, use `curl.exe`, on one line.** In PowerShell, `curl` is an alias for a different tool and fails with `Cannot bind parameter 'Headers'`. The `\` line breaks don't work there either, and the quotes inside the JSON need a backslash. Git Bash needs no change. Every `curl` command below has both forms.

**1. Is it alive.** Real output:

```powershell
curl.exe -X POST http://127.0.0.1:5000/ping -H "Content-Type: application/json" -d '{\"message\": \"hello\"}'
```

```bash
curl -X POST http://127.0.0.1:5000/ping -H "Content-Type: application/json" -d '{"message": "hello"}'
```

```json
{"ok": true, "service": "provenance-guard", "you_sent": "hello"}
```

**2. Health.** `curl http://127.0.0.1:5000/health` returns, before the first submit:

```json
{"detector_loaded": false, "detector_model": "gpt2", "log_entries": 1809, "ok": true, "rate_limiting": true}
```

`log_entries` is not zero because the repository ships with the log from earlier sessions.

**3. Submit text.** Real output, 7.4 s for this first one because it loads the model:

```powershell
curl.exe -X POST http://127.0.0.1:5000/submit -H "Content-Type: application/json" -d '{\"text\": \"We missed the last train, so we walked home along the canal.\", \"creator_id\": \"me\"}'
```

```bash
curl -X POST http://127.0.0.1:5000/submit -H "Content-Type: application/json" -d '{"text": "We missed the last train, so we walked home along the canal.", "creator_id": "me"}'
```

```json
{"confidence": 0.5507, "content_id": "01c51c02-050f-46a4-9baf-c6f1accbe49b", "degraded": false, "guess": "unsure", "label": "We couldn't tell either way. This piece could have been written by a person or by AI — treat this result as inconclusive, not as an accusation.", "model_score": 0.4125, "style_score": 0.7222}
```

Later requests took 0.3 to 3 s. The response always has `content_id`, `guess`, `confidence`, `label`, both signal scores, and `degraded`.

**4. Appeal a decision** (use a real `content_id` from step 3):

```bash
curl -X POST http://127.0.0.1:5000/appeal -H "Content-Type: application/json" -d '{"content_id": "<id from step 3>", "reasoning": "I wrote this myself."}'
```

```json
{"content_id": "01c51c02-050f-46a4-9baf-c6f1accbe49b", "message": "Your appeal has been recorded and will be reviewed.", "status": "under_review"}
```

**5. Bad input gets a 400, not a crash.** An empty `text` returns `{"error": "invalid_request", "message": "text is required and must be a non-empty string."}` in about 20 ms. Fewer than 5 words gives `"Text needs at least 5 words that contain letters."`

**6. The rate limit.** Six requests a minute per `creator_id`. Eight quick requests from one gave `200 200 200 200 200 200 429 429`.

---

## The logs

Two files in `logs/`, both committed, both appended to on every run:

| File | What it records | Written by |
|---|---|---|
| `logs/audit.jsonl` | Decisions, appeals and rejections, in a fixed shape | `audit.py` |
| `logs/runs.jsonl` | **Every `/submit` request**, including rejected, rate-limited, degraded and crashed ones: input, output, duration, CPU time, per-signal time, the settings in force | `runlog.py` |

Read the run log back:

```bash
python runlog.py --last 20      # a table of recent runs
python runlog.py --failures     # only runs that did not end in a plain decision
python runlog.py --json         # the raw records
```

`GET /log` serves the audit log as JSON. Both files already hold earlier sessions, so filter by `creator_id` or timestamp to find your own.

### A real session, as logged

This is the committed run record: six entries from the clean-checkout test of this very page (a fresh clone of commit `cab44bb`, a fresh environment, and an empty model cache), pasted from `logs/runs.jsonl` exactly as written. In order: the first request after start (the model loads), a second, a rejected input, one of a burst, the first refused by the rate limiter, and one with the model deliberately broken.

```json
{"timestamp": "2026-11-09T03:39:39.066+00:00", "run_id": "dbc8ba3bfca144b0b77e294d5fc4ba45", "content_id": "01c51c02-050f-46a4-9baf-c6f1accbe49b", "route": "/submit", "status_code": 200, "outcome": "decided", "creator_id": "walk_a", "input": {"type": "str", "chars": 60, "words": 12, "preview": "We missed the last train, so we walked home along the canal."}, "output": {"status_code": 200, "guess": "unsure", "confidence": 0.5507, "label": "We couldn't tell either way. This piece could have been written by a person or by AI — treat this result as inconclusive, not as an accusation.", "error": null, "message": null}, "duration_ms": 7395.2, "cpu_ms": 6171.9, "model_ms": 7295.0, "style_ms": 1.2, "cold_start": true, "model_score": 0.4125, "style_score": 0.7222, "combined_score": 0.5674, "degraded": false, "degraded_reason": null, "exception": null, "config": {"detector_model": "gpt2", "human_threshold": 0.35, "ai_threshold": 0.65, "weight_model": 0.5, "weight_style": 0.5}}
{"timestamp": "2026-11-09T03:39:42.652+00:00", "run_id": "1f747fefc6c943b2a17d96ddf3f7493b", "content_id": "46bc9d6d-bbd9-4132-875d-37ef6a8d3701", "route": "/submit", "status_code": 200, "outcome": "decided", "creator_id": "walk_b", "input": {"type": "str", "chars": 252, "words": 31, "preview": "Artificial intelligence is transforming the way organizations operate in the modern world. By leveraging advanced algorithms, businesses can streamline their processes, enhance productivity, and deliver more personalized experiences to their customers."}, "output": {"status_code": 200, "guess": "ai", "confidence": 0.1737, "label": "We think this was probably written by AI, or with heavy AI assistance.", "error": null, "message": null}, "duration_ms": 3243.6, "cpu_ms": 3312.5, "model_ms": 3217.2, "style_ms": 16.0, "cold_start": false, "model_score": 0.84, "style_score": 0.5817, "combined_score": 0.7108, "degraded": false, "degraded_reason": null, "exception": null, "config": {"detector_model": "gpt2", "human_threshold": 0.35, "ai_threshold": 0.65, "weight_model": 0.5, "weight_style": 0.5}}
{"timestamp": "2026-11-09T03:39:42.911+00:00", "run_id": "24b92c6caca1498faf12c2105324f59e", "content_id": null, "route": "/submit", "status_code": 400, "outcome": "rejected", "creator_id": "walk_c", "input": {"type": "str", "chars": 0, "words": 0, "preview": ""}, "output": {"status_code": 400, "guess": null, "confidence": null, "label": null, "error": "invalid_request", "message": "text is required and must be a non-empty string."}, "duration_ms": 9.3, "cpu_ms": 15.6, "model_ms": null, "style_ms": null, "cold_start": null, "model_score": null, "style_score": null, "combined_score": null, "degraded": false, "degraded_reason": null, "exception": null, "config": {"detector_model": "gpt2", "human_threshold": 0.35, "ai_threshold": 0.65, "weight_model": 0.5, "weight_style": 0.5}}
{"timestamp": "2026-11-09T03:39:45.858+00:00", "run_id": "284edbbe770141f2ad3c5b62faddba08", "content_id": "fef3aab2-25cd-49d1-a88a-98fd49bec606", "route": "/submit", "status_code": 200, "outcome": "decided", "creator_id": "walk_burst", "input": {"type": "str", "chars": 60, "words": 12, "preview": "We missed the last train, so we walked home along the canal."}, "output": {"status_code": 200, "guess": "unsure", "confidence": 0.5507, "label": "We couldn't tell either way. This piece could have been written by a person or by AI — treat this result as inconclusive, not as an accusation.", "error": null, "message": null}, "duration_ms": 1163.3, "cpu_ms": 2218.8, "model_ms": 1157.8, "style_ms": 0.1, "cold_start": false, "model_score": 0.4125, "style_score": 0.7222, "combined_score": 0.5674, "degraded": false, "degraded_reason": null, "exception": null, "config": {"detector_model": "gpt2", "human_threshold": 0.35, "ai_threshold": 0.65, "weight_model": 0.5, "weight_style": 0.5}}
{"timestamp": "2026-11-09T03:39:50.592+00:00", "run_id": "a725e1343021476f95e465c7ab0a9491", "content_id": null, "route": "/submit", "status_code": 429, "outcome": "rate_limited", "creator_id": "walk_burst", "input": {"type": "str", "chars": 60, "words": 12, "preview": "We missed the last train, so we walked home along the canal."}, "output": {"status_code": 429, "guess": null, "confidence": null, "label": null, "error": "rate_limited", "message": "Too many submissions. Try again shortly."}, "duration_ms": 188.6, "cpu_ms": 93.8, "model_ms": null, "style_ms": null, "cold_start": null, "model_score": null, "style_score": null, "combined_score": null, "degraded": false, "degraded_reason": null, "exception": null, "config": {"detector_model": "gpt2", "human_threshold": 0.35, "ai_threshold": 0.65, "weight_model": 0.5, "weight_style": 0.5}}
{"timestamp": "2026-11-09T03:40:16.065+00:00", "run_id": "98d934ec70e74913b4f855dcd1ef3ee0", "content_id": "8bea730b-369c-4ebf-9168-8ac762dce0b1", "route": "/submit", "status_code": 200, "outcome": "degraded", "creator_id": "walk_degraded", "input": {"type": "str", "chars": 60, "words": 12, "preview": "We missed the last train, so we walked home along the canal."}, "output": {"status_code": 200, "guess": "unsure", "confidence": 0.0, "label": "We couldn't tell either way. This piece could have been written by a person or by AI — treat this result as inconclusive, not as an accusation. Only part of our check could run, so this is less certain than usual.", "error": null, "message": null}, "duration_ms": 766.7, "cpu_ms": 453.1, "model_ms": 756.8, "style_ms": 0.4, "cold_start": true, "model_score": null, "style_score": 0.7222, "combined_score": 0.7222, "degraded": true, "degraded_reason": "DetectorUnavailable: Couldn't load 'does-not-exist-xyz': does-not-exist-xyz is not a local folder and is not a valid model identifier listed on 'https://huggingface.co/models' If this is a private repository, make sure to pass a token having permission to this repo either by logging in with `hf auth", "exception": null, "config": {"detector_model": "does-not-exist-xyz", "human_threshold": 0.35, "ai_threshold": 0.65, "weight_model": 0.5, "weight_style": 0.5}}
```

The matching `logs/audit.jsonl` entries: the first two decisions, the appeal that moved the first to `under_review`, and the degraded decision.

```json
{"timestamp": "2026-11-09T03:39:39+00:00", "content_id": "01c51c02-050f-46a4-9baf-c6f1accbe49b", "creator_id": "walk_a", "guess": "unsure", "model_score": 0.4125, "style_score": 0.7222, "combined_score": 0.5674, "label": "We couldn't tell either way. This piece could have been written by a person or by AI — treat this result as inconclusive, not as an accusation.", "status": "decided"}
{"timestamp": "2026-11-09T03:39:44+00:00", "content_id": "01c51c02-050f-46a4-9baf-c6f1accbe49b", "creator_id": "walk_a", "event": "appeal", "status": "under_review", "reasoning": "I wrote this myself."}
{"timestamp": "2026-11-09T03:39:42+00:00", "content_id": "46bc9d6d-bbd9-4132-875d-37ef6a8d3701", "creator_id": "walk_b", "guess": "ai", "model_score": 0.84, "style_score": 0.5817, "combined_score": 0.7108, "label": "We think this was probably written by AI, or with heavy AI assistance.", "status": "decided"}
{"timestamp": "2026-11-09T03:40:16+00:00", "content_id": "8bea730b-369c-4ebf-9168-8ac762dce0b1", "creator_id": "walk_degraded", "guess": "unsure", "model_score": null, "style_score": 0.7222, "combined_score": 0.7222, "label": "We couldn't tell either way. This piece could have been written by a person or by AI — treat this result as inconclusive, not as an accusation. Only part of our check could run, so this is less certain than usual.", "status": "decided", "degraded": true, "degraded_reason": "DetectorUnavailable: Couldn't load 'does-not-exist-xyz': does-not-exist-xyz is not a local folder and is not a valid model identifier listed on 'https://huggingface.co/models' If this is a private repository, make sure to pass a token having permission to this repo either by logging in with `hf auth"}
```

The whole session as a table (`python runlog.py --last 21`, abridged to the session):

```
time (UTC)          status outcome           ms   model  style  input / why
---------------------------------------------------------------------------
2026-11-09 03:39:39    200 decided         7395    7295      1  We missed the last train, so we wa
2026-11-09 03:39:42    200 decided         3244    3217     16  Artificial intelligence is transfo
2026-11-09 03:39:42    400 rejected           9       -      -  text is required and must be a non-empty string.
2026-11-09 03:39:43    400 rejected           6       -      -  Text needs at least 5 words that contain letters.
2026-11-09 03:39:45    200 decided         1163    1158      0  We missed the last train, so we wa
2026-11-09 03:39:46    200 decided          551     453      0  We missed the last train, so we wa
2026-11-09 03:39:47    200 decided          795     775      0  We missed the last train, so we wa
2026-11-09 03:39:49    200 decided          570     531      1  We missed the last train, so we wa
2026-11-09 03:39:49    200 decided          301     285      0  We missed the last train, so we wa
2026-11-09 03:39:50    200 decided          409     391      0  We missed the last train, so we wa
2026-11-09 03:39:50    429 rate_limited     189       -      -  Too many submissions. Try again shortly.
2026-11-09 03:39:50    429 rate_limited      10       -      -  Too many submissions. Try again shortly.
2026-11-09 03:40:16    200 degraded         767     757      0  DetectorUnavailable: Couldn't load 'does-not-exist-xyz': doe
```

---

## Degraded mode: when the model can't run

If signal one (the local gpt2 model) fails, `/submit` does not return a 500. It answers from the style signal alone and says so:

| What you see | Normal | Degraded |
|---|---|---|
| Response `degraded` | `false` | `true` |
| Response `model_score` | a number | `null` |
| `guess` | `human`, `unsure` or `ai` | `human` or `unsure` only. It never says `ai` on one signal |
| `confidence` | as computed | halved (`config.DEGRADED_CONFIDENCE_FACTOR`) |
| `logs/audit.jsonl` entry | the nine fields | the nine fields plus `degraded: true` and `degraded_reason` |

It covers failures that raise an error: a model never downloaded, an out-of-memory error, a load that fails. A call that hangs is not covered.

**See it happen.** Point the service at a model that doesn't exist. PowerShell:

```powershell
$env:AI201_DETECTOR_MODEL = "does-not-exist-xyz"
python app.py
```

Git Bash: `AI201_DETECTOR_MODEL=does-not-exist-xyz python app.py`. Submit anything. Real output (0.8 s):

```json
{"confidence": 0.0, "content_id": "8bea730b-369c-4ebf-9168-8ac762dce0b1", "degraded": true, "guess": "unsure", "label": "We couldn't tell either way. This piece could have been written by a person or by AI — treat this result as inconclusive, not as an accusation. Only part of our check could run, so this is less certain than usual.", "model_score": null, "style_score": 0.7222}
```

Note that the style score, 0.7222, would normally have been called `ai`. **Clear the variable afterwards** (`Remove-Item Env:AI201_DETECTOR_MODEL`), or the next server you start is still broken.

---

## Tests and checks

| Command | What it does | Needs the server? |
|---|---|---|
| `python test.py` | Checks your environment | no |
| `python -m unittest discover -s tests` | All 49 tests | no |
| `python tests/test_degraded.py` | Degraded-mode tests, as a readable report | no |
| `python tests/test_runlog.py` | Run-log tests, as a readable report | no |
| `python tools/failure_check.py` | Criterion 9.1: nine kinds of failure, one record each | no |
| `python tools/degraded_check.py --expect degraded` | Criterion 9.2 (start the server with the model broken first) | yes |
| `python tools/reconcile_check.py` | Criterion 9.3: 40 concurrent requests, both logs compared | starts its own |
| `python tools/measure_cost.py` | Cost of one run: cold start and warm runs | starts its own |
| `python tools/startup_check.py` | Preload on versus off, in one session | starts its own |
| `python tools/run_unit9.py --label after` | All five unit 9 criteria, three separate runs, saved to `results/unit9_after/` | starts its own |
| `python tools/demo_session.py` | One of each kind of outcome, into the run log | starts its own |
| `python run_attacks.py --set attack_set` | The 56-row attack set | yes |
| `python run_attacks.py --flood 15` | Push past the rate limit and print the status codes | yes |
| `python run_eval.py --label before` | The five original criteria, three trials | yes |
| `python appeal_check.py` | Criterion 4: ten submit-and-appeal pairs, three trials | yes |

Run the tools that talk to a server one at a time and not alongside each other: they share one rate limiter and one CPU, so overlapping them gives spurious 429s and distorts every timing.

---

## Why not hosted

Everything a host would have to keep in memory, measured:

| What has to be in memory | Measured |
|---|---|
| The service with the model loaded | about **490 MB** (working set, 482 to 503 MB) |
| `torch` and the Python packages | part of that figure; the install is large |
| **A free tier gives you** | **512 MB** |

That leaves essentially nothing for requests. A free host also has no persistent disk, so the 526 MB model would download again after every idle spin-down, and the first request after a restart takes seconds to tens of seconds. There is no setting that fixes this, so this system takes Path B: local, started by `python app.py`, with its record in `logs/`. What running it costs is worked out in the README under *What It Costs*.

---

## What I tested, and how

I followed this page from a **fresh clone** of commit `cab44bb` in an empty folder, with a new virtual environment, and with the home folder pointed at an empty directory so that the model really was downloaded (otherwise `test.py` finds the copy already on my machine, because it only looks in `~/.cache/huggingface`). Windows 11, Python 3.11.9.

What was run: `pip install -r requirements.txt` (387 s), `python test.py` (WARN, as above), `python detector.py` (28 s, 526 MB), `python app.py` (answered `/health` after 18 s), then `/ping`, `/health`, two submits, two bad inputs, an appeal, a burst of eight, a second start with the model broken and one request to it, `python runlog.py`, and the 49 tests (all pass). The log lines above are from that session.

What I did **not** test: macOS or Linux; Python 3.12 or 3.13; the `gunicorn` command (it does not run on Windows, and this system does not use it); and the PowerShell `curl.exe` forms and `Activate.ps1` are noted below with what I found.

**PowerShell, tested separately.** In a real PowerShell session, `.venv\Scripts\Activate.ps1` activated the environment (`python` then resolved to the venv's), and the two `curl.exe` commands above, copied as written, returned the same responses (that start-up took 60 s). My session's execution policy allowed scripts, so the common Windows error *running scripts is disabled on this system* was not exercised. If you meet it, `Set-ExecutionPolicy -Scope Process Bypass` allows scripts for that one window; that is standard Windows behaviour, and not something I needed or tested.

---

## When something goes wrong

| What you see | What it means |
|---|---|
| `Cannot bind parameter 'Headers'` | PowerShell's `curl` is a different tool. Use `curl.exe`, on one line |
| `Address already in use`, or requests that ignore your changes | Another server holds the port. Stop it, or set `PORT` |
| It takes 10 to 20 s (sometimes a minute) to start answering | The deliberate preload. `AI201_PRELOAD=0` skips it |
| The first `/submit` takes several seconds | The model loads on the first request. `/health` shows `detector_loaded` become `true` |
| `[WARN] Detector model` in `test.py` | Run `python detector.py` once |
| `test.py` says the model is downloaded but it is not | `test.py` only looks in `~/.cache/huggingface`. If you set `HF_HOME`, it will not see it |
| `DetectorUnavailable` in a log entry, `degraded: true` in a response | The model could not load. See Degraded mode. Check `AI201_DETECTOR_MODEL` is unset |
| A `UserWarning` about symlinks, and a note about `hf_xet` | Harmless on Windows |
| `429` | The limit is 6 a minute per `creator_id`. Wait a minute, or change `RATE_LIMIT_PER_MINUTE` in `config.py` |
| `GET /health` says `detector_loaded: false` | Expected until the first successful submit |

---

## Where everything lives

| Path | What it is |
|---|---|
| `app.py` | The service: `/ping`, `/health`, `/log`, `/submit`, `/appeal`, and the run-log hooks |
| `detector.py` | Signal one: the local model, and the start-up preload |
| `stylometry.py` | Signal two: sentence shape, vocabulary variety, punctuation |
| `scoring.py` | `combine_signals`, `score_to_label`, and the degraded-mode label |
| `audit.py`, `runlog.py` | The two logs |
| `config.py` | Every setting: thresholds, weights, rate limits, the model, preload |
| `criteria.md` | The criteria, 1 to 7 and 9.1 to 9.5, with the target and the reason for each |
| `tests/` | The automated tests |
| `tools/` | Checks and measurements: failure, degraded, reconcile, cost, start-up, the unit 9 runner |
| `run_attacks.py`, `run_eval.py`, `scenarios.py`, `appeal_check.py` | The unit 8 tooling |
| `logs/` | `audit.jsonl` and `runs.jsonl`. Committed on purpose |
| `results/` | Every run's report, including `unit9_before/` and `unit9_after/`. Committed on purpose |
| `README.md` | The write-up |

**A note on committing.** `logs/` and `results/` are deliberately not in `.gitignore`: they are the evidence. Do not delete and recreate this repository, and do not rewrite its history.
