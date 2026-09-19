# Verification — Language Hangman 1.0.0rc2

What was actually executed, on which revision, with what result. Manual and human
acceptance gates, and their status, are in [ACCEPTANCE.md](ACCEPTANCE.md). Nothing here
was produced by a learner or an educator.

**Release candidate:** revision `4ad1e34bf1dca5286e3722152a3fbc505a05af44` (branch
`release/1.0`). Evidence: [`evidence/2026-09-19-rc2-4ad1e34/`](evidence/2026-09-19-rc2-4ad1e34/).

## Environment

| Item | Value |
| --- | --- |
| Machine | AMD Ryzen 7 6800H (8 cores/16 threads), 15.2 GB RAM, NVMe SSD |
| OS | Windows 11 Home 10.0.26200, 1920×1080 panel at 125% display scaling |
| Runtime / build | Python 3.12.1 · CustomTkinter 5.2.2 · Pillow 12.3.0 · PyInstaller 6.11.1 · Inno Setup 6.7.3 |
| Executed by | Claude Code (AI assistant) on the owner's computer, 2026-09-19 |

The owner was using the same computer during testing, so no step sent operating-system
keystrokes or mouse input, and screenshots capture only the application's own window.

## Results by revision

| Revision | Tests | Skipped | Lint | Content | Native smoke | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `16f3fc3` baseline | 134 passed | 0 | clean | PASS, 24 warnings | passed (10 checks) | P0 defects D-01..D-03 reproduced |
| `525c377` M2 | 158 passed ×3 | 0 | clean | PASS | passed (11 checks) | reproductions no longer reproduce |
| **`4ad1e34` candidate** | **163 passed ×3** | **0** | clean | PASS, 24 warnings all dispositioned | **passed (16 checks), source and installed** | installer validated end to end |

Each test run reported one third-party deprecation warning (Starlette `TestClient`, used
only by the legacy browser tests). On a Linux runner without a display, the six GUI
scenarios in `tests/test_desktop_gui.py` skip by design; on Windows they run. The Windows
CI job and the release workflow have been written but **not yet run on GitHub** (the
repository has no remote yet).

Commands, from a clean checkout of the revision (a `git worktree`; in an ordinary clone on
the `release/1.0` branch, `release-check` reports `.git/refs/heads/release`: defect D-29):

```powershell
python -m pytest -q -rs            # 163 passed
python -m ruff check .             # clean
python scripts/check_curated_content.py
python -m src.cli release-check    # clean
python desktop_app.py --smoke-test <output-folder>
```

## Installer validation (candidate)

Installer `LanguageHangman-1.0.0rc2-Setup.exe`, 14,678,690 bytes, SHA256
`2fc27de78a94aca7c96637dafc70b15ff707349b403c878bfd050ad79a58dc95`, built by
`scripts/build_desktop.ps1` from a clean checkout of `4ad1e34` in a fresh Python 3.12 build
environment. Unsigned. Files: `evidence/…/installer-validation/`.

| # | Check | Result |
| --- | --- | --- |
| 1 | Pre-state: no program, data, Start-menu entry or uninstall registration | Clean |
| 2 | Install 1.0.0rc1 (built from `5a41404`); create learner data with rc1's own code: 2 profiles, 1 win, 1 loss, a session paused mid-round | Done (rc1's UI crashes after sign-in, R-01, so its services created the data) |
| 3 | **Upgrade** by running the rc2 installer over rc1 | Exit 0; learner database byte-identical before/after; installed EXE identical to the build; one `1.0.0rc2` registration |
| 4 | Launch the installed app normally on the upgraded data | Sign-in screen (not recovery) in 1.84 s; rc1 credentials accepted, wrong password rejected; progress 2 rounds; paused session resumes at round 3 with its wrong letter and completes |
| 5 | Installed `--smoke-test` with `PATH` limited to Windows folders and no `PYTHON*` variables | Exit 0; 16/16 checks (below); real data untouched |
| 6 | Import a **v1.0.0-beta** database (schema 0, made by the beta's code) through the Restore/import path; launch installed app | Opens normally; beta credentials and 3 rounds kept; Review offers only shared curated words (`clean` in Hotel, `early` in Airport), refuses Restaurant; legacy-only word kept for history |
| 7 | Corrupt the live database; launch the installed app | **Recovery window** in 0.89 s; restoring the newest automatic backup (the button's code path) quarantined the damaged bytes exactly; normal start afterwards |
| 8 | Uninstall | Program, Start-menu entry and registration removed; all 8 learner data files preserved byte-for-byte |

Steps 4, 6 and 7 verified sign-in and data with the candidate's code (same revision as the
installer) because typing into the installed window would have interfered with the person
using the computer. Signing in through the installed UI is in the manual checks.

### Native smoke journey (16 checks, `src/desktop/smoke.py`)

Registration · Review refused for a new profile, Standard offered · clue after a wrong guess
and resume · three rounds in reports · Review uses only practised words and explains a
shorter session · lost round and abandoned session reported correctly · profile export
without credentials · deleting one profile keeps others · backup and restore · text size
after dropdown screens · guest practice · round resumes after the process is ended mid-round
· learning card and next round resume after the process ends between rounds · damaged
database detected at start-up · backup restored over it with the damaged bytes quarantined
· sign-in and progress after recovery.

It drives the app's own handlers and buttons; it is **not** evidence of keyboard or
screen-reader behaviour.

## Performance (proposed supported history)

Dataset: 5 profiles; one with **5,000 completed rounds** (150 played through the app's
services, then scaled by copying rows with spread dates) and 999 sessions; 5.3 MB.

| Operation | Median | 95th percentile |
| --- | --- | --- |
| Start-up database open + check | 18 ms | 29 ms |
| Full backup (copy + validation) | 125 ms | 134 ms |
| Report aggregation, 5,000 rounds | 57 ms | 67 ms |
| Guess (round continues) | 14 ms | 17 ms |
| Guess completing a round (all writes) | 28 ms | 36 ms |
| Screen change (Home / Reports with 5,000 rows / Practice) | 221–313 ms | ≤ 343 ms |
| Installed-build EXE start to visible window | 0.79 s (1.26 s with the day's first backup) | — |

No optimisation was made: every figure is well below one second and the Reports table with
5,000 rows is no slower than screens without data. The supported history size is a
proposal awaiting the owner's agreement (DELIVERY.md, decision DEC-10).

## Display scaling and window size

Real: 125% on 1920×1080. Emulated with CustomTkinter scaling (not the Windows setting):
100% and 150%. At every scale the window opens inside the screen work area, including the
800×600 minimum with Large text (before D-22 the window was 167 px taller than the screen
at 150%). No control was clipped horizontally; at the minimum size content scrolls. Real
100% and 150% checks remain manual.

## Requirement-to-test traceability

| Req | Requirement | Automated evidence | Native / installed evidence | Result |
| --- | --- | --- | --- | --- |
| RQ-01 | Fresh profile cannot start Review; Standard offered | `test_fresh_profile_cannot_start_review` | smoke; installer step 5 | Pass |
| RQ-02 | Review uses only eligible practised words in the situation; due first; once per session | `test_review_uses_only_practised_words_from_the_situation`, `test_review_plays_due_words_before_words_not_yet_due` | smoke | Pass |
| RQ-03 | Short or exhausted Review queue gives a controlled, explained outcome | `test_review_queue_exhausted_mid_session_ends_with_explanation` | smoke (shortened session) | Pass |
| RQ-04 | Standard practice unaffected | `test_standard_practice_still_works_for_fresh_profile`, `test_supported_journey_and_reports` (18 cases) | smoke | Pass |
| RQ-05 | Curated-only practice after importing legacy data; no fallback bypass; counts curated | `test_imported_legacy_review_items_are_not_offered`, `test_imported_database_practice_uses_curated_words_only` | installer step 6 | Pass |
| RQ-06 | Legacy history and review items preserved | same, plus `test_legacy_upgrade_preserves_data_and_takes_backup` | installer step 6 | Pass |
| RQ-07 | Valid backup restores a corrupt live database; damaged bytes quarantined | `test_valid_backup_restores_a_corrupt_live_database` | smoke; installer step 7 | Pass |
| RQ-08 | Invalid/unsupported backups change nothing | `test_invalid_backup_leaves_a_corrupt_live_database_unchanged` (3), `test_bad_restore_leaves_current_database_unchanged` (3) | — | Pass |
| RQ-09 | No partial replacement on permission/replace failure | `test_replace_failure_keeps_the_original_and_its_side_files`, `test_failures_before_the_switch_leave_data_unchanged` (2) | — | Pass |
| RQ-10 | Recovery reachable when start-up fails | `test_launcher_offers_recovery_when_start_up_fails`, `test_page_corruption_is_detected_at_start_up` | installer step 7 | Pass |
| RQ-11 | Restored credentials, progress and active sessions work | `test_valid_backup_restores_a_corrupt_live_database` | smoke | Pass |
| RQ-12 | Every action atomic; completion counted once | `test_failed_final_guess_rolls_back_everything` (4), `test_completion_retry_survives_process_restart` | — | Pass |
| RQ-13 | Close/reopen recovery during and between rounds | `test_guesses_and_hints_resume`, journey tests | smoke with real process termination (2) | Pass |
| RQ-14 | Correct reports after wins, losses, abandoned sessions | `test_lost_round_and_repeated_guess`, journey tests | smoke | Pass |
| RQ-15 | Backup/restore, export, profile deletion scoped | `test_profile_deletion_export_and_diagnostics_are_scoped`, backup tests | smoke | Pass |
| RQ-16 | Genuine upgrade keeps credentials and progress | `test_legacy_upgrade_preserves_data_and_takes_backup` | installer steps 3–4 and 6 | Pass |
| RQ-17 | Uninstall preserves learner data | — | installer step 8 | Pass |
| RQ-18 | Runs without Python installed | — | installer step 5 (no Python on `PATH`) | Partial — clean account pending |
| RQ-19 | Privacy-safe diagnostics with operation, stage, version | `test_diagnostics_contain_codes_but_no_personal_data` | — | Pass |
| RQ-20 | Backup failure does not block start-up; visible warning | GUI scenario `automatic_backup_failure_does_not_block_start_up` | — | Pass |
| RQ-21 | Keyboard: dropdowns operable, focus visible and in view, text-size shortcuts | GUI scenarios (3) | — | Bindings pass; **real keyboard pending** |
| RQ-22 | Layout at 100/125/150% and minimum size | GUI scenario `window_opens_inside_the_work_area` | emulated scaling screenshots | 125% pass; **100/150% real pending** |
| RQ-23 | Content structurally valid; warnings dispositioned | `scripts/check_curated_content.py` | — | Pass; **educator review pending** |
| RQ-24 | Learner acceptance (5 sessions) | — | — | **Pending** |

## Defect reproduction

Each P0 defect was reproduced on `16f3fc3` before it was changed
(`evidence/2026-09-19-baseline-16f3fc3/defect-repro.txt`) and re-run afterwards
(`evidence/2026-09-19-m2-525c377/defect-repro-after-fix.txt`). D-07 was reproduced the same
way (`repro_d07.py`).

## Test-harness finding (D-26)

In the long-lived pytest process, new Tk windows intermittently failed to read Tcl's own
library files. pytest's output capture swaps the process's standard handles between tests
and Tcl caches them; the failure was reproduced outside pytest by swapping handles the same
way (1/20 window starts) and never with fixed handles (0/75), which is how the shipped app
runs. GUI scenarios now run one per process: 36/36 runs passed versus 60–70% of runs
failing before.

## Not verified here

- A clean Windows account without Python, and a machine other than this one.
- Real keyboard-only use, visible focus by eye, and screen readers.
- Real 100% and 150% Windows display scaling.
- The GitHub Actions workflows (no remote repository yet).
- Educator review of content and learner sessions.
- Code signing (the installer is unsigned).
