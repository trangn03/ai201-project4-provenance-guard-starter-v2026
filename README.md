# Provenance Guard

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first.**
>
> Once `python test.py` passes, in one terminal:
>
> ```bash
> python app.py
> ```
>
> and in another:
>
> ```bash
> curl -X POST http://127.0.0.1:5000/ping \
>   -H "Content-Type: application/json" \
>   -d '{"message": "hello"}'
> ```
>
> That's a web service. Something sent it text and it sent something back.
> Everything this unit is filling in the middle.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     Unit 7 asks for the first five sections. Unit 8 adds the five below.

     Everything is pasted as TEXT. A pasted curl response gets full credit;
     a picture of your terminal gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 7 — THE BUILD ═══════════════════════ -->

## What This Does

<!-- The path a submission takes, from arriving to the label a reader sees.
     Six or seven steps — this is the trace you wrote in Milestone 1. -->

1. **`app.py` `/submit`** pulls `text` and `creator_id` out of the JSON body.
2. **`detector.py` `model_signal(text)`** runs the text through a local GPT-2
   instance and turns its perplexity into a 0–1 "AI-likely" score (signal one).
3. **`stylometry.py` `style_signal(text)`** independently measures the shape
   of the text — sentence-length spread, vocabulary variety, punctuation
   density — and produces a second 0–1 "AI-likely" score (signal two).
4. **`scoring.py` `combine_signals(model_score, style_score)`** merges the two
   independent scores into one 0–1 score, using the weights in `config.py`.
5. **`scoring.py` `score_to_label(score)`** maps that combined score to a
   `(guess, label_text)` pair, using the thresholds in `config.py`. `app.py`
   separately derives `confidence` from how far the score sits past the
   threshold it crossed (or past the unsure band's midpoint).
6. **`audit.py` `log_decision(...)`** appends one line to `logs/audit.jsonl`
   with all nine required fields, regardless of what's returned to the caller.
7. **`app.py`** returns `content_id`, `guess`, `confidence`, `label`,
   `model_score`, and `style_score` to the caller.

---

## Signals and Scoring

<!-- For each signal: what property it measures, why that might differ between
     human and AI writing, and WHAT IT CAN'T SEE.

     The blind spot is not optional. If you can't name it you don't understand
     the signal yet — and unit 8's attack set is built out of blind spots. -->

### Signal one — the model signal

**What it measures:** how predictable each next token is to a local GPT-2
model, averaged over the text as perplexity, then mapped through a logistic
curve onto 0–1 (lower perplexity → higher AI score).

**Why that might differ between human and AI writing:** a language model
writes by repeatedly picking a likely next token, so its own output tends to
be easy for a model to predict. Human writing is noisier — odd word choices,
digressions, the specific rather than the typical — which reads as higher
perplexity.

**What it can't see:** who actually wrote the text — only how surprising the
words are against gpt2's training distribution. It can't tell "generated"
apart from "plain." Someone writing simply on purpose (a second-language
writer, a younger writer, anyone being deliberately clear) scores just as
AI-like as a model would. It also runs backwards on register: dense, ornate
prose scores *human* — including AI-generated ornate prose — because rare
words are exactly what trips the model up.

### Signal two — the style signal

**What it measures:** three shape statistics with no semantic content —
whether sentence length varies or marches in lockstep, how much vocabulary
repeats, how much and what kind of punctuation appears.

**Why that might differ between human and AI writing:** generated text tends
toward even, mid-length sentences and a narrower vocabulary band, because
that's what "most likely next word" produces on average. Human writing is
lumpier — a three-word sentence next to a forty-word one, idiosyncratic
punctuation habits that vary writer to writer.

**What it can't see:** meaning, at all — it only sees the shape the
characters make on the page. It can't tell a text that's naturally uniform
from one deliberately reshaped to look varied: typos, sentence-splitting, a
pasted quotation all move the score without touching what the text says. It
also can't catch AI generation that's been prompted to vary its own sentence
length and vocabulary — the content can still be machine-written while the
shape reads as human.

### The combining rule

<!-- Write the rule in words, then give the numbers. What happens when the two
     signals disagree? -->

**The rule:** a weighted average of `model_score` and `style_score` is the
base case. But when the two disagree by more than a set threshold, a flat
average isn't trusted to land honestly on "unsure" — the result is pulled
halfway toward whichever signal read more human. A wrong accusation costs a
writer more than a missed detection costs the site (see `criteria.md`), so
when two independent methods split sharply, that split is a reason to lean
toward the writer, not a reason to average the disagreement away.

**The numbers:** `WEIGHT_MODEL_SIGNAL = 0.5`, `WEIGHT_STYLE_SIGNAL = 0.5`,
`SIGNAL_DISAGREEMENT_THRESHOLD = 0.35` (all in `config.py`).

**Where it lives:** `scoring.py::combine_signals`

<!-- ⚠️ The grader checks your code against that line. If your rule lives
     somewhere else, say where. -->

**A case where my two signals split, and what my rule does with it:** a text
with ordinary vocabulary but genuinely varied, idiosyncratic sentence
structure (uneven sentence lengths, a semicolon, an em dash) scored
`model_score = 0.7270` (moderate perplexity reads as somewhat AI-like) and
`style_score = 0.2290` (the shape reads clearly human — exactly what the
model signal can't see). The disagreement is 0.498, above the 0.35
threshold. A flat average would land at 0.478 — barely inside "unsure." The
disagreement rule instead pulls it to 0.3535, right at the edge of
high-confidence human, because the style signal is picking up concrete,
checkable structure that the model signal has no way to notice, and the cost
of being wrong favors trusting that read.

---

## Label Variants

<!-- The exact text of all three labels, as a reader would see them, and the
     score range each covers.

     Write them for someone who has never heard the word "threshold". -->

| Label                 | Score range | The exact text a reader sees |
| --------------------- | ----------- | ----------------------------- |
| high-confidence human | 0.00 – 0.35 | "We think this was probably written by a person." |
| unsure                | 0.35 – 0.65 | "We couldn't tell either way. This piece could have been written by a person or by AI — treat this result as inconclusive, not as an accusation." |
| high-confidence AI    | 0.65 – 1.00 | "We think this was probably written by AI, or with heavy AI assistance." |

**Why I worded the "unsure" one this way:**

<!-- It's the hardest of the three. It has to admit uncertainty without
     sounding like an accusation, because the person reading it may well have
     written every word themselves. -->

It names what the system knows (it couldn't tell) instead of what it
suspects (maybe AI). "Treat this result as inconclusive, not as an
accusation" is there on purpose — the plain reading of "unsure" on your own
writing is still "they think I might have used AI," so the sentence has to
say out loud that this isn't a verdict, or a reader has no way to know that
for themselves.

**Confirming all three are reachable:** submitted through the running
service — a plain personal anecdote with contractions and a parenthetical
scored 0.2857 → `human`; a generic, hedging paragraph scored 0.7752 →
`ai`; several genuinely human texts that were less extreme (a single clean
sentence, dense formal prose, casual writing without much punctuation
variety) landed between 0.37 and 0.60 → `unsure`. All three bands fire on
real input, not just on constructed edge cases.

---

## Sample Run

<!-- One submission and one appeal, pasted as text: the request, the response,
     and the log entries. -->

**A submission**

<!-- The response needs content_id, guess, confidence, label, AND both
     signal scores - model_score and style_score. Unit 8's tools read those
     two off the response, so leaving them out costs you next unit's
     diagnostics. -->

```bash
$ curl -X POST http://127.0.0.1:5000/submit \
  -H "Content-Type: application/json" \
  -d '{"text": "My grandmother used to keep a jar of buttons on the windowsill, mismatched and rusted, and I never once saw her sew anything with them.", "creator_id": "writer-1"}'
```

```json
{
  "confidence": 0.1747,
  "content_id": "c1891801-c3aa-4384-ba0c-f5c3cfcbc8c6",
  "guess": "unsure",
  "label": "We couldn't tell either way. This piece could have been written by a person or by AI — treat this result as inconclusive, not as an accusation.",
  "model_score": 0.5675,
  "style_score": 0.68
}
```

**An appeal**

```bash
$ curl -X POST http://127.0.0.1:5000/appeal \
  -H "Content-Type: application/json" \
  -d '{"content_id": "c1891801-c3aa-4384-ba0c-f5c3cfcbc8c6", "reasoning": "I wrote this myself about my own grandmother. It is not AI-generated."}'
```

```json
{
  "content_id": "c1891801-c3aa-4384-ba0c-f5c3cfcbc8c6",
  "message": "Your appeal has been recorded and will be reviewed.",
  "status": "under_review"
}
```

**What the log shows afterwards**

<!-- The original decision is untouched; the appeal sits after it as its own
     entry, same content_id, status moved to under_review — audit.log_appeal
     never overwrites the original. -->

```bash
$ curl "http://127.0.0.1:5000/log?limit=2"
```

```json
{
  "count": 2,
  "entries": [
    {
      "combined_score": 0.6238,
      "content_id": "c1891801-c3aa-4384-ba0c-f5c3cfcbc8c6",
      "creator_id": "writer-1",
      "guess": "unsure",
      "label": "We couldn't tell either way. This piece could have been written by a person or by AI — treat this result as inconclusive, not as an accusation.",
      "model_score": 0.5675,
      "status": "decided",
      "style_score": 0.68,
      "timestamp": "2026-10-28T02:00:15+00:00"
    },
    {
      "content_id": "c1891801-c3aa-4384-ba0c-f5c3cfcbc8c6",
      "creator_id": "writer-1",
      "event": "appeal",
      "reasoning": "I wrote this myself about my own grandmother. It is not AI-generated.",
      "status": "under_review",
      "timestamp": "2026-10-28T02:00:15+00:00"
    }
  ]
}
```

---

## How I Used AI

**Moment 1**

- *What I asked for:* run both signals over four deliberately chosen
  calibration inputs — clearly AI, clearly human, formal human writing, and
  lightly-edited AI — and dig into the components if any score looked
  surprising.
- *What came back:* `formal_human`'s `style_score` (0.4736) looked too
  neutral for dense, distinctive prose. Breaking down the three measures
  separately showed `punctuation_density` at only 0.080 despite the text
  containing a colon and two possessive apostrophes — because
  `_INTERESTING_PUNCTUATION` included a bare `'`, which matches ordinary
  contractions and possessives, not just real quotation marks. It was
  double-counting the single most common punctuation mark in English as if
  it were a rare, personal one.
- *What I changed:* removed `'` from `_INTERESTING_PUNCTUATION` in
  `stylometry.py`, keeping only `;:—()"`. Re-ran all four calibration texts
  to confirm the fix moved the numbers in the direction expected
  (`formal_human`'s punctuation reading dropped to a more honest 0.020) and
  didn't break the two agreement cases.

**Moment 2**

- *What I asked for:* a combining rule for `scoring.py::combine_signals` that
  does something deliberate when the two signals disagree sharply, rather
  than just using a flat weighted average — tied to the cost asymmetry
  already written down in `criteria.md` (a wrong accusation costs a writer
  more than a missed detection costs the site).
- *What came back:* a rule with a disagreement threshold
  (`SIGNAL_DISAGREEMENT_THRESHOLD` in `config.py`): below it, a plain
  weighted average; above it, the result is pulled halfway toward whichever
  signal read more human, instead of letting the two cancel out to a flat
  "unsure." It came with a worked example from a real split case: `model_score
  = 0.7270`, `style_score = 0.2290` — a flat average lands at 0.478, the
  disagreement rule pulls it to 0.3535.
- *What I changed:* nothing about the logic — I verified the worked numbers
  myself by re-running `scoring.combine_signals` against that exact split
  case and two non-disagreeing cases, to confirm the rule only kicks in where
  it's supposed to and doesn't disturb scores that already agree. I did
  rewrite the docstring and the README's combining-rule section to explain
  *why* leaning toward the writer is the right default here, since the
  original phrasing only described the mechanism, not the reasoning behind
  it.

<!-- ═══════════════════════ UNIT 8 — THE TEST ═══════════════════════ -->

---

## Rate Limiting

**My limits:** ___ per minute, ___ per day

**Why those numbers and not others:**

<!-- Think about two people: a real writer submitting their own work a few
     times an hour, and a script sending a thousand variations to map your
     thresholds. Your numbers have to be liveable for the first and hostile to
     the second. -->

**What a caller counts as:**

**The run of status codes when I pushed past it:**

<!-- python run_attacks.py --flood 15 -->

```

```

---

## Attack Run — Before

<!-- Every attack with its outcome and a held-or-broke mark.
     `run_attacks.py --label before` produces the table. -->

**Ten audit log entries from the run**

<!-- Choose entries that show the interesting failures, not the ten easiest. -->

```json

```

**The single worst outcome** — the one I'd least want to explain to a writer
whose work got caught by it:

---

## Run Log and Verdicts

<!-- Your five criteria across three trials. `run_eval.py --label before`. -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
| --------- | ------ | ----- | ----- | ----- | ------- |
| 1.        |        |       |       |       |         |
| 2.        |        |       |       |       |         |
| 3.        |        |       |       |       |         |
| 4.        |        |       |       |       |         |
| 5.        |        |       |       |       |         |

**Real output from one trial**, pasted as text, naming the file and function
that produced it:

```json

```

**Diagnoses**

<!-- For each miss AND each broken attack: the stage and the mechanism.

     Your service has five stages: the route, signal one, signal two, the
     combining rule, and the label mapping.

     Not a diagnosis:  "The evasion attacks got through."
     A diagnosis:      "Four evasion inputs got through. All four had typos
                        added to AI-generated text. My second signal measures
                        word variety, and typos raise word variety — so it read
                        them as more human. My combining rule weights that
                        signal at 0.6, so it dragged the whole score down."

     Look for a pattern. Five failures on one signal is one problem, not five. -->

---

## The Improvement

**What I changed:**

**Which diagnosis pointed at it:**

### Attack Run — After

<!-- Same format. `run_attacks.py --label after` -->

**Did it help, and how do I know:**

<!-- Widening the unsure band usually fixes one problem and creates another.
     Reporting that trade honestly is worth full credit. -->

---

## What's Still Broken

<!-- For each attack still getting through and each criterion still missed:
     what you'd do, and why you stopped. -->

**The trade I'd make if this ran for real:**

<!-- Two sentences. Fewer wrong accusations means more AI text getting through.
     Say which way you'd go and WHO PAYS FOR IT. -->

<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 7

       [ ] criteria.md has five numbered criteria, each naming a target
       [ ] Each has a reason underneath
       [ ] POST /submit returns content_id, guess, confidence, label,
           model_score and style_score
       [ ] Two signals that measure DIFFERENT things, each with a named blind spot
       [ ] Three label variants, all reachable, written out in full
       [ ] POST /appeal changes status and writes to the log
       [ ] Signals and Scoring names scoring.py::combine_signals
       [ ] Sample Run: a submission AND an appeal, as pasted text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN

     SUBMISSION CHECKLIST — unit 8

       [ ] Rate limiting on /submit, with your numbers justified
       [ ] The pasted run of status codes showing 429
       [ ] Audit log with all nine fields, recording rejections too
       [ ] The attack set run IN FULL, every input with an outcome
       [ ] Ten audit log entries pasted as text
       [ ] Five criteria across three trials
       [ ] A diagnosis for every miss and every broken attack — stage AND mechanism
       [ ] One improvement, with Attack Run — After
       [ ] What's Still Broken, including the production trade
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
