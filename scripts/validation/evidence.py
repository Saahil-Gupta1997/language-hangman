"""Copy release evidence into the repository, with personal paths removed.

    python -m scripts.validation.evidence scrub <in> [<out>]
    python -m scripts.validation.evidence collect <staging folder> <evidence folder>

Evidence is written on someone's computer, so it carries their user name, machine and file
paths. Everything copied here is rewritten to placeholders, and screenshots are refused
unless they are verifiably the application's own window (incident I-3).
"""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

RULES = (
    (
        r"[A-Za-z]:[\\/]+Users[\\/]+[^\\/\s\"']+[\\/]+AppData[\\/]+Local[\\/]+Temp[^\s\"']*",
        "<TEMP>",
    ),
    (
        r"[A-Za-z]:[\\/]+Users[\\/]+[^\\/\s\"']+[\\/]+AppData[\\/]+Local[\\/]+Programs[\\/]+LanguageHangman",
        r"%LOCALAPPDATA%\\Programs\\LanguageHangman",
    ),
    (
        r"[A-Za-z]:[\\/]+Users[\\/]+[^\\/\s\"']+[\\/]+AppData[\\/]+Local[\\/]+LanguageHangman",
        r"%LOCALAPPDATA%\\LanguageHangman",
    ),
    (r"[A-Za-z]:[\\/]+Users[\\/]+[^\\/\s\"']+[\\/]+AppData[\\/]+Roaming", "%APPDATA%"),
    (
        r"[A-Za-z]:[\\/]+Users[\\/]+[^\\/\s\"']+[\\/]+OneDrive[\\/]+Documents[\\/]+Hangman",
        "<PROJECT>",
    ),
    (r"(\.\.[\\/])+OneDrive[\\/]+Documents[\\/]+Hangman", "<PROJECT>"),
    (r"[A-Za-z]:[\\/]+Users[\\/]+[^\\/\s\"']+", "<HOME>"),
    (r"hostname=\"[^\"]*\"", 'hostname="<HOST>"'),
    (r"(User name|Computer name|Username):\s*\S+", r"\1: <redacted>"),
)


def scrub(text, extra=()):
    """Replace personal paths and names. ``extra`` catches whatever the rules above miss."""
    for pattern, replacement in RULES:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    for pattern, replacement in extra:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text.replace("�", "·")


def copy_text(source, destination, extra=()):
    raw = Path(source).read_bytes()
    for encoding in ("utf-8-sig", "utf-16", "cp1252"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        text = raw.decode("utf-8", "replace")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(scrub(text, extra), encoding="utf-8", newline="\n")


def copy_image(source, destination):
    """Copy a screenshot only if it is verifiably the application's own window."""
    from PIL import Image

    sys.path.insert(0, str(Path.cwd()))
    from scripts.validation.window import is_app_window

    image = Image.open(source)
    if not is_app_window(image):
        raise SystemExit(f"refusing to copy {Path(source).name}: not verifiably the app window")
    if min(image.size) < 300:
        raise SystemExit(f"refusing to copy {Path(source).name}: {image.size} looks cropped")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def collect(staging, evidence, extra=()):
    """Copy a staging tree into the repository's evidence folder, scrubbing as it goes."""
    staging, evidence = Path(staging), Path(evidence)
    if evidence.exists():
        shutil.rmtree(evidence)
    texts = images = 0
    for source in sorted(staging.rglob("*")):
        if not source.is_file():
            continue
        destination = evidence / source.relative_to(staging)
        if source.suffix.lower() in (".png", ".jpg"):
            copy_image(source, destination)
            images += 1
        elif source.suffix.lower() in (".txt", ".log", ".json", ".xml", ".md", ".csv"):
            copy_text(source, destination, extra)
            texts += 1
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
    leaks = [
        str(path.relative_to(evidence))
        for path in evidence.rglob("*")
        if path.is_file()
        and path.suffix.lower() in (".txt", ".log", ".json", ".xml", ".md")
        and re.search(
            r"saahi|onedrive|[A-Za-z]:\\Users",
            path.read_text(encoding="utf-8", errors="replace"),
            re.I,
        )
    ]
    print(f"copied {texts} text files and {images} screenshots to {evidence}")
    print("personal data remaining:", ", ".join(leaks) if leaks else "none")
    return not leaks


if __name__ == "__main__":
    if sys.argv[1] == "scrub":
        text = scrub(Path(sys.argv[2]).read_text(encoding="utf-8", errors="replace"))
        if len(sys.argv) > 3:
            Path(sys.argv[3]).write_text(text, encoding="utf-8", newline="\n")
        else:
            sys.stdout.write(text)
    else:
        sys.exit(0 if collect(sys.argv[2], sys.argv[3]) else 1)
