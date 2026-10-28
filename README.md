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
   `(guess, label_text)` pair, using the thresholds in `config.py`.
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
| --------------------- | ----------- | ---------------------------- |
| high-confidence human |             |                              |
| unsure                |             |                              |
| high-confidence AI    |             |                              |

**Why I worded the "unsure" one this way:**

<!-- It's the hardest of the three. It has to admit uncertainty without
     sounding like an accusation, because the person reading it may well have
     written every word themselves. -->

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
  "confidence": 0.0,
  "content_id": "2ea5baca-dbdd-40ea-adbc-9fb9155b38aa",
  "guess": "placeholder",
  "label": "PLACEHOLDER — not scored yet.",
  "model_score": 0.5675,
  "style_score": null
}
```

<!-- Milestone 3 checkpoint: only the first signal is wired in. guess, label,
     and style_score are still placeholders — confidence/label/style_score
     fill in across Milestones 4 and 5. -->

**An appeal**

```bash
$ curl -X POST http://127.0.0.1:5000/appeal \
  -H "Content-Type: application/json" \
  -d '{"content_id": "...", "reasoning": "..."}'
```

```json
```

**What the log shows afterwards**

<!-- The appeal isn't built yet (Milestone 5) — this shows the submission's
     log entry only. content_id matches the response above, and guess/label/
     combined_score/style_score are present as null rather than missing,
     which is what audit.py's nine-field-from-the-start design means. -->

```bash
$ curl "http://127.0.0.1:5000/log?limit=1"
```

```json
{
  "count": 1,
  "entries": [
    {
      "combined_score": null,
      "content_id": "2ea5baca-dbdd-40ea-adbc-9fb9155b38aa",
      "creator_id": "writer-1",
      "guess": null,
      "label": null,
      "model_score": 0.5675,
      "status": "decided",
      "style_score": null,
      "timestamp": "2026-10-28T01:37:17+00:00"
    }
  ]
}
```

---

## How I Used AI

**Moment 1**

- *What I asked for:*
- *What came back:*
- *What I changed:*

**Moment 2**

- *What I asked for:*
- *What came back:*
- *What I changed:*

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
