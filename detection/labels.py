"""Transparency labels shown to a reader on the platform.

Three variants, keyed by verdict. The exact wording here is the canonical text
also reproduced verbatim in the README. Confidence is rendered as a whole
percentage so it is meaningful to a non-technical reader.
"""
from detection import scoring

# variant identifiers
VARIANT_AI = "high_confidence_ai"
VARIANT_HUMAN = "high_confidence_human"
VARIANT_UNCERTAIN = "uncertain"


def build_label(decision):
    """Map a scoring decision -> {'variant': str, 'text': str}."""
    pct = round(decision["confidence"] * 100)
    verdict = decision["verdict"]

    if verdict == scoring.VERDICT_AI:
        return {
            "variant": VARIANT_AI,
            "text": (
                "⚠️ Likely AI-generated. Our analysis strongly suggests this "
                f"text was produced by an AI system. Confidence: {pct}%. "
                "The creator can appeal this assessment."
            ),
        }
    if verdict == scoring.VERDICT_HUMAN:
        return {
            "variant": VARIANT_HUMAN,
            "text": (
                "✍️ Likely human-written. Our analysis found no strong signs "
                f"of AI generation. Confidence: {pct}%."
            ),
        }
    return {
        "variant": VARIANT_UNCERTAIN,
        "text": (
            "❓ Uncertain origin. Our analysis couldn't reliably determine "
            "whether this text is human- or AI-written, so we're not making a "
            "call. Treat attribution as unconfirmed."
        ),
    }
