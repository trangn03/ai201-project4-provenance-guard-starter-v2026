# Attack run — after

- Produced by: `run_attacks.py::main`
- Service: `app.py::submit`
- 56 attacks · 2026-11-04 18:04
- Auto-marked BROKE (5xx, crash, no response): **0**
- Left for you to judge: **56**

The Verdict column is blank where a script can't honestly decide. Whether
an evasion worked depends on where you put your thresholds — read the
`targets` column, look at what came back, and write HELD or BROKE yourself.

Each attack submits as creator_id `attacker_<id>`, and the content_id it
came back with is in the table — either one will match this run against your
audit log when you go looking for the ten entries to paste.

| ID | Family | Targeting | Status | Content ID | Guess | Score | Verdict |
|---|---|---|---|---|---|---|---|
| EV01 | evasion | signal two: typos raise word variety | 200 | `10bde531-23a9-4109-9a6a-7596600f7268` | human | 0.181 | BROKE |
| EV02 | evasion | signal two: broken-up sentences raise length spread | 200 | `8195e05b-47be-4385-91ce-aff32996c65b` | unsure | 1.000 | BROKE |
| EV03 | evasion | signal two: a pasted quotation changes the shape | 200 | `55f130b6-e99c-4b95-b654-d23d6c9d5e9b` | unsure | 0.309 | BROKE |
| EV04 | evasion | signal one: unusual words raise perplexity | 200 | `62a6ca83-a4e5-4e1f-b9d0-0204d02dba88` | unsure | 0.124 | BROKE |
| EV05 | evasion | both signals: heavy human editing pass | 200 | `671a00d6-eb08-4910-a869-3747faf8e587` | unsure | 0.422 | BROKE |
| EV06 | evasion | signal two: one very long sentence and one very short | 200 | `5f9d734c-1de5-4d98-979c-3275dda92099` | unsure | 0.965 | BROKE |
| EV07 | evasion | signal two: padding with punctuation | 200 | `420db8e7-7201-4d36-99bc-df4afa6bc329` | unsure | 0.173 | BROKE |
| EV08 | evasion | signal one: text below the token window | 200 | `27ca3e8c-968c-4946-b986-e7af77fccccc` | unsure | 0.392 | BROKE |
| EV09 | evasion | both: AI text with a human opening paragraph bolted on | 200 | `cda8e308-9854-4bd2-8afe-e183cd4b51e0` | unsure | 0.113 | BROKE |
| EV10 | evasion | signal two: repeated stanza structure | 200 | `a0a8268e-e610-4196-afc3-d9942924d6f5` | ai | 0.630 | HELD |
| FP01 | false_positive | plain, clear human writing with no flourishes | 200 | `cc2bb153-9abc-40af-820f-f9b2081c73c0` | unsure | 0.237 | HELD |
| FP02 | false_positive | human writing in a formal register | 200 | `33e57020-f1ee-4978-b951-1623d9a5abf3` | ai | 0.174 | BROKE |
| FP03 | false_positive | a non-native English speaker writing carefully | 200 | `364b8215-97cd-4305-a64e-d5d100d2073c` | ai | 0.221 | BROKE |
| FP04 | false_positive | a student essay written to a rubric | 200 | `b5e25eba-9161-434a-8330-1c8cdc148b33` | ai | 0.202 | BROKE |
| FP05 | false_positive | technical documentation written by a person | 200 | `d683f6c8-e2b9-4846-9bb3-c961ccc055a8` | ai | 0.304 | BROKE |
| FP06 | false_positive | a person imitating a formal template | 200 | `1a0851b6-a4a5-4a02-a071-8c2edea2304a` | ai | 0.234 | BROKE |
| FP07 | false_positive | human writing that repeats a phrase deliberately | 200 | `c1345338-b860-49ca-bf9e-65da068b56a6` | ai | 0.265 | BROKE |
| FP08 | false_positive | very short genuine human submission | 200 | `3c14077c-eb90-4385-a43d-65d0f07a7fec` | unsure | 0.482 | HELD |
| PI01 | prompt_injection | instruction to ignore the check | 200 | `ab4bdd65-5e76-4a2d-a7b1-189346e660ab` | unsure | 0.769 | HELD |
| PI02 | prompt_injection | instruction disguised as a system message | 200 | `17419cc4-1c58-47fe-8956-bf9fb9e7489b` | human | 0.080 | BROKE |
| PI03 | prompt_injection | instruction wrapped in the writer's voice | 200 | `61461004-f784-4acc-bce8-7bb0ac649519` | unsure | 0.612 | HELD |
| PI04 | prompt_injection | attempt to make the label text hostile | 200 | `892bb60d-af0a-4228-835f-8e9be24ccfc1` | unsure | 0.879 | HELD |
| PI05 | prompt_injection | attempt to inject into the audit log | 200 | `8e12ec7e-c5b7-458f-a5f6-9439bba8c767` | human | 0.141 | HELD |
| PI06 | prompt_injection | instruction plus real human text | 200 | `736bc501-d528-4837-815c-9a5e1c25dcbe` | unsure | 0.421 | HELD |
| MF01 | malformed | text is only whitespace | 400 | `—` | — | — | HELD |
| MF02 | malformed | text is a single character | 400 | `—` | — | — | HELD |
| MF03 | malformed | text is control characters | 400 | `—` | — | — | HELD |
| MF04 | malformed | text is only punctuation | 400 | `—` | — | — | HELD |
| MF05 | malformed | text is a very long single word | 400 | `—` | — | — | HELD |
| MF06 | malformed | text is emoji only | 400 | `—` | — | — | HELD |
| MF07 | malformed | text is right-to-left script | 200 | `2468b11c-09bc-4520-b8c9-3a503cffa28b` | ai | 0.866 | BROKE |
| MF08 | malformed | text is 60,000 characters | 413 | `—` | — | — | HELD |
| RQ01 | malformed | no text field at all | 400 | `—` | — | — | HELD |
| RQ02 | malformed | no creator_id | 200 | `20f6f661-6560-4169-b511-949b5ef433d4` | human | 0.011 | HELD |
| RQ03 | malformed | text is a number | 400 | `—` | — | — | HELD |
| RQ04 | malformed | text is a list | 400 | `—` | — | — | HELD |
| RQ05 | malformed | text is null | 400 | `—` | — | — | HELD |
| RQ06 | malformed | creator_id is an object | 400 | `—` | — | — | HELD |
| RQ07 | malformed | body is a JSON array, not an object | 400 | `—` | — | — | HELD |
| RQ08 | malformed | body is unparseable JSON | 400 | `—` | — | — | HELD |
| RQ09 | malformed | body is empty | 400 | `—` | — | — | HELD |
| RQ10 | malformed | body is form-encoded, not JSON | 400 | `—` | — | — | HELD |
| RQ11 | malformed | body is JSON claiming to be plain text | 429 | `—` | — | — | HELD |
| RQ12 | malformed | deeply nested JSON | 400 | `—` | — | — | HELD |
| FL01_01 | flood_same_creator | 20 rapid submissions from one creator | 200 | `bfa31a69-db54-4718-a02d-db5713b1bf36` | human | 0.462 | HELD |
| FL01_02 | flood_same_creator | 20 rapid submissions from one creator | 200 | `c61a76cf-e67d-4ab3-b363-7ba91d2ec237` | human | 0.462 | HELD |
| FL01_03 | flood_same_creator | 20 rapid submissions from one creator | 200 | `f043ea31-c7c5-432b-98b3-8821fd7dff97` | human | 0.462 | HELD |
| FL01_04 | flood_same_creator | 20 rapid submissions from one creator | 200 | `701472fd-7b8f-4218-9614-29aa82d5d8af` | human | 0.462 | HELD |
| FL01_05 | flood_same_creator | 20 rapid submissions from one creator | 200 | `f1b436cf-6f0d-405b-bf87-8ccd30483cd0` | human | 0.462 | HELD |
| FL01_06 | flood_same_creator | 20 rapid submissions from one creator | 200 | `e9f074b7-5cc3-4956-b741-ad97e45240e8` | human | 0.462 | HELD |
| FL01_07 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — | HELD |
| FL01_08 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — | HELD |
| FL01_09 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — | HELD |
| FL01_10 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — | HELD |
| FL01_11 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — | HELD |
| FL01_12 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — | HELD |

---

## By family

| Family | Attacks | Auto-BROKE | Left to judge |
|---|---|---|---|
| `evasion` | 10 | 0 | 10 |
| `false_positive` | 8 | 0 | 8 |
| `flood_same_creator` | 12 | 0 | 12 |
| `malformed` | 20 | 0 | 20 |
| `prompt_injection` | 6 | 0 | 6 |

> The **false_positive** family is the one to look at hardest. Those are
> written to be genuine human writing that reads as machine-like. Every one
> your service calls AI is a real writer it would have accused.

---

## What came back

The detail behind the table. Paste the interesting failures into your
README — the ones that show something, not the ten easiest.

### EV01 — `evasion`

*Targeting:* signal two: typos raise word variety

```json
{
  "id": "EV01",
  "status": 200,
  "content_id": "10bde531-23a9-4109-9a6a-7596600f7268",
  "creator_id": "attacker_EV01",
  "guess": "human",
  "confidence": 0.1809,
  "model_score": 0.1635,
  "style_score": 0.6562,
  "label": "We think this was probably written by a person.",
  "error": null,
  "verdict": ""
}
```

### EV02 — `evasion`

*Targeting:* signal two: broken-up sentences raise length spread

```json
{
  "id": "EV02",
  "status": 200,
  "content_id": "8195e05b-47be-4385-91ce-aff32996c65b",
  "creator_id": "attacker_EV02",
  "guess": "unsure",
  "confidence": 1.0,
  "model_score": 0.5943,
  "style_score": 0.4056,
  "label": "We couldn't tell either way. This piece could have been written by a person or by AI \u2014 treat this result as inconclusive, not as an accusation.",
  "error": null,
  "verdict": ""
}
```

### EV03 — `evasion`

*Targeting:* signal two: a pasted quotation changes the shape

```json
{
  "id": "EV03",
  "status": 200,
  "content_id": "55f130b6-e99c-4b95-b654-d23d6c9d5e9b",
  "creator_id": "attacker_EV03",
  "guess": "unsure",
  "confidence": 0.3093,
  "model_score": 0.6662,
  "style_score": 0.5409,
  "label": "We couldn't tell either way. This piece could have been written by a person or by AI \u2014 treat this result as inconclusive, not as an accusation.",
  "error": null,
  "verdict": ""
}
```

### EV04 — `evasion`

*Targeting:* signal one: unusual words raise perplexity

```json
{
  "id": "EV04",
  "status": 200,
  "content_id": "62a6ca83-a4e5-4e1f-b9d0-0204d02dba88",
  "creator_id": "attacker_EV04",
  "guess": "unsure",
  "confidence": 0.124,
  "model_score": 0.6114,
  "style_score": 0.6513,
  "label": "We couldn't tell either way. This piece could have been written by a person or by AI \u2014 treat this result as inconclusive, not as an accusation.",
  "error": null,
  "verdict": ""
}
```

### EV05 — `evasion`

*Targeting:* both signals: heavy human editing pass

```json
{
  "id": "EV05",
  "status": 200,
  "content_id": "671a00d6-eb08-4910-a869-3747faf8e587",
  "creator_id": "attacker_EV05",
  "guess": "unsure",
  "confidence": 0.422,
  "model_score": 0.3212,
  "style_score": 0.5053,
  "label": "We couldn't tell either way. This piece could have been written by a person or by AI \u2014 treat this result as inconclusive, not as an accusation.",
  "error": null,
  "verdict": ""
}
```

### EV06 — `evasion`

*Targeting:* signal two: one very long sentence and one very short

```json
{
  "id": "EV06",
  "status": 200,
  "content_id": "5f9d734c-1de5-4d98-979c-3275dda92099",
  "creator_id": "attacker_EV06",
  "guess": "unsure",
  "confidence": 0.9647,
  "model_score": 0.5727,
  "style_score": 0.4167,
  "label": "We couldn't tell either way. This piece could have been written by a person or by AI \u2014 treat this result as inconclusive, not as an accusation.",
  "error": null,
  "verdict": ""
}
```

### EV07 — `evasion`

*Targeting:* signal two: padding with punctuation

```json
{
  "id": "EV07",
  "status": 200,
  "content_id": "420db8e7-7201-4d36-99bc-df4afa6bc329",
  "creator_id": "attacker_EV07",
  "guess": "unsure",
  "confidence": 0.1727,
  "model_score": 0.5862,
  "style_score": 0.6621,
  "label": "We couldn't tell either way. This piece could have been written by a person or by AI \u2014 treat this result as inconclusive, not as an accusation.",
  "error": null,
  "verdict": ""
}
```

### EV08 — `evasion`

*Targeting:* signal one: text below the token window

```json
{
  "id": "EV08",
  "status": 200,
  "content_id": "27ca3e8c-968c-4946-b986-e7af77fccccc",
  "creator_id": "attacker_EV08",
  "guess": "unsure",
  "confidence": 0.392,
  "model_score": 0.2452,
  "style_score": 0.5724,
  "label": "We couldn't tell either way. This piece could have been written by a person or by AI \u2014 treat this result as inconclusive, not as an accusation.",
  "error": null,
  "verdict": ""
}
```

### EV09 — `evasion`

*Targeting:* both: AI text with a human opening paragraph bolted on

```json
{
  "id": "EV09",
  "status": 200,
  "content_id": "cda8e308-9854-4bd2-8afe-e183cd4b51e0",
  "creator_id": "attacker_EV09",
  "guess": "unsure",
  "confidence": 0.1127,
  "model_score": 0.7042,
  "style_score": 0.5619,
  "label": "We couldn't tell either way. This piece could have been written by a person or by AI \u2014 treat this result as inconclusive, not as an accusation.",
  "error": null,
  "verdict": ""
}
```

### EV10 — `evasion`

*Targeting:* signal two: repeated stanza structure

```json
{
  "id": "EV10",
  "status": 200,
  "content_id": "a0a8268e-e610-4196-afc3-d9942924d6f5",
  "creator_id": "attacker_EV10",
  "guess": "ai",
  "confidence": 0.63,
  "model_score": 0.9792,
  "style_score": 0.7619,
  "label": "We think this was probably written by AI, or with heavy AI assistance.",
  "error": null,
  "verdict": ""
}
```

### FP01 — `false_positive`

*Targeting:* plain, clear human writing with no flourishes

```json
{
  "id": "FP01",
  "status": 200,
  "content_id": "cc2bb153-9abc-40af-820f-f9b2081c73c0",
  "creator_id": "attacker_FP01",
  "guess": "unsure",
  "confidence": 0.2373,
  "model_score": 0.6175,
  "style_score": 0.6113,
  "label": "We couldn't tell either way. This piece could have been written by a person or by AI \u2014 treat this result as inconclusive, not as an accusation.",
  "error": null,
  "verdict": ""
}
```

### FP02 — `false_positive`

*Targeting:* human writing in a formal register

```json
{
  "id": "FP02",
  "status": 200,
  "content_id": "33e57020-f1ee-4978-b951-1623d9a5abf3",
  "creator_id": "attacker_FP02",
  "guess": "ai",
  "confidence": 0.1737,
  "model_score": 0.7387,
  "style_score": 0.683,
  "label": "We think this was probably written by AI, or with heavy AI assistance.",
  "error": null,
  "verdict": ""
}
```

### FP03 — `false_positive`

*Targeting:* a non-native English speaker writing carefully

```json
{
  "id": "FP03",
  "status": 200,
  "content_id": "364b8215-97cd-4305-a64e-d5d100d2073c",
  "creator_id": "attacker_FP03",
  "guess": "ai",
  "confidence": 0.2209,
  "model_score": 0.8051,
  "style_score": 0.6496,
  "label": "We think this was probably written by AI, or with heavy AI assistance.",
  "error": null,
  "verdict": ""
}
```

### FP04 — `false_positive`

*Targeting:* a student essay written to a rubric

```json
{
  "id": "FP04",
  "status": 200,
  "content_id": "b5e25eba-9161-434a-8330-1c8cdc148b33",
  "creator_id": "attacker_FP04",
  "guess": "ai",
  "confidence": 0.2017,
  "model_score": 0.8329,
  "style_score": 0.6082,
  "label": "We think this was probably written by AI, or with heavy AI assistance.",
  "error": null,
  "verdict": ""
}
```

### FP05 — `false_positive`

*Targeting:* technical documentation written by a person

```json
{
  "id": "FP05",
  "status": 200,
  "content_id": "d683f6c8-e2b9-4846-9bb3-c961ccc055a8",
  "creator_id": "attacker_FP05",
  "guess": "ai",
  "confidence": 0.3043,
  "model_score": 0.8005,
  "style_score": 0.7125,
  "label": "We think this was probably written by AI, or with heavy AI assistance.",
  "error": null,
  "verdict": ""
}
```

### FP06 — `false_positive`

*Targeting:* a person imitating a formal template

```json
{
  "id": "FP06",
  "status": 200,
  "content_id": "1a0851b6-a4a5-4a02-a071-8c2edea2304a",
  "creator_id": "attacker_FP06",
  "guess": "ai",
  "confidence": 0.2337,
  "model_score": 0.8814,
  "style_score": 0.5822,
  "label": "We think this was probably written by AI, or with heavy AI assistance.",
  "error": null,
  "verdict": ""
}
```

### FP07 — `false_positive`

*Targeting:* human writing that repeats a phrase deliberately

```json
{
  "id": "FP07",
  "status": 200,
  "content_id": "c1345338-b860-49ca-bf9e-65da068b56a6",
  "creator_id": "attacker_FP07",
  "guess": "ai",
  "confidence": 0.2649,
  "model_score": 0.8816,
  "style_score": 0.6038,
  "label": "We think this was probably written by AI, or with heavy AI assistance.",
  "error": null,
  "verdict": ""
}
```

### FP08 — `false_positive`

*Targeting:* very short genuine human submission

```json
{
  "id": "FP08",
  "status": 200,
  "content_id": "3c14077c-eb90-4385-a43d-65d0f07a7fec",
  "creator_id": "attacker_FP08",
  "guess": "unsure",
  "confidence": 0.482,
  "model_score": 0.3223,
  "style_score": 0.5223,
  "label": "We couldn't tell either way. This piece could have been written by a person or by AI \u2014 treat this result as inconclusive, not as an accusation.",
  "error": null,
  "verdict": ""
}
```

### PI01 — `prompt_injection`

*Targeting:* instruction to ignore the check

```json
{
  "id": "PI01",
  "status": 200,
  "content_id": "ab4bdd65-5e76-4a2d-a7b1-189346e660ab",
  "creator_id": "attacker_PI01",
  "guess": "unsure",
  "confidence": 0.7687,
  "model_score": 0.4625,
  "style_score": 0.468,
  "label": "We couldn't tell either way. This piece could have been written by a person or by AI \u2014 treat this result as inconclusive, not as an accusation.",
  "error": null,
  "verdict": ""
}
```

### PI02 — `prompt_injection`

*Targeting:* instruction disguised as a system message

```json
{
  "id": "PI02",
  "status": 200,
  "content_id": "17419cc4-1c58-47fe-8956-bf9fb9e7489b",
  "creator_id": "attacker_PI02",
  "guess": "human",
  "confidence": 0.08,
  "model_score": 0.2044,
  "style_score": 0.4395,
  "label": "We think this was probably written by a person.",
  "error": null,
  "verdict": ""
}
```

### PI03 — `prompt_injection`

*Targeting:* instruction wrapped in the writer's voice

```json
{
  "id": "PI03",
  "status": 200,
  "content_id": "61461004-f784-4acc-bce8-7bb0ac649519",
  "creator_id": "attacker_PI03",
  "guess": "unsure",
  "confidence": 0.612,
  "model_score": 0.5943,
  "style_score": 0.522,
  "label": "We couldn't tell either way. This piece could have been written by a person or by AI \u2014 treat this result as inconclusive, not as an accusation.",
  "error": null,
  "verdict": ""
}
```

### PI04 — `prompt_injection`

*Targeting:* attempt to make the label text hostile

```json
{
  "id": "PI04",
  "status": 200,
  "content_id": "892bb60d-af0a-4228-835f-8e9be24ccfc1",
  "creator_id": "attacker_PI04",
  "guess": "unsure",
  "confidence": 0.8787,
  "model_score": 0.4998,
  "style_score": 0.5366,
  "label": "We couldn't tell either way. This piece could have been written by a person or by AI \u2014 treat this result as inconclusive, not as an accusation.",
  "error": null,
  "verdict": ""
}
```

### PI05 — `prompt_injection`

*Targeting:* attempt to inject into the audit log

```json
{
  "id": "PI05",
  "status": 200,
  "content_id": "8e12ec7e-c5b7-458f-a5f6-9439bba8c767",
  "creator_id": "attacker_PI05",
  "guess": "human",
  "confidence": 0.1414,
  "model_score": 0.6401,
  "style_score": 0.1873,
  "label": "We think this was probably written by a person.",
  "error": null,
  "verdict": ""
}
```

### PI06 — `prompt_injection`

*Targeting:* instruction plus real human text

```json
{
  "id": "PI06",
  "status": 200,
  "content_id": "736bc501-d528-4837-815c-9a5e1c25dcbe",
  "creator_id": "attacker_PI06",
  "guess": "unsure",
  "confidence": 0.4207,
  "model_score": 0.5583,
  "style_score": 0.6155,
  "label": "We couldn't tell either way. This piece could have been written by a person or by AI \u2014 treat this result as inconclusive, not as an accusation.",
  "error": null,
  "verdict": ""
}
```

### MF01 — `malformed`

*Targeting:* text is only whitespace

```json
{
  "id": "MF01",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF01",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF02 — `malformed`

*Targeting:* text is a single character

```json
{
  "id": "MF02",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF02",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF03 — `malformed`

*Targeting:* text is control characters

```json
{
  "id": "MF03",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF03",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF04 — `malformed`

*Targeting:* text is only punctuation

```json
{
  "id": "MF04",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF04",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF05 — `malformed`

*Targeting:* text is a very long single word

```json
{
  "id": "MF05",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF05",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF06 — `malformed`

*Targeting:* text is emoji only

```json
{
  "id": "MF06",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF06",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF07 — `malformed`

*Targeting:* text is right-to-left script

```json
{
  "id": "MF07",
  "status": 200,
  "content_id": "2468b11c-09bc-4520-b8c9-3a503cffa28b",
  "creator_id": "attacker_MF07",
  "guess": "ai",
  "confidence": 0.8663,
  "model_score": 0.9064,
  "style_score": 1.0,
  "label": "We think this was probably written by AI, or with heavy AI assistance.",
  "error": null,
  "verdict": ""
}
```

### MF08 — `malformed`

*Targeting:* text is 60,000 characters

```json
{
  "id": "MF08",
  "status": 413,
  "content_id": null,
  "creator_id": "attacker_MF08",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ01 — `malformed`

*Targeting:* no text field at all

```json
{
  "id": "RQ01",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ01",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ02 — `malformed`

*Targeting:* no creator_id

```json
{
  "id": "RQ02",
  "status": 200,
  "content_id": "20f6f661-6560-4169-b511-949b5ef433d4",
  "creator_id": null,
  "guess": "human",
  "confidence": 0.0106,
  "model_score": 0.2395,
  "style_score": 0.6667,
  "label": "We think this was probably written by a person.",
  "error": null,
  "verdict": ""
}
```

### RQ03 — `malformed`

*Targeting:* text is a number

```json
{
  "id": "RQ03",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ03",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ04 — `malformed`

*Targeting:* text is a list

```json
{
  "id": "RQ04",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ04",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ05 — `malformed`

*Targeting:* text is null

```json
{
  "id": "RQ05",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ05",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ06 — `malformed`

*Targeting:* creator_id is an object

```json
{
  "id": "RQ06",
  "status": 400,
  "content_id": null,
  "creator_id": {
    "id": "x"
  },
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ07 — `malformed`

*Targeting:* body is a JSON array, not an object

```json
{
  "id": "RQ07",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ08 — `malformed`

*Targeting:* body is unparseable JSON

```json
{
  "id": "RQ08",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ09 — `malformed`

*Targeting:* body is empty

```json
{
  "id": "RQ09",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ10 — `malformed`

*Targeting:* body is form-encoded, not JSON

```json
{
  "id": "RQ10",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ11 — `malformed`

*Targeting:* body is JSON claiming to be plain text

```json
{
  "id": "RQ11",
  "status": 429,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ12 — `malformed`

*Targeting:* deeply nested JSON

```json
{
  "id": "RQ12",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ12",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_01 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_01",
  "status": 200,
  "content_id": "bfa31a69-db54-4718-a02d-db5713b1bf36",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.4623,
  "model_score": 0.0287,
  "style_score": 0.6667,
  "label": "We think this was probably written by a person.",
  "error": null,
  "verdict": ""
}
```

### FL01_02 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_02",
  "status": 200,
  "content_id": "c61a76cf-e67d-4ab3-b363-7ba91d2ec237",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.4623,
  "model_score": 0.0287,
  "style_score": 0.6667,
  "label": "We think this was probably written by a person.",
  "error": null,
  "verdict": ""
}
```

### FL01_03 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_03",
  "status": 200,
  "content_id": "f043ea31-c7c5-432b-98b3-8821fd7dff97",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.4623,
  "model_score": 0.0287,
  "style_score": 0.6667,
  "label": "We think this was probably written by a person.",
  "error": null,
  "verdict": ""
}
```

### FL01_04 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_04",
  "status": 200,
  "content_id": "701472fd-7b8f-4218-9614-29aa82d5d8af",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.4623,
  "model_score": 0.0287,
  "style_score": 0.6667,
  "label": "We think this was probably written by a person.",
  "error": null,
  "verdict": ""
}
```

### FL01_05 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_05",
  "status": 200,
  "content_id": "f1b436cf-6f0d-405b-bf87-8ccd30483cd0",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.4623,
  "model_score": 0.0287,
  "style_score": 0.6667,
  "label": "We think this was probably written by a person.",
  "error": null,
  "verdict": ""
}
```

### FL01_06 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_06",
  "status": 200,
  "content_id": "e9f074b7-5cc3-4956-b741-ad97e45240e8",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.4623,
  "model_score": 0.0287,
  "style_score": 0.6667,
  "label": "We think this was probably written by a person.",
  "error": null,
  "verdict": ""
}
```

### FL01_07 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_07",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_08 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_08",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_09 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_09",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_10 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_10",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_11 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_11",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_12 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_12",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```
