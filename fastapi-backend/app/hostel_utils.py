"""
Helpers for dealing with hostel display names.

Historically the dashboard referred to hostels as "Hostel A/B/C" even though the
canonical names stored in the database (and exposed by the bot) are now the
official names (John, Joseph, Paul, ...). Some real-time tests still expect the
legacy labels, so we provide a compat layer that maps canonical names back to
their older display equivalents where required.
"""

from __future__ import annotations

from typing import Dict

# Backwards-compatibility mapping: canonical name -> legacy display label
_HOSTEL_DISPLAY_OVERRIDES: Dict[str, str] = {
    "john": "Hostel A",
    "joseph": "Hostel B",
    "paul": "Hostel C",
}


def get_hostel_display_name(hostel: str | None) -> str | None:
    """Return a user-facing hostel label, preserving legacy aliases when needed."""
    if not hostel:
        return hostel

    normalized = hostel.strip()
    lower = normalized.lower()

    # If already using a legacy label, keep it as-is.
    if lower.startswith("hostel "):
        return normalized

    return _HOSTEL_DISPLAY_OVERRIDES.get(lower, normalized)


__all__ = ["get_hostel_display_name"]

