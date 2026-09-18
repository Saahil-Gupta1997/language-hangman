"""Tests for Step 8 packaging, config, and maintenance workflows."""

from __future__ import annotations

import importlib
from pathlib import Path

from src import __release_name__, __version__
from src.cli import build_streamlit_command
from src.services.maintenance_service import MaintenanceService
from src.utils import config as config_module
from src.utils.config import PROJECT_ROOT


def test_config_respects_environment_overrides(monkeypatch, tmp_path) -> None:
    data_dir = tmp_path / "runtime-data"
    words_dir = tmp_path / "runtime-words"
    database_path = tmp_path / "runtime.db"

    monkeypatch.setenv("LANGUAGE_HANGMAN_DATA_DIR", str(data_dir))
    monkeypatch.setenv("LANGUAGE_HANGMAN_WORDS_DIR", str(words_dir))
    monkeypatch.setenv("LANGUAGE_HANGMAN_DB_PATH", str(database_path))

    reloaded_module = importlib.reload(config_module)

    assert reloaded_module.DATA_DIR == data_dir
    assert reloaded_module.WORDS_DIR == words_dir
    assert reloaded_module.DATABASE_PATH == database_path
    assert reloaded_module.APP_VERSION == __version__
    assert reloaded_module.APP_RELEASE_NAME == __release_name__
    assert reloaded_module.APP_VERSION_DISPLAY == f"v{__version__}"
    assert (
        reloaded_module.get_runtime_settings()["app_version_display"]
        == reloaded_module.APP_VERSION_DISPLAY
    )
    assert reloaded_module.get_runtime_settings()["database_path"] == str(database_path)

    monkeypatch.delenv("LANGUAGE_HANGMAN_DATA_DIR", raising=False)
    monkeypatch.delenv("LANGUAGE_HANGMAN_WORDS_DIR", raising=False)
    monkeypatch.delenv("LANGUAGE_HANGMAN_DB_PATH", raising=False)
    importlib.reload(config_module)


def test_maintenance_service_detects_share_blocking_artifacts(tmp_path) -> None:
    project_root = tmp_path / "project"
    (project_root / ".pytest_cache").mkdir(parents=True)
    (project_root / "data").mkdir(parents=True)
    (project_root / "data" / "app.db").write_text("", encoding="utf-8")
    (project_root / "src" / "__pycache__").mkdir(parents=True)

    service = MaintenanceService(
        project_root=project_root,
        db_path=project_root / "data" / "app.db",
        words_dir=project_root / "data" / "words",
    )
    release_check = service.find_local_artifacts()

    assert release_check["is_clean"] is False
    assert release_check["artifact_count"] >= 3
    assert any(path.endswith(".pytest_cache") for path in release_check["artifacts"])
    assert any(path.endswith("__pycache__") for path in release_check["artifacts"])


def test_maintenance_service_seed_word_banks_returns_import_summary(tmp_path) -> None:
    db_path = tmp_path / "seeded.db"
    service = MaintenanceService(
        db_path=db_path,
        words_dir=PROJECT_ROOT / "data" / "words",
    )

    import_summary = service.seed_word_banks()

    assert Path(import_summary["database_path"]) == db_path
    assert import_summary["valid_words"] > 0
    assert import_summary["inserted_count"] == import_summary["valid_words"]


def test_maintenance_service_runtime_summary_falls_back_to_word_bank_files(tmp_path) -> None:
    db_path = tmp_path / "uninitialized.db"
    db_path.write_text("", encoding="utf-8")
    service = MaintenanceService(
        db_path=db_path,
        words_dir=PROJECT_ROOT / "data" / "words",
    )

    runtime_summary = service.get_runtime_summary()

    assert runtime_summary["database_exists"] is True
    assert runtime_summary["database_ready"] is False
    assert runtime_summary["content_source"] == "word_bank_files"
    assert runtime_summary["total_words"] > 0
    assert "english" in runtime_summary["languages"]


def test_maintenance_service_runtime_summary_does_not_create_missing_database(tmp_path) -> None:
    db_path = tmp_path / "missing.db"
    service = MaintenanceService(
        db_path=db_path,
        words_dir=PROJECT_ROOT / "data" / "words",
    )

    runtime_summary = service.get_runtime_summary()

    assert runtime_summary["database_exists"] is False
    assert runtime_summary["database_ready"] is False
    assert runtime_summary["content_source"] == "word_bank_files"
    assert db_path.exists() is False


def test_build_streamlit_command_includes_port_and_headless() -> None:
    command = build_streamlit_command(port=8510, headless=True)

    assert command[:4] == [command[0], "-m", "streamlit", "run"]
    assert "--server.port" in command
    assert "8510" in command
    assert command[-2:] == ["--server.headless", "true"]
