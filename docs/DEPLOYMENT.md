# Deployment Notes

This project is ready to share as a local-first GitHub portfolio project. A hosted deployment is possible, but it should be treated as a separate milestone.

## Recommended Showcase Path

1. Publish the clean source repo on GitHub.
2. Include `data/words/*.json` so the app has content immediately.
3. Exclude runtime data such as `data/app.db`, `.venv/`, caches, and secrets.
4. Use GitHub Actions to run lint, tests, content validation, and release hygiene checks.
5. Add screenshots or a short demo video to the repository description or README.

## Local Run

Gateway-based local run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m src.cli run-auth-gateway
```

Then open:

```text
http://localhost:8000/login
```

Direct Streamlit fallback for development:

```powershell
streamlit run app.py
```

## Docker Run

```powershell
docker build -t language-hangman .
docker run --rm -p 8000:8000 -p 8501:8501 language-hangman
```

Then open:

```text
http://localhost:8000/login
```

## Release Hygiene Check

Use `-B` so Python does not create `__pycache__` while checking for local artifacts:

```powershell
python -B -m src.cli release-check
```

## AWS Direction

If you want to showcase cloud deployment later, a clean target architecture would be:

```text
Browser
  |
  |-- HTTPS load balancer
        |
        |-- FastAPI gateway for /login and /api/auth
        |-- Streamlit app for /app
        |-- PostgreSQL or another persistent database
```

For AWS, prefer a persistent database such as RDS/PostgreSQL instead of relying on a container-local SQLite file. SQLite is excellent for the local-first beta, but a hosted multi-user app needs persistent storage, backups, and environment-based secrets.

## Future Auth Gateway

The local beta now includes the lightweight version of this split:

```text
/login -> standalone HTML/CSS login page
/api/auth -> validates credentials and sets signed httpOnly session cookie
/app -> Streamlit, only available with valid session cookie
```

This keeps Streamlit focused on the learning experience while a normal web framework owns auth, cookies, and routing.

In local development there is no reverse proxy, so FastAPI and Streamlit run on separate ports:

```text
http://localhost:8000/login
http://localhost:8501
```

For production, put both behind one HTTPS origin and replace the default local session secret with a real secret from environment-managed infrastructure.
