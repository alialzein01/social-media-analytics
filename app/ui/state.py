"""
Session State Management
========================

Centralized session state management for the Streamlit application.
"""

import streamlit as st
from typing import Optional, List, Dict, Any


class UIState:
    """
    Manages Streamlit session state with consistent initialization and access patterns.
    """

    @staticmethod
    def initialize():
        """Initialize all session state variables with default values."""
        defaults = {
            'raw_data': None,
            'normalized_data': None,
            'platform': 'Facebook',
            'theme': 'light',
            'last_fetch_time': None,
            'loaded_file': None,
            'selected_post_index': 0,
            'show_advanced_nlp': False,
            'comments_fetched': False,
            'fetch_mode': 'batch',  # 'batch' or 'individual'
        }

        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

    @staticmethod
    def get(key: str, default: Any = None) -> Any:
        """Get a value from session state with optional default."""
        return st.session_state.get(key, default)

    @staticmethod
    def set(key: str, value: Any):
        """Set a value in session state."""
        st.session_state[key] = value

    @staticmethod
    def update(updates: Dict[str, Any]):
        """Update multiple session state values at once."""
        for key, value in updates.items():
            st.session_state[key] = value

    @staticmethod
    def clear_data():
        """Clear all data-related session state."""
        st.session_state.raw_data = None
        st.session_state.normalized_data = None
        st.session_state.last_fetch_time = None
        st.session_state.loaded_file = None
        st.session_state.comments_fetched = False

    @staticmethod
    def has_data() -> bool:
        """Check if data is loaded."""
        return st.session_state.get('normalized_data') is not None

    @staticmethod
    def get_normalized_data() -> Optional[List[Dict]]:
        """Get normalized data from session state."""
        return st.session_state.get('normalized_data')

    @staticmethod
    def get_raw_data() -> Optional[List[Dict]]:
        """Get raw data from session state."""
        return st.session_state.get('raw_data')

    @staticmethod
    def get_platform() -> str:
        """Get current platform."""
        return st.session_state.get('platform', 'Facebook')

    @staticmethod
    def get_theme() -> str:
        """Get current theme."""
        return st.session_state.get('theme', 'light')

    @staticmethod
    def toggle_theme():
        """Toggle between light and dark theme."""
        current = st.session_state.get('theme', 'light')
        st.session_state.theme = 'dark' if current == 'light' else 'light'
