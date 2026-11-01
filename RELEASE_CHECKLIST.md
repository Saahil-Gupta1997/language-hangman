# Release checklist

1. Make a fresh clone (or `git worktree`) of the release commit. Before running anything
   else, run `release-check` with `PYTHONDONTWRITEBYTECODE=1`: Python and pytest create
   caches that the check rightly reports and that never reach the `git archive` source zip.
2. Then `python -m ruff check .`, `python scripts/check_curated_content.py`,
   `python -m pytest -rs` (read pytest's own exit code, not a filtered summary) and
   `python desktop_app.py --smoke-test <folder>`. If the interface changed, measure
   performance **now**, before building: in rc4 a redesign made a guess four times slower
   than the previous release, and the installer had to be discarded and rebuilt (I-7).
   The tooling for every step below is in `scripts/validation/` (I-6).
3. Build in a fresh clone of the same commit on Windows x64 with **Python 3.12.1** and
   **Inno Setup 6.7.3** (the versions the third-party notices describe):
   `./scripts/build_desktop.ps1 -Python <clean 3.12.1 environment>\python.exe`. The build
   fails if the notices do not cover every shipped file or the versions differ; if a
   dependency changes, run `python scripts/third_party_notices.py collect` with the build
   interpreter, review the result and commit it first.
4. **Immediately copy** `dist\installer\*.exe` and `SHA256.txt` out of the build tree
   (incident I-1: a later clean-up deleted a validated installer).
5. Validate that exact installer and record results against its SHA256: install the
   previous release and let it create data; upgrade; `third_party_notices.py check
   <install folder> --installed`; normal launch; `LanguageHangman.exe --smoke-test <folder>`
   without Python on `PATH`; beta import; damaged-data recovery; uninstall with data
   preserved. Capture screenshots with a DPI-aware process (incident I-4). Compare the
   upgraded program folder with the build: only `LICENSE.txt` and the two uninstaller files
   should differ (D-34).
6. Run the manual checks and record them (docs/ACCEPTANCE.md M1–M4).
7. Confirm the word lists are fine with the owner. This is their call and is not a recorded gate (DEC-36).
8. Owner decisions recorded: licence (DEC-08) and installer terms (DEC-14) before publishing.
   Silent installs skip the licence page, so check it in the real wizard too.
9. Source archive from the tagged commit (`git archive`); extract it and run `release-check`
   on the extracted tree; publish `SHA256SUMS.txt` for every artifact.
10. Update RELEASE_NOTES.md and the go/no-go record. Never mark an unrun gate passed.
11. Promote the version (`src/__init__.py`) only after acceptance and owner approval; rebuild
    and repeat 1–5 and 9 on the final artifact.
