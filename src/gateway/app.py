"""Optional FastAPI auth gateway for the Streamlit app."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel

from src.db.database import init_db
from src.gateway.login_page import render_login_page
from src.services.auth_service import AuthService
from src.services.session_token_service import create_session_token
from src.utils.config import (
    DATABASE_PATH,
    SESSION_COOKIE_NAME,
    SESSION_TTL_SECONDS,
)
from src.utils.constants import DEFAULT_LANGUAGE, DEFAULT_LEVEL


class LoginCredentials(BaseModel):
    """Credentials posted by the standalone login form."""

    username: str
    password: str
    remember_me: bool = False


class RegisterCredentials(BaseModel):
    """Local account payload posted by the standalone create-account form."""

    username: str
    password: str
    target_language: Literal["english", "spanish", "french"] = DEFAULT_LANGUAGE
    level: Literal["beginner", "intermediate", "advanced"] = DEFAULT_LEVEL


def create_gateway_app(
    *,
    db_path: Path | None = None,
    streamlit_url: str | None = None,
) -> FastAPI:
    """Create the optional local auth gateway app."""
    resolved_db_path = init_db(db_path=db_path or DATABASE_PATH)
    resolved_streamlit_url = streamlit_url or os.getenv(
        "LANGUAGE_HANGMAN_STREAMLIT_URL",
        "http://localhost:8501",
    )
    auth_service = AuthService(db_path=resolved_db_path)
    app = FastAPI(title="Language Learning Hangman Auth Gateway")

    @app.get("/", response_class=HTMLResponse)
    def root() -> HTMLResponse:
        return HTMLResponse(
            '<meta http-equiv="refresh" content="0;url=/login">'
            '<a href="/login">Open Language Learning Hangman login</a>'
        )

    @app.get("/login", response_class=HTMLResponse)
    def login_page() -> HTMLResponse:
        return HTMLResponse(render_login_page(streamlit_url=resolved_streamlit_url))

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/auth")
    def login(credentials: LoginCredentials, response: Response) -> dict[str, str]:
        user = auth_service.authenticate_user(
            username=credentials.username,
            password=credentials.password,
        )
        if user is None:
            raise HTTPException(status_code=401, detail="Invalid username or password.")

        _set_session_cookie(
            response=response,
            user_id=int(user["id"]),
            remember_me=credentials.remember_me,
        )
        return {"redirect": resolved_streamlit_url}

    @app.post("/api/register")
    def register(credentials: RegisterCredentials, response: Response) -> dict[str, str]:
        try:
            user = auth_service.register_user(
                username=credentials.username,
                password=credentials.password,
                target_language=credentials.target_language,
                level=credentials.level,
            )
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

        _set_session_cookie(
            response=response,
            user_id=int(user["id"]),
            remember_me=True,
        )
        return {"redirect": resolved_streamlit_url}

    @app.post("/api/logout")
    def logout(response: Response) -> dict[str, str]:
        response.delete_cookie(
            key=SESSION_COOKIE_NAME,
            httponly=True,
            samesite="lax",
        )
        return {"redirect": "/login"}

    @app.get("/logout")
    def browser_logout() -> RedirectResponse:
        response = RedirectResponse(url="/login", status_code=303)
        response.delete_cookie(
            key=SESSION_COOKIE_NAME,
            httponly=True,
            samesite="lax",
        )
        return response

    return app


def _set_session_cookie(
    *,
    response: Response,
    user_id: int,
    remember_me: bool,
) -> None:
    max_age = SESSION_TTL_SECONDS if remember_me else None
    token = create_session_token(user_id=user_id)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=max_age,
        httponly=True,
        samesite="lax",
        secure=False,
    )

