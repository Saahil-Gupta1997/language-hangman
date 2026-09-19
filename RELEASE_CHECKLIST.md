# Release checklist

1. On the release commit, from a clean checkout: `python -m pytest -rs` (check pytest's own
   exit code, not a filtered summary), `python -m ruff check .`,
   `python scripts/check_curated_content.py`, `python -m src.cli release-check`,
   `python desktop_app.py --smoke-test <folder>`. Until D-29 is fixed, run `release-check` in a
   `git worktree` of the commit (it wrongly flags `.git/refs/heads/release`).
2. Build on Windows x64 with Python 3.12 and Inno Setup 6:
   `./scripts/build_desktop.ps1 -Python <clean 3.12 environment>\python.exe`.
3. **Immediately copy** `dist\installer\*.exe` and `SHA256.txt` out of the build tree
   (incident I-1: a later clean-up deleted a validated installer).
4. Validate that exact installer: install, upgrade over the previous release with real data,
   `LanguageHangman.exe --smoke-test <folder>` without Python on `PATH`, corrupt-data
   recovery, uninstall with data preserved. Record results against its SHA256.
5. Run the manual checks and record them (docs/ACCEPTANCE.md M1–M4).
6. Content and learner gates: CONTENT_REVIEW.md and USER_ACCEPTANCE.md completed by people.
7. Third-party notices included (T-28); licence chosen (DEC-08).
8. Source archive from the tagged commit (`git archive`), excluding databases, secrets and
   build output; publish `SHA256SUMS.txt` for every artifact.
9. Update RELEASE_NOTES.md and the go/no-go record. Never mark an unrun gate passed.
10. Promote the version (`src/__init__.py`) only after acceptance; rebuild and repeat 1–4.
