# Delivery log — Language Hangman Desktop 1.0

Project-management record for taking 1.0.0rc1 to a portfolio-ready 1.0. Test results live
in [VERIFICATION.md](VERIFICATION.md); release gates and sign-off live in
[ACCEPTANCE.md](ACCEPTANCE.md).

Status values: **Open**, **In progress**, **Fixed** (code changed, automated evidence),
**Verified** (manual/native evidence recorded), **Pending owner** (needs a person or
decision outside the engineering work), **Deferred** (accepted for a later release).

## Source revisions

| Revision | Branch | Meaning |
| --- | --- | --- |
| `023f2bd` | master | v1.0.0-beta working copy, snapshotted before the upgrade |
| `5a41404` | release/1.0 | 1.0.0rc1 exactly as received (zip SHA256 `0510a1a0…fe364`) |
| `16f3fc3` | release/1.0 | rc1 + post-review fixes R-01..R-03; **baseline for this delivery** |

## Defect and task register

| ID | Pri | Title | Acceptance criteria | Status | Evidence |
| --- | --- | --- | --- | --- | --- |
| R-01 | P0 | Crash on every signed-in screen (pack/grid mix) | Native smoke passes past sign-in | Fixed | `16f3fc3`; baseline smoke |
| R-02 | P0 | `events.log` held open; Windows cleanup fails | Smoke temp folder deleted on exit | Fixed | `16f3fc3`; baseline smoke |
| R-03 | P1 | Text-size change raises TclError after dropdowns | Scaling works after any screen; regression test | Fixed | `16f3fc3`; `test_text_size_change_after_dropdown_is_destroyed` |
| D-01 | P0 | Fresh profile can start Review with an unseen word | Fresh profile cannot start Review; every Review word meets the documented rule; situation enforced; short/exhausted queues controlled; Standard unaffected; tests drive `PracticeService` incl. later rounds | Open | baseline `defect-repro.txt` |
| D-02 | P0 | Legacy vocabulary reachable from desktop practice | Standard and Review use only `desktop-core` after importing legacy data; no fallback bypass; counts reflect curated words; history preserved | Open | baseline `defect-repro.txt` |
| D-03 | P0 | Corrupt live database blocks startup and restore | Valid backup restores a corrupt live DB; corrupt bytes quarantined; invalid backups change nothing; no partial replacement; recovery reachable when startup fails | Open | baseline `defect-repro.txt` |
| T-04 | P0 | Build and validate the Windows release | Installer, SHA256, clean source archive, results tied to revision, notes, demo recording; manual checks recorded per ACCEPTANCE.md | Open | — |
| T-05 | P0 | Content and learner acceptance | 24 heuristic warnings dispositioned; qualified review of 30 cards; 5 learner sessions recorded; material issues fixed and retested | Open | — |
| T-06 | P1 | Privacy-safe failure diagnostics | Failures log operation code, stage, version; no names, passwords, payloads or paths | Open | — |
| D-07 | P1 | Automatic backup failure may block startup | If safe, start with a visible "backup protection unavailable" warning | Open (to reproduce) | — |
| T-08 | P1 | Performance baseline | Agreed history size; startup, guess, report and backup timings recorded with hardware | Open | — |
| T-09 | P1 | Repository clarity | Metadata, entry point, legacy labels, version consistency, dependency docs, licence proposal, provenance | Open | — |
| T-10 | P1 | TPM evidence | Architecture/data flow, traceability, RAID, decisions, evidence index, go/no-go, AI-assistance note | Open | — |
| D-11 | P2 | Legacy gateway tests write `.session_secret` into the real app-data folder | Test suite writes nothing outside temporary folders | Open | review finding |
| D-12 | P2 | "Why this word" names the wrong category (e.g. adjective `fresh` shown as "focus on Noun") | Reason text matches the selected word | Open | baseline `smoke-practice.png` |
| T-13 | P2 | GUI not exercised in PR CI; release workflow manual-only | Native smoke runs on Windows for every PR | Open | review finding |
| T-14 | P2 | Line endings vary with checkout settings | `.gitattributes` makes source archives deterministic | Open | — |
| D-15 | P3 | Easy mode advertises three clues but the blank synonym repeats the association | Clue text and count agree | Open | review finding |
| T-16 | P3 | Black configured but not enforced (15 files differ) | Either enforced in CI or configuration removed | Open | baseline `checks.txt` |

## Milestone updates

### M1 — Baseline and defect reproduction (2026-09-19)

- Revision `16f3fc3` checked out into a clean worktree; environment in
  `evidence/2026-09-19-baseline-16f3fc3/environment.txt`.
- Results: 134 passed, 0 skipped, 1 third-party deprecation warning; Ruff clean; release
  check clean; curated check PASS with 24 warnings; legacy banks 324 valid / 759 warnings;
  native smoke journey passed on Windows. Black reports 15 files (T-16).
- The historical rc1 review reported 133 passed and one skipped GUI test. The difference is
  the R-03 regression test, which runs (not skips) on a Windows desktop.
- D-01, D-02 and D-03 reproduced with `repro_defects.py` (output in `defect-repro.txt`).
  D-02 needs more than ten later rounds, because recently played words are excluded
  from selection; a real imported database meets that condition.
