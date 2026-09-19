# Release acceptance — 1.0.0rc1

The application is a release candidate. Do not change the version to final 1.0.0 until
all blocking gates below have an identified reviewer, date and evidence. Automated
service tests do not substitute for native UI, accessibility or learner review.

| Gate | Status in this delivery | Evidence needed |
| --- | --- | --- |
| Transaction, retry, recovery, migration, privacy regressions | Executed; see VERIFICATION.md | Test output |
| Native Windows source and installed application smoke | Pending | desktop-release workflow output |
| Clean Windows install, update, uninstall/data preservation | Pending | Machine/version, steps, screenshots, resulting data |
| Layout at 100%, 125%, 150% Windows scaling and minimum window size | Pending | Screenshots; no clipped controls |
| Keyboard navigation, focus, Enter/Escape and text scaling | Implemented, native verification pending | Actual tester result |
| Independent review of all 30 teaching cards | Pending | Reviewer corrections and acceptance |
| Five learner sessions | Pending | First-round time, completion, confusion and next-day meaning recall |
| Critical/high defects closed or explicitly accepted | Pending native test results | Defect log and release decision |

## Manual journey

1. Install without Python present. Start from the Start menu and desktop shortcut.
2. Register; reject mismatched/short passwords. Sign out; reject wrong credentials.
3. Start each situation and mode. Submit invalid and repeated guesses; verify no extra life loss.
4. Lose lives; verify progressive clues. Close/reopen, sign in and resume the same word/guesses/clues.
5. Win and lose rounds; close between rounds; resume the learning card and continue.
6. Complete a session. Reconcile game rows/wins/losses and completed sessions with reports.
7. Discard an unfinished session; verify completed rounds remain in reports.
8. Run guest practice; sign out/restart; verify no guest data is retained.
9. Create two profiles. Export one; verify the other and password hashes are absent.
10. Create a backup; add progress; restore; verify backed-up state and safety backup.
11. Try a corrupt/future-version backup; verify existing state is unchanged.
12. Import the old app.db; sign in with old credentials; verify old progress and new corpus scope.
13. Export diagnostics; inspect allowed fields. Delete one profile; preserve the other.
14. Update/reinstall and uninstall; confirm the application-data folder survives.
15. Test keyboard-only interaction and text scaling on a small window.

Record tester, date, OS, build/installer SHA256, result, steps and evidence for each failure.
Never fill external-user or educator results with automated or AI-generated observations.
