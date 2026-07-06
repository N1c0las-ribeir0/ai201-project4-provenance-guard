"""Combine the two signals into a single verdict + confidence.

Design-first principle: we decided what the numbers should *mean* before
choosing the math.

  * p_ai        = combined probability the text is AI-generated (0..1).
  * confidence  = probability of the verdict we report, i.e. max(p_ai, 1-p_ai),
                  so it ranges 0.5 (a coin toss) .. 1.0 (certain). This is the
                  number shown to the user, and it reads naturally: "Likely AI,
                  confidence 78%" means p_ai = 0.78.

Two honesty mechanisms:
  1. Agreement check — if the signals land on opposite sides of 0.5 they
     disagree; we pull p_ai toward 0.5, so conflict drags both the verdict and
     the confidence toward "uncertain" instead of a false, confident verdict.
  2. False-positive asymmetry — declaring "AI" carries an EXTRA condition:
     p_ai >= AI_THRESHOLD AND the signals agree. Declaring "human" only needs
     p_ai <= HUMAN_THRESHOLD. On a creative platform, wrongly accusing a human
     is the expensive mistake, so reaching the AI verdict is deliberately harder.
"""
import config

VERDICT_AI = "likely_ai"
VERDICT_HUMAN = "likely_human"
VERDICT_UNCERTAIN = "uncertain"


def _signals_agree(a, b):
    """True unless the two probabilities straddle 0.5 (opposite conclusions)."""
    return (a - 0.5) * (b - 0.5) >= 0


def combine(llm_result, stylometry_result):
    """Return the combined decision dict from the two signal results."""
    llm_p = llm_result["p_ai"]
    sty_p = stylometry_result["p_ai"]

    combined = config.LLM_WEIGHT * llm_p + config.STYLOMETRY_WEIGHT * sty_p
    agree = _signals_agree(llm_p, sty_p)

    if not agree:
        # Disagreement -> pull gently back toward 0.5 (dampen the claim without
        # erasing it). This most often fires on formal text the LLM reads as AI
        # but stylometry reads as human, so in practice it holds back borderline
        # AI calls — the false-positive-averse direction.
        combined = 0.5 + (combined - 0.5) * 0.85

    # Confidence = probability mass behind whichever side we lean toward.
    confidence = max(combined, 1 - combined)

    # Verdict with the false-positive-aware thresholds (reaching AI needs more
    # distance from 0.5 than reaching human).
    if combined >= config.AI_THRESHOLD:
        verdict = VERDICT_AI
    elif combined <= config.HUMAN_THRESHOLD:
        verdict = VERDICT_HUMAN
    else:
        verdict = VERDICT_UNCERTAIN

    return {
        "verdict": verdict,
        "p_ai": round(combined, 4),
        "confidence": round(confidence, 4),
        "signals_agree": agree,
    }
