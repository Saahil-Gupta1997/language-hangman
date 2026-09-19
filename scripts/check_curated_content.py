"""Check the explicit supported corpus without claiming pedagogical validation."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.utils.config import CURATED_WORDS_DIR  # noqa: E402
from src.utils.word_bank_loader import build_seed_rows  # noqa: E402

payload = build_seed_rows(CURATED_WORDS_DIR)
if payload["has_errors"] or payload["valid_words"] != 30:
    raise SystemExit("The release must contain 30 structurally valid words.")
words = json.loads((CURATED_WORDS_DIR / "english.json").read_text())["words"]
assert len({row["word"] for row in words}) == 30
for situation in ("restaurant", "airport", "hotel"):
    assert sum(situation in row["situations"] for row in words) == 10
for row in words:
    assert row["source"] == "desktop-core"
    assert row["word"].casefold() in row["example_sentence"].casefold()
    assert row["synonym"] == row["synonym_hint"] == ""
    assert row["pronunciation_text"].casefold() != row["word"].casefold()
print("PASS: 30 unique words, 10 per situation, complete fields and contextual examples.")
print("Independent educator review remains pending.")
print("Editorial heuristic warnings:", sum(len(file["warnings"]) for file in payload["files"]))
