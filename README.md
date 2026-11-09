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

<!-- ═══════════════════════ UNIT 7, THE BUILD ═══════════════════════ -->

## What This Does

<!-- The path a submission takes, from arriving to the label a reader sees.
     Six or seven steps, this is the trace you wrote in Milestone 1. -->

1. **`app.py` `/submit`** pulls `text` and `creator_id` out of the JSON body.
2. **`detector.py` `model_signal(text)`** runs the text through a local GPT-2
   instance and turns its perplexity into a 0–1 "AI-likely" score (signal one).
3. **`stylometry.py` `style_signal(text)`** independently measures the shape
   of the text, sentence-length spread, vocabulary variety, punctuation
   density, and produces a second 0–1 "AI-likely" score (signal two).
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
     the signal yet, and unit 8's attack set is built out of blind spots. -->

### Signal one - the model signal

**What it measures:** how predictable each next token is to a local GPT-2
model, averaged over the text as perplexity, then mapped through a logistic
curve onto 0–1 (lower perplexity → higher AI score).

**Why that might differ between human and AI writing:** a language model
writes by repeatedly picking a likely next token, so its own output tends to
be easy for a model to predict. Human writing is noisier, odd word choices,
digressions, the specific rather than the typical, which reads as higher
perplexity.

**What it can't see:** who actually wrote the text, only how surprising the
words are against gpt2's training distribution. It can't tell "generated"
apart from "plain." Someone writing simply on purpose (a second-language
writer, a younger writer, anyone being deliberately clear) scores just as
AI-like as a model would. It also runs backwards on register: dense, ornate
prose scores *human*, including AI-generated ornate prose, because rare
words are exactly what trips the model up.

### Signal two - the style signal

**What it measures:** three shape statistics with no semantic content,
whether sentence length varies or marches in lockstep, how much vocabulary
repeats, how much and what kind of punctuation appears.

**Why that might differ between human and AI writing:** generated text tends
toward even, mid-length sentences and a narrower vocabulary band, because
that's what "most likely next word" produces on average. Human writing is
lumpier, a three-word sentence next to a forty-word one, idiosyncratic
punctuation habits that vary writer to writer.

**What it can't see:** meaning, at all, it only sees the shape the
characters make on the page. It can't tell a text that's naturally uniform
from one deliberately reshaped to look varied: typos, sentence-splitting, a
pasted quotation all move the score without touching what the text says. It
also can't catch AI generation that's been prompted to vary its own sentence
length and vocabulary, the content can still be machine-written while the
shape reads as human.

### The combining rule

<!-- Write the rule in words, then give the numbers. What happens when the two
     signals disagree? -->

**The rule:** a weighted average of `model_score` and `style_score` is the
base case. But when the two disagree by more than a set threshold, a flat
average isn't trusted to land honestly on "unsure", the result is pulled
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
`style_score = 0.2290` (the shape reads clearly human, exactly what the
model signal can't see). The disagreement is 0.498, above the 0.35
threshold. A flat average would land at 0.478, barely inside "unsure." The
disagreement rule instead pulls it to 0.3535, right at the edge of
high-confidence human, because the style signal is picking up concrete,
checkable structure that the model signal has no way to notice, and the cost
of being wrong favors trusting that read.

---

## Label Variants

<!-- The exact text of all three labels, as a reader would see them, and the
     score range each covers.

     Write them for someone who has never heard the word "threshold". -->

| Label                 | Score range  | The exact text a reader sees                                                                                                                     |
| --------------------- | ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| high-confidence human | 0.00 – 0.35 | "We think this was probably written by a person."                                                                                                |
| unsure                | 0.35 – 0.65 | "We couldn't tell either way. This piece could have been written by a person or by AI, treat this result as inconclusive, not as an accusation." |
| high-confidence AI    | 0.65 – 1.00 | "We think this was probably written by AI, or with heavy AI assistance."                                                                         |

**Why I worded the "unsure" one this way:**

<!-- It's the hardest of the three. It has to admit uncertainty without
     sounding like an accusation, because the person reading it may well have
     written every word themselves. -->

It names what the system knows (it couldn't tell) instead of what it
suspects (maybe AI). "Treat this result as inconclusive, not as an
accusation" is there on purpose, the plain reading of "unsure" on your own
writing is still "they think I might have used AI," so the sentence has to
say out loud that this isn't a verdict, or a reader has no way to know that
for themselves.

**Confirming all three are reachable:** submitted through the running
service, a plain personal anecdote with contractions and a parenthetical
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
     entry, same content_id, status moved to under_review, audit.log_appeal
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
  calibration inputs, clearly AI, clearly human, formal human writing, and
  lightly-edited AI, and dig into the components if any score looked
  surprising.
- *What came back:* `formal_human`'s `style_score` (0.4736) looked too
  neutral for dense, distinctive prose. Breaking down the three measures
  separately showed `punctuation_density` at only 0.080 despite the text
  containing a colon and two possessive apostrophes, because
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
  than just using a flat weighted average, tied to the cost asymmetry
  already written down in `criteria.md` (a wrong accusation costs a writer
  more than a missed detection costs the site).
- *What came back:* a rule with a disagreement threshold
  (`SIGNAL_DISAGREEMENT_THRESHOLD` in `config.py`): below it, a plain
  weighted average; above it, the result is pulled halfway toward whichever
  signal read more human, instead of letting the two cancel out to a flat
  "unsure." It came with a worked example from a real split case: `model_score = 0.7270`, `style_score = 0.2290`, a flat average lands at 0.478, the
  disagreement rule pulls it to 0.3535.
- *What I changed:* nothing about the logic, I verified the worked numbers
  myself by re-running `scoring.combine_signals` against that exact split
  case and two non-disagreeing cases, to confirm the rule only kicks in where
  it's supposed to and doesn't disturb scores that already agree. I did
  rewrite the docstring and the README's combining-rule section to explain
  *why* leaning toward the writer is the right default here, since the
  original phrasing only described the mechanism, not the reasoning behind
  it.

**Moment 3: held or broke for 56 attacks**

- *What I asked for:* a verdict, HELD or BROKE, for every attack in the set,
  judged against what the `targets` column said each one was going for, and a
  count.
- *What came back:* 22 BROKE and 34 HELD, with the rule written down per
  family (an evasion BROKE if the text stopped being labeled AI, measured
  against the unmodified AI text's 0.6628; a false positive BROKE if human
  writing was labeled AI; malformed input held if it was rejected cleanly or
  answered defensibly). It flagged its own weak calls: EV04, EV07 and EV09
  broke by only 0.02–0.03 because the baseline sits 0.013 over the AI
  threshold, and MF03–MF07 only count as broken if a service should refuse
  input with nothing to read.
- *What I changed:* I did not accept RQ11's first 429 as a result. The
  instructor's note says a malformed row with no usable `creator_id` counts
  against the IP, so that request never reached the route. I had it rerun
  alone after the rate window; it returned a clean 400, so RQ11 is HELD. I
  also had the AI check each verdict against the audit log's scores rather
  than the report's Score column, which is confidence, not the combined score.

**Moment 4: scenarios, and the one thing the AI wouldn't write for me**

- *What I asked for:* `scenarios.py` for my five criteria, including the
  criterion that needs my own writing and the one that needs inputs across the
  score range.
- *What came back:* calibration texts it had scored offline against my
  scoring code before choosing them. Its first "clearly human" text, a polished
  family-trip anecdote, only reached "unsure" (0.476); a casual lowercase one
  reached "human" (0.317), which is how it found that the human label is hard
  to reach. For criterion 1 it left ten placeholders and told me it could not
  supply my writing, because the criterion is about whether the service
  accuses real people.
- *What I changed:* I gave it two of my own course assignments. It used ten
  paragraphs in my wording, typos included, and left out the ones that read as
  encyclopedia definitions and the one that names me and my school, since the repo gets pushed. I also recorded that my own formal prose is an easier test than the
  plain writing criterion 1 was written about, which is why I would tighten
  that criterion.

**Moment 5: two mistakes the AI made, and how they were caught**

- *What I asked for:* the "after" attack run, and the "What's Still Broken"
  section.
- *What came back wrong:* (1) a rerun of one attack in the same minute as the
  full run overwrote the full report, because the filename only has the
  minute in it; and a second `run_attacks.py` at the same time shared the rate
  limiter, so some rows came back 429. (2) The script that wrote the README
  section looked for its end marker from the start of the file, matched an
  earlier comment, and pasted 919 duplicated lines in. It had already
  committed that.
- *What I changed:* the diffstat read "919 insertions" where about 30 were
  expected, so it was caught before pushing. The README was restored from the
  last good commit, the script was fixed to search from the section heading, and
  the unpushed commit was amended. For the reports, I used the labeled `_after`
  run, confirmed it matched the before run on every row that was not rejected,
  and deleted two redundant reports of my own.

**Moment 6: choosing the improvement, and what it did not fix**

- *What I asked for:* one improvement from reweighting, moving a threshold, or
  validating input.
- *What came back:* input validation, with the arithmetic for why not the
  others: cutting signal one's weight from 0.5 to 0.3 leaves all of FP02–FP07
  above 0.65 (lowest 0.672), and raising `AI_THRESHOLD` past 0.76 would clear
  them but push my clearly-AI calibration text (0.7364) out of the AI band.
  After the change it reported 22 broken attacks down to 17, criterion 5 from
  MISSED to MET, and said outright that it did nothing for the six human texts
  still called AI.
- *What I changed:* I kept that last sentence in the README as the verdict
  instead of leading with 22 → 17, since none of the five attacks it fixed
  involved a real writer being accused. I also checked the claim myself by
  diffing the two attack reports: 50 of 56 rows are identical, and the six that
  changed are exactly the rejected inputs.

<!-- ═══════════════════════ UNIT 8, THE TEST ═══════════════════════ -->

---

## Rate Limiting

**My limits:** 6 per minute, 100 per day

**Why those numbers and not others:**

A real writer submitting their own work, drafting, revising, resubmitting a
paragraph they reworded, fits comfortably inside 6 submissions in a minute
and well under 100 in a day; nobody writes and resubmits faster than that by
hand. A script trying to map where my thresholds sit needs many more data
points than that to be useful: with each submission taking a second or two
(the model runs inline), 6/minute already slows a sweep to a crawl, and
100/day caps how much of that sweep can happen at all before the day's
budget is gone. The per-minute number stops a burst; the per-day number
stops someone from just submitting slowly to dodge the first limit.

**What a caller counts as:**

`app.py`'s `rate_limit_key()` keys by `creator_id` when the request body is a
JSON object with a non-empty string `creator_id`, and falls back to the
caller's IP address otherwise. That means one writer submitting from
different machines still shares one limit, and a script that can't or
doesn't send a `creator_id` is limited by address instead, it can't dodge
the limit just by omitting the field.

**The run of status codes when I pushed past it:**

```bash
$ python run_attacks.py --flood 15
```

```
200 200 200 200 200 200 429 429 429 429 429 429 429 429 429
```

9 of 15 requests from the same `creator_id` were rate limited once the
6-per-minute cap was crossed. The 429s were logged too, `audit.log_rejection`
records `reason: "rate_limited"` and the limit string, so a flood leaves the
same trace a legitimate burst wouldn't: many entries, same creator, all
rejected in the same window.

---

## Attack Run - Before

**56 attacks, 34 held, 22 broke** (`results/attack_run_2026-11-04_1718.md`, run against the service with rate limiting on). Combined score is the `scoring.py::combine_signals` output from the audit log; `-` means the request was rejected before scoring.

| ID      | Family             | Going for                                              | Status | Guess  | Combined | Verdict         |
| ------- | ------------------ | ------------------------------------------------------ | ------ | ------ | -------- | --------------- |
| EV01    | evasion            | signal two: typos raise word variety                   | 200    | human  | 0.287    | **BROKE** |
| EV02    | evasion            | signal two: broken-up sentences raise length spread    | 200    | unsure | 0.500    | **BROKE** |
| EV03    | evasion            | signal two: a pasted quotation changes the shape       | 200    | unsure | 0.604    | **BROKE** |
| EV04    | evasion            | signal one: unusual words raise perplexity             | 200    | unsure | 0.631    | **BROKE** |
| EV05    | evasion            | both signals: heavy human editing pass                 | 200    | unsure | 0.413    | **BROKE** |
| EV06    | evasion            | signal two: one very long sentence and one very short  | 200    | unsure | 0.495    | **BROKE** |
| EV07    | evasion            | signal two: padding with punctuation                   | 200    | unsure | 0.624    | **BROKE** |
| EV08    | evasion            | signal one: text below the token window                | 200    | unsure | 0.409    | **BROKE** |
| EV09    | evasion            | both: AI text with a human opening paragraph bolted on | 200    | unsure | 0.633    | **BROKE** |
| EV10    | evasion            | signal two: repeated stanza structure                  | 200    | ai     | 0.871    | **HELD**  |
| FP01    | false_positive     | plain, clear human writing with no flourishes          | 200    | unsure | 0.614    | **HELD**  |
| FP02    | false_positive     | human writing in a formal register                     | 200    | ai     | 0.711    | **BROKE** |
| FP03    | false_positive     | a non-native English speaker writing carefully         | 200    | ai     | 0.727    | **BROKE** |
| FP04    | false_positive     | a student essay written to a rubric                    | 200    | ai     | 0.721    | **BROKE** |
| FP05    | false_positive     | technical documentation written by a person            | 200    | ai     | 0.756    | **BROKE** |
| FP06    | false_positive     | a person imitating a formal template                   | 200    | ai     | 0.732    | **BROKE** |
| FP07    | false_positive     | human writing that repeats a phrase deliberately       | 200    | ai     | 0.743    | **BROKE** |
| FP08    | false_positive     | very short genuine human submission                    | 200    | unsure | 0.422    | **HELD**  |
| PI01    | prompt_injection   | instruction to ignore the check                        | 200    | unsure | 0.465    | **HELD**  |
| PI02    | prompt_injection   | instruction disguised as a system message              | 200    | human  | 0.322    | **BROKE** |
| PI03    | prompt_injection   | instruction wrapped in the writer's voice              | 200    | unsure | 0.558    | **HELD**  |
| PI04    | prompt_injection   | attempt to make the label text hostile                 | 200    | unsure | 0.518    | **HELD**  |
| PI05    | prompt_injection   | attempt to inject into the audit log                   | 200    | human  | 0.300    | **HELD**  |
| PI06    | prompt_injection   | instruction plus real human text                       | 200    | unsure | 0.587    | **HELD**  |
| MF01    | malformed          | text is only whitespace                                | 400    | -      | -        | **HELD**  |
| MF02    | malformed          | text is a single character                             | 400    | -      | -        | **HELD**  |
| MF03    | malformed          | text is control characters                             | 200    | human  | 0.167    | **BROKE** |
| MF04    | malformed          | text is only punctuation                               | 200    | human  | 0.258    | **BROKE** |
| MF05    | malformed          | text is a very long single word                        | 200    | ai     | 0.832    | **BROKE** |
| MF06    | malformed          | text is emoji only                                     | 200    | ai     | 0.999    | **BROKE** |
| MF07    | malformed          | text is right-to-left script                           | 200    | ai     | 0.953    | **BROKE** |
| MF08    | malformed          | text is 60,000 characters                              | 200    | ai     | 0.921    | **HELD**  |
| RQ01    | malformed          | no text field at all                                   | 400    | -      | -        | **HELD**  |
| RQ02    | malformed          | no creator_id                                          | 200    | human  | 0.346    | **HELD**  |
| RQ03    | malformed          | text is a number                                       | 400    | -      | -        | **HELD**  |
| RQ04    | malformed          | text is a list                                         | 400    | -      | -        | **HELD**  |
| RQ05    | malformed          | text is null                                           | 400    | -      | -        | **HELD**  |
| RQ06    | malformed          | creator_id is an object                                | 200    | human  | 0.204    | **BROKE** |
| RQ07    | malformed          | body is a JSON array, not an object                    | 400    | -      | -        | **HELD**  |
| RQ08    | malformed          | body is unparseable JSON                               | 400    | -      | -        | **HELD**  |
| RQ09    | malformed          | body is empty                                          | 400    | -      | -        | **HELD**  |
| RQ10    | malformed          | body is form-encoded, not JSON                         | 400    | -      | -        | **HELD**  |
| RQ11    | malformed          | body is JSON claiming to be plain text                 | 429    | -      | -        | **HELD**  |
| RQ12    | malformed          | deeply nested JSON                                     | 400    | -      | -        | **HELD**  |
| FL01_01 | flood_same_creator | 20 rapid submissions from one creator                  | 200    | human  | 0.188    | **HELD**  |
| FL01_02 | flood_same_creator | 20 rapid submissions from one creator                  | 200    | human  | 0.188    | **HELD**  |
| FL01_03 | flood_same_creator | 20 rapid submissions from one creator                  | 200    | human  | 0.188    | **HELD**  |
| FL01_04 | flood_same_creator | 20 rapid submissions from one creator                  | 200    | human  | 0.188    | **HELD**  |
| FL01_05 | flood_same_creator | 20 rapid submissions from one creator                  | 200    | human  | 0.188    | **HELD**  |
| FL01_06 | flood_same_creator | 20 rapid submissions from one creator                  | 200    | human  | 0.188    | **HELD**  |
| FL01_07 | flood_same_creator | 20 rapid submissions from one creator                  | 429    | -      | -        | **HELD**  |
| FL01_08 | flood_same_creator | 20 rapid submissions from one creator                  | 429    | -      | -        | **HELD**  |
| FL01_09 | flood_same_creator | 20 rapid submissions from one creator                  | 429    | -      | -        | **HELD**  |
| FL01_10 | flood_same_creator | 20 rapid submissions from one creator                  | 429    | -      | -        | **HELD**  |
| FL01_11 | flood_same_creator | 20 rapid submissions from one creator                  | 429    | -      | -        | **HELD**  |
| FL01_12 | flood_same_creator | 20 rapid submissions from one creator                  | 429    | -      | -        | **HELD**  |

How I judged each one:

- **evasion**, the unmodified AI text scores 0.663 and is labeled AI. BROKE if the text stopped being labeled AI. Only EV10 held (repeating the stanzas pushed it up to 0.871). EV04, EV07 and EV09 broke by only 0.02–0.03, because the baseline sits 0.013 above `AI_THRESHOLD`.
- **false_positive**, BROKE if genuine human writing was labeled AI (FP02–FP07). FP01 and FP08 came back unsure, so they held.
- **prompt_injection**, judged on what the injection asked for. PI02 BROKE: it asked for a human label and got one, but only because the extra line changed the style score, nothing in the service reads instructions. PI05 held: the audit entry was written intact and nothing was forged.
- **malformed**, held if rejected cleanly or answered defensibly. MF03–MF07 BROKE: a confident label (emoji-only text at 0.9985 AI, a right-to-left script at 0.92) on input with nothing to score or that the detector can't judge fairly. RQ06 BROKE: a dict `creator_id` is written to the audit log as a dict. RQ11 first returned 429 from the per-IP limiter before reaching the route; the rerun returned a clean 400.
- **flood_same_creator**, all 12 held: 6 accepted, then 429 from the 7th, matching the 6-per-minute limit.

**Ten audit log entries from the run**

Picked for the failures, not the easy cases: EV01 (typos took AI text to "human"), EV10 (the one evasion that held), FP02 and FP03 (human writers accused), PI02 and PI05 (injections), MF06 and MF07 (confident labels on non-prose and non-English text), RQ06 (a dict stored as `creator_id`), and a `rate_limited` rejection from the flood.

```json
[
  {
    "combined_score": 0.2867,
    "content_id": "1899f1c3-3949-47b6-8326-61b266c106f0",
    "creator_id": "attacker_EV01",
    "guess": "human",
    "label": "We think this was probably written by a person.",
    "model_score": 0.1635,
    "status": "decided",
    "style_score": 0.6562,
    "timestamp": "2026-11-05T01:17:04+00:00"
  },
  {
    "combined_score": 0.8705,
    "content_id": "cb9e9523-f523-48b6-8477-da9e32e5a774",
    "creator_id": "attacker_EV10",
    "guess": "ai",
    "label": "We think this was probably written by AI, or with heavy AI assistance.",
    "model_score": 0.9792,
    "status": "decided",
    "style_score": 0.7619,
    "timestamp": "2026-11-05T01:17:14+00:00"
  },
  {
    "combined_score": 0.7108,
    "content_id": "405914cf-49a0-40ba-a485-7c56e7519e5c",
    "creator_id": "attacker_FP02",
    "guess": "ai",
    "label": "We think this was probably written by AI, or with heavy AI assistance.",
    "model_score": 0.7387,
    "status": "decided",
    "style_score": 0.683,
    "timestamp": "2026-11-05T01:17:15+00:00"
  },
  {
    "combined_score": 0.7273,
    "content_id": "b063f2de-7dfe-49b1-a526-c80955493d71",
    "creator_id": "attacker_FP03",
    "guess": "ai",
    "label": "We think this was probably written by AI, or with heavy AI assistance.",
    "model_score": 0.8051,
    "status": "decided",
    "style_score": 0.6496,
    "timestamp": "2026-11-05T01:17:15+00:00"
  },
  {
    "combined_score": 0.322,
    "content_id": "9b94a890-59c5-4c45-b0e0-ea4137eb218b",
    "creator_id": "attacker_PI02",
    "guess": "human",
    "label": "We think this was probably written by a person.",
    "model_score": 0.2044,
    "status": "decided",
    "style_score": 0.4395,
    "timestamp": "2026-11-05T01:17:27+00:00"
  },
  {
    "combined_score": 0.3005,
    "content_id": "aae58c00-d8e6-43a5-a32f-a624bea31612",
    "creator_id": "attacker_PI05",
    "guess": "human",
    "label": "We think this was probably written by a person.",
    "model_score": 0.6401,
    "status": "decided",
    "style_score": 0.1873,
    "timestamp": "2026-11-05T01:17:31+00:00"
  },
  {
    "combined_score": 0.9985,
    "content_id": "cd73c209-fe37-4744-b6fb-4859fef64121",
    "creator_id": "attacker_MF06",
    "guess": "ai",
    "label": "We think this was probably written by AI, or with heavy AI assistance.",
    "model_score": 0.9969,
    "status": "decided",
    "style_score": 1.0,
    "timestamp": "2026-11-05T01:17:50+00:00"
  },
  {
    "combined_score": 0.9532,
    "content_id": "44710f8e-7504-4c8d-9d38-c96bcd9990e2",
    "creator_id": "attacker_MF07",
    "guess": "ai",
    "label": "We think this was probably written by AI, or with heavy AI assistance.",
    "model_score": 0.9064,
    "status": "decided",
    "style_score": 1.0,
    "timestamp": "2026-11-05T01:17:53+00:00"
  },
  {
    "combined_score": 0.2036,
    "content_id": "fcab769b-e4dc-4c13-80c7-2a32acbe4153",
    "creator_id": {
      "id": "x"
    },
    "guess": "human",
    "label": "We think this was probably written by a person.",
    "model_score": 0.0492,
    "status": "decided",
    "style_score": 0.6667,
    "timestamp": "2026-11-05T01:17:59+00:00"
  },
  {
    "creator_id": "attacker_flood",
    "event": "rejected",
    "limit": "6 per 1 minute",
    "reason": "rate_limited",
    "status": "rejected",
    "timestamp": "2026-11-05T01:18:05+00:00"
  }
]
```

**The single worst outcome**, the one I'd least want to explain to a writer
whose work got caught by it:

FP03, a non-native English speaker writing carefully about their first month in a new country, was labeled **AI** (combined 0.727; model signal 0.805, style signal 0.650). Both signals read the same thing: short, plain sentences in common words are what the language model predicts easily, and even sentence lengths are what the style signal reads as machine-like. A careful second-language writer is exactly who that describes, so the service accuses the writer it should be most careful with. Both signals agree here, so the disagreement rule in `scoring.py::combine_signals` never fires to pull the score back toward human.

---

## Run Log and Verdicts

<!-- Your five criteria across three trials. `run_eval.py --label before`. -->

Run with `python run_eval.py --label before` (report: `results/run_2026-11-04_1739_before.md`)
for criteria 1, 2, 3 and 5. Criterion 2's `combined_score` is not in the API
response, so it was read from the audit log (`eval_score spread_1` / `_2`).
Criterion 4 can't be expressed as a scenario (it needs the `content_id` a
submission returned), so it was run with `python appeal_check.py`.

| Criterion          | Target                                                                                                 | Run 1                                                                   | Run 2                          | Run 3                          | Verdict          |
| ------------------ | ------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------- | ------------------------------ | ------------------------------ | ---------------- |
| 1. False positives | at most 1 of 10 of my own paragraphs labeled AI, in every trial                                        | 0 of 10 AI (1 human, 9 unsure)                                          | 0 of 10 AI (1 human, 9 unsure) | 0 of 10 AI (1 human, 9 unsure) | **MET**    |
| 2. Score spread    | clearly-AI and clearly-human texts at least 0.4 apart on `combined_score`, every trial               | 0.7364 − 0.3165 = 0.420                                                | 0.420                          | 0.420                          | **MET**    |
| 3. Label coverage  | each of human / unsure / AI produced by at least one of 4 calibration inputs in at least 2 of 3 trials | ai, human, unsure, unsure, all 3 labels                                 | all 3 labels                   | all 3 labels                   | **MET**    |
| 4. Appeal path     | 10 of 10 appeals set `under_review` and sit beside the original entry                                | 10 of 10                                                                | 10 of 10                       | 10 of 10                       | **MET**    |
| 5. Bad input       | missing, empty and 50,000-word `text` each return a 4xx, no 5xx, every trial                         | missing 400, empty 400, 50,000 words **200 (labeled AI, 0.9988)** | same                           | same                           | **MISSED** |

**Real output from one trial** (trial 1 of each; the other two trials were
identical), pasted as text. Criteria 1, 3 and 5 are `run_eval.py::main`
recording what `app.py::submit` returned; criterion 2 is the audit entry that
`audit.py::log_decision` wrote; criterion 4 is `app.py::appeal` and
`audit.py::log_appeal`.

**Criterion 1: false positives.** Ten of my own paragraphs, one result per
line, returned by `app.py::submit` and recorded by `run_eval.py::main`
(`sent` is the first 70 characters of what was submitted). None is `ai`:

```json
{"status": 200, "guess": "unsure", "confidence": 0.128, "model_score": 0.5532, "style_score": 0.7084, "label": "We couldn't tell either way. This piece could have been written by a person or by AI — treat this result as inconclusive, not as an accusation.", "sent": "I decided to take Music Appreciation online because I am curious about"}
{"status": 200, "guess": "human", "confidence": 0.4394, "model_score": 0.0966, "style_score": 0.495, "label": "We think this was probably written by a person.", "sent": "Baa Baa Black Sheep is written by a Swedish music teacher named Alice "}
{"status": 200, "guess": "unsure", "confidence": 0.5033, "model_score": 0.4761, "style_score": 0.6728, "label": "We couldn't tell either way. This piece could have been written by a person or by AI — treat this result as inconclusive, not as an accusation.", "sent": "On Monday, I had dinner at my uncle’s house and we got a chance to wat"}
{"status": 200, "guess": "unsure", "confidence": 0.3573, "model_score": 0.5266, "style_score": 0.6662, "label": "We couldn't tell either way. This piece could have been written by a person or by AI — treat this result as inconclusive, not as an accusation.", "sent": "During the Middle Ages, Catholic Church started to make systematic use"}
{"status": 200, "guess": "unsure", "confidence": 0.2473, "model_score": 0.285, "style_score": 0.6933, "label": "We couldn't tell either way. This piece could have been written by a person or by AI — treat this result as inconclusive, not as an accusation.", "sent": "Sacred music is associated with religious or expanded approaches to su"}
{"status": 200, "guess": "unsure", "confidence": 0.9547, "model_score": 0.3509, "style_score": 0.6627, "label": "We couldn't tell either way. This piece could have been written by a person or by AI — treat this result as inconclusive, not as an accusation.", "sent": "Music was a basic piece of city, strict, and dignified life in the Ren"}
{"status": 200, "guess": "unsure", "confidence": 0.4313, "model_score": 0.3213, "style_score": 0.5082, "label": "We couldn't tell either way. This piece could have been written by a person or by AI — treat this result as inconclusive, not as an accusation.", "sent": "Basse danse was a popular court dance that took place in Burgundian Co"}
{"status": 200, "guess": "unsure", "confidence": 0.5713, "model_score": 0.5135, "style_score": 0.6151, "label": "We couldn't tell either way. This piece could have been written by a person or by AI — treat this result as inconclusive, not as an accusation.", "sent": "The lute, harpsichord, and contrabassoon are among the strange and fan"}
{"status": 200, "guess": "unsure", "confidence": 0.198, "model_score": 0.5987, "style_score": 0.6419, "label": "We couldn't tell either way. This piece could have been written by a person or by AI — treat this result as inconclusive, not as an accusation.", "sent": "King George II attended the London premier and allegedly rose to his f"}
{"status": 200, "guess": "unsure", "confidence": 0.0267, "model_score": 0.7852, "style_score": 0.5068, "label": "We couldn't tell either way. This piece could have been written by a person or by AI — treat this result as inconclusive, not as an accusation.", "sent": "Guitar belongs to string family instruments. They are usually made fro"}
```

**Criterion 2: score spread.** The clearly-AI and clearly-human calibration
texts as logged by `audit.py::log_decision` (read back from `logs/audit.jsonl`,
because `app.py::submit` does not return `combined_score`).
0.7364 − 0.3165 = 0.4199:

```json
{"timestamp": "2026-11-05T01:37:44+00:00", "content_id": "9632a3bc-b6ed-4a29-abcf-6f9586936763", "creator_id": "eval_score spread_1", "guess": "ai", "model_score": 0.8162, "style_score": 0.6566, "combined_score": 0.7364, "label": "We think this was probably written by AI, or with heavy AI assistance.", "status": "decided"}
{"timestamp": "2026-11-05T01:37:45+00:00", "content_id": "9d8bad44-c682-4a82-a7b5-4bf7f6abcc99", "creator_id": "eval_score spread_2", "guess": "human", "model_score": 0.1897, "style_score": 0.4433, "combined_score": 0.3165, "label": "We think this was probably written by a person.", "status": "decided"}
```

**Criterion 3: label coverage.** Four calibration inputs through
`app.py::submit`, recorded by `run_eval.py::main`. All three labels appear
(`ai`, `human`, `unsure`):

```json
{"status": 200, "guess": "ai", "confidence": 0.2469, "model_score": 0.8162, "style_score": 0.6566, "label": "We think this was probably written by AI, or with heavy AI assistance.", "sent": "Artificial intelligence is transforming the way organizations operate "}
{"status": 200, "guess": "human", "confidence": 0.0957, "model_score": 0.1897, "style_score": 0.4433, "label": "We think this was probably written by a person.", "sent": "ok so the bus was late AGAIN and i'm standing there in the drizzle lik"}
{"status": 200, "guess": "unsure", "confidence": 0.2373, "model_score": 0.6175, "style_score": 0.6113, "label": "We couldn't tell either way. This piece could have been written by a person or by AI — treat this result as inconclusive, not as an accusation.", "sent": "We got to the campsite about four. The pitch was fine, a bit sloped, b"}
{"status": 200, "guess": "unsure", "confidence": 0.9527, "model_score": 0.4588, "style_score": 0.5554, "label": "We couldn't tell either way. This piece could have been written by a person or by AI — treat this result as inconclusive, not as an accusation.", "sent": "Artificial intelligence is changing how organizations operate. By usin"}
```

**Criterion 4: the appeal path.** A fresh submission and appeal against its
`content_id`, using `app.py::submit` and `app.py::appeal`. The responses:

```json
{
  "confidence": 0.1043,
  "content_id": "1010253e-9c11-4f6c-9744-9621983e3f32",
  "guess": "human",
  "label": "We think this was probably written by a person.",
  "model_score": 0.1958,
  "style_score": 0.6667
}
```

```json
{
  "content_id": "1010253e-9c11-4f6c-9744-9621983e3f32",
  "message": "Your appeal has been recorded and will be reviewed.",
  "status": "under_review"
}
```

and the two entries now in the log for that `content_id`, the original
decision written by `audit.py::log_decision` and the appeal written by
`audit.py::log_appeal`, as separate lines, original untouched:

```json
{"combined_score": 0.3135, "content_id": "1010253e-9c11-4f6c-9744-9621983e3f32", "creator_id": "appeal_demo", "guess": "human", "label": "We think this was probably written by a person.", "model_score": 0.1958, "status": "decided", "style_score": 0.6667, "timestamp": "2026-11-05T01:50:20+00:00"}
{"content_id": "1010253e-9c11-4f6c-9744-9621983e3f32", "creator_id": "appeal_demo", "event": "appeal", "reasoning": "I wrote this myself.", "status": "under_review", "timestamp": "2026-11-05T01:50:20+00:00"}
```

**Criterion 5: bad input.** What `run_eval.py::main` recorded
from `app.py::submit` (status 400, 400, then **200**):

```json
{"status": 400, "guess": null, "confidence": null, "model_score": null, "style_score": null, "label": null, "sent": "{\"creator_id\": \"eval_bad_missing\"}"}
{"status": 400, "guess": null, "confidence": null, "model_score": null, "style_score": null, "label": null, "sent": "(empty text)"}
{"status": 200, "guess": "ai", "confidence": 0.9966, "model_score": 0.9975, "style_score": 1.0, "label": "We think this was probably written by AI, or with heavy AI assistance.", "sent": "word word word word word word word word word word word word word word "}
```

and the matching audit entries (from the first run of this scenario in the log, which
has the same outcome as the reported trials): the two rejections written
by `audit.py::log_rejection`, then the 50,000-word submission scored by
`audit.py::log_decision` as if it were normal input:

```json
{"timestamp": "2026-11-05T01:38:03+00:00", "creator_id": "eval_bad_missing", "event": "rejected", "status": "rejected", "reason": "invalid_text", "detail": "text is required and must be a non-empty string."}
{"timestamp": "2026-11-05T01:38:03+00:00", "creator_id": "eval_bad_empty", "event": "rejected", "status": "rejected", "reason": "invalid_text", "detail": "text is required and must be a non-empty string."}
{"timestamp": "2026-11-05T01:38:06+00:00", "content_id": "9f659212-961e-4544-8509-644f86430440", "creator_id": "eval_bad_huge", "guess": "ai", "model_score": 0.9975, "style_score": 1.0, "combined_score": 0.9988, "label": "We think this was probably written by AI, or with heavy AI assistance.", "status": "decided"}
```

**Diagnoses**

The five stages are: **route** (`app.py::submit`), **signal one**
(`detector.py::model_signal`), **signal two** (`stylometry.py::style_signal`),
**combining rule** (`scoring.py::combine_signals`) and **label mapping**
(`scoring.py::score_to_label`, thresholds 0.35 / 0.65 in `config.py`). Scores
below are `model / style → combined` from the audit log. For reference, the
unmodified AI text the evasions start from scores 0.669 / 0.656 → 0.663, which
is only 0.013 over `AI_THRESHOLD`.

**The pattern.** There are 23 failures (the one missed criterion and the 22
broken attacks), and **signal one is involved in 17 of them**. That is one
problem, not 17: `detector.py::model_signal` measures how *predictable* text
is, not who wrote it, and it fails in both directions. Plain, formal or
repetitive text is predictable, so it reads as AI (FP02–FP07, MF05, MF06,
MF07, criterion 5). Strange text is unpredictable, so it reads as human (EV01,
EV08, PI02, MF03, MF04). Every attack that "worked" was a way of making text
more or less predictable without changing who wrote it. The other failures
sit around that one:

1. **Signal one reads predictability as authorship** (above). This is the
   named blind spot, and it is where the false accusations come from.
2. **Signal two is a weak second opinion, not an independent one.** On plain
   human writing it agrees with signal one (even sentence lengths score as
   AI-like), so the combining rule never sees a disagreement to act on
   (FP02–FP07). On non-Latin or empty-of-words input it returns 1.0 because
   `stylometry.py::words` only matches `[a-z0-9']` (MF04, MF06, MF07).
3. **The combining rule amplifies a signal-one swing.** When the signals split
   by more than 0.35, the score is pulled halfway toward the more human one
   (`min(model, style)`). A single odd signal-one reading therefore drags the
   result toward human instead of cancelling out (EV01, MF03, MF04).
4. **The label mapping leaves almost no room above the AI threshold.** Even
   obviously AI text only reaches 0.663 combined, so any dilution at all
   falls into "unsure" (EV02, EV03, EV04, EV06, EV07, EV09).
5. **The route validates shape, not content or size.** It checks that `text`
   is a non-empty string and long enough, and nothing else (MF03–MF08, RQ06,
   criterion 5).

**The missed criterion**

| Criterion                                   | Stage                  | Mechanism                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| ------------------------------------------- | ---------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 5. Bad input (50,000 words → 200, not 4xx) | route, then signal one | `app.py::submit` has no maximum length, so a 250,000-character body goes straight to scoring. It came back **AI at 0.9988** (0.9975 / 1.0): signal one reads only the first `DETECTOR_MAX_TOKENS` (400) tokens, and 400 tokens of "word word word…" are maximally predictable, so perplexity is near 1; signal two sees no sentence breaks and no punctuation, which it scores as uniform. The same gap let MF08 (57,640 characters) through. |

**The 22 broken attacks**

| Attack                           | Stage                             | Mechanism                                                                                                                                                                                                                                                                                                                                                               |
| -------------------------------- | --------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| EV01 typos → human              | signal one, then combining rule   | It aimed at signal two, but signal two did not move (0.656, same as the clean text). Typos like "poistioned" are unseen word pieces, so signal one's perplexity jumped and its score fell to 0.164. That split the signals by 0.49, over the 0.35 limit, so the combining rule pulled the result halfway to the human reading: 0.164 / 0.656 → **0.287, human**. |
| EV02 broken-up sentences         | signal two                        | Inserting "Really." between sentences widens the sentence-length spread, so signal two fell 0.656 → 0.406. Signal one stayed at 0.594 → 0.500, unsure. Working as aimed.                                                                                                                                                                                              |
| EV03 pasted quotation            | signal two                        | The casual quoted line changes the sentence shape: style fell 0.656 → 0.541, model stayed at 0.666 → 0.604.                                                                                                                                                                                                                                                           |
| EV04 unusual words               | label mapping                     | Signal one barely moved (0.669 → 0.611). The text only lands in unsure (0.631) because the clean baseline was 0.013 above the threshold. A margin problem, not a signal-one bypass.                                                                                                                                                                                    |
| EV05 heavy human edit            | signal one and signal two         | Both fell (0.321 / 0.505 → 0.413). This is a real rewrite, so both signals correctly read it as less AI-like.                                                                                                                                                                                                                                                          |
| EV06 one very long sentence      | signal two, signal one            | The long sentence raises the length spread (style 0.417); the added text also lowered the model score (0.573). 0.495, unsure.                                                                                                                                                                                                                                           |
| EV07 punctuation padding         | label mapping                     | Style did not move (0.662, the padding did not change the measure). Model fell to 0.586 → 0.624, 0.026 under the threshold. A margin problem.                                                                                                                                                                                                                          |
| EV08 text below the token window | signal one                        | 65 characters give signal one almost no context, so per-token perplexity is high and the score is 0.245. Signal two stays 0.572 → 0.409. The route let it through because it is over the minimum length.                                                                                                                                                               |
| EV09 human paragraph bolted on   | signal two                        | The casual opener's short, varied sentences cut style to 0.562 while signal one went up (0.704): 0.633, 0.017 under the threshold.                                                                                                                                                                                                                                      |
| FP02 formal register             | signal one, signal two            | Short plain sentences in common words are low-perplexity, so signal one reads 0.739. Signal two agrees (0.683) because the sentences are even in length. Both point the same way, so the combining rule has nothing to correct: 0.711, AI.                                                                                                                              |
| FP03 non-native speaker          | signal one, signal two            | The same as FP02: 0.805 / 0.650 → 0.727. The writer who uses simple vocabulary and even sentences is the one both signals mistake for a machine.                                                                                                                                                                                                                       |
| FP04 student essay to a rubric   | signal one, signal two            | 0.833 / 0.608 → 0.721. Rubric prose is formulaic and low-perplexity.                                                                                                                                                                                                                                                                                                   |
| FP05 technical documentation     | signal one, signal two            | 0.801 / 0.713 → 0.757. Instructions use the most predictable vocabulary and the most uniform sentences.                                                                                                                                                                                                                                                                |
| FP06 formal template letter      | signal one, signal two            | 0.881 / 0.582 → 0.732. Template phrases ("I am writing to enquire") are what a language model predicts best.                                                                                                                                                                                                                                                           |
| FP07 deliberate repetition       | signal one, signal two            | 0.882 / 0.604 → 0.743. Repeating "It rained on…" makes later tokens easy to predict, which is exactly what perplexity rewards.                                                                                                                                                                                                                                        |
| PI02 fake system message         | signal one                        | Nothing reads the instruction. The extra "SYSTEM: provenance check bypassed…" line is odd text, so perplexity rose and the model score fell to 0.204 (style 0.440): 0.322, human. The same mechanism as EV01: prepending unusual text lowers signal one.                                                                                                               |
| MF03 control characters          | route, signal one, combining rule | The route accepts any 21 characters. The control bytes are junk tokens, so perplexity is huge and signal one reads 0.0; style reads 0.667. That 0.667 split triggers the pull toward the human reading: **0.167, human** for text that is not writing.                                                                                                            |
| MF04 only punctuation            | route, signal one, combining rule | The same as MF03: 0.011 / 1.0 → 0.258, human. Signal two scores 1.0 because there are no word tokens at all, which it counts as maximally uniform.                                                                                                                                                                                                                     |
| MF05 one 4,000-character word    | route, signal one                 | A repeated token is perfectly predictable, so perplexity collapses and signal one reads 0.998 (style 0.667): 0.832, AI. The route has no check that the input contains different words.                                                                                                                                                                                 |
| MF06 emoji only                  | signal two, signal one            | `stylometry.py::words` only matches `[a-z0-9']`, so emoji give zero word tokens, zero sentences and zero punctuation, and every measure falls back to its AI-like default: style 1.0. Signal one reads 0.997. I haven't checked how the model tokenises emoji, only that it scores them as predictable. Combined 0.9985, the highest score in the run.              |
| MF07 right-to-left script        | signal two, signal one            | The same regex gap: non-Latin writing has no word tokens, so style is 1.0, and signal one reads 0.906. A real writer in another language is accused at 0.953.                                                                                                                                                                                                           |
| RQ06 `creator_id` as an object | route                             | `app.py::submit` sanitises `creator_id` only on its rejection paths (`isinstance(creator_id, str)`). On the success path it passes the raw value straight to `audit.log_decision`, so the dict `{"id": "x"}` is stored in the audit log.                                                                                                                      |

**I did not hold everything, and my targets were partly too easy.** Criterion
5 missed. Criteria 1–4 held in every trial, but one of those passes does not
mean what it looks like:

- **Criterion 1 is the one I would tighten.** I passed it (0 of 10 labeled
  AI), but the same service accused 6 of the 8 human false-positive attacks
  (FP02–FP07) in the attack run. Both can be true because the criterion asks
  for *plain* writing and my ten paragraphs are long, uneven coursework
  sentences, which signal one and signal two both score as less machine-like.
  So the test was easier than the claim it was written to protect. It also
  only counts `ai`: 9 of the 10 came back "unsure", which still tells a real
  writer the system could not vouch for them. A tighter version would use
  paragraphs matching the target (short sentences, ordinary vocabulary) and
  would also cap how many come back "unsure".
- **Criterion 2 held by 0.02** (0.7364 − 0.3165 = 0.4199). That is a pass, not
  a comfortable one, and it fails as soon as the human end drifts: it only
  reaches 0.3165 because the human calibration text is casual and lowercase.
- **Criterion 3 was easy by construction.** I chose the four calibration
  inputs, and the same scores came back every trial, so "2 of 3 trials" never
  mattered.

I have not edited `criteria.md`: its rule is that an original line is never
changed, only revised underneath when it turns out to be unmeasurable, and a
target I passed too easily is a different thing from a broken one.

---

## The Improvement

**What I changed:** I validated the input in the route, before either signal
sees the text, no weights or thresholds moved. `app.py::check_text` (new) and
the checks in `app.py::submit` now reject, and log through `audit.log_rejection`:

- text over `config.MAX_TEXT_CHARS` = 20,000 characters (about 3,500 words) → **413** `text_too_long`. The detector only reads 400 tokens, roughly 1,600 characters, so nothing past 20,000 changes the score.
- text containing control characters other than tab, newline and carriage return → **400** `invalid_characters`.
- text with fewer than `config.MIN_WORDS` = 5 words containing a letter → **400** `text_too_short`. Letters are tested with `str.isalpha`, not `[a-z]`, so Arabic, Hebrew and other non-Latin writing counts as writing.
- a `creator_id` that is present but not a string → **400** `invalid_creator_id`. A missing `creator_id` is still allowed.

**Which diagnosis pointed at it:** the route problem (4 in the pattern list):
the one missed criterion (5, bad input) and 5 of the 22 broken attacks (MF03,
MF04, MF05, MF06, RQ06) all came from `app.py::submit` checking the shape of
the request but not its content or size. I chose this over reweighting or
moving a threshold because it is the only change that fixes a failure without
buying it back somewhere else: cutting signal one's weight from 0.5 to 0.3 (and
raising signal two's to 0.7) leaves all six of FP02–FP07 above 0.65, the
lowest is 0.672, because signal two agrees with signal one on those, and moving
`AI_THRESHOLD` above 0.76 to clear them would also push the clearly-AI
calibration text (0.7364) out of the AI band, breaking criterion 3's AI label.

### Attack Run - After

`python run_attacks.py --set attack_set --label after`
(`results/attack_run_2026-11-04_1804_after.md`). Every attack that still
reaches the model scores exactly what it scored before; only inputs that are
now rejected changed. Combined score is from the audit log; a bare status
means the request was rejected before scoring.

| Family             | Attacks      | Before: held / broke | After: held / broke |
| ------------------ | ------------ | -------------------- | ------------------- |
| evasion            | 10           | 1 / 9                | 1 / 9               |
| false_positive     | 8            | 2 / 6                | 2 / 6               |
| prompt_injection   | 6            | 5 / 1                | 5 / 1               |
| malformed (MF, RQ) | 20           | 14 / 6               | 19 / 1              |
| flood_same_creator | 12           | 12 / 0               | 12 / 0              |
| **Total**    | **56** | **34 / 22**    | **39 / 17**   |

| ID      | Going for                                              | Before           | Verdict | After            | Verdict        |
| ------- | ------------------------------------------------------ | ---------------- | ------- | ---------------- | -------------- |
| EV01    | signal two: typos raise word variety                   | 200 human 0.287  | BROKE   | 200 human 0.287  | BROKE          |
| EV02    | signal two: broken-up sentences raise length spread    | 200 unsure 0.500 | BROKE   | 200 unsure 0.500 | BROKE          |
| EV03    | signal two: a pasted quotation changes the shape       | 200 unsure 0.604 | BROKE   | 200 unsure 0.604 | BROKE          |
| EV04    | signal one: unusual words raise perplexity             | 200 unsure 0.631 | BROKE   | 200 unsure 0.631 | BROKE          |
| EV05    | both signals: heavy human editing pass                 | 200 unsure 0.413 | BROKE   | 200 unsure 0.413 | BROKE          |
| EV06    | signal two: one very long sentence and one very short  | 200 unsure 0.495 | BROKE   | 200 unsure 0.495 | BROKE          |
| EV07    | signal two: padding with punctuation                   | 200 unsure 0.624 | BROKE   | 200 unsure 0.624 | BROKE          |
| EV08    | signal one: text below the token window                | 200 unsure 0.409 | BROKE   | 200 unsure 0.409 | BROKE          |
| EV09    | both: AI text with a human opening paragraph bolted on | 200 unsure 0.633 | BROKE   | 200 unsure 0.633 | BROKE          |
| EV10    | signal two: repeated stanza structure                  | 200 ai 0.871     | HELD    | 200 ai 0.871     | HELD           |
| FP01    | plain, clear human writing with no flourishes          | 200 unsure 0.614 | HELD    | 200 unsure 0.614 | HELD           |
| FP02    | human writing in a formal register                     | 200 ai 0.711     | BROKE   | 200 ai 0.711     | BROKE          |
| FP03    | a non-native English speaker writing carefully         | 200 ai 0.727     | BROKE   | 200 ai 0.727     | BROKE          |
| FP04    | a student essay written to a rubric                    | 200 ai 0.721     | BROKE   | 200 ai 0.721     | BROKE          |
| FP05    | technical documentation written by a person            | 200 ai 0.756     | BROKE   | 200 ai 0.756     | BROKE          |
| FP06    | a person imitating a formal template                   | 200 ai 0.732     | BROKE   | 200 ai 0.732     | BROKE          |
| FP07    | human writing that repeats a phrase deliberately       | 200 ai 0.743     | BROKE   | 200 ai 0.743     | BROKE          |
| FP08    | very short genuine human submission                    | 200 unsure 0.422 | HELD    | 200 unsure 0.422 | HELD           |
| PI01    | instruction to ignore the check                        | 200 unsure 0.465 | HELD    | 200 unsure 0.465 | HELD           |
| PI02    | instruction disguised as a system message              | 200 human 0.322  | BROKE   | 200 human 0.322  | BROKE          |
| PI03    | instruction wrapped in the writer's voice              | 200 unsure 0.558 | HELD    | 200 unsure 0.558 | HELD           |
| PI04    | attempt to make the label text hostile                 | 200 unsure 0.518 | HELD    | 200 unsure 0.518 | HELD           |
| PI05    | attempt to inject into the audit log                   | 200 human 0.300  | HELD    | 200 human 0.300  | HELD           |
| PI06    | instruction plus real human text                       | 200 unsure 0.587 | HELD    | 200 unsure 0.587 | HELD           |
| MF01    | text is only whitespace                                | 400              | HELD    | 400              | HELD           |
| MF02    | text is a single character                             | 400              | HELD    | 400              | HELD           |
| MF03    | text is control characters                             | 200 human 0.167  | BROKE   | 400              | **HELD** |
| MF04    | text is only punctuation                               | 200 human 0.258  | BROKE   | 400              | **HELD** |
| MF05    | text is a very long single word                        | 200 ai 0.832     | BROKE   | 400              | **HELD** |
| MF06    | text is emoji only                                     | 200 ai 0.999     | BROKE   | 400              | **HELD** |
| MF07    | text is right-to-left script                           | 200 ai 0.953     | BROKE   | 200 ai 0.953     | BROKE          |
| MF08    | text is 60,000 characters                              | 200 ai 0.921     | HELD    | 413              | HELD           |
| RQ01    | no text field at all                                   | 400              | HELD    | 400              | HELD           |
| RQ02    | no creator_id                                          | 200 human 0.346  | HELD    | 200 human 0.346  | HELD           |
| RQ03    | text is a number                                       | 400              | HELD    | 400              | HELD           |
| RQ04    | text is a list                                         | 400              | HELD    | 400              | HELD           |
| RQ05    | text is null                                           | 400              | HELD    | 400              | HELD           |
| RQ06    | creator_id is an object                                | 200 human 0.204  | BROKE   | 400              | **HELD** |
| RQ07    | body is a JSON array, not an object                    | 400              | HELD    | 400              | HELD           |
| RQ08    | body is unparseable JSON                               | 400              | HELD    | 400              | HELD           |
| RQ09    | body is empty                                          | 400              | HELD    | 400              | HELD           |
| RQ10    | body is form-encoded, not JSON                         | 400              | HELD    | 400              | HELD           |
| RQ11    | body is JSON claiming to be plain text                 | 429              | HELD    | 429              | HELD           |
| RQ12    | deeply nested JSON                                     | 400              | HELD    | 400              | HELD           |
| FL01_01 | 20 rapid submissions from one creator                  | 200 human 0.188  | HELD    | 200 human 0.188  | HELD           |
| FL01_02 | 20 rapid submissions from one creator                  | 200 human 0.188  | HELD    | 200 human 0.188  | HELD           |
| FL01_03 | 20 rapid submissions from one creator                  | 200 human 0.188  | HELD    | 200 human 0.188  | HELD           |
| FL01_04 | 20 rapid submissions from one creator                  | 200 human 0.188  | HELD    | 200 human 0.188  | HELD           |
| FL01_05 | 20 rapid submissions from one creator                  | 200 human 0.188  | HELD    | 200 human 0.188  | HELD           |
| FL01_06 | 20 rapid submissions from one creator                  | 200 human 0.188  | HELD    | 200 human 0.188  | HELD           |
| FL01_07 | 20 rapid submissions from one creator                  | 429              | HELD    | 429              | HELD           |
| FL01_08 | 20 rapid submissions from one creator                  | 429              | HELD    | 429              | HELD           |
| FL01_09 | 20 rapid submissions from one creator                  | 429              | HELD    | 429              | HELD           |
| FL01_10 | 20 rapid submissions from one creator                  | 429              | HELD    | 429              | HELD           |
| FL01_11 | 20 rapid submissions from one creator                  | 429              | HELD    | 429              | HELD           |
| FL01_12 | 20 rapid submissions from one creator                  | 429              | HELD    | 429              | HELD           |

RQ11 returned 429 in both full runs because it carries no `creator_id`, so it
counts against the IP, and earlier malformed rows had used the allowance. Run
alone after the window it returned 400 both before (`results/attack_run_2026-11-04_1721.md`)
and after (`results/attack_run_2026-11-04_1802.md`), so it is HELD in both.

**Six audit entries for the inputs that changed**, written by
`audit.py::log_rejection`, a rejection carries no scores, and these inputs
used to get a verdict:

```json
{"timestamp": "2026-11-05T02:04:34+00:00", "creator_id": "attacker_MF03", "event": "rejected", "status": "rejected", "reason": "invalid_characters", "detail": "Text contains control characters."}
{"timestamp": "2026-11-05T02:04:34+00:00", "creator_id": "attacker_MF04", "event": "rejected", "status": "rejected", "reason": "text_too_short", "detail": "Text needs at least 5 words that contain letters."}
{"timestamp": "2026-11-05T02:04:34+00:00", "creator_id": "attacker_MF05", "event": "rejected", "status": "rejected", "reason": "text_too_short", "detail": "Text needs at least 5 words that contain letters."}
{"timestamp": "2026-11-05T02:04:34+00:00", "creator_id": "attacker_MF06", "event": "rejected", "status": "rejected", "reason": "text_too_short", "detail": "Text needs at least 5 words that contain letters."}
{"timestamp": "2026-11-05T02:04:34+00:00", "creator_id": "attacker_MF08", "event": "rejected", "status": "rejected", "reason": "text_too_long", "detail": "Text is over 20,000 characters."}
{"timestamp": "2026-11-05T02:04:09+00:00", "creator_id": "unknown", "event": "rejected", "status": "rejected", "reason": "invalid_creator_id", "detail": "creator_id must be a string."}
```

**The criteria, before and after** (`run_eval.py --label after`,
`results/run_2026-11-04_1800_after.md`; the other four are unchanged):

| Criterion          | Before                                                     | After                                                                             |
| ------------------ | ---------------------------------------------------------- | --------------------------------------------------------------------------------- |
| 1. False positives | 0 of 10 AI, every trial, MET                               | 0 of 10 AI, every trial, **MET**                                            |
| 2. Score spread    | 0.4199 every trial, MET                                    | 0.4199 every trial, **MET**                                                 |
| 3. Label coverage  | all three labels, every trial, MET                         | all three labels, every trial, **MET**                                      |
| 4. Appeal path     | 10 of 10, every trial, MET                                 | 10 of 10, every trial, **MET**                                              |
| 5. Bad input       | missing 400, empty 400, 50,000 words **200**, MISSED | missing 400, empty 400, 50,000 words **413**, in every trial, **MET** |

**Did it help, and how do I know:** partly, and not on the problem that
matters most. It fixed the one missed criterion and 5 of 22 broken attacks, but
none of those 5 involves a real writer being accused. The 6 human texts the
service calls AI (FP02–FP07) are exactly as wrong as before, so for the person
this service can hurt, it did not help. It helped where it was aimed and nowhere
else. Broken attacks went from 22 to 17, and criterion 5 went from MISSED to
MET. The 5 attacks it fixed are MF03, MF04, MF05, MF06 (text with nothing to
read now gets a 400 instead of a confident verdict) and RQ06 (a dict
`creator_id` is no longer written to the log). MF08 was already HELD, but the
60,000-character input is now rejected with a 413 instead of scored. I know
because the other 50 rows are identical to the before run, row for row, and the
audit log shows the new rejections.

**What it did not touch, and what it costs.** It did nothing about the pattern
that matters most: signal one reading plain or repetitive text as AI. FP02–FP07
are still accused (0.711–0.757), the evasions still work (EV01–EV09), PI02 still
reads as human, and MF07, a real right-to-left text, is still accused at 0.953
because `stylometry.py::words` has no non-Latin tokens to read. The price is on
the other side of the new checks:

- A real piece longer than 20,000 characters is now refused, not scored. That is about 3,500 words, so a long article or chapter is blocked, where before it was scored on its first 1,600 characters.
- A real piece with fewer than 5 words containing letters is refused. A haiku or a two-line caption would have scored before; it now gets a 400.
- Control characters are rejected outright, including form feeds and vertical tabs that can arrive when text is copied out of a PDF.

None of these is a wrongful accusation, so I judged them cheaper than the
cases above. They are, though, people refused rather than people labeled, and
that is a cost the service did not have before.

---

## What's Still Broken

**Why I stopped.** I made one improvement, as asked, and did not try any of
the fixes below. That is the whole reason: it is not that I tried them and they
failed. I did not have a reason to think any of them is quick, because each
one trades a wrong accusation for a missed detection or the reverse, and I only
have eight human false-positive texts and ten of my own paragraphs to judge
that trade with. Where I give a number below it is arithmetic on scores I
already have, not a result from a run.

**Criteria still missed: none.** All five held in every trial after the change
(criterion 5 went from MISSED to MET). Three of those passes are weaker than
they look, and the first is the one I would tighten: criterion 1 passed only
because my paragraphs are longer and more uneven than the plain writing it was
written about (see the Diagnoses section above), criterion 2 holds by
0.02, and criterion 3 is satisfied by calibration texts I picked.

**The 17 attacks that still get through**, by cause:

| Attacks                                                                  | Cause (stage)                                                                                                                                  | What I'd do                                                                                                                                                                                                                                | Why I didn't                                                                                                                                                                                                                                                                                                                                                                                      |
| ------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| FP02, FP03, FP04, FP05, FP06, FP07, human writing accused (0.711–0.757) | signal one and signal two agree that plain, formal or repetitive text is AI                                                                    | Raise `AI_THRESHOLD` from 0.65 to about 0.76, which sits just above the highest of the six (0.757). The alternative, a perplexity midpoint tuned for plain English (`detector.py`, currently 45), needs calibration data I don't have. | Moving the threshold clears all six, but pushes my clearly-AI calibration text (0.7364) into "unsure", so criterion 3's AI label would depend on EV10-style text (0.871). It trades the accusation I care about most for missed AI, which I judged the right trade but did not make without checking it against more AI samples. Reweighting does not work: at 0.3 / 0.7 all six stay above 0.65. |
| EV03, EV04, EV07, EV09, AI text called "unsure" by 0.01–0.05            | label mapping: the unmodified AI text only reaches 0.663 against an `AI_THRESHOLD` of 0.65                                                   | Lower `AI_THRESHOLD` to about 0.60, which catches all four (0.604, 0.631, 0.624, 0.633).                                                                                                                                                 | It also moves FP01 (human writing, 0.614) from unsure to AI, so seven of the eight human texts would be accused instead of six. That is the trade the other direction, and it contradicts the first row. These two rows cannot both be fixed by the threshold; the real problem is that neither signal gives AI text a high score.                                                                |
| EV01 (typos → human), PI02 (fake system line → human)                  | signal one reads odd text as unpredictable, and the combining rule's disagreement pull then halves the distance to the human reading           | Cap the pull, or score perplexity on a robust statistic (the median per-sentence value) so one strange line cannot dominate.                                                                                                               | The pull is a deliberate choice documented in `scoring.py::combine_signals` (a wrong accusation costs more than a miss), so removing it moves the service toward accusing more people. I'd want to test a cap against the human texts before touching it.                                                                                                                                       |
| EV02, EV06 (broken-up sentences, one long and one short)                 | signal two: sentence-length spread is easy to inflate                                                                                          | Replace spread with a measure that is harder to game, or accept it.                                                                                                                                                                        | Signal two has three simple measures and no better one yet; this is the cheapest attack on it and any fix is a new signal, not a tweak.                                                                                                                                                                                                                                                           |
| EV05 (heavy human edit)                                                  | both signals, correctly                                                                                                                        | Nothing.                                                                                                                                                                                                                                   | A real rewrite of AI text is partly human writing, and "unsure" is a defensible answer. I would not call this a bug.                                                                                                                                                                                                                                                                              |
| EV08 (65-character text)                                                 | signal one has too little context for a stable perplexity                                                                                      | Refuse text under about 20 words, or force "unsure" below it.                                                                                                                                                                              | It would refuse FP08 ("Went for a run. Legs hurt. Worth it.", 8 words), a real short submission that today gets "unsure". Same trade as the length checks I added.                                                                                                                                                                                                                                |
| MF07 (right-to-left script accused at 0.953)                             | signal two: `stylometry.py::words` only matches `[a-z0-9']`, so non-Latin text has no words and scores 1.0; signal one is an English model | Match Unicode letters in `words`, and force "unsure" for text that is mostly non-Latin, since neither signal is built for it.                                                                                                            | It needs a language or script check I did not write. This is a real writer in another language accused with high confidence, so it is the one I'd do first.                                                                                                                                                                                                                                       |

Not on the list because they held: EV10, FP01, FP08, PI01, PI03–PI06 and all
of the flood and malformed rows except the five fixed.

**The trade I'd make if this ran for real:** I would go toward fewer wrong accusations: raise `AI_THRESHOLD` toward 0.76 and add a script check for MF07, accepting that AI text like EV03, EV04, EV07 and EV09 gets through as "unsure". The people who pay are the site and the honest writers whose work competes with AI text that was not caught, and I would rather they pay than a writer who is told their own work is machine-made and has only the appeal to answer with.

---

## The Shape

I am extending this system with **Shape B, harden against failure**. Everything above describes a service that works when everything goes right, and the weakest point on the bad path is signal one: it is a roughly 550 MB local GPT-2 model loaded lazily, and nothing in `/submit` handles it failing. A model that was never downloaded, or an out-of-memory error would end the request in a 500 and leave nothing useful in `logs/audit.jsonl`. I am adding exception handling around `detector.model_signal` so that when signal one fails, `/submit` still answers using signal two alone, marks the response as degraded with lower confidence, and writes the failure and the degraded flag into the audit entry instead of losing them. The new criteria are about what happens on that bad path (a request with the model unavailable still gets a labelled answer, never a 500; every failure leaves a log entry), and I will test them with the same attack and scenario tooling as before, run before and after. I am not changing the thresholds, the weights, or either signal's measures. The system runs on my machine with its logs rather than on a host, because a free 512 MB tier cannot hold the model (see RUNNING.md).

### Out of scope

Three things I thought about doing and decided not to, so the unit stays about the failure path:

- **I am not fixing the accuracy problems listed in What's Still Broken.** That means no change to `AI_THRESHOLD`, the signal weights, the combining rule's disagreement pull, or the MF07 script check I said I would do first on a real deployment. Those are about the service being wrong when it works, and Shape B is about what it does when it breaks. They would also move the numbers the rest of this README justifies, and I would have to redo the before and after runs to defend them.
- **I am not swapping `gpt2` for a smaller model, or adding a third signal, to make failures rarer.** A lighter model would fail less often, but the perplexity midpoint in `detector.py` (currently 45) was set for `gpt2`, so a different model would change every score. The aim is a service that fails safely, not one that fails less because the signal underneath it changed.
- **I am not putting the service on a host or changing how it logs.** It stays on Path B, started by `python app.py`, with `logs/audit.jsonl` as the only record. I am not adding a database, a queue, or retries for a model that is missing or out of memory, because retrying a failure like that gives the same result and only delays the answer.
- **I am not adding a timeout for a model call that hangs.** Python cannot stop a thread that is busy inside `torch`, so a timeout would return to the caller while the stuck call kept using the CPU, and getting that right is more building than this unit has room for. The failures I do handle are the ones that raise an error: a missing model, an out-of-memory error, a load that fails.


---

## Instrumentation

Every request to `/submit` writes one record to `logs/runs.jsonl`, whatever happens to it: decided, degraded, rejected, rate limited or crashed. The hooks are in `app.py` and the record is built by `runlog.py`. It is a separate file from the audit log on purpose: `audit.jsonl` is the record of decisions and appeals with a fixed nine-field shape, and this is the record of *runs*, including the ones that never became a decision.

Each record has the same 21 named fields:

| Field | What it is for |
| ----- | -------------- |
| `timestamp`, `run_id` | when (UTC, to the millisecond) and which run |
| `content_id` | links a decided run to its `audit.jsonl` entry; null if no decision was made |
| `route`, `status_code`, `outcome` | `decided`, `degraded`, `rejected`, `rate_limited` or `error` |
| `creator_id` | who submitted |
| `input` | type, character and word count, and the first 500 characters (`RUN_LOG_INPUT_CHARS` in `config.py`; set it to 0 to keep no text) |
| `output` | status code, guess, confidence, label, and the error and message when there was one |
| `duration_ms`, `cpu_ms` | wall clock for the whole request, and CPU time the process used (it can exceed wall time because torch uses several cores) |
| `model_ms`, `style_ms` | time inside each signal, null if that signal never ran |
| `cold_start` | true if the model was not yet loaded when the run began |
| `model_score`, `style_score`, `combined_score` | the numbers behind the answer |
| `degraded`, `degraded_reason` | whether signal one failed, and why |
| `exception` | null, or type, message and traceback for an unhandled crash |
| `config` | detector model, both thresholds and both weights in force, so a record still means something after the settings change |

**Failures are recorded, not only successes.** The record is written in `teardown_request`, not `after_request`, because Flask skips `after_request` for an unhandled error in debug mode, which is the mode this service runs in by default. A record written there would silently never appear for exactly the runs that went wrong. If writing the record itself fails, `runlog.write` reports it through `logging` to stderr and the request still gets its answer.

**Reading it back:**

```bash
python runlog.py --last 20      # a table of recent runs
python runlog.py --failures     # only runs that did not end in a plain decision
python runlog.py --json         # the raw records
```

### A real session

`python tools/demo_session.py` starts the service, sends one of each kind of outcome, then restarts it with the model unable to load (`AI201_DETECTOR_MODEL=does-not-exist-xyz`) and sends two more. It recorded 18 runs; twelve are pasted below, in the order they happened. The table is a summary of the same twelve entries that follow it.

| # | Outcome | Status | Wall ms | CPU ms | Model ms | creator_id | Result or reason |
| - | ------- | ------ | ------- | ------ | -------- | ---------- | ---------------- |
| 1 | decided | 200 | 67,753 | 22,734 | 67,594 | demo_cold_human | human (model 0.1897, style 0.4433) |
| 2 | decided | 200 | 1,410 | 1,391 | 1,401 | demo_ai | ai (model 0.8162, style 0.6566) |
| 3 | decided | 200 | 753 | 1,438 | 736 | demo_plain | unsure (model 0.6175, style 0.6113) |
| 4 | rejected | 400 | 6 | 0 | - | demo_empty | text is required and must be a non-empty string. |
| 5 | rejected | 400 | 5 | 0 | - | demo_short | Text needs at least 5 words that contain letters. |
| 6 | rejected | 400 | 6 | 0 | - | demo_control | Text contains control characters. |
| 7 | rejected | 400 | 5 | 0 | - | demo_missing | text is required and must be a non-empty string. |
| 8 | rejected | 400 | 6 | 16 | - | null | Request body must be a JSON object. |
| 9 | decided | 200 | 363 | 828 | 358 | demo_burst | unsure (model 0.4125, style 0.7222) |
| 10 | rate_limited | 429 | 3 | 0 | - | demo_burst | Too many submissions. Try again shortly. |
| 11 | degraded | 200 | 38,111 | 14,844 | 38,086 | demo_degraded_ai | DetectorUnavailable: Couldn't load 'does-not-exi... -> unsure |
| 12 | degraded | 200 | 701 | 484 | 696 | demo_degraded_human | DetectorUnavailable: Couldn't load 'does-not-exi... -> unsure |

The entries as written to `logs/runs.jsonl`, unedited:

```json
{"timestamp": "2026-11-09T02:17:47.911+00:00", "run_id": "30b066f076214a1a9d027e7dac343796", "content_id": "2208fdd7-6d0f-40ab-bed1-98580edc566a", "route": "/submit", "status_code": 200, "outcome": "decided", "creator_id": "demo_cold_human", "input": {"type": "str", "chars": 359, "words": 71, "preview": "ok so the bus was late AGAIN and i'm standing there in the drizzle like an idiot, no umbrella, phone at 3%. a woman next to me offers to share hers and we end up talking about her dog (Biscuit, a deaf spaniel, apparently he steals socks?). anyway the 47 finally shows up forty minutes late and she gets off two stops before me. never got her name. wish i had."}, "output": {"status_code": 200, "guess": "human", "confidence": 0.0957, "label": "We think this was probably written by a person.", "error": null, "message": null}, "duration_ms": 67753.0, "cpu_ms": 22734.4, "model_ms": 67594.4, "style_ms": 20.5, "cold_start": true, "model_score": 0.1897, "style_score": 0.4433, "combined_score": 0.3165, "degraded": false, "degraded_reason": null, "exception": null, "config": {"detector_model": "gpt2", "human_threshold": 0.35, "ai_threshold": 0.65, "weight_model": 0.5, "weight_style": 0.5}}
{"timestamp": "2026-11-09T02:17:51.141+00:00", "run_id": "8aa79165ceb240499b0de7d670b44b70", "content_id": "4f3b713b-a238-43a3-8ec3-c84371c19ded", "route": "/submit", "status_code": 200, "outcome": "decided", "creator_id": "demo_ai", "input": {"type": "str", "chars": 681, "words": 84, "preview": "Artificial intelligence is transforming the way organizations operate in the modern world. By leveraging advanced algorithms, businesses can streamline their processes, enhance productivity, and deliver more personalized experiences to their customers. Furthermore, the integration of machine learning into everyday workflows enables teams to make data-driven decisions with greater confidence. It is important to note that responsible adoption requires careful consideration of ethical implications,"}, "output": {"status_code": 200, "guess": "ai", "confidence": 0.2469, "label": "We think this was probably written by AI, or with heavy AI assistance.", "error": null, "message": null}, "duration_ms": 1409.8, "cpu_ms": 1390.6, "model_ms": 1401.4, "style_ms": 0.5, "cold_start": false, "model_score": 0.8162, "style_score": 0.6566, "combined_score": 0.7364, "degraded": false, "degraded_reason": null, "exception": null, "config": {"detector_model": "gpt2", "human_threshold": 0.35, "ai_threshold": 0.65, "weight_model": 0.5, "weight_style": 0.5}}
{"timestamp": "2026-11-09T02:17:51.909+00:00", "run_id": "0b8b6f34fa0548339d482dd9eb801aa3", "content_id": "f99c6cf0-3dc6-4655-aea3-e422edf66e7f", "route": "/submit", "status_code": 200, "outcome": "decided", "creator_id": "demo_plain", "input": {"type": "str", "chars": 523, "words": 103, "preview": "We got to the campsite about four. The pitch was fine, a bit sloped, but there was a tap nearby and the toilets were clean enough. Putting the tent up took longer than it should have because I had forgotten how the poles went. The weather held until Saturday night. Then it rained hard and kept raining. We stayed in the tent and played cards and ate most of the food we had brought for Sunday. On Sunday we packed up wet and drove home early. It was not the weekend we planned but the kids enjoyed i"}, "output": {"status_code": 200, "guess": "unsure", "confidence": 0.2373, "label": "We couldn't tell either way. This piece could have been written by a person or by AI — treat this result as inconclusive, not as an accusation.", "error": null, "message": null}, "duration_ms": 752.7, "cpu_ms": 1437.5, "model_ms": 736.1, "style_ms": 0.5, "cold_start": false, "model_score": 0.6175, "style_score": 0.6113, "combined_score": 0.6144, "degraded": false, "degraded_reason": null, "exception": null, "config": {"detector_model": "gpt2", "human_threshold": 0.35, "ai_threshold": 0.65, "weight_model": 0.5, "weight_style": 0.5}}
{"timestamp": "2026-11-09T02:17:51.937+00:00", "run_id": "7e6743c8c29942959c45ed57d1220264", "content_id": null, "route": "/submit", "status_code": 400, "outcome": "rejected", "creator_id": "demo_empty", "input": {"type": "str", "chars": 0, "words": 0, "preview": ""}, "output": {"status_code": 400, "guess": null, "confidence": null, "label": null, "error": "invalid_request", "message": "text is required and must be a non-empty string."}, "duration_ms": 6.1, "cpu_ms": 0.0, "model_ms": null, "style_ms": null, "cold_start": null, "model_score": null, "style_score": null, "combined_score": null, "degraded": false, "degraded_reason": null, "exception": null, "config": {"detector_model": "gpt2", "human_threshold": 0.35, "ai_threshold": 0.65, "weight_model": 0.5, "weight_style": 0.5}}
{"timestamp": "2026-11-09T02:17:51.961+00:00", "run_id": "acb243ba45ed417a826ae4312c5e11f1", "content_id": null, "route": "/submit", "status_code": 400, "outcome": "rejected", "creator_id": "demo_short", "input": {"type": "str", "chars": 8, "words": 2, "preview": "hi there"}, "output": {"status_code": 400, "guess": null, "confidence": null, "label": null, "error": "invalid_request", "message": "Text needs at least 5 words that contain letters."}, "duration_ms": 4.9, "cpu_ms": 0.0, "model_ms": null, "style_ms": null, "cold_start": null, "model_score": null, "style_score": null, "combined_score": null, "degraded": false, "degraded_reason": null, "exception": null, "config": {"detector_model": "gpt2", "human_threshold": 0.35, "ai_threshold": 0.65, "weight_model": 0.5, "weight_style": 0.5}}
{"timestamp": "2026-11-09T02:17:51.986+00:00", "run_id": "bbe88218db2c48cca3403a76134cfbd3", "content_id": null, "route": "/submit", "status_code": 400, "outcome": "rejected", "creator_id": "demo_control", "input": {"type": "str", "chars": 39, "words": 8, "preview": "Hello there\u0007 this has a bell inside it."}, "output": {"status_code": 400, "guess": null, "confidence": null, "label": null, "error": "invalid_request", "message": "Text contains control characters."}, "duration_ms": 5.8, "cpu_ms": 0.0, "model_ms": null, "style_ms": null, "cold_start": null, "model_score": null, "style_score": null, "combined_score": null, "degraded": false, "degraded_reason": null, "exception": null, "config": {"detector_model": "gpt2", "human_threshold": 0.35, "ai_threshold": 0.65, "weight_model": 0.5, "weight_style": 0.5}}
{"timestamp": "2026-11-09T02:17:52.072+00:00", "run_id": "efa5e9055760419e903f811e13d2068f", "content_id": null, "route": "/submit", "status_code": 400, "outcome": "rejected", "creator_id": "demo_missing", "input": {"type": "missing", "chars": null, "words": null, "preview": null}, "output": {"status_code": 400, "guess": null, "confidence": null, "label": null, "error": "invalid_request", "message": "text is required and must be a non-empty string."}, "duration_ms": 5.2, "cpu_ms": 0.0, "model_ms": null, "style_ms": null, "cold_start": null, "model_score": null, "style_score": null, "combined_score": null, "degraded": false, "degraded_reason": null, "exception": null, "config": {"detector_model": "gpt2", "human_threshold": 0.35, "ai_threshold": 0.65, "weight_model": 0.5, "weight_style": 0.5}}
{"timestamp": "2026-11-09T02:17:52.096+00:00", "run_id": "b8151f876fdb41fabfa6d5e64095ab30", "content_id": null, "route": "/submit", "status_code": 400, "outcome": "rejected", "creator_id": null, "input": {"type": "missing", "chars": null, "words": null, "preview": null}, "output": {"status_code": 400, "guess": null, "confidence": null, "label": null, "error": "invalid_request", "message": "Request body must be a JSON object."}, "duration_ms": 5.8, "cpu_ms": 15.6, "model_ms": null, "style_ms": null, "cold_start": null, "model_score": null, "style_score": null, "combined_score": null, "degraded": false, "degraded_reason": null, "exception": null, "config": {"detector_model": "gpt2", "human_threshold": 0.35, "ai_threshold": 0.65, "weight_model": 0.5, "weight_style": 0.5}}
{"timestamp": "2026-11-09T02:17:52.469+00:00", "run_id": "f6dd08af6d77499b8a24d260da826b72", "content_id": "7e3b6720-bd1e-420b-aaf3-ff24b9e45b02", "route": "/submit", "status_code": 200, "outcome": "decided", "creator_id": "demo_burst", "input": {"type": "str", "chars": 60, "words": 12, "preview": "We missed the last train, so we walked home along the canal."}, "output": {"status_code": 200, "guess": "unsure", "confidence": 0.5507, "label": "We couldn't tell either way. This piece could have been written by a person or by AI — treat this result as inconclusive, not as an accusation.", "error": null, "message": null}, "duration_ms": 362.9, "cpu_ms": 828.1, "model_ms": 358.5, "style_ms": 0.1, "cold_start": false, "model_score": 0.4125, "style_score": 0.7222, "combined_score": 0.5674, "degraded": false, "degraded_reason": null, "exception": null, "config": {"detector_model": "gpt2", "human_threshold": 0.35, "ai_threshold": 0.65, "weight_model": 0.5, "weight_style": 0.5}}
{"timestamp": "2026-11-09T02:17:54.208+00:00", "run_id": "47ec1bb8969b4c7eb871ac9a79339406", "content_id": null, "route": "/submit", "status_code": 429, "outcome": "rate_limited", "creator_id": "demo_burst", "input": {"type": "str", "chars": 60, "words": 12, "preview": "We missed the last train, so we walked home along the canal."}, "output": {"status_code": 429, "guess": null, "confidence": null, "label": null, "error": "rate_limited", "message": "Too many submissions. Try again shortly."}, "duration_ms": 3.3, "cpu_ms": 0.0, "model_ms": null, "style_ms": null, "cold_start": null, "model_score": null, "style_score": null, "combined_score": null, "degraded": false, "degraded_reason": null, "exception": null, "config": {"detector_model": "gpt2", "human_threshold": 0.35, "ai_threshold": 0.65, "weight_model": 0.5, "weight_style": 0.5}}
{"timestamp": "2026-11-09T02:18:36.088+00:00", "run_id": "622787f655234b37a131f309c184f508", "content_id": "3d4131c8-bf9d-493c-8a37-3ce655898a4e", "route": "/submit", "status_code": 200, "outcome": "degraded", "creator_id": "demo_degraded_ai", "input": {"type": "str", "chars": 681, "words": 84, "preview": "Artificial intelligence is transforming the way organizations operate in the modern world. By leveraging advanced algorithms, businesses can streamline their processes, enhance productivity, and deliver more personalized experiences to their customers. Furthermore, the integration of machine learning into everyday workflows enables teams to make data-driven decisions with greater confidence. It is important to note that responsible adoption requires careful consideration of ethical implications,"}, "output": {"status_code": 200, "guess": "unsure", "confidence": 0.0, "label": "We couldn't tell either way. This piece could have been written by a person or by AI — treat this result as inconclusive, not as an accusation. Only part of our check could run, so this is less certain than usual.", "error": null, "message": null}, "duration_ms": 38111.0, "cpu_ms": 14843.8, "model_ms": 38085.9, "style_ms": 0.7, "cold_start": true, "model_score": null, "style_score": 0.6566, "combined_score": 0.6566, "degraded": true, "degraded_reason": "DetectorUnavailable: Couldn't load 'does-not-exist-xyz': does-not-exist-xyz is not a local folder and is not a valid model identifier listed on 'https://huggingface.co/models' If this is a private repository, make sure to pass a token having permission to this repo either by logging in with `hf auth", "exception": null, "config": {"detector_model": "does-not-exist-xyz", "human_threshold": 0.35, "ai_threshold": 0.65, "weight_model": 0.5, "weight_style": 0.5}}
{"timestamp": "2026-11-09T02:18:36.924+00:00", "run_id": "b5616381496d47b0869d5ecd133c3702", "content_id": "8068539e-9312-4611-8e3f-cca266ec21d8", "route": "/submit", "status_code": 200, "outcome": "degraded", "creator_id": "demo_degraded_human", "input": {"type": "str", "chars": 359, "words": 71, "preview": "ok so the bus was late AGAIN and i'm standing there in the drizzle like an idiot, no umbrella, phone at 3%. a woman next to me offers to share hers and we end up talking about her dog (Biscuit, a deaf spaniel, apparently he steals socks?). anyway the 47 finally shows up forty minutes late and she gets off two stops before me. never got her name. wish i had."}, "output": {"status_code": 200, "guess": "unsure", "confidence": 0.311, "label": "We couldn't tell either way. This piece could have been written by a person or by AI — treat this result as inconclusive, not as an accusation. Only part of our check could run, so this is less certain than usual.", "error": null, "message": null}, "duration_ms": 701.2, "cpu_ms": 484.4, "model_ms": 695.9, "style_ms": 0.4, "cold_start": true, "model_score": null, "style_score": 0.4433, "combined_score": 0.4433, "degraded": true, "degraded_reason": "DetectorUnavailable: Couldn't load 'does-not-exist-xyz': does-not-exist-xyz is not a local folder and is not a valid model identifier listed on 'https://huggingface.co/models' If this is a private repository, make sure to pass a token having permission to this repo either by logging in with `hf auth", "exception": null, "config": {"detector_model": "does-not-exist-xyz", "human_threshold": 0.35, "ai_threshold": 0.65, "weight_model": 0.5, "weight_style": 0.5}}
```

**What these show:**

- **The model is the cost.** On decided runs `model_ms` is nearly all of `duration_ms` (entry 2: 1401 of 1410 ms), and the style signal is a few milliseconds. A rejected request costs about 5 ms and never touches the model.
- **The cold start is large.** Entry 1 took 67.8 s of wall time but only 22.7 s of CPU, so most of it was waiting rather than computing. `config.py` says the first call takes "ten to twenty seconds"; on this machine it took more than three times that.
- **The rate limit behaves as configured.** The burst from one `creator_id` gets six 200s and then 429s, matching 6 per minute (entry 9 is the first of the 200s, entry 10 the first 429). The 429 is a record of its own, with no model time.
- **Degraded mode is visible in the log.** Entries 11 and 12 have `outcome: degraded`, a null `model_score`, and the reason. Entry 11's `guess` is `unsure` even though its `style_score` (0.6566) is above `AI_THRESHOLD` (0.65), which is the cap in `scoring.label_without_model` doing its job, narrowly, and its `combined_score` is the style score alone.
- **The first degraded request was slow.** Entry 11 took 38.1 s and 14.8 s of CPU before falling back; entry 12, the next one, took 0.7 s. I have not isolated the cause. My reading is that the first request still imports `torch` and `transformers` before the model load fails and the later ones do not, but I did not time the import separately. Both degraded entries say `cold_start: true` because the model never loaded, which is accurate but means the flag stays true for every degraded run.
- **The log keeps part of the submitted text.** `input.preview` holds up to 500 characters, which `audit.jsonl` does not. That is a choice to revisit if the text should not be stored.

**What is not shown here:** a crash inside the route. There is no honest way to make the live service raise an unhandled error without changing its code, so that path (and a crash that propagates out of Flask, as in debug mode) is covered by `tests/test_runlog.py`, which passes 23 of 23 tests, not by a pasted record.

---

## What It Costs

This system calls no paid API and uses no tokens: signal one is a model that runs on my own machine. So the cost of a run is compute, in three forms: **wall time** (what a writer waits), **CPU time**, and **memory**.

**The number, measured on this machine** (11th Gen Intel Core i5-1135G7, 4 cores / 8 threads, Windows 11, Python 3.11.9, `gpt2`, 400-token limit), over 30 warm runs of one 103-word text:

| | Mean | Median | 90th percentile | Fastest | Slowest |
| - | ---- | ------ | --------------- | ------- | ------- |
| Wall time | **5.28 s** | 2.55 s | 20.9 s | 0.66 s | 23.0 s |
| CPU time | **2.39 s** | 1.88 s | 5.16 s | 1.28 s | 6.19 s |

The first run after a launch, where the model loads, is a different cost: **60.6 s** mean wall time over 3 launches (56.1, 59.7, 65.9) and 20.9 s of CPU. After loading, the server process holds about **490 MB** (working set 482 to 503 MB, up from 41 MB), which is why this system takes Path B: it already uses nearly all of a 512 MB free tier before it has answered anything. That memory figure is the Windows working set from `tasklist`, so it is not directly comparable to a Linux resident-set number.

Length matters up to the model's token limit and then stops: warm CPU averaged 1.3 s for a 12-word text, 2.4 s for the 103-word one, and 8.1 s for a 515-word one that the model truncates at 400 tokens.

**Read the mean with care.** The same text took anywhere from 0.66 s to 23 s, a factor of 35, and the slow runs bunch up at the end of each launch (runs 8 to 10 of launches 2 and 3 took 9 to 23 s). CPU time for the identical work rose in the slowest of those runs, from about 1.5 s to 5 to 6 s, so the machine itself slowed down partway through. The demo session above, run soon after, handled the 12-word text in 0.3 to 0.4 s per request, where the measurement averaged 5.7 s for it. I do not know what was competing for the machine, and I did not find out, so I report the mean because it was asked for, the median because it is the better description, and the fastest run (0.66 s) as the closest I have to a quiet-machine floor. No single one of them is "the cost".

**How it was measured**, so it can be checked and repeated (`python tools/measure_cost.py`):

1. The tool starts its own server (`python app.py`, debug off) on a spare port, so the first request after launch is a true cold start. It does this 3 times, and times each cold run on its own.
2. After each launch it sends 10 warm requests of one fixed text, one at a time, each under its own `creator_id` so the rate limiter never interferes.
3. Wall time, CPU time and per-signal time are read back from the service's own run record in `logs/runs.jsonl` (`duration_ms`, `cpu_ms`, `model_ms`), matched by `creator_id`, not taken from the response. A client-side `perf_counter` around each call is kept alongside as a check, and runs about 50 to 150 ms higher.
4. `cpu_ms` is process-wide CPU time over the request (`time.process_time`). It is attributable to one request only because requests were sent one at a time.
5. Memory is read from `tasklist` for the process listening on the port, before and after the cold run.

The full report, with every warm run in order, is `results/cost_2026-11-08_1812.md`. The runs themselves are in `logs/runs.jsonl` under `creator_id`s starting `cost_20261108180312_`. A repeat takes about ten minutes, and should be done with nothing else running.

This is what criteria 9.2 and 9.4 in `criteria.md` are measured against. 9.4 (90% of warm runs within 5 s) was known to fail when written, and does. 9.2 (a degraded answer in 1 s median, 3 s at most) is probably missed too, because of the 38.1 s first degraded request above, though I have not yet run it as written.

<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST, unit 7

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
       [ ] Repository URL submitted, WRITE IT DOWN

     SUBMISSION CHECKLIST, unit 8

       [ ] Rate limiting on /submit, with your numbers justified
       [ ] The pasted run of status codes showing 429
       [ ] Audit log with all nine fields, recording rejections too
       [ ] The attack set run IN FULL, every input with an outcome
       [ ] Ten audit log entries pasted as text
       [ ] Five criteria across three trials
       [ ] A diagnosis for every miss and every broken attack, stage AND mechanism
       [ ] One improvement, with Attack Run, After
       [ ] What's Still Broken, including the production trade
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
