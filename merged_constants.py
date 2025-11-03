"""Clean, merged constants for the complaint bot project.

This module consolidates values from the older `constants.py` and `schema_constants.py` files.
It aims to be the single source of truth for enums, labels, conversation states, and
small validation patterns used across the codebase.

Keep the legacy files for reference; update imports gradually to use this module.
"""

from typing import Dict, List
import re

# ---------------------------------------------------------------------------
# General / UI constants
# ---------------------------------------------------------------------------
# Hostels (canonical list used by the bot to render the hostel selection keyboard)
HOSTELS: List[str] = ["John", "Joseph", "Paul", "Peter", "Daniel", "Esther", "Dorcas", "Lydia", "Mary", "Deborah"]

# Legacy human-friendly categories (kept for backward compatibility/reference).
# Prefer using CATEGORY_LABEL_TO_KEY and CATEGORY_KEY_TO_LABEL in the app logic.
LEGACY_COMPLAINT_CATEGORIES: List[str] = [
    "Plumbing Issue",
    "Electrical Fault",
    "Structural Damage",
    "HVAC/Fan Repair",
    "Cleaning/Sanitation",
    "Other",
]

# ---------------------------------------------------------------------------
# Category / severity / status enums and mappings
# - Storage keys (compact) are used in DB & API payloads
# - Display labels are used in UI (inline keyboards and messages)
# ---------------------------------------------------------------------------
# Display label -> storage key mappings (canonical)
CATEGORY_LABEL_TO_KEY: Dict[str, str] = {
    "Plumbing / Water": "plumbing",
    "Electrical / Lighting": "electrical",
    "Structural / Furniture": "structural",
    "Pest Control": "pest",
    "Common Area / Facility": "common_area",
    "Other / Not Listed": "other",
    # Legacy labels mapped to canonical storage keys
    "Plumbing Issue": "plumbing",
    "Electrical Fault": "electrical",
    "Structural Damage": "structural",
    "HVAC/Fan Repair": "other",
    "Cleaning/Sanitation": "common_area",
    "Other": "other",
}

# Reverse mapping (storage key -> display label) - canonical display labels
CATEGORY_KEY_TO_LABEL: Dict[str, str] = {
    key: label for label, key in CATEGORY_LABEL_TO_KEY.items() if label in (
        "Plumbing / Water",
        "Electrical / Lighting",
        "Structural / Furniture",
        "Pest Control",
        "Common Area / Facility",
        "Other / Not Listed",
    )
}

# Derived lists for quick iteration
CATEGORY_KEYS: List[str] = list(CATEGORY_KEY_TO_LABEL.keys())
CATEGORY_LABELS: List[str] = [CATEGORY_KEY_TO_LABEL[k] for k in CATEGORY_KEYS]

# Severity
SEVERITY_KEYS: List[str] = ["low", "medium", "high"]
SEVERITY_LABELS: List[str] = ["Low", "Medium", "High"]
SEVERITY_KEY_TO_LABEL: Dict[str, str] = dict(zip(SEVERITY_KEYS, SEVERITY_LABELS))

# Status
STATUS_KEYS: List[str] = ["reported", "in_progress", "on_hold", "resolved", "rejected"]
STATUS_LABELS: List[str] = ["Reported", "In Progress", "On Hold", "Resolved", "Rejected"]
STATUS_KEY_TO_LABEL: Dict[str, str] = dict(zip(STATUS_KEYS, STATUS_LABELS))

# Default values
DEFAULT_STATUS = "reported"

# ---------------------------------------------------------------------------
# Conversation handler states
# Keep the numeric values stable (used by ConversationHandler). Do not change them
# unless you update all references in the codebase.
# ---------------------------------------------------------------------------
SELECT_HOSTEL = 1
GET_ROOM_NUMBER = 2
SELECT_CATEGORY = 3
GET_DESCRIPTION = 4
SUBMIT_COMPLAINT = 5
CANCEL = 6
# Additional conversation states added to require explicit user input for all fields
GET_TELEGRAM_ID = 0
GET_WING = 7  # retained for backward-compatibility but not used in the active flow
SELECT_SEVERITY = 8

# Active conversation flow states (GET_WING is no longer used; wing is derived from room number)
ALL_STATES: List[int] = [GET_TELEGRAM_ID, SELECT_HOSTEL, GET_ROOM_NUMBER, SELECT_CATEGORY, GET_DESCRIPTION, SELECT_SEVERITY, SUBMIT_COMPLAINT]

# ---------------------------------------------------------------------------
# Validation patterns and small helpers
# ---------------------------------------------------------------------------
# Regex for a valid Telegram user id (digits only) - keep generous length
TELEGRAM_USER_ID_PATTERN = re.compile(r"^[0-9]{3,32}$")

# Room number pattern & example
# Enforce canonical room format: one uppercase letter A-H followed by three digits
# Example: A312
ROOM_NUMBER_PATTERN = re.compile(r"^[A-H][0-9]{3}$")
ROOM_NUMBER_EXAMPLE = "A312"

# JSON Schema for complaint payload validation (used in tests and server-side validation)
JSON_SCHEMA_COMPLAINT = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Complaint",
    "type": "object",
    "required": ["telegram_user_id", "hostel", "wing", "room_number", "category", "description", "severity"],
    "properties": {
        "telegram_user_id": {"type": "string", "pattern": TELEGRAM_USER_ID_PATTERN.pattern},
        "hostel": {"type": "string", "maxLength": 50},
        "wing": {"type": "string", "maxLength": 20},
        "room_number": {"type": "string", "maxLength": 10, "pattern": ROOM_NUMBER_PATTERN.pattern, "examples": [ROOM_NUMBER_EXAMPLE]},
        "category": {"type": "string", "enum": CATEGORY_KEYS},
        "description": {"type": "string", "minLength": 10, "maxLength": 500},
        "severity": {"type": "string", "enum": SEVERITY_KEYS},
        "status": {"type": "string", "enum": STATUS_KEYS},
        "photo_urls": {"type": "array", "items": {"type": "string", "format": "uri"}}
    }
}

# ---------------------------------------------------------------------------
# Public API of this module
# ---------------------------------------------------------------------------
__all__ = [
    # UI / lookup
    "HOSTELS",
    "CATEGORY_KEYS",
    "CATEGORY_LABELS",
    "CATEGORY_LABEL_TO_KEY",
    "CATEGORY_KEY_TO_LABEL",
    # legacy
    "LEGACY_COMPLAINT_CATEGORIES",
    # severity / status
    "SEVERITY_KEYS",
    "SEVERITY_LABELS",
    "SEVERITY_KEY_TO_LABEL",
    "STATUS_KEYS",
    "STATUS_LABELS",
    "STATUS_KEY_TO_LABEL",
    "DEFAULT_STATUS",
    # conversation states
    "SELECT_HOSTEL",
    "GET_ROOM_NUMBER",
    "SELECT_CATEGORY",
    "GET_DESCRIPTION",
    "GET_TELEGRAM_ID",
    "SELECT_SEVERITY",
    "SUBMIT_COMPLAINT",
    "CANCEL",
    "ALL_STATES",
    # validation
    "TELEGRAM_USER_ID_PATTERN",
    "ROOM_NUMBER_PATTERN",
    "ROOM_NUMBER_EXAMPLE",
    # schemas
    "JSON_SCHEMA_COMPLAINT",
]

