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
| `fd3b25a` | 1.0.0rc3 release candidate (installer `5e1b3107…665f84` built from this commit) |
| `944fe27` | rc3 documentation and evidence; rc3 source archive (tag `v1.0.0rc3`) |
| `849d1e1`, `8019a84`, `d543579` | rc4: UI redesign (T-29), MIT licence and validation tooling, board performance (D-32) |
| `d543579` | 1.0.0rc4 release candidate (installer `abb0cf94…ebcd3c` built from this commit) |
| `f5ac6a2`, `21cee81`, `06fc02c`, `7c425fd` | tests, documents and release tooling only; nothing the installer bundles |
| `801cdf4` | rc4 documentation and evidence; rc4 source archive (tag `v1.0.0rc4`) |
| `9c9ffbb`, `d85c109` | the owner's rc4 decisions, record corrections and the rc3/rc4 re-measure (I-9); documents and evidence only |
| `f2bb6b9` | **1.0.0rc5 release candidate** (installer `a94a9269…d47531` built from this commit): original feedback lines and level word lists |
| later commits | documents, evidence, test wiring (I-11) and the build script's logging; no application change (check with `git diff f2bb6b9 -- src desktop_app.py packaging`) |

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
| D-17 | P2 | Feedback lines mocked the learner or relied on idioms | **Reversed by the owner in rc5** (DEC-07): the original lines are back, deliberately | `25aebde`, `f2bb6b9` |
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
| T-28 | P1 | Installer shipped no third-party licence notices | **Verified** (build machine): 15-component inventory, 11 licence texts and the notices file next to the program (rc3; rc4 has 12 texts); the build fails if a shipped file is not covered; installed folder checked | `8e3b90f`; rc3 `defects/T-28…`, `installer-validation/04…` |
| D-29 | P2 | `release-check` scanned inside `.git`, so a clone on a `release/…` branch failed | **Verified**: clean in an ordinary clone, a worktree and the extracted source archive; genuine artifacts still reported | `3004976`; rc3 `defects/D-29…` |
| D-30 | **P0** | Restore: if moving the second journal side file failed, the first stayed in `backups` while the message said the data was unchanged; a failed put-back raised a raw error | **Verified** (fault-injection tests; installed restore path re-run). Every move is recorded at once and put back; a failed put-back gives stage `rollback`, names each file's location and the safety copy, and no longer claims "unchanged" | `8e9e61d`; rc3 `defects/D-30…` |
| T-29 | P2 | The UI read as a form: the word was a line of underscores among same-weight paragraphs, lives were a sentence, and seven identical buttons served as navigation, so no screen showed its primary action (owner feedback, 2026-11-01) | **Done**: game board (figure, letter tiles, lives, A–Z keys), slim navigation with the current page marked, primary/secondary/quiet/danger button weights, stat tiles, design tokens and the system UI font | `849d1e1`, `d543579`; rc4 `scaling/`, `media/` |
| D-32 | P1 | The redesigned round screen rebuilt about 160 CustomTkinter widgets after every guess: 1.13 s median from guess to redrawn screen, against 285 ms in rc3 (neither figure has a raw record; rc3 measured again at 273–349 ms, I-9) | **Fixed**: the board updates in place while a round continues, and is drawn on one canvas instead of about 55 widgets. 39 ms median, p95 606 ms (the guess that completes a round and changes the screen); measured again the same day at 44–56 ms and 763–789 ms (I-9) | `d543579`; rc4 `performance.txt` |
| T-30 | P1 | Restore the older app's word database: four languages, five levels, three clues per word (owner request, 2026-11-01, DEC-22) | **Done, content unreviewed**: 1,538 words as a separate pack; Language and Words in Practice setup; accent keys; phrases; level learning card; word lists; "not yet reviewed" labels. Accuracy is a G9 matter | `f2bb6b9`; `tests/test_level_words.py`; rc5 `level-list-conversion.txt` |
| T-31 | P2 | Restore the 40 original feedback lines word for word (owner request, 2026-11-01, DEC-07) | **Done** | `f2bb6b9`; `tests/test_level_words.py` |
| D-31 | P1 | Fixed text-wrap widths clipped the recovery instructions below the default window width, and body text by 10 px at the minimum size with Large text; the recovery window ignored the saved text size | **Verified** (automated at real 125% and emulated 100%/150%; installed build at real 125%); real 100%/150% and keyboard pending (G6, G7) | `942c780`; rc3 `defects/D-31…`, `scaling/` |

## RAID log

| ID | Type | Description | Owner | Closure condition | Status |
| --- | --- | --- | --- | --- | --- |
| RK-1 | Risk | Content errors reach learners (AI-assisted writing, no educator yet). Larger since rc5: 1,538 unreviewed words in four languages, with a repeat rate that shows the sheet was not cleaned (56 rows) and at least one fragment (German `Quanten-`). The app labels the lists "not yet reviewed" | Owner | G9 review done, corrections applied and retested | Open |
| RK-8 | Risk | Reviewing 1,568 words in four languages needs several reviewers and far longer than the 2 hours estimated for the 30 cards, so G9 may hold up 1.0. The owner decided that all four languages must pass before 1.0 (DEC-23), so 1.0 waits for all four reviews | Owner | Reviewers appointed for all four languages and their reviews finished | Open |
| RK-9 | Risk | The restored lines mock the learner and use idioms, chosen deliberately by the owner. G10 learners read simple English and may be confused or put off | Owner | G10 observed; the owner reviews what learners say | Open |
| RK-2 | Risk | Keyboard/screen-reader users blocked: CustomTkinter draws controls on canvases that Windows screen readers generally cannot read | Owner | G6 passed; screen-reader limitation stated in README | Open (limitation documented) |
| RK-3 | Risk | SmartScreen "unknown publisher" warning deters installers | Owner | Signing certificate or documented expectation | Accepted: documented |
| RK-4 | Risk | Real 100%/150% scaling differs from emulation | Owner | G7 passed | Open |
| RK-5 | Risk | CustomTkinter 5.2.2 internals patched (dropdown leak, timers) break on upgrade | Engineering | Workarounds skip themselves if internals move; re-test on any upgrade | Mitigated |
| A-1 | Assumption | Intended learner reads simple English (about CEFR A2): a proposed profile, not validated | Owner | DEC-15 confirmed; reviewer agrees the cards suit it (G9) | Pending owner |
| A-2 | Assumption | One learner per Windows account; a few profiles per computer | Owner | DEC-10 agreed | Pending owner |
| I-1 | Issue | Validated installer `fd93a4d3…` deleted by a clean-up step before archiving | Engineering | Rebuilt from the same commit and all installer checks re-run (`2fc27de7…`); artifacts now copied out immediately after building | Closed |
| I-2 | Issue | Commit `05eef7a` made after a test run whose failure a pipeline masked | Engineering | Cause (D-26) fixed; test runs now check pytest's exit code | Closed |
| I-3 | Issue | A screenshot captured another program's window (D-18) | Engineering | Image deleted, never committed; window-only capture proven | Closed |
| DP-1 | Dependency | Qualified content reviewers: one each for English, Spanish, Italian and German | Owner | All four appointed | Open |
| DP-2 | Dependency | Five learners matching the intended profile | Owner | Sessions scheduled | Open |
| DP-3 | Dependency | GitHub repository for CI and release workflows | Owner | Repository published and workflows run | Open |
| RK-6 | Risk | Distributing without third-party notices breaches bundled licences | Owner + engineering | T-28 closed | Closed (rc3) |
| I-4 | Issue | rc2 installed-app screenshots were cropped to 80%: the capture helper was not DPI aware (the published `docs/media/recovery.png` looked clipped) | Engineering | DPI-aware helper; rc3 captures complete; rc2 folder annotated | Closed |
| I-5 | Issue | Two rc2 statements were inaccurate: "no control clipped horizontally" (10 px clipping existed at minimum size with Large text) and "every operation under one second" (start-up with the day's first backup took 1.26 s) | Engineering | Measured check added (D-31); performance restated with figures | Closed |
| RK-7 | Risk | Python's licence asks distributors of the Microsoft Distributable Code (VCRUNTIME140.dll) to have end users agree to terms at least as protective as Microsoft's; the installer ships LICENSE.txt and the notices but shows no terms during setup. rc4 stays that way by the owner's choice (2026-11-01, DEC-14). The licence wording names external end users, so outside testers may already count | Owner | DEC-14 decided | Open |
| I-6 | Issue | The validation tooling lived only in a temporary folder and was cleaned after six weeks, with the beta database and the performance dataset: the release could not be revalidated without rewriting it | Engineering | Rewritten into `scripts/validation/` with a README, including the beta database builder and the guess-to-redraw measurement, which first stayed in scratch (I-8). The installer steps themselves are still run by hand from the README | Closed |
| I-8 | Issue | The first rc4 record was wrong: it claimed 175 passed on `d543579` (the clean run was 174 passed, 1 failed), named archive commit `06fc02c` for checks run on `21cee81`, said two scratch-only tools were in the repository, left placeholders in this log, and left rc3 details in current documents. The handover repeated the first of these and an unsupported remark that the rc2 and rc3 demos shared a flaw | Engineering | Record audited against the runs; final tree tested three times in a clean clone; remark withdrawn | Closed |
| I-7 | Issue | The UI redesign was measured only after the rc4 installer had been built and validated, so the artifact had to be discarded and rebuilt | Engineering | Performance measured before packaging in future candidates (RELEASE_CHECKLIST step 2) | Closed |
| I-9 | Issue | An audit of the rc4 record on 2026-11-01 found: the D-32 row and M11 gave 41 ms (D-32 also p95 640 ms), not `performance.txt`'s 39 ms and 606 ms; VERIFICATION.md's open and backup rows and the README's backup figure did not match the same file; "13 licence texts" was 12 texts plus the notices file (rc3's "12" was 11 plus it); rc3's 285 ms and 329 ms and the first rc4 build's 1.13 s have no raw record; `build.log` does not name the commit | Engineering | Figures and counts corrected and the unrecorded figures marked. rc3 and rc4 measured again in one session on 2026-11-01: rc3 273–349 ms median, 330–407 ms p95; rc4 44–56 ms, 763–789 ms, so rc4's recorded 39 ms and 606 ms were not reproduced. The rc5 build's commit is recorded beside its log in `revision.txt`, and `build_desktop.ps1` now prints it. Closes when the next build's log names its commit | Open |
| I-10 | Issue | The first clean-clone test run of `f2bb6b9` was 193 passed, 1 failed: the validation script had pointed `TEMP` at the long scratch folder, so a test's `git init` failed on Windows' path limit ("cannot stat"). Rerun on the same commit with the system temp folder: 194 passed | Engineering | Cause shown by the rerun; the first run's output is kept in `checks-first-run/` | Closed |
| I-11 | Issue | Five new GUI scenarios were written for rc5 but never added to the list in `tests/test_desktop_gui.py`, so the build commit's 194 passed without them, and a draft of VERIFICATION.md said they had run. Found by adding up the test counts (175 + 19 left no room for them), after the installer was built and validated | Engineering | Added to the list; all five passed on the same application code; included in the final-tree runs. The content of the installer did not need to change | Closed |
| I-12 | Issue | One of six final-tree runs on `1c2eb39` failed `main_window_text_wraps_at_minimum_size` with "application has been destroyed". Only the close handler can destroy that window and the test had not reached its cleanup, so something probably closed it from outside while the owner was using the computer. Likely, not proven: it was not reproduced | Engineering | Scenario passed 10 of 10 alone; a second set of three full runs passed; the failing output is kept in `checks-final-first-set/`. Reopen if it recurs on a machine nobody is using | Closed |
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
| DEC-04 | 30 curated English words; other languages dropped | rc1 excluded the older corpus; an earlier review had found 42 misspelled French/Spanish words there. Quality over breadth (inferred) | Retrospective | **Superseded by DEC-22** for the app's scope; the 30 cards stay |
| DEC-05 | Keep legacy browser code and banks for history and regression tests only | Imported progress still reports; the desktop reuses the game engine | Retrospective | Owner to confirm |
| DEC-06 | Review = all active review items for curated words in the situation, due first, once per session | Keeps Review usable on the day of practice (due-only would wait a day); matches rc1's fallback but as one consistent rule | Claude Code (this delivery) | **Owner to confirm** |
| DEC-07 | Feedback tone. rc2 replaced the mocking lines with plain encouraging English (Claude Code's change: sarcasm and idioms may confuse and offend). In rc5 the owner chose "Original sarcastic lines", so the 40 originals are back word for word | The owner was told these reverse D-17 and insult the learner; the rationale for the choice is theirs and is not recorded here | **Owner, 2026-11-01** | Decided; see RK-9 |
| DEC-08 | Licence: **MIT for this project's software**; the teaching content and the icon stay unlicensed until their authorship is confirmed | Rationale written by Claude Code, not stated by the owner. The owner said "MIT for the code"; the LICENSE scope note also names tests and documentation, and the copyright name comes from the Git author. Asked to confirm, the owner answered "Keep rc4 as is" (2026-11-01), so LICENSE stays unchanged for rc4. rc5 names the level lists as excluded, like the cards, and changes nothing else. Raised and not resolved: `docs/CONTENT_REVIEW.md` repeats most of the card text, so "documentation" overlaps the exclusion; `frontend/` and `assets/audio/` are not named; the year was not confirmed | **Owner, 2026-11-01** | Decided; scope and copyright line kept; content licence open |
| DEC-09 | Version the new candidate as 1.0.0rc2 | It differs from the rc1 build; still a release candidate until gates close | Claude Code | Done |
| DEC-10 | Supported history: up to 5 profiles, 5,000 completed rounds per profile | Measured on the build machine (rc3): in-process operations ≤ 386 ms at the 95th percentile; start-up 0.78–0.84 s, 1.65 s with the day's first backup | Proposal | **Owner to agree** |
| DEC-11 | Minimum window 800×600 logical pixels | Fits 1080p at 150% scaling | Claude Code | Done |
| DEC-12 | GUI tests run one per process | Removes a test-harness-only Tcl interaction (D-26) | Claude Code | Done |
| DEC-13 | Build locally from a clean checkout; GitHub workflows prepared but not yet run | No remote repository available | Claude Code | Done |
| DEC-14 | Whether the installer shows licence terms to end users (see RK-7), and which | Depends on the project licence (DEC-08). The owner answered "Keep rc4 as is" (2026-11-01), so rc4's setup shows no terms; rc5 did not raise it again and is the same | Owner, for rc4; carried into rc5 unchanged | **Owner decision still needed before public distribution** |
| DEC-15 | Intended learner: reads short, simple English (about CEFR A2), preparing for travel | A proposed profile for reviewing content and recruiting learners; not a certification that the content is A2 | Proposal (CONTENT_REVIEW.md) | **Owner to confirm; reviewer to test** |
| DEC-16 | Version the corrected candidate 1.0.0rc3 | Code changed after rc2 (D-30, D-31, D-29, T-28); still a candidate until gates close | Claude Code | Done |
| DEC-17 | Generate notices from the build environment and check coverage at build time | Keeps the notices true to what ships; a new file or version fails the build | Claude Code | Done |
| DEC-18 | Redesign the UI within CustomTkinter rather than moving to native widgets or Qt | Claude Code's reasoning when offering the options, not the owner's: days rather than weeks, no packaging or licence change; the alternative (ttk) would also have fixed the screen-reader gap and remains open | **Owner, 2026-11-01** | Done |
| DEC-19 | Draw the board on a canvas instead of building it from widgets | The only way to keep the redesign and stay faster than rc3; the keys were never focusable, so no keyboard route is lost | Claude Code | Done |
| DEC-21 | Whether learners see a hanging figure | Claude Code added the drawing in the redesign without raising it. It may sit badly with the plain, encouraging tone in DEC-07; a neutral progress graphic is a small change. The owner answered "Keep rc4 as is" (2026-11-01), so the figure stays, and rc5 keeps it. Changing it after G9 or G10 would mean rerunning the affected checks | Claude Code (added); **owner, 2026-11-01** (kept) | Decided |
| DEC-20 | Keep the validation tooling in the repository | A release that cannot be revalidated by someone else is not finished (I-6) | Claude Code | Done |
| DEC-22 | Bring back the older app's word database in English, Spanish, Italian and German. This lifts the owner's earlier "no extra languages" rule | The owner chose "English & other language words" after being told the cost: an rc5, reviewers per language, words the keys could not enter. Who wrote `words.xlsx` is not recorded | **Owner, 2026-11-01** | Decided; **owner to say who wrote the sheet** |
| DEC-23 | G9 covers every word that ships, with one reviewer per language, and **all four languages must pass before 1.0**. Level lists say "not yet reviewed" until then. G10 uses the English travel cards unless the owner says otherwise | Proposed by Claude Code in the rc5 plan; the owner answered "Start rc5" to that plan, which listed these as defaults. Asked "Must all four languages pass review before 1.0?", the owner answered "Yes, all four" | **Owner, 2026-11-01** (G9); G10 is a default | G9 decided; **G10's language still a default the owner can change** |
| DEC-24 | The placement test and adaptive word choice stay out | The owner chose "Not now". They need levels to choose between, which rc5 now has, so this can be revisited | **Owner, 2026-11-01** | Decided for now |
| DEC-25 | No clue changes: the 30 cards keep two clues, and there is no first-letter button | The owner answered "No preference", so nothing was added ("do not add features unless I ask"). Level words have three clues because their rows do | Claude Code, following the owner's rule | Open to the owner |
| DEC-26 | How the sheet became a pack: keep each repeated word at its lowest level, leave out the six English words already on cards, keep German nouns' and phrases' capitals, invent no teaching notes, add only the accent keys the lists use | Each keeps the content as written or protects something that already works; a level-list row with a card's word, type and level would overwrite the card | Claude Code, listed in the rc5 plan | Done |

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
- **Where the AI's own evidence was wrong.** Incidents I-1 to I-12 record them, including
  cropped screenshots published with rc2 (I-4) and two rc2 claims that measurement later
  contradicted (I-5). An independent review found the D-30 rollback defect in AI-written
  code; fault-injection tests now cover it. In rc4 the AI's own redesign made the game four
  times slower, which measurement caught before release and a second build fixed (D-32,
  I-7).
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

### M11 — rc4: the owner's UI feedback, the licence, and a performance regression

The owner reported that the UI looked like a form and chose a redesign inside CustomTkinter
(DEC-18), and chose MIT for the software (DEC-08). Both are in `849d1e1` and `8019a84`,
with the validation tooling moved into the repository after the old set was lost (I-6).

The first rc4 installer passed the whole validation sequence, and then performance
measurement showed the redesign had made a guess four times slower than rc3 (D-32). The
board was rewritten as one drawn canvas that updates in place, bringing a guess to 39 ms
median for a guess that continues a round, and the installer was rebuilt and revalidated
from `d543579` (I-7). A guess that ends a round is slower than rc3. A later audit corrected
the rc4 record (I-8). Clicking a letter is now hit-tested rather than a button, so a GUI scenario covers
it.

Dependencies unchanged: the human gates, the clean machine, DEC-14 (installer terms, still
open) and a GitHub repository.

### M12 — rc5: the older app's lines and words

The owner kept rc4's licence, figure and setup as they were, then pointed to the older
Hangman Learning app and chose what returns: the original lines and the word database in four
languages, with no placement test (DEC-07, DEC-22, DEC-24). The words went in as a separate
pack with their own source, so the legacy banks stay out of practice (D-02) and the engine's
selection, Review and reporting rules apply unchanged. The board gained accent keys, wrapped
tiles and word gaps, and German nouns kept their capitals.

Built from `f2bb6b9` after measuring, and validated on the build machine in a separate data
folder, with the owner's agreement to replace their installed rc4; their data was checked
unchanged and rc5 was left installed. Travel-card speed matches rc4; Word cards opens more
slowly than rc4, and switching lists is quick. Nothing in the level lists has been reviewed,
which widens G9 (DEC-23, RK-1, RK-8).

Dependencies: the human gates, reviewers per language, the clean machine, DEC-14, who wrote
the word sheet, and a GitHub repository.
