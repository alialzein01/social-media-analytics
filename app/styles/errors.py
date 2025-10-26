"""
Error Handling and Error Boundaries
====================================

Provides graceful error handling with user-friendly messages.
"""

import streamlit as st
import traceback
from typing import Optional, Callable, Any
from functools import wraps
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ErrorHandler:
    """Centralized error handling for the dashboard."""

    @staticmethod
    def show_error(
        error: Exception,
        title: str = "An Error Occurred",
        show_details: bool = False,
        show_retry: bool = False,
        retry_callback: Optional[Callable] = None
    ):
        """
        Show a user-friendly error message.

        Args:
            error: The exception that occurred
            title: Error title
            show_details: Whether to show technical details
            show_retry: Whether to show retry button
            retry_callback: Function to call on retry
        """
        # Log the error
        logger.error(f"{title}: {str(error)}", exc_info=True)

        # Determine error message
        user_message = ErrorHandler._get_user_friendly_message(error)

        # Show error UI
        st.markdown(f"""
        <div style="
            background: rgba(239, 68, 68, 0.1);
            border-left: 4px solid var(--accent-red);
            padding: 1.5rem;
            border-radius: var(--radius-md);
            margin: 1rem 0;
        ">
            <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 0.75rem;">
                <span style="font-size: 2rem;">⚠️</span>
                <h3 style="margin: 0; color: var(--accent-red);">{title}</h3>
            </div>
            <p style="color: var(--text-primary); margin-bottom: 0.5rem; font-weight: 500;">
                {user_message}
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Show technical details in expander
        if show_details:
            with st.expander("🔍 Technical Details"):
                st.code(traceback.format_exc(), language="python")

        # Show retry button
        if show_retry and retry_callback:
            if st.button("🔄 Retry", key=f"retry_{id(error)}"):
                retry_callback()

    @staticmethod
    def _get_user_friendly_message(error: Exception) -> str:
        """
        Convert technical error to user-friendly message.

        Args:
            error: The exception

        Returns:
            User-friendly error message
        """
        error_str = str(error).lower()
        error_type = type(error).__name__

        # Network/API errors
        if 'connection' in error_str or 'timeout' in error_str:
            return "Unable to connect to the server. Please check your internet connection and try again."

        if 'api' in error_str or 'apify' in error_str:
            return "There was a problem connecting to the data source. Please verify your API credentials and try again."

        if '401' in error_str or 'unauthorized' in error_str:
            return "Authentication failed. Please check your API token in the sidebar."

        if '403' in error_str or 'forbidden' in error_str:
            return "Access denied. Please verify you have permission to access this resource."

        if '404' in error_str or 'not found' in error_str:
            return "The requested resource was not found. Please verify the URL or ID."

        if '429' in error_str or 'rate limit' in error_str:
            return "Rate limit exceeded. Please wait a few minutes and try again."

        if '500' in error_str or 'server error' in error_str:
            return "The server encountered an error. Please try again later."

        # Data errors
        if 'keyerror' in error_type.lower():
            return "Missing required data field. The data format may have changed."

        if 'valueerror' in error_type.lower():
            return "Invalid data value encountered. Please verify your input."

        if 'typeerror' in error_type.lower():
            return "Unexpected data type. The data format may be incorrect."

        # File errors
        if 'filenotfound' in error_type.lower():
            return "File not found. Please check the file path."

        if 'permission' in error_str:
            return "Permission denied. Please check file permissions."

        # Default message
        return f"An unexpected error occurred: {str(error)}"

    @staticmethod
    def handle_api_error(error: Exception, platform: str):
        """
        Handle API-specific errors.

        Args:
            error: The exception
            platform: Platform name (Facebook, Instagram, YouTube)
        """
        ErrorHandler.show_error(
            error,
            title=f"{platform} API Error",
            show_details=True,
            show_retry=False
        )

        # Show platform-specific help
        st.info(f"""
        💡 **Troubleshooting Tips for {platform}:**

        1. Verify your API token is correct
        2. Check that the {platform} page/profile URL is valid
        3. Ensure you have permission to access this content
        4. Try reducing the date range
        5. Check the Apify dashboard for usage limits
        """)

    @staticmethod
    def handle_data_error(error: Exception, context: str):
        """
        Handle data processing errors.

        Args:
            error: The exception
            context: Context where error occurred
        """
        ErrorHandler.show_error(
            error,
            title=f"Data Processing Error ({context})",
            show_details=True,
            show_retry=False
        )

        st.warning("""
        💡 **Possible Solutions:**

        - The data format may have changed
        - Try clearing cached data
        - Re-fetch the data
        - Check if all required fields are present
        """)


def safe_execute(
    func: Callable,
    error_title: str = "Operation Failed",
    show_details: bool = False,
    default_return: Any = None
) -> Any:
    """
    Safely execute a function with error handling.

    Args:
        func: Function to execute
        error_title: Title for error message
        show_details: Whether to show technical details
        default_return: Default value to return on error

    Returns:
        Function result or default_return on error
    """
    try:
        return func()
    except Exception as e:
        ErrorHandler.show_error(e, title=error_title, show_details=show_details)
        return default_return


def with_error_boundary(
    error_title: str = "Operation Failed",
    show_details: bool = False,
    show_retry: bool = False
):
    """
    Decorator for adding error boundaries to functions.

    Args:
        error_title: Title for error message
        show_details: Whether to show technical details
        show_retry: Whether to show retry button

    Usage:
        @with_error_boundary("Failed to fetch data")
        def fetch_data():
            # Your code here
            return data
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                ErrorHandler.show_error(
                    e,
                    title=error_title,
                    show_details=show_details,
                    show_retry=show_retry,
                    retry_callback=lambda: func(*args, **kwargs) if show_retry else None
                )
                return None
        return wrapper
    return decorator


def validate_input(
    value: Any,
    field_name: str,
    required: bool = True,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    pattern: Optional[str] = None
) -> bool:
    """
    Validate user input with helpful error messages.

    Args:
        value: Value to validate
        field_name: Name of the field
        required: Whether field is required
        min_length: Minimum length (for strings)
        max_length: Maximum length (for strings)
        pattern: Regex pattern to match

    Returns:
        True if valid, False otherwise
    """
    import re

    # Required check
    if required and not value:
        st.error(f"❌ {field_name} is required")
        return False

    # Skip other checks if value is empty and not required
    if not value and not required:
        return True

    # String validations
    if isinstance(value, str):
        if min_length and len(value) < min_length:
            st.error(f"❌ {field_name} must be at least {min_length} characters")
            return False

        if max_length and len(value) > max_length:
            st.error(f"❌ {field_name} must be no more than {max_length} characters")
            return False

        if pattern and not re.match(pattern, value):
            st.error(f"❌ {field_name} format is invalid")
            return False

    return True


def show_warning(
    message: str,
    title: str = "Warning",
    dismissible: bool = True
):
    """
    Show a warning message.

    Args:
        message: Warning message
        title: Warning title
        dismissible: Whether warning can be dismissed
    """
    st.markdown(f"""
    <div style="
        background: rgba(245, 158, 11, 0.1);
        border-left: 4px solid var(--accent-orange);
        padding: 1.5rem;
        border-radius: var(--radius-md);
        margin: 1rem 0;
    ">
        <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 0.75rem;">
            <span style="font-size: 2rem;">⚠️</span>
            <h3 style="margin: 0; color: var(--accent-orange);">{title}</h3>
        </div>
        <p style="color: var(--text-primary); margin: 0;">
            {message}
        </p>
    </div>
    """, unsafe_allow_html=True)


def show_info(
    message: str,
    title: str = "Information",
    icon: str = "ℹ️"
):
    """
    Show an info message.

    Args:
        message: Info message
        title: Info title
        icon: Icon emoji
    """
    st.markdown(f"""
    <div style="
        background: rgba(59, 130, 246, 0.1);
        border-left: 4px solid var(--accent-blue);
        padding: 1.5rem;
        border-radius: var(--radius-md);
        margin: 1rem 0;
    ">
        <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 0.75rem;">
            <span style="font-size: 2rem;">{icon}</span>
            <h3 style="margin: 0; color: var(--accent-blue);">{title}</h3>
        </div>
        <p style="color: var(--text-primary); margin: 0;">
            {message}
        </p>
    </div>
    """, unsafe_allow_html=True)


def show_success(
    message: str,
    title: str = "Success",
    icon: str = "✅"
):
    """
    Show a success message.

    Args:
        message: Success message
        title: Success title
        icon: Icon emoji
    """
    st.markdown(f"""
    <div style="
        background: rgba(16, 185, 129, 0.1);
        border-left: 4px solid var(--accent-green);
        padding: 1.5rem;
        border-radius: var(--radius-md);
        margin: 1rem 0;
    ">
        <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 0.75rem;">
            <span style="font-size: 2rem;">{icon}</span>
            <h3 style="margin: 0; color: var(--accent-green);">{title}</h3>
        </div>
        <p style="color: var(--text-primary); margin: 0;">
            {message}
        </p>
    </div>
    """, unsafe_allow_html=True)
