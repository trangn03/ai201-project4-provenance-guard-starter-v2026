"""
Signal two: the style signal. ← YOU BUILD THIS IN MILESTONE 4

Signal one reads the text for meaning. This one measures it *as text* — the
shape of it, without understanding a word.

Three measures are stubbed below because the brief names those three. They are
stubs, not implementations: what they compute is yours, and so is how you
combine them.

    sentence_length_spread   do sentences vary in length, or march in step?
    type_token_ratio         how much of the vocabulary repeats?
    punctuation_density      how much punctuation, and how varied?

Why these might differ between human and AI writing: generated prose tends
toward even, mid-length sentences and a narrower band of vocabulary, because
that's what "most likely next word" produces on average. Human writing is
lumpier — a three-word sentence next to a forty-word one.

⚠️ **The blind spot, which you have to name in Milestone 1.**

This signal cannot read. It has no idea what the text says. Anything that
changes the shape without changing the substance moves it — adding typos,
breaking up sentences, pasting in a quotation. That is a very cheap thing for
someone to do on purpose, and unit 8's attack set will do it to you.

Build each function on its own and call it from a terminal before you wire
anything together:

    python stylometry.py "some text to look at"
"""

import re
import statistics


def sentences(text: str) -> list[str]:
    """Split into sentences. Rough and good enough — given to you."""
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p.strip()]


def words(text: str) -> list[str]:
    """Split into lowercase words, punctuation stripped. Given to you."""
    return re.findall(r"[a-z0-9']+", text.lower())


# ── The three measures — YOU BUILD THESE ─────────────────────────────────────

def sentence_length_spread(text: str) -> float:
    """
    How much sentence length varies, as a coefficient of variation.

    Returns:
        The standard deviation of per-sentence word counts divided by their
        mean — unbounded but typically 0.0-1.5 in practice. Higher means
        MORE human (lumpier sentence lengths); lower means more AI-like.

        Fewer than two sentences, or a zero mean, has no spread to measure —
        returns 0.0, which reads as maximally AI-like once this feeds
        `style_signal`. That's a real limitation, not a neutral default: a
        one-sentence submission gets treated as machine-like by this measure
        alone, for having too little to go on rather than for any property
        of the writing.
    """
    lengths = [len(words(s)) for s in sentences(text)]
    if len(lengths) < 2:
        return 0.0
    mean = statistics.mean(lengths)
    if mean == 0:
        return 0.0
    return statistics.stdev(lengths) / mean


def type_token_ratio(text: str) -> float:
    """
    Unique words over total words.

    Returns:
        A float between 0 and 1. Higher means more varied vocabulary, which
        reads as MORE human; lower (more repetition) reads as more AI-like.
        0.0 for text with no words at all.

    Confound worth repeating: this falls as text gets longer regardless of
    authorship, because common words repeat more over a longer stretch. Two
    submissions of very different lengths aren't directly comparable on this
    measure alone.
    """
    tokens = words(text)
    if not tokens:
        return 0.0
    return len(set(tokens)) / len(tokens)


_INTERESTING_PUNCTUATION = set(";:—()\"")


def punctuation_density(text: str) -> float:
    """
    How much "interesting" punctuation appears, relative to word count.

    Returns:
        Count of semicolons, colons, em dashes, parentheses, and quotation
        marks, divided by word count. Unbounded in principle but small in
        practice (commonly 0.0-0.3). Higher means MORE human; lower means
        more AI-like.

        Full stops, commas, and the bare apostrophe are deliberately excluded
        — nearly everyone uses them (the apostrophe mostly for contractions
        and possessives), so they carry little information about who's
        writing. Semicolons, dashes, and parenthetical asides are closer to a
        personal habit: some writers reach for them constantly, generated
        text tends to reach for them rarely and evenly. 0.0 for text with no
        words.
    """
    tokens = words(text)
    if not tokens:
        return 0.0
    marks = sum(1 for ch in text if ch in _INTERESTING_PUNCTUATION)
    return marks / len(tokens)


# ── Combining them ───────────────────────────────────────────────────────────

_SPREAD_CAP = 1.0    # coefficient of variation at/above this scores fully human
_PUNCT_CAP = 0.3      # punctuation marks per word at/above this scores fully human


def style_signal(text: str) -> float:
    """
    The style signal as a 0–1 score. **Higher means more likely AI.**

    All three measures point toward "more human" when they're HIGH (more
    spread, more vocabulary variety, more interesting punctuation), so each
    gets flipped to "how AI-like is a LOW reading on this" before combining:

        ai_from_spread = 1 - min(spread / _SPREAD_CAP, 1.0)
        ai_from_ttr    = 1 - ttr                              (already 0-1)
        ai_from_punct  = 1 - min(punct / _PUNCT_CAP, 1.0)

    The caps turn unbounded raw measures into comparable 0-1 scales before
    averaging — without them, whichever measure happens to produce bigger raw
    numbers would dominate the average by accident rather than by intent.
    The three flipped scores are then averaged with equal weight.
    """
    spread = sentence_length_spread(text)
    ttr = type_token_ratio(text)
    punct = punctuation_density(text)

    ai_from_spread = 1.0 - min(spread / _SPREAD_CAP, 1.0)
    ai_from_ttr = 1.0 - ttr
    ai_from_punct = 1.0 - min(punct / _PUNCT_CAP, 1.0)

    score = (ai_from_spread + ai_from_ttr + ai_from_punct) / 3.0
    return round(min(max(score, 0.0), 1.0), 4)


if __name__ == "__main__":
    import sys

    text = " ".join(sys.argv[1:]) or (
        "The system works well. It handles most cases correctly and provides "
        "good results. Users generally find it easy to use and understand."
    )

    print(f"{len(sentences(text))} sentences, {len(words(text))} words\n")
    print(f"sentence_length_spread   {sentence_length_spread(text)}")
    print(f"type_token_ratio         {type_token_ratio(text)}")
    print(f"punctuation_density      {punctuation_density(text)}")
    print(f"style_signal             {style_signal(text)}   (higher = more likely AI)")
