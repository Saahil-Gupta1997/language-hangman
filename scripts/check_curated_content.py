"""Check the structure of the word lists without claiming pedagogical validation.

Automated checks cover structure only: a passing run says nothing about whether a word, a
clue or a level is correct. Independent review is a separate, manual gate (ACCEPTANCE.md G9).
"""

import json
import sys
import unicodedata
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.models.game_round import base_letter  # noqa: E402
from src.services.curated_content import LEVEL_WORD_COUNT  # noqa: E402
from src.utils.config import LEVEL_WORDS_DIR  # noqa: E402
from src.utils.constants import (  # noqa: E402
    BOARD_LETTERS,
    GENERAL_SITUATION,
    LEVEL_WORD_SOURCE,
    PRACTICE_LANGUAGES,
    WORD_LEVELS,
)
from src.utils.word_bank_loader import build_seed_rows  # noqa: E402

levels = build_seed_rows(LEVEL_WORDS_DIR)
if levels["has_errors"] or levels["valid_words"] != LEVEL_WORD_COUNT:
    raise SystemExit(f"The word lists must contain {LEVEL_WORD_COUNT} structurally valid words.")
for language in PRACTICE_LANGUAGES:
    path = LEVEL_WORDS_DIR / f"{language}.json"
    rows = json.loads(path.read_text(encoding="utf-8"))["words"]
    assert Counter(row["difficulty"] for row in rows).keys() == set(WORD_LEVELS)
    assert len({row["word"].casefold() for row in rows}) == len(rows), f"{language}: repeats"
    for row in rows:
        assert row["language"] == language and row["source"] == LEVEL_WORD_SOURCE
        assert row["situations"] == [GENERAL_SITUATION]
        assert unicodedata.normalize("NFC", row["word"]) == row["word"]
        clues = [row[field].strip() for field in ("meaning", "synonym", "association")]
        assert len(set(clues)) == 3 and all(clues), f"{row['word']}: needs three clues"
        letters = {base_letter(letter) for letter in row["word"] if letter.isalpha()}
        assert letters <= set(BOARD_LETTERS), f"{row['word']}: a letter has no key"
print(
    f"PASS: {levels['valid_words']} words in {len(PRACTICE_LANGUAGES)} languages: no repeats, "
    "three clues each, every letter on the A-Z keys."
)
print("This checks their structure; their accuracy is not checked here.")
