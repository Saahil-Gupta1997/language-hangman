# Release acceptance — 1.0.0rc3

The version stays a release candidate until every **blocking** gate below has a named
person, a date and evidence. Automated tests and AI-run checks never substitute for the
manual, educator or learner gates, and those results must never be written by an AI or
filled in from automated output.

## Gates

| # | Gate | Blocking | Status | Owner | Evidence |
| --- | --- | --- | --- | --- | --- |
| G1 | P0 defects fixed with regression tests: D-01, D-02, D-03 (rc2) and D-30 (rc3) | Yes | **Met** | Engineering | VERIFICATION.md RQ-01..RQ-11 |
| G2 | Automated suite, lint, content check, release check on the candidate revision | Yes | **Met** (174 passed, 0 skipped, `fd3b25a`) | Engineering | evidence/…/checks |
| G3 | Installer built from the candidate commit in a clean checkout; SHA256 recorded | Yes | **Met** | Engineering | evidence/…/build-output |
| G4 | Install, upgrade from the previous release, beta import, recovery, uninstall on Windows | Yes | **Met on the build machine** (not a clean machine) | Engineering | VERIFICATION.md installer steps 1–10 |
| G5 | Clean Windows account without Python: install, launch, sign in, play | Yes | Pending | Owner | Manual record M1 |
| G6 | Keyboard-only journey, visible focus, Enter/Escape, text size | Yes | Pending (bindings and Tab traversal verified automatically) | Owner | Manual record M2 |
| G7 | Layout at real 100%, 125% and 150% and at the minimum window size, main and recovery windows | Yes | Pending (real 125% and emulated 100%/150% pass) | Owner | Manual record M3 |
| G8 | Recovery through the installed UI (damaged data, restore, sign in), Standard and Large text | Yes | Pending (installed-build path verified automatically) | Owner | Manual record M4 |
| G9 | Qualified review of all 30 teaching cards | Yes | Pending | Owner to appoint reviewer | CONTENT_REVIEW.md |
| G10 | Five learner sessions recorded | Yes | Pending | Owner to recruit | USER_ACCEPTANCE.md |
| G11 | Material issues from G5–G10 fixed and retested | Yes | Not started | Engineering + owner | DELIVERY.md register |
| G12 | Owner decisions: Review rule (DEC-06), feedback tone (DEC-07), licence (DEC-08), supported history (DEC-10), installer terms (DEC-14), intended learner (DEC-15) | Yes (DEC-08 and DEC-14 before publishing) | Pending | Owner | DELIVERY.md decision log |
| G13 | Windows CI and release workflows run on GitHub for the release commit | No | Pending (no remote yet) | Owner | Actions run links |
| G14 | Code signing | No | Not planned; installer documented as unsigned | Owner | README.md |
| G15 | Third-party licence notices shipped with the installer (T-28) | Yes, before public distribution | **Met on the build machine** | Engineering | VERIFICATION.md "Third-party notices" |

## Manual checks

Use the rc3 installer and confirm its SHA256 before starting:
`5e1b31077061dabd9cc764e07f8243f3054f526b8b1202181805b17022665f84`. Record every check in the
table at the end, including failures and anything confusing. A printable copy of these
steps is in the release package's `acceptance-kit` folder.

### M1 — Clean installation (G5)

1. On a Windows 10/11 account that has never had Python or Language Hangman, confirm
   `where python` finds nothing (or only the Microsoft Store stub).
2. Run the installer. Expect an "unknown publisher" SmartScreen warning (unsigned).
3. Start from the Start menu. Create a profile; confirm a short password and a mismatched
   confirmation are rejected. Sign out; confirm a wrong password is rejected; sign in.
4. Play a Standard session to the end. Try guest practice; sign out; confirm the guest's
   progress is gone after restarting.
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
   "Submit guess", "Save and return home" and "Discard"; focused controls scroll into view.
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
   card, Reports, Word cards, Settings and Help, no text or control is cut off at the right;
   the page scrolls where needed.
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

Install the 1.0.0rc2 installer, create a profile and play a round through its UI, then run
the rc3 installer over it and sign in with the same profile: progress and any paused round
are still there.

### Record

| Check | Tester | Date | OS and scaling | Revision | Installer SHA256 | Result | Evidence / notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M1 | | | | fd3b25a | 5e1b3107…665f84 | Not run | |
| M2 | | | | fd3b25a | 5e1b3107…665f84 | Not run | |
| M3 100% | | | | fd3b25a | 5e1b3107…665f84 | Not run | |
| M3 125% | | | | fd3b25a | 5e1b3107…665f84 | Not run | |
| M3 150% | | | | fd3b25a | 5e1b3107…665f84 | Not run | |
| M4 | | | | fd3b25a | 5e1b3107…665f84 | Not run | |

## Release evidence index

| Item | Location | Identifier |
| --- | --- | --- |
| Source revision (installer) | branch `release/1.0` | `fd3b25aa93d5b7de1fb7763aaecd5cb5898aa979` |
| Windows installer (unsigned) | release package | `LanguageHangman-1.0.0rc3-Setup.exe`, 14,717,048 bytes, SHA256 `5e1b31077061dabd9cc764e07f8243f3054f526b8b1202181805b17022665f84` |
| Installed program | inside the installer | `LanguageHangman.exe` SHA256 `87b319ecf21564aaf432f1b29f67775cf707e46d3647c1446a513e2008f86f5f` |
| Third-party notices | `packaging/third-party/`; installed next to the program | 15 components, 12 licence texts |
| Source archive | release package | see `SHA256SUMS.txt` in the release package |
| Build log | `docs/evidence/2026-09-19-rc3-fd3b25a/build-output/` | — |
| Automated results | `docs/evidence/2026-09-19-rc3-fd3b25a/checks/` | 174 passed, JUnit XML |
| Defect reproductions (D-29, D-30, D-31, T-28) | `docs/evidence/2026-09-19-rc3-fd3b25a/defects/` | rc2 code vs `fd3b25a` |
| Installer validation | `docs/evidence/2026-09-19-rc3-fd3b25a/installer-validation/` | steps 01–10, Inno Setup logs, screenshots |
| Installed smoke journey | `docs/evidence/2026-09-19-rc3-fd3b25a/installed-smoke/` | 16 checks |
| Performance | `docs/evidence/2026-09-19-rc3-fd3b25a/performance.txt` | 5,000-round profile, sample counts |
| Scaling | `docs/evidence/2026-09-19-rc3-fd3b25a/scaling/` | real 125%; emulated 100% and 150% |
| Demo recording | `docs/media/language-hangman-1.0.0rc3-demo.mp4` | 153 s, SHA256 `0052cfa654eb244ee84fd71e3ae94af43a111d30e6b4fa273016a57bf74801ba`; scripted run of `fd3b25a` from a clean worktree, slowed 1.3× for captions |
| rc2 and earlier evidence | `docs/evidence/2026-09-19-rc2-4ad1e34/`, `…-baseline-16f3fc3/`, `…-m2-525c377/` | historical; see the I-4 note in the rc2 folder |
| Content review record | [CONTENT_REVIEW.md](CONTENT_REVIEW.md), [editorial-dispositions.json](editorial-dispositions.json) | 24/24 dispositioned; review not done |
| Learner sessions | [USER_ACCEPTANCE.md](USER_ACCEPTANCE.md) | none run |

## Go / no-go record

| Date | Candidate | Decision | Basis | Decided by |
| --- | --- | --- | --- | --- |
| 2026-09-19 | 1.0.0rc2 (`4ad1e34`) | No-go for 1.0 final. Recommended: share rc2 as a tested release candidate for G5–G10. | G1–G4 met; G5–G12 and G15 pending | Recommendation by Claude Code; owner decision pending |
| 2026-09-19 | 1.0.0rc3 (`fd3b25a`) | **No-go for 1.0 final.** Recommended: give rc3 to the people running G5–G10; do not publish the installer until DEC-08 and DEC-14 are decided. | G1–G4 and G15 met on the build machine; G5–G12 pending; no open P0 or P1 defects; the independent review's blocker (D-30) fixed | Recommendation by Claude Code; **owner decision pending** |

Promote to 1.0.0 only when G1–G12 and G15 are met and the owner approves: change the version
in `src/__init__.py` (the installer and `VERSION` follow it), rebuild from the tagged commit
in a clean checkout, repeat G2–G4 and G15 on that artifact, and add a row above.
