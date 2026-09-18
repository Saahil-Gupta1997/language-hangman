"""Tests for desktop login handoff helpers."""

from __future__ import annotations

import json
import time

from src.services.desktop_login_handoff import (
    consume_desktop_login_handoff,
    write_desktop_login_handoff,
)


def test_desktop_login_handoff_round_trip(tmp_path):
    handoff_path = tmp_path / "handoff.json"

    write_desktop_login_handoff(user_id=42, remember_me=True, path=handoff_path)

    assert consume_desktop_login_handoff(path=handoff_path) == 42
    assert not handoff_path.exists()


def test_desktop_login_handoff_rejects_expired_payload(tmp_path):
    handoff_path = tmp_path / "handoff.json"
    handoff_path.write_text(
        json.dumps({"user_id": 42, "created_at": time.time() - 999}),
        encoding="utf-8",
    )

    assert consume_desktop_login_handoff(path=handoff_path) is None
    assert not handoff_path.exists()
