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
least 0.4 apart on the combined score, in all 3 trials.

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
