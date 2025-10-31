"""
Sidebar UI Components
=====================

Handles all sidebar controls including platform selection, data source,
configuration options, and analysis settings.
"""

import os
import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from .state import UIState


def render_sidebar(apify_token: str) -> Dict[str, Any]:
    """
    Render simplified sidebar with only essential controls.

    Args:
        apify_token: Apify API token

    Returns:
        Dictionary with all sidebar configuration values
    """
    config = {}

    # =========================================================================
    # THEME SETTINGS
    # =========================================================================
    st.sidebar.markdown("### ⚙️ Settings")
    theme_toggle = st.sidebar.checkbox(
        "🌙 Dark Mode",
        value=UIState.get_theme() == 'dark',
        help="Toggle between light and dark themes"
    )

    if theme_toggle and UIState.get_theme() != 'dark':
        UIState.set('theme', 'dark')
        st.rerun()
    elif not theme_toggle and UIState.get_theme() != 'light':
        UIState.set('theme', 'light')
        st.rerun()

    st.sidebar.markdown("---")

    # =========================================================================
    # PLATFORM SELECTION
    # =========================================================================
    st.sidebar.markdown("### 📱 Platform Selection")
    platform = st.sidebar.radio(
        "Choose a platform:",
        ["Facebook", "Instagram", "YouTube"],
        help="Select the social media platform to analyze"
    )
    config['platform'] = platform
    UIState.set('platform', platform)

    st.sidebar.markdown("---")

    # =========================================================================
    # DATE RANGE SELECTION
    # =========================================================================
    st.sidebar.markdown("### 📅 Date Range")
    date_range_config = _render_date_range_selector()
    config.update(date_range_config)

    # =========================================================================
    # SET DEFAULT CONFIGURATION (Always API, Always Comments)
    # =========================================================================
    config.update({
        'data_source': 'Fetch from API',
        'fetch_detailed_comments': True,
        'comment_method': 'Batch Processing',
        'max_posts': 50,  # Reasonable default for 30 days
        'max_comments_per_post': 4,  # Top 4 comments per post (optimized)
        'use_phrase_analysis': True,
        'use_sentiment_coloring': True,
        'use_simple_wordcloud': False
    })

    return config


def _render_fetch_configuration(platform: str) -> Dict[str, Any]:
    """
    Render fetch configuration options (API mode).

    Args:
        platform: Selected platform name

    Returns:
        Dictionary with fetch configuration
    """
    config = {}

    if platform == "Facebook":
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📊 Facebook Configuration")

        # Number of posts
        config['max_posts'] = st.sidebar.slider(
            "Number of Posts to Extract",
            min_value=1,
            max_value=50,
            value=10,
            help="Maximum number of posts to extract from the Facebook page"
        )

        # Date range
        date_config = _render_date_range_selector()
        config.update(date_config)

        # Comments configuration
        st.sidebar.markdown("### 💬 Facebook Comments")
        st.sidebar.info("⚠️ **Note:** Facebook Comments Scraper actors are currently experiencing issues. The app will try multiple actors but may fail.")
        st.sidebar.info("💡 **Tip:** The Facebook Posts Scraper only provides comment counts. Enable 'Fetch Detailed Comments' to get actual comment text for word clouds and sentiment analysis.")

        config['comment_method'] = st.sidebar.radio(
            "Comment Extraction Method:",
            ["Individual Posts", "Batch Processing"],
            help="Choose how to extract comments: individual posts (slower but more reliable) or batch processing (faster but may have limitations)"
        )

        config['fetch_detailed_comments'] = st.sidebar.checkbox(
            "Fetch Detailed Comments",
            value=False,
            help="Fetch detailed comments for Facebook posts using the Comments Scraper actor (currently having issues - may fail)"
        )

    elif platform == "Instagram":
        config['max_posts'] = 10
        config.update(_render_date_range_selector())

        st.sidebar.markdown("### 💬 Instagram Comments")
        st.sidebar.info("💡 **Tip:** Instagram Posts Scraper only provides comment counts. Enable 'Fetch Detailed Comments' to get actual comment text for word clouds and sentiment analysis.")
        st.sidebar.info("💰 **Cost:** Instagram comments cost $2.30 per 1,000 comments. Free plan includes $5 monthly credits (2,100+ comments).")

        config['fetch_detailed_comments'] = st.sidebar.checkbox(
            "Fetch Detailed Comments",
            value=False,
            help="Fetch detailed comments for Instagram posts using the Instagram Comments Scraper (pay-per-result pricing)"
        )
        config['comment_method'] = "Batch Processing"

    else:  # YouTube
        config['max_posts'] = 10
        config.update(_render_date_range_selector())

        st.sidebar.markdown("### 💬 Comments")
        st.sidebar.info("💡 **YouTube Two-Step Tip:** Step 1: Channel scraper gets videos. Step 2: Comments scraper analyzes comments from those videos. Enable 'Fetch Detailed Comments' for Step 2.")

        config['fetch_detailed_comments'] = st.sidebar.checkbox(
            "Fetch Detailed Comments",
            value=False,
            help="Fetch detailed comments for posts"
        )
        config['comment_method'] = "Batch Processing"

    # Max comments per post (for batch mode)
    if config.get('comment_method') == "Batch Processing" and config.get('fetch_detailed_comments'):
        config['max_comments_per_post'] = st.sidebar.slider(
            "Max Comments per Post",
            min_value=10,
            max_value=100,
            value=25,
            help="Maximum number of comments to extract per post"
        )
    else:
        config['max_comments_per_post'] = 25

    return config


def _render_date_range_selector() -> Dict[str, Optional[str]]:
    """
    Render date range selector for post filtering (default: Last 30 Days).

    Returns:
        Dictionary with from_date and to_date
    """
    date_range_option = st.sidebar.radio(
        "Date Range:",
        ["Last 30 Days", "Last 7 Days", "Last 60 Days", "Custom Range"],
        index=0,  # Default to "Last 30 Days"
        help="Choose the time range for posts to extract"
    )

    today = datetime.now()

    if date_range_option == "Last 30 Days":
        from_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")
        to_date = None
    elif date_range_option == "Last 7 Days":
        from_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        to_date = None
    elif date_range_option == "Last 60 Days":
        from_date = (today - timedelta(days=60)).strftime("%Y-%m-%d")
        to_date = None
    elif date_range_option == "Custom Range":
        from_date = st.sidebar.date_input(
            "From Date",
            value=today - timedelta(days=30),
            help="Start date for posts extraction"
        ).strftime("%Y-%m-%d")
        to_date = st.sidebar.date_input(
            "To Date",
            value=today,
            help="End date for posts extraction"
        ).strftime("%Y-%m-%d")
    else:
        from_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")
        to_date = None

    return {'from_date': from_date, 'to_date': to_date}


def _render_file_selector(platform: str) -> Dict[str, Any]:
    """
    Render file selector for loading saved data.

    Args:
        platform: Selected platform name

    Returns:
        Dictionary with file selection status
    """
    from app.services.persistence import DataPersistenceService

    config = {'file_selected': False}

    # Get saved files
    saved_files = DataPersistenceService.get_saved_files()
    platform_files = saved_files.get(platform, [])

    if platform_files:
        st.sidebar.markdown("#### Available Files")
        file_options = []

        for file_path in platform_files:
            filename = os.path.basename(file_path)
            try:
                timestamp_part = filename.split('_', 1)[1].replace('.json', '').replace('.csv', '')
                display_name = f"{timestamp_part} ({'JSON' if file_path.endswith('.json') else 'CSV'})"
            except (IndexError, ValueError, AttributeError):
                display_name = filename
            file_options.append((display_name, file_path))

        selected_file_display = st.sidebar.selectbox(
            "Select a file:",
            options=[opt[0] for opt in file_options],
            help="Choose a previously saved data file to load"
        )

        # Get actual file path
        selected_file_path = None
        for display_name, file_path in file_options:
            if display_name == selected_file_display:
                selected_file_path = file_path
                break

        if selected_file_path and st.sidebar.button("📂 Load Selected File", type="primary"):
            with st.spinner(f"Loading data from {os.path.basename(selected_file_path)}..."):
                loaded_data = DataPersistenceService.load_from_file(selected_file_path)

            if loaded_data:
                UIState.set('normalized_data', loaded_data)
                UIState.set('loaded_file', selected_file_path)
                st.success(f"✅ Successfully loaded {len(loaded_data)} posts from file")
                st.info(f"📁 File: {selected_file_path}")
                config['file_selected'] = True
                st.rerun()
            else:
                st.error("Failed to load data from file")
    else:
        st.sidebar.info(f"No saved files found for {platform}")
        st.sidebar.markdown("**Tip:** Fetch data from API first to create saved files")

    return config


def _render_analysis_options() -> Dict[str, bool]:
    """
    Render analysis options (phrase analysis, sentiment coloring, etc).

    Returns:
        Dictionary with analysis option flags
    """
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔧 Analysis Options")

    use_phrase_analysis = st.sidebar.checkbox(
        "Use Phrase-Based Analysis",
        value=True,
        help="Extract meaningful phrases (like 'thank you', 'very good') instead of individual words for more accurate sentiment analysis"
    )

    use_sentiment_coloring = st.sidebar.checkbox(
        "Use Sentiment Coloring in Word Clouds",
        value=True,
        help="Color words/phrases in word clouds based on their sentiment (green=positive, red=negative, gray=neutral)"
    )

    use_simple_wordcloud = st.sidebar.checkbox(
        "Use Simple Word Cloud (Fallback)",
        value=False,
        help="Use simple word cloud instead of phrase-based analysis. Try this if you see 'No meaningful content found'."
    )

    # Store in session state for access across the app
    UIState.update({
        'use_phrase_analysis': use_phrase_analysis,
        'use_sentiment_coloring': use_sentiment_coloring,
        'use_simple_wordcloud': use_simple_wordcloud
    })

    return {
        'use_phrase_analysis': use_phrase_analysis,
        'use_sentiment_coloring': use_sentiment_coloring,
        'use_simple_wordcloud': use_simple_wordcloud
    }
