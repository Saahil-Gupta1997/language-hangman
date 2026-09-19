# Language Hangman Desktop

A local desktop application for English travel vocabulary practice, built with
Python, CustomTkinter and SQLite. No browser server, paid API, cloud account or
network connection is required during normal use.

**Version: 1.0.0rc1 — release candidate.** The software changes are implemented;
a final 1.0 release requires the Windows installer/native UI acceptance pass and
independent content/user review listed in `docs/ACCEPTANCE.md`. This source package
is not a prebuilt Windows installer. Do not describe unrun gates as passed.

## What you can do

- Create a password-protected local profile or try disposable guest practice.
- Practise 30 English words across Restaurant, Airport and Hotel.
- Choose Easy (7 lives) or Hard (5 lives), Standard or Review, and 3/5/10 rounds.
- Resume saved profile sessions with guesses, lives, clues and learning cards intact.
- Read original examples, plain-English meanings, usage notes and approximate
  pronunciation spelling. There are no invented synonym labels.
- View accurately defined all-time round, session, word and guess metrics.
- Back up/restore all local profiles, export one profile's progress, or delete it.
- Change text size, navigate by keyboard, and export privacy-safe diagnostics.

The English starter pack uses English definitions. It does not provide bilingual
translations. Difficulty and progress describe the game, not certified language
proficiency. Recommendations are rule-based; this application contains no ML.

## Run from source (developers)

Python 3.12 is the build/test target. On Windows:

```powershell
./scripts/start.ps1
```

Or:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-desktop.txt
.\.venv\Scripts\python.exe desktop_app.py
```

A graphical desktop is required. The source launcher requires Python; the generated
Windows installer bundles Python and dependencies for end users.

## Build the Windows application and installer

On Windows x64 with Python 3.12 and Inno Setup 6 installed:

```powershell
./scripts/build_desktop.ps1
```

Outputs:

- `dist/LanguageHangman/LanguageHangman.exe` with its supporting files.
- `dist/installer/LanguageHangman-1.0.0rc1-Setup.exe`.
- `dist/installer/SHA256.txt`.

Keep the whole portable application folder together. Do not distribute its EXE alone.
The installer adds Start-menu/uninstall entries and an optional desktop shortcut.
It installs per user without administrator access. The installer is unsigned until
its owner supplies a signing certificate; no certificate or signing claim is included.

The **Desktop release candidate** GitHub Actions workflow builds on Windows,
exercises the native UI, installs the result, exercises the installed application,
and uninstalls it. Run it with `workflow_dispatch` after uploading this codebase.
Its artifacts include the installer and actual smoke results/screenshots when available.

## Data, upgrades and recovery

Windows data is stored in `%LOCALAPPDATA%\LanguageHangman`, separately from program
files. macOS/Linux development paths follow their application-data conventions.
Environment overrides remain available for development: `LANGUAGE_HANGMAN_DATA_DIR`
and `LANGUAGE_HANGMAN_DB_PATH`.

- Every accepted action is persisted. Completed rounds, word progress, review queue,
  completion receipt and desktop state commit together.
- Database migrations run on a staging copy and keep a pre-upgrade backup.
- Automatic daily backups retain seven daily copies; manual/pre-upgrade backups remain.
- Restore validates a candidate, upgrades a staging copy, creates a safety backup,
  then replaces the current database. Invalid backups leave current data unchanged.
- Only one desktop process may use the same database at a time.
- Close the app before updating. Reinstalling/uninstalling preserves learner data.
- Import an old installation by selecting its `data/app.db` through Restore on the
  sign-in page. This replaces all current profiles after confirmation; it is not a merge.
  Old results remain available; new sessions use the curated English pack.

Profiles protect in-app access, not access by someone who can read your OS files.
The database is not encrypted. Full backups contain password hashes and all profiles;
keep them private. Profile JSON exports exclude credentials and cannot replace full
recovery backups. There is no email password recovery or telemetry.

## Verification

```powershell
python -m pip install -r requirements.txt -r requirements-desktop.txt
python -m pytest -q
python -m ruff check .
python scripts/check_curated_content.py
python desktop_app.py --smoke-test desktop-evidence
```

The smoke command needs a graphical desktop and uses temporary profiles, not your data.
See `docs/VERIFICATION.md` for results actually observed in the implementation environment.
See `docs/ACCEPTANCE.md` for pending release gates and a manual test procedure.

## Code map

| Location | Responsibility |
| --- | --- |
| `desktop_app.py` | Supported desktop entry point and single-instance ownership |
| `src/desktop/` | Small native views, runtime support and desktop smoke journey |
| `src/desktop/content/` | 30-word English starter pack |
| `src/services/practice_service.py` | Persisted action/session orchestration |
| `src/services/game_service.py` | Reused game rules and idempotent completion |
| `src/db/transaction.py` | Shared transaction across nested repository calls |
| `src/services/desktop_storage.py` | Validated backups, privacy and report aggregation |
| `packaging/` | PyInstaller and Inno Setup definitions |
| `tests/test_desktop_delivery.py` | Failure, retry, recovery, upgrade and privacy regression checks |

The older Streamlit/FastAPI/React paths and 324-word banks remain as compatibility
source and regression fixtures. They are **not supported desktop entry points** and
are excluded from the frozen application's import graph/resources. Historical
instructions are in `docs/LEGACY_BROWSER.md`; they do not describe this release.

## Source archive

```powershell
python scripts/build_release.py --name language-hangman-desktop-1.0.0rc1
```

The builder excludes databases, secrets, backups, environments and build output.
