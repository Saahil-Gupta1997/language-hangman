# Language Hangman Desktop

An offline Windows app for practising English travel vocabulary through Hangman: 30
curated words for the Restaurant, Airport and Hotel. It is built with Python, CustomTkinter
and SQLite. It is rule-based software built with AI assistance: it contains no machine
learning, chatbot or network service, and it needs no account or internet connection.

**Status: 1.0.0rc2, a tested release candidate. It is not the final 1.0.**

| Verified on the build machine (Windows 11) | Still pending, needs people |
| --- | --- |
| 163 automated tests, lint, content and release checks on `4ad1e34` | Clean-computer install without Python (G5) |
| Installer built from that commit; install, upgrade from rc1 with real data, beta import, recovery, uninstall | Keyboard-only, display scaling and recovery checks by hand (G6–G8) |
| 16-step native journey in the installed app, without Python on `PATH` | Review of all 30 teaching cards by a qualified reviewer (G9) |
| Performance with 5,000 rounds: every operation under 1 second | Five learner sessions (G10) |
| | Third-party licence notices in the installer (G15); licence choice |

The gates, evidence and go/no-go record are in [docs/ACCEPTANCE.md](docs/ACCEPTANCE.md).

## Demo

[2½-minute captioned recording](docs/media/language-hangman-1.0.0rc2-demo.mp4): a new
profile, Review offered as Standard for a new learner, a Standard session with learning
cards, reports, a shortened Review, resuming after closing, word cards, text size, settings
and recovery from a damaged data file. It is a scripted run of revision `4ad1e34` from
source, driven through the app's own controls and slowed so that captions can be read; only
the app window is captured.

Screenshots from the installed rc2 build:

| Practice round | Review shortened, with the reason | Recovery window |
| --- | --- | --- |
| ![Practice round](docs/media/practice.png) | ![Review shortened](docs/media/review-shortened.png) | ![Recovery](docs/media/recovery.png) |

## What it does

- Local profiles protected by a password, and guest practice that is not saved.
- 30 curated English words in three travel situations, with plain-English meanings, an
  original example, a usage note and an approximate respelling for pronunciation.
- Easy (7 lives, clues shown) or Hard (5 lives), 3, 5 or 10 rounds per session.
- **Standard** practice, and **Review** of words you have already practised in that
  situation (due words first). A new learner is offered Standard instead, and a shortened
  Review says why.
- Sessions are saved after every guess and can be resumed after closing the app.
- Reports on rounds, sessions, words and guesses; word cards for all 30 words.
- Full backup and restore, a daily automatic backup (seven kept), profile export and
  deletion, and a recovery window if the data file is damaged.
- Text size, keyboard operation and privacy-safe diagnostics.

## Install

1. Download `LanguageHangman-1.0.0rc2-Setup.exe` from the release package and check it:

   ```powershell
   Get-FileHash .\LanguageHangman-1.0.0rc2-Setup.exe -Algorithm SHA256
   ```

   Expected: `2fc27de78a94aca7c96637dafc70b15ff707349b403c878bfd050ad79a58dc95`.
2. Run it. **The installer is not code-signed**, so Windows SmartScreen shows "Windows
   protected your PC" and "Unknown publisher". Choose *More info › Run anyway* only if the
   checksum matched. It installs for the current user; no administrator rights are needed.
3. Start *Language Hangman* from the Start menu.

**Upgrade:** close the app and run the newer installer. Profiles, progress and saved
sessions are kept; any database upgrade runs on a copy after a pre-upgrade backup.
**Uninstall:** Settings › Apps, or the Start-menu uninstaller. Your data is kept in
`%LOCALAPPDATA%\LanguageHangman`; delete that folder to remove it.

## Data, backup and recovery

- Data lives in `%LOCALAPPDATA%\LanguageHangman\app.db`; backups in its `backups` folder.
- **Settings › Create full backup** saves every profile. **Restore** checks a backup,
  keeps a safety copy of the current data, and only then replaces it. An invalid backup
  changes nothing.
- **If the data file is damaged**, the app opens a recovery window instead of failing.
  Choose the newest automatic backup (or your own) and confirm; the damaged file is kept
  in `backups\quarantine-…` and you can sign in again.
- **Moving from the older browser beta:** on the sign-in screen, choose *Restore / import
  old database* and pick the beta's `data\app.db`. This replaces all current profiles after
  confirmation. Old results stay in reports; new practice uses the 30 curated words.
- **Diagnostics** (Settings) export the app, Python and Windows versions, database checks
  and recent failure records (operation, stage, error type). They exclude passwords, usernames, session
  content and personal folder paths.

## Known limitations

- English only, about CEFR A2, 30 words; meanings are in English, not translations.
- Pronunciation is an approximate respelling, not audio or IPA.
- Easy mode offers two distinct clues per word (the synonym clue is empty by design).
- Windows screen readers generally cannot read CustomTkinter controls.
- The database is not encrypted; passwords protect in-app access only. There is no
  password reset by email. Full backups contain every profile's password hash: keep them
  private.
- One copy of the app per Windows account at a time; guest practice is discarded on
  sign-out.
- The installer is unsigned and does not yet include third-party licence notices (T-28);
  it should not be distributed publicly until they are added.
- Tested on Windows 11 only; Windows 10 is expected to work but has not been checked.
- Supported history (proposed): up to 5 profiles and 5,000 rounds per profile.

## How it was built

The beta and rc1 were written with AI coding assistance. The rc2 delivery (defect fixes,
tests, packaging, validation and these documents) was carried out by Claude Code at the
owner's direction. Every fix was reproduced first and checked afterwards, and results are
tied to commits. Educator, learner and manual checks are left for people to perform and
record. See [How AI assistance was used and verified](docs/DELIVERY.md#how-ai-assistance-was-used-and-verified).

## Project documents

| Document | Contents |
| --- | --- |
| [ACCEPTANCE.md](docs/ACCEPTANCE.md) | Release gates, manual test procedures, evidence index, go/no-go |
| [DELIVERY.md](docs/DELIVERY.md) | Defect and task register, RAID log, decision log, milestones, AI assistance |
| [VERIFICATION.md](docs/VERIFICATION.md) | Results by revision, installer validation, performance, requirement traceability |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Components, data flow, persistence, recovery |
| [CONTENT_REVIEW.md](docs/CONTENT_REVIEW.md) | Intended learner, review worksheet for 30 cards, content provenance |
| [USER_ACCEPTANCE.md](docs/USER_ACCEPTANCE.md) | Five-session learner protocol |
| [RELEASE_NOTES.md](RELEASE_NOTES.md), [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) | What changed; how to release |
| [LEGACY_BROWSER.md](docs/LEGACY_BROWSER.md) | The unsupported browser prototype |

## For developers

Python 3.12 on Windows:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-desktop.txt -r requirements.txt
.\.venv\Scripts\python.exe desktop_app.py
```

(`./scripts/start.ps1` does the same for running the app.) Checks:

```powershell
python -m pytest -rs
python -m ruff check .
python scripts/check_curated_content.py
python -m src.cli release-check
python desktop_app.py --smoke-test desktop-evidence
```

The GUI tests and the smoke journey need a Windows desktop session; they use temporary
data, never yours. Build the installer with Inno Setup 6 installed:
`./scripts/build_desktop.ps1 -Python <python 3.12 exe>`, then follow
[RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md).

### Code map

| Supported desktop app | Responsibility |
| --- | --- |
| `desktop_app.py` | Entry point: single instance, recovery window, smoke journey |
| `src/desktop/` | Views, recovery window, keyboard and window helpers, logging |
| `src/desktop/content/english.json` | The 30 curated words |
| `src/services/practice_service.py` | Session orchestration; saves every action |
| `src/services/game_service.py` | Game rules, Review eligibility, completion |
| `src/services/curated_content.py`, `word_service.py` | Curated-only word selection |
| `src/services/desktop_storage.py` | Backups, restore, recovery, export, diagnostics |
| `src/db/` | SQLite schema, migrations, transactions |
| `packaging/`, `scripts/build_desktop.ps1` | PyInstaller and Inno Setup build |
| `tests/` | 163 tests, including GUI scenarios run one per process |

**Legacy, unsupported:** `app.py`, `src/ui/`, `src/gateway/`, `frontend/`, `Dockerfile`,
`data/words/` and most of `src/cli.py` belong to the earlier browser prototype. They are not
in the installer; the desktop app reuses the shared engine and can import beta databases.
See [LEGACY_BROWSER.md](docs/LEGACY_BROWSER.md).

## Licence

Not yet chosen (decision DEC-08 is pending with the owner). Until then, all rights are
reserved. Bundled third-party components keep their own licences.
