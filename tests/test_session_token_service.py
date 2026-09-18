"""Tests for signed gateway session tokens."""

from src.services.session_token_service import (
    create_session_token,
    extract_session_token_from_cookie_header,
    verify_session_token,
)


def test_session_token_round_trip() -> None:
    token = create_session_token(
        user_id=42,
        secret="test-secret",
        ttl_seconds=60,
        now=100,
    )

    assert verify_session_token(token, secret="test-secret", now=120) == 42


def test_session_token_rejects_tampering() -> None:
    token = create_session_token(
        user_id=42,
        secret="test-secret",
        ttl_seconds=60,
        now=100,
    )
    tampered_token = token.replace(token[0], "x", 1)

    assert verify_session_token(tampered_token, secret="test-secret", now=120) is None


def test_session_token_rejects_expired_payload() -> None:
    token = create_session_token(
        user_id=42,
        secret="test-secret",
        ttl_seconds=10,
        now=100,
    )

    assert verify_session_token(token, secret="test-secret", now=111) is None


def test_extract_session_token_from_cookie_header() -> None:
    cookie_header = "theme=light; language_hangman_session=abc.def; other=value"

    assert extract_session_token_from_cookie_header(cookie_header) == "abc.def"


def test_expiry_boundary_and_non_ascii_token_are_rejected():
    token = create_session_token(42, secret="test", now=100, ttl_seconds=10)
    assert verify_session_token(token, secret="test", now=110) is None
    assert verify_session_token("invalid.\u00e9", secret="test") is None


def test_installation_secret_persists(tmp_path, monkeypatch):
    from src.services import session_token_service as service

    monkeypatch.setattr(service, "DATA_DIR", tmp_path)
    monkeypatch.setattr(service, "SESSION_SECRET", None)
    first = service.get_session_secret()
    assert len(first) >= 48
    assert service.get_session_secret() == first
