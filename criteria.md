# Acceptance criteria — Provenance Guard

Five criteria that say what "working" means for this service, written in unit 7
**before** you built it.

**All five are yours.** None are given.

An acceptance criterion names a number or something plainly observable. *"The
detector is accurate"* is an opinion — and perfect AI detection isn't possible
anyway, so it's an opinion about something nobody can deliver. *"Of 10 pieces I
wrote myself, at most 1 is labelled high-confidence AI"* is a criterion.

Under each, write a sentence or two on **why that target**. *"I allow at most 1
false positive in 10 because on a writing site a wrong accusation costs more
than a missed detection"* is a real answer.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

---

## Pick numbers you can defend

**Cover at least three of these five areas.** They're prompts, not a form.

| Area | A question it could answer |
|---|---|
| False positives | How often may a human's writing get called AI? |
| Score spread | How far apart should clearly-AI and clearly-human text score? |
| Label coverage | Is every one of your three labels actually reachable? |
| The appeal path | Does an appeal always change status and always get recorded? |
| Bad input | What happens when `text` is missing, empty, or enormous? |

Two things worth knowing before you pick numbers:

- **The expensive mistake is one-sided.** Missing some AI text costs the site a
  little. Accusing a real writer costs that person a lot. A criterion that
  treats both errors as equally bad is describing a system nobody would ship.
- **Unit 8 tests across three trials, and the target has to hold across all
  three.** Your first signal runs a model, so identical input can score
  differently twice. A target of "at most 1 in 10" against trials of 2, 1, 2 is
  a **miss**.

---
## 1. False positives

Of 10 plainly-written human paragraphs I submit (short sentences, ordinary
vocabulary, no attempt to sound formal), at most 1 scores high-confidence AI
— and that holds in every one of the 3 trials, not just on average.

**Why this target:** plain writing is signal one's named blind spot — low
perplexity rewards "common words, short ordinary sentences" regardless of who
wrote them. On a writing site, a wrong accusation costs the writer far more
than a missed detection costs the site, so this is the error I budget
tightest. "At most 1 in 10" across all 3 trials, not 1-in-10-on-average, is
the point: signal one is non-deterministic run to run, and a target that only
holds on a lucky trial isn't a target.

---

## 2. Score spread

A clearly-AI calibration text and a clearly-human calibration text score at
least 0.4 apart on `combined_score` (read from the audit log entry for each
submission, since the API response doesn't return it), in all 3 trials.

**Why this target:** if the two most obvious cases I can construct land
close together, the combined score isn't doing any separating work no matter
where I later put the thresholds — tuning `HUMAN_THRESHOLD`/`AI_THRESHOLD`
can't fix a combining rule that compresses everything toward the middle.
0.4 is deliberately short of the full 0–1 range: I'd rather catch a weak
combining rule early than pick a number so easy a flat average always clears
it.

---

## 3. Label coverage

Each of the three labels — human, unsure, AI — is actually produced by at
least one of my four Milestone 4 calibration inputs (clearly AI, clearly
human, plain conventional human, lightly-edited AI), in at least 2 of the 3
trials.

**Why this target:** a label no input can reach is dead code in
`score_to_label` — config.py's own warning is that a weighted average with a
stub style signal traps the combined score in 0.25–0.75, making "human"
unreachable without a model score under ~0.20. "2 of 3 trials" rather than
3 of 3 allows for the model signal's run-to-run noise landing a borderline
input on the wrong side of a threshold once, without letting a label go
untested across every trial.

---

## 4. The appeal path

Of 10 test appeals submitted against valid content_ids, 10 of 10 move the
audit log status to `under_review` and appear as a distinct log entry
alongside (not overwriting) the original decision.

**Why this target:** the appeal is the only thing standing between a wrong
accusation and nothing at all — it has no acceptable failure rate, unlike a
detection signal where some error is inherent. 10 of 10 rather than "mostly
works" because a silent failure here (a typo'd content_id check, an
overwritten entry) is exactly the kind of bug the project docs call out as
the one that eats an hour and leaves the writer with no record their
challenge was ever heard.

---

## 5. Bad input

Submitting missing `text`, empty-string `text`, and an oversized (50,000+
word) `text` each returns a 4xx response with no server crash and no 5xx, in
every trial.

**Why this target:** a crash on malformed input is one of the most common
real failures in a service like this, and unit 8's attack set is built to
find exactly this gap if it exists. This is an all-or-nothing target — a 5xx
on any of the three inputs, in any trial, is a miss — because an input that
crashes the route doesn't get logged as a rejection the way a clean 4xx does,
and `audit.py`'s own docs warn that an attack showing up only as an absence
is one that can't be diagnosed.

---

## 6. A model failure still gets an answer

With the service started with its model unable to load, 10 submissions
(`python tools/degraded_check.py --expect degraded`) each return a 200 with
`degraded: true` and `model_score: null`, and none returns a 5xx, in every one
of 3 trials.

**Why this target:** the model is a ~550 MB local download and the weakest
point on the bad path. Before this extension, a missing or failed model ended
every `/submit` in a 500. A writer who submits cannot tell whether the service
or their text is the problem, so a failure that is not theirs should still get
an answer. All-or-nothing across the trials, because one 5xx is the failure
this criterion exists to rule out.

---

## 7. A degraded answer never accuses, and always leaves a trace

In the same degraded runs, none of the 30 submissions is labelled `ai`, and
every one has exactly one audit log entry with `degraded: true` and a
`degraded_reason`.

**Why this target:** with only signal two, the shape of the text, the service is
working from the weaker signal, and the README already shows how cheaply it is
fooled. A wrong accusation costs a writer more than a missed detection costs
the site (criterion 1), so one signal never gets to say "ai". The log entry is
the other half: a failure that returned a clean-looking answer and left no
record would be invisible, which is the same absence `audit.py` warns about.

---

## Unit 9 criteria: the extension

Five more, numbered 9.1 to 9.5 so they cannot be confused with 1 to 7 above,
which the eval tooling and the earlier write-up refer to by number. The
extension is degraded mode, failure handling and the structured run log
(`runlog.py`, `logs/runs.jsonl`). Criteria 9.1, 9.2 and 9.3 are about that. 9.4
and 9.5 are about the system underneath, and are here because the new
instrumentation exposed a number that was easy not to look at.

These were written to be missable. Two of them were already known to fail on this
machine when written, and say so. A criterion that cannot fail teaches nothing.

---

## 9.1 No failure goes unrecorded

Nine kinds of failing request are each sent to `/submit`: empty text, text too
short, a control character, `text` missing, a body that is not a JSON object,
text over `MAX_TEXT_CHARS`, a rate-limited request, a model that cannot load,
and a crash inside the route. Each one produces **exactly one** record in
`logs/runs.jsonl` with a non-empty reason (`output.message`, `degraded_reason`
or `exception.message`): 9 of 9, not 8.

**Why this target:** a failure that shows up only as an absence is one nobody
finds. The kind most likely to be missing is the crash. Flask skips
`after_request` for an unhandled error in debug mode, which is the mode this
service runs in by default, so a record written there would silently never
appear. The record is written in `teardown_request` for that reason, and this
criterion is what checks that the choice worked. 9 of 9 because a log that is
complete for eight kinds of failure and blind to the ninth cannot be relied on
for any of them.

**Why not stricter, why not looser:** Looser would be 8 of 9, and the one I would
be tempted to drop is the crash, which is the case this design exists for and
the one that costs most when missing: an unrecorded 500 leaves no evidence at
all except a writer's complaint. "Exactly one" rather than "at least one"
because duplicates would inflate any failure rate read off the log. Stricter
would be more kinds, but the nine are chosen by mechanism, not by branch. A
rejection the route makes itself, a 429 the rate limiter raises before the
route runs, and an unhandled exception all reach the log by different paths,
and the nine cover each path more than once. A tenth kind, such as a
non-string `creator_id`, goes through the same path as rejections already
counted, so it would add a test and not any coverage. The one stricter demand I
cannot meet is a record when the run log itself cannot be written: there is
nowhere to put it, so `runlog.write` reports that to stderr instead.

*How it is run:* `python tools/failure_check.py` triggers each of the nine kinds
on purpose and counts the new records after each one. Six are real bad inputs,
the rate limit is a real burst past the limiter, and two are injected, because a
healthy service cannot be made to fail those ways without changing it: the model
failure, and the crash inside the route, which is raised with Flask's exception
propagation on, as in debug mode. The same exercise is a unit test in
`tests/test_runlog.py`.

---

## 9.2 A degraded answer is quick

With the model unable to load, across 3 trials of 10 requests
(`python tools/degraded_check.py --expect degraded`), the median wall time
recorded in `duration_ms` is at most 1 second and the slowest request at most 3
seconds.

**Why this target:** a service that is hurt should not also be slower. Degraded
mode does less work than a normal run: it skips the model and the long part of
the request. But `detector._load()` caches nothing when a load fails, so every
request retries it, and if that retry reaches the network each degraded answer
could wait on a failed lookup. A writer would then wait longest exactly when
something is broken. Fast failure is the point of falling back instead of
raising. The bound is deliberately well under a normal warm run (the
measurement below puts that median at about 2.6 seconds) because the fallback
has to be clearly better than waiting for the model, not merely equal to it.

**Why not stricter, why not looser:** Looser, such as the 2.6 seconds a normal
warm run takes, would let the fallback be as slow as the thing it replaces, so a
writer would wait longest exactly when the service is broken. A looser maximum
such as 10 seconds would also hide what this criterion is for, a slow first
request. Stricter is limited by the design. Each degraded request still
attempts the model load, because a failed load is not cached, and the second
degraded request in my demo session took 0.7 seconds doing that, so a median of
1 second sits just above what the retry costs. Going lower would mean
remembering the failure, and then a service started before the model finished
downloading would never recover without a restart; I would rather keep the
retry. The 3-second maximum is three times the median. It is not tighter
because this machine's timings varied 35-fold on identical input, so a tighter
maximum would mostly measure the laptop, and any miss has to be diagnosed as
the code or the machine before it counts.

*How it is run:* start the service with `AI201_DETECTOR_MODEL=does-not-exist-xyz`
so the model really cannot load, then `python tools/degraded_check.py --expect
degraded --trials 3`: 3 trials of 10 requests, so 30 durations, from a freshly
started server each time so the slow first request is included. Median and
maximum are read from `duration_ms` in `logs/runs.jsonl`.

---

## 9.3 The two logs agree

Forty requests, a mix of valid and invalid text, are sent to the live service
from 8 clients at once. Afterwards `logs/runs.jsonl` holds **exactly 40**
records for them, every line is valid JSON, and for each request that became a
decision the run record and the audit entry agree on `content_id`, `guess`,
`model_score` and `style_score`, 40 of 40 where applicable.

**Why this target:** the run log and the audit log are written separately, one
in the route and one after it, so they can drift. A crash between the two would
leave one without the other. A log that disagrees with the audit log is worse
than no log, because it looks like evidence. Concurrency is the other
risk: both are append-only files written by a threaded server, and interleaved
writes are the usual way a JSON-lines file ends up with a corrupt line. "Exactly
40" rather than "about 40" because a lost record is the very failure 9.1 is about.

**Why not stricter, why not looser:** Looser, such as "about 40" or "at least
95%", is not available for a log. Unlike the detection signal, writing a line
has no inherent error rate, so any missing record is a bug, and a log that is
95% complete does not say which 5% is gone. The agreement check is exact for
the same reason: both logs are written from the same variables, so a
difference of even 0.01 means a different code path, not rounding. Stricter
would be more load, but 40 requests from 8 clients is already more concurrency
than this system sees. It serves one writer at a time on one machine, and its
own limiter allows 6 requests a minute per `creator_id`, which is why the 40
are spread across creator ids. More clients would mostly test Flask's
development server. What this does not cover is more than one server process:
`runlog.py` guards the file with a lock that exists only inside one process, so
several workers (under gunicorn, for example) would be unprotected. That is out
of scope while the system runs locally as one process.

*How it is run:* `python tools/reconcile_check.py` starts the service and sends
40 requests from 8 clients at once (3 valid texts and 2 bad inputs each), then
counts the run records for them, checks every line of the run log, and compares
each decision's run record with its audit entry.

---

## 9.4 A writer does not wait long

On the warm path, 90% of runs finish in **5 seconds or less** of wall time and
use **3 seconds or less** of CPU, over at least 30 warm runs of one text
(`python tools/measure_cost.py`, the spread section of its report).

**Why this target:** the model is local, so the cost of a run is the writer's
wait. RUNNING.md says warm submissions take "a second or two", and 5 seconds at
the 90th percentile is 2 to 3 times that, which is generous. A mean would hide
what matters here, which is the slow runs, so the target is a percentile.

**Why not stricter, why not looser:** Looser, such as the mean or the median,
is the trap: the measured median is 2.6 seconds, which passes any reasonable
limit, while one run in ten took 20 seconds or more. A writer's experience of
this system is its slow runs. A looser time such as 10 seconds would be five
times what RUNNING.md promises. Stricter, such as the 99th percentile or 2
seconds, is limited by the sample: with 30 runs the 99th percentile is the
single slowest run, so one outlier decides the result, and 2 seconds is what
the quiet runs achieve (0.3 to 1.4 s in the demo session) but not what this
laptop holds. The stakes also set how strict to be. A run that takes 8 seconds
instead of 2 costs a writer some patience, where a wrong label (9.5) costs
them an accusation. That is why this one is a percentile with room in it and
9.5 is a count with none to spare. The CPU bound is separate because CPU is
what a host would meter: 3 seconds is about 1.5 times the measured median of
1.9 seconds.

*How it is run:* `python tools/measure_cost.py --launches 1 --runs 30`: a fresh
launch and 30 warm runs of one text, with nothing else running. The 90th
percentiles are read from `duration_ms` and `cpu_ms` in `logs/runs.jsonl`. Thirty
is the fewest runs for which a 90th percentile is more than a single data point.

*Result, added later:* it held in all six unit 9 runs (90th percentile 0.5 to 1.5 s
wall and 1.4 to 2.0 s CPU), so it is MET. That is not what the "known to fail"
paragraph above predicted. That paragraph describes the first measurement, whose
slow tail did not reproduce. I believe it was the machine, but I did not identify
what else was running, so the prediction above is left as written.

**Known to fail when written.** The 30-run measurement on this machine
(`results/cost_2026-11-08_1812.md`) gave a median of 2.6 s but a 90th percentile
of 20.9 s wall and 5.2 s CPU, with the slowest run 35 times the fastest on
identical input. The slow runs cluster late in each launch, and CPU time for the
same work also rose from about 1.5 s to 5 to 6 s. This criterion starts out
**missed**, and the work is finding out whether that is the laptop, the model or
the service, not moving the number.

---

## 9.5 Plain human writing is not accused

Of the eight human-written texts in the attack set that stand in for people at
risk of a false accusation (FP01 to FP08), **at most 2** are labelled
high-confidence AI, in every one of 3 trials.

**Why this target:** this is the failure the whole project is about, and the one
I have so far chosen not to fix. A wrong accusation costs a writer far more
than a missed detection costs the site, and the writers this signal is most
likely to accuse are the ones with the least room to argue back. Criterion 1 is
met, but only because my own paragraphs are longer and more uneven than the
plain writing it was written about, and I said so in the README. This criterion
uses texts I did not pick to pass, so it cannot be met by my choice of examples.
Two of eight rather than zero because some plain, formal human writing really is
close to model output and I would rather say that than promise what two weak
signals cannot do.

**Why not stricter, why not looser:** Stricter, 0 of 8, would mean raising
`AI_THRESHOLD` to about 0.76. The README already works through this: that clears
all six accused texts but moves my clearly-AI calibration text (combined score
0.7364) into "unsure", so the AI label would only be reachable for text more
extreme than anything I tested, which would break criterion 3. Zero is the right
aim and the wrong number for two signals that measure predictability and
sentence shape, not authorship. Looser, such as 4 of 8, would accept accusing
half of the plain and formal writers this signal is known to mistake for a
machine, and the cost of each is a person told their own work is machine-made
with only the appeal to answer back. Even the 2 I chose is one accusation in
four on this kind of writing. It is the strictest number I can defend without
losing the AI label, not one I consider acceptable. It is a count out of 8
rather than a percentage because 8 texts cannot support a rate, and each of
them is a person.

*How it is run:* `python run_attacks.py --set attack_set --family false_positive`
against a running service. The number is how many of FP01 to FP08 come back as
`ai`, taken from the report it writes.

All five are run, three separate times from scratch, by `python
tools/run_unit9.py`, which saves every step's output and fills in the run log. The
set was run twice, with `--label before` and `--label after`, and the logs are
`results/unit9_run_log_before.md` and `results/unit9_run_log_after.md`.

**Known to fail when written.** In the 2026-11-08 regression attack run, 6 of
the 8 (FP02 to FP07) come back as AI; only FP01 and FP08 are held at "unsure".
It starts out **missed**. The trade I have written down, raising `AI_THRESHOLD`
toward 0.76, is the change this criterion would be used to judge, and it also
lets some AI text through as "unsure", which is not counted here and must be
reported next to it.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 8 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath, like this:

         ## 2. Uncertain cases land in the unsure band

         The system handles uncertain cases well.

         **Why this target:** ...

         > **Revised in unit 8:** Text I judged borderline scores between
         > 0.4 and 0.6 in at least 4 of 5 cases.
         >
         > **Why revised:** "well" gave me nothing to check. I couldn't
         > reach a verdict from it at all.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "At most 1 of 10 of my own pieces flagged as AI" → "at most 3
            of 10", because 1 of 10 turned out to be hard.

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
