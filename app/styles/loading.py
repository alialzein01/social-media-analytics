"""
Loading States and Progress Indicators
=======================================

Provides loading spinners, progress bars, and status indicators.
"""

import streamlit as st
import time
from typing import Optional, Callable, Any
from contextlib import contextmanager


def show_spinner(message: str = "Loading..."):
    """
    Show a loading spinner with custom message.

    Args:
        message: Loading message to display
    """
    st.markdown(
        f"""
    <div style="text-align: center; padding: 2rem;">
        <div class="loading-spinner"></div>
        <p style="margin-top: 1rem; color: var(--text-secondary); font-weight: 500;">
            {message}
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )


def show_loading_dots(message: str = "Processing"):
    """
    Show animated loading dots.

    Args:
        message: Message to display
    """
    st.markdown(
        f"""
    <div style="text-align: center; padding: 1rem;">
        <p style="color: var(--text-secondary); font-weight: 500; margin-bottom: 0.5rem;">
            {message}
        </p>
        <div class="loading-dots">
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def show_progress_bar(progress: float, message: str = ""):
    """
    Show a progress bar.

    Args:
        progress: Progress value between 0 and 1
        message: Optional message to display
    """
    percentage = int(progress * 100)

    st.markdown(
        f"""
    <div style="margin: 1rem 0;">
        {f'<p style="color: var(--text-secondary); font-weight: 500; margin-bottom: 0.5rem;">{message}</p>' if message else ""}
        <div style="
            width: 100%;
            height: 8px;
            background: var(--bg-tertiary);
            border-radius: 999px;
            overflow: hidden;
        ">
            <div style="
                width: {percentage}%;
                height: 100%;
                background: var(--gradient-primary);
                border-radius: 999px;
                transition: width 0.3s ease;
            "></div>
        </div>
        <p style="
            text-align: right;
            color: var(--text-muted);
            font-size: 0.875rem;
            margin-top: 0.25rem;
        ">{percentage}%</p>
    </div>
    """,
        unsafe_allow_html=True,
    )


def show_skeleton_loader(height: str = "100px", count: int = 1):
    """
    Show skeleton loader for content that's loading.

    Args:
        height: Height of skeleton element
        count: Number of skeleton elements
    """
    skeleton_html = ""
    for _ in range(count):
        skeleton_html += f"""
        <div style="
            width: 100%;
            height: {height};
            background: linear-gradient(
                90deg,
                var(--bg-tertiary) 25%,
                var(--bg-secondary) 50%,
                var(--bg-tertiary) 75%
            );
            background-size: 200% 100%;
            animation: loading 1.5s infinite;
            border-radius: var(--radius-md);
            margin-bottom: 1rem;
        "></div>
        """

    st.markdown(
        f"""
    <style>
        @keyframes loading {{
            0% {{ background-position: 200% 0; }}
            100% {{ background-position: -200% 0; }}
        }}
    </style>
    {skeleton_html}
    """,
        unsafe_allow_html=True,
    )


@contextmanager
def loading_state(message: str = "Loading...", show_progress: bool = False):
    """
    Context manager for showing loading state during operations.

    Args:
        message: Loading message
        show_progress: Whether to show progress bar

    Usage:
        with loading_state("Fetching data..."):
            # Your code here
            data = fetch_data()
    """
    placeholder = st.empty()

    try:
        with placeholder.container():
            if show_progress:
                show_progress_bar(0.5, message)
            else:
                show_spinner(message)

        yield placeholder

    finally:
        placeholder.empty()


def with_loading(message: str = "Loading..."):
    """
    Decorator for functions that should show loading state.

    Args:
        message: Loading message

    Usage:
        @with_loading("Fetching posts...")
        def fetch_posts():
            # Your code here
            return posts
    """

    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> Any:
            with st.spinner(message):
                return func(*args, **kwargs)

        return wrapper

    return decorator


def show_status_indicator(status: str, message: str, icon: Optional[str] = None):
    """
    Show a status indicator (success, warning, error, info).

    Args:
        status: 'success', 'warning', 'error', or 'info'
        message: Status message
        icon: Optional emoji icon
    """
    status_config = {
        "success": {
            "color": "var(--accent-green)",
            "bg": "rgba(16, 185, 129, 0.1)",
            "icon": "✅" if not icon else icon,
        },
        "warning": {
            "color": "var(--accent-orange)",
            "bg": "rgba(245, 158, 11, 0.1)",
            "icon": "⚠️" if not icon else icon,
        },
        "error": {
            "color": "var(--accent-red)",
            "bg": "rgba(239, 68, 68, 0.1)",
            "icon": "❌" if not icon else icon,
        },
        "info": {
            "color": "var(--accent-blue)",
            "bg": "rgba(59, 130, 246, 0.1)",
            "icon": "ℹ️" if not icon else icon,
        },
    }

    config = status_config.get(status, status_config["info"])

    st.markdown(
        f"""
    <div style="
        background: {config["bg"]};
        border-left: 4px solid {config["color"]};
        padding: 1rem 1.5rem;
        border-radius: var(--radius-md);
        display: flex;
        align-items: center;
        gap: 1rem;
        margin: 1rem 0;
    ">
        <span style="font-size: 1.5rem;">{config["icon"]}</span>
        <p style="
            margin: 0;
            color: var(--text-primary);
            font-weight: 500;
        ">{message}</p>
    </div>
    """,
        unsafe_allow_html=True,
    )


def show_processing_steps(steps: list, current_step: int):
    """
    Show processing steps with progress indication.

    Args:
        steps: List of step names
        current_step: Current step index (0-based)
    """
    steps_html = ""

    for i, step in enumerate(steps):
        is_complete = i < current_step
        is_current = i == current_step
        is_pending = i > current_step

        if is_complete:
            icon = "✅"
            color = "var(--accent-green)"
            opacity = "1"
        elif is_current:
            icon = "🔄"
            color = "var(--primary-color)"
            opacity = "1"
        else:
            icon = "⏳"
            color = "var(--text-muted)"
            opacity = "0.5"

        steps_html += f"""
        <div style="
            display: flex;
            align-items: center;
            gap: 1rem;
            padding: 0.75rem;
            opacity: {opacity};
            transition: opacity 0.3s ease;
        ">
            <span style="font-size: 1.25rem;">{icon}</span>
            <p style="
                margin: 0;
                color: {color};
                font-weight: {"600" if is_current else "500"};
            ">{step}</p>
        </div>
        """

    st.markdown(
        f"""
    <div style="
        background: var(--bg-primary);
        padding: 1rem;
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-md);
    ">
        {steps_html}
    </div>
    """,
        unsafe_allow_html=True,
    )


def show_data_loading_placeholder(rows: int = 3):
    """
    Show placeholder for data that's loading (like a table).

    Args:
        rows: Number of rows to show
    """
    for _ in range(rows):
        cols = st.columns([1, 2, 1, 1])
        for col in cols:
            with col:
                show_skeleton_loader(height="40px", count=1)


def show_chart_loading_placeholder():
    """Show placeholder for chart that's loading."""
    st.markdown(
        """
    <div style="
        width: 100%;
        height: 400px;
        background: var(--bg-primary);
        border-radius: var(--radius-lg);
        display: flex;
        align-items: center;
        justify-content: center;
        flex-direction: column;
        gap: 1rem;
    ">
        <div class="loading-spinner"></div>
        <p style="color: var(--text-secondary); font-weight: 500;">
            Loading chart...
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )


def show_empty_state(
    icon: str,
    title: str,
    message: str,
    action_text: Optional[str] = None,
    action_callback: Optional[Callable] = None,
):
    """
    Show an empty state when no data is available.

    Args:
        icon: Emoji icon
        title: Title text
        message: Description message
        action_text: Optional action button text
        action_callback: Optional callback for action button
    """
    st.markdown(
        f"""
    <div style="
        text-align: center;
        padding: 3rem 2rem;
        background: var(--bg-primary);
        border-radius: var(--radius-xl);
        box-shadow: var(--shadow-md);
    ">
        <div style="font-size: 4rem; margin-bottom: 1rem;">{icon}</div>
        <h3 style="color: var(--text-primary); margin-bottom: 0.5rem;">{title}</h3>
        <p style="color: var(--text-secondary); max-width: 400px; margin: 0 auto;">
            {message}
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    if action_text and action_callback:
        if st.button(action_text, key=f"empty_state_{title}"):
            action_callback()
