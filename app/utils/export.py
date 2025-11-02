"""
Export Features for Social Media Analytics Dashboard
=====================================================

Provides CSV export, PDF reports, and data download capabilities.
"""

import streamlit as st
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime
import io
import base64


def create_csv_download_button(
    data: pd.DataFrame,
    filename: str,
    button_text: str = "📥 Download CSV",
    help_text: Optional[str] = None
):
    """
    Create a download button for CSV export.

    Args:
        data: DataFrame to export
        filename: Name of the file (without extension)
        button_text: Text for the button
        help_text: Optional help text
    """
    if data.empty:
        st.warning("No data available to export")
        return

    # Convert DataFrame to CSV
    csv = data.to_csv(index=False)

    # Create download button
    st.download_button(
        label=button_text,
        data=csv,
        file_name=f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        help=help_text or f"Download {len(data)} rows as CSV"
    )


def create_json_download_button(
    data: List[Dict[str, Any]],
    filename: str,
    button_text: str = "📥 Download JSON",
    help_text: Optional[str] = None
):
    """
    Create a download button for JSON export.

    Args:
        data: List of dictionaries to export
        filename: Name of the file (without extension)
        button_text: Text for the button
        help_text: Optional help text
    """
    import json

    if not data:
        st.warning("No data available to export")
        return

    # Custom JSON encoder to handle Timestamp and other non-serializable objects
    def json_serializer(obj):
        """Custom JSON serializer for objects not serializable by default json code"""
        import pandas as pd
        if isinstance(obj, (pd.Timestamp, pd.DatetimeTZDtype)):
            return obj.isoformat() if hasattr(obj, 'isoformat') else str(obj)
        elif hasattr(obj, 'isoformat'):  # datetime objects
            return obj.isoformat()
        elif isinstance(obj, (pd.Series, pd.DataFrame)):
            return obj.to_dict()
        return str(obj)

    # Convert to JSON with custom serializer
    json_str = json.dumps(data, indent=2, ensure_ascii=False, default=json_serializer)

    # Create download button
    st.download_button(
        label=button_text,
        data=json_str,
        file_name=f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json",
        help=help_text or f"Download {len(data)} items as JSON"
    )


def create_export_section(
    posts_data: List[Dict[str, Any]],
    platform: str
):
    """
    Create export section with multiple format options.

    Args:
        posts_data: List of posts
        platform: Platform name
    """
    st.markdown("### 📥 Export Data")
    st.markdown("Download your analytics data in various formats")

    if not posts_data:
        st.info("No data available to export. Please analyze a page/profile first.")
        return

    col1, col2, col3 = st.columns(3)

    with col1:
        # Export posts as CSV
        posts_df = pd.DataFrame(posts_data)
        create_csv_download_button(
            posts_df,
            f"{platform.lower()}_posts",
            "📥 Posts CSV"
        )

    with col2:
        # Export posts as JSON
        create_json_download_button(
            posts_data,
            f"{platform.lower()}_posts",
            "📥 Posts JSON"
        )

    with col3:
        # Export summary statistics
        summary_data = generate_summary_stats(posts_data, platform)
        create_csv_download_button(
            summary_data,
            f"{platform.lower()}_summary",
            "📥 Summary CSV"
        )


def generate_summary_stats(
    posts_data: List[Dict[str, Any]],
    platform: str
) -> pd.DataFrame:
    """
    Generate summary statistics DataFrame.

    Args:
        posts_data: List of posts
        platform: Platform name

    Returns:
        DataFrame with summary statistics
    """
    if not posts_data:
        return pd.DataFrame()

    df = pd.DataFrame(posts_data)

    summary = {
        'Metric': [],
        'Value': []
    }

    # Basic counts
    summary['Metric'].append('Total Posts')
    summary['Value'].append(len(posts_data))

    # Engagement metrics
    if 'likes' in df.columns:
        summary['Metric'].append('Total Likes')
        summary['Value'].append(df['likes'].sum())
        summary['Metric'].append('Average Likes')
        summary['Value'].append(round(df['likes'].mean(), 2))

    if 'comments_count' in df.columns:
        summary['Metric'].append('Total Comments')
        summary['Value'].append(df['comments_count'].sum())
        summary['Metric'].append('Average Comments')
        summary['Value'].append(round(df['comments_count'].mean(), 2))

    if 'shares' in df.columns:
        summary['Metric'].append('Total Shares')
        summary['Value'].append(df['shares'].sum())
        summary['Metric'].append('Average Shares')
        summary['Value'].append(round(df['shares'].mean(), 2))

    # Platform-specific metrics
    if platform == "Instagram":
        if 'hashtags' in df.columns:
            all_hashtags = [tag for post in posts_data if post.get('hashtags')
                           for tag in post['hashtags']]
            summary['Metric'].append('Total Hashtags Used')
            summary['Value'].append(len(all_hashtags))

    elif platform == "Facebook":
        if 'reactions' in df.columns:
            total_reactions = sum(sum(post.get('reactions', {}).values())
                                for post in posts_data)
            summary['Metric'].append('Total Reactions')
            summary['Value'].append(total_reactions)

    return pd.DataFrame(summary)


def create_comments_export(
    posts_data: List[Dict[str, Any]],
    platform: str
):
    """
    Create export buttons for comments data.

    Args:
        posts_data: List of posts with comments
        platform: Platform name
    """
    # Extract all comments
    all_comments = []

    for post in posts_data:
        post_id = post.get('post_id', 'unknown')
        comments = post.get('comments_list', [])

        if isinstance(comments, list):
            for comment in comments:
                if isinstance(comment, dict):
                    comment_data = {
                        'post_id': post_id,
                        'comment_text': comment.get('text', ''),
                        'comment_author': comment.get('author', 'Unknown'),
                        'comment_likes': comment.get('likes', 0),
                        'comment_timestamp': comment.get('timestamp', '')
                    }
                    all_comments.append(comment_data)
                elif isinstance(comment, str):
                    comment_data = {
                        'post_id': post_id,
                        'comment_text': comment,
                        'comment_author': 'Unknown',
                        'comment_likes': 0,
                        'comment_timestamp': ''
                    }
                    all_comments.append(comment_data)

    if all_comments:
        st.markdown("#### 💬 Export Comments")

        col1, col2 = st.columns(2)

        with col1:
            comments_df = pd.DataFrame(all_comments)
            create_csv_download_button(
                comments_df,
                f"{platform.lower()}_comments",
                f"📥 Comments CSV ({len(all_comments)} comments)"
            )

        with col2:
            create_json_download_button(
                all_comments,
                f"{platform.lower()}_comments",
                f"📥 Comments JSON ({len(all_comments)} comments)"
            )
    else:
        st.info("No comments available to export")


def create_analytics_export(
    analytics_data: Dict[str, Any],
    platform: str
):
    """
    Create export button for analytics summary.

    Args:
        analytics_data: Dictionary of analytics metrics
        platform: Platform name
    """
    if not analytics_data:
        return

    # Convert analytics dict to DataFrame
    analytics_df = pd.DataFrame([analytics_data])

    create_csv_download_button(
        analytics_df,
        f"{platform.lower()}_analytics",
        "📥 Analytics Summary CSV",
        "Download complete analytics summary"
    )


def create_comprehensive_export_section(
    posts_data: List[Dict[str, Any]],
    platform: str
):
    """
    Create comprehensive export section with all options.

    Args:
        posts_data: List of posts
        platform: Platform name
    """
    with st.expander("📥 Export Data", expanded=False):
        if not posts_data:
            st.info("No data available to export. Please analyze a page/profile first.")
            return

        st.markdown(f"### Export {platform} Data")
        st.markdown("Choose from various export formats below:")

        # Posts export
        st.markdown("#### 📊 Posts Data")
        col1, col2 = st.columns(2)

        with col1:
            posts_df = pd.DataFrame(posts_data)
            create_csv_download_button(
                posts_df,
                f"{platform.lower()}_posts",
                f"📥 All Posts CSV ({len(posts_data)} posts)"
            )

        with col2:
            create_json_download_button(
                posts_data,
                f"{platform.lower()}_posts",
                f"📥 All Posts JSON ({len(posts_data)} posts)"
            )

        st.markdown("---")

        # Comments export
        create_comments_export(posts_data, platform)

        st.markdown("---")

        # Summary statistics
        st.markdown("#### 📈 Summary Statistics")
        summary_data = generate_summary_stats(posts_data, platform)

        if not summary_data.empty:
            col1, col2 = st.columns([2, 1])

            with col1:
                st.dataframe(summary_data, use_container_width=True, hide_index=True)

            with col2:
                create_csv_download_button(
                    summary_data,
                    f"{platform.lower()}_summary",
                    "📥 Download Summary"
                )

        st.markdown("---")

        # Help section
        st.markdown("""
        #### 💡 Export Tips

        - **CSV Format**: Best for Excel, Google Sheets, and data analysis
        - **JSON Format**: Best for developers and API integrations
        - **Summary**: Quick overview of key metrics
        - **Comments**: Separate export for detailed comment analysis

        All files include a timestamp in the filename for easy organization.
        """)
