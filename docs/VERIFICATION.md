# Observed verification — 1.0.0rc1

Environment: Linux, Python 3.12. These are executed checks, not Windows certification.

| Check | Observed result |
| --- | --- |
| Complete Python suite | 133 passed, 1 third-party deprecation warning |
| Delivery/recovery tests | 39 passed; included in the total above |
| Ruff | All checks passed |
| Curated structural checks | 30 unique words; 10 per situation; complete required fields |
| Editorial heuristics | 24 context-keyword warnings; independent educator review pending |
| PyInstaller packaging | Linux bundle built successfully; its --help entry point ran |
| Wheel packaging | Built; desktop_app.py and curated English JSON included |
| Native GUI smoke | Attempted; blocked by no display / no DISPLAY environment variable |
| Windows EXE/installer | Not executed here; Windows workflow supplied |
| Independent learner/educator acceptance | Not performed |

## New tested failure and recovery cases

- Fresh-service completion retries do not double-count persistent round UUIDs.
- Failure in progress, review, session totals or snapshot writing rolls back the final guess.
- Failed finalization preserves caller round/session objects.
- Guesses and auto-revealed hints survive controller restart.
- All situations, game modes and session lengths complete and reconcile reports.
- Losing rounds, repeated guesses and stale-round events produce the intended counters.
- Backup/restore preserves credentials, progress and active sessions with safety backups.
- Corrupt, unrelated, future-schema and incomplete current-schema backups are rejected.
- Legacy migration preserves credentials and creates a pre-upgrade backup.
- Injected migration failure leaves the original file byte-for-byte unchanged.
- Export/deletion and diagnostics stay scoped; other profiles survive deletion.
- Legacy teaching content is excluded from new desktop practice.
- Decomposed Unicode accented input is normalized.
- Single-instance lock rejects concurrent ownership and can be reacquired after release.
- Corrupt password-hash metadata fails authentication without crashing.

Packaging checks occurred during implementation and demonstrate the build path, not
execution of the final native screens. Run the Windows workflow on the exact commit
being released. Service tests do not close native UI, installer, accessibility,
content or external-user acceptance gates in ACCEPTANCE.md.

The warning comes from Starlette TestClient in retained legacy gateway tests. It is
not a failed assertion. Retained browser regressions do not make those entry points
part of the supported desktop product.
