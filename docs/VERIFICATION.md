# Verification — Language Hangman 1.0.0rc6

What was actually executed, on which revision and artifact, with what result. Manual and
human acceptance gates, and their status, are in [ACCEPTANCE.md](ACCEPTANCE.md). Nothing
here was produced by a learner, an educator or a manual tester, and **nothing here checks
that the words or their clues are correct**.

**Release candidate:** revision `e0aa9c0` (branch `release/1.0`); installer
`LanguageHangman-1.0.0rc6-Setup.exe`, SHA256 `32f4b0f0612d37ecc9e135b834f49f3769100adf5ff70fcbadfe7f14524f6ff7`. Evidence:
[`evidence/2026-11-01-rc6-e0aa9c0/`](evidence/2026-11-01-rc6-e0aa9c0/). Commits after
`e0aa9c0` change documents and evidence only: `git diff e0aa9c0 -- src desktop_app.py packaging`
is empty. So the installer matches the published source.

The previous candidates' evidence stays in place: rc5 in
[`evidence/2026-11-01-rc5-f2bb6b9/`](evidence/2026-11-01-rc5-f2bb6b9/), rc4 in
[`evidence/2026-11-01-rc4-d543579/`](evidence/2026-11-01-rc4-d543579/), rc3 in
[`evidence/2026-09-19-rc3-fd3b25a/`](evidence/2026-09-19-rc3-fd3b25a/), rc2 in
[`evidence/2026-09-19-rc2-4ad1e34/`](evidence/2026-09-19-rc2-4ad1e34/).

## Environment: the build machine, not a clean machine

| Item | Value |
| --- | --- |
| Machine | AMD Ryzen 7 6800H (8 cores/16 threads), 15.2 GB RAM, NVMe SSD |
| OS | Windows 11 Home 10.0.26200, 1920×1080 panel at **125%** display scaling (the real setting) |
| Runtime / build | Python 3.12.1 · CustomTkinter 5.2.2 · Pillow 12.3.0 · PyInstaller 6.11.1 · Inno Setup 6.7.3 |
| Executed by | Claude Code (AI assistant) on the owner's computer, 2026-09-19 (rc2, rc3) and 2026-11-01 (rc4, rc5, rc6) |

This is the development and build machine: Python, the build tools and earlier versions of
the app have all been on it. Installer results below are **build-machine** results. A clean
Windows account without Python (G5) has not been tested. The owner was using the computer
throughout, so no step sent operating-system keystrokes or mouse input, and screenshots
capture only the application's own window.

For rc6 the owner had rc5 installed. With their agreement it was replaced, and every step ran
in a separate data folder set with `LANGUAGE_HANGMAN_DATA_DIR`. The hashes of their 4 data files
are unchanged from before validation to after the demo, and rc6 was left installed with their
desktop shortcut. rc6 has not yet been started on their real data.

## Kinds of evidence

| Label | Meaning | What it is not |
| --- | --- | --- |
| Automated | pytest: service tests, fault-injection tests and GUI scenarios. GUI scenarios open real windows and call the app's own handlers, bindings and Tk's focus traversal | Not real key presses, not visible focus judged by eye |
| Smoke journey | `--smoke-test`: 17 scripted checks in a real window, from source or the installed EXE | Same limits as above |
| Installed build | The real installer on the build machine; the installed EXE launched normally | Not a clean machine; sign-in was checked with code of the same revision, not typed |
| Real / emulated scaling | 125% is the machine's real setting; 100% and 150% are emulated with CustomTkinter's scaling | Emulation is not the Windows setting |
| Content check | `scripts/check_curated_content.py`: structure of the word lists | Says nothing about whether a word or clue is correct |
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
| `7c425fd` rc4 final tree | 175 passed, 0 skipped, ×3 | 0 | clean | PASS, 24 dispositioned | installer code unchanged since `d543579` | three consecutive runs in a clean clone |
| `f2bb6b9` rc5 build commit | 194 passed in the clean clone; first run 193 passed, 1 failed (below) | 0 | clean | PASS, 24 dispositioned; 1,538 level-list words structurally valid | passed (17), source and installed | 19 new tests. Five new GUI scenarios were written but not yet in the runner's list (I-11) |
| `1c2eb39` rc5 final tree | 199 passed, 0 skipped, ×3; an earlier set of three was 199, 199, then 198 passed, 1 failed (below) | 0 | clean | PASS, 24 dispositioned; 1,538 level-list words structurally valid | passed (17) from source; installer code unchanged since `f2bb6b9` | three consecutive runs in a clean clone, each exit 0 |
| `2bfbd61` rc6 first candidate | **210 passed, 1 failed** in the clean clone | 0 | clean | PASS, 1,544 words structurally valid | passed (17) from source | `letter_keys_guess_on_click` failed, which exposed D-33 (below). Not built |
| `d7cac11` rc6 second candidate | 212 passed in the clean clone | 0 | clean | PASS, 1,544 words structurally valid | passed (17) from source | D-33 fixed, but a typical guess measured slower. Not built |
| **`e0aa9c0` rc6 build commit** | **212 passed** in the clean clone | **0** | clean | PASS, 1,544 words structurally valid | passed (17), source and installed | equal columns; the installer was built from this commit |

**The failure on rc6's first candidate.** `letter_keys_guess_on_click` failed in the clean clone
of `2bfbd61` with "a used key fired again": the click had landed on a different key. This was a
real defect, not test noise (D-33). The two columns of the round screen took their width partly
from their content, so a long feedback line narrowed the board. Across the 40 lines the board
took four widths, and the A key's left edge moved from 94 to 64 px; with fixed columns it has
one (`d33-board-moves.txt`). The scenario had passed before only because of which random lines
appeared, and the long lines came back in rc5, so rc5 has this defect too. A new GUI scenario
tries all 40 lines.

**Why the columns became equal.** The first fix, `d7cac11`, kept the 3:2 proportions and passed
every check, but measuring before building showed a typical guess at 56–71 ms against rc5's
35–48 ms in that session (`performance/second-candidate-d7cac11/`). A diagnosis on the same code
pointed at text wrapping: 52–55 ms with the real lines at 3:2, 26–28 ms with lines too short to
wrap, and 27–30 ms with the real lines at 1:1 (`d33-columns-diagnosis.txt`, nine runs). So
`e0aa9c0` made the columns equal. That re-run came after validation, so those three rows compare
only with each other.

**The failure on rc5's final tree.** In the first set of three runs on `1c2eb39`, run 3 failed
`main_window_text_wraps_at_minimum_size` with "application has been destroyed". The window
had gone before the test finished: it was not a layout failure. In that scenario only the
app's close handler can destroy the window, and the test had not reached its own cleanup, so
something probably closed the window from outside; test windows open on the owner's desktop
while they use the computer. That is the likely explanation, not a proven one, because it
was not reproduced. The scenario then passed 10 of 10 on its own and a second set of three
full runs passed (I-12). The failing output stays in `checks-final-first-set/`.

**Five GUI scenarios missed the build-commit run.** The new scenarios existed at `f2bb6b9`,
but `tests/test_desktop_gui.py` lists scenarios by name and they were not added, so the 194
did not include them. An arithmetic check of the totals caught this. All five then passed
on the same application code, and they are in the final-tree runs (I-11).

**The first clean run of the rc5 build commit.** `test_release_check_on_a_real_release_branch_clone_and_worktree`
failed once: the check script had set `TEMP` to the long scratch folder, and the test's own
`git init` failed there on Windows' path limit ("cannot stat"). The same commit then passed all
194 with the system temp folder, which shows the script as the cause (I-10). The output is kept
in `checks-first-run/`.

**The failure on the rc4 build commit.** `focused_control_scrolls_into_view` failed once in the
clean clone of `d543579`. It is a test scenario, and it failed on a position measured
straight after a resize. Making it wait for the layout to settle was the fix; that the race
was the cause is the likely explanation, not a proven one, because the failure was not
reproduced on demand. The installer's inputs did not change. The original failing output
stays in the rc4 folder's `checks/pytest.txt`.

On a machine without a display, the 15 GUI scenarios skip by design (not run on Linux for
rc6). `test_release_check_on_a_real_release_branch_clone_and_worktree` skips if Git is not
installed. The GitHub workflows have not run: there is no remote repository (G13).

### What was re-run for rc6, and what was carried forward

The practice flow, the board, the screens, the word data and the session rules changed in rc6,
so everything was re-run on `e0aa9c0` or its installer: the suite, the smoke journey from source
and from the installed build, the whole installer sequence, performance, the scaling checks, the
demo, the screenshots and the word conversion (0 files changed by re-running it).

Carried forward without re-running, because neither the code nor the inputs changed: the D-26
harness investigation, the original D-01..D-03 reproduction scripts (their regression tests ran
again inside the 212), and the rc3 defect reproductions for D-29 to D-31 (their regression tests
also ran again). The v1.0.0-beta database for the import check is the file rebuilt for rc4 with
the beta's own code (SHA256 `a512e245…`); the original was lost (I-6).

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

For rc6, `release-check` was clean in an ordinary clone of `e0aa9c0`
(`checks/release-check.txt`) and on the extracted source archive (see the release package's
`VERIFICATION-*.txt`). The worktree case runs inside the suite.

## Installer validation (rc6, build machine)

Installer 14,785,343 bytes, SHA256 `32f4b0f0612d37ecc9e135b834f49f3769100adf5ff70fcbadfe7f14524f6ff7`, built by `scripts/build_desktop.ps1` in a fresh
clone of `e0aa9c0`; installed EXE SHA256
`c0df9ef049e8d828b52bdbbc93636f8ff303ec86a0948021b56b9ceee3968a9d`. Unsigned.
Files: `evidence/…/installer-validation/`.

| # | Check | Result |
| --- | --- | --- |
| 1 | The owner's rc5 uninstalled; pre-state; install 1.0.0rc5 (`a94a9269…`) | Nothing installed before; rc5 installed and registered |
| 2 | rc5 creates its own data with rc5's code (`f2bb6b9`): 2 profiles, a win, a loss, a Restaurant round paused mid-guess | Done |
| 3 | **Upgrade**: run the rc6 installer over rc5 | Exit 0; the data file byte-identical; installed EXE identical to the build; one `1.0.0rc6` registration; `LICENSE.txt`, the notices and 12 licence texts beside the program; all four word lists installed. **One problem: rc5's travel cards file stayed in the program folder (D-34)** |
| 4 | Third-party notices in the installed folder | 986 files, 13 notice files, **0 problems**; installed `LICENSE.txt` identical to the repository's. A fresh install has 985, because it lacks D-34's file |
| 5 | Normal launch of installed rc6 on the upgraded data; sign-in and data checked with `e0aa9c0` code | Sign-in screen in 2.36 s, including the first word load; rc5 password accepted, wrong one rejected; 2 rounds kept; the paused travel round resumed and completed |
| 6 | Installed `--smoke-test`, `PATH` = Windows folders only, no `PYTHON*` variables | Exit 0; 17/17 in 25 s, including a German list on the A–Z keys, with D-34's file present; validation data untouched |
| 7 | Import a v1.0.0-beta database (schema 0) through the restore path | Opens normally in 1.09 s; beta sign-in and 3 rounds kept; Review my words offers only practised words at that level (`clean`, `small` and `early` at Beginner; Novice refused) |
| 8 | Damage the live data file; launch the installed app, Standard and Large text | **Recovery window** in 0.88 s; captured at opening and minimum size; text fits at both sizes |
| 9 | Restore the newest automatic backup (the first button's code path) | Damaged bytes quarantined exactly; both profiles back; **no stale side files**; normal start in 0.99 s |
| 10 | Uninstall | Program, Start-menu entry and registration removed, including D-34's file; all 7 data files kept byte-for-byte |

The final install used the desktop-shortcut option, because rc5's validation had shown that
uninstalling removes the shortcut. The shortcut was checked afterwards, along with the owner's
data and the installed EXE (`11-after-validation.txt`).

## Restore rollback (D-30)

Fault-injection tests in `tests/test_recovery.py`, run in the 212:

| Case | Test | Result |
| --- | --- | --- |
| Second side-file move fails | `test_failed_second_side_file_move_puts_the_first_back` | First file back, bytes identical; "unchanged" is true |
| Replacing the main database fails | `test_failed_database_switch_puts_every_side_file_back` | All three side files back |
| Successful restore | `test_successful_restore_keeps_stale_side_files_out_of_the_restored_data` | No side file next to the restored data; set-aside copies kept; data comes from the backup |
| Putting a file back fails | `test_failed_rollback_says_where_the_side_files_are_kept` | Stage `rollback`; message names each kept file, its original place and the safety copy; no "unchanged" claim |

The first and last fail on the rc2 code (`defects/D-30-restore-rollback.txt`). The installed
build contains the same code (EXE built from `e0aa9c0`); its successful restore paths were
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
from the inventory. rc6 build folder: 982 files, 0 problems. Upgraded installed folder: 986
files, 0 problems. Fresh install: 985 files, 0 problems.

## Performance (build machine)

rc6 and rc5 were measured in one session on 2026-11-01 from clean clones of `e0aa9c0` and
`f2bb6b9`, with the same tool and interpreter and with the revisions alternating
(`performance/`). The owner was using the computer. These are single-machine observations,
not guarantees.

**Guess to redrawn screen, the game's hot path** (a fresh profile; three runs of each; correct
guesses only, about one in five of which ends a round). Sample counts differ because plain
letters leave fewer distinct letters to guess in Spanish and German, and English has six more
words:

| Words | Samples per run | Median | 95th percentile | Longest guess |
| --- | --- | --- | --- | --- |
| rc5, English Beginner | 46 | 34 / 36 / 41 ms | 452 / 570 / 600 ms | 675 ms |
| **rc6, English Beginner** | 48 | **32 / 33 / 41 ms** | **430 / 539 / 541 ms** | 604 ms |
| rc5, Spanish Beginner | 59 | 34 / 35 / 36 ms | 570 / 573 / 608 ms | 761 ms |
| **rc6, Spanish Beginner** | 59 | **33 / 41 / 45 ms** | **520 / 538 / 553 ms** | 647 ms |
| rc5, German Expert | 110 | 35 / 36 / 39 ms | 547 / 563 / 564 ms | 687 ms |
| **rc6, German Expert** | 102 | **34 / 36 / 43 ms** | **511 / 523 / 528 ms** | 647 ms |

The round-ending guess, which sets the 95th percentile, is faster in every list. The typical
guess is level rather than faster: two of three Spanish runs had a higher median than any rc5
Spanish run, by 5–9 ms, and the cause has not been measured (G16).

**One long session** (rc6 only, one All words session of 200 rounds; rc5 has no endless session):

| Guess | Rounds | Samples | Median | 95th percentile | Longest guess |
| --- | --- | --- | --- | --- | --- |
| Round continues | first 20 | 60 | 32 ms | 86 ms | 890 ms |
| Round continues | last 20 | 94 | 34 ms | 98 ms | 112 ms |
| Ends a round | first 20 | 20 | 518 ms | 609 ms | 610 ms |
| Ends a round | last 20 | 20 | 483 ms | 509 ms | 539 ms |

The saved session held no review records after 200 rounds, so it does not grow with play.

**Other operations** (5 profiles, one with 5,000+ completed rounds, 5.57 MB; both columns from the
same day, one after the other):

| Operation | Samples | rc6 median | rc6 95th percentile | rc5 median | rc5 95th percentile |
| --- | --- | --- | --- | --- | --- |
| Open, upgrade check and quick check | 10 | 17 ms | 20 ms | 17 ms | 19 ms |
| Full backup (copy and validation) | 5 | 126 ms | 136 ms | 173 ms | 183 ms |
| Reports aggregation, 5,000+ rounds | 20 | 59 ms | 73 ms | 61 ms | 95 ms |
| Guess, round continues (service only) | 86 | 14 ms | 19 ms | 15 ms | 19 ms |
| Guess that completes a round (all writes) | 30 | 77 ms | 92 ms | 74 ms | 89 ms |
| Screen change: Home / Reports / Practice setup | 5 each | 451 / 710 / 606 ms | 579 / 779 / 634 ms | 570 / 883 / 951 ms | 767 / 957 / 963 ms |

**Start-up of the installed EXE to a visible window**, 5 launches on a fresh copy of the dataset:
1.08–1.09 s, and 2.06 s for the first launch, which also loads the words for the first time and
makes the day's automatic backup. rc5 measured 1.03–1.04 s and 2.06 s, in a different session.

Three honest comparisons:

- **Sessions differ more than versions do.** rc5's Spanish Beginner median was 53–127 ms in its
  own record, and 34–36 ms here. Part of that is the corrected tool (I-13). Compare only within a
  session.
- **The screen rows are small samples**, five each, so treat the differences as indications.
- **Against rc3**, a typical guess is much faster and a round-ending guess slower. That is rc4's
  trade-off, and rc6 keeps it. Navigation is slower than rc3, because screens group content into
  cards.

### rc3 and rc4, earlier the same day (I-9)

rc3's `performance.txt` has no guess-to-redraw line and rc4's records only rc4's result, so
rc3's 285 ms and 329 ms have no raw record; none was found in the evidence or in the temporary
files left from the rc4 work. Both revisions were therefore measured again in one session
(`evidence/2026-11-01-rc4-d543579/guess-redraw-remeasure.txt`):

| Revision | Median (three runs) | 95th percentile (three runs) | Longest guess |
| --- | --- | --- | --- |
| rc3 `fd3b25a` | 273 / 342 / 349 ms | 330 / 385 / 407 ms | 634 ms |
| rc4 `d543579` | 44 / 50 / 56 ms | 763 / 774 / 789 ms | 1,146 ms |

rc3's recorded figures are plausible but still have no raw record. The 1.13 s from the
discarded first rc4 build has none either, so "four times slower" cannot be confirmed.

## Requirement-to-test traceability

| Req | Requirement | Automated evidence | Native / installed evidence (rc6) | Result |
| --- | --- | --- | --- | --- |
| RQ-01 | Fresh profile cannot start Review my words; All words offered | `test_fresh_profile_cannot_start_review` | smoke; step 6 | Pass |
| RQ-02 | Review uses only eligible practised words at the level; due first; once per session | `test_review_uses_only_practised_words_from_the_level`, `test_review_from_the_app_plays_every_eligible_word_once_with_no_notice`, `test_review_plays_due_words_before_words_not_yet_due` | smoke | Pass (rule pending owner, DEC-06) |
| RQ-03 | Short or exhausted Review queue gives a controlled, explained outcome | `test_review_queue_exhausted_mid_session_ends_with_explanation` | smoke | Pass |
| RQ-04 | All words works for a fresh profile | `test_standard_practice_still_works_for_fresh_profile`, journey tests | smoke | Pass |
| RQ-05 | Word lists only in practice after importing legacy data | `test_imported_legacy_review_items_are_not_offered`, `test_imported_database_practice_uses_word_lists_only` | step 7 | Pass |
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
| RQ-16 | Genuine upgrade keeps credentials and progress | `test_legacy_upgrade_preserves_data_and_takes_backup` | steps 2–5 (data made by rc5) | Pass |
| RQ-17 | Uninstall preserves learner data | — | step 10 | Pass |
| RQ-18 | Runs without Python installed | — | step 6 (no Python on `PATH`) | Partial: clean machine pending (G5) |
| RQ-19 | Privacy-safe diagnostics with operation, stage, version | `test_diagnostics_contain_codes_but_no_personal_data` | — | Pass |
| RQ-20 | Backup failure does not block start-up; visible warning | GUI `automatic_backup_failure_does_not_block_start_up` | — | Pass |
| RQ-21 | Keyboard: dropdowns operable, focus visible and in view, text-size shortcuts; recovery actions reachable by Tab | GUI scenarios (4) | — | Handler level pass; **real keyboard pending** (G6) |
| RQ-22 | Layout at 100/125/150% and minimum size; text wraps to the window (D-31) | GUI `window_opens_inside_the_work_area`, `recovery_window_fits_at_minimum_size`, `main_window_text_wraps_at_minimum_size` | installed at real 125%; `scaling/` (12 captures: round and recovery, three scalings, two text sizes) | 125% pass; 100/150% emulated pass; **real 100/150% pending** (G7) |
| RQ-27 | A letter key guesses that letter, and a used key does nothing | GUI `letter_keys_guess_on_click` | demo; smoke uses the typing route | Pass |
| RQ-28 | A guess redraws the round without rebuilding the screen (D-32) | — | `performance/guess-to-redraw.txt`: 32–45 ms median, 48–102 samples per run | Pass for guesses that continue a round; the round-ending guess still rebuilds |
| RQ-29 | Feedback lines are the 40 originals, word for word (T-31, DEC-07) | `test_the_original_feedback_lines_are_back_word_for_word` | `installed-smoke/practice.png` | Pass |
| RQ-30 | Word lists: 1,544 words, four languages, five levels, three clues, no repeats (T-30) | `test_every_language_has_all_five_levels_and_the_counts_add_up`, `scripts/check_curated_content.py` | step 3 | Pass for structure; **accuracy pending** (G9) |
| RQ-31 | A level session stays in its language and level; Review stays inside it | `test_a_level_session_stays_in_its_language_and_level`, `test_review_at_a_level_only_uses_words_practised_at_that_level` | step 6 (German list) | Pass |
| RQ-32 | Legacy banks and old travel cards stay out of practice (D-02) | `test_seeding_never_offers_legacy_banks_or_old_travel_cards`, `test_legacy_content_is_excluded_from_new_practice` | step 7 | Pass |
| RQ-33 | Accents count as the normal letter, `s` reveals `ß`, German capitals stay, spaces and hyphens show, and every letter is on the A–Z keys | `test_a_plain_letter_reveals_its_accented_forms`, `test_an_accented_guess_counts_as_the_plain_letter_and_costs_no_second_try`, `test_a_word_is_won_with_plain_letters_alone`, `test_s_reveals_sharp_s`, `test_a_round_paused_in_rc5_with_an_accented_guess_still_works`, `test_german_nouns_keep_their_capital`, `test_phrases_show_their_spaces_and_hyphens_without_being_guessed`, `test_every_letter_in_the_lists_is_on_the_a_to_z_keys` (4), `test_ignoring_accents_never_makes_two_words_in_a_language_identical`, GUI `plain_keys_reveal_accented_letters` | step 6 | Pass; **real keyboard pending** (G6) |
| RQ-34 | Board and learning card work for every word, at minimum size | GUI `long_phrases_fit_the_board_at_minimum_size`, `level_word_card_shows_its_clues` | demo | Pass; **a person using them pending** (G6, G7) |
| RQ-35 | Three clues show on Easy and Hard | `test_level_words_show_three_different_clues_on_easy`, `test_hard_mode_shows_all_three_clues_with_two_lives_left` | — | Pass |
| RQ-36 | All words runs until End session, uses every word, then repeats oldest first, and the saved session stays small (DEC-30) | `test_an_endless_session_uses_every_word_then_repeats_oldest_first`, `test_an_endless_session_keeps_the_saved_session_small`, GUI `endless_play_runs_until_end_session` | `performance/long-session.txt`: 200 rounds, 0 review records | Pass |
| RQ-37 | End session keeps finished words and drops the one in play; a session with no finished word is not counted; ending twice changes nothing (DEC-32) | `test_end_session_keeps_finished_words_and_drops_the_unfinished_one`, `test_ending_a_session_with_no_finished_word_is_not_counted`, `test_ending_twice_changes_nothing` | smoke | Pass |
| RQ-38 | Travel cards and Word cards are gone, the six held-back words are back, and a paused travel session ends cleanly (DEC-27, DEC-29) | `test_the_travel_cards_are_gone`, `test_the_six_words_kept_off_the_lists_for_the_travel_cards_are_back`, `test_a_paused_travel_session_finishes_its_word_then_says_it_has_ended`, GUI `removed_screens_and_settings_stay_removed` | step 5 (a paused Restaurant round from rc5 finished) | Pass; an upgrade leaves one unread file (D-34) |
| RQ-39 | The letter keys stay still whatever the feedback says (D-33) | GUI `board_stays_put_whatever_the_feedback_says`, `letter_keys_guess_on_click` | `d33-board-moves.txt` | Pass |
| RQ-23 | Content structurally valid; warnings dispositioned | `scripts/check_curated_content.py` | — | Pass; **educator review pending** (G9) |
| RQ-24 | Learner acceptance (5 sessions) | — | — | **Pending** (G10) |
| RQ-25 | Third-party notices ship and match what is bundled (T-28) | `tests/test_third_party_notices.py` (3) | build check; step 4 | Pass (build machine) |
| RQ-26 | Release hygiene check ignores Git's data but reports real artifacts (D-29) | `test_release_check_ignores_git_data_but_not_real_artifacts`, `test_release_check_on_a_real_release_branch_clone_and_worktree` | clone, worktree, extracted archive | Pass |

## Defect reproduction

D-01..D-03 and D-07: reproduced on `16f3fc3` before any change
(`evidence/2026-09-19-baseline-16f3fc3/`), re-run after (`evidence/2026-09-19-m2-525c377/`).
D-29, D-30, D-31 and T-28: reproduced on the rc2 code and re-run on `fd3b25a`
(`evidence/2026-09-19-rc3-fd3b25a/defects/`). D-33: reproduced on `2bfbd61` and re-run on
`e0aa9c0` (`evidence/2026-11-01-rc6-e0aa9c0/d33-board-moves.txt`).

## Corrections to earlier records

**rc5's verification missed D-33.** rc5's record shows the board checked at the minimum size,
and the checks passed, but none of them tried the long feedback lines rc5 restored. The defect
was in the rc5 installer. Its results stand as a record of what ran; rc6 replaces it.

**The rc5 test count.** The first draft of this record said the five new GUI scenarios had
run in the 194. They had not (I-11).

**The rc4 summary and first record.** The handover and an earlier version of this record
said 175 tests passed on `d543579`; the clean-clone run there was 174 passed, 1 failed. The
archive record also named a commit it had not been run on. Both are corrected (I-8).

**The rc4 figures and counts (I-9).** An audit against the evidence on 2026-11-01 corrected
this record and DELIVERY.md. From `performance.txt`: open 13 ms and 17 ms (this table said
12 and 15), full backup 122 ms and 125 ms (it said 102 and 123, and the README said 102),
and guess to redrawn screen 39 ms and 606 ms (DELIVERY.md said 41 and 640). `licenses/`
holds 12 texts, not 13; the thirteenth file is the notices list. `build-output/build.log`
does not name the commit, so the link between the installer and `d543579` rests on the
validation records and the tag. The installer and the raw evidence did not change.

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
- Whether any word, clue or level is correct: no check here can tell.
- A person playing the words, or typing accented letters.
- A profile with a long history in the word lists: the performance dataset's history is on the
  old travel cards.
- rc6 running on the owner's real data, which it has not yet opened.
- Code signing (the installer is unsigned).
