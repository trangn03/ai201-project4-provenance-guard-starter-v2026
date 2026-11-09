# Attack run — unit9_run2

- Produced by: `run_attacks.py::main`
- Service: `app.py::submit`
- 8 attacks · 2026-11-08 18:38
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
| FP01 | false_positive | plain, clear human writing with no flourishes | 200 | `4cbee666-e74b-4030-b057-ca5ce6d6bb68` | unsure | 0.237 |  |
| FP02 | false_positive | human writing in a formal register | 200 | `03c1976d-f066-4207-9161-f005bbbaa572` | ai | 0.174 |  |
| FP03 | false_positive | a non-native English speaker writing carefully | 200 | `8bac871b-5de6-4e73-ae1a-0afe81118fe5` | ai | 0.221 |  |
| FP04 | false_positive | a student essay written to a rubric | 200 | `c7dfd037-0e5b-4480-ad72-492e6345f7de` | ai | 0.202 |  |
| FP05 | false_positive | technical documentation written by a person | 200 | `11f22794-abdb-4099-98da-c54b937e715d` | ai | 0.304 |  |
| FP06 | false_positive | a person imitating a formal template | 200 | `89ba98f6-eb80-42c7-80ae-cd9aa36b40e5` | ai | 0.234 |  |
| FP07 | false_positive | human writing that repeats a phrase deliberately | 200 | `05b04d21-51f5-4899-abb8-795e98efa478` | ai | 0.265 |  |
| FP08 | false_positive | very short genuine human submission | 200 | `84f936aa-9997-447b-bf17-f77d1655b99e` | unsure | 0.482 |  |

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
  "content_id": "4cbee666-e74b-4030-b057-ca5ce6d6bb68",
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
  "content_id": "03c1976d-f066-4207-9161-f005bbbaa572",
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
  "content_id": "8bac871b-5de6-4e73-ae1a-0afe81118fe5",
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
  "content_id": "c7dfd037-0e5b-4480-ad72-492e6345f7de",
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
  "content_id": "11f22794-abdb-4099-98da-c54b937e715d",
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
  "content_id": "89ba98f6-eb80-42c7-80ae-cd9aa36b40e5",
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
  "content_id": "05b04d21-51f5-4899-abb8-795e98efa478",
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
  "content_id": "84f936aa-9997-447b-bf17-f77d1655b99e",
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
