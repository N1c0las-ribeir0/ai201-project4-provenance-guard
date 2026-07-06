"""Provenance Guard — Flask API.

Endpoints:
  POST /submit  — classify a piece of text, return verdict + confidence + label
  POST /appeal  — contest a classification; flips status to "under review"
  GET  /log     — the structured audit log
  GET  /health  — liveness check
"""
import uuid
from datetime import datetime, timezone

from flask import Flask, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

import audit
import config
import store
from detection import labels, llm_signal, scoring, stylometry_signal

app = Flask(__name__)

limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=[],  # only the endpoints we explicitly decorate are limited
)


def _now():
    return datetime.now(timezone.utc).isoformat()


def _error(message, status):
    return jsonify({"error": message}), status


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/submit")
@limiter.limit(config.SUBMIT_RATE_LIMITS)
def submit():
    body = request.get_json(silent=True) or {}
    content = body.get("content")
    creator_id = body.get("creator_id")

    if not isinstance(content, str) or not content.strip():
        return _error("Field 'content' is required and must be non-empty text.", 400)
    if len(content) > config.MAX_CONTENT_CHARS:
        return _error(
            f"Content exceeds the {config.MAX_CONTENT_CHARS}-character limit.", 400
        )

    # --- run the two signals ------------------------------------------------
    llm_result = llm_signal.analyze(content)
    sty_result = stylometry_signal.analyze(content)

    # --- combine + label ----------------------------------------------------
    decision = scoring.combine(llm_result, sty_result)
    label = labels.build_label(decision)

    submission_id = f"sub_{uuid.uuid4().hex[:12]}"
    timestamp = _now()

    record = {
        "submission_id": submission_id,
        "timestamp": timestamp,
        "creator_id": creator_id,
        "content": content,
        "verdict": decision["verdict"],
        "confidence": decision["confidence"],
        "p_ai": decision["p_ai"],
        "label": label,
        "signals": {"llm": llm_result, "stylometry": sty_result},
        "status": "classified",
    }
    store.save_submission(record)
    audit.log_decision(submission_id, timestamp, decision, llm_result,
                       sty_result, creator_id)

    return jsonify({
        "submission_id": submission_id,
        "verdict": decision["verdict"],
        "confidence": decision["confidence"],
        "p_ai": decision["p_ai"],
        "label": label,
        "signals": {
            "llm": {"p_ai": llm_result["p_ai"],
                    "rationale": llm_result.get("rationale", "")},
            "stylometry": {"p_ai": sty_result["p_ai"],
                           "features": sty_result["features"]},
        },
        "status": record["status"],
    })


@app.post("/appeal")
@limiter.limit(config.APPEAL_RATE_LIMITS)
def appeal():
    body = request.get_json(silent=True) or {}
    submission_id = body.get("submission_id")
    reason = body.get("reason")

    if not isinstance(submission_id, str) or not submission_id:
        return _error("Field 'submission_id' is required.", 400)
    if not isinstance(reason, str) or not reason.strip():
        return _error("Field 'reason' is required and must be non-empty.", 400)

    original = store.get_submission(submission_id)
    if original is None:
        return _error("No submission found with that id.", 404)

    updated = store.update_submission_status(submission_id, "under review")

    appeal_id = f"apl_{uuid.uuid4().hex[:12]}"
    timestamp = _now()
    store.save_appeal({
        "appeal_id": appeal_id,
        "submission_id": submission_id,
        "timestamp": timestamp,
        "reason": reason,
        "original_verdict": original.get("verdict"),
        "original_confidence": original.get("confidence"),
    })
    audit.log_appeal(appeal_id, submission_id, timestamp, reason, original)

    return jsonify({
        "appeal_id": appeal_id,
        "submission_id": submission_id,
        "status": updated["status"],
        "message": "Your appeal has been logged. This content is now under review.",
    })


@app.get("/log")
def get_log():
    return jsonify(audit.read_all())


@app.errorhandler(429)
def ratelimit_handler(err):
    return jsonify({
        "error": "Rate limit exceeded. Please slow down and try again later.",
        "detail": str(err.description),
    }), 429


if __name__ == "__main__":
    app.run(debug=True, port=5000)
