# Verification — Language Hangman 1.0.0rc4

What was actually executed, on which revision and artifact, with what result. Manual and
human acceptance gates, and their status, are in [ACCEPTANCE.md](ACCEPTANCE.md). Nothing
here was produced by a learner, an educator or a manual tester.

**Release candidate:** revision `d543579` (branch `release/1.0`); installer
`LanguageHangman-1.0.0rc4-Setup.exe`, SHA256 `abb0cf94428503316b2619add6bd3388b8ca4f3c22bc116e6b90e649e9ebcd3c`. Evidence:
[`evidence/2026-11-01-rc4-d543579/`](evidence/2026-11-01-rc4-d543579/). Commits after
`d543579` change tests, documents and release tooling only: `git diff d543579 -- src
desktop_app.py packaging` is empty, and the one change under `scripts/` is the demo
recorder, which PyInstaller does not bundle. So the installer matches the published source.

The previous candidates' evidence stays in place: rc3 in
[`evidence/2026-09-19-rc3-fd3b25a/`](evidence/2026-09-19-rc3-fd3b25a/), rc2 in
[`evidence/2026-09-19-rc2-4ad1e34/`](evidence/2026-09-19-rc2-4ad1e34/).

## Environment: the build machine, not a clean machine

| Item | Value |
| --- | --- |
| Machine | AMD Ryzen 7 6800H (8 cores/16 threads), 15.2 GB RAM, NVMe SSD |
| OS | Windows 11 Home 10.0.26200, 1920×1080 panel at **125%** display scaling (the real setting) |
| Runtime / build | Python 3.12.1 · CustomTkinter 5.2.2 · Pillow 12.3.0 · PyInstaller 6.11.1 · Inno Setup 6.7.3 |
| Executed by | Claude Code (AI assistant) on the owner's computer, 2026-09-19 (rc2, rc3) and 2026-11-01 (rc4) |

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
| `fd3b25a` rc3 | 174 passed | 0 | clean | PASS, 24 dispositioned | passed (16), source and installed | 1 warning (Starlette, legacy tests only) |
| `d543579` rc4 build commit | **174 passed, 1 failed** in the clean clone | 0 | clean | PASS, 24 dispositioned | passed (16), source and installed | `focused_control_scrolls_into_view` failed; see below. 175 had passed on the uncommitted working tree |
| `f5ac6a2`..`21cee81` | 175 passed on the extracted `21cee81` archive | 0 | clean | PASS | not re-run | the failing scenario now waits for the layout to settle |
| **`7c425fd` rc4 final tree** | **175 passed, 0 skipped, ×3** | **0** | clean | PASS, 24 dispositioned | installer code unchanged since `d543579` | three consecutive runs in a clean clone |

**The failure on the build commit.** `focused_control_scrolls_into_view` failed once in the
clean clone of `d543579`. It is a test scenario, and it failed on a position measured
straight after a resize. Making it wait for the layout to settle was the fix; that the race
was the cause is the likely explanation, not a proven one, because the failure was not
reproduced on demand. The installer's inputs did not change. The original failing output
stays in `checks/pytest.txt`.

On a machine without a display, the nine GUI scenarios skip by design (not run on Linux for
rc4). `test_release_check_on_a_real_release_branch_clone_and_worktree` skips if Git is not
installed. The GitHub workflows have not run: there is no remote repository (G13).

### What was re-run for rc4, and what was carried forward

The interface changed in rc4, so everything that touches it was re-run on `d543579` or its
installer: the suite, the smoke journey from source and from the installed build, the whole
installer sequence, performance, the scaling checks, the demo and the screenshots.

Carried forward without re-running, because neither the code nor the inputs changed: the
D-26 harness investigation, the original D-01..D-03 reproduction scripts (their regression
tests ran again inside the 175), and the rc3 defect reproductions for D-29 to D-31 (their
regression tests also ran again). The v1.0.0-beta database used for the import check was
rebuilt with the beta's own code, because the original was lost with a temporary folder
(incident I-6); it contains the same three words.

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

For rc4, `release-check` was clean in an ordinary clone on `release/1.0`
(`checks/release-check.txt`) and on the extracted source archive (see the release package's
`VERIFICATION-*.txt`). The worktree case last ran for rc3.

## Installer validation (rc4, build machine)

Installer 14,736,907 bytes, SHA256 `abb0cf94428503316b2619add6bd3388b8ca4f3c22bc116e6b90e649e9ebcd3c`, built by `scripts/build_desktop.ps1` in a fresh
clone of `d543579`; installed EXE SHA256
`e6b3c0f910b626036b0df0753481b9b6fe9fd8ca51ab3a3d0cbe9b54df571436`. Unsigned.
Files: `evidence/…/installer-validation/`.

| # | Check | Result |
| --- | --- | --- |
| 1 | Pre-state; install 1.0.0rc3 (`5e1b3107…`) | Nothing installed before; rc3 installed and registered |
| 2 | rc3 creates its own data with rc3's code (`fd3b25a`): 2 profiles, a win, a loss, a round paused mid-guess | Done |
| 3 | **Upgrade**: run the rc4 installer over rc3 | Exit 0; the data file byte-identical; installed EXE identical to the build; one `1.0.0rc4` registration; `LICENSE.txt`, the notices and 12 licence texts beside the program |
| 4 | Third-party notices in the installed folder | 982 files, 13 notice files, **0 problems**; installed `LICENSE.txt` identical to the repository's |
| 5 | Normal launch of installed rc4 on the upgraded data; sign-in and data checked with `d543579` code | Sign-in screen in 1.72 s; rc3 password accepted, wrong one rejected; 2 rounds kept; paused round resumed and completed |
| 6 | Installed `--smoke-test`, `PATH` = Windows folders only, no `PYTHON*` variables | Exit 0; 16/16 in 25 s; real data untouched |
| 7 | Import a v1.0.0-beta database (schema 0) through the restore path | Opens normally; beta sign-in and 3 rounds kept; Review offers only practised curated words (`clean` in Hotel, `early` in Airport, Restaurant refused) |
| 8 | Damage the live data file; launch the installed app, Standard and Large text | **Recovery window** in 0.89–0.94 s; captured at opening and minimum size; text fits at both sizes |
| 9 | Restore the newest automatic backup (the first button's code path) | Damaged bytes quarantined exactly; both profiles back; **no stale side files**; normal start in 0.94 s |
| 10 | Uninstall | Program, Start-menu entry and registration removed; all 8 data files kept byte-for-byte |

A first rc4 installer passed this same sequence before performance measurement rejected the
build (D-32); it was discarded, and every step above was run again on the rebuilt installer
(incident I-7).

## Restore rollback (D-30)

Fault-injection tests in `tests/test_recovery.py`, run in the 174:

| Case | Test | Result |
| --- | --- | --- |
| Second side-file move fails | `test_failed_second_side_file_move_puts_the_first_back` | First file back, bytes identical; "unchanged" is true |
| Replacing the main database fails | `test_failed_database_switch_puts_every_side_file_back` | All three side files back |
| Successful restore | `test_successful_restore_keeps_stale_side_files_out_of_the_restored_data` | No side file next to the restored data; set-aside copies kept; data comes from the backup |
| Putting a file back fails | `test_failed_rollback_says_where_the_side_files_are_kept` | Stage `rollback`; message names each kept file, its original place and the safety copy; no "unchanged" claim |

The first and last fail on the rc2 code (`defects/D-30-restore-rollback.txt`). The installed
build contains the same code (EXE built from `d543579`); its successful restore paths were
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
and the files they cover; `licenses/` holds 13 texts. The build copies them next to the
program and runs `scripts/third_party_notices.py check`: it fails if a shipped file is not
in the inventory, a notice is missing or changed, or the build environment's versions differ
from the inventory. rc4 build folder: 979 files, 0 problems. Installed folder: 982 files, 0
problems.

## Performance (build machine)

Dataset: 5 profiles; one with **5,000+ completed rounds** (150 played through the app's
services, the rest copied rows with spread dates) and 4.55 MB. It was rebuilt for rc4
because the rc3 dataset (5.3 MB) was lost (I-6), so the rc3 column is a guide, not a
like-for-like comparison. The guess-to-redraw row used a fresh profile on both revisions. Measured in-process from
`d543579` while the owner was using the computer (`performance.txt`). Single-machine
observations, not guarantees.

| Operation | Samples | Median | 95th percentile | rc3 median |
| --- | --- | --- | --- | --- |
| Open, upgrade check and quick check | 10 | 12 ms | 15 ms | 15 ms |
| Full backup (copy and validation) | 5 | 102 ms | 123 ms | 128 ms |
| Reports aggregation, 5,000+ rounds | 20 | 55 ms | 74 ms | 65 ms |
| Guess, round continues (service only) | 115 | 13 ms | 29 ms | 13 ms |
| Guess that completes a round (all writes) | 30 | 30 ms | 40 ms | 28 ms |
| **Guess to redrawn screen (the game's hot path)** | 55 | **39 ms** | 606 ms (rc3: 329 ms) | 285 ms |
| Screen change: Home / Reports / Practice setup | 5 each | 354 / 565 / 503 ms | 446 / 585 / 513 ms | 238 / 365 / 317 ms |

Start-up of the built EXE to a visible window, 5 launches on a fresh copy of the dataset:
**1.19 s** for the first launch of the day, which also makes the automatic backup, then
**0.88–0.93 s** (rc3: 1.65 s and 0.78–0.84 s).

Two honest comparisons with rc3:

- **A typical guess is about seven times faster; the round-ending guess is slower.** A
  guess that continues a round now updates the
  board in place instead of rebuilding the screen, and the board is one drawn canvas
  instead of about 55 widgets (D-32). The 95th percentile, 606 ms, is the guess that
  *completes* a round and rebuilds the screen for the learning card. That is slower than
  rc3's 329 ms.
- **Navigation screens are 100–200 ms slower**, because Home, Reports and Practice setup
  now group content into cards and stat tiles, which are more widgets than the plain
  paragraphs they replaced. All stay well under a second.

The redesign was measured only after the first rc4 installer had been built and validated,
which is why that artifact was discarded (incident I-7); the checklist now measures before
building when the interface changed.

## Requirement-to-test traceability

| Req | Requirement | Automated evidence | Native / installed evidence (rc4) | Result |
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
| RQ-22 | Layout at 100/125/150% and minimum size; text wraps to the window (D-31) | GUI `window_opens_inside_the_work_area`, `recovery_window_fits_at_minimum_size`, `main_window_text_wraps_at_minimum_size` | installed at real 125%; `scaling/` (12 captures: round and recovery, three scalings, two text sizes) | 125% pass; 100/150% emulated pass; **real 100/150% pending** (G7) |
| RQ-27 | A letter key guesses that letter, and a used key does nothing | GUI `letter_keys_guess_on_click` | demo; smoke uses the typing route | Pass |
| RQ-28 | A guess redraws the round without rebuilding the screen (D-32) | — | `performance.txt`: 39 ms median, 55 samples | Pass for guesses that continue a round; the round-ending guess still rebuilds |
| RQ-23 | Content structurally valid; warnings dispositioned | `scripts/check_curated_content.py` | — | Pass; **educator review pending** (G9) |
| RQ-24 | Learner acceptance (5 sessions) | — | — | **Pending** (G10) |
| RQ-25 | Third-party notices ship and match what is bundled (T-28) | `tests/test_third_party_notices.py` (3) | build check; step 4 | Pass (build machine) |
| RQ-26 | Release hygiene check ignores Git's data but reports real artifacts (D-29) | `test_release_check_ignores_git_data_but_not_real_artifacts`, `test_release_check_on_a_real_release_branch_clone_and_worktree` | clone, worktree, extracted archive | Pass |

## Defect reproduction

D-01..D-03 and D-07: reproduced on `16f3fc3` before any change
(`evidence/2026-09-19-baseline-16f3fc3/`), re-run after (`evidence/2026-09-19-m2-525c377/`).
D-29, D-30, D-31 and T-28: reproduced on the rc2 code and re-run on `fd3b25a`
(`evidence/2026-09-19-rc3-fd3b25a/defects/`).

## Corrections to earlier records

**The rc4 summary and first record.** The handover and an earlier version of this record
said 175 tests passed on `d543579`; the clean-clone run there was 174 passed, 1 failed. The
archive record also named a commit it had not been run on. Both are corrected (I-8).

**rc3 → rc4.** The redesigned interface made a guess four times slower than rc3 (1.13 s
median against 285 ms). Measurement caught it before release, the board was rewritten, and
the figures above are from the rebuilt artifact. The first rc4 installer was discarded.

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
