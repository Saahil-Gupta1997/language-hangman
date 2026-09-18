# Local Release Verification

Verified on Windows with Python 3.12 on 2026-09-07.

## Delivered

- Isolated guest practice with disposable SQLite storage.
- Account creation and login, including passwords containing spaces.
- Per-installation session signing keys and strict token expiry.
- SQLite connections close after commit or rollback.
- Compact gameplay, progressive hints, round results, and reports.
- React login connected to the real gateway API.
- Windows launcher with automatic selection of available ports.
- Source ZIP builder that excludes local data and refuses to overwrite releases.

## Verification

- Python suite: 94 tests passed.
- Ruff: passed.
- React production build: passed.
- Browser: guest entry, session start, wrong guess, and hint reveal verified.
- Responsive layout: 390-pixel viewport has no horizontal document overflow.
- Content: 324 valid entries, no invalid entries or duplicates, all coverage areas met.

## Scope

This is a local application. Public hosting, cloud sync, machine learning, and
account recovery by email are not included. The 759 content-quality warnings
remain an editorial backlog; they are not suppressed by validation.

Run `./scripts/start.ps1` to launch. Run `./scripts/build_release.ps1` to build
a shareable source ZIP. Install dependencies from `requirements.txt` after
extracting the archive; environments and local profiles are deliberately excluded.
