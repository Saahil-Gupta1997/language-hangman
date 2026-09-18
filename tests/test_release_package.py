"""Source archives must exclude account storage and installation keys."""

from zipfile import ZipFile

import pytest

from scripts.build_release import build_release


def test_release_excludes_private_data_and_preserves_source(tmp_path):
    root = tmp_path / "project"
    for name in [
        "app.py", ".gitignore", "data/words/english.json", "data/app.db",
        "data/app.db-wal", "data/.session_secret", ".git/config",
        ".venv/private.py", "frontend/node_modules/package/index.js",
        "backups/progress.json", ".env", "server.log",
    ]:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("test", encoding="utf-8")
    archive = build_release(root, root / "release", "hangman")
    with ZipFile(archive) as package:
        assert set(package.namelist()) == {
            "hangman/app.py", "hangman/.gitignore", "hangman/data/words/english.json"
        }
    with pytest.raises(FileExistsError):
        build_release(root, root / "release", "hangman")
