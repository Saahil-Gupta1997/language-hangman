"""Source archives must exclude account storage and installation keys."""

from zipfile import ZipFile

import pytest

from scripts.build_release import build_release


def test_release_excludes_private_data_and_preserves_source(tmp_path):
    root = tmp_path / "project"
    for name in [
        "app.py",
        ".gitignore",
        "data/words/english.json",
        "data/app.db",
        "data/app.db-wal",
        "data/.session_secret",
        ".git/config",
        ".venv/private.py",
        "frontend/node_modules/package/index.js",
        "backups/progress.json",
        ".env",
        "server.log",
    ]:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("test", encoding="utf-8")
    archive = build_release(root, root / "release", "hangman")
    with ZipFile(archive) as package:
        assert set(package.namelist()) == {
            "hangman/app.py",
            "hangman/.gitignore",
            "hangman/data/words/english.json",
        }
    with pytest.raises(FileExistsError):
        build_release(root, root / "release", "hangman")


def release_check(root):
    from src.services.maintenance_service import MaintenanceService

    service = MaintenanceService(
        project_root=root, db_path=root / "data" / "app.db", words_dir=root / "data" / "words"
    )
    return service.find_local_artifacts()


def test_release_check_ignores_git_data_but_not_real_artifacts(tmp_path):
    """D-29: a branch named release/... puts a "release" folder inside .git."""
    root = tmp_path / "clone"
    (root / ".git" / "refs" / "heads" / "release").mkdir(parents=True)
    (root / ".git" / "objects" / "pack").mkdir(parents=True)
    (root / ".git" / "objects" / "pack" / "pack-1.zip").write_text("git data")
    (root / "src").mkdir()
    (root / "src" / "app.py").write_text("print('hello')\n")
    assert release_check(root)["is_clean"] is True

    (root / "release").mkdir()
    (root / "src" / "local.db").write_text("private")
    assert set(release_check(root)["relative_artifacts"]) == {"release", "src/local.db"}


def test_release_check_on_a_real_release_branch_clone_and_worktree(tmp_path):
    import shutil
    import subprocess

    if shutil.which("git") is None:
        pytest.skip("git is not installed")

    def git(*arguments, cwd):
        subprocess.run(
            ["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", *arguments],
            cwd=cwd,
            check=True,
            capture_output=True,
        )

    origin = tmp_path / "origin"
    origin.mkdir()
    (origin / "app.py").write_text("print('hello')\n")
    git("init", "-q", "-b", "main", cwd=origin)
    git("add", "app.py", cwd=origin)
    git("commit", "-q", "-m", "initial", cwd=origin)
    git("branch", "release/1.0", cwd=origin)
    git("clone", "-q", "-b", "release/1.0", str(origin), str(tmp_path / "clone"), cwd=tmp_path)
    assert (tmp_path / "clone" / ".git" / "refs" / "heads" / "release").is_dir()
    git("worktree", "add", "-q", str(tmp_path / "worktree"), "release/1.0", cwd=origin)
    for checkout in ("clone", "worktree"):
        result = release_check(tmp_path / checkout)
        assert result["is_clean"] is True, (checkout, result["relative_artifacts"])
