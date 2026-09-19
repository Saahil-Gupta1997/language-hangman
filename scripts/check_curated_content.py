"""Check the explicit supported corpus without claiming pedagogical validation.

Every editorial heuristic warning must have a recorded disposition (revised or accepted,
with a reason) in docs/editorial-dispositions.json; an unreviewed warning
fails the check. Independent educator review is a separate, manual gate.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.utils.config import CURATED_WORDS_DIR  # noqa: E402
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
