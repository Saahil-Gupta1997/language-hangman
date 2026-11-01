# Verification — Language Hangman 1.0.0rc5

What was actually executed, on which revision and artifact, with what result. Manual and
human acceptance gates, and their status, are in [ACCEPTANCE.md](ACCEPTANCE.md). Nothing
here was produced by a learner, an educator or a manual tester, and **nothing here checks
that the level-list words or their clues are correct**.

**Release candidate:** revision `f2bb6b9` (branch `release/1.0`); installer
`LanguageHangman-1.0.0rc5-Setup.exe`, SHA256 `a94a92696cf5f001fb7326fb92628557f5907b0122383d3269d3aa4e26d47531`. Evidence:
[`evidence/2026-11-01-rc5-f2bb6b9/`](evidence/2026-11-01-rc5-f2bb6b9/). Commits after
`f2bb6b9` change documents, evidence, one line of test wiring (I-11) and one logging line
in the build script: `git diff f2bb6b9 -- src desktop_app.py packaging` is empty, and
PyInstaller does not bundle `scripts/` or `tests/`. So the installer matches the published
source.

The previous candidates' evidence stays in place: rc4 in
[`evidence/2026-11-01-rc4-d543579/`](evidence/2026-11-01-rc4-d543579/), rc3 in
[`evidence/2026-09-19-rc3-fd3b25a/`](evidence/2026-09-19-rc3-fd3b25a/), rc2 in
[`evidence/2026-09-19-rc2-4ad1e34/`](evidence/2026-09-19-rc2-4ad1e34/).

## Environment: the build machine, not a clean machine

| Item | Value |
| --- | --- |
| Machine | AMD Ryzen 7 6800H (8 cores/16 threads), 15.2 GB RAM, NVMe SSD |
| OS | Windows 11 Home 10.0.26200, 1920×1080 panel at **125%** display scaling (the real setting) |
| Runtime / build | Python 3.12.1 · CustomTkinter 5.2.2 · Pillow 12.3.0 · PyInstaller 6.11.1 · Inno Setup 6.7.3 |
| Executed by | Claude Code (AI assistant) on the owner's computer, 2026-09-19 (rc2, rc3) and 2026-11-01 (rc4, rc5) |

This is the development and build machine: Python, the build tools and earlier versions of
the app have all been on it. Installer results below are **build-machine** results. A clean
Windows account without Python (G5) has not been tested. The owner was using the computer
throughout, so no step sent operating-system keystrokes or mouse input, and screenshots
capture only the application's own window.

For rc5 the owner had rc4 installed and open on their own data. With their agreement it was
closed and replaced, and every step ran in a separate data folder set with
`LANGUAGE_HANGMAN_DATA_DIR`. Hashes of their data files are unchanged from before validation
to after it, and rc5 was left installed with their desktop shortcut restored.

## Kinds of evidence

| Label | Meaning | What it is not |
| --- | --- | --- |
| Automated | pytest: service tests, fault-injection tests and GUI scenarios. GUI scenarios open real windows and call the app's own handlers, bindings and Tk's focus traversal | Not real key presses, not visible focus judged by eye |
| Smoke journey | `--smoke-test`: 17 scripted checks in a real window, from source or the installed EXE | Same limits as above |
| Installed build | The real installer on the build machine; the installed EXE launched normally | Not a clean machine; sign-in was checked with code of the same revision, not typed |
| Real / emulated scaling | 125% is the machine's real setting; 100% and 150% are emulated with CustomTkinter's scaling | Emulation is not the Windows setting |
| Content check | `scripts/check_curated_content.py`: structure of the 30 cards and the level lists | Says nothing about whether a word or clue is correct |
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
| **`f2bb6b9` rc5 build commit** | **194 passed** in the clean clone; first run 193 passed, 1 failed (below) | **0** | clean | PASS, 24 dispositioned; 1,538 level-list words structurally valid | passed (17), source and installed | 19 new tests. Five new GUI scenarios were written but not yet in the runner's list (I-11) |

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

On a machine without a display, the 14 GUI scenarios skip by design (not run on Linux for
rc5). `test_release_check_on_a_real_release_branch_clone_and_worktree` skips if Git is not
installed. The GitHub workflows have not run: there is no remote repository (G13).

### What was re-run for rc5, and what was carried forward

The practice flow, the board, the word data and the feedback lines changed in rc5, so
everything that touches them was re-run on `f2bb6b9` or its installer: the suite, the smoke
journey from source and from the installed build, the whole installer sequence, performance,
the scaling checks, the demo and the screenshots.

Carried forward without re-running, because neither the code nor the inputs changed: the
D-26 harness investigation, the original D-01..D-03 reproduction scripts (their regression
tests ran again inside the 194), and the rc3 defect reproductions for D-29 to D-31 (their
regression tests also ran again). The v1.0.0-beta database for the import check is the file
rebuilt for rc4 with the beta's own code (SHA256 `a512e245…`); the original was lost (I-6).

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

For rc5, `release-check` was clean in an ordinary clone of `f2bb6b9`
(`checks/release-check.txt`) and on the extracted source archive (see the release package's
`VERIFICATION-*.txt`). The worktree case runs inside the suite.

## Installer validation (rc5, build machine)

Installer 14,791,371 bytes, SHA256 `a94a92696cf5f001fb7326fb92628557f5907b0122383d3269d3aa4e26d47531`, built by `scripts/build_desktop.ps1` in a fresh
clone of `f2bb6b9`; installed EXE SHA256
`9de7b25420319c9c163dcf623ffb530ce48805c56a053accf50a1640bc1428b8`. Unsigned.
Files: `evidence/…/installer-validation/`.

| # | Check | Result |
| --- | --- | --- |
| 1 | The owner's rc4 uninstalled; pre-state; install 1.0.0rc4 (`abb0cf94…`) | Nothing installed before; rc4 installed and registered |
| 2 | rc4 creates its own data with rc4's code (`d543579`): 2 profiles, a win, a loss, a round paused mid-guess | Done |
| 3 | **Upgrade**: run the rc5 installer over rc4 | Exit 0; the data file byte-identical; installed EXE identical to the build; one `1.0.0rc5` registration; `LICENSE.txt`, the notices and 12 licence texts beside the program; all four level lists installed |
| 4 | Third-party notices in the installed folder | 986 files, 13 notice files, **0 problems**; installed `LICENSE.txt` identical to the repository's |
| 5 | Normal launch of installed rc5 on the upgraded data; sign-in and data checked with `f2bb6b9` code | Sign-in screen in 2.27 s, including the first word load; rc4 password accepted, wrong one rejected; 2 rounds kept; paused round resumed and completed |
| 6 | Installed `--smoke-test`, `PATH` = Windows folders only, no `PYTHON*` variables | Exit 0; 17/17 in 28 s, including the German level list; validation data untouched |
| 7 | Import a v1.0.0-beta database (schema 0) through the restore path | Opens normally; beta sign-in and 3 rounds kept; Review offers only practised curated words (`clean` in Hotel, `early` in Airport, Restaurant refused) |
| 8 | Damage the live data file; launch the installed app, Standard and Large text | **Recovery window** in 0.83–0.88 s; captured at opening and minimum size; text fits at both sizes |
| 9 | Restore the newest automatic backup (the first button's code path) | Damaged bytes quarantined exactly; both profiles back; **no stale side files**; normal start in 1.04 s |
| 10 | Uninstall | Program, Start-menu entry and registration removed; all 7 data files kept byte-for-byte |

The uninstall in step 1 also removed the owner's desktop shortcut, which the final silent
install did not bring back. That was noticed in the uninstall log and put right by rerunning
the installer with the desktop-shortcut option.

## Restore rollback (D-30)

Fault-injection tests in `tests/test_recovery.py`, run in the 194:

| Case | Test | Result |
| --- | --- | --- |
| Second side-file move fails | `test_failed_second_side_file_move_puts_the_first_back` | First file back, bytes identical; "unchanged" is true |
| Replacing the main database fails | `test_failed_database_switch_puts_every_side_file_back` | All three side files back |
| Successful restore | `test_successful_restore_keeps_stale_side_files_out_of_the_restored_data` | No side file next to the restored data; set-aside copies kept; data comes from the backup |
| Putting a file back fails | `test_failed_rollback_says_where_the_side_files_are_kept` | Stage `rollback`; message names each kept file, its original place and the safety copy; no "unchanged" claim |

The first and last fail on the rc2 code (`defects/D-30-restore-rollback.txt`). The installed
build contains the same code (EXE built from `f2bb6b9`); its successful restore paths were
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
from the inventory. rc5 build folder: 983 files, 0 problems. Installed folder: 986 files, 0
problems.

## Performance (build machine)

rc5 and rc4 were measured in one session on 2026-11-01 from clean clones of `f2bb6b9` and
`d543579`, with the same tool and interpreter and with the revisions alternating
(`performance/`). The owner was using the computer. These are single-machine observations,
not guarantees.

**Guess to redrawn screen, the game's hot path** (a fresh profile; three runs of each;
correct guesses only, about one in five of which ends a round):

| Words | Samples per run | Median | 95th percentile | Longest guess |
| --- | --- | --- | --- | --- |
| rc4, travel cards | 55 | 28 / 41 / 51 ms | 559 / 570 / 583 ms | 1,003 ms |
| **rc5, travel cards** | 55 | **40 / 41 / 42 ms** | **555 / 581 / 589 ms** | 1,096 ms |
| rc5, Spanish Beginner | 59 | 53 / 59 / 127 ms | 709 / 709 / 712 ms | 951 ms |
| rc5, German Expert | 110 | 31 / 32 / 32 ms | 763 / 790 / 803 ms | 1,389 ms |

Travel cards are no slower than rc4 (G16). The guess that ends a round is 150–200 ms slower
in a word list than on travel cards, which is probably because the next word is chosen from
about 80 candidates instead of 10; that cause has not been measured.

**Other operations** (5 profiles, one with 5,000+ completed rounds, 4.55 MB; the rc4 column is
rc4's `performance.txt`, measured earlier the same day):

| Operation | Samples | Median | 95th percentile | rc4 median |
| --- | --- | --- | --- | --- |
| Open, upgrade check and quick check | 10 | 13 ms | 16 ms | 13 ms |
| Full backup (copy and validation) | 5 | 95 ms | 114 ms | 122 ms |
| Reports aggregation, 5,000+ rounds | 20 | 56 ms | 66 ms | 55 ms |
| Guess, round continues (service only) | 115 | 14 ms | 16 ms | 13 ms |
| Guess that completes a round (all writes) | 30 | 33 ms | 43 ms | 30 ms |
| Screen change: Home / Reports / Practice setup | 5 each | 357 / 538 / 626 ms | 458 / 559 / 632 ms | 354 / 565 / 503 ms |

**Word cards** (`word-cards.txt`, a fresh profile, two runs of five against rc4 in the same
session): opening the page takes 1.9–3.1 s, against 1.8 s in rc4. It still builds 30 cards from
widgets, now with two filters above them. Switching to a word list takes 117–166 ms at the
median, because a list is one text box.

**Start-up of the installed EXE to a visible window**, 5 launches on a fresh copy of the dataset:
1.03–1.04 s, and 2.06 s for the first launch, which also loads the level lists for the first
time and makes the day's automatic backup (rc4: 0.88–0.93 s and 1.19 s). Loading and checking
the words at every start accounts for most of the difference: about 129 ms when timed on its
own.

Three honest comparisons:

- **Sessions differ more than versions do.** rc4's 95th percentile above is 559–583 ms, and
  earlier the same day it was 763–789 ms. Compare only within a session.
- **rc4's recorded 39 ms and 606 ms** are real output in rc4's `performance.txt`, but they are
  one run, and later runs differ.
- **Against rc3**, a typical guess is much faster and a round-ending guess about twice as slow.
  That is rc4's trade-off, and rc5 keeps it. Navigation is slower than rc3, because screens
  group content into cards.

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
| RQ-16 | Genuine upgrade keeps credentials and progress | `test_legacy_upgrade_preserves_data_and_takes_backup` | steps 2–5 (data made by rc4) | Pass |
| RQ-17 | Uninstall preserves learner data | — | step 10 | Pass |
| RQ-18 | Runs without Python installed | — | step 6 (no Python on `PATH`) | Partial: clean machine pending (G5) |
| RQ-19 | Privacy-safe diagnostics with operation, stage, version | `test_diagnostics_contain_codes_but_no_personal_data` | — | Pass |
| RQ-20 | Backup failure does not block start-up; visible warning | GUI `automatic_backup_failure_does_not_block_start_up` | — | Pass |
| RQ-21 | Keyboard: dropdowns operable, focus visible and in view, text-size shortcuts; recovery actions reachable by Tab | GUI scenarios (4) | — | Handler level pass; **real keyboard pending** (G6) |
| RQ-22 | Layout at 100/125/150% and minimum size; text wraps to the window (D-31) | GUI `window_opens_inside_the_work_area`, `recovery_window_fits_at_minimum_size`, `main_window_text_wraps_at_minimum_size` | installed at real 125%; `scaling/` (12 captures: round and recovery, three scalings, two text sizes) | 125% pass; 100/150% emulated pass; **real 100/150% pending** (G7) |
| RQ-27 | A letter key guesses that letter, and a used key does nothing | GUI `letter_keys_guess_on_click` | demo; smoke uses the typing route | Pass |
| RQ-28 | A guess redraws the round without rebuilding the screen (D-32) | — | `performance/guess-to-redraw.txt`: 40–42 ms median, 55 samples per run | Pass for guesses that continue a round; the round-ending guess still rebuilds |
| RQ-29 | Feedback lines are the 40 originals, word for word (T-31, DEC-07) | `test_the_original_feedback_lines_are_back_word_for_word` | `installed-smoke/practice.png` | Pass |
| RQ-30 | Level lists: four languages, five levels, three clues, no repeats (T-30) | `test_every_language_has_all_five_levels_and_the_counts_add_up`, `scripts/check_curated_content.py` | step 3 | Pass for structure; **accuracy pending** (G9) |
| RQ-31 | A level session stays in its language and level; Review stays inside it | `test_a_level_session_stays_in_its_language_and_level`, `test_review_at_a_level_only_uses_words_practised_at_that_level` | step 6 (German list) | Pass |
| RQ-32 | Legacy banks stay out of practice with two packs (D-02) | `test_seeding_keeps_the_travel_cards_and_never_offers_legacy_banks`, `test_legacy_content_is_excluded_from_new_practice` | step 7 | Pass |
| RQ-33 | Accents, ß, capitals, spaces and hyphens work; every letter has a key | `test_an_accented_letter_is_its_own_letter`, `test_german_nouns_keep_their_capital_and_are_guessed_in_lower_case`, `test_sharp_s_can_be_guessed_and_composed_input_is_accepted`, `test_phrases_show_their_spaces_and_hyphens_without_being_guessed`, `test_every_letter_in_the_lists_has_a_key` (4), GUI `accent_keys_are_on_the_board_for_each_language` | step 6 | Pass; **real keyboard pending** (G6) |
| RQ-34 | Setup, board, learning card and Word cards work for word lists, at minimum size | GUI `word_set_choices_follow_the_language`, `long_phrases_fit_the_board_at_minimum_size`, `level_word_card_shows_its_clues`, `word_cards_page_lists_a_level_without_a_card_per_word` | demo | Pass; **a person using them pending** (G6, G7) |
| RQ-35 | Three clues show on Easy and Hard for level-list words | `test_level_words_show_three_different_clues_on_easy`, `test_hard_mode_shows_all_three_clues_with_two_lives_left` | — | Pass |
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
- Whether any level-list word, clue or level is correct: no check here can tell.
- A person playing a word list, or typing or clicking accented letters.
- A profile with long histories in word lists: the performance dataset uses travel cards.
- Code signing (the installer is unsigned).
