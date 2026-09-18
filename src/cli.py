"""Small local admin CLI for packaging, content, release, and backup workflows."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from src.services.maintenance_service import MaintenanceService
from src.utils.config import PROJECT_ROOT


def build_parser() -> argparse.ArgumentParser:
    """Return the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="language-hangman",
        description="Local admin commands for Language Learning Hangman.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    show_config_parser = subparsers.add_parser("show-config")
    show_config_parser.add_argument("--json", action="store_true", dest="json_output")

    validate_parser = subparsers.add_parser("validate-content")
    validate_parser.add_argument("--json", action="store_true", dest="json_output")
    validate_parser.add_argument("--summary", action="store_true")
    validate_parser.add_argument("--errors-only", action="store_true")
    validate_parser.add_argument("--coverage", action="store_true")

    seed_parser = subparsers.add_parser("seed-content")
    seed_parser.add_argument("--json", action="store_true", dest="json_output")

    release_parser = subparsers.add_parser("release-check")
    release_parser.add_argument("--json", action="store_true", dest="json_output")

    export_parser = subparsers.add_parser("export-progress")
    export_parser.add_argument("--output", required=True)
    export_parser.add_argument("--json", action="store_true", dest="json_output")

    import_parser = subparsers.add_parser("import-progress")
    import_parser.add_argument("--input", required=True)
    import_parser.add_argument("--json", action="store_true", dest="json_output")

    run_parser = subparsers.add_parser("run-app")
    run_parser.add_argument("--port", type=int, default=None)
    run_parser.add_argument("--headless", action="store_true")

    gateway_parser = subparsers.add_parser("run-auth-gateway")
    gateway_parser.add_argument("--gateway-host", default="127.0.0.1")
    gateway_parser.add_argument("--gateway-port", type=int, default=8000)
    gateway_parser.add_argument("--streamlit-port", type=int, default=8501)
    gateway_parser.add_argument("--show-browser", action="store_true")

    return parser


def main(argv: list[str] | None = None) -> int:
    """Execute the requested local admin command."""
    parser = build_parser()
    args = parser.parse_args(argv)
    service = MaintenanceService()

    if args.command == "show-config":
        _render_payload(service.get_runtime_summary(), json_output=args.json_output)
        return 0

    if args.command == "validate-content":
        payload = service.validate_word_banks(include_rows=False)
        filtered_payload = _filter_validation_payload(
            payload,
            errors_only=args.errors_only,
            include_coverage=args.coverage,
        )
        if args.json_output:
            _render_payload(filtered_payload, json_output=True)
        else:
            _render_validation_report(
                filtered_payload,
                summary=args.summary,
                coverage=args.coverage,
                errors_only=args.errors_only,
            )
        return 1 if payload["has_errors"] else 0

    if args.command == "seed-content":
        _render_payload(service.seed_word_banks(), json_output=args.json_output)
        return 0

    if args.command == "release-check":
        payload = service.find_local_artifacts()
        _render_payload(payload, json_output=args.json_output)
        return 0 if payload["is_clean"] else 1

    if args.command == "export-progress":
        payload = service.export_progress(Path(args.output))
        _render_payload(payload, json_output=args.json_output)
        return 0

    if args.command == "import-progress":
        payload = service.import_progress(Path(args.input))
        _render_payload(payload, json_output=args.json_output)
        return 0

    if args.command == "run-app":
        command = build_streamlit_command(port=args.port, headless=args.headless)
        completed_process = subprocess.run(command, check=False)
        return int(completed_process.returncode)

    if args.command == "run-auth-gateway":
        from src.gateway.launcher import run_gateway_with_streamlit

        return run_gateway_with_streamlit(
            gateway_host=args.gateway_host,
            gateway_port=args.gateway_port,
            streamlit_port=args.streamlit_port,
            headless=not args.show_browser,
        )

    parser.error("Unsupported command.")
    return 2


def build_streamlit_command(
    *,
    port: int | None = None,
    headless: bool = False,
) -> list[str]:
    """Return the Streamlit command used to launch the app."""
    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(PROJECT_ROOT / "app.py"),
    ]
    if port is not None:
        command.extend(["--server.port", str(port)])
    if headless:
        command.extend(["--server.headless", "true"])
    return command


def _filter_validation_payload(
    payload: dict[str, Any],
    *,
    errors_only: bool,
    include_coverage: bool,
) -> dict[str, Any]:
    """Return a scalable validation payload without raw valid rows."""
    file_summaries = []
    for file_summary in payload["files"]:
        if errors_only and not file_summary["errors"]:
            continue
        file_summaries.append(
            {
                "file": file_summary["file"],
                "language": file_summary["language"],
                "valid_words": file_summary["valid_words"],
                "invalid_words": file_summary["invalid_words"],
                "duplicate_words": file_summary["duplicate_words"],
                "warning_count": len(file_summary["warnings"]),
                "errors": file_summary["errors"],
                "warnings": file_summary["warnings"],
            }
        )

    filtered_payload = {
        "files": file_summaries,
        "files_processed": payload["files_processed"],
        "valid_words": payload["valid_words"],
        "invalid_words": payload["invalid_words"],
        "duplicate_words": payload["duplicate_words"],
        "quality_warning_count": sum(
            len(file_summary["warnings"]) for file_summary in file_summaries
        ),
        "has_errors": payload["has_errors"],
    }
    if include_coverage:
        filtered_payload["coverage"] = payload["coverage"]
    return filtered_payload


def _render_validation_report(
    payload: dict[str, Any],
    *,
    summary: bool,
    coverage: bool,
    errors_only: bool,
) -> None:
    """Print a concise validation report for large word banks."""
    print(f"Files processed: {payload['files_processed']}")
    print(f"Valid words: {payload['valid_words']}")
    print(f"Invalid words: {payload['invalid_words']}")
    print(f"Duplicate words: {payload['duplicate_words']}")
    print(f"Quality warnings: {payload.get('quality_warning_count', 0)}")

    if coverage and "coverage" in payload:
        coverage_summary = payload["coverage"]
        print("\nCoverage by language:")
        for language, count in coverage_summary["total_words_by_language"].items():
            print(f"- {language}: {count}")

        print("\nCoverage by category:")
        for category, count in coverage_summary["words_by_category"].items():
            print(f"- {category}: {count}")

        print("\nCoverage by difficulty:")
        for difficulty, count in coverage_summary["words_by_difficulty"].items():
            print(f"- {difficulty}: {count}")

        if "words_by_situation" in coverage_summary:
            print("\nCoverage by situation:")
            for situation, count in coverage_summary["words_by_situation"].items():
                print(f"- {situation}: {count}")

        print("\nWeak coverage areas:")
        weak_areas = coverage_summary["weak_coverage_areas"]
        if weak_areas:
            for weak_area in weak_areas:
                print(f"- {weak_area}")
        else:
            print("- None")

    if summary and not payload["files"]:
        print("\nNo file-level issues matched this filter.")
        return

    if summary and not errors_only:
        print("\nFile summary:")
        for file_summary in payload["files"]:
            print(
                "- "
                f"{file_summary['file']}: "
                f"{file_summary['valid_words']} valid, "
                f"{file_summary['invalid_words']} invalid, "
                f"{file_summary['duplicate_words']} duplicates, "
                f"{file_summary['warning_count']} warnings"
            )
        _render_quality_warning_preview(payload)
        return

    issue_files = [
        file_summary
        for file_summary in payload["files"]
        if file_summary["errors"] or file_summary["warnings"]
    ]
    if issue_files:
        print("\nValidation issues:")
        for file_summary in issue_files:
            print(f"- {file_summary['file']}")
            for error in file_summary["errors"]:
                print(f"  error: {error}")
            for warning in file_summary["warnings"]:
                print(f"  warning: {warning}")
    elif not summary:
        print("\nNo validation issues found.")


def _render_quality_warning_preview(payload: dict[str, Any], *, limit: int = 20) -> None:
    """Print a bounded quality-warning preview for summary reports."""
    warnings: list[tuple[str, str]] = []
    for file_summary in payload["files"]:
        warnings.extend(
            (str(file_summary["file"]), str(warning))
            for warning in file_summary["warnings"]
        )
    if not warnings:
        return

    print("\nQuality warning preview:")
    for file_name, warning in warnings[:limit]:
        print(f"- {file_name}: {warning}")
    if len(warnings) > limit:
        remaining = len(warnings) - limit
        print(f"- ... {remaining} more warning(s). Run without --summary for the full report.")


def _render_payload(payload: dict[str, Any], *, json_output: bool) -> None:
    """Print a JSON or readable text representation of a payload."""
    if json_output:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return

    for key, value in payload.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    raise SystemExit(main())
