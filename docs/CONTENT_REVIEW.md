# Content review — travel cards and level lists

The 30 teaching cards in `src/desktop/content/english.json` and the 1,538 level-list words in
`src/desktop/content/levels/` must be checked by qualified reviewers before 1.0 (gate G9 in
[ACCEPTANCE.md](ACCEPTANCE.md)). This file is the reviewer's worksheet and the record of the
result. **No independent review has taken place yet**; the "Reviewer verdict" columns below
are empty until one does, and the app labels the level lists "not yet reviewed".

## Intended learner (proposed profile — owner to confirm, DEC-15)

This is a **proposed** profile, used to choose the reviewer and the learners for the
sessions. The cards have not been assessed against CEFR descriptors, and nothing in this
project certifies them as A2 material; the reviewer's verdict below (G9) is the first
check.

- Adults or older teenagers preparing for travel, who already read short, simple English
  sentences (about CEFR A2). All explanations are in English only; the app does not
  translate, so it is **not suitable for absolute beginners**.
- Goal: recognise and spell 30 high-frequency words for restaurants, airports and hotels.
- The app is a spelling-and-recall game. It makes no claim to teach or certify language
  proficiency.

## Reviewer

A qualified English-language teacher (for example CELTA, TESOL or equivalent experience
teaching adults at A2–B1). Record name or initials, qualification, date and the file's
revision (`git rev-parse HEAD`).

The 30 cards are unchanged from rc2 to rc5 (`git diff 4ad1e34 f2bb6b9 --
src/desktop/content/english.json` is empty), so a review of any of these candidates applies
to all of them. The level lists are new in rc5 and need a reviewer for each language.

## What to check on every card

1. **Meaning** is correct, simple and does not use the word itself.
2. **Example** is natural, correct and fits the situation.
3. **Pronunciation spelling** is a reasonable approximation for an A2 learner
   (capitals mark stress; it is not IPA).
4. **Usage note** is correct, useful at A2 and not misleading.
5. **Level and fit**: the word suits the learner and situation.

Mark each card **OK**, **Minor fix** (write the correction) or **Replace**. Material issues
are logged in [DELIVERY.md](DELIVERY.md), fixed and retested (gate G11).

## Worksheet

| # | Word | Meaning | Example | Pronunciation | Usage note | Reviewer verdict | Correction |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | **menu** (noun, Restaurant) | A list of food and drinks you can order. | Could I see the menu, please? | MEN-yoo | Ask for the menu before choosing your meal. | | |
| 2 | **bill** (noun, Restaurant) | A statement showing how much you must pay. | Could we have the bill, please? | bil | In US restaurants, people also ask for the check. | | |
| 3 | **water** (noun, Restaurant) | A clear liquid that people drink. | I would like a glass of water. | WAW-ter | Specify still or sparkling if the restaurant offers both. | | |
| 4 | **bread** (noun, Restaurant) | Food made from flour and baked. | Please bring some bread for the table. | bred | Bread is usually uncountable: say some bread or a slice of bread. | | |
| 5 | **spoon** (noun, Restaurant) | A utensil with a small bowl for eating or serving. | I need a spoon for my soup. | spoon (long oo) | A spoon is useful for soup; a fork is useful for solid food. | | |
| 6 | **order** (verb, Restaurant) | To ask a restaurant to prepare food or drink. | Are you ready to order? | OR-der | Order can also be a noun: the waiter took our order. | | |
| 7 | **share** (verb, Restaurant) | To have or use something together with another person. | We would like to share a dessert. | shair | Share a dish when more than one person will eat it. | | |
| 8 | **fresh** (adjective, Restaurant) | Recently made, picked, or prepared. | Is the fish fresh today? | fresh (one syllable) | Fresh describes food quality, not necessarily its temperature. | | |
| 9 | **spicy** (adjective, Restaurant) | Having a hot taste from spices such as chilli. | Is this curry very spicy? | SPY-see | Spicy describes flavour; hot can also describe temperature. | | |
| 10 | **slowly** (adverb, Restaurant) | At a low speed. | Please speak slowly while I read the menu. | SLOH-lee | Use slowly to ask for help when you do not understand: Could you say that more slowly? *(revised in rc2)* | | |
| 11 | **passport** (noun, Airport) | An official document used to identify a traveller abroad. | Please show your passport at the desk. | PASS-port | Keep your passport somewhere easy to reach; you show it at check-in, security and boarding. *(revised in rc2)* | | |
| 12 | **ticket** (noun, Airport) | A document or electronic record showing your right to travel. | I booked my ticket yesterday. | TIK-it | An airline ticket and a boarding pass are different documents. | | |
| 13 | **gate** (noun, Airport) | The airport area where passengers board a flight. | Our flight leaves from gate twelve. | gayt | Check the departure screen because a gate can change. | | |
| 14 | **luggage** (noun, Airport) | The bags and suitcases taken on a journey. | Where can I collect my luggage? | LUG-ij | Luggage is uncountable: say two bags, not two luggages. | | |
| 15 | **flight** (noun, Airport) | A journey made by an aircraft. | Our flight arrives at six. | flyt | Your flight number, such as BA 117, is on your ticket and on the departure screens. *(revised in rc2)* | | |
| 16 | **board** (verb, Airport) | To get onto a plane, train, or ship. | We can board the plane now. | bord | Wait until your boarding group is called. | | |
| 17 | **arrive** (verb, Airport) | To reach a destination. | We arrive in London tonight. | uh-RYV | Say arrive in a city and arrive at an airport. | | |
| 18 | **delayed** (adjective, Airport) | Later than the expected or planned time. | Our flight is delayed by an hour. | dih-LAYD | Delayed means late, not cancelled: the flight will still leave, but later than planned. *(revised in rc2)* | | |
| 19 | **ready** (adjective, Airport) | Prepared for an action or event. | Please have your passport ready. | RED-ee | Staff often say this before a check: have your ticket ready means have it in your hand. *(revised in rc2)* | | |
| 20 | **early** (adverb, Airport) | Before the expected or usual time. | We arrived early for our flight. | UR-lee | Early can also be an adjective, as in an early flight. | | |
| 21 | **room** (noun, Hotel) | A separate space inside a building. | I booked a room for two nights. | room (long oo) | In a hotel, a room usually means the space where you stay. | | |
| 22 | **key** (noun, Hotel) | An object used to open a lock. | May I have the key to my room? | kee | Many hotels use a key card instead of a metal key. | | |
| 23 | **towel** (noun, Hotel) | A piece of absorbent cloth used for drying. | Could I have a clean towel? | TOW-uhl | Ask for an extra towel if you need another one. | | |
| 24 | **pillow** (noun, Hotel) | A soft support for your head in bed. | Could you bring an extra pillow? | PIL-oh | Pillow is countable: one pillow, two pillows. Ask at reception if you need more. *(revised in rc2)* | | |
| 25 | **breakfast** (noun, Hotel) | The first meal of the day. | Is breakfast included in the room price? | BREK-fuhst | We usually say have breakfast: What time can we have breakfast? *(revised in rc2)* | | |
| 26 | **stay** (verb, Hotel) | To remain in a place for a period of time. | We will stay for three nights. | stay (rhymes with day) | Hotels commonly measure a stay in nights. | | |
| 27 | **reserve** (verb, Hotel) | To arrange for something to be kept for your use. | I would like to reserve a room. | rih-ZURV | Book is another verb commonly used for arranging a room. | | |
| 28 | **quiet** (adjective, Hotel) | Making little or no noise. | Could I have a quiet room? | KWY-uht | Quiet describes noise; quite is a different word. | | |
| 29 | **clean** (adjective, Hotel) | Free from dirt. | The room is clean and comfortable. | kleen | Clean can also be a verb: please clean the room. | | |
| 30 | **upstairs** (adverb, Hotel) | On or towards a higher floor in a building. | Your room is upstairs. | up-STAIRZ | The opposite is downstairs. | | |

Clues shown during play are the meaning (first clue) and the association text (second
clue), which are separate fields in the file; please glance at those too.

## Level lists (rc5): 1,538 words, not yet reviewed

Converted from the owner's older `words.xlsx` by `scripts/build_level_words.py`. Each word has
a level, a word type and three clues, and no example, pronunciation or usage note: nothing was
invented to fill those gaps. Clues are in English in every language, so the lists suit someone
who reads English.

| Language | Beginner | Novice | Intermediate | Advanced | Expert | Total |
| --- | --- | --- | --- | --- | --- | --- |
| English | 76 | 78 | 80 | 80 | 80 | 394 |
| Spanish | 80 | 76 | 77 | 79 | 77 | 389 |
| Italian | 79 | 77 | 78 | 80 | 76 | 390 |
| German | 70 | 70 | 76 | 76 | 73 | 365 |

What the conversion changed, and nothing else: 56 repeats within a language were removed,
keeping the lowest level; the 6 English words already on travel cards were removed (clean,
early, quiet, room, slowly, water); and capitals were normalised (lower case, except German
nouns and German phrases, which stay as the sheet wrote them).

**Reviewers:** one qualified reviewer per language, using the matching
`4-level-list-review-<language>.csv` in the acceptance kit, which has blank columns for their
verdicts. For each word check that:

1. The word is spelled correctly and really is a word or phrase of that language.
2. The English clues are correct for this word. They were written per concept and shared
   between languages, so a clue can fit the English meaning better than the translation.
3. The level is reasonable. The levels are the sheet's own and have not been assessed.

Automated checks confirm only the structure: no repeats, three different clues, and every
letter on the keyboard. They say nothing about accuracy. Rows such as the German `Quanten-`, a
word fragment, are examples of what only a reviewer can judge.

## Automated editorial warnings (24) — disposition

The content check flags usage notes that do not name the situation word (for example
"restaurant"). All 24 have a recorded decision in
[editorial-dispositions.json](editorial-dispositions.json): **7 notes rewritten** in plainer
English with a concrete use (slowly, passport, flight, delayed, ready, pillow, breakfast) and
**17 accepted** because the context is already clear or the note is a useful grammar point.
The rewritten notes are part of this review. `scripts/check_curated_content.py` fails if a
future warning has no recorded decision.

## Feedback lines (D-17, reversed in rc5)

Wrong- and right-guess messages are in `src/utils/feedback_lines.py`. rc2 replaced the original
lines because they mocked the learner and used idioms (D-17). In rc5 the owner restored the 40
originals word for word (decision DEC-07), so the sarcastic tone is deliberate. Reviewers and
facilitators need not correct it, but please note anything a learner could not understand.

## Provenance (for owner confirmation)

| Item | Where | Origin as far as the repository shows | Confirm |
| --- | --- | --- | --- |
| 30 teaching cards | `src/desktop/content/english.json` | Written for this project during rc1 ("original" per rc1 notes), with AI assistance; 7 usage notes revised in rc2 by Claude Code | Owner: authorship and licence |
| Level lists | `src/desktop/content/levels/*.json` | Converted in rc5 from `words.xlsx` in the owner's older Hangman Learning app (March 2025); who wrote the sheet is not recorded | Owner: authorship and licence |
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
  The installer currently shows no licence terms during setup (RK-7, decision DEC-14).
- Pillow's Windows build used here contains no GPL components (no libimagequant); its font
  module (FreeType, HarfBuzz) is not shipped.
