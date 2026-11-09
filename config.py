"""
Settings for Provenance Guard.

Everything you're likely to change lives here, at the top, on purpose.

You'll edit the thresholds in Milestone 5 and the rate limits in unit 8.
"""

import os
from pathlib import Path

ROOT = Path(__file__).parent


# ─── The service ─────────────────────────────────────────────────────────────

# `127.0.0.1` is loopback — only your own machine can reach it, which is what
# you want all through units 7 and 8. A host somewhere else has to accept
# traffic from outside the box, and that means `0.0.0.0`. Setting the env var
# is how you get it; the default keeps your local `curl` commands unchanged.
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "5000"))

# Flask's debug mode gives anyone who can reach the service an interactive
# Python prompt inside your process. Fine on loopback, a gift to strangers
# anywhere else — so it turns itself off the moment HOST isn't loopback.
DEBUG = os.getenv("AI201_DEBUG", "1") == "1" and HOST in ("127.0.0.1", "localhost")


# ─── The local model ─────────────────────────────────────────────────────────
# Your first signal runs a language model ON YOUR OWN MACHINE. No account, no
# key, no card. It downloads about 550 MB the first time — do that before
# class, not during it.
#
# What it measures: how *predictable* your text is to a language model. Text a
# model finds easy to predict tends to be text a model wrote.
#
# The first call is the slow one — ten to twenty seconds while the model loads,
# longer on an older laptop. After that it stays in memory and a submission
# takes a second or two. That cost is part of what you're learning: this is
# what running a model inline in a request actually looks like.

DETECTOR_MODEL = os.getenv("AI201_DETECTOR_MODEL", "gpt2")

# Longer text gives a steadier reading but takes longer. 400 tokens is roughly
# 300 words, which is enough for the signal to mean something.
DETECTOR_MAX_TOKENS = 400

# ─── Input validation (Unit 8 improvement) ───────────────────────────────────
#
# What `/submit` refuses before either signal sees the text. Each of these was
# a before-run failure: an oversized body scored as ordinary text (criterion 5),
# and emoji-only, punctuation-only, control-character and one-word inputs got a
# confident verdict on text with nothing to read.
#
# 20,000 characters is about 3,500 words — over ten times what the detector
# reads (400 tokens is roughly 1,600 characters), so rejecting longer text
# loses no signal, only the cost of scanning it.
MAX_TEXT_CHARS = 20_000

# Words that contain at least one letter, in any script. Five is deliberately
# low: "Went for a run. Legs hurt. Worth it." (8 words) is a real submission.
# Letters are checked with str.isalpha, not [a-z], so Arabic, Hebrew and
# other non-Latin writing counts as writing.
MIN_WORDS = 5


# ─── Scoring (Milestone 4) ───────────────────────────────────────────────────
# How much each signal counts toward the combined score.
#
# ⚠️ These are placeholders. Milestone 4 asks you to write your combining rule
# down BEFORE you code it, and to put the numbers in your README. Whatever you
# decide, it goes here.

WEIGHT_MODEL_SIGNAL = 0.5
WEIGHT_STYLE_SIGNAL = 0.5

# When the two signals disagree by more than this, `combine_signals` stops
# trusting a flat average and leans toward whichever signal read more human
# — see scoring.py::combine_signals for why.
SIGNAL_DISAGREEMENT_THRESHOLD = 0.35


# ─── Thresholds (Milestone 5) ────────────────────────────────────────────────
# Where one label becomes another. Scores run 0.0 (confidently human) to 1.0
# (confidently AI).
#
#   score < HUMAN_THRESHOLD          -> high-confidence human
#   between the two                  -> unsure
#   score > AI_THRESHOLD             -> high-confidence AI
#
# ⚠️ This is where your false-positive decision from Milestone 1 actually gets
# made. Widening the unsure band means fewer wrong accusations and more AI text
# getting through. There is no setting that avoids the trade — only settings
# that decide who pays for it.

HUMAN_THRESHOLD = 0.35
AI_THRESHOLD = 0.65

# ⚠️ One thing that catches people out in Milestone 5. A weighted average can
# only land between its two inputs — so while `style_signal` is still the stub
# returning 0.5, the combined score can never leave 0.25–0.75 no matter what
# the model signal says, and the human label needs a model score below 0.20 to
# be reachable at all.
#
# If a label you can't reach is the problem, the fix is upstream of the
# thresholds: a style signal that actually varies. `scoring.label_ranges()`
# prints the bands; the reachable range is a different question.


# ─── Degraded mode (Shape B: harden against failure) ─────────────────────────
# When signal one (the local model) cannot run, /submit still answers from the
# style signal alone instead of returning a 500. One signal is weaker evidence,
# so the answer carries less confidence: the normal confidence is multiplied by
# this factor. The label side of the same decision lives in
# scoring.py::label_without_model, which never returns the "ai" label.
DEGRADED_CONFIDENCE_FACTOR = 0.5


# ─── Rate limiting (UNIT 8) ──────────────────────────────────────────────────
# Off in unit 7. You turn it on and choose the numbers in unit 8, Milestone 1.
#
# Think about two people: a real writer submitting their own work a few times
# an hour, and a script sending a thousand variations to map your thresholds.
# Your README has to say why your numbers and not others.

RATE_LIMITING_ENABLED = True

RATE_LIMIT_PER_MINUTE = 6
RATE_LIMIT_PER_DAY = 100

# Flask-Limiter warns loudly without this. In-memory is right for one laptop
# and wrong for anything real — a restart forgets every count, and two copies
# of the service wouldn't share limits.
RATE_LIMIT_STORAGE = "memory://"


# ─── Run log (structured logging) ────────────────────────────────────────────
# One JSON line per /submit request, including ones that were rejected, rate
# limited or crashed. See runlog.py for the fields. It sits in LOG_DIR beside
# the audit log, and unlike the audit log it keeps part of the submitted text,
# so this is the setting to turn down if the text should not be stored: how many
# characters of each input to keep. 0 keeps the length and word count only.
RUN_LOG_NAME = "runs.jsonl"
RUN_LOG_INPUT_CHARS = 500


# ─── Paths ───────────────────────────────────────────────────────────────────

LOG_DIR = ROOT / "logs"
AUDIT_LOG = LOG_DIR / "audit.jsonl"
RESULTS_DIR = ROOT / "results"
