# Release acceptance — 1.0.0rc2

The version stays a release candidate until every **blocking** gate below has a named
person, a date and evidence. Automated tests and AI-run checks never substitute for the
manual, educator or learner gates, and those results must never be written by an AI or
filled in from automated output.

## Gates

| # | Gate | Blocking | Status | Owner | Evidence |
| --- | --- | --- | --- | --- | --- |
| G1 | P0 defects D-01, D-02, D-03 fixed with regression tests | Yes | **Met** | Engineering | VERIFICATION.md RQ-01..RQ-11 |
| G2 | Automated suite, lint, content check, release check on the candidate revision | Yes | **Met** (163 passed, 0 skipped) | Engineering | evidence/…/checks |
| G3 | Installer built from the candidate commit; SHA256 recorded | Yes | **Met** | Engineering | evidence/…/build-output |
| G4 | Install, genuine upgrade, beta import, recovery, uninstall on Windows | Yes | **Met on the build machine** | Engineering | VERIFICATION.md installer steps 1–8 |
| G5 | Clean Windows account without Python: install, launch, sign in, play | Yes | Pending | Owner | Manual record M1 |
| G6 | Keyboard-only journey, visible focus, Enter/Escape, text size | Yes | Pending (bindings verified automatically) | Owner | Manual record M2 |
| G7 | Layout at real 100%, 125%, 150% and the minimum window size | Yes | Pending (125% real and 100/150% emulated pass) | Owner | Manual record M3 |
| G8 | Recovery journey through the installed UI (corrupt data, restore, sign in) | Yes | Pending (installed-build path verified automatically) | Owner | Manual record M4 |
| G9 | Qualified review of all 30 teaching cards | Yes | Pending | Owner to appoint reviewer | CONTENT_REVIEW.md |
| G10 | Five learner sessions recorded | Yes | Pending | Owner to recruit | USER_ACCEPTANCE.md |
| G11 | Material issues from G5–G10 fixed and retested | Yes | Not started | Engineering + owner | DELIVERY.md register |
| G12 | Owner decisions: licence, feedback tone, Review rule, supported history size | Yes (licence before publishing) | Pending | Owner | DELIVERY.md decision log |
| G13 | Windows CI and release workflows run on GitHub for the release commit | No | Pending (no remote yet) | Owner | Actions run links |
| G14 | Code signing | No | Not planned; installer documented as unsigned | Owner | README.md |
| G15 | Third-party licence notices shipped with the installer (T-28) | Yes, before public distribution | Open | Engineering + owner | Notices file in the installed folder |

## Manual checks

Use the published installer and confirm its SHA256 before starting. Record every check in
the table at the end, including failures and anything confusing.

### M1 — Clean installation (G5)

1. On a Windows 10/11 account that has never had Python or Language Hangman, confirm
   `where python` finds nothing (or only the Microsoft Store stub).
2. Run the installer. Expect an "unknown publisher" SmartScreen warning (unsigned).
3. Start from the Start menu. Create a profile; confirm a short password and a mismatched
   confirmation are rejected. Sign out; confirm a wrong password is rejected; sign in.
4. Play a Standard session to the end. Try guest practice; sign out; confirm the guest's
   progress is gone after restarting.

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

### M3 — Display scaling and window size (G7)

For each of 100%, 125% and 150% (Settings › System › Display › Scale), sign out and back
in to Windows, then start the app:

1. The window fits on screen; the title bar is visible.
2. Resize to the smallest size allowed. On Home, Practice (setup and a round), a learning
   card, Reports, Word cards, Settings and Help, no text or control is cut off; the page
   scrolls where needed.
3. Repeat step 2 with Large text.

### M4 — Recovery through the installed UI (G8)

1. Settings › Create full backup; save it somewhere you can find.
2. Close the app. In `%LOCALAPPDATA%\LanguageHangman`, rename `app.db` to `app.db.old` (this
   keeps the original), then create a text file containing a few words and name it
   `app.db`. (An *empty* file is not enough: SQLite treats it as a new, valid database.)
3. Start the app: the recovery window appears instead of an error.
4. Choose the backup (or the newest automatic backup), confirm, and sign in: profiles and
   progress are back; `backups\quarantine-…` contains the damaged file.

### Upgrade (optional repeat of G4)

Install the previous installer, create a profile and some progress through its UI, then
run the new installer over it and sign in with the same credentials. Note: rc1's UI crashes
after sign-in (fixed in rc2), so on a real machine use an older build's data via Restore.

### Record

| Check | Tester | Date | OS and scaling | Revision | Installer SHA256 | Result | Evidence / notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M1 | | | | 4ad1e34 | 2fc27de7…58dc95 | Not run | |
| M2 | | | | 4ad1e34 | 2fc27de7…58dc95 | Not run | |
| M3 100% | | | | 4ad1e34 | 2fc27de7…58dc95 | Not run | |
| M3 125% | | | | 4ad1e34 | 2fc27de7…58dc95 | Not run | |
| M3 150% | | | | 4ad1e34 | 2fc27de7…58dc95 | Not run | |
| M4 | | | | 4ad1e34 | 2fc27de7…58dc95 | Not run | |

## Release evidence index

| Item | Location | Identifier |
| --- | --- | --- |
| Source revision | branch `release/1.0` | `4ad1e34bf1dca5286e3722152a3fbc505a05af44` |
| Windows installer (unsigned) | release package | `LanguageHangman-1.0.0rc2-Setup.exe`, 14,678,690 bytes, SHA256 `2fc27de78a94aca7c96637dafc70b15ff707349b403c878bfd050ad79a58dc95` |
| Installed program | inside the installer | `LanguageHangman.exe` SHA256 `224bf1cc8adb8c273241f69877d6fb6776cb0e1d2fef371d1f707b0bb9e511f2` |
| Source archive | release package | see `SHA256SUMS.txt` in the release package |
| Build log | `docs/evidence/2026-09-19-rc2-4ad1e34/build-output/` | — |
| Automated results | `docs/evidence/2026-09-19-rc2-4ad1e34/checks/` | 163 passed, JUnit XML |
| Installer validation | `docs/evidence/2026-09-19-rc2-4ad1e34/installer-validation/` | steps 01–08, Inno Setup logs, screenshots |
| Installed smoke journey | `docs/evidence/2026-09-19-rc2-4ad1e34/installed-smoke/` | 16 checks |
| Performance | `docs/evidence/2026-09-19-rc2-4ad1e34/performance.txt` | 5,000-round profile |
| Scaling | `docs/evidence/2026-09-19-rc2-4ad1e34/scaling/` | emulated 100/150%, real 125% |
| Demo recording | `docs/media/language-hangman-1.0.0rc2-demo.mp4` | 153 s, SHA256 `90471585468a0480c377c6c6a93e380773bd950503ec283aea5eaa89c5164de5`; scripted run of `4ad1e34` from a clean checkout, slowed 1.3× for captions |
| Baseline and milestone evidence | `docs/evidence/2026-09-19-baseline-16f3fc3/`, `…-m2-525c377/` | defect reproductions |
| Content review record | [CONTENT_REVIEW.md](CONTENT_REVIEW.md), [editorial-dispositions.json](editorial-dispositions.json) | 24/24 dispositioned |
| Learner sessions | [USER_ACCEPTANCE.md](USER_ACCEPTANCE.md) | none run |

## Go / no-go record

| Date | Candidate | Decision | Basis | Decided by |
| --- | --- | --- | --- | --- |
| 2026-09-19 | 1.0.0rc2 (`4ad1e34`) | **No-go for 1.0 final.** Recommended: share rc2 as a tested release candidate for G5–G10. | G1–G4 met; G5–G12 and G15 pending; no open P0 defects; one open P1 (T-28, notices) blocks public distribution only; one open P2 in tooling (D-29) | Recommendation by Claude Code; **owner decision pending** |

Promote to 1.0.0 only when G1–G12 and G15 are met: change the version in `src/__init__.py` (the
installer and `VERSION` follow it), rebuild from the tagged commit, repeat G2–G4, and add a
row above.
