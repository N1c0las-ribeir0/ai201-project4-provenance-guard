"""Combine the two signals into a single verdict + confidence.

Design-first principle: we decided what the numbers should *mean* before
choosing the math.

  * p_ai        = combined probability the text is AI-generated (0..1).
  * confidence  = how sure we are of the verdict (0..1). 0.5-ish p_ai -> ~0
                  confidence; the extremes -> ~1. This is what the user sees.

Two honesty mechanisms:
  1. Agreement check — if the signals land on opposite sides of 0.5 they
     disagree; we pull p_ai toward the fence and cap confidence, so conflict
     surfaces as doubt instead of a false verdict.
  2. False-positive asymmetry — declaring "AI" needs a high bar (>=0.80 AND
     agreement); declaring "human" is easier (<=0.25). Everything else is
     reported as "uncertain". On a creative platform, wrongly accusing a human
     is the expensive mistake, so the AI zone is deliberately narrow.
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
        # Disagreement -> pull halfway back toward 0.5 (dampen the claim).
        combined = 0.5 + (combined - 0.5) * 0.5

    confidence = abs(combined - 0.5) * 2
    if not agree:
        confidence = min(confidence, config.DISAGREEMENT_CONFIDENCE_CAP)

    # Verdict with the false-positive-aware thresholds.
    if combined >= config.AI_THRESHOLD and agree:
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
