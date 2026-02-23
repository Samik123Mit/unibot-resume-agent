"""
Resume state management.
The resume is loaded once at startup from resume_data.json into a global dict.
All tools read and write to this dict directly.
"""

import json
import os

# ─────────────────────────────────────────────
# To change the resume, edit resume_data.json
# ─────────────────────────────────────────────
_DATA_FILE = os.path.join(os.path.dirname(__file__), "resume_data.json")


def _load() -> dict:
    with open(_DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# Single in-memory resume store — all tools operate on this object
RESUME: dict = _load()


def save_to_file() -> None:
    """Persist in-memory state back to the JSON file (optional helper)."""
    with open(_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(RESUME, f, indent=2)
