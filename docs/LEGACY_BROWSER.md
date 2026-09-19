# Language Learning Hangman

Language Learning Hangman is a local-first Streamlit app that turns Hangman into situation-based language practice. Learners create a local profile, choose a target language, pick a real-world situation, play short Hangman sessions, and review progress stored on their own machine.

Current version: `v1.0.0-beta`

## Portfolio Showcase

This repo is designed to be a GitHub-ready portfolio project that demonstrates building a production-minded MVP with Codex:

- Modular Python architecture with UI, services, repositories, models, utilities, and tests separated.
- Local-first persistence with SQLite and curated JSON word-bank content.
- Secure local password hashing without storing plain-text passwords.
- Rule-based adaptive learning and review logic without machine learning.
- Content validation, release hygiene checks, backup/restore utilities, and CI.
- Optional FastAPI auth gateway that serves a standalone login page and hands a signed local cookie to Streamlit.
- A documented path from the local gateway to a future AWS deployment.

See `docs/ARCHITECTURE.md` for the system design and `docs/DEPLOYMENT.md` for local, Docker, and future AWS notes.

## Features

- Local sign-up and login with hashed passwords.
- Guest practice in isolated temporary storage, with no account required.
- English, Spanish, and French JSON word banks.
- First-time three-round assessment for calibrated level selection.
- Situation-based sessions such as Restaurant, Airport, Hotel, Cafe, Hospital, and School/College.
- Simple default practice setup with advanced controls available when needed.
- Standard, Weak Area, Category, Review, and custom practice flows.
- Easy Mode with 7 lives and progressive hints after wrong guesses 1, 3, and 5.
- Hard Mode with 5 lives and hints revealed only when 2 lives or fewer remain.
- Visual Hangman stages, humorous feedback lines, and post-round learning review.
- Rule-based adaptive learning for word choice, review scheduling, recommendations, and mastery labels.
- Dashboard cards for language, effective level, daily goal progress, streaks, review words due, and suggested practice.
- Local content validation, JSON upload import, SQLite backup/restore, and release-check utilities.

Machine learning is not included in this beta. The current adaptive behavior is intentionally rule-based and explainable so future ML can be added later without replacing the stable local-first flow.

## Install

On Windows with Python 3.12 installed, run `./scripts/start.ps1` from this folder.
It creates a local environment on first launch and opens the login page.
Use `./scripts/start.ps1 -NoBrowser` to run without opening a browser.
If a default port is occupied, the launcher prints the available port it selected.

```powershell
cd "C:\Users\saahi\OneDrive\Documents\Hangman"
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If your system uses `python` instead of `py`, use that command instead.

## Run

Recommended local run path:

```powershell
python -m src.cli run-auth-gateway
```

Then open:

```text
http://localhost:8000/login
```

The FastAPI gateway serves the polished login page, validates credentials through the
existing local `AuthService`, sets a signed `httpOnly` cookie, and redirects to
Streamlit at `http://localhost:8501`.

To run the Streamlit app directly as a development fallback:

```powershell
streamlit run app.py
```

Or use the helper command shown by the CLI:

```powershell
python -m src.cli run-app
```

The older CustomTkinter desktop launcher is still available as an optional local wrapper:

```powershell
python desktop_app.py
```

After a successful sign-in, the desktop launcher opens the Streamlit app and hands off
the logged-in user locally. It is kept for local desktop-style demos, while the gateway
path is the cleaner browser-based structure.

## Run With Docker

Docker is optional, but useful for reviewers who want a clean gateway-based environment:

```powershell
docker build -t language-hangman .
docker run --rm -p 8000:8000 -p 8501:8501 language-hangman
```

Then open:

```text
http://localhost:8000/login
```

## How To Play

1. Start the app and create a local profile, or sign in with an existing one.
2. Choose your target language, level, and preferred categories.
3. Complete the existing short assessment when the app asks for it.
4. Open the game page, choose where you are going today, and pick Easy Mode or Hard Mode.
5. Start a session. Advanced settings are optional.
6. Guess one letter at a time until you solve the word or run out of lives.
7. Review the learning card after each round: target word, meaning, example sentence, sentence translation, pronunciation text, usage note, synonym, association, result, and review status.
8. Continue through the session, start another session, or view your reports.

## Game Modes

Easy Mode gives 7 lives. Hints unlock gradually after wrong guesses 1, 3, and 5.

Hard Mode gives 5 lives. Hints stay hidden early and reveal only when the player has 2 lives or fewer.

Switching modes or starting a new session resets the active round so old guesses, lives, and revealed hints do not carry into the new game.

## Hint Rules

Each word can show a meaning hint, synonym hint, and association hint. Hints that are revealed stay visible for the rest of the round.

The app should never show a blank hint. If a word is missing a specific hint, the hint service falls back to another useful field such as association, example sentence, category, or a simple part-of-speech clue.

## Test

```powershell
python -m pytest
python -m src.cli validate-content --summary --coverage
python -B -m src.cli release-check
```

`release-check` expects a clean shareable copy. It will flag local artifacts such as `.venv/`, cache folders, `data/app.db`, and stray `*.db` files.

To build a clean local zip without shipping user data:

```powershell
.\scripts\build_release.ps1
```

## Project Structure

```text
language_hangman/
|-- app.py
|-- desktop_app.py
|-- Dockerfile
|-- VERSION
|-- RELEASE_NOTES.md
|-- BETA_TEST_LOG.md
|-- requirements.txt
|-- pyproject.toml
|-- README.md
|-- .dockerignore
|-- docs/
|   |-- ARCHITECTURE.md
|   `-- DEPLOYMENT.md
|-- .github/
|   `-- workflows/
|       `-- ci.yml
|-- assets/
|   `-- audio/
|-- data/
|   `-- words/
|       |-- english.json
|       |-- french.json
|       `-- spanish.json
|-- src/
|   |-- cli.py
|   |-- db/
|   |-- gateway/
|   |-- models/
|   |-- services/
|   |-- ui/
|   `-- utils/
`-- tests/
```

`data/app.db` is created locally when the app initializes. It is runtime data, not source content.

## Word Banks

Word-bank files live in `data/words/*.json`. Each word should include:

- `word_id`
- `word`
- `meaning`
- `language`
- `situations`
- `category`
- `difficulty`
- `hint`
- `translation`
- `example_sentence`
- `sentence_translation`
- `pronunciation_text`
- `usage_note`
- `synonym`
- `association`
- `synonym_hint`
- `association_hint`

Supported categories are `noun`, `verb`, `adjective`, and `adverb`. Supported difficulties are `beginner`, `intermediate`, and `advanced`.

Import behavior is intentionally conservative: invalid rows are skipped, duplicate word/language pairs are reported, and existing database words are not overwritten by UI uploads. Content validation also reports quality warnings for generic examples, weak usage notes, obvious missing accents, and pronunciation text that needs learner-friendly guidance.

## Audio Notes

Optional audio files live in `assets/audio/`:

- `background_music.wav`
- `correct_guess.wav`
- `wrong_guess.wav`

The beta includes simple generated fallback WAV tones. You can replace them later with royalty-free or CC0 files using the same filenames. If audio files are missing or browser playback is blocked, gameplay continues silently.

## Troubleshooting

- If `streamlit` is not recognized, activate your virtual environment and run `pip install -r requirements.txt` again.
- If the app opens but has no words, run `python -m src.cli seed-content` and then restart Streamlit.
- If content import fails, run `python -m src.cli validate-content --summary --coverage` to see missing fields, duplicates, or unsupported categories.
- If audio does not play, keep playing normally. Browser autoplay rules or missing files can block sound without affecting gameplay.
- If release-check reports `.venv/`, cache folders, or `data/app.db`, that means your working copy has local runtime files. Remove those only from a shareable zip, not from your active personal copy unless you intentionally want a clean reset.

## Save File Notes

The Streamlit beta stores profiles, preferences, sessions, review queue items, and word progress in SQLite at `data/app.db` by default. You can override runtime paths with:

- `LANGUAGE_HANGMAN_DATA_DIR`
- `LANGUAGE_HANGMAN_WORDS_DIR`
- `LANGUAGE_HANGMAN_DB_PATH`

The gateway creates a private `data/.session_secret` key on first login.
Do not share that file. Set `LANGUAGE_HANGMAN_SESSION_SECRET` to supply your own key.
Guest progress is separate from registered accounts and is discarded on logout or
after the browser session is released. Reloading a guest page starts a new guest session.

Progress backup and restore use JSON:

```powershell
python -m src.cli export-progress --output .\backups\progress.json
python -m src.cli import-progress --input .\backups\progress.json
```

Legacy Tkinter save files such as `user_data.pkl` and `Performance_data.pkl` are not deleted or modified by this app. They are not part of the active Streamlit persistence path, so keep a backup if you still need them for an older build.

## Local Admin CLI

```powershell
python -m src.cli show-config
python -m src.cli show-config --json
python -m src.cli validate-content --summary --coverage
python -m src.cli validate-content --errors-only
python -m src.cli seed-content
python -m src.cli run-auth-gateway
python -B -m src.cli release-check --json
.\scripts\build_release.ps1
```

## Clean Repo / Zip Checklist

Before sharing a zip or release copy, exclude:

- `.venv/`
- `__pycache__/`
- `*.pyc`
- `.pytest_cache/`
- `.pytest_tmp/`
- `pytest_tmp*/`
- `pytest-cache-files-*/`
- `codex_pytest_tmp*/`
- `.ruff_cache/`
- `.mypy_cache/`
- `.coverage`
- `htmlcov/`
- `build/`
- `dist/`
- `data/app.db`
- stray `*.db` or `*.sqlite` files
- `.streamlit/secrets.toml`

Keep `data/words/*.json` included because those are source word-bank files.

See `RELEASE_CHECKLIST.md` for the short release checklist.

## GitHub Checklist

Before pushing publicly:

- Run `python -m pytest`.
- Run `ruff check .`.
- Run `python -m src.cli validate-content --summary --coverage`.
- Run `python -B -m src.cli release-check` from a clean copy or release package.
- Confirm `data/app.db`, `.venv/`, cache folders, local backups, and secrets are not staged.
- Add screenshots or a short demo video to the GitHub repo page if you want reviewers to understand the app quickly.

GitHub Actions are included in `.github/workflows/ci.yml` to run lint, tests, content validation, and release hygiene checks on pushes and pull requests.

## Manual Beta Checklist

- Register a new local user.
- Log out and log back in with that user.
- Confirm language and profile preferences save.
- Complete the existing three-round assessment.
- Start Easy Mode and confirm 7 lives.
- In Easy Mode, confirm hints reveal after wrong guesses 1, 3, and 5.
- Start Hard Mode and confirm 5 lives.
- In Hard Mode, confirm hints stay hidden until lives are 2 or fewer.
- Win a round and confirm progress/report data updates.
- Lose a round and confirm the word appears in review behavior.
- Toggle sound/music on and off; missing or blocked audio should not crash.
- Run content validation and tests before sharing.

## Known Beta Limitations

- Content validation reports 759 editorial warnings in the supplied word banks,
  mostly generic examples, pronunciation guidance, and usage notes. All 324
  entries pass structural validation, but the vocabulary content still needs editorial review.

- No machine learning yet.
- No external APIs, cloud sync, or multi-device account system.
- The FastAPI auth gateway is local-first; hosted deployment still needs HTTPS, persistent storage, and production secret management.
- CSV import is future scope; JSON import is the supported beta path.
- Audio is optional and browser playback may be blocked by browser policy.
- Legacy `.pkl` save files are preserved but not automatically migrated into SQLite.
- The UI is ready for beta testing, not a final commercial design system.

## Roadmap

- Expand curated language content.
- Add CSV import after more JSON import testing.
- Improve visual reporting where charts add real clarity.
- Add optional feedback/audio settings.
- Move the local FastAPI auth gateway behind HTTPS and persistent storage for AWS.
- Prepare a future ML integration seam while preserving the current rule-based behavior.
