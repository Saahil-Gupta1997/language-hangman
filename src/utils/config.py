"""Centralized project paths and configuration values."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from src import __release_name__, __version__

PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_VERSION = __version__
APP_RELEASE_NAME = __release_name__
APP_VERSION_DISPLAY = f"v{APP_VERSION}"


def application_data_dir() -> Path:
    if sys.platform == "win32":
        return (
            Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "LanguageHangman"
        )
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "LanguageHangman"
    return Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "language-hangman"


RESOURCE_ROOT = Path(getattr(sys, "_MEIPASS", PROJECT_ROOT))
DATA_DIR = Path(os.getenv("LANGUAGE_HANGMAN_DATA_DIR", application_data_dir()))
WORDS_DIR = Path(os.getenv("LANGUAGE_HANGMAN_WORDS_DIR", RESOURCE_ROOT / "data" / "words"))
LEVEL_WORDS_DIR = Path(__file__).resolve().parents[1] / "desktop" / "content" / "levels"
DATABASE_PATH = Path(os.getenv("LANGUAGE_HANGMAN_DB_PATH", DATA_DIR / "app.db"))
AUTH_GATEWAY_ENABLED = os.getenv("LANGUAGE_HANGMAN_AUTH_GATEWAY_ENABLED", "0") == "1"
AUTH_GATEWAY_LOGIN_URL = os.getenv("LANGUAGE_HANGMAN_LOGIN_URL", "http://localhost:8000/login")
AUTH_GATEWAY_LOGOUT_URL = os.getenv("LANGUAGE_HANGMAN_LOGOUT_URL", "http://localhost:8000/logout")
AUTH_GATEWAY_STREAMLIT_URL = os.getenv(
    "LANGUAGE_HANGMAN_STREAMLIT_URL",
    "http://localhost:8501",
)
SESSION_COOKIE_NAME = os.getenv("LANGUAGE_HANGMAN_SESSION_COOKIE", "language_hangman_session")
SESSION_SECRET = os.getenv("LANGUAGE_HANGMAN_SESSION_SECRET")
SESSION_TTL_SECONDS = int(os.getenv("LANGUAGE_HANGMAN_SESSION_TTL_SECONDS", "604800"))


def get_runtime_settings() -> dict[str, str]:
    """Return a serializable snapshot of the current runtime paths."""
    return {
        "project_root": str(PROJECT_ROOT),
        "data_dir": str(DATA_DIR),
        "words_dir": str(WORDS_DIR),
        "database_path": str(DATABASE_PATH),
        "app_version": APP_VERSION,
        "app_version_display": APP_VERSION_DISPLAY,
        "auth_gateway_enabled": str(AUTH_GATEWAY_ENABLED),
        "auth_gateway_login_url": AUTH_GATEWAY_LOGIN_URL,
        "auth_gateway_logout_url": AUTH_GATEWAY_LOGOUT_URL,
    }
