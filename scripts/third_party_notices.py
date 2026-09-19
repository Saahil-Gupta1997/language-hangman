"""Third-party notices shipped with the Windows build (T-28).

    python scripts/third_party_notices.py collect
        Regenerate packaging/third-party/ from the build environment. Run it with the build
        interpreter after installing requirements-build.txt, on the machine with Inno Setup.
        It stops if any installed version differs from the inventory below: update the
        inventory first, then review the regenerated files.

    python scripts/third_party_notices.py check <app folder> [--installed]
        Fail unless every file in a built (dist/LanguageHangman) or installed application
        folder belongs to a listed component, and the notices in it are present and
        byte-identical to packaging/third-party/. Without --installed it must run with the
        interpreter that built the folder, and also fails if that environment's versions
        differ from the inventory. The build script and the installer validation run this.
"""

from __future__ import annotations

import argparse
import hashlib
import html.parser
import shutil
import sys
from fnmatch import fnmatchcase
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTICES = ROOT / "packaging" / "third-party"
PYTHON_PYDS = (
    "_bz2 _ctypes _decimal _elementtree _hashlib _lzma _queue _socket _sqlite3 _ssl _tkinter "
    "_uuid _wmi pyexpat select unicodedata"
).split()

# name, version, licence, what ships (patterns relative to the app folder), notice files,
# and notes. Versions were read from the build environment on 2026-09-19 (collect verifies).
COMPONENTS = [
    {
        "name": "Language Hangman (this project)",
        "version": "see the title bar",
        "licence": "Not yet chosen by the owner (decision DEC-08)",
        "files": ["LanguageHangman.exe", "_internal/src/*"],
        "notices": [],
        "notes": "Application code (inside LanguageHangman.exe), the 30-word content file "
        "and the application icon.",
    },
    {
        "name": "PyInstaller bootloader",
        "version": "6.11.1",
        "licence": "GPL-2.0-or-later with the PyInstaller bootloader exception",
        "files": ["LanguageHangman.exe"],
        "notices": ["PyInstaller-6.11.1-COPYING.txt"],
        "notes": "The exception allows the bootloader to be distributed with programs under "
        "any licence.",
    },
    {
        "name": "Python (CPython) runtime and standard library",
        "version": "3.12.1",
        "licence": "PSF-2.0, with the licences of incorporated software",
        "files": [
            "LanguageHangman.exe",
            "_internal/python312.dll",
            "_internal/base_library.zip",
            *[f"_internal/{name}.pyd" for name in PYTHON_PYDS],
        ],
        "notices": ["Python-3.12.1-LICENSE.txt", "Python-3.12.1-incorporated-software.txt"],
        "notes": "Standard-library modules are inside LanguageHangman.exe and base_library.zip. "
        "Statically linked: bzip2 1.0.8 (bzip2 licence), xz/liblzma 5.2.5 (public domain), "
        "libmpdec 2.5.1 (BSD-2-Clause), expat 2.5.0 (MIT), zlib 1.2.13 (Zlib).",
    },
    {
        "name": "Microsoft Visual C++ runtime (VCRUNTIME140.dll)",
        "version": "14.38.33126.1",
        "licence": "Microsoft Distributable Code, redistributed as part of the Python runtime",
        "files": ["_internal/VCRUNTIME140.dll"],
        "notices": ["Python-3.12.1-LICENSE.txt"],
        "notes": "Conditions: 'Additional Conditions for this Windows binary build' in the "
        "Python licence file.",
    },
    {
        "name": "OpenSSL",
        "version": "3.0.11",
        "licence": "Apache-2.0",
        "files": ["_internal/libcrypto-3.dll", "_internal/libssl-3.dll"],
        "notices": ["Apache-2.0.txt"],
        "notes": "Used by Python's ssl and hashlib modules.",
    },
    {
        "name": "libffi",
        "version": "3.4.4",
        "licence": "MIT",
        "files": ["_internal/libffi-8.dll"],
        "notices": ["Python-3.12.1-LICENSE.txt"],
        "notes": "",
    },
    {
        "name": "SQLite",
        "version": "3.43.1",
        "licence": "Public domain",
        "files": ["_internal/sqlite3.dll"],
        "notices": [],
        "notes": "The SQLite authors have dedicated the code to the public domain.",
    },
    {
        "name": "Tcl/Tk",
        "version": "8.6.13",
        "licence": "Tcl/Tk licence (BSD-style)",
        "files": [
            "_internal/tcl86t.dll",
            "_internal/tk86t.dll",
            "_internal/_tcl_data/*",
            "_internal/_tk_data/*",
            "_internal/tcl8/*",
        ],
        "notices": ["Tcl-Tk-8.6.13-license.terms.txt"],
        "notes": "",
    },
    {
        "name": "zlib",
        "version": "1.2.13",
        "licence": "Zlib",
        "files": ["_internal/zlib1.dll"],
        "notices": ["Python-3.12.1-incorporated-software.txt"],
        "notes": "",
    },
    {
        "name": "Pillow",
        "version": "12.3.0",
        "licence": "MIT-CMU, with the licences of its bundled libraries",
        "files": ["LanguageHangman.exe", "_internal/PIL/*"],
        "notices": ["Pillow-12.3.0-LICENSE.txt"],
        "notes": "The shipped modules use libjpeg-turbo 3.1.4.1, zlib-ng 2.3.3, libtiff 4.7.1, "
        "OpenJPEG 2.5.4, libwebp 1.6.0, libavif 1.4.2 and Little CMS 2.19. The licence file "
        "covers every library Pillow's Windows wheel can contain; its font module (FreeType, "
        "HarfBuzz) is not shipped, and this build contains no libimagequant or libxcb.",
    },
    {
        "name": "CustomTkinter",
        "version": "5.2.2",
        "licence": "MIT",
        "files": ["LanguageHangman.exe", "_internal/customtkinter/*"],
        "notices": ["CustomTkinter-5.2.2-LICENSE.txt"],
        "notes": "Includes its themes, icon and CustomTkinter_shapes_font.",
    },
    {
        "name": "Roboto font (bundled by CustomTkinter)",
        "version": "2.137",
        "licence": "Apache-2.0",
        "files": ["_internal/customtkinter/assets/fonts/Roboto/*"],
        "notices": ["Apache-2.0.txt"],
        "notes": "Copyright 2011 Google Inc. Roboto is a trademark of Google.",
    },
    {
        "name": "darkdetect",
        "version": "0.8.0",
        "licence": "BSD-3-Clause",
        "files": ["LanguageHangman.exe"],
        "notices": ["darkdetect-0.8.0-LICENSE.txt"],
        "notes": "A CustomTkinter dependency, inside LanguageHangman.exe.",
    },
    {
        "name": "packaging",
        "version": "26.3",
        "licence": "Apache-2.0 OR BSD-2-Clause",
        "files": ["LanguageHangman.exe"],
        "notices": [
            "packaging-26.3-LICENSE.txt",
            "packaging-26.3-LICENSE.BSD.txt",
            "Apache-2.0.txt",
        ],
        "notes": "A CustomTkinter dependency, inside LanguageHangman.exe.",
    },
    {
        "name": "Inno Setup",
        "version": "6.7.3",
        "licence": "Inno Setup License",
        "files": ["unins000.exe", "unins000.dat"],
        "notices": ["InnoSetup-6.7.3-license.txt"],
        "notes": "The setup program and the uninstaller it installs.",
    },
]
NOTICE_FILES = ["THIRD-PARTY-NOTICES.txt", "licenses/*"]


def expected_versions():
    """Read the versions actually present in the running build environment."""
    import sqlite3
    import ssl
    import tkinter
    from importlib.metadata import version

    return {
        "Python (CPython) runtime and standard library": sys.version.split()[0],
        "OpenSSL": ssl.OPENSSL_VERSION.split()[1],
        "SQLite": sqlite3.sqlite_version,
        "Tcl/Tk": tkinter.Tcl().eval("info patchlevel"),
        "Pillow": version("pillow"),
        "CustomTkinter": version("customtkinter"),
        "darkdetect": version("darkdetect"),
        "packaging": version("packaging"),
        "PyInstaller bootloader": version("pyinstaller"),
    }


class _Text(html.parser.HTMLParser):
    """Plain text of the licence page body, keeping <pre> blocks as they are."""

    BLOCKS = {"p", "div", "section", "h1", "h2", "h3", "h4", "li", "pre", "br", "tr"}

    def __init__(self):
        super().__init__()
        self.parts, self.pre, self.inside, self.skip = [], 0, False, 0

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "section" and attributes.get("id") == "history-and-license":
            self.inside = True
        if tag == "a" and "headerlink" in (attributes.get("class") or ""):
            self.skip += 1
        if tag == "pre":
            self.pre += 1
        if self.inside and tag in self.BLOCKS:
            self.parts.append("\n\n" if tag not in {"br", "li", "tr"} else "\n")
        if self.inside and tag == "li":
            self.parts.append("- ")

    def handle_endtag(self, tag):
        if tag == "a" and self.skip:
            self.skip -= 1
        if tag == "pre":
            self.pre -= 1
        if tag in {"h1", "h2", "h3"} and self.inside:
            self.parts.append("\n" + "-" * 70)

    def handle_data(self, data):
        if not self.inside or self.skip:
            return
        if self.pre:
            self.parts.append(data)
            return
        text = " ".join(data.split())
        self.parts.append(
            (" " if data[:1].isspace() else "")
            + text
            + (" " if data[-1:].isspace() and text else "")
        )

    def text(self):
        lines = [line.rstrip() for line in "".join(self.parts).splitlines()]
        out, blank = [], 0
        for line in lines:
            blank = blank + 1 if not line else 0
            if blank <= 1:
                out.append(line)
        return "\n".join(out).strip() + "\n"


def version_drift():
    """Components whose listed version differs from the running build environment."""
    found = expected_versions()
    return {
        component["name"]: (component["version"], found[component["name"]])
        for component in COMPONENTS
        if component["name"] in found and component["version"] != found[component["name"]]
    }


def collect():
    from importlib.metadata import distribution

    import customtkinter

    wrong = version_drift()
    if wrong:
        sys.exit(f"Inventory versions differ from this environment (listed, found): {wrong}")

    def metadata_file(package, name):
        installed = distribution(package)
        for file in installed.files:
            if file.parts[0].endswith(".dist-info") and "/".join(file.parts[1:]) == name:
                return Path(installed.locate_file(file))
        raise FileNotFoundError(f"{package}: {name}")

    python = Path(sys.base_prefix)
    inno = Path.home() / "AppData/Local/Programs/Inno Setup 6/license.txt"
    if not inno.exists():
        inno = Path("C:/Program Files (x86)/Inno Setup 6/license.txt")
    sources = {
        "Python-3.12.1-LICENSE.txt": python / "LICENSE.txt",
        "Tcl-Tk-8.6.13-license.terms.txt": python / "tcl/tk8.6/license.terms",
        "Pillow-12.3.0-LICENSE.txt": metadata_file("pillow", "licenses/LICENSE"),
        "CustomTkinter-5.2.2-LICENSE.txt": metadata_file("customtkinter", "LICENSE"),
        "darkdetect-0.8.0-LICENSE.txt": metadata_file("darkdetect", "LICENSE"),
        "packaging-26.3-LICENSE.txt": metadata_file("packaging", "licenses/LICENSE"),
        "packaging-26.3-LICENSE.BSD.txt": metadata_file("packaging", "licenses/LICENSE.BSD"),
        "Apache-2.0.txt": metadata_file("packaging", "licenses/LICENSE.APACHE"),
        "PyInstaller-6.11.1-COPYING.txt": metadata_file("pyinstaller", "COPYING.txt"),
        "InnoSetup-6.7.3-license.txt": inno,
    }
    licences = NOTICES / "licenses"
    shutil.rmtree(NOTICES, ignore_errors=True)
    licences.mkdir(parents=True)
    for name, source in sources.items():
        text = source.read_text(encoding="utf-8", errors="strict")
        (licences / name).write_text(text.replace("\r\n", "\n"), encoding="utf-8", newline="\n")
    page = _Text()
    page.feed((python / "Doc/html/license.html").read_text(encoding="utf-8"))
    (licences / "Python-3.12.1-incorporated-software.txt").write_text(
        "History and License, from the Python 3.12.1 documentation (license.html), as text.\n\n"
        + page.text(),
        encoding="utf-8",
        newline="\n",
    )
    assert Path(customtkinter.__file__).parent.joinpath("assets/fonts/Roboto").is_dir()
    (NOTICES / "THIRD-PARTY-NOTICES.txt").write_text(summary(), encoding="utf-8", newline="\n")
    print(f"Wrote {len(sources) + 2} files to {NOTICES.relative_to(ROOT)}")


def summary():
    lines = [
        "Language Hangman - third-party notices",
        "",
        "Language Hangman for Windows includes the third-party software listed below. Each",
        "component remains under its own licence; the full texts are in the 'licenses' folder",
        "next to this file. The licence for Language Hangman's own code and content has not",
        "yet been chosen by its owner.",
        "",
    ]
    for component in COMPONENTS:
        lines += [
            component["name"],
            f"  Version:  {component['version']}",
            f"  Licence:  {component['licence']}",
            f"  Files:    {', '.join(component['files'])}",
        ]
        if component["notices"]:
            lines.append(f"  Text:     {', '.join('licenses/' + n for n in component['notices'])}")
        if component["notes"]:
            lines.append(f"  Note:     {component['notes']}")
        lines.append("")
    return "\n".join(lines)


def check(folder, installed=False):
    folder = Path(folder)
    patterns = [pattern for component in COMPONENTS for pattern in component["files"]]
    patterns += NOTICE_FILES
    if not installed:
        patterns = [p for p in patterns if not p.startswith("unins000")]
    problems = []
    if not installed:  # run by the build with the interpreter that produced the folder
        problems += [
            f"built with {n} {v[1]}, notices list {v[0]}" for n, v in version_drift().items()
        ]
    files = sorted(p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file())
    uncovered = [name for name in files if not any(fnmatchcase(name, p) for p in patterns)]
    problems += [f"not in the inventory: {name}" for name in uncovered]
    for component in COMPONENTS:
        for pattern in component["files"]:
            if pattern.startswith("unins000") and not installed:
                continue
            if not any(fnmatchcase(name, pattern) for name in files):
                problems.append(f"expected but missing: {pattern} ({component['name']})")
    expected = sorted(p.relative_to(NOTICES).as_posix() for p in NOTICES.rglob("*") if p.is_file())
    for name in expected:
        shipped = folder / name
        if not shipped.is_file():
            problems.append(f"notice missing: {name}")
        elif _sha256(shipped) != _sha256(NOTICES / name):
            problems.append(f"notice differs from packaging/third-party: {name}")
    referenced = {n for component in COMPONENTS for n in component["notices"]}
    problems += [
        f"inventory names a missing notice: {n}"
        for n in sorted(referenced)
        if not (NOTICES / "licenses" / n).is_file()
    ]
    if (NOTICES / "THIRD-PARTY-NOTICES.txt").read_text(encoding="utf-8") != summary():
        problems.append("THIRD-PARTY-NOTICES.txt is out of date; run collect")
    for problem in problems:
        print(problem)
    print(f"{len(files)} files checked, {len(expected)} notice files, {len(problems)} problems")
    return not problems


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("collect")
    checker = commands.add_parser("check")
    checker.add_argument("folder")
    checker.add_argument("--installed", action="store_true")
    arguments = parser.parse_args()
    if arguments.command == "collect":
        collect()
    else:
        sys.exit(0 if check(arguments.folder, arguments.installed) else 1)
