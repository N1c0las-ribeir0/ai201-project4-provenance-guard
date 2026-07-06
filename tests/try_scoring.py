"""Test the combined confidence scoring on 4 deliberately chosen inputs.

Milestone 4: run clearly-AI, clearly-human, and two borderline cases through the
full pipeline (both signals + scoring) and confirm the combined score varies
meaningfully and reaches at least 3 label categories. Prints both signal scores
separately so a misbehaving signal is easy to spot.

    source .venv/bin/activate
    python tests/try_scoring.py   # needs GROQ_API_KEY
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from detection import labels, llm_signal, scoring, stylometry_signal  # noqa: E402

INPUTS = {
    "clearly_ai": (
        "Artificial intelligence represents a transformative paradigm shift in modern "
        "society. It is important to note that while the benefits of AI are numerous, it "
        "is equally essential to consider the ethical implications. Furthermore, "
        "stakeholders across various sectors must collaborate to ensure responsible "
        "deployment."
    ),
    "clearly_human": (
        "ok so i finally tried that new ramen place downtown and honestly? underwhelming. "
        "the broth was fine but they put WAY too much sodium in it and i was thirsty for "
        "like three hours after. my friend got the spicy version and said it was better. "
        "probably won't go back unless someone drags me there"
    ),
    "borderline_formal_human": (
        "The relationship between monetary policy and asset price inflation has been "
        "extensively studied in the literature. Central banks face a fundamental tension "
        "between their mandate for price stability and the unintended consequences of "
        "prolonged low interest rates on equity and real estate valuations."
    ),
    "borderline_edited_ai": (
        "I've been thinking a lot about remote work lately. There are genuine tradeoffs — "
        "flexibility and no commute on one side, isolation and blurred work-life "
        "boundaries on the other. Studies show productivity varies widely by individual "
        "and role type."
    ),
}


def main():
    print(f"{'input':<26}{'llm':>7}{'styl':>7}{'p_ai':>8}{'conf':>8}  {'agree':<6} attribution")
    print("-" * 78)
    seen_variants = set()
    for name, text in INPUTS.items():
        llm = llm_signal.analyze(text)
        sty = stylometry_signal.analyze(text)
        decision = scoring.combine(llm, sty)
        label = labels.build_label(decision)
        seen_variants.add(label["variant"])
        print(f"{name:<26}{llm['p_ai']:>7}{sty['p_ai']:>7}"
              f"{decision['p_ai']:>8}{decision['confidence']:>8}  "
              f"{str(decision['signals_agree']):<6} {decision['verdict']}")
    print("-" * 78)
    print(f"distinct label variants reached: {len(seen_variants)} -> {sorted(seen_variants)}")


if __name__ == "__main__":
    main()
