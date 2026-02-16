"""
Reusable UI components for a consistent, premium analytics layout.

Use these instead of ad-hoc columns/expanders/markdown so the app
has a single visual language and clear hierarchy.
"""

from typing import Any, Callable, List, Optional

import streamlit as st

from app.styles.theme import THEME_COLORS

# Re-export for convenience
from app.styles.loading import (
    show_empty_state as empty_state,
    show_loading_dots,
    show_progress_bar,
    show_skeleton_loader,
)
from app.styles.errors import show_warning, show_success, show_info, ErrorHandler


# KPI card accent colors (same metric = same color across the app)
KPI_COLORS = {
    "reactions": "#6366f1",  # primary
    "comments": "#3b82f6",  # info
    "shares": "#14b8a6",  # teal
    "engagement": "#10b981",  # success
    "views": "#8b5cf6",  # secondary
    "likes": "#ec4899",  # pink
    "default": "#475569",
}


def page_header(
    title: str,
    subtitle: Optional[str] = None,
    actions: Optional[List[tuple]] = None,
) -> None:
    """
    Render a compact page header with optional subtitle and action buttons.

    Args:
        title: Main heading (e.g. "Facebook Analysis").
        subtitle: Optional one-line description.
        actions: Optional list of (label, key) for st.button in a row.
    """
    st.markdown(
        f"""
        <div class="ui-page-header" style="
            margin-bottom: 1.5rem;
        ">
            <h1 style="
                margin: 0;
                font-size: 1.75rem;
                font-weight: 700;
                color: var(--text-primary, #0f172a);
                letter-spacing: -0.02em;
            ">{title}</h1>
            {f'<p style="margin: 0.5rem 0 0 0; color: var(--text-secondary, #475569); font-size: 0.9375rem;">{subtitle}</p>' if subtitle else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )
    if actions:
        cols = st.columns([4] + [1] * len(actions))
        with cols[0]:
            st.write("")
        for i, (label, key) in enumerate(actions):
            with cols[i + 1]:
                st.button(label, key=key or f"header_btn_{i}")


def kpi_cards(
    metrics: List[dict],
    *,
    columns: Optional[int] = None,
    help_prefix: str = "",
) -> None:
    """
    Render a row of KPI cards with consistent style (no heavy gradients).

    Args:
        metrics: List of dicts with keys:
            - label: str
            - value: str (or number formatted as string)
            - help_text: optional str
            - color_key: optional key in KPI_COLORS (e.g. "reactions", "comments")
        columns: Number of columns (default: len(metrics), max 4).
        help_prefix: Optional prefix for help tooltips.
    """
    n = min(len(metrics), columns or len(metrics), 4)
    if n <= 0:
        return
    cols = st.columns(n)
    for i, m in enumerate(metrics[:n]):
        with cols[i]:
            label = m.get("label", "")
            value = m.get("value", "—")
            help_text = m.get("help_text") or ""
            if help_prefix and help_text:
                help_text = f"{help_prefix} {help_text}"
            color_key = m.get("color_key") or "default"
            color = KPI_COLORS.get(color_key, KPI_COLORS["default"])
            st.markdown(
                f"""
                <div class="ui-kpi-card" style="
                    background: var(--bg-primary, #fff);
                    border: 1px solid var(--border-color, #e2e8f0);
                    border-radius: 10px;
                    padding: 1rem 1.25rem;
                    margin-bottom: 1rem;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
                ">
                    <div style="
                        font-size: 0.8125rem;
                        font-weight: 500;
                        color: var(--text-secondary, #475569);
                        margin-bottom: 0.25rem;
                    ">{label}</div>
                    <div style="
                        font-size: 1.5rem;
                        font-weight: 700;
                        color: {color};
                        letter-spacing: -0.02em;
                    ">{value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if help_text:
                st.caption(help_text)


def section(
    title: str,
    *,
    help_text: Optional[str] = None,
    expanded: bool = True,
    icon: str = "",
):
    """
    Provide a consistent section wrapper (expander + optional help).
    Use as context manager: with section("Overview", expanded=True): ...
    """
    return SectionContext(title=title, help_text=help_text, expanded=expanded, icon=icon)


class SectionContext:
    """Context manager for a section (expander) with optional help."""

    def __init__(
        self,
        title: str,
        *,
        help_text: Optional[str] = None,
        expanded: bool = True,
        icon: str = "",
    ):
        self.title = f"{icon} {title}".strip() if icon else title
        self.help_text = help_text
        self.expanded = expanded
        self._expander = None

    def __enter__(self):
        self._expander = st.expander(self.title, expanded=self.expanded)
        inner = self._expander.__enter__()
        if self.help_text:
            st.caption(self.help_text)
        return inner

    def __exit__(self, *args):
        return self._expander.__exit__(*args)


def error_state(
    message: str,
    title: str = "Something went wrong",
    show_retry: bool = False,
    retry_key: str = "error_retry",
) -> None:
    """Show a consistent error block (uses existing ErrorHandler styling)."""
    st.markdown(
        f"""
        <div style="
            background: rgba(239, 68, 68, 0.08);
            border-left: 4px solid var(--accent-red, #ef4444);
            padding: 1rem 1.25rem;
            border-radius: 8px;
            margin: 1rem 0;
        ">
            <div style="font-weight: 600; color: var(--text-primary);">{title}</div>
            <div style="margin-top: 0.5rem; color: var(--text-secondary); font-size: 0.9375rem;">{message}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if show_retry:
        st.button("Try again", key=retry_key)


def loading_state(message: str = "Loading...", use_spinner: bool = True) -> Any:
    """
    Show loading state. If use_spinner=True, returns a context manager that shows
    st.spinner; otherwise you can use with a placeholder.
    """
    if use_spinner:
        return st.spinner(message)
    return _LoadingPlaceholder(message)


class _LoadingPlaceholder:
    """Context manager: show loading message in a placeholder until exit."""

    def __init__(self, message: str):
        self.message = message
        self._placeholder = None

    def __enter__(self):
        self._placeholder = st.empty()
        with self._placeholder.container():
            show_loading_dots(self.message)
        return self._placeholder

    def __exit__(self, *args):
        if self._placeholder:
            self._placeholder.empty()


def section_divider() -> None:
    """Subtle horizontal spacing between major sections."""
    st.markdown(
        '<div style="height: 1.5rem;"></div>',
        unsafe_allow_html=True,
    )


__all__ = [
    "page_header",
    "kpi_cards",
    "section",
    "SectionContext",
    "empty_state",
    "error_state",
    "loading_state",
    "section_divider",
    "KPI_COLORS",
    "show_loading_dots",
    "show_progress_bar",
    "show_skeleton_loader",
    "show_warning",
    "show_success",
    "show_info",
    "ErrorHandler",
]
