"""Signed local session tokens for the optional FastAPI auth gateway."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from http.cookies import SimpleCookie
from typing import Any

from src.utils.config import DATA_DIR, SESSION_COOKIE_NAME, SESSION_SECRET, SESSION_TTL_SECONDS


def get_session_secret() -> str:
    """Share a private installation key between the gateway and Streamlit."""
    if SESSION_SECRET:
        return SESSION_SECRET
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / ".session_secret"
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        # Another worker may still be writing the newly created key.
        for _ in range(20):
            value = path.read_text(encoding="ascii").strip()
            if value:
                return value
            time.sleep(0.05)
        raise RuntimeError("The local session key is empty.")
    value = secrets.token_urlsafe(48)
    with os.fdopen(descriptor, "w", encoding="ascii") as handle:
        handle.write(value)
    return value


def create_session_token(
    user_id: int,
    *,
    secret: str | None = None,
    ttl_seconds: int = SESSION_TTL_SECONDS,
    now: int | None = None,
) -> str:
    """Return a compact HMAC-signed token for a local user id."""
    issued_at = int(now if now is not None else time.time())
    payload = {
        "user_id": int(user_id),
        "iat": issued_at,
        "exp": issued_at + int(ttl_seconds),
    }
    payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    payload_part = _base64url_encode(payload_bytes)
    signature_part = _sign(payload_part, secret=secret or get_session_secret())
    return f"{payload_part}.{signature_part}"


def verify_session_token(
    token: str,
    *,
    secret: str | None = None,
    now: int | None = None,
) -> int | None:
    """Return the user id from a valid token, or None when invalid/expired."""
    try:
        payload_part, signature_part = token.split(".", maxsplit=1)
    except ValueError:
        return None

    if not token.isascii():
        return None
    expected_signature = _sign(payload_part, secret=secret or get_session_secret())
    if not hmac.compare_digest(signature_part, expected_signature):
        return None

    try:
        payload = json.loads(_base64url_decode(payload_part))
    except (json.JSONDecodeError, ValueError):
        return None

    if not isinstance(payload, dict):
        return None
    expires_at = _safe_int(payload.get("exp"))
    user_id = _safe_int(payload.get("user_id"))
    current_time = int(now if now is not None else time.time())
    if user_id is None or user_id <= 0 or expires_at is None or expires_at <= current_time:
        return None

    return user_id


def extract_session_token_from_cookie_header(
    cookie_header: str,
    *,
    cookie_name: str = SESSION_COOKIE_NAME,
) -> str | None:
    """Return the configured session cookie value from a raw Cookie header."""
    if not cookie_header:
        return None

    cookie = SimpleCookie()
    try:
        cookie.load(cookie_header)
    except Exception:
        return None

    morsel = cookie.get(cookie_name)
    if morsel is None:
        return None
    return morsel.value or None


def _sign(payload_part: str, *, secret: str) -> str:
    digest = hmac.new(
        secret.encode("utf-8"),
        payload_part.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return _base64url_encode(digest)


def _base64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _base64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _safe_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
