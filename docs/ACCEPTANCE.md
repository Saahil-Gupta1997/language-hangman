# Release acceptance — 1.0.0rc7

The version stays a release candidate until every **blocking** gate below has a named
person, a date and evidence. Automated tests and AI-run checks never substitute for the
manual, educator or learner gates, and those results must never be written by an AI or
filled in from automated output.

## Gates

| # | Gate | Blocking | Status | Owner | Evidence |
| --- | --- | --- | --- | --- | --- |
| G1 | P0 defects fixed with regression tests: D-01, D-02, D-03 (rc2) and D-30 (rc3) | Yes | **Met** | Engineering | VERIFICATION.md RQ-01..RQ-11 |
| G2 | Automated suite, lint, content check, release check on the candidate revision | Yes | **Met on the build commit** (214 passed, 0 skipped, `c58d208`) | Engineering | evidence/…/checks |
| G3 | Installer built from the candidate commit in a clean checkout; SHA256 recorded | Yes | **Met** | Engineering | evidence/…/build-output |
| G4 | Install, upgrade from the previous release, beta import, recovery, uninstall on Windows | Yes | **Met on the build machine** (not a clean machine) | Engineering | VERIFICATION.md installer steps 1–10 |
| G16 | Performance measured on the candidate: the game's hot path no slower than the previous release | Yes | **Met** against rc6, measured in one session on 2026-11-01, three word lists, three runs each: guess to redrawn screen, median 35–49 ms against 35–40 ms, 95th percentile 522–648 ms against 434–635 ms, longest guess 679 ms against 738 ms. Level, not faster: the ranges overlap, one English run reached 49 ms, and the cause of that run has not been measured. Against rc3 the round-ending guess is slower, as in rc4 to rc6 | Engineering | VERIFICATION.md performance |
| G5 | Clean Windows account without Python: install, launch, sign in, play | Yes | Pending | Owner | Manual record M1 |
| G6 | Keyboard-only journey, visible focus, Enter/Escape, text size | Yes | Pending (bindings and Tab traversal verified automatically) | Owner | Manual record M2 |
| G7 | Layout at real 100%, 125% and 150% and at the minimum window size, main and recovery windows | Yes | Pending (real 125% and emulated 100%/150% pass) | Owner | Manual record M3 |
| G8 | Recovery through the installed UI (damaged data, restore, sign in), Standard and Large text | Yes | Pending (installed-build path verified automatically) | Owner | Manual record M4 |
| G9 | Qualified review of everything that ships: the 1,544 words in the four word lists, with a reviewer for each language. All four languages must pass before 1.0 (owner, 2026-11-01, DEC-23) | Yes | Pending | Owner to appoint four reviewers | CONTENT_REVIEW.md, the kit's review sheets |
| G10 | Five learner sessions recorded, on the English Beginner list unless the owner decides otherwise (DEC-23) | Yes | Pending | Owner to recruit | USER_ACCEPTANCE.md |
| G11 | Material issues from G5–G10 fixed and retested | Yes | Not started | Engineering + owner | DELIVERY.md register |
| G12 | Owner decisions: Review rule (DEC-06), supported history (DEC-10), installer terms (DEC-14: none in rc4 to rc7, decision still needed before publishing), intended learner (DEC-15), who wrote `words.xlsx` (DEC-22). **Decided: licence (DEC-08), MIT for the software, scope and copyright line kept, with the word lists excluded; feedback tone (DEC-07), the original sarcastic lines; hanging figure (DEC-21), kept; word lists in four languages (DEC-22); rc6's redesign (DEC-27 to DEC-32); rc7's simpler round screens (DEC-35)** | Yes (DEC-14 before publishing) | Partly met | Owner | DELIVERY.md decision log |
| G13 | Windows CI and release workflows run on GitHub for the release commit | No | Pending (no remote yet) | Owner | Actions run links |
| G14 | Code signing | No | Not planned; installer documented as unsigned | Owner | README.md |
| G15 | Third-party licence notices shipped with the installer (T-28) | Yes, before public distribution | **Met on the build machine** | Engineering | VERIFICATION.md "Third-party notices" |

## Manual checks

Use the rc7 installer and confirm its SHA256 before starting:
`c0089bfbc8cc9f56d2996e18e794438870c82a384ed797d4f6b699bab3e6d2c3`. Record every check in the
table at the end, including failures and anything confusing. A printable copy of these
steps is in the release package's `acceptance-kit` folder.

### M1 — Clean installation (G5)

1. On a Windows 10/11 account that has never had Python or Language Hangman, confirm
   `where python` finds nothing (or only the Microsoft Store stub).
2. Run the installer. Expect an "unknown publisher" SmartScreen warning (unsigned).
3. Start from the Start menu. Create a profile; confirm a short password and a mismatched
   confirmation are rejected. Sign out; confirm a wrong password is rejected; sign in.
4. Play at least four words with All words, guessing both by typing and by clicking letter
   keys, then choose End session: Reports opens and counts the session. Try guest practice;
   sign out; confirm the guest's progress is gone after restarting. Then play German and
   Spanish words until one has an accented letter: guessing the plain letter fills it in.
5. Open the program folder (`%LOCALAPPDATA%\Programs\LanguageHangman`) and confirm
   `THIRD-PARTY-NOTICES.txt` and the `licenses` folder are there and readable.

### M2 — Keyboard only (G6)

Unplug or ignore the mouse for the whole journey.

1. Sign-in: Tab reaches profile name, password and each button in order; the current
   button shows an **amber outline**; Enter or Space activates it; Enter in the password
   field signs in.
2. Practice setup: Tab reaches each dropdown (it turns **amber**); Up/Down change the value;
   Enter or Space opens the list, arrows move, Enter chooses, Escape closes.
3. During a round: the guess box has focus; typing a letter and Enter submits; Tab reaches
   "Submit guess", "Save and return home" and "End session"; focused controls scroll into
   view. After a round, Enter moves to the next word.
   The A–Z letter keys are deliberately **not** in the Tab order (they repeat the typing
   route for mouse users): confirm Tab skips them, and that clicking one guesses that letter.
4. Escape returns home from any signed-in screen. Ctrl + (or Ctrl =) makes text larger;
   Ctrl − returns to standard; the setting is kept after restarting.
5. Settings: reach backup, restore, export, delete and diagnostics by keyboard; dialogs
   answer with Enter/Escape.
6. Recovery window (after M4 step 2): Tab reaches every restore button, "Choose a backup
   file…", "Open data folder" and "Quit"; each scrolls into view; Escape closes the window.

### M3 — Display scaling and window size (G7)

For each of 100%, 125% and 150% (Settings › System › Display › Scale), sign out and back
in to Windows, then start the app:

1. The window fits on screen; the title bar is visible.
2. Resize to the smallest size allowed. On Home, Practice (setup and a round), a learning
   card, Reports, Settings and Help, no text or control is cut off at the right; the page
   scrolls where needed. In a round, check the whole board is usable: the figure, the letter
   tiles, the lives and every letter key. Include an Expert list, which has the longest words
   and phrases.
3. Repeat step 2 with Large text.
4. At this scaling, open the recovery window (M4 step 2) at its smallest size with Standard
   and with Large text: every instruction is readable without being cut off, and every
   button can be reached by scrolling.

### M4 — Recovery through the installed UI (G8)

1. Settings › Create full backup; save it somewhere you can find.
2. Close the app. In `%LOCALAPPDATA%\LanguageHangman`, rename `app.db` to `app.db.old` (this
   keeps the original), then create a text file containing a few words and name it
   `app.db`. (An *empty* file is not enough: SQLite treats it as a new, valid database.)
3. Start the app: the recovery window appears instead of an error. Resize it to its smallest
   size and read every instruction.
4. Choose the backup (or the newest automatic backup), confirm, and sign in: profiles and
   progress are back; `backups\quarantine-…` contains the damaged file.
5. Repeat steps 2–4 with Large text set in Settings beforehand.

### Upgrade (optional repeat of G4)

Install the 1.0.0rc6 installer, create a profile and play a round through its UI, then run
the rc7 installer over it and sign in with the same profile: progress and any paused round
are still there.

### Record

| Check | Tester | Date | OS and scaling | Revision | Installer SHA256 | Result | Evidence / notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M1 | | | | c58d208 | c0089bfb…e6d2c3 | Not run | |
| M2 | | | | c58d208 | c0089bfb…e6d2c3 | Not run | |
| M3 100% | | | | c58d208 | c0089bfb…e6d2c3 | Not run | |
| M3 125% | | | | c58d208 | c0089bfb…e6d2c3 | Not run | |
| M3 150% | | | | c58d208 | c0089bfb…e6d2c3 | Not run | |
| M4 | | | | c58d208 | c0089bfb…e6d2c3 | Not run | |

## Release evidence index

| Item | Location | Identifier |
| --- | --- | --- |
| Source revision (installer) | branch `release/1.0` | `c58d208` (later commits change documents and evidence only; nothing the installer bundles) |
| Windows installer (unsigned) | release package | `LanguageHangman-1.0.0rc7-Setup.exe`, 14,784,365 bytes, SHA256 `c0089bfbc8cc9f56d2996e18e794438870c82a384ed797d4f6b699bab3e6d2c3` |
| Installed program | inside the installer | `LanguageHangman.exe` SHA256 `ff3ef89d691cba9bc8cfc0a1763cf34d7bbf925e32f4fecd7fc1585199cb3e79` |
| Licence | `LICENSE`; installed as `LICENSE.txt` beside the program | MIT for the software; word content and icon not yet licensed |
| Third-party notices | `packaging/third-party/`; installed next to the program | 15 components, 12 licence texts and the notices file |
| Source archive | release package | see `SHA256SUMS.txt` in the release package |
| Build log | `docs/evidence/2026-11-01-rc7-c58d208/build-output/` | line 11 of `build.log` names the commit; `revision.txt` repeats it |
| Automated results | `docs/evidence/2026-11-01-rc7-c58d208/checks/` | build commit: 214 passed |
| Word conversion | `scripts/build_level_words.py`, `docs/evidence/2026-11-01-rc6-e0aa9c0/level-list-conversion.txt` | 1,544 words kept, 56 repeated rows left out; the word files have not changed since |
| Defect reproductions (D-29, D-30, D-31, T-28) | `docs/evidence/2026-09-19-rc3-fd3b25a/defects/` | rc2 code vs `fd3b25a` |
| Defect reproduction (D-33) | `docs/evidence/2026-11-01-rc6-e0aa9c0/d33-board-moves.txt`, `d33-columns-diagnosis.txt` | `2bfbd61` vs `e0aa9c0`; why the columns became equal |
| New tests on the old code (D-34, D-35, D-36) | `docs/evidence/2026-11-01-rc7-c58d208/new-tests-on-rc6.txt` | each fails on rc6 and passes on rc7 |
| Installer validation | `docs/evidence/2026-11-01-rc7-c58d208/installer-validation/` | steps 01–10, Inno Setup logs, screenshots, and `11-after-validation.txt` |
| Installed smoke journey | `docs/evidence/2026-11-01-rc7-c58d208/installed-smoke/` | 17 checks |
| Performance | `docs/evidence/2026-11-01-rc7-c58d208/performance/` | rc6 and rc7 guess to redraw in one session, a 200-round session, 5,000+ round profile, start-up |
| Scaling | `docs/evidence/2026-11-01-rc7-c58d208/scaling/` | round and recovery at three scalings, two text sizes |
| Demo recording | `docs/media/language-hangman-1.0.0rc7-demo.mp4` | 154 s, SHA256 `fc49d1059fc176d55ced8a58a5273f24952e6a8113e5e9684b64927f0f54f47e`; scripted run of `c58d208` from a clean clone, slowed 1.3× for captions |
| rc6 and earlier evidence | `docs/evidence/2026-11-01-rc6-e0aa9c0/`, `…-rc5-f2bb6b9/`, `…-rc4-d543579/`, `…-rc3-fd3b25a/`, `…-rc2-4ad1e34/`, `…-baseline-16f3fc3/`, `…-m2-525c377/` | historical; see the I-4 note in the rc2 folder |
| Content review record | [CONTENT_REVIEW.md](CONTENT_REVIEW.md) | review not done |
| Learner sessions | [USER_ACCEPTANCE.md](USER_ACCEPTANCE.md) | none run |

## Go / no-go record

| Date | Candidate | Decision | Basis | Decided by |
| --- | --- | --- | --- | --- |
| 2026-09-19 | 1.0.0rc2 (`4ad1e34`) | No-go for 1.0 final. Recommended: share rc2 as a tested release candidate for G5–G10. | G1–G4 met; G5–G12 and G15 pending | Recommendation by Claude Code; owner decision pending |
| 2026-09-19 | 1.0.0rc3 (`fd3b25a`) | No-go for 1.0 final. Recommended: give rc3 to the people running G5–G10; do not publish the installer until DEC-08 and DEC-14 are decided. | G1–G4 and G15 met on the build machine; G5–G12 pending; no open P0 or P1 defects; the independent review's blocker (D-30) fixed | Recommendation by Claude Code; **owner decision pending** |
| 2026-11-01 | 1.0.0rc4 (`d543579`) | **No-go for 1.0 final.** Recommended: give rc4 to the people running G5–G10; it supersedes rc3 for every purpose. | G1–G4, G15 and G16 met on the build machine; licence decided (MIT); G5–G11 and the remaining G12 decisions pending; no open P0 or P1 defects | Recommendation by Claude Code; **owner decision pending** |
| 2026-11-01 | 1.0.0rc5 (`f2bb6b9`) | **No-go for 1.0 final.** Recommended: give rc5, not rc4, to the people running G5–G10. The level lists reach learners unreviewed and are labelled so in the app. | G1–G4, G15 and G16 met on the build machine; G9 widened to 1,568 words and four languages; G5–G11 and the remaining G12 decisions pending; no open P0 or P1 defects | Recommendation by Claude Code; **owner decision pending** |
| 2026-11-01 | 1.0.0rc6 (`e0aa9c0`) | **No-go for 1.0 final.** Recommended: give rc6, not rc5, to the people running G5–G10: rc5 has D-33. The words reach learners unreviewed and are labelled so in the app. | G1–G4, G15 and G16 met on the build machine; G5–G11 and the remaining G12 decisions pending; no open P0 or P1 defects; D-34, D-35 and D-36 open at P3, and the owner first chose to keep rc6 without fixing them (DEC-34) | Recommendation by Claude Code; **owner decision pending** |
| 2026-11-01 | 1.0.0rc7 (`c58d208`) | **No-go for 1.0 final.** Recommended: give rc7, not rc6, to the people running G5–G10. The words reach learners unreviewed, and Practice setup and Help say so. | G1–G4, G15 and G16 met on the build machine; G5–G11 and the remaining G12 decisions pending; no open P0 or P1 defects; D-34, D-35 and D-36 fixed | Recommendation by Claude Code; **owner decision pending** |

Promote to 1.0.0 only when G1–G12, G15 and G16 are met and the owner approves: change the version
in `src/__init__.py` (the installer and `VERSION` follow it), rebuild from the tagged commit
in a clean checkout, repeat G2–G4 and G15 on that artifact, and add a row above.
