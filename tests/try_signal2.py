"""Exercise detection signal 2 (stylometric heuristics) in isolation.

Milestone 4 asks us to test the second signal independently — on the same inputs
used for signal 1 — before integration, so we can see where the two signals agree
and disagree. Pure Python, no API key needed. Run:

    python tests/try_signal2.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from detection import stylometry_signal  # noqa: E402
from try_signal1 import SAMPLES  # noqa: E402  (same inputs as signal 1)


def main():
    for name, text in SAMPLES.items():
        result = stylometry_signal.analyze(text)
        f = result["features"]
        print(f"\n=== {name} ===")
        print(f"  p_ai                 : {result['p_ai']}")
        print(f"  sentence_length_cv   : {f.get('sentence_length_cv')}")
        print(f"  type_token_ratio     : {f.get('type_token_ratio')}")
        print(f"  punctuation_density  : {f.get('punctuation_density')}")


if __name__ == "__main__":
    main()
