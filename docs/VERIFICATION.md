# Verification — Language Hangman 1.0.0rc3

What was actually executed, on which revision and artifact, with what result. Manual and
human acceptance gates, and their status, are in [ACCEPTANCE.md](ACCEPTANCE.md). Nothing
here was produced by a learner, an educator or a manual tester.

**Release candidate:** revision `fd3b25aa93d5b7de1fb7763aaecd5cb5898aa979` (branch
`release/1.0`); installer `LanguageHangman-1.0.0rc3-Setup.exe`, SHA256
`5e1b31077061dabd9cc764e07f8243f3054f526b8b1202181805b17022665f84`. Evidence:
[`evidence/2026-09-19-rc3-fd3b25a/`](evidence/2026-09-19-rc3-fd3b25a/).

## Environment: the build machine, not a clean machine

| Item | Value |
| --- | --- |
| Machine | AMD Ryzen 7 6800H (8 cores/16 threads), 15.2 GB RAM, NVMe SSD |
| OS | Windows 11 Home 10.0.26200, 1920×1080 panel at **125%** display scaling (the real setting) |
| Runtime / build | Python 3.12.1 · CustomTkinter 5.2.2 · Pillow 12.3.0 · PyInstaller 6.11.1 · Inno Setup 6.7.3 |
| Executed by | Claude Code (AI assistant) on the owner's computer, 2026-09-19 |

This is the development and build machine: Python, the build tools and earlier versions of
the app have all been on it. Installer results below are **build-machine** results. A clean
Windows account without Python (G5) has not been tested. The owner was using the computer
throughout, so no step sent operating-system keystrokes or mouse input, and screenshots
capture only the application's own window.

## Kinds of evidence

| Label | Meaning | What it is not |
| --- | --- | --- |
| Automated | pytest: service tests, fault-injection tests and GUI scenarios. GUI scenarios open real windows and call the app's own handlers, bindings and Tk's focus traversal | Not real key presses, not visible focus judged by eye |
| Smoke journey | `--smoke-test`: 16 scripted checks in a real window, from source or the installed EXE | Same limits as above |
| Installed build | The real installer on the build machine; the installed EXE launched normally | Not a clean machine; sign-in was checked with code of the same revision, not typed |
| Real / emulated scaling | 125% is the machine's real setting; 100% and 150% are emulated with CustomTkinter's scaling | Emulation is not the Windows setting |
| Manual | A person using the installed app | **None performed yet** (ACCEPTANCE.md M1–M4) |

## Results by revision

| Revision | Tests | Skipped | Lint | Content | Smoke journey | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `16f3fc3` baseline | 134 passed | 0 | clean | PASS, 24 warnings | passed (10 checks) | P0 defects D-01..D-03 reproduced |
| `525c377` M2 | 158 passed ×3 | 0 | clean | PASS | passed (11 checks) | reproductions no longer reproduce |
| `4ad1e34` rc2 | 163 passed ×3 | 0 | clean | PASS, 24 dispositioned | passed (16), source and installed | independent review on Linux: 157 passed, 6 GUI skipped, 1 warning (reported to the owner; not run here) |
| **`fd3b25a` rc3** | **174 passed** | **0** | clean | PASS, 24 dispositioned | **passed (16), source and installed** | run in a fresh worktree; 1 warning (Starlette, legacy tests only) |

On a machine without a display, the eight GUI scenarios skip by design (not run on Linux for
rc3). `test_release_check_on_a_real_release_branch_clone_and_worktree` skips if Git is not
installed. The GitHub workflows have not run: there is no remote repository (G13).

### What was re-run for rc3, and what was carried forward

Everything listed under rc3 below was run on `fd3b25a` or its installer. Carried forward
without re-running: the D-26 harness investigation (the harness did not change) and the
original D-01..D-03 reproduction scripts (their regression tests ran again in the 174).

## Verification sequence

Run `release-check` **first**, on an untouched checkout: running Python or pytest creates
`__pycache__` folders and test caches, which `release-check` correctly reports as files that
must not be distributed. They are never in the source archive, because the archive is made
with `git archive` from the commit.

```powershell
git clone -b release/1.0 <repository> hangman-check   # or: git worktree add ... <commit>
cd hangman-check
$env:PYTHONDONTWRITEBYTECODE = "1"; python -m src.cli release-check; Remove-Item Env:\PYTHONDONTWRITEBYTECODE
python -m ruff check .
python scripts/check_curated_content.py
python -m pytest -rs            # read pytest's own exit code
python desktop_app.py --smoke-test <output-folder>
```

For rc3, `release-check` was clean in a worktree and in an ordinary clone on `release/1.0`
(`checks/release-check-worktree-and-clone.txt`), and on the extracted source archive (see the
release package's `VERIFICATION-*.txt`).

## Installer validation (rc3, build machine)

Installer 14,717,048 bytes, SHA256 `5e1b3107…665f84`, built by `scripts/build_desktop.ps1` in
a fresh clone of `fd3b25a`; installed EXE SHA256 `87b319ec…6f5f`. Unsigned.
Files: `evidence/…/installer-validation/`.

| # | Check | Result |
| --- | --- | --- |
| 1 | Pre-state; install 1.0.0rc2 (`2fc27de7…`) | Nothing installed before; rc2 installed and registered |
| 2 | rc2 creates its own data: first normal launch of the installed rc2 app, then 2 profiles, a win, a loss and a paused round with rc2's code (`4ad1e34`) | Done |
| 3 | **Upgrade**: run the rc3 installer over rc2 | Exit 0; all 4 data files byte-identical; installed EXE identical to the build; one `1.0.0rc3` registration |
| 4 | Third-party notices in the installed folder (`third_party_notices.py check --installed`) | 980 files, 12 notice files, **0 problems** |
| 5 | Normal launch of installed rc3 on the upgraded data; sign-in and data checked with `fd3b25a` code | Sign-in screen in 1.73 s; rc2 password accepted, wrong one rejected; 2 rounds kept; paused round resumes and completes |
| 6 | Installed `--smoke-test`, `PATH` = Windows folders only, no `PYTHON*` variables | Exit 0; 16/16; real data untouched |
| 7 | Import a v1.0.0-beta database (schema 0) through the restore path | Opens normally; beta sign-in and 3 rounds kept; Review offers only practised curated words |
| 8 | Damage the live data file; launch the installed app normally, Standard and Large text | **Recovery window** in 0.90–0.99 s; captured at opening and minimum size: text wraps inside the window at real 125% |
| 9 | Restore the newest automatic backup (the first button's code path) | Damaged bytes quarantined exactly; profiles back; no side files left; normal start in 0.94 s |
| 10 | Uninstall | Program, Start-menu entry and registration removed; all 8 data files kept byte-for-byte |

Installed screenshots are captured by a DPI-aware helper (rc2's were cropped: incident I-4).

## Restore rollback (D-30)

Fault-injection tests in `tests/test_recovery.py`, run in the 174:

| Case | Test | Result |
| --- | --- | --- |
| Second side-file move fails | `test_failed_second_side_file_move_puts_the_first_back` | First file back, bytes identical; "unchanged" is true |
| Replacing the main database fails | `test_failed_database_switch_puts_every_side_file_back` | All three side files back |
| Successful restore | `test_successful_restore_keeps_stale_side_files_out_of_the_restored_data` | No side file next to the restored data; set-aside copies kept; data comes from the backup |
| Putting a file back fails | `test_failed_rollback_says_where_the_side_files_are_kept` | Stage `rollback`; message names each kept file, its original place and the safety copy; no "unchanged" claim |

The first and last fail on the rc2 code (`defects/D-30-restore-rollback.txt`). The installed
build contains the same code (EXE built from `fd3b25a`); its successful restore paths were
exercised in steps 7 and 9. Failures cannot be injected into the installed build.

## Recovery window and text wrapping (D-31)

| Check | How | Scaling | Result |
| --- | --- | --- | --- |
| Automated: recovery window at minimum size | Each label's needed width ≤ its width; controls inside the view; each action scrolls into view; Tk's Tab traversal reaches all 6 actions; Escape bound | real 125% (Standard, Large) and emulated 150% (Large) | Pass; fails on rc2 views |
| Automated: main window at minimum size | Same width checks on Home, Practice, Settings, Help | as above | Pass; fails on rc2 (10 px at Large) |
| Source, minimum size, 6 combinations | Same measurement plus screenshots | emulated 100%, real 125%, emulated 150% × Standard, Large | 12/12 fit (`scaling/`) |
| Installed build | Normal launch on damaged data; resized to minimum with `SetWindowPos` (no input) | real 125%, Standard and Large | Wraps inside the window (`installer-validation/installed-recovery-*.png`) |
| Real 100% and 150%; real keyboard; vertical scrolling by a person | — | — | **Not performed** (M2, M3, M4) |

## Third-party notices (T-28)

`packaging/third-party/THIRD-PARTY-NOTICES.txt` lists 15 components with versions, licences
and the files they cover; `licenses/` holds 12 texts. The build copies them next to the
program and runs `scripts/third_party_notices.py check`: it fails if a shipped file is not
in the inventory, a notice is missing or changed, or the build environment's versions differ
from the inventory. rc3 build folder: 978 files, 0 problems. Installed folder: 980 files, 0
problems. The rc2 program folder fails the same check (12 notices missing).

## Performance (build machine)

Dataset: 5 profiles; one with **5,000 completed rounds** (150 played through the app's
services, then scaled by copying rows with spread dates) and 999 sessions; 5.3 MB. Measured
in-process from `fd3b25a` while the owner was using the computer (`performance.txt`).

| Operation | Samples | Median | 95th percentile | Max |
| --- | --- | --- | --- | --- |
| Open, upgrade check and quick check | 10 | 15 ms | 25 ms | 25 ms |
| Full backup (copy and validation) | 5 | 128 ms | 131 ms | 131 ms |
| Reports aggregation, 5,000 rounds | 20 | 65 ms | 79 ms | 81 ms |
| Guess, round continues | 123 | 13 ms | 21 ms | 177 ms |
| Guess that completes a round (all writes) | 30 | 28 ms | 36 ms | 48 ms |
| Screen change: Home / Reports (5,000 rows) / Practice | 5 each | 238 / 365 / 317 ms | 323 / 386 / 341 ms | — |

Start-up of the built EXE to a visible window, 5 launches on a fresh copy of the dataset:
**1.65 s** for the first launch of the day, which makes the day's automatic backup (and was
the new EXE's first run), then **0.78–0.84 s**. rc2 measured 1.26 s and 0.75–0.79 s the same
way. These are single-machine figures, not guarantees; the supported history size is a
proposal awaiting the owner (DEC-10).

## Requirement-to-test traceability

| Req | Requirement | Automated evidence | Native / installed evidence (rc3) | Result |
| --- | --- | --- | --- | --- |
| RQ-01 | Fresh profile cannot start Review; Standard offered | `test_fresh_profile_cannot_start_review` | smoke; step 6 | Pass |
| RQ-02 | Review uses only eligible practised words in the situation; due first; once per session | `test_review_uses_only_practised_words_from_the_situation`, `test_review_plays_due_words_before_words_not_yet_due` | smoke | Pass (rule pending owner, DEC-06) |
| RQ-03 | Short or exhausted Review queue gives a controlled, explained outcome | `test_review_queue_exhausted_mid_session_ends_with_explanation` | smoke | Pass |
| RQ-04 | Standard practice unaffected | `test_standard_practice_still_works_for_fresh_profile`, journey tests | smoke | Pass |
| RQ-05 | Curated-only practice after importing legacy data | `test_imported_legacy_review_items_are_not_offered`, `test_imported_database_practice_uses_curated_words_only` | step 7 | Pass |
| RQ-06 | Legacy history and review items preserved | same, plus `test_legacy_upgrade_preserves_data_and_takes_backup` | step 7 | Pass |
| RQ-07 | Valid backup restores a corrupt live database; damaged bytes quarantined | `test_valid_backup_restores_a_corrupt_live_database` | smoke; steps 8–9 | Pass |
| RQ-08 | Invalid or unsupported backups change nothing | `test_invalid_backup_leaves_a_corrupt_live_database_unchanged` (3), `test_bad_restore_leaves_current_database_unchanged` (3) | — | Pass |
| RQ-09 | No partial replacement; every moved side file put back; failed put-back reported with locations (D-30) | four D-30 tests above, `test_replace_failure_keeps_the_original_and_its_side_files`, `test_failures_before_the_switch_leave_data_unchanged` (2) | — (cannot inject faults into the installed build) | Pass |
| RQ-10 | Recovery reachable when start-up fails | `test_launcher_offers_recovery_when_start_up_fails`, `test_page_corruption_is_detected_at_start_up` | step 8 | Pass |
| RQ-11 | Restored credentials, progress and sessions work; stale side files not replayed | `test_valid_backup_restores_a_corrupt_live_database`, `test_successful_restore_keeps_stale_side_files_out_of_the_restored_data` | smoke; step 9 | Pass |
| RQ-12 | Every action atomic; completion counted once | `test_failed_final_guess_rolls_back_everything` (4), `test_completion_retry_survives_process_restart` | — | Pass |
| RQ-13 | Close and reopen during and between rounds | `test_guesses_and_hints_resume`, journey tests | smoke, real process termination (2) | Pass |
| RQ-14 | Correct reports after wins, losses, abandoned sessions | `test_lost_round_and_repeated_guess`, journey tests | smoke | Pass |
| RQ-15 | Backup/restore, export, profile deletion scoped | `test_profile_deletion_export_and_diagnostics_are_scoped`, backup tests | smoke | Pass |
| RQ-16 | Genuine upgrade keeps credentials and progress | `test_legacy_upgrade_preserves_data_and_takes_backup` | steps 2–5 (data made by rc2) | Pass |
| RQ-17 | Uninstall preserves learner data | — | step 10 | Pass |
| RQ-18 | Runs without Python installed | — | step 6 (no Python on `PATH`) | Partial: clean machine pending (G5) |
| RQ-19 | Privacy-safe diagnostics with operation, stage, version | `test_diagnostics_contain_codes_but_no_personal_data` | — | Pass |
| RQ-20 | Backup failure does not block start-up; visible warning | GUI `automatic_backup_failure_does_not_block_start_up` | — | Pass |
| RQ-21 | Keyboard: dropdowns operable, focus visible and in view, text-size shortcuts; recovery actions reachable by Tab | GUI scenarios (4) | — | Handler level pass; **real keyboard pending** (G6) |
| RQ-22 | Layout at 100/125/150% and minimum size; text wraps to the window (D-31) | GUI `window_opens_inside_the_work_area`, `recovery_window_fits_at_minimum_size`, `main_window_text_wraps_at_minimum_size` | installed at real 125%; `scaling/` | 125% pass; 100/150% emulated pass; **real 100/150% pending** (G7) |
| RQ-23 | Content structurally valid; warnings dispositioned | `scripts/check_curated_content.py` | — | Pass; **educator review pending** (G9) |
| RQ-24 | Learner acceptance (5 sessions) | — | — | **Pending** (G10) |
| RQ-25 | Third-party notices ship and match what is bundled (T-28) | `tests/test_third_party_notices.py` (3) | build check; step 4 | Pass (build machine) |
| RQ-26 | Release hygiene check ignores Git's data but reports real artifacts (D-29) | `test_release_check_ignores_git_data_but_not_real_artifacts`, `test_release_check_on_a_real_release_branch_clone_and_worktree` | clone, worktree, extracted archive | Pass |

## Defect reproduction

D-01..D-03 and D-07: reproduced on `16f3fc3` before any change
(`evidence/2026-09-19-baseline-16f3fc3/`), re-run after (`evidence/2026-09-19-m2-525c377/`).
D-29, D-30, D-31 and T-28: reproduced on the rc2 code and re-run on `fd3b25a`
(`evidence/2026-09-19-rc3-fd3b25a/defects/`).

## Corrections to the rc2 record

- rc2 said no control was clipped horizontally at emulated scalings. That was judged from
  screenshots. Measurement in rc3 showed Practice-page text clipped by 10 px at the minimum
  size with Large text, and the recovery instructions clipped whenever the window was
  narrower than its default. Fixed in rc3 (D-31).
- The rc2 installed-app screenshots, including the README's recovery image, were cropped by
  the capture helper, not by the app (I-4). The rc2 evidence folder carries a note.
- rc2 said every operation took under one second. Start-up with the day's first automatic
  backup took 1.26 s. The figures above replace that claim.

## Test-harness finding (D-26)

In the long-lived pytest process, new Tk windows intermittently failed to read Tcl's own
library files. pytest's output capture swaps the process's standard handles between tests
and Tcl caches them; the failure was reproduced outside pytest by swapping handles the same
way (1/20 window starts) and never with fixed handles (0/75), which is how the shipped app
runs. GUI scenarios run one per process: 36/36 runs passed versus 60–70% of runs failing
before.

## Not verified here

- A clean Windows account without Python, and any machine other than the build machine.
- Real keyboard-only use, visible focus judged by eye, screen readers.
- Real 100% and 150% Windows display scaling (only emulated).
- Failure injection in the installed build (covered by automated tests on the same code).
- Windows 10.
- The GitHub Actions workflows (no remote repository).
- Educator review of the content; learner sessions.
- Code signing (the installer is unsigned).
