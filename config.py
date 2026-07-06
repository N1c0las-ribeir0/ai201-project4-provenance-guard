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
LLM_WEIGHT = 0.65
STYLOMETRY_WEIGHT = 0.35

# Decision thresholds on the combined P(AI). Declaring AI needs a much higher
# bar than declaring human: a false positive (accusing a human) is the costly
# error on a creative platform, so the "AI" zone is deliberately narrow.
AI_THRESHOLD = 0.80        # p_ai >= this AND signals agree -> high-confidence AI
HUMAN_THRESHOLD = 0.25     # p_ai <= this -> high-confidence human
# Everything between is reported as "uncertain".

# When the two signals land on opposite sides of 0.5 they disagree; we pull the
# combined score toward the fence and cap confidence so conflict reads as doubt.
DISAGREEMENT_CONFIDENCE_CAP = 0.4

# --- Input limits ------------------------------------------------------------
MAX_CONTENT_CHARS = 20_000   # generous for a poem/story excerpt/blog post
MIN_CONTENT_CHARS = 1

# --- Rate limits (per client IP) ---------------------------------------------
SUBMIT_RATE_LIMITS = "10 per minute;100 per day"
APPEAL_RATE_LIMITS = "20 per hour"
