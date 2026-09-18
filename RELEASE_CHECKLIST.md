# Clean Release Checklist

Use this checklist before sharing a zip of Language Learning Hangman.

1. Run `python -m pytest`.
2. Run `python -m src.cli validate-content --summary --coverage`.
3. Run `python -m src.cli release-check`.
4. Confirm the release copy does not include local-only artifacts:
   `.venv`, `.idea`, `__pycache__`, `.pytest_cache`, `.ruff_cache`,
   `.pytest_tmp`, `pytest_tmp*`, `pytest-cache-files-*`, `data/app.db`,
   `.streamlit/secrets.toml`, `*.db`, `*.sqlite`, `*.sqlite3`, or `*.pyc`.
5. Confirm `data/words/*.json` is included.
6. Confirm no local learner data or runtime database files are included.

For a clean zip, use `scripts/build_release.ps1`. It creates a shareable copy
with source files and word-bank JSON while excluding local user data, caches,
virtual environments, editor folders, and runtime database files.
