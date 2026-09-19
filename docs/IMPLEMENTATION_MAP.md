# Requested changes and implementation map

| Area | Implemented code / remaining limit |
| --- | --- |
| Atomic, duplicate-safe completion | db/transaction.py, game_service.finalize_round, persistent receipts |
| Resume/recovery | practice_service.py, per-action versioned snapshots |
| One desktop experience | desktop_app.py, focused native views; browser paths unsupported |
| Installer/distribution | PyInstaller/Inno Setup definitions, build script and Windows workflow; execution pending |
| App-data paths | utils/config.py; explicit old-database import through Restore |
| Accounts/privacy | Password hashing, corrupt-hash rejection, export/deletion; no desktop cookie handoff |
| Content quality | 30-word English pack; older corpus excluded; educator review pending |
| Difficulty/adaptation | Game settings and explained rules; no proficiency certification claims |
| Accessibility | Keyboard activation/focus, Unicode input, text sizing, scrollable views; native checks pending |
| Reports | desktop_storage.progress_report; completed records and stated denominators |
| Backup/upgrades | Staged migration/restore; safety and daily backups |
| Diagnostics | Bounded event logs and whitelisted diagnostic export |
| Maintainability | Separate authentication, practice, reports and settings views |
| Verification | 39 delivery tests plus retained regressions; native smoke and installer pipeline |
| Support/updates | In-app Help, README, release checklist, manual updates and preservation instructions |

Cloud sync, ML, bilingual teaching, automatic updates, multiplayer and additional-platform
certification are outside this release. Guest progress is intentionally temporary.
No learner studies or educator sign-offs are fabricated. Version 1.0.0rc1 remains until
the actual acceptance gates are completed.
