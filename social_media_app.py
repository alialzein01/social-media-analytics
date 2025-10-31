"""
Social Media Analytics Dashboard
=================================

Clean, modular social media analytics application.

How to run:
1. Set your Apify API token:
   export APIFY_TOKEN=your_token_here

2. Install dependencies:
   pip install -r requirements.txt

3. Run the app:
   streamlit run social_media_app.py
"""

import os
import streamlit as st
from datetime import datetime

# Import modular components
from app.ui import UIState, render_sidebar, render_main_content
from app.services import DataFetchingService
from app.services.persistence import DataPersistenceService
from app.styles.theme import get_custom_css
from app.styles.errors import with_error_boundary, show_warning
from app.adapters.facebook import FacebookAdapter
from app.adapters.instagram import InstagramAdapter
from app.adapters.youtube import YouTubeAdapter


def get_api_token() -> str:
    """
    Get Apify API token from environment or secrets.

    Returns:
        API token string
    """
    @with_error_boundary("API Token Error", show_details=True)
    def _get_token():
        # Try Streamlit secrets first
        if hasattr(st, 'secrets') and 'APIFY_TOKEN' in st.secrets:
            return st.secrets['APIFY_TOKEN']

        # Fall back to environment variable
        token = os.environ.get('APIFY_TOKEN')

        # Development fallback (remove in production)
        if not token:
            token = os.environ.get('APIFY_TOKEN', 'apify_api_14gYxq0ETCby20EvyECx9plcTt0DgO4uSyss')

        return token

    return _get_token()


def initialize_app():
    """Initialize Streamlit app configuration and session state."""
    st.set_page_config(
        page_title="Social Media Analytics",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Initialize session state
    UIState.initialize()

    # Apply custom theme
    theme = UIState.get_theme()
    st.markdown(get_custom_css(theme), unsafe_allow_html=True)


def render_header():
    """Render application header."""
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0 2rem 0;">
        <h1 style="margin-bottom: 0.5rem;">📊 Social Media Analytics Dashboard</h1>
        <p style="color: var(--text-secondary); font-size: 1.125rem; font-weight: 500;">
            Analyze Facebook, Instagram, and YouTube content with AI-powered insights
        </p>
    </div>
    """, unsafe_allow_html=True)


def validate_url(url: str, platform: str) -> bool:
    """
    Validate URL for the selected platform.

    Args:
        url: URL to validate
        platform: Platform name

    Returns:
        True if valid, False otherwise
    """
    if not url or not url.strip():
        return False

    # Get adapter for platform
    adapters = {
        'Facebook': FacebookAdapter,
        'Instagram': InstagramAdapter,
        'YouTube': YouTubeAdapter
    }

    adapter_class = adapters.get(platform)
    if adapter_class:
        adapter = adapter_class("")  # Token not needed for URL validation
        return adapter.validate_url(url)

    return False


def handle_data_fetch(config: dict, apify_token: str):
    """
    Handle data fetching when analyze button is clicked.

    Args:
        config: Configuration from sidebar
        apify_token: Apify API token
    """
    url = config.get('url', '').strip()
    platform = config['platform']

    # Validate URL
    if not validate_url(url, platform):
        show_warning(
            f"Please enter a valid {platform} URL",
            title="Invalid URL"
        )
        return

    # Get platform adapter
    adapters = {
        'Facebook': FacebookAdapter(apify_token),
        'Instagram': InstagramAdapter(apify_token),
        'YouTube': YouTubeAdapter(apify_token)
    }

    adapter = adapters.get(platform)
    if not adapter:
        st.error(f"No adapter found for {platform}")
        return

    # Initialize data fetching service
    fetcher = DataFetchingService(apify_token)

    # Fetch complete dataset (posts + optionally comments)
    with st.spinner(f"🔄 Fetching {platform} data..."):
        normalized_posts = fetcher.fetch_complete_dataset(
            adapter=adapter,
            url=url,
            max_posts=config.get('max_posts', 10),
            fetch_comments=config.get('fetch_detailed_comments', False),
            max_comments_per_post=config.get('max_comments_per_post', 25),
            from_date=config.get('from_date'),
            to_date=config.get('to_date')
        )

    if not normalized_posts:
        st.error("Failed to fetch data. Please check the URL and try again.")
        return

    # Store normalized data in session state
    UIState.update({
        'raw_data': normalized_posts,
        'normalized_data': normalized_posts,
        'last_fetch_time': datetime.now(),
        'comments_fetched': config.get('fetch_detailed_comments', False)
    })

    # Save data to files
    try:
        persistence = DataPersistenceService()
        persistence.save_dataset(
            raw_data=normalized_posts,
            normalized_data=normalized_posts,
            platform=platform
        )
        st.success("✅ Data saved to files")
    except Exception as e:
        st.warning(f"⚠️ Could not save data: {str(e)}")

    # Rerun to show results
    st.rerun()


def main():
    """Main application entry point."""
    # Initialize app
    initialize_app()

    # Render header
    render_header()

    # Get API token
    apify_token = get_api_token()

    if not apify_token:
        show_warning(
            message="Please set your APIFY_TOKEN in environment variables or Streamlit secrets.",
            title="API Token Required"
        )
        st.stop()

    # Render sidebar and get configuration
    config = render_sidebar(apify_token)

    # Render main content (includes URL input and results)
    render_main_content(config, apify_token)

    # Handle data fetching when analyze button is clicked
    if config.get('analyze_button', False):
        handle_data_fetch(config, apify_token)


if __name__ == "__main__":
    main()
