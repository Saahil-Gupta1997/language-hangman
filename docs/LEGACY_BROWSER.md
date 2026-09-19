# Legacy browser prototype (unsupported)

Before the desktop app, Language Hangman was a local Streamlit web app (v1.0.0-beta) with an
optional FastAPI sign-in gateway, a React login page and Docker packaging. That code is
**not part of the supported product** and is not included in the Windows installer. It stays
in the repository for three reasons:

- The desktop app reuses its game engine and database layer (`src/services`, `src/db`).
- Its tests are regression tests for that shared code.
- Databases created by the beta can be imported into the desktop app (Settings or the
  sign-in screen › Restore / import old database); their results stay reportable.

| Legacy item | Path |
| --- | --- |
| Streamlit entry point and pages | `app.py`, `src/ui/` |
| FastAPI gateway | `src/gateway/` |
| React login | `frontend/` |
| Admin CLI (`release-check` and `validate-content` are still used by CI) | `src/cli.py` |
| Docker image | `Dockerfile` |
| 324-word English/French/Spanish banks (not used by the desktop app) | `data/words/` |

Known problems that were never fixed in the prototype, and are why it is unsupported: the
French and Spanish banks contain misspellings (accents stripped), the Streamlit app
re-initialised the database on every interaction, the sign-in pages advertised features that
did not exist, and the pinned web framework versions have published security advisories.

To run the prototype for regression work only:

```powershell
python -m pip install -r requirements.txt
python -m src.cli run-auth-gateway    # then open http://localhost:8000/login
```
