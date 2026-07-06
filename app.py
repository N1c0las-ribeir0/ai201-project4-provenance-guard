"""Provenance Guard — Flask API.

Endpoints:
  POST /submit  — classify a piece of text, return attribution + confidence + label
  POST /appeal  — contest a classification; flips status to "under review"
  GET  /log     — the structured audit log ({"entries": [...]}, newest first)
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
    storage_uri="memory://",  # in-memory store is fine for local dev
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
    text = body.get("text")
    creator_id = body.get("creator_id")

    if not isinstance(text, str) or not text.strip():
        return _error("Field 'text' is required and must be non-empty text.", 400)
    if len(text) > config.MAX_CONTENT_CHARS:
        return _error(
            f"Text exceeds the {config.MAX_CONTENT_CHARS}-character limit.", 400
        )

    # --- run the two signals ------------------------------------------------
    llm_result = llm_signal.analyze(text)
    sty_result = stylometry_signal.analyze(text)

    # --- combine + label ----------------------------------------------------
    decision = scoring.combine(llm_result, sty_result)
    label = labels.build_label(decision)

    content_id = f"sub_{uuid.uuid4().hex[:12]}"
    timestamp = _now()

    record = {
        "content_id": content_id,
        "timestamp": timestamp,
        "creator_id": creator_id,
        "text": text,
        "attribution": decision["verdict"],
        "confidence": decision["confidence"],
        "p_ai": decision["p_ai"],
        "label": label,
        "signals": {"llm": llm_result, "stylometry": sty_result},
        "status": "classified",
    }
    store.save_submission(record)
    audit.log_decision(content_id, timestamp, decision, llm_result,
                       sty_result, creator_id)

    return jsonify({
        "content_id": content_id,
        "attribution": decision["verdict"],
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
    content_id = body.get("content_id")
    creator_reasoning = body.get("creator_reasoning")

    if not isinstance(content_id, str) or not content_id:
        return _error("Field 'content_id' is required.", 400)
    if not isinstance(creator_reasoning, str) or not creator_reasoning.strip():
        return _error("Field 'creator_reasoning' is required and must be non-empty.", 400)

    original = store.get_submission(content_id)
    if original is None:
        return _error("No submission found with that content_id.", 404)

    updated = store.update_submission_status(content_id, "under_review")

    appeal_id = f"apl_{uuid.uuid4().hex[:12]}"
    timestamp = _now()
    store.save_appeal({
        "appeal_id": appeal_id,
        "content_id": content_id,
        "timestamp": timestamp,
        "creator_reasoning": creator_reasoning,
        "original_attribution": original.get("attribution"),
        "original_confidence": original.get("confidence"),
    })
    audit.log_appeal(appeal_id, content_id, timestamp, creator_reasoning, original)

    return jsonify({
        "appeal_id": appeal_id,
        "content_id": content_id,
        "status": updated["status"],
        "message": "Your appeal has been logged. This content is now under review.",
    })


@app.get("/log")
def get_log():
    # Newest first so the most recent decisions/appeals surface at the top.
    return jsonify({"entries": list(reversed(audit.read_all()))})


@app.errorhandler(429)
def ratelimit_handler(err):
    return jsonify({
        "error": "Rate limit exceeded. Please slow down and try again later.",
        "detail": str(err.description),
    }), 429


if __name__ == "__main__":
    app.run(debug=True, port=5000)
