"""JSON-file persistence for submissions and appeals.

Two flat JSON documents keyed by id. A module-level lock guards read-modify-write
so concurrent requests (the app is multi-threaded under Flask's dev server) can't
clobber each other's writes.
"""
import json
import threading

import config

_lock = threading.Lock()


def _ensure_dir():
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)


def _read(path):
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _write(path, data):
    _ensure_dir()
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
    tmp.replace(path)  # atomic swap


# --- Submissions -------------------------------------------------------------
def save_submission(record):
    with _lock:
        data = _read(config.SUBMISSIONS_PATH)
        data[record["submission_id"]] = record
        _write(config.SUBMISSIONS_PATH, data)


def get_submission(submission_id):
    with _lock:
        return _read(config.SUBMISSIONS_PATH).get(submission_id)


def update_submission_status(submission_id, status):
    """Set a submission's status. Returns the updated record or None if absent."""
    with _lock:
        data = _read(config.SUBMISSIONS_PATH)
        record = data.get(submission_id)
        if record is None:
            return None
        record["status"] = status
        _write(config.SUBMISSIONS_PATH, data)
        return record


# --- Appeals -----------------------------------------------------------------
def save_appeal(record):
    with _lock:
        data = _read(config.APPEALS_PATH)
        data[record["appeal_id"]] = record
        _write(config.APPEALS_PATH, data)
