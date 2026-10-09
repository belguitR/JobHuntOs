"""Profile loading and validation.  The profile is deliberately plain local JSON."""

from __future__ import annotations

import json
from pathlib import Path

REQUIRED_LISTS = (
    "target_roles",
    "target_locations",
    "target_countries",
    "skills",
    "facts",
    "preferred_languages",
    "blocked_companies",
)


def load(path: Path) -> dict:
    if not path.exists():
        raise ValueError(f"Profile not found: {path}. Run 'jobhunt init' and edit profile.json.")
    try:
        profile = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"Profile is not valid JSON: {error.msg}") from error
    if not isinstance(profile, dict):
        raise ValueError("Profile must be a JSON object.")
    for key in REQUIRED_LISTS:
        if not isinstance(profile.get(key), list):
            raise ValueError(f"Profile field '{key}' must be a list.")
    if not profile.get("name"):
        raise ValueError("Profile field 'name' is required.")
    return profile


def normalized_terms(values: list[str]) -> set[str]:
    return {value.casefold().strip() for value in values if value.strip()}
