"""Short-lived local auth handoff for the desktop CustomTkinter launcher."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from src.utils.config import DATA_DIR

DEFAULT_HANDOFF_PATH = DATA_DIR / ".desktop_login_handoff.json"
HANDOFF_TTL_SECONDS = 120


def write_desktop_login_handoff(
    user_id: int,
    remember_me: bool = False,
    path: Path | None = None,
) -> None:
    """Write a short-lived local handoff consumed by the Streamlit app."""
    handoff_path = Path(path or DEFAULT_HANDOFF_PATH)
    handoff_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "user_id": int(user_id),
        "remember_me": bool(remember_me),
        "created_at": time.time(),
    }
    handoff_path.write_text(json.dumps(payload), encoding="utf-8")


def consume_desktop_login_handoff(path: Path | None = None) -> int | None:
    """Return a handed-off user id once, or None when no valid handoff exists."""
    handoff_path = Path(path or DEFAULT_HANDOFF_PATH)
    if not handoff_path.exists():
        return None

    try:
        payload: dict[str, Any] = json.loads(handoff_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        _safe_unlink(handoff_path)
        return None

    _safe_unlink(handoff_path)

    created_at = float(payload.get("created_at", 0))
    if time.time() - created_at > HANDOFF_TTL_SECONDS:
        return None

    try:
        return int(payload["user_id"])
    except (KeyError, TypeError, ValueError):
        return None


def _safe_unlink(path: Path) -> None:
    """Delete a handoff file without failing normal app startup."""
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass
