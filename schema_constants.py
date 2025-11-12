"""Schema constants and mappings for the complaints bot and backend.

This file is intended for Phase 1 usage by the bot (inline keyboard labels, validation)
and for Phase 2 server-side validation where appropriate.
"""

from typing import Dict, List

# Display label -> storage key mappings (categories)
CATEGORY_LABEL_TO_KEY: Dict[str, str] = {
    "Plumbing / Water": "plumbing",
    "Electrical / Lighting": "electrical",
    "Carpentry": "structural",
    "Pest Control": "pest",
    "Metalworks/Bunks": "common_area",
    "Other / Not Listed": "other",
}

# Reverse mapping for display
CATEGORY_KEY_TO_LABEL: Dict[str, str] = {v: k for k, v in CATEGORY_LABEL_TO_KEY.items()}

SEVERITY_KEYS: List[str] = ["low", "medium", "high"]
SEVERITY_LABELS: List[str] = ["Low", "Medium", "High"]

STATUS_KEYS: List[str] = ["reported", "in_progress", "on_hold", "resolved", "rejected"]
STATUS_LABELS: List[str] = ["Reported", "In Progress", "On Hold", "Resolved", "Rejected"]

# JSON Schema (string) for validation or tests
JSON_SCHEMA_COMPLAINT = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Complaint",
    "type": "object",
    "required": ["telegram_user_id", "hostel", "wing", "room_number", "category", "description", "severity"],
    "properties": {
        "telegram_user_id": {"type": "string", "pattern": "^[0-9]{3,32}$"},
        "hostel": {"type": "string", "maxLength": 50},
        "wing": {"type": "string", "maxLength": 20},
        "room_number": {"type": "string", "maxLength": 10, "pattern": "^[A-Za-z0-9\\-\\s]{1,10}$", "examples": ["A312"]},
        "category": {"type": "string", "enum": list(CATEGORY_KEY_TO_LABEL.keys())},
        "description": {"type": "string", "minLength": 10, "maxLength": 500},
        "severity": {"type": "string", "enum": SEVERITY_KEYS},
        "status": {"type": "string", "enum": STATUS_KEYS},
        "photo_urls": {"type": "array", "items": {"type": "string", "format": "uri"}}
    }
}

__all__ = [
    "CATEGORY_LABEL_TO_KEY",
    "CATEGORY_KEY_TO_LABEL",
    "SEVERITY_KEYS",
    "SEVERITY_LABELS",
    "STATUS_KEYS",
    "STATUS_LABELS",
    "JSON_SCHEMA_COMPLAINT",
]
