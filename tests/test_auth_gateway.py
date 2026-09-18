"""Tests for the optional FastAPI auth gateway."""

from fastapi.testclient import TestClient

from src.db.database import init_db
from src.gateway.app import create_gateway_app
from src.services.auth_service import AuthService
from src.utils.config import SESSION_COOKIE_NAME


def test_gateway_login_page_renders_standalone_auth_ui(tmp_path) -> None:
    db_path = tmp_path / "gateway_login_page.db"
    init_db(db_path=db_path, seed_words=False)
    client = TestClient(create_gateway_app(db_path=db_path, streamlit_url="http://test/app"))

    response = client.get("/login")

    assert response.status_code == 200
    assert "Play.<br>Learn.<br>Get Fluent." in response.text
    assert "Welcome back!" in response.text
    assert "Username or Email" in response.text


def test_gateway_login_sets_signed_session_cookie(tmp_path) -> None:
    db_path = tmp_path / "gateway_login.db"
    init_db(db_path=db_path, seed_words=False)
    auth_service = AuthService(db_path=db_path)
    auth_service.register_user(
        username="gatewayuser",
        password="secret123",
        target_language="english",
        level="beginner",
    )
    client = TestClient(create_gateway_app(db_path=db_path, streamlit_url="http://test/app"))

    response = client.post(
        "/api/auth",
        json={
            "username": "gatewayuser",
            "password": "secret123",
            "remember_me": True,
        },
    )

    assert response.status_code == 200
    assert response.json()["redirect"] == "http://test/app"
    assert SESSION_COOKIE_NAME in response.cookies
    assert "httponly" in response.headers["set-cookie"].lower()


def test_gateway_login_rejects_bad_password(tmp_path) -> None:
    db_path = tmp_path / "gateway_bad_password.db"
    init_db(db_path=db_path, seed_words=False)
    auth_service = AuthService(db_path=db_path)
    auth_service.register_user(
        username="gatewayuser",
        password="secret123",
        target_language="english",
        level="beginner",
    )
    client = TestClient(create_gateway_app(db_path=db_path, streamlit_url="http://test/app"))

    response = client.post(
        "/api/auth",
        json={
            "username": "gatewayuser",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401


def test_gateway_register_creates_user_and_sets_cookie(tmp_path) -> None:
    db_path = tmp_path / "gateway_register.db"
    init_db(db_path=db_path, seed_words=False)
    client = TestClient(create_gateway_app(db_path=db_path, streamlit_url="http://test/app"))

    response = client.post(
        "/api/register",
        json={
            "username": "newgatewayuser",
            "password": "secret123",
            "target_language": "spanish",
            "level": "beginner",
        },
    )

    assert response.status_code == 200
    assert SESSION_COOKIE_NAME in response.cookies
    assert AuthService(db_path=db_path).authenticate_user("newgatewayuser", "secret123") is not None


def test_gateway_browser_logout_clears_cookie(tmp_path) -> None:
    db_path = tmp_path / "gateway_logout.db"
    init_db(db_path=db_path, seed_words=False)
    client = TestClient(create_gateway_app(db_path=db_path, streamlit_url="http://test/app"))

    response = client.get("/logout", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"
    assert SESSION_COOKIE_NAME in response.headers["set-cookie"]
    assert "max-age=0" in response.headers["set-cookie"].lower()


def test_gateway_preserves_password_spaces_and_rejects_invalid_language(tmp_path):
    client = TestClient(create_gateway_app(db_path=tmp_path / "accounts.db"))
    credentials = {"username": "spaceuser", "password": "  secret123  "}
    assert client.post("/api/register", json=credentials).status_code == 200
    assert client.post("/api/auth", json=credentials).status_code == 200
    assert client.post(
        "/api/auth", json={**credentials, "password": "secret123"}
    ).status_code == 401
    assert client.post(
        "/api/register", json={**credentials, "target_language": "unknown"}
    ).status_code == 422
