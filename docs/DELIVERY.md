# Delivery log — Language Hangman Desktop 1.0

Project-management record for taking 1.0.0rc1 to a portfolio-ready 1.0: register, RAID,
decisions, AI assistance and milestone updates. Test results are in
[VERIFICATION.md](VERIFICATION.md); gates and sign-off in [ACCEPTANCE.md](ACCEPTANCE.md).

Status values: **Open**, **Fixed** (code changed, automated evidence), **Verified**
(native or installed evidence), **Pending owner** (needs a person or decision outside
engineering), **Deferred** (accepted for a later release).

## Source revisions

| Revision | Meaning |
| --- | --- |
| `023f2bd` (master) | v1.0.0-beta working copy, snapshotted before the upgrade |
| `5a41404` | 1.0.0rc1 exactly as received (zip SHA256 `0510a1a0…fe364`) |
| `16f3fc3` | rc1 + post-review fixes R-01..R-03; **baseline for this delivery** |
| `4ad1e34` | 1.0.0rc2 release candidate (installer `2fc27de7…58dc95` built from this commit) |
| `8621ff3` | rc2 documentation and evidence; rc2 source archive (tag `v1.0.0rc2`) |
| `8e9e61d`, `942c780`, `3004976`, `8e3b90f` | rc3 fixes: D-30, D-31, D-29, T-28 |
| `fd3b25a` | **1.0.0rc3 release candidate** (installer `5e1b3107…665f84` built from this commit) |
| later commits | documentation and evidence only; no application change (check with `git diff fd3b25a -- src desktop_app.py packaging scripts tests`) |

## Defect and task register

| ID | Pri | Title | Status | Evidence |
| --- | --- | --- | --- | --- |
| R-01 | P0 | Crash on every signed-in screen (pack/grid mix) | Verified | `16f3fc3`; smoke, installed smoke |
| R-02 | P0 | `events.log` held open; Windows cleanup failed | Verified | smoke temp folder removed |
| R-03 | P1 | Text-size change raised TclError after dropdowns | Verified | GUI scenario; smoke |
| D-01 | P0 | Fresh profile could start Review with an unseen word | Verified | `d2e696f`; RQ-01..03 |
| D-02 | P0 | Legacy vocabulary reachable from desktop practice | Verified | `d2e696f`; RQ-05/06; installer step 7 (rc3) |
| D-03 | P0 | Corrupt live database blocked start-up and restore | Verified (manual UI pass pending, G8) | `525c377`; RQ-07..11; installer steps 8–9 (rc3) |
| T-04 | P0 | Build and validate the Windows release | Verified on the build machine for rc3; clean machine and manual checks (G5–G8) pending owner | VERIFICATION.md installer steps 1–10 |
| T-05 | P0 | Content and learner acceptance | Pending owner (24/24 warnings dispositioned; review kit and session kit ready) | CONTENT_REVIEW.md, USER_ACCEPTANCE.md |
| T-06 | P1 | Privacy-safe failure diagnostics | Fixed | RQ-19 |
| D-07 | P1 | Automatic backup failure stopped start-up (`FileExistsError`) | Fixed | RQ-20 |
| T-08 | P1 | Performance baseline | Done; supported history needs owner agreement (DEC-10) | performance.txt |
| T-09 | P1 | Repository clarity (metadata, legacy labels, versions, dependencies, licence, provenance) | Done; licence pending owner (DEC-08) | `05eef7a`; CONTENT_REVIEW.md |
| T-10 | P1 | TPM evidence | Done | this file, VERIFICATION.md, ACCEPTANCE.md, ARCHITECTURE.md |
| D-11 | P2 | Legacy tests wrote `.session_secret` into real app data | Fixed | `tests/conftest.py` |
| D-12 | P2 | "Why this word" showed wrong legacy reason text | Fixed | GUI and unit tests |
| T-13 | P2 | GUI not exercised in PR CI | Fixed in workflow; not yet run on GitHub (no remote) | `.github/workflows/ci.yml` |
| T-14 | P2 | Line endings varied with checkout settings | Fixed | `.gitattributes` |
| D-15 | P3 | Easy mode shows two distinct clues (synonym field is empty by design) | Accepted: no screen promises three clues; README states two | — |
| T-16 | P3 | Black configured but not enforced (15 files differ) | Deferred; all new and changed code is formatted | — |
| D-17 | P2 | Feedback lines mocked the learner or relied on idioms | Fixed; tone confirmation pending owner (DEC-07) | `25aebde` |
| D-18 | P1 | Screenshot helper copied a screen region (could record other programs) | Fixed | `src/desktop/capture.py`; occlusion test |
| D-19 | P3 | Destroyed windows left timers pending ("invalid command name" noise) | Fixed (9 lines → 0) | `release_window` |
| D-20 | P2 | Smoke evidence listed fixed text, not results | Fixed | `desktop-smoke.json` |
| D-21 | P1 | Build script failed when its log was captured; could not find a single Inno Setup install | Fixed | `03453ae`, `d8f49aa` |
| D-22 | P1 | Window 167 px taller than a 1080p screen at 150% | Fixed | emulated scaling; GUI scenario |
| D-23 | P1 | Keyboard focus could land below the visible area | Fixed | GUI scenario |
| D-24 | P1 | Dropdowns (situation, difficulty, rounds, focus, text size) were mouse-only | Fixed; real keyboard pass pending (G6) | GUI scenario |
| D-25 | P3 | Text size needed Ctrl+Shift+= | Fixed (Ctrl+=, numeric keypad) | GUI scenario |
| D-26 | P2 | Intermittent Tk start-up failure in the test process | Fixed in tests; product unaffected (see VERIFICATION.md) | `4ad1e34` |
| D-27 | P3 | Logging kept a handler for a different data folder | Fixed | `4ad1e34` |
| T-28 | P1 | Installer shipped no third-party licence notices | **Verified** (build machine): 15-component inventory and 12 licence texts next to the program; the build fails if a shipped file is not covered; installed folder checked | `8e3b90f`; rc3 `defects/T-28…`, `installer-validation/04…` |
| D-29 | P2 | `release-check` scanned inside `.git`, so a clone on a `release/…` branch failed | **Verified**: clean in an ordinary clone, a worktree and the extracted source archive; genuine artifacts still reported | `3004976`; rc3 `defects/D-29…` |
| D-30 | **P0** | Restore: if moving the second journal side file failed, the first stayed in `backups` while the message said the data was unchanged; a failed put-back raised a raw error | **Verified** (fault-injection tests; installed restore path re-run). Every move is recorded at once and put back; a failed put-back gives stage `rollback`, names each file's location and the safety copy, and no longer claims "unchanged" | `8e9e61d`; rc3 `defects/D-30…` |
| D-31 | P1 | Fixed text-wrap widths clipped the recovery instructions below the default window width, and body text by 10 px at the minimum size with Large text; the recovery window ignored the saved text size | **Verified** (automated at real 125% and emulated 100%/150%; installed build at real 125%); real 100%/150% and keyboard pending (G6, G7) | `942c780`; rc3 `defects/D-31…`, `scaling/` |

## RAID log

| ID | Type | Description | Owner | Closure condition | Status |
| --- | --- | --- | --- | --- | --- |
| RK-1 | Risk | Content errors reach learners (AI-assisted writing, no educator yet) | Owner | G9 review done, corrections applied and retested | Open |
| RK-2 | Risk | Keyboard/screen-reader users blocked: CustomTkinter draws controls on canvases that Windows screen readers generally cannot read | Owner | G6 passed; screen-reader limitation stated in README | Open (limitation documented) |
| RK-3 | Risk | SmartScreen "unknown publisher" warning deters installers | Owner | Signing certificate or documented expectation | Accepted: documented |
| RK-4 | Risk | Real 100%/150% scaling differs from emulation | Owner | G7 passed | Open |
| RK-5 | Risk | CustomTkinter 5.2.2 internals patched (dropdown leak, timers) break on upgrade | Engineering | Workarounds skip themselves if internals move; re-test on any upgrade | Mitigated |
| A-1 | Assumption | Intended learner reads simple English (about CEFR A2): a proposed profile, not validated | Owner | DEC-15 confirmed; reviewer agrees the cards suit it (G9) | Pending owner |
| A-2 | Assumption | One learner per Windows account; a few profiles per computer | Owner | DEC-10 agreed | Pending owner |
| I-1 | Issue | Validated installer `fd93a4d3…` deleted by a clean-up step before archiving | Engineering | Rebuilt from the same commit and all installer checks re-run (`2fc27de7…`); artifacts now copied out immediately after building | Closed |
| I-2 | Issue | Commit `05eef7a` made after a test run whose failure a pipeline masked | Engineering | Cause (D-26) fixed; test runs now check pytest's exit code | Closed |
| I-3 | Issue | A screenshot captured another program's window (D-18) | Engineering | Image deleted, never committed; window-only capture proven | Closed |
| DP-1 | Dependency | Qualified content reviewer | Owner | Reviewer appointed | Open |
| DP-2 | Dependency | Five learners matching the intended profile | Owner | Sessions scheduled | Open |
| DP-3 | Dependency | GitHub repository for CI and release workflows | Owner | Repository published and workflows run | Open |
| RK-6 | Risk | Distributing without third-party notices breaches bundled licences | Owner + engineering | T-28 closed | Closed (rc3) |
| I-4 | Issue | rc2 installed-app screenshots were cropped to 80%: the capture helper was not DPI aware (the published `docs/media/recovery.png` looked clipped) | Engineering | DPI-aware helper; rc3 captures complete; rc2 folder annotated | Closed |
| I-5 | Issue | Two rc2 statements were inaccurate: "no control clipped horizontally" (10 px clipping existed at minimum size with Large text) and "every operation under one second" (start-up with the day's first backup took 1.26 s) | Engineering | Measured check added (D-31); performance restated with figures | Closed |
| RK-7 | Risk | Python's licence asks distributors of the Microsoft Distributable Code (VCRUNTIME140.dll) to have end users agree to terms at least as protective as Microsoft's; the installer shows no licence terms | Owner | DEC-14 decided | Open |
| DP-4 | Dependency | Clean Windows machine or account without Python | Owner | G5 run | Open |

## Decision log

"Retrospective" entries explain choices already present in the repository when this work
began. They are inferred from the code and documents, not from the owner, and need the
owner's confirmation before they are quoted as the owner's reasoning.

| ID | Decision | Rationale | Made by | Status |
| --- | --- | --- | --- | --- |
| DEC-01 | Native desktop app instead of the browser prototype | Offline, single-user, no server or cookies to secure; one install for learners | Retrospective (rc1 README and code) | Owner to confirm |
| DEC-02 | SQLite with transactions per learner action | Local, file-based, atomic, easy to back up and restore | Retrospective | Owner to confirm |
| DEC-03 | Explainable rules, no machine learning | Predictable, testable behaviour for a small corpus | Retrospective | Owner to confirm |
| DEC-04 | 30 curated English words; other languages dropped | rc1 excluded the older corpus; an earlier review had found 42 misspelled French/Spanish words there. Quality over breadth (inferred) | Retrospective | Owner to confirm |
| DEC-05 | Keep legacy browser code and banks for history and regression tests only | Imported progress still reports; the desktop reuses the game engine | Retrospective | Owner to confirm |
| DEC-06 | Review = all active review items for curated words in the situation, due first, once per session | Keeps Review usable on the day of practice (due-only would wait a day); matches rc1's fallback but as one consistent rule | Claude Code (this delivery) | **Owner to confirm** |
| DEC-07 | Replace mocking feedback lines with plain encouraging English | Learners of English; sarcasm and idioms confuse and may offend | Claude Code | **Owner to confirm tone** |
| DEC-08 | Licence | Proposal: MIT for code; content licence (e.g. CC BY 4.0) only after provenance is confirmed | Proposal | **Owner decision needed before publishing** |
| DEC-09 | Version the new candidate as 1.0.0rc2 | It differs from the rc1 build; still a release candidate until gates close | Claude Code | Done |
| DEC-10 | Supported history: up to 5 profiles, 5,000 completed rounds per profile | Measured on the build machine (rc3): in-process operations ≤ 386 ms at the 95th percentile; start-up 0.78–0.84 s, 1.65 s with the day's first backup | Proposal | **Owner to agree** |
| DEC-11 | Minimum window 800×600 logical pixels | Fits 1080p at 150% scaling | Claude Code | Done |
| DEC-12 | GUI tests run one per process | Removes a test-harness-only Tcl interaction (D-26) | Claude Code | Done |
| DEC-13 | Build locally from a clean checkout; GitHub workflows prepared but not yet run | No remote repository available | Claude Code | Done |
| DEC-14 | Whether the installer shows licence terms to end users (see RK-7), and which | Depends on the project licence (DEC-08) | — | **Owner decision needed before public distribution** |
| DEC-15 | Intended learner: reads short, simple English (about CEFR A2), preparing for travel | A proposed profile for reviewing content and recruiting learners; not a certification that the content is A2 | Proposal (CONTENT_REVIEW.md) | **Owner to confirm; reviewer to test** |
| DEC-16 | Version the corrected candidate 1.0.0rc3 | Code changed after rc2 (D-30, D-31, D-29, T-28); still a candidate until gates close | Claude Code | Done |
| DEC-17 | Generate notices from the build environment and check coverage at build time | Keeps the notices true to what ships; a new file or version fails the build | Claude Code | Done |

## How AI assistance was used and verified

- **Origin.** The beta and rc1 were built with AI coding assistance (the beta README names
  Codex). This delivery was carried out by Claude Code (Anthropic) working on the owner's
  computer at the owner's direction.
- **What the AI did.** Reproduced defects before changing code; wrote fixes, regression
  tests and documentation; built and installed the Windows release; measured performance;
  recorded the demo; prepared the content-review and learner-session kits.
- **How it was checked.** Every defect was reproduced first and re-run after the fix;
  results are tied to commits and recorded with the commands used; the installer was
  exercised by installing, upgrading, recovering and uninstalling it; screenshots were
  checked to contain only the application window. Hypotheses that turned out wrong
  (D-26's first two theories) were recorded and their code removed.
- **Where the AI's own evidence was wrong.** Incidents I-1 to I-5 record them, including
  cropped screenshots published with rc2 (I-4) and two rc2 claims that measurement later
  contradicted (I-5). An independent review found the D-30 rollback defect in AI-written
  code; fault-injection tests now cover it.
- **What the AI must not do.** Fill in educator, learner or manual-test results; mark a gate
  passed without evidence. Those records remain empty until people complete them.
- **Owner review.** All code, content and decisions above are subject to the owner's review;
  items marked "Owner to confirm" are not settled.

## Milestone updates

### M1 — Baseline and defect reproduction

Revision `16f3fc3`: 134 passed, 0 skipped, 1 third-party warning; Ruff clean; native smoke
passed; Black reports 15 files (T-16). D-01, D-02 and D-03 reproduced
(`evidence/2026-09-19-baseline-16f3fc3/`). The historical rc1 figure (133 passed, 1 skipped)
differs because the R-03 GUI test runs rather than skips on a Windows desktop.

### M2 — P0 defects fixed

D-01/D-02 in `d2e696f`, D-03 in `525c377`, plus D-07, T-06, D-11, D-12, D-20, T-14.
158 passed ×3 on a clean checkout; reproductions no longer reproduce. Incident I-3.

### M3 — Windows artifact built and validated

1.0.0rc2 candidate `4ad1e34`: keyboard (D-23..D-25), screen fit (D-22), feedback tone (D-17),
build-script fixes (D-21), test isolation (D-26). Installer `2fc27de7…58dc95` built from a
clean checkout; install, genuine upgrade from rc1, beta import, recovery and uninstall all
verified; installed smoke 16/16 without Python on `PATH`. Incidents I-1 and I-2.
Dependencies: clean-machine and manual checks (owner).

### M4 — Content and learner acceptance (prepared, pending people)

24/24 editorial warnings dispositioned (7 notes rewritten). Reviewer worksheet, intended-
learner definition and five-session protocol prepared. No review or session has taken place.

### M5 — Documentation and evidence reconciled

README, architecture, verification (with traceability), acceptance, this log, release notes
and legacy notes updated; evidence under `docs/evidence/`; demo in `docs/media/`.

### M6 — Release decision

No-go for 1.0 final; recommendation to share 1.0.0rc2 as a tested release candidate
(ACCEPTANCE.md go/no-go record). Owner decision pending.

### M7 — rc3 baseline: review findings reproduced

The independent review of rc2 reported a release blocker (D-30) and the recovery-window
clipping (D-31); D-29 and T-28 were already open. On `8621ff3`: D-30 reproduced with a
fault-injection script, D-31 by measuring label widths at the minimum size, D-29 in an
ordinary clone, T-28 by checking the rc2 program folder (12 notices missing). Two rc2
evidence problems found along the way (I-4, I-5).

### M8 — Fixes

D-30 `8e9e61d`, D-31 `942c780`, D-29 `3004976`, T-28 `8e3b90f`, version `fd3b25a`. Each new
regression test fails on the rc2 code and passes on the fix. 174 passed, 0 skipped.

### M9 — rc3 artifact built and validated (build machine)

Installer `5e1b3107…665f84` built from `fd3b25a` in a fresh clone; notices check 978 files,
0 problems. Upgrade from rc2 with data created by rc2 itself (byte-identical), installed
notices (980 files, 0 problems), installed smoke 16/16 without Python, beta import,
recovery window at real 125% (Standard/Large, opening and minimum size), restore, uninstall
with data preserved. Performance, scaling screenshots and demo re-recorded on `fd3b25a`.
Dependencies: clean machine, real 100%/150%, keyboard, content review, learner sessions,
owner decisions, GitHub repository.

### M10 — Documents and release decision (rc3)

README, release notes, checklist, verification, acceptance, architecture, content review and
this log updated; evidence in `evidence/2026-09-19-rc3-fd3b25a/`. Recommendation: no-go for
1.0 final; share 1.0.0rc3 with the people running G5–G10. Owner decision pending.
