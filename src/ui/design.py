"""Small presentation helpers for Streamlit screens."""

from __future__ import annotations

from html import escape
from typing import Iterable

import streamlit as st


def render_page_header(
    title: str,
    description: str,
    *,
    eyebrow: str | None = None,
    meta: Iterable[str] | None = None,
) -> None:
    """Render a consistent page heading without adding a nested card."""
    eyebrow_html = (
        f'<div class="llh-eyebrow">{escape(eyebrow)}</div>' if eyebrow else ""
    )
    meta_items = "".join(
        f'<span class="llh-meta-pill">{escape(item)}</span>' for item in (meta or [])
    )
    meta_html = f'<div class="llh-meta-row">{meta_items}</div>' if meta_items else ""
    st.markdown(
        f"""
        <section class="llh-page-heading">
            {eyebrow_html}
            <h2>{escape(title)}</h2>
            <p>{escape(description)}</p>
            {meta_html}
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_section_intro(title: str, description: str | None = None) -> None:
    """Render a compact section heading."""
    description_html = f"<p>{escape(description)}</p>" if description else ""
    st.markdown(
        f"""
        <div class="llh-section-intro">
            <h3>{escape(title)}</h3>
            {description_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_grid(items: Iterable[dict[str, object]]) -> None:
    """Render responsive KPI cards from simple dictionaries."""
    cards = []
    for item in items:
        label = escape(str(item.get("label", "")))
        value = escape(str(item.get("value", "")))
        caption = item.get("caption")
        caption_html = (
            f'<span class="llh-kpi-caption">{escape(str(caption))}</span>'
            if caption
            else ""
        )
        cards.append(
            '<div class="llh-kpi">'
            f'<span class="llh-kpi-label">{label}</span>'
            f"<strong>{value}</strong>"
            f"{caption_html}"
            "</div>"
        )
    st.markdown(
        f'<div class="llh-kpi-grid">{"".join(cards)}</div>',
        unsafe_allow_html=True,
    )


def render_callout(
    title: str,
    body: str,
    *,
    tone: str = "neutral",
) -> None:
    """Render a concise status or empty-state callout."""
    st.markdown(
        f"""
        <div class="llh-callout llh-callout-{escape(tone)}">
            <strong>{escape(title)}</strong>
            <span>{escape(body)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
