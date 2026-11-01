# 1.0.0rc5 — Desktop release candidate 5 (2026-11-01)

A tested release candidate, **not** the final 1.0. A clean-computer installation, manual
keyboard and display checks, a review of every word by qualified reviewers, five learner
sessions and some owner decisions are still open (see
[docs/ACCEPTANCE.md](docs/ACCEPTANCE.md)). It supersedes rc4 for every purpose.

- **Installer:** `LanguageHangman-1.0.0rc5-Setup.exe`, SHA256 `a94a92696cf5f001fb7326fb92628557f5907b0122383d3269d3aa4e26d47531`, built from `f2bb6b9`.
  **Unsigned**: Windows SmartScreen will show "unknown publisher".
- **Upgrading:** run the new installer; profiles, progress and paused rounds are kept
  (checked from rc4 on the build machine).

## New since 1.0.0rc4

- **Word lists in four languages.** 1,538 words in English, Spanish, Italian and German at
  five levels, from the owner's older word sheet, each with three clues in English. **Nobody
  has reviewed them**, and the app says so.
- **The original feedback lines are back**, word for word: all 40, sarcasm included, at the
  owner's choice.
- **Practice setup** now has Language and Words. Situation applies only to the 30 English
  travel cards, which have not changed.
- **The board handles other languages.** It adds each language's accented keys and shows ß as
  itself. An accented letter is its own letter, so `n` does not reveal `ñ`. Spaces and hyphens
  show from the start, long phrases wrap, and German nouns keep their capitals.
- **Word cards** lists every word by language and level.
- **Licence:** the word lists are outside the MIT grant, like the teaching cards.

## Known limitations

- The word lists are unreviewed. Automated checks cover their structure, not their accuracy.
- Word-list words have clues but no example, pronunciation or usage note, and none were
  invented. Their clues are in English, so they suit someone who reads English.
- Pronunciation is an approximate respelling, on travel cards only.
- The restored lines mock the learner and use idioms that a learner of English may not follow.
- Windows screen readers generally cannot read CustomTkinter's controls, and the letter keys
  are drawn rather than separate controls; typing a letter remains the keyboard route, which
  needs a keyboard that can type the accented letters.
- The database is not encrypted; local passwords protect in-app access only. No email
  password reset. Backups contain every profile's password hash: keep them private.
- One app instance per Windows account; guest practice is deleted on sign-out or close.
- The installer is unsigned and shows no licence terms during setup.
- On the build machine, Word cards takes 2–3 s to open and start-up takes about 1.0 s; both
  are slower than rc4. The guess that ends a round takes 0.6–0.8 s.
- No cloud sync, automatic updates, multiplayer, machine learning or placement test.

## Verification

Automated suite on the build commit `f2bb6b9`: 194 passed, 0 skipped; five more GUI scenarios
ran afterwards (I-11). Lint, content and release checks clean.
On the build machine (Windows 11 at 125%): upgrade from rc4 with data created by rc4, the
17-step journey in the installed app without Python, beta import, recovery at both text sizes,
restore, uninstall, and the installed licence and notices. Not yet: a clean machine, real
100%/150% scaling, a person using the keyboard. Details:
[docs/VERIFICATION.md](docs/VERIFICATION.md).

## 1.0.0rc4 — Desktop release candidate 4 (2026-11-01)

A tested release candidate, **not** the final 1.0. A clean-computer installation, manual
keyboard and display checks, an educator's review of the 30 cards, five learner sessions and
some owner decisions are still open (see [docs/ACCEPTANCE.md](docs/ACCEPTANCE.md)).

- **Installer:** `LanguageHangman-1.0.0rc4-Setup.exe`, SHA256 `abb0cf94428503316b2619add6bd3388b8ca4f3c22bc116e6b90e649e9ebcd3c`, built from `d543579`.
  **Unsigned**: Windows SmartScreen will show "unknown publisher".
- **Upgrading:** run the new installer; profiles, progress and paused rounds are kept
  (checked from rc3 on the build machine).

## New since 1.0.0rc3

- **A redesigned practice screen.** The round is now a board: the hangman figure beside the
  word as letter tiles, lives as pips, and an A–Z keyboard that also shows which letters you
  have tried. Type a letter as before, or click a key.
- **The rest of the app follows the same design**: a slim navigation strip that marks the
  current page, one clear primary action per screen, stat tiles on Home and Reports, and
  cards for learning content.
- **The software is under the MIT licence.** `LICENSE.txt` installs beside the program. The
  30 teaching cards and the icon are not covered until their authorship is confirmed.
- **Most guesses now draw about seven times faster than rc3** (44–56 ms against 273–349 ms
  median, three runs each on the same day). The guess that ends a round is about twice as
  slow (763–789 ms against 330–407 ms at the 95th percentile).

## Known limitations

- English only; 30 words across Restaurant, Airport and Hotel; explanations are in English.
  The intended learner (about CEFR A2) is a proposal awaiting review, not a certification.
- Pronunciation is an approximate respelling, not audio or IPA.
- Windows screen readers generally cannot read CustomTkinter's controls, and the A–Z keys
  are drawn rather than separate controls; typing a letter remains the keyboard route.
- The database is not encrypted; local passwords protect in-app access only. No email
  password reset. Backups contain every profile's password hash: keep them private.
- One app instance per Windows account; guest practice is deleted on sign-out or close.
- The installer is unsigned and shows no licence terms during setup.
- Moving between screens takes 350–570 ms on the build machine, slower than rc3, because
  those screens now group content into cards.
- No cloud sync, automatic updates, multiplayer, machine learning or other languages.

## Verification

Automated suite on the final tree (`7c425fd`): 175 passed, 0 skipped, ×3, three runs in a clean
clone. On the build commit `d543579` the clean run was 174 passed, 1 failed; that test was
then changed, and the installer's inputs were not. Lint, content and release checks clean. On the build machine (Windows 11 at 125%): upgrade from rc3 with
data created by rc3, the 16-step journey in the installed app without Python, beta import,
recovery at both text sizes, restore, uninstall, and the installed licence and notices. Not
yet: a clean machine, real 100%/150% scaling, a person using the keyboard. Details:
[docs/VERIFICATION.md](docs/VERIFICATION.md).

## 1.0.0rc3 — Desktop release candidate 3 (2026-09-19)

A tested release candidate, **not** the final 1.0. A clean-computer installation, manual
keyboard and display checks, an educator's review of the 30 cards, five learner sessions
and the owner's decisions are still open (see [docs/ACCEPTANCE.md](docs/ACCEPTANCE.md)).

- **Installer:** `LanguageHangman-1.0.0rc3-Setup.exe`, SHA256
  `5e1b31077061dabd9cc764e07f8243f3054f526b8b1202181805b17022665f84`, built from `fd3b25a`.
  **Unsigned**: Windows SmartScreen will show "unknown publisher".
- **Upgrading:** run the new installer; profiles, progress and paused rounds are kept
  (checked from rc2 on the build machine; rc1 to rc2 was checked for rc2). **From the older
  browser beta:** use *Restore / import old database* on the sign-in screen.

### Fixed since 1.0.0rc2

- **Restore could leave a journal file stranded while saying nothing had changed.** If
  Windows refused to move the second of the data file's journal files, the first stayed in
  the backups folder. Every moved file is now put back; if one cannot be, the message says
  which file is where and how to put it back, and no longer says the data is unchanged.
- **Recovery instructions could be cut off on the right** when the recovery window was
  narrower than its opening size, and some text was cut off by a few pixels in the main
  window at its smallest size with Large text. Text now wraps to the space available. The
  recovery window also uses the saved Large text setting.
- **Third-party licence notices are now installed** next to the program
  (`THIRD-PARTY-NOTICES.txt` and `licenses`), covering every bundled component.
- The release hygiene check no longer fails in a clone of a `release/…` branch.
- Help names where the notices are and describes the app as rule-based software built
  with AI assistance.

### Known limitations

- English only; 30 words across Restaurant, Airport and Hotel; explanations are in English.
  The intended learner (about CEFR A2) is a proposal awaiting review, not a certification.
- Pronunciation is an approximate respelling, not audio or IPA.
- Windows screen readers generally cannot read CustomTkinter's controls.
- The database is not encrypted; local passwords protect in-app access only. No email
  password reset. Backups contain every profile's password hash: keep them private.
- One app instance per Windows account; guest practice is deleted on sign-out or close.
- The installer is unsigned and shows no licence terms; the project licence is not yet
  chosen.
- No cloud sync, automatic updates, multiplayer, machine learning or other languages.

### Verification

On revision `fd3b25a`: 174 automated tests passed (0 skipped), lint and content checks
clean, release check clean in a clone, a worktree and the source archive. On the build
machine (Windows 11 at 125%): upgrade from rc2 with data created by rc2, the 16-step
journey in the installed app without Python, beta import, recovery, uninstall, and the
installed notices. Not yet: a clean machine, real 100%/150% scaling, a person using the
keyboard. Details: [docs/VERIFICATION.md](docs/VERIFICATION.md).

## 1.0.0rc2 — Desktop release candidate 2 (2026-09-19)

A tested release candidate, **not** the final 1.0: educator review, learner sessions and the
owner's manual checks are still open (see [docs/ACCEPTANCE.md](docs/ACCEPTANCE.md)).

- **Installer:** `LanguageHangman-1.0.0rc2-Setup.exe` — SHA256
  `2fc27de78a94aca7c96637dafc70b15ff707349b403c878bfd050ad79a58dc95`, built from
  `4ad1e34`. **Unsigned**: Windows SmartScreen will show "unknown publisher".
- **Upgrading from rc1:** run the new installer; your profiles and progress are kept.
  **From the older browser beta:** use *Restore / import old database* on the sign-in
  screen and pick its `data\app.db` (this replaces all current profiles after confirmation).

### Fixed since 1.0.0rc1

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
