"""Local content utility UI."""

from __future__ import annotations

import streamlit as st

from src.services.maintenance_service import MaintenanceService
from src.services.word_service import WordService
from src.ui.design import render_callout, render_kpi_grid, render_page_header, render_section_intro
from src.utils.language_display import format_language_label


def render_content_page(
    word_service: WordService,
    maintenance_service: MaintenanceService,
) -> None:
    """Render the local-only word-bank inspection and reload page."""
    render_page_header(
        "Content Utility",
        "Inspect word-bank coverage, preview content, and reload JSON files into SQLite.",
        eyebrow="Local admin",
    )

    runtime_summary = maintenance_service.get_runtime_summary()
    release_check = maintenance_service.find_local_artifacts()
    validation_summary = word_service.inspect_word_banks()
    coverage_summary = validation_summary["coverage"]
    content_summary = word_service.get_content_summary()

    render_section_intro("Runtime Setup")
    render_kpi_grid(
        [
            {"label": "Version", "value": runtime_summary["app_version_display"]},
            {"label": "Word files", "value": validation_summary["files_processed"]},
            {"label": "Stored words", "value": content_summary["total_words"]},
        ]
    )
    st.caption(f"Words directory: {runtime_summary['words_dir']}")
    st.caption(f"Database path: {runtime_summary['database_path']}")

    render_section_intro("Release Readiness")
    if release_check["is_clean"]:
        render_callout(
            "Ready to share",
            "No local share-blocking artifacts were found in the project tree.",
            tone="success",
        )
    else:
        st.warning(
            f"{release_check['artifact_count']} local artifact(s) should be removed "
            "before sharing this repo snapshot."
        )
        st.dataframe(
            [{"artifact_path": artifact_path} for artifact_path in release_check["artifacts"]],
            use_container_width=True,
            hide_index=True,
        )

    render_kpi_grid(
        [
            {"label": "Files processed", "value": validation_summary["files_processed"]},
            {"label": "Valid words", "value": validation_summary["valid_words"]},
            {"label": "Invalid words", "value": validation_summary["invalid_words"]},
            {"label": "Duplicates skipped", "value": validation_summary["duplicate_words"]},
        ]
    )

    if st.button("Reload Word Banks From JSON", type="primary", use_container_width=True):
        st.session_state.content_import_summary = maintenance_service.seed_word_banks()
        st.success("Word-bank reload complete.")
        st.rerun()

    render_section_intro("Import Custom Word File")
    st.write(
        "Upload a local JSON word-bank file to validate and add its valid rows to SQLite. "
        "CSV import is planned for a future version."
    )
    uploaded_file = st.file_uploader(
        "Upload JSON word file",
        type=["json"],
        help=(
            "Required fields: word, language, category, difficulty, hint, "
            "translation, example_sentence, synonym, association."
        ),
    )
    if uploaded_file is not None:
        uploaded_bytes = uploaded_file.getvalue()
        validation_preview = word_service.validate_uploaded_word_bank(
            filename=uploaded_file.name,
            content=uploaded_bytes,
        )
        st.write(
            f"Preview: {validation_preview['valid_words']} valid row(s), "
            f"{validation_preview['invalid_words']} invalid row(s), "
            f"{validation_preview['duplicate_words']} duplicate(s)."
        )
        if validation_preview["errors"]:
            with st.expander("Validation Errors", expanded=True):
                for error in validation_preview["errors"]:
                    st.error(error)
        if validation_preview["warnings"]:
            for warning in validation_preview["warnings"]:
                st.warning(warning)
        if st.button(
            "Import Valid Rows",
            use_container_width=True,
            disabled=validation_preview["valid_words"] == 0,
        ):
            st.session_state.content_import_summary = word_service.import_uploaded_word_bank(
                filename=uploaded_file.name,
                content=uploaded_bytes,
            )
            import_summary = st.session_state.content_import_summary
            st.success(
                "Import finished: "
                f"{import_summary['valid_words']} valid row(s), "
                f"{import_summary['invalid_words']} invalid row(s), "
                f"{import_summary['inserted_count']} newly added."
            )
            st.rerun()

    if st.session_state.get("content_import_summary"):
        import_summary = st.session_state["content_import_summary"]
        st.subheader("Latest Import Summary")
        st.write(
            f"Inserted or newly added: {import_summary['inserted_count']} | "
            f"Reloaded or updated: {import_summary['reloaded_count']} | "
            f"Existing rows skipped: {import_summary.get('skipped_existing_count', 0)} | "
            f"Total words now stored: {import_summary['total_words_after_import']}"
        )

    render_section_intro("Coverage Snapshot")
    left_column, middle_column, right_column = st.columns(3)
    with left_column:
        st.write("By language")
        st.dataframe(
            _dict_counts_to_rows(coverage_summary["total_words_by_language"], "language"),
            use_container_width=True,
            hide_index=True,
        )
    with middle_column:
        st.write("By category")
        st.dataframe(
            _dict_counts_to_rows(coverage_summary["words_by_category"], "category"),
            use_container_width=True,
            hide_index=True,
        )
    with right_column:
        st.write("By difficulty")
        st.dataframe(
            _dict_counts_to_rows(coverage_summary["words_by_difficulty"], "difficulty"),
            use_container_width=True,
            hide_index=True,
        )

    render_section_intro("Stored Database Snapshot")
    database_left, database_middle, database_right = st.columns(3)
    with database_left:
        st.dataframe(content_summary["by_language"], use_container_width=True, hide_index=True)
    with database_middle:
        st.dataframe(content_summary["by_category"], use_container_width=True, hide_index=True)
    with database_right:
        st.dataframe(content_summary["by_difficulty"], use_container_width=True, hide_index=True)

    render_section_intro("Weak Coverage Areas")
    if coverage_summary["weak_coverage_areas"]:
        for weak_area in coverage_summary["weak_coverage_areas"]:
            st.warning(weak_area)
    else:
        render_callout(
            "Coverage targets met",
            "All language/category/difficulty coverage targets are currently met.",
            tone="success",
        )

    available_languages = word_service.get_available_languages()
    preview_language = st.selectbox(
        "Preview language",
        options=available_languages,
        index=0 if available_languages else None,
        format_func=format_language_label,
    )
    preview_categories = word_service.get_categories(preview_language) if preview_language else []
    preview_category = st.selectbox(
        "Preview category",
        options=["All Categories", *preview_categories],
        index=0,
    )
    preview_words = (
        word_service.preview_words(
            language=preview_language,
            limit=8,
            categories=None if preview_category == "All Categories" else [preview_category],
        )
        if preview_language
        else []
    )
    render_section_intro("Word Preview")
    if preview_words:
        st.dataframe(preview_words, use_container_width=True, hide_index=True)
    else:
        st.write("No words are available for this preview filter yet.")

    render_section_intro("Validation Details")
    for file_summary in validation_summary["files"]:
        with st.expander(file_summary["file"], expanded=False):
            st.write(
                f"Language: {file_summary['language']} | "
                f"Valid words: {file_summary['valid_words']} | "
                f"Invalid words: {file_summary['invalid_words']}"
            )
            if file_summary["warnings"]:
                for warning in file_summary["warnings"]:
                    st.warning(warning)
            if file_summary["errors"]:
                for error in file_summary["errors"]:
                    st.error(error)
            elif file_summary["valid_words"]:
                st.success("This file validated successfully.")


def _dict_counts_to_rows(counts: dict[str, int], label: str) -> list[dict[str, object]]:
    """Convert coverage counters into dataframe-friendly rows."""
    return [{label: key, "word_count": value} for key, value in counts.items()]
