"""Convert the owner's older word sheet into the desktop level lists.

    python scripts/build_level_words.py <words.xlsx>

Run once to create src/desktop/content/levels/; the JSON files are then the source of truth.
The sheet is read with the standard library, so the app needs no Excel dependency.

Every row is kept as written apart from two checked changes, both reported here: a word that
repeats within a language keeps only its lowest level, and capitals are normalised, which
keeps German nouns and German phrases as written. Nothing here checks accuracy: a qualified
reviewer has not seen this content (ACCEPTANCE.md G9).
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.utils.constants import GENERAL_SITUATION, LEVEL_WORD_SOURCE, WORD_LEVELS  # noqa: E402

OUTPUT = ROOT / "src" / "desktop" / "content" / "levels"
SHEETS = ("English", "Spanish", "Italian", "German")
MAIN = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
RELATIONSHIP = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"


def read_rows(path):
    """Return {sheet name: [(row number, {column letter: text})]} from an .xlsx file."""
    with zipfile.ZipFile(path) as book:
        shared = [
            "".join(text.text or "" for text in item.iter(MAIN + "t"))
            for item in ET.fromstring(book.read("xl/sharedStrings.xml")).findall(MAIN + "si")
        ]
        targets = {
            link.get("Id"): link.get("Target")
            for link in ET.fromstring(book.read("xl/_rels/workbook.xml.rels"))
        }
        sheets = {}
        for sheet in ET.fromstring(book.read("xl/workbook.xml")).find(MAIN + "sheets"):
            target = targets[sheet.get(RELATIONSHIP)].lstrip("/")
            target = target if target.startswith("xl/") else f"xl/{target}"
            rows = []
            for row in ET.fromstring(book.read(target)).iter(MAIN + "row"):
                cells = {}
                for cell in row.findall(MAIN + "c"):
                    value = cell.find(MAIN + "v")
                    if value is not None:
                        column = re.match(r"[A-Z]+", cell.get("r")).group()
                        shared_text = cell.get("t") == "s"
                        cells[column] = shared[int(value.text)] if shared_text else value.text
                rows.append((int(row.get("r")), cells))
            sheets[sheet.get("name")] = rows
    return sheets


def clean(text):
    return unicodedata.normalize("NFC", " ".join(str(text or "").split()))


def spelled(word, language, category):
    """Return the word as a learner should see it."""
    if language != "german":
        return word.lower()
    if category == "noun" or " " in word or "-" in word:
        return word  # nouns take a capital, and phrases can hold nouns: keep them as written
    return word[0].lower() + word[1:]


def convert(rows, language):
    """Return the kept word entries and a count of what was left out."""
    candidates = []
    for number, cells in rows[1:]:
        word = clean(cells.get("A"))
        if word:
            category, level = clean(cells.get("B")).lower(), clean(cells.get("F")).lower()
            candidates.append((WORD_LEVELS.index(level), number, word, category, level, cells))

    kept, seen, left_out = [], set(), Counter()
    for _, number, word, category, level, cells in sorted(candidates, key=lambda row: row[:2]):
        key = word.casefold()
        if key in seen:
            left_out["repeat of a word at the same or a lower level"] += 1
            continue
        seen.add(key)
        meaning, synonym, association = (clean(cells.get(column)) for column in "CDE")
        kept.append(
            {
                "word_id": f"levels_{language}_{number:04d}",
                "word": spelled(word, language, category),
                "language": language,
                "category": category,
                "difficulty": level,
                "meaning": meaning,
                "translation": meaning,
                "hint": meaning,
                "meaning_hint": meaning,
                "example_sentence": "",
                "sentence_translation": "",
                "pronunciation_text": "",
                "usage_note": "",
                "synonym": synonym,
                "synonym_hint": synonym,
                "association": association,
                "association_hint": association,
                "situations": [GENERAL_SITUATION],
                "source": LEVEL_WORD_SOURCE,
                "notes": f"words.xlsx, {language.title()} sheet, row {number}. Not yet reviewed.",
                "tags": [],
            }
        )
    return kept, left_out


def main(sheet_path):
    sheets = read_rows(sheet_path)
    OUTPUT.mkdir(exist_ok=True)
    total = 0
    for sheet in SHEETS:
        language = sheet.lower()
        words, left_out = convert(sheets[sheet], language)
        description = (
            f"{sheet} words at five levels, converted from the owner's words.xlsx. "
            "Clues are in English. Not yet reviewed."
        )
        (OUTPUT / f"{language}.json").write_text(
            json.dumps(
                {"language": language, "description": description, "words": words},
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
        levels = Counter(word["difficulty"] for word in words)
        print(f"{sheet}: {len(words)} words {dict(levels)}; left out {dict(left_out)}")
        total += len(words)
    print(f"Total: {total} words")


if __name__ == "__main__":
    main(sys.argv[1])
