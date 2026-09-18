"""General helper functions used across the project."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

from src.utils.constants import DIFFICULTY_ORDER


def load_json_file(file_path: Path) -> dict[str, Any]:
    """Load a JSON file into a Python dictionary."""
    with Path(file_path).open("r", encoding="utf-8") as json_file:
        return json.load(json_file)


def serialize_string_list(values: Iterable[str]) -> str:
    """Serialize a list of strings for SQLite storage."""
    cleaned_values = [str(value).strip().lower() for value in values if str(value).strip()]
    return json.dumps(cleaned_values)


def deserialize_string_list(
    raw_value: str | None,
    default: Iterable[str] | None = None,
) -> list[str]:
    """Deserialize JSON or comma-separated strings into a normalized list."""
    if not raw_value:
        return [str(item).strip().lower() for item in (default or []) if str(item).strip()]

    try:
        parsed_value = json.loads(raw_value)
        if isinstance(parsed_value, list):
            return [str(item).strip().lower() for item in parsed_value if str(item).strip()]
    except json.JSONDecodeError:
        pass

    return [item.strip().lower() for item in raw_value.split(",") if item.strip()] or [
        str(item).strip().lower() for item in (default or []) if str(item).strip()
    ]


def serialize_json(value: Any) -> str:
    """Serialize a JSON-compatible value for SQLite storage."""
    return json.dumps(value, ensure_ascii=True)


def deserialize_json_object(
    raw_value: str | None,
    default: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Deserialize a JSON object string into a dictionary."""
    if not raw_value:
        return dict(default or {})

    try:
        parsed_value = json.loads(raw_value)
    except json.JSONDecodeError:
        return dict(default or {})

    return parsed_value if isinstance(parsed_value, dict) else dict(default or {})


def utc_now_iso() -> str:
    """Return the current UTC time in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def shift_utc_iso(
    base_value: str | None = None,
    *,
    days: int = 0,
    hours: int = 0,
) -> str:
    """Return an ISO timestamp shifted from the provided UTC time."""
    if base_value:
        base_datetime = datetime.fromisoformat(base_value)
        if base_datetime.tzinfo is None:
            base_datetime = base_datetime.replace(tzinfo=timezone.utc)
    else:
        base_datetime = datetime.now(timezone.utc)

    return (base_datetime + timedelta(days=days, hours=hours)).isoformat()


def build_difficulty_range(
    minimum_difficulty: str,
    maximum_difficulty: str,
) -> list[str]:
    """Return the ordered difficulty values between the provided endpoints."""
    normalized_minimum = minimum_difficulty.strip().lower()
    normalized_maximum = maximum_difficulty.strip().lower()
    order = list(DIFFICULTY_ORDER)

    if normalized_minimum not in order or normalized_maximum not in order:
        return order

    start_index = order.index(normalized_minimum)
    end_index = order.index(normalized_maximum)
    if start_index > end_index:
        start_index, end_index = end_index, start_index

    return order[start_index : end_index + 1]
