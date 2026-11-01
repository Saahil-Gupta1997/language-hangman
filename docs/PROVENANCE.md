# Provenance — where the content came from

Language Hangman is for people who want to practise new words (DEC-15). It is a spelling-and-recall
game: it makes no claim to teach or certify language proficiency, and levels are labels from the
word sheet, not assessed levels. The app does not translate.

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

Automated checks confirm only the structure: no repeats, three different clues, and every letter on
the A–Z keys once accents are ignored. They say nothing about accuracy.

## Feedback lines (D-17, reversed in rc5)

Wrong- and right-guess messages are in `src/utils/feedback_lines.py`. rc2 replaced the original
lines because they mocked the learner and used idioms (D-17). In rc5 the owner restored the 40
originals word for word (decision DEC-07), so the sarcastic tone is deliberate.

## Origins

| Item | Where | Origin |
| --- | --- | --- |
| Word lists | `src/desktop/content/levels/*.json` | Converted from `words.xlsx`, written by the owner. MIT since rc8 (DEC-08) |
| Feedback lines | `src/utils/feedback_lines.py` | The owner's `humorous_lines.py`, restored in rc5 |
| Application icon | `assets/app.ico` | Made by the owner. MIT since rc8 (DEC-08) |
| Audio tones | `assets/audio/*.wav` | "Simple generated fallback tones" (`assets/audio/README.md`); not used by the desktop app |
| Legacy word banks | `data/words/*.json` | Beta-era, AI-assisted; not in the installer and outside the MIT grant |

## Third-party components bundled in the installer

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
