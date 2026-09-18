# Architecture

Language Learning Hangman is currently a local-first Streamlit application with a modular service layer. The goal of this version is to be easy to run, inspect, test, and extend.

## Runtime Shape

```text
Browser
  |
  |-- Streamlit UI
        |
        |-- UI pages in src/ui/
        |-- business services in src/services/
        |-- repository/database layer in src/db/
        |-- SQLite runtime database at data/app.db
        |-- curated JSON word banks in data/words/
```

## Core Boundaries

- `src/ui/` owns Streamlit rendering and session-state orchestration.
- `src/services/` owns application behavior such as auth, word selection, game flow, reports, review scheduling, and validation.
- `src/db/` owns SQLite initialization and repository access.
- `data/words/*.json` is source content and should be committed.
- `data/app.db` is runtime user data and should not be committed.

## Auth Today

The beta supports local accounts with PBKDF2 password hashes in SQLite. The preferred local entry point is the FastAPI gateway, with direct Streamlit and desktop launchers kept as fallbacks:

- `python -m src.cli run-auth-gateway` starts the polished FastAPI login page and Streamlit together.
- `streamlit run app.py` keeps the Streamlit auth page as a development fallback.
- `python desktop_app.py` remains an optional CustomTkinter wrapper for desktop-style local demos.

The gateway path serves `/login` from FastAPI, posts credentials to `/api/auth`, sets a signed `httpOnly` cookie, and redirects to Streamlit.

```text
Browser
  |
  |-- http://localhost:8000/login
        |
        |-- FastAPI validates via AuthService
        |-- FastAPI sets language_hangman_session cookie
        |
  |-- http://localhost:8501
        |
        |-- Streamlit reads Cookie header
        |-- Streamlit restores current_user
```

The signed token code lives in `src/services/session_token_service.py`. It uses HMAC signing from the Python standard library, not an external auth provider.

## Future Web Deployment Direction

If the app grows into a hosted product, auth should move out of Streamlit and into a web gateway:

```text
Browser
  |
  |-- /login -> FastAPI static login page
  |            posts credentials to /api/auth
  |
  |-- /app   -> Streamlit app behind a valid signed session cookie
```

The local FastAPI gateway is already a first step toward that shape. A production version would add HTTPS, a production secret, persistent database storage, and a reverse proxy or load balancer.

## Why Not Cloud Yet?

For the current portfolio beta, local-first is intentional:

- No hosted secrets or account infrastructure are required.
- The app is easy for reviewers to run from GitHub.
- The database and word-bank behavior are transparent.
- The code demonstrates modular Python design before adding deployment complexity.

AWS is a good next milestone after the local beta is stable and documented.
