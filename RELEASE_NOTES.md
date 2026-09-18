# Release Notes

## Version: v1.0.0-beta

Language Learning Hangman is ready for beta user testing as a local-first vocabulary practice app. This release keeps the existing Streamlit + SQLite architecture and focuses on stability, clarity, and handoff readiness.

## Included

- Local profile creation and login with hashed passwords.
- English, Spanish, and French curated word banks.
- Existing three-round assessment and calibrated level flow.
- Easy and Hard game modes.
- Progressive hints with non-blank fallback behavior.
- Visual Hangman stages and humorous guess feedback.
- Optional local audio with safe fallback behavior.
- Multi-round practice sessions, review queue, dashboard, and reports.
- Local JSON word import, content validation, progress export/import, and release checks.

## Recent Changes

- Cleaned beta-facing version wording to `v1.0.0-beta`.
- Clarified active gameplay page headings so setup and play states are easier to understand.
- Added release handoff files for future beta testing notes.
- Confirmed audio remains optional and gameplay continues if playback is unavailable.

## Known Limitations

- Machine learning is not included yet.
- There are no external APIs, cloud sync, or multi-device accounts.
- CSV word import is future scope; JSON import is supported.
- Browser audio autoplay may be blocked depending on the user's browser settings.
- Legacy `.pkl` save files are preserved but not automatically migrated into SQLite.

## Manual Testing Status

Manual testing has been reported as working for the current beta flow. Before sharing a release copy, run the commands in `README.md` and record a pass in `BETA_TEST_LOG.md`.
