"""Build a source release without copying local private data."""

import argparse
import os
from fnmatch import fnmatch
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

EXCLUDED_DIRS = {
    ".git", ".venv", ".idea", "__pycache__", ".pytest_cache", ".pytest_tmp",
    ".ruff_cache", ".mypy_cache", "htmlcov", "build", "dist", "release",
    "node_modules", "backups", ".streamlit",
}
EXCLUDED_PATTERNS = (
    "pytest_tmp*", "pytest-cache-files-*", "codex_pytest_tmp*", "*.pyc",
    "*.db*", "*.sqlite*", "*.zip", "*.log", ".coverage*", ".session_secret",
    ".desktop_login_handoff.json", ".env", ".env.*",
    "*.tsbuildinfo", "vite.config.js", "vite.config.d.ts",
)


def build_release(root: Path, output: Path, name: str) -> Path:
    """Create a new archive; never overwrite an existing release."""
    root, output = root.resolve(), output.resolve()
    if not name or name in {".", ".."} or any(char in name for char in '/\\:'):
        raise ValueError("Package name must be a single directory name.")
    output.mkdir(parents=True, exist_ok=True)
    archive_path = output / f"{name}.zip"
    with ZipFile(archive_path, "x", compression=ZIP_DEFLATED) as archive:
        for current, directories, files in os.walk(root):
            directories[:] = [
                item for item in directories
                if item not in EXCLUDED_DIRS
                and not any(fnmatch(item, pattern) for pattern in EXCLUDED_PATTERNS)
                and not (Path(current) / item).is_symlink()
                and (Path(current) / item).resolve() != output
            ]
            for filename in sorted(files):
                source = Path(current) / filename
                if source.is_symlink() or any(
                    fnmatch(filename, pattern) for pattern in EXCLUDED_PATTERNS
                ):
                    continue
                archive.write(source, Path(name) / source.relative_to(root))
    return archive_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="release")
    parser.add_argument("--name", default="")
    args = parser.parse_args()
    project_root = Path(__file__).resolve().parents[1]
    version = (project_root / "VERSION").read_text().strip()
    package_name = args.name or f"language_hangman-v{version}"
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = project_root / output_path
    print(build_release(project_root, output_path, package_name))
