"""
UI Module
=========

Streamlit UI components and coordination for the social media analytics dashboard.

This module contains:
- sidebar.py: Sidebar controls and inputs
- main_view.py: Main content area rendering
- state.py: Session state management
"""

from .state import UIState
from .sidebar import render_sidebar
from .main_view import render_main_content

__all__ = [
    'UIState',
    'render_sidebar',
    'render_main_content'
]
