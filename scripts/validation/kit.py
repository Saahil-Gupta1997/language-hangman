"""Build the printable acceptance kit for the people who run the human gates.

    python -m scripts.validation.kit <output folder> <installer sha256>

The worksheets are generated from the repository's own documents, so the steps a tester
follows and the steps the project records can never drift apart. Results stay blank: they
are filled in by the person who did the work, never from automated output.
"""

from __future__ import annotations

import csv
import html
import json
import re
import shutil
import sys
from pathlib import Path

from src import __version__
from src.utils.config import LEVEL_WORDS_DIR
from src.utils.constants import PRACTICE_LANGUAGES

ROOT = Path(__file__).resolve().parents[2]
STYLE = """
body { font-family: "Segoe UI", Arial, sans-serif; font-size: 11pt; color: #172B4D; margin: 24px; }
h1 { font-size: 18pt; } h2 { font-size: 14pt; margin-top: 22px; } h3 { font-size: 12pt; }
table { border-collapse: collapse; width: 100%; margin: 10px 0; }
th, td { border: 1px solid #888; padding: 6px; vertical-align: top; text-align: left; }
td:empty { height: 42px; }
code { font-family: Consolas, monospace; background: #F1F5F9; padding: 0 2px; }
pre { background: #F1F5F9; padding: 8px; white-space: pre-wrap; }
.banner { border: 2px solid #155E75; padding: 8px 12px; margin-bottom: 16px; }
@media print {
  body { margin: 0; }
  h2 { page-break-after: avoid; }
  tr { page-break-inside: avoid; }
}
"""


def inline(text):
    text = html.escape(text, quote=False)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![*\w])\*([^*]+)\*(?!\w)", r"<em>\1</em>", text)
    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", text)  # a printout cannot follow links


def convert(markdown):
    """Render the Markdown subset these worksheets use: headings, lists, tables, code."""
    out, lines, index = [], markdown.splitlines(), 0
    while index < len(lines):
        line = lines[index]
        if line.startswith("```"):
            block = []
            index += 1
            while index < len(lines) and not lines[index].startswith("```"):
                block.append(html.escape(lines[index]))
                index += 1
            out.append("<pre>" + "\n".join(block) + "</pre>")
        elif re.match(r"#{1,4} ", line):
            level = len(line.split(" ")[0])
            out.append(f"<h{level}>{inline(line[level + 1:])}</h{level}>")
        elif line.startswith("|"):
            rows = []
            while index < len(lines) and lines[index].startswith("|"):
                rows.append([cell.strip() for cell in lines[index].strip().strip("|").split("|")])
                index += 1
            index -= 1
            body = [row for row in rows[1:] if not all(set(cell) <= set("-: ") for cell in row)]
            out.append("<table><tr>" + "".join(f"<th>{inline(c)}</th>" for c in rows[0]) + "</tr>")
            out += [
                "<tr>" + "".join(f"<td>{inline(c)}</td>" for c in row) + "</tr>" for row in body
            ]
            out.append("</table>")
        elif re.match(r"(\d+\.|-) ", line):
            ordered, items = line[0].isdigit(), []
            while index < len(lines) and (
                re.match(r"(\d+\.|-) ", lines[index]) or lines[index].startswith("   ")
            ):
                if re.match(r"(\d+\.|-) ", lines[index]):
                    items.append(re.sub(r"^(\d+\.|-) ", "", lines[index]))
                else:
                    items[-1] += " " + lines[index].strip()
                index += 1
            index -= 1
            tag = "ol" if ordered else "ul"
            out.append(f"<{tag}>" + "".join(f"<li>{inline(i)}</li>" for i in items) + f"</{tag}>")
        elif line.strip():
            paragraph = [line.strip()]
            while (
                index + 1 < len(lines)
                and lines[index + 1].strip()
                and not re.match(r"(#{1,4} |\||```|(\d+\.|-) )", lines[index + 1])
            ):
                index += 1
                paragraph.append(lines[index].strip())
            out.append(f"<p>{inline(' '.join(paragraph))}</p>")
        index += 1
    return "\n".join(out)


def page(title, banner, markdown):
    return (
        f"<!doctype html><html lang='en'><head><meta charset='utf-8'><title>{title}</title>"
        f"<style>{STYLE}</style></head><body><div class='banner'>{banner}</div>"
        f"{convert(markdown)}</body></html>"
    )


def level_review_sheets(output):
    """One spreadsheet per language for G9: the verdict columns stay blank for the reviewer."""
    for language in PRACTICE_LANGUAGES:
        words = json.loads((LEVEL_WORDS_DIR / f"{language}.json").read_text(encoding="utf-8"))
        with (output / f"4-level-list-review-{language}.csv").open(
            "w", encoding="utf-8-sig", newline=""
        ) as sheet:
            table = csv.writer(sheet)
            table.writerow(
                ["Word", "Type", "Level", "Meaning", "Synonyms", "Association"]
                + ["Word correct?", "Level fits?", "Clues correct?", "Correction"]
            )
            for word in words["words"]:
                table.writerow(
                    [word["word"], word["category"], word["difficulty"], word["meaning"]]
                    + [word["synonym"], word["association"], "", "", "", ""]
                )


def build(output, installer_sha256):
    output = Path(output)
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    docs = ROOT / "docs"
    acceptance = (docs / "ACCEPTANCE.md").read_text(encoding="utf-8")
    manual = acceptance[
        acceptance.index("## Manual checks") : acceptance.index("## Release evidence index")
    ]
    banner = (
        f"Language Hangman <strong>{__version__}</strong>. Installer "
        f"<code>LanguageHangman-{__version__}-Setup.exe</code>, SHA256 "
        f"<code>{installer_sha256}</code>. Record only what you observe; leave anything you "
        "did not do blank."
    )
    documents = {
        "1-manual-checks-M1-M4": ("Manual checks M1-M4", manual),
        "2-content-review-worksheet": (
            "Content review worksheet",
            (docs / "CONTENT_REVIEW.md").read_text(encoding="utf-8"),
        ),
        "3-learner-sessions": (
            "Learner sessions",
            (docs / "USER_ACCEPTANCE.md").read_text(encoding="utf-8"),
        ),
    }
    for name, (title, markdown) in documents.items():
        (output / f"{name}.html").write_text(page(title, banner, markdown), encoding="utf-8")
        (output / f"{name}.md").write_text(markdown, encoding="utf-8", newline="\n")
    level_review_sheets(output)
    (output / "README.txt").write_text(
        f"""Language Hangman {__version__} - acceptance kit

Everything the people running the remaining acceptance gates need. Each HTML file prints
from any browser (File > Print); the .md files are the same text for editing.

Installer: ..\\LanguageHangman-{__version__}-Setup.exe
SHA256:    {installer_sha256}
Check it first in PowerShell:
    Get-FileHash .\\LanguageHangman-{__version__}-Setup.exe -Algorithm SHA256
It is not code-signed: Windows SmartScreen will say "unknown publisher".

1-manual-checks-M1-M4       For a tester; roughly 90 minutes in total (estimate).
                            Gates G5-G8: clean install on a Windows account without
                            Python, keyboard only, real 100/125/150% display scaling,
                            and recovery through the installed app.
2-content-review-worksheet  For a qualified English teacher; roughly 2 hours (estimate).
                            Gate G9: one row per teaching card, plus the intended-learner
                            profile to confirm or correct.
3-learner-sessions          For a facilitator; roughly 30-45 minutes per learner
                            (estimate), five learners. Gate G10: consent, tasks, what to
                            record, and the record table. Sessions use the English travel
                            cards unless the owner decides otherwise.
4-level-list-review-*.csv   One sheet per language for a qualified reviewer of that
                            language. Gate G9: 1,538 words in all; open in Excel and fill
                            in the blank columns. Nobody has reviewed these words yet.

Please return the completed record tables (a photo or scan is fine) with the tester's or
reviewer's name or initials and the date. Report anything that goes wrong, including what
you did, what you expected and what happened; the diagnostics export in Settings helps.
Do not send learners' names or anyone's full database.
""",
        encoding="utf-8",
        newline="\n",
    )
    print("acceptance kit:", ", ".join(sorted(path.name for path in output.iterdir())))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
