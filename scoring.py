"""
Turning two numbers into one, and one number into something a person can read.
← YOU BUILD THIS IN MILESTONES 4 AND 5

Two functions live here, and both are stubs.

`combine_signals` is where your false-positive decision from Milestone 1
actually gets made. Everything above it — the labels, the appeal path — is
downstream of a number this function produced.

`score_to_label` is where you stop writing for a machine and start writing for
a person. A score of 0.62 means nothing to a writer.

⚠️ Your README's **Signals and Scoring** section has to name the file and
function holding your combining rule. The grader checks your code against what
you claim, so that line should read `scoring.py::combine_signals`.
"""

import config


def combine_signals(model_score: float, style_score: float) -> float:
    """
    Combine two 0–1 signals into one 0–1 score.

    Args:
        model_score: from `detector.model_signal` — how predictable the text is.
        style_score: from `stylometry.style_signal` — the shape of the text.

    Returns:
        A float from 0.0 (confidently human) to 1.0 (confidently AI).

    The rule: a weighted average (`config.WEIGHT_MODEL_SIGNAL` /
    `WEIGHT_STYLE_SIGNAL`) as the base case. But when the two signals disagree
    by more than `config.SIGNAL_DISAGREEMENT_THRESHOLD`, a flat average isn't
    trusted to cancel out to "unsure" — the result is pulled halfway toward
    whichever signal read more human.

    Why: a wrong accusation costs a writer more than a missed detection costs
    the site (see criteria.md). When two independent methods split sharply,
    that's a case to lean toward the writer in, not a case to average away.

    The case this handles: a text with ordinary vocabulary but genuinely
    varied, idiosyncratic sentence structure — model_score ~0.73 (moderate
    perplexity reads as somewhat AI-like), style_score ~0.23 (clearly human
    shape: uneven sentence lengths, a semicolon, an em dash). A flat average
    lands at ~0.48, barely inside "unsure." This rule pulls it to ~0.35 —
    at the edge of "human" — because the style signal is picking up concrete,
    checkable features the model signal can't see at all, and the cost of
    being wrong favors that read.
    """
    average = (
        config.WEIGHT_MODEL_SIGNAL * model_score
        + config.WEIGHT_STYLE_SIGNAL * style_score
    )

    disagreement = abs(model_score - style_score)
    if disagreement > config.SIGNAL_DISAGREEMENT_THRESHOLD:
        more_human_reading = min(model_score, style_score)
        average = (average + more_human_reading) / 2.0

    return round(min(max(average, 0.0), 1.0), 4)


def score_to_label(score: float) -> tuple[str, str]:
    """
    Turn a score into a guess and the text a reader actually sees.

    Returns:
        (guess, label_text) — where `guess` is a short machine-readable string
        like "ai" / "human" / "unsure", and `label_text` is the full sentence
        shown to a person.

    Confirmed reachable by submitting real text through the running service:
    a plainly-worded personal anecdote lands "human" (~0.29), a textbook
    generic paragraph lands "ai" (~0.78), and several genuinely human but less
    extreme texts land "unsure" (~0.37-0.60) — so the gap isn't in the
    thresholds, it's in how confidently a given piece of writing happens to
    read.
    """
    if score >= config.AI_THRESHOLD:
        return "ai", (
            "We think this was probably written by AI, or with heavy AI "
            "assistance."
        )
    if score <= config.HUMAN_THRESHOLD:
        return "human", "We think this was probably written by a person."
    return "unsure", (
        "We couldn't tell either way. This piece could have been written by "
        "a person or by AI — treat this result as inconclusive, not as an "
        "accusation."
    )


def label_ranges() -> list[tuple[str, str]]:
    """
    The score range each label covers. Your README needs these beside the
    label text — given to you so the numbers can't drift apart from config.py.
    """
    return [
        ("high-confidence human", f"0.00 – {config.HUMAN_THRESHOLD:.2f}"),
        ("unsure", f"{config.HUMAN_THRESHOLD:.2f} – {config.AI_THRESHOLD:.2f}"),
        ("high-confidence AI", f"{config.AI_THRESHOLD:.2f} – 1.00"),
    ]
