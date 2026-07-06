"""Central configuration for Provenance Guard.

All tunable knobs (model, thresholds, signal weights, rate limits, storage
paths) live here so the rest of the code reads declaratively and the README
can point to a single source of truth.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# --- Groq / LLM signal -------------------------------------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.3-70b-versatile"

# --- Storage paths -----------------------------------------------------------
DATA_DIR = Path(__file__).parent / "data"
SUBMISSIONS_PATH = DATA_DIR / "submissions.json"
APPEALS_PATH = DATA_DIR / "appeals.json"
AUDIT_LOG_PATH = DATA_DIR / "audit_log.jsonl"

# --- Scoring -----------------------------------------------------------------
# The LLM read is weighted higher than the structural heuristics because it
# captures meaning the stylometry is blind to; stylometry is the sanity check.
LLM_WEIGHT = 0.70
STYLOMETRY_WEIGHT = 0.30

# Within the stylometry signal, burstiness (sentence-length variability) is the
# most reliable human/AI discriminator; type-token ratio is the noisiest (it is
# length-dependent and, on short texts, formal AI prose can be MORE diverse than
# casual human writing). Weight the features accordingly.
STYLOMETRY_FEATURE_WEIGHTS = {
    "burstiness": 0.5,
    "punctuation": 0.3,
    "ttr": 0.2,
}

# Decision thresholds on the combined P(AI): >=0.65 -> AI, <=0.35 -> human, the
# band between -> uncertain. The false-positive aversion (never lightly accuse a
# human) is carried behaviourally, not by the raw numbers: the LLM prompt is told
# to lean human when torn, and the disagreement damping below almost always fires
# on the "LLM says AI / stylometry says human" pattern that formal-but-human prose
# produces, dragging borderline AI calls back toward "uncertain".
AI_THRESHOLD = 0.65        # p_ai >= this -> likely AI
HUMAN_THRESHOLD = 0.35     # p_ai <= this -> likely human
# Everything between (0.35, 0.65) is reported as "uncertain".

# --- Input limits ------------------------------------------------------------
MAX_CONTENT_CHARS = 20_000   # generous for a poem/story excerpt/blog post
MIN_CONTENT_CHARS = 1

# --- Rate limits (per client IP) ---------------------------------------------
SUBMIT_RATE_LIMITS = "10 per minute;100 per day"
APPEAL_RATE_LIMITS = "20 per hour"
