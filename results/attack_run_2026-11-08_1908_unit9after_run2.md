# Attack run — unit9after_run2

- Produced by: `run_attacks.py::main`
- Service: `app.py::submit`
- 8 attacks · 2026-11-08 19:08
- Auto-marked BROKE (5xx, crash, no response): **0**
- Left for you to judge: **8**

The Verdict column is blank where a script can't honestly decide. Whether
an evasion worked depends on where you put your thresholds — read the
`targets` column, look at what came back, and write HELD or BROKE yourself.

Each attack submits as creator_id `attacker_<id>`, and the content_id it
came back with is in the table — either one will match this run against your
audit log when you go looking for the ten entries to paste.

| ID | Family | Targeting | Status | Content ID | Guess | Score | Verdict |
|---|---|---|---|---|---|---|---|
| FP01 | false_positive | plain, clear human writing with no flourishes | 200 | `c4766136-e7d5-4ab5-b58d-a0c11757f531` | unsure | 0.237 |  |
| FP02 | false_positive | human writing in a formal register | 200 | `5a376923-6ca6-4a14-93b4-9324a39f721a` | ai | 0.174 |  |
| FP03 | false_positive | a non-native English speaker writing carefully | 200 | `804386c0-d470-40e6-a67e-7940b45a495c` | ai | 0.221 |  |
| FP04 | false_positive | a student essay written to a rubric | 200 | `a1fe2ec2-f36a-46ad-9f3c-295c07107cb5` | ai | 0.202 |  |
| FP05 | false_positive | technical documentation written by a person | 200 | `1326c155-bbf0-4731-bbfd-ede2f1ad1d10` | ai | 0.304 |  |
| FP06 | false_positive | a person imitating a formal template | 200 | `1428bf63-cdab-426d-ada8-92d102fdd2e4` | ai | 0.234 |  |
| FP07 | false_positive | human writing that repeats a phrase deliberately | 200 | `e549482b-2dcf-4494-9f85-1be1f0255416` | ai | 0.265 |  |
| FP08 | false_positive | very short genuine human submission | 200 | `ce578b2f-e2f0-42af-8c4e-f4a3c0fb2cdc` | unsure | 0.482 |  |

---

## By family

| Family | Attacks | Auto-BROKE | Left to judge |
|---|---|---|---|
| `false_positive` | 8 | 0 | 8 |

> The **false_positive** family is the one to look at hardest. Those are
> written to be genuine human writing that reads as machine-like. Every one
> your service calls AI is a real writer it would have accused.

---

## What came back

The detail behind the table. Paste the interesting failures into your
README — the ones that show something, not the ten easiest.

### FP01 — `false_positive`

*Targeting:* plain, clear human writing with no flourishes

```json
{
  "id": "FP01",
  "status": 200,
  "content_id": "c4766136-e7d5-4ab5-b58d-a0c11757f531",
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
  "content_id": "5a376923-6ca6-4a14-93b4-9324a39f721a",
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
  "content_id": "804386c0-d470-40e6-a67e-7940b45a495c",
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
  "content_id": "a1fe2ec2-f36a-46ad-9f3c-295c07107cb5",
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
  "content_id": "1326c155-bbf0-4731-bbfd-ede2f1ad1d10",
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
  "content_id": "1428bf63-cdab-426d-ada8-92d102fdd2e4",
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
  "content_id": "e549482b-2dcf-4494-9f85-1be1f0255416",
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
  "content_id": "ce578b2f-e2f0-42af-8c4e-f4a3c0fb2cdc",
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
