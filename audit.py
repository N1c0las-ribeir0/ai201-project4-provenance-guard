"""Append-only structured audit log (JSONL — one JSON object per line).

Every attribution decision and every appeal is recorded here. JSONL is chosen
so the log is genuinely append-only (a decision, once written, is never
rewritten) and trivially streamable / greppable.
"""
import json
import threading

import config

_lock = threading.Lock()


def _append(entry):
    with _lock:
        config.DATA_DIR.mkdir(parents=True, exist_ok=True)
        with config.AUDIT_LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def log_decision(submission_id, timestamp, decision, llm_result,
                 stylometry_result, creator_id):
    """Record an attribution decision."""
    _append({
        "event": "decision",
        "submission_id": submission_id,
        "timestamp": timestamp,
        "creator_id": creator_id,
        "verdict": decision["verdict"],
        "confidence": decision["confidence"],
        "p_ai": decision["p_ai"],
        "signals": {
            "llm": {"p_ai": llm_result["p_ai"], "rationale": llm_result.get("rationale", "")},
            "stylometry": {"p_ai": stylometry_result["p_ai"],
                           "features": stylometry_result["features"]},
        },
    })


def log_appeal(appeal_id, submission_id, timestamp, reason, original_decision):
    """Record an appeal alongside a snapshot of the original decision."""
    _append({
        "event": "appeal",
        "appeal_id": appeal_id,
        "submission_id": submission_id,
        "timestamp": timestamp,
        "reason": reason,
        "original_decision": {
            "verdict": original_decision.get("verdict"),
            "confidence": original_decision.get("confidence"),
            "p_ai": original_decision.get("p_ai"),
        },
    })


def read_all():
    """Return every audit entry as a list of dicts, oldest first."""
    if not config.AUDIT_LOG_PATH.exists():
        return []
    entries = []
    with config.AUDIT_LOG_PATH.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries
