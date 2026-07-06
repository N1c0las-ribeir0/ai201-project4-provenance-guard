"""Exercise detection signal 1 (Groq LLM classifier) in isolation.

Milestone 3 asks us to test the signal directly — call the function with a few
inputs and inspect the output — BEFORE trusting it inside the endpoint. Run:

    source .venv/bin/activate
    python tests/try_signal1.py

Requires GROQ_API_KEY in .env. Prints each sample's {p_ai, rationale, ok}.
"""
import sys
from pathlib import Path

# Allow running as a plain script (add repo root to the import path).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from detection import llm_signal  # noqa: E402

SAMPLES = {
    "clearly_ai": (
        "Artificial intelligence is a transformative technology that offers "
        "numerous benefits across various industries. It improves efficiency, "
        "enhances decision-making, and enables the automation of repetitive "
        "tasks. Organizations can leverage AI to optimize operations and deliver "
        "better outcomes for their stakeholders."
    ),
    "clearly_human": (
        "The old man sat and watched the tide come crawling up the flats, gray "
        "on gray, thinking of nothing much. A gull screamed. Then quiet again — "
        "that heavy, salt-smelling quiet he'd known since boyhood, when his "
        "father hauled nets here and cursed the weather, laughing all the while."
    ),
    "short_fragment": "It rained today.",
}


def main():
    for name, text in SAMPLES.items():
        result = llm_signal.analyze(text)
        print(f"\n=== {name} ===")
        print(f"  p_ai      : {result['p_ai']}")
        print(f"  ok        : {result['ok']}")
        print(f"  rationale : {result.get('rationale', '')}")


if __name__ == "__main__":
    main()
