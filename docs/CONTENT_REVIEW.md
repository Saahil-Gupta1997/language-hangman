# Content review — word lists

The 1,544 words in `src/desktop/content/levels/` must be checked by qualified reviewers before
1.0, and **all four languages must pass** (gate G9 in [ACCEPTANCE.md](ACCEPTANCE.md), decision
DEC-23). This file explains the review and records its result. **No independent review has
taken place yet**, and the app says these words have not been reviewed.

## Intended learner (open — owner to decide, DEC-15)

The earlier proposal was someone preparing for travel. That no longer fits, because the travel
cards were removed in rc6 (DEC-27), so **the owner needs to say who the app is for**. Until
then, reviewers should judge the words for an adult or older teenager who reads short, simple
English, which is what the clues require. The app does not translate.

The app is a spelling-and-recall game. It makes no claim to teach or certify language
proficiency, and the levels below are labels from the word sheet, not assessed levels.

## Reviewers

One qualified reviewer per language, for example a teacher of that language with experience of
adult learners. Each works from the matching `4-level-list-review-<language>.csv` in the
acceptance kit, which has blank columns for their verdicts, and records their name or initials,
qualification, date and the file's revision (`git rev-parse HEAD`).

## The word lists

Converted from the owner's older `words.xlsx` by `scripts/build_level_words.py`. Each word has a
level, a word type and three clues in English, and no example, pronunciation or usage note:
nothing was invented to fill those gaps.

| Language | Beginner | Novice | Intermediate | Advanced | Expert | Total |
| --- | --- | --- | --- | --- | --- | --- |
| English | 80 | 80 | 80 | 80 | 80 | 400 |
| Spanish | 80 | 76 | 77 | 79 | 77 | 389 |
| Italian | 79 | 77 | 78 | 80 | 76 | 390 |
| German | 70 | 70 | 76 | 76 | 73 | 365 |

What the conversion changed, and nothing else: 56 repeats within a language were removed,
keeping the lowest level, and capitals were normalised (lower case, except German nouns and
German phrases, which stay as the sheet wrote them).

## What to check on every word

1. The word is spelled correctly and really is a word or phrase of that language.
2. The English clues are correct for this word. They were written per concept and shared
   between languages, so a clue can fit the English meaning better than the translation.
3. The level is reasonable. The levels are the sheet's own and have not been assessed.

Mark each word in the sheet and write any correction. Material issues are logged in
[DELIVERY.md](DELIVERY.md), fixed and retested (gate G11).

Automated checks confirm only the structure: no repeats, three different clues, and every
letter on the A–Z keys once accents are ignored. They say nothing about accuracy. Rows such as
the German `Quanten-`, a word fragment, are examples of what only a reviewer can judge.

## Feedback lines (D-17, reversed in rc5)

Wrong- and right-guess messages are in `src/utils/feedback_lines.py`. rc2 replaced the original
lines because they mocked the learner and used idioms (D-17). In rc5 the owner restored the 40
originals word for word (decision DEC-07), so the sarcastic tone is deliberate. Reviewers and
facilitators need not correct it, but please note anything a learner could not understand.

## Provenance (for owner confirmation)

| Item | Where | Origin as far as the repository shows | Confirm |
| --- | --- | --- | --- |
| Word lists | `src/desktop/content/levels/*.json` | Converted from `words.xlsx` in the owner's older Hangman Learning app (March 2025); written by the owner (owner, 2026-11-01) | MIT since rc8 (DEC-08) |
| Feedback lines | `src/utils/feedback_lines.py` | The owner's `humorous_lines.py`, restored in rc5 | Owner: authorship |
| Application icon | `assets/app.ico` | Not recorded | Owner: source and rights |
| Audio tones | `assets/audio/*.wav` | "Simple generated fallback tones" (assets/audio/README.md); **not used** by the desktop app | — |
| Legacy word banks | `data/words/*.json` | Beta-era, AI-assisted; not shipped in the installer | — |

### Third-party components bundled in the installer

The inventory, with versions, licences and the files each component covers, is
[`packaging/third-party/THIRD-PARTY-NOTICES.txt`](../packaging/third-party/THIRD-PARTY-NOTICES.txt);
the licence texts are in `packaging/third-party/licenses/`. Both are installed next to the
program, and the build fails if they do not cover every shipped file (T-28, closed in rc3).

In summary: Python 3.12.1 (PSF), with bzip2, xz, libmpdec, expat and zlib linked in;
OpenSSL 3.0.11 (Apache-2.0); libffi 3.4.4 (MIT); SQLite 3.43.1 (public domain);
Tcl/Tk 8.6.13; zlib 1.2.13; the Microsoft Visual C++ runtime; Pillow 12.3.0 (MIT-CMU, with
its bundled image libraries); CustomTkinter 5.2.2 (MIT) with the Roboto font (Apache-2.0);
darkdetect 0.8.0 (BSD-3-Clause); packaging 26.3 (Apache-2.0 or BSD-2-Clause); the PyInstaller
6.11.1 bootloader (GPL-2.0-or-later with an exception permitting distribution with any
program); and Inno Setup 6.7.3's setup and uninstall programs.

Points for the owner:

- **CustomTkinter's metadata disagrees with itself**: its `License` field says CC0-1.0, while
  its LICENSE file and classifier say MIT. The MIT text is shipped; it satisfies either.
- **Microsoft Distributable Code**: Python's licence asks anyone redistributing
  `VCRUNTIME140.dll` to have end users agree to terms at least as protective as Microsoft's.
  Since rc8 setup shows `LICENSE` and needs it accepted (DEC-14). Whether that fully meets the
  terms has not had a legal review (RK-7).
- Pillow's Windows build used here contains no GPL components (no libimagequant); its font
  module (FreeType, HarfBuzz) is not shipped.
