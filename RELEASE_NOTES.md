# 1.0.0rc2 — Desktop release candidate 2 (2026-09-19)

A tested release candidate, **not** the final 1.0: educator review, learner sessions and the
owner's manual checks are still open (see [docs/ACCEPTANCE.md](docs/ACCEPTANCE.md)).

- **Installer:** `LanguageHangman-1.0.0rc2-Setup.exe` — SHA256
  `2fc27de78a94aca7c96637dafc70b15ff707349b403c878bfd050ad79a58dc95`, built from
  `4ad1e34`. **Unsigned**: Windows SmartScreen will show "unknown publisher".
- **Upgrading from rc1:** run the new installer; your profiles and progress are kept.
  **From the older browser beta:** use *Restore / import old database* on the sign-in
  screen and pick its `data\app.db` (this replaces all current profiles after confirmation).

## Fixed since 1.0.0rc1

- Every screen after sign-in crashed (rc1's app was unusable once signed in).
- Review could start for a brand-new learner and serve unseen words; it now uses only words
  already practised in the chosen situation (due words first) and offers Standard practice
  when there are none. Shortened sessions say why.
- Imported older databases could put retired vocabulary into practice; practice now always
  uses the 30 curated words, while older results stay in reports.
- A damaged data file stopped the app from starting and blocked restore. The app now opens a
  recovery window, restores a backup and keeps an exact copy of the damaged file.
- A failed daily backup stopped the app from starting; it now starts with a warning.
- Dropdowns could not be used with the keyboard; focus could move off-screen; text size now
  also responds to Ctrl+= and the numeric keypad.
- The window no longer opens taller than the screen at 150% display scaling.
- Wrong-guess messages no longer mock the learner.
- Diagnostics now record what failed (operation, stage, version) without personal data.

## Known limitations

- English only; 30 words across Restaurant, Airport and Hotel; explanations are in English.
- Pronunciation is an approximate respelling, not audio or IPA.
- Windows screen readers generally cannot read CustomTkinter's controls.
- The database is not encrypted; local passwords protect in-app access only. No email
  password reset. Backups contain every profile's password hash: keep them private.
- One app instance per Windows account; guest practice is deleted on sign-out or close.
- The installer does not yet include third-party licence notices (to be added before public
  distribution) and the project licence is not yet chosen.
- No cloud sync, automatic updates, multiplayer, machine learning or other languages.

## Verification

163 automated tests passed on the candidate revision; the native journey passed 16 checks
both from source and in the installed build; install, genuine upgrade from rc1, beta import,
recovery and uninstall were verified on Windows 11. Details:
[docs/VERIFICATION.md](docs/VERIFICATION.md).
