# Release acceptance — 1.0.0rc5

The version stays a release candidate until every **blocking** gate below has a named
person, a date and evidence. Automated tests and AI-run checks never substitute for the
manual, educator or learner gates, and those results must never be written by an AI or
filled in from automated output.

## Gates

| # | Gate | Blocking | Status | Owner | Evidence |
| --- | --- | --- | --- | --- | --- |
| G1 | P0 defects fixed with regression tests: D-01, D-02, D-03 (rc2) and D-30 (rc3) | Yes | **Met** | Engineering | VERIFICATION.md RQ-01..RQ-11 |
| G2 | Automated suite, lint, content check, release check on the candidate revision | Yes | **Met on the final tree** (199 passed, 0 skipped, ×3, `1c2eb39`). An earlier set of three had one failure, and the build commit's run left out 5 new GUI scenarios; both are explained in VERIFICATION.md | Engineering | evidence/…/checks, checks-final |
| G3 | Installer built from the candidate commit in a clean checkout; SHA256 recorded | Yes | **Met** | Engineering | evidence/…/build-output |
| G4 | Install, upgrade from the previous release, beta import, recovery, uninstall on Windows | Yes | **Met on the build machine** (not a clean machine) | Engineering | VERIFICATION.md installer steps 1–10 |
| G16 | Performance measured on the candidate: the game's hot path no slower than the previous release | Yes | **Met** against rc4, measured in one session on 2026-11-01: guess to redrawn screen, travel cards, median 40–42 ms against 28–51 ms and 95th percentile 555–589 ms against 559–583 ms. Against rc3 the round-ending guess stays about twice as slow, as in rc4 | Engineering | VERIFICATION.md performance |
| G5 | Clean Windows account without Python: install, launch, sign in, play | Yes | Pending | Owner | Manual record M1 |
| G6 | Keyboard-only journey, visible focus, Enter/Escape, text size | Yes | Pending (bindings and Tab traversal verified automatically) | Owner | Manual record M2 |
| G7 | Layout at real 100%, 125% and 150% and at the minimum window size, main and recovery windows | Yes | Pending (real 125% and emulated 100%/150% pass) | Owner | Manual record M3 |
| G8 | Recovery through the installed UI (damaged data, restore, sign in), Standard and Large text | Yes | Pending (installed-build path verified automatically) | Owner | Manual record M4 |
| G9 | Qualified review of everything that ships: the 30 teaching cards and the 1,538 level-list words, with a reviewer for each language (widened in rc5, DEC-23) | Yes | Pending | Owner to appoint reviewers | CONTENT_REVIEW.md, kit sheets 2 and 4 |
| G10 | Five learner sessions recorded, on the English travel cards unless the owner decides otherwise (DEC-23) | Yes | Pending | Owner to recruit | USER_ACCEPTANCE.md |
| G11 | Material issues from G5–G10 fixed and retested | Yes | Not started | Engineering + owner | DELIVERY.md register |
| G12 | Owner decisions: Review rule (DEC-06), supported history (DEC-10), installer terms (DEC-14: none in rc4 or rc5, decision still needed before publishing), intended learner (DEC-15), who wrote `words.xlsx` (DEC-22). **Decided: licence (DEC-08), MIT for the software, scope and copyright line kept, with the level lists excluded like the cards; feedback tone (DEC-07), the original sarcastic lines; hanging figure (DEC-21), kept; level lists in four languages (DEC-22)** | Yes (DEC-14 before publishing) | Partly met | Owner | DELIVERY.md decision log |
| G13 | Windows CI and release workflows run on GitHub for the release commit | No | Pending (no remote yet) | Owner | Actions run links |
| G14 | Code signing | No | Not planned; installer documented as unsigned | Owner | README.md |
| G15 | Third-party licence notices shipped with the installer (T-28) | Yes, before public distribution | **Met on the build machine** | Engineering | VERIFICATION.md "Third-party notices" |

## Manual checks

Use the rc5 installer and confirm its SHA256 before starting:
`a94a92696cf5f001fb7326fb92628557f5907b0122383d3269d3aa4e26d47531`. Record every check in the
table at the end, including failures and anything confusing. A printable copy of these
steps is in the release package's `acceptance-kit` folder.

### M1 — Clean installation (G5)

1. On a Windows 10/11 account that has never had Python or Language Hangman, confirm
   `where python` finds nothing (or only the Microsoft Store stub).
2. Run the installer. Expect an "unknown publisher" SmartScreen warning (unsigned).
3. Start from the Start menu. Create a profile; confirm a short password and a mismatched
   confirmation are rejected. Sign out; confirm a wrong password is rejected; sign in.
4. Play a Standard session to the end, guessing both by typing and by clicking letter
   keys. Try guest practice; sign out; confirm the guest's progress is gone after restarting.
   Then start a German and a Spanish word list: the board shows that language's extra
   letters, and clicking one guesses it.
5. Open the program folder (`%LOCALAPPDATA%\Programs\LanguageHangman`) and confirm
   `THIRD-PARTY-NOTICES.txt` and the `licenses` folder are there and readable.

### M2 — Keyboard only (G6)

Unplug or ignore the mouse for the whole journey.

1. Sign-in: Tab reaches profile name, password and each button in order; the current
   button shows an **amber outline**; Enter or Space activates it; Enter in the password
   field signs in.
2. Practice setup: Tab reaches each dropdown (it turns **amber**); Up/Down change the value;
   Enter or Space opens the list, arrows move, Enter chooses, Escape closes. Changing Language
   updates the Words list, and Situation appears only for Travel cards.
3. During a round: the guess box has focus; typing a letter and Enter submits; Tab reaches
   "Submit guess", "Save and return home" and "Discard"; focused controls scroll into view.
   The A–Z letter keys are deliberately **not** in the Tab order (they repeat the typing
   route for mouse users): confirm Tab skips them, and that clicking one guesses that letter.
4. Escape returns home from any signed-in screen. Ctrl + (or Ctrl =) makes text larger;
   Ctrl − returns to standard; the setting is kept after restarting.
5. Settings: reach backup, restore, export, delete and diagnostics by keyboard; dialogs
   answer with Enter/Escape. Word cards: reach both dropdowns and scroll a word list.
6. Recovery window (after M4 step 2): Tab reaches every restore button, "Choose a backup
   file…", "Open data folder" and "Quit"; each scrolls into view; Escape closes the window.

### M3 — Display scaling and window size (G7)

For each of 100%, 125% and 150% (Settings › System › Display › Scale), sign out and back
in to Windows, then start the app:

1. The window fits on screen; the title bar is visible.
2. Resize to the smallest size allowed. On Home, Practice (setup and a round), a learning
   card, Reports, Word cards (travel cards and a word list), Settings and Help, no text or
   control is cut off at the right; the page scrolls where needed. In a round, check the
   whole board is usable: the figure, the letter tiles, the lives and every letter key.
   Include an Expert word list, which has the longest words and phrases.
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

Install the 1.0.0rc4 installer, create a profile and play a round through its UI, then run
the rc5 installer over it and sign in with the same profile: progress and any paused round
are still there.

### Record

| Check | Tester | Date | OS and scaling | Revision | Installer SHA256 | Result | Evidence / notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M1 | | | | f2bb6b9 | a94a9269…d47531 | Not run | |
| M2 | | | | f2bb6b9 | a94a9269…d47531 | Not run | |
| M3 100% | | | | f2bb6b9 | a94a9269…d47531 | Not run | |
| M3 125% | | | | f2bb6b9 | a94a9269…d47531 | Not run | |
| M3 150% | | | | f2bb6b9 | a94a9269…d47531 | Not run | |
| M4 | | | | f2bb6b9 | a94a9269…d47531 | Not run | |

## Release evidence index

| Item | Location | Identifier |
| --- | --- | --- |
| Source revision (installer) | branch `release/1.0` | `f2bb6b9` (later commits change documents, evidence, test wiring and the build script's logging only; nothing the installer bundles) |
| Windows installer (unsigned) | release package | `LanguageHangman-1.0.0rc5-Setup.exe`, 14,791,371 bytes, SHA256 `a94a92696cf5f001fb7326fb92628557f5907b0122383d3269d3aa4e26d47531` |
| Installed program | inside the installer | `LanguageHangman.exe` SHA256 `9de7b25420319c9c163dcf623ffb530ce48805c56a053accf50a1640bc1428b8` |
| Licence | `LICENSE`; installed as `LICENSE.txt` beside the program | MIT for the software; word content and icon not yet licensed |
| Third-party notices | `packaging/third-party/`; installed next to the program | 15 components, 12 licence texts and the notices file |
| Source archive | release package | see `SHA256SUMS.txt` in the release package |
| Build log | `docs/evidence/2026-11-01-rc5-f2bb6b9/build-output/` | `revision.txt` names the commit; the log itself does not (I-9) |
| Automated results | `docs/evidence/2026-11-01-rc5-f2bb6b9/checks/` | build commit: 194 passed; the first run's failure kept in `checks-first-run/`; final tree in `checks-final/`, with its earlier failed set in `checks-final-first-set/` |
| Word conversion | `scripts/build_level_words.py`, `docs/evidence/2026-11-01-rc5-f2bb6b9/level-list-conversion.txt` | 1,538 words kept, 62 rows left out |
| Defect reproductions (D-29, D-30, D-31, T-28) | `docs/evidence/2026-09-19-rc3-fd3b25a/defects/` | rc2 code vs `fd3b25a` |
| Installer validation | `docs/evidence/2026-11-01-rc5-f2bb6b9/installer-validation/` | steps 01–10, Inno Setup logs, screenshots |
| Installed smoke journey | `docs/evidence/2026-11-01-rc5-f2bb6b9/installed-smoke/` | 17 checks |
| Performance | `docs/evidence/2026-11-01-rc5-f2bb6b9/performance/` | rc4 and rc5 guess to redraw in one session, 5,000+ round profile, Word cards, start-up |
| Scaling | `docs/evidence/2026-11-01-rc5-f2bb6b9/scaling/` | round and recovery at three scalings, two text sizes |
| Demo recording | `docs/media/language-hangman-1.0.0rc5-demo.mp4` | 168 s, SHA256 `43ecaa2a95ce3f54a34e6ec934f20f0a0de317be628ac39c40d2d2f1b70394d2`; scripted run of `f2bb6b9` from a clean clone, slowed 1.3× for captions |
| rc4 and earlier evidence | `docs/evidence/2026-11-01-rc4-d543579/`, `…-rc3-fd3b25a/`, `…-rc2-4ad1e34/`, `…-baseline-16f3fc3/`, `…-m2-525c377/` | historical; see the I-4 note in the rc2 folder |
| Content review record | [CONTENT_REVIEW.md](CONTENT_REVIEW.md), [editorial-dispositions.json](editorial-dispositions.json) | 24/24 dispositioned for the cards; review not done; level lists not reviewed |
| Learner sessions | [USER_ACCEPTANCE.md](USER_ACCEPTANCE.md) | none run |

## Go / no-go record

| Date | Candidate | Decision | Basis | Decided by |
| --- | --- | --- | --- | --- |
| 2026-09-19 | 1.0.0rc2 (`4ad1e34`) | No-go for 1.0 final. Recommended: share rc2 as a tested release candidate for G5–G10. | G1–G4 met; G5–G12 and G15 pending | Recommendation by Claude Code; owner decision pending |
| 2026-09-19 | 1.0.0rc3 (`fd3b25a`) | No-go for 1.0 final. Recommended: give rc3 to the people running G5–G10; do not publish the installer until DEC-08 and DEC-14 are decided. | G1–G4 and G15 met on the build machine; G5–G12 pending; no open P0 or P1 defects; the independent review's blocker (D-30) fixed | Recommendation by Claude Code; **owner decision pending** |
| 2026-11-01 | 1.0.0rc4 (`d543579`) | **No-go for 1.0 final.** Recommended: give rc4 to the people running G5–G10; it supersedes rc3 for every purpose. | G1–G4, G15 and G16 met on the build machine; licence decided (MIT); G5–G11 and the remaining G12 decisions pending; no open P0 or P1 defects | Recommendation by Claude Code; **owner decision pending** |
| 2026-11-01 | 1.0.0rc5 (`f2bb6b9`) | **No-go for 1.0 final.** Recommended: give rc5, not rc4, to the people running G5–G10. The level lists reach learners unreviewed and are labelled so in the app. | G1–G4, G15 and G16 met on the build machine; G9 widened to 1,568 words and four languages; G5–G11 and the remaining G12 decisions pending; no open P0 or P1 defects | Recommendation by Claude Code; **owner decision pending** |

Promote to 1.0.0 only when G1–G12, G15 and G16 are met and the owner approves: change the version
in `src/__init__.py` (the installer and `VERSION` follow it), rebuild from the tagged commit
in a clean checkout, repeat G2–G4 and G15 on that artifact, and add a row above.
