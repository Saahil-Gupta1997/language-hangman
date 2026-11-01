"""Check the explicit supported corpus without claiming pedagogical validation.

Every editorial heuristic warning must have a recorded disposition (revised or accepted,
with a reason) in docs/editorial-dispositions.json; an unreviewed warning
fails the check. Independent educator review is a separate, manual gate.
"""

import json
import sys
import unicodedata
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.services.curated_content import LEVEL_WORD_COUNT  # noqa: E402
from src.utils.config import CURATED_WORDS_DIR, LEVEL_WORDS_DIR  # noqa: E402
from src.utils.constants import (  # noqa: E402
    BOARD_LETTERS,
    EXTRA_LETTERS,
    GENERAL_SITUATION,
    LEVEL_WORD_SOURCE,
    PRACTICE_LANGUAGES,
    WORD_LEVELS,
)
from src.utils.word_bank_loader import build_seed_rows  # noqa: E402

payload = build_seed_rows(CURATED_WORDS_DIR)
if payload["has_errors"] or payload["valid_words"] != 30:
    raise SystemExit("The release must contain 30 structurally valid words.")
words = json.loads((CURATED_WORDS_DIR / "english.json").read_text(encoding="utf-8"))["words"]
assert len({row["word"] for row in words}) == 30
for situation in ("restaurant", "airport", "hotel"):
    assert sum(situation in row["situations"] for row in words) == 10
for row in words:
    assert row["source"] == "desktop-core"
    assert row["word"].casefold() in row["example_sentence"].casefold()
    assert row["synonym"] == row["synonym_hint"] == ""
    assert row["pronunciation_text"].casefold() != row["word"].casefold()
print("PASS: 30 unique words, 10 per situation, complete fields and contextual examples.")

warnings = [warning for file in payload["files"] for warning in file["warnings"]]
DISPOSITIONS = Path(__file__).resolve().parents[1] / "docs" / "editorial-dispositions.json"
dispositions = json.loads(DISPOSITIONS.read_text(encoding="utf-8"))
undispositioned = [
    warning for warning in warnings if warning.split("(", 1)[1].split(")", 1)[0] not in dispositions
]
if undispositioned:
    raise SystemExit("Warnings without a recorded disposition:\n" + "\n".join(undispositioned))
decisions = [dispositions[w.split("(", 1)[1].split(")", 1)[0]]["decision"] for w in warnings]
print(
    f"Editorial heuristic warnings: {len(warnings)}, all dispositioned "
    f"({decisions.count('revised')} revised, {decisions.count('accepted')} accepted)."
)
print("Independent educator review remains pending.")

levels = build_seed_rows(LEVEL_WORDS_DIR)
if levels["has_errors"] or levels["valid_words"] != LEVEL_WORD_COUNT:
    raise SystemExit(f"The level lists must contain {LEVEL_WORD_COUNT} structurally valid words.")
travel_words = {row["word"].casefold() for row in words}
for language in PRACTICE_LANGUAGES:
    path = LEVEL_WORDS_DIR / f"{language}.json"
    rows = json.loads(path.read_text(encoding="utf-8"))["words"]
    keys = set(BOARD_LETTERS + EXTRA_LETTERS.get(language, ""))
    assert Counter(row["difficulty"] for row in rows).keys() == set(WORD_LEVELS)
    assert len({row["word"].casefold() for row in rows}) == len(rows), f"{language}: repeats"
    for row in rows:
        assert row["language"] == language and row["source"] == LEVEL_WORD_SOURCE
        assert row["situations"] == [GENERAL_SITUATION]
        assert unicodedata.normalize("NFC", row["word"]) == row["word"]
        clues = [row[field].strip() for field in ("meaning", "synonym", "association")]
        assert len(set(clues)) == 3 and all(clues), f"{row['word']}: needs three clues"
        letters = {letter.lower() for letter in row["word"] if letter.isalpha()}
        assert letters <= keys, f"{row['word']}: a letter has no key"
    if language == "english":
        assert not travel_words & {row["word"].casefold() for row in rows}
print(
    f"PASS: {levels['valid_words']} level-list words in {len(PRACTICE_LANGUAGES)} languages: "
    "no repeats, three clues each, every letter on the keyboard."
)
print("The level lists have not been reviewed; their accuracy is not checked here.")
