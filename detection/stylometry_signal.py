"""Signal 2 — Stylometric heuristics (pure Python, no external libraries).

Measures *structural* properties of the text that tend to differ between human
and AI writing, independent of meaning:

  * Burstiness (sentence-length variance) — humans mix long and short sentences;
    AI prose is more uniform in rhythm.
  * Type-token ratio (vocabulary diversity) — how often the writer reuses words.
    AI text often leans on a slightly narrower, safer vocabulary.
  * Punctuation density — humans pepper in dashes, semicolons, parentheses and
    varied marks; AI tends toward plainer, comma-and-period prose.

Each feature is normalised to a 0..1 "AI-likeness" score and averaged into the
signal's p_ai.

Blind spot: short texts are noisy (few sentences -> unstable variance), and a
formulaic human or a deliberately varied AI can invert the pattern. This is why
it is only one of two signals and never decides alone.
"""
import re
import statistics

# Below this many sentences the structural stats are too noisy to trust, so we
# hedge the signal back toward 0.5 (see p_ai computation).
MIN_RELIABLE_SENTENCES = 4

_SENTENCE_SPLIT = re.compile(r"[.!?]+(?:\s+|$)")
_WORD = re.compile(r"[A-Za-z']+")
_PUNCT = re.compile(r"[,;:\-\—\(\)\"'…]")


def _split_sentences(text):
    parts = [s.strip() for s in _SENTENCE_SPLIT.split(text) if s.strip()]
    return parts


def _clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def analyze(text):
    """Return {'p_ai': float, 'features': {...}} for the given text."""
    words = _WORD.findall(text.lower())
    sentences = _split_sentences(text)
    n_words = len(words)
    n_sentences = len(sentences)

    # Degenerate input: no real words -> we genuinely can't tell.
    if n_words == 0 or n_sentences == 0:
        return {
            "p_ai": 0.5,
            "features": {
                "n_words": n_words,
                "n_sentences": n_sentences,
                "note": "insufficient text for structural analysis",
            },
        }

    # --- Feature 1: burstiness (sentence-length variability) ----------------
    sent_lengths = [len(_WORD.findall(s)) for s in sentences]
    sent_lengths = [n for n in sent_lengths if n > 0] or [n_words]
    mean_len = statistics.mean(sent_lengths)
    stdev_len = statistics.pstdev(sent_lengths) if len(sent_lengths) > 1 else 0.0
    # Coefficient of variation: stdev relative to mean. Humans ~0.5+, uniform
    # AI ~0.2 and below. Map low variability -> AI-like.
    cv = stdev_len / mean_len if mean_len else 0.0
    burstiness_ai = _clamp(1.0 - (cv / 0.6))  # cv>=0.6 -> very human; cv=0 -> AI

    # --- Feature 2: type-token ratio (vocabulary diversity) -----------------
    ttr = len(set(words)) / n_words
    # TTR falls naturally as texts get longer, so scale the expectation by length.
    # Short human texts sit high (>0.7); repetitive/AI-flavored text sits lower.
    ttr_ai = _clamp((0.72 - ttr) / 0.32)  # ttr>=0.72 -> human; ttr<=0.40 -> AI-like

    # --- Feature 3: punctuation density -------------------------------------
    punct_count = len(_PUNCT.findall(text))
    punct_density = punct_count / n_words  # marks per word
    # Rich, varied punctuation reads human; sparse reads AI-uniform.
    punct_ai = _clamp((0.12 - punct_density) / 0.12)  # >=0.12/word -> human

    raw_p_ai = statistics.mean([burstiness_ai, ttr_ai, punct_ai])

    # Reliability hedge: with too few sentences, blend the estimate back toward
    # 0.5 rather than pretending to certainty.
    if n_sentences < MIN_RELIABLE_SENTENCES:
        weight = n_sentences / MIN_RELIABLE_SENTENCES
        p_ai = weight * raw_p_ai + (1 - weight) * 0.5
    else:
        p_ai = raw_p_ai

    return {
        "p_ai": round(p_ai, 4),
        "features": {
            "n_words": n_words,
            "n_sentences": n_sentences,
            "mean_sentence_length": round(mean_len, 2),
            "sentence_length_cv": round(cv, 4),
            "type_token_ratio": round(ttr, 4),
            "punctuation_density": round(punct_density, 4),
            "burstiness_ai": round(burstiness_ai, 4),
            "ttr_ai": round(ttr_ai, 4),
            "punctuation_ai": round(punct_ai, 4),
        },
    }
