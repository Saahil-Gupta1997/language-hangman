# Release acceptance — 1.0.0

1.0.0 was released on the owner's approval on 2026-11-01 (DEC-38). **Owner-reported** means the owner
said the check was done; no tester name, date sheet or observations are held in this repository, and
this record claims no more than that. Automated tests and AI-run checks never substitute for a manual
check.

## Gates

| # | Gate | Blocking | Status | Owner | Evidence |
| --- | --- | --- | --- | --- | --- |
| G1 | P0 defects fixed with regression tests: D-01, D-02, D-03 (rc2) and D-30 (rc3) | Yes | **Met** | Engineering | VERIFICATION.md RQ-01..RQ-11 |
| G2 | Automated suite, lint, content check, release check on the candidate revision | Yes | **Met on the build commit** (216 passed, 0 skipped, `5f89265`) | Engineering | evidence/…/checks |
| G3 | Installer built from the candidate commit in a clean checkout; SHA256 recorded | Yes | **Met** | Engineering | evidence/…/build-output |
| G4 | Install, upgrade from the previous release, beta import, recovery, uninstall on Windows | Yes | **Met on the build machine** (not a clean machine) | Engineering | VERIFICATION.md installer steps 1–10 |
| G16 | Performance measured on the candidate: the game's hot path no slower than the previous release | Yes | **Met** against rc9, measured in one session on 2026-11-01, three word lists, three runs each: guess to redrawn screen, median 34–48 ms against 34–52 ms, 95th percentile 516–726 ms against 535–691 ms, longest guess 819 ms against 1,129 ms. Level, as expected: 1.0.0 changes no game code. Against rc3 the round-ending guess is slower, as in rc4 to rc9 | Engineering | VERIFICATION.md performance |
| G5 | Clean Windows system without Python: install, licence page, launch, sign in, play | Yes | **Owner-reported on rc8 (2026-11-01)**: "completed on a separate system". Not repeated on rc9 or 1.0.0 | Owner | Manual record M1 |
| G6 | Keyboard-only journey, visible focus, Enter/Escape, text size | Yes | **Owner-reported on rc8 (2026-11-01)**: "checked". Not repeated on rc9 or 1.0.0 | Owner | Manual record M2 |
| G7 | Layout at the minimum window size, main and recovery windows: real 100%, automated real 125%, emulated 150% | Yes | **Owner-reported on rc8 (2026-11-01) at real 100%**. Automated at real 125% and emulated 150% on `5f89265`. Real 150% is not tested and is a stated limitation. The owner narrowed this gate (DEC-37) | Owner | Manual record M3; scaling evidence |
| G8 | Recovery through the installed UI (damaged data, restore, sign in), Standard and Large text | Yes | **Owner-reported on rc8 (2026-11-01)**: "completed". Not repeated on rc9 or 1.0.0 | Owner | Manual record M4 |
| G11 | Material issues from G5–G8 fixed and retested | Yes | **Met, owner-reported**: the owner names the rc6 and rc7 changes as the fixes (DEC-37), and those are verified above | Engineering + owner | DELIVERY.md register |
| G12 | Owner decisions | Yes | **Met**: review rule (DEC-06), supported history (DEC-10), installer terms (DEC-14), licence (DEC-08), intended learner (DEC-15), feedback tone (DEC-07), hanging figure (DEC-21), word lists (DEC-22), rc6's redesign (DEC-27 to DEC-32), rc7's round screens (DEC-35), the gates themselves (DEC-36, DEC-37), the release (DEC-38) | Owner | DELIVERY.md decision log |
| G13 | Windows CI runs on GitHub for the release commit | No | **Met on `5f89265`** (run 41334484841, Linux and Windows, including the smoke journey). The first run, on rc8's commit, failed one test (D-38). The release workflow has not run: it needs a `desktop-v*` tag | Owner | `github-actions.txt` |
| G14 | Code signing | No | Not planned; installer documented as unsigned | Owner | README.md |
| G15 | Third-party licence notices shipped with the installer (T-28) | Yes, before public distribution | **Met on the build machine** | Engineering | VERIFICATION.md "Third-party notices" |

G9 (word review) and G10 (learner sessions) were removed by the owner on 2026-11-01 (DEC-36). They are
not release checks, so this record makes no claim about them.

## Manual checks

Use the 1.0.0 installer and confirm its SHA256 before starting:
`1707bd4a8a3c4f9d3baf2a216b97cdbd5e1acc43caadbea72f816a4ba7fcfa1e`. Record every check in the
table at the end, including failures and anything confusing. A printable copy of these
steps is in the release package's `acceptance-kit` folder.

### M1 — Clean installation (G5)

1. On a Windows 10/11 account that has never had Python or Language Hangman, confirm
   `where python` finds nothing (or only the Microsoft Store stub).
2. Run the installer. Expect an "unknown publisher" SmartScreen warning (unsigned). The licence
   page appears: confirm Next stays disabled until you choose "I accept the agreement".
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

Install the 1.0.0rc9 installer, create a profile and play a round through its UI, then run
the 1.0.0 installer over it and sign in with the same profile: progress and any paused round
are still there.

### Record

| Check | Tester | Date | OS and scaling | Revision | Installer SHA256 | Result | Evidence / notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M1 | Owner-reported, unnamed | 2026-11-01 | Separate system; details not recorded | `f66aa51` (rc8) | f4b158b3…119288 | Reported complete | "completed on a separate system" |
| M2 | Owner-reported, unnamed | 2026-11-01 | Not recorded | `f66aa51` (rc8) | f4b158b3…119288 | Reported complete | "checked" |
| M3 100% | Owner-reported, unnamed | 2026-11-01 | 100% | `f66aa51` (rc8) | f4b158b3…119288 | Reported fine | "100% is best" |
| M3 125% | | | | | | Not run by a person | Automated at real 125% |
| M3 150% | | | | | | Not run by a person | Emulated only; stated limitation |
| M4 | Owner-reported, unnamed | 2026-11-01 | Not recorded | `f66aa51` (rc8) | f4b158b3…119288 | Reported complete | "Completed" |

## Release evidence index

| Item | Location | Identifier |
| --- | --- | --- |
| Source revision (installer) | branch `release/1.0`, `main` on GitHub | `5f89265` (later commits change documents and evidence only; nothing the installer bundles) |
| Windows installer (unsigned) | release package | `LanguageHangman-1.0.0-Setup.exe`, 14,786,721 bytes, SHA256 `1707bd4a8a3c4f9d3baf2a216b97cdbd5e1acc43caadbea72f816a4ba7fcfa1e` |
| Installed program | inside the installer | `LanguageHangman.exe` SHA256 `ac6440292f3c03abbd2dfa17f5351b0fbb34f78769d7879157767d43e7dd1806` |
| Licence | `LICENSE`; shown in setup and installed as `LICENSE.txt` beside the program | MIT for the software, word lists and icon; the legacy banks in `data/words/` are excluded |
| Third-party notices | `packaging/third-party/`; installed next to the program | 15 components, 12 licence texts and the notices file |
| Source archive | release package | see `SHA256SUMS.txt` in the release package |
| Build log | `docs/evidence/2026-11-01-1.0.0-5f89265/build-output/` | line 11 of `build.log` names the commit; `revision.txt` repeats it |
| Automated results | `docs/evidence/2026-11-01-1.0.0-5f89265/checks/`, `github-actions.txt` | build commit: 216 passed; GitHub Actions runs |
| Word conversion | `scripts/build_level_words.py`, `docs/evidence/2026-11-01-rc6-e0aa9c0/level-list-conversion.txt` | 1,544 words kept, 56 repeated rows left out; rc9 changed only the files' notes |
| Defect reproductions (D-29, D-30, D-31, T-28) | `docs/evidence/2026-09-19-rc3-fd3b25a/defects/` | rc2 code vs `fd3b25a` |
| Defect reproduction (D-33) | `docs/evidence/2026-11-01-rc6-e0aa9c0/d33-board-moves.txt`, `d33-columns-diagnosis.txt` | `2bfbd61` vs `e0aa9c0`; why the columns became equal |
| New tests on the old code | `docs/evidence/2026-11-01-rc9-0d2b821/new-tests-on-rc8.txt`, `docs/evidence/2026-11-01-rc7-c58d208/new-tests-on-rc6.txt` | each fails on the earlier code |
| Installer validation | `docs/evidence/2026-11-01-1.0.0-5f89265/installer-validation/` | steps 01–10, Inno Setup logs, screenshots, `11-after-validation.txt` and `12-licence-page.txt` |
| Installed smoke journey | `docs/evidence/2026-11-01-1.0.0-5f89265/installed-smoke/` | 17 checks |
| Performance | `docs/evidence/2026-11-01-1.0.0-5f89265/performance/` | rc9 and 1.0.0 guess to redraw in one session, a 200-round session, 5,000+ round profile, start-up |
| Scaling | `docs/evidence/2026-11-01-1.0.0-5f89265/scaling/` | round and recovery at three scalings, two text sizes |
| Demo recording | `docs/media/language-hangman-1.0.0-demo.mp4` | 154 s, SHA256 `4bc2df9c4db8f61b6a2a5700fd7c78d11428736a62e2896539962507d57ee03c`; scripted run of `5f89265` from a clean clone, slowed 1.3× for captions |
| rc9 and earlier evidence | `docs/evidence/2026-11-01-rc9-0d2b821/`, `…-rc8-f66aa51/`, `…-rc7-c58d208/`, `…-rc6-e0aa9c0/`, `…-rc5-f2bb6b9/`, `…-rc4-d543579/`, `…-rc3-fd3b25a/`, `…-rc2-4ad1e34/`, `…-baseline-16f3fc3/`, `…-m2-525c377/` | historical; see the I-4 note in the rc2 folder |

## Go / no-go record

| Date | Candidate | Decision | Basis | Decided by |
| --- | --- | --- | --- | --- |
| 2026-09-19 | 1.0.0rc2 (`4ad1e34`) | No-go for 1.0 final. Recommended: share rc2 as a tested release candidate for G5–G10. | G1–G4 met; G5–G12 and G15 pending | Recommendation by Claude Code; owner decision pending |
| 2026-09-19 | 1.0.0rc3 (`fd3b25a`) | No-go for 1.0 final. Recommended: give rc3 to the people running G5–G10; do not publish the installer until DEC-08 and DEC-14 are decided. | G1–G4 and G15 met on the build machine; G5–G12 pending; no open P0 or P1 defects; the independent review's blocker (D-30) fixed | Recommendation by Claude Code; **owner decision pending** |
| 2026-11-01 | 1.0.0rc4 (`d543579`) | **No-go for 1.0 final.** Recommended: give rc4 to the people running G5–G10; it supersedes rc3 for every purpose. | G1–G4, G15 and G16 met on the build machine; licence decided (MIT); G5–G11 and the remaining G12 decisions pending; no open P0 or P1 defects | Recommendation by Claude Code; **owner decision pending** |
| 2026-11-01 | 1.0.0rc5 (`f2bb6b9`) | **No-go for 1.0 final.** Recommended: give rc5, not rc4, to the people running G5–G10. The level lists reach learners unreviewed and are labelled so in the app. | G1–G4, G15 and G16 met on the build machine; G9 widened to 1,568 words and four languages; G5–G11 and the remaining G12 decisions pending; no open P0 or P1 defects | Recommendation by Claude Code; **owner decision pending** |
| 2026-11-01 | 1.0.0rc6 (`e0aa9c0`) | **No-go for 1.0 final.** Recommended: give rc6, not rc5, to the people running G5–G10: rc5 has D-33. The words reach learners unreviewed and are labelled so in the app. | G1–G4, G15 and G16 met on the build machine; G5–G11 and the remaining G12 decisions pending; no open P0 or P1 defects; D-34, D-35 and D-36 open at P3, and the owner first chose to keep rc6 without fixing them (DEC-34) | Recommendation by Claude Code; **owner decision pending** |
| 2026-11-01 | 1.0.0rc7 (`c58d208`) | **No-go for 1.0 final.** Recommended: give rc7, not rc6, to the people running G5–G10. The words reach learners unreviewed, and Practice setup and Help say so. | G1–G4, G15 and G16 met on the build machine; G5–G11 and the remaining G12 decisions pending; no open P0 or P1 defects; D-34, D-35 and D-36 fixed | Recommendation by Claude Code; **owner decision pending** |
| 2026-11-01 | 1.0.0rc8 (`f66aa51`) | **No-go for 1.0 final.** Recommended: give rc8, not rc7, to the people running G5–G10. The words reach learners unreviewed, and Practice setup and Help say so. | G1–G4, G15 and G16 met on the build machine; G5–G11 and the remaining G12 decisions pending; no open P0 or P1 defects | Recommendation by Claude Code; **owner decision pending** |
| 2026-11-01 | 1.0.0rc9 (`0d2b821`) | **Ready for the owner's final approval.** No 1.0.0 exists until they give it. | Every blocking gate met or owner-reported; G9 and G10 removed by the owner (DEC-36); real 150% scaling untested; no open P0 or P1 defects | Assessment by Claude Code; the owner approved it |
| 2026-11-01 | 1.0.0 (`5f89265`) | **Go.** The owner answered "Approve 1.0.0" after being told what it carries: manual checks reported on rc8, real 150% untested, no record of word accuracy, RK-7 open, the installer unsigned. | Blocking gates met or owner-reported on this basis; G2–G4, G15 and G16 repeated on this artifact; no open P0 or P1 defects | **Owner, 2026-11-01** |

For a later release, change the version in `src/__init__.py` (the installer and `VERSION` follow it), rebuild
in a clean checkout, repeat G2–G4 and G15 on that artifact, and add a row above.
