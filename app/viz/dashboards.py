"""
Enhanced Dashboard Components for Social Media Analytics
========================================================

Rich, interactive dashboards with KPIs, trends, and insights.
"""

from typing import Dict, List, Optional, Any
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Optional Plotly for interactive charts
try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False


# ============================================================================
# THEME & STYLING (single source: app.styles.theme)
# ============================================================================

from app.styles.theme import THEME_COLORS, GRADIENT_STYLES


# ============================================================================
# KPI DASHBOARD
# ============================================================================

def create_kpi_dashboard(posts: List[Dict], platform: str) -> None:
    """
    Create comprehensive KPI dashboard with key metrics.

    Args:
        posts: List of posts
        platform: Platform name (Facebook, Instagram, YouTube)
    """
    st.markdown("## 📊 Key Performance Indicators")

    if not posts:
        st.warning("No data available for KPI dashboard")
        return

    # Calculate metrics
    total_posts = len(posts)
    total_likes = sum(p.get('likes', 0) for p in posts)
    total_comments = sum(p.get('comments_count', 0) for p in posts)
    total_shares = sum(p.get('shares_count', 0) for p in posts)

    # Calculate averages
    avg_likes = total_likes / total_posts if total_posts > 0 else 0
    avg_comments = total_comments / total_posts if total_posts > 0 else 0
    avg_engagement = (total_likes + total_comments + total_shares) / total_posts if total_posts > 0 else 0

    # Find best performing post
    best_post = max(posts, key=lambda p: p.get('likes', 0) + p.get('comments_count', 0) + p.get('shares_count', 0))
    best_engagement = best_post.get('likes', 0) + best_post.get('comments_count', 0) + best_post.get('shares_count', 0)

    # Row 1: Primary Metrics
    st.markdown("### 🎯 Primary Metrics")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        _create_metric_card(
            "📝 Total Posts",
            f"{total_posts:,}",
            "Posts published this month",
            GRADIENT_STYLES['purple']
        )

    with col2:
        _create_metric_card(
            "❤️ Total Likes",
            f"{total_likes:,}",
            "Total likes received",
            GRADIENT_STYLES['pink']
        )

    with col3:
        _create_metric_card(
            "💬 Total Comments",
            f"{total_comments:,}",
            "Total comments received",
            GRADIENT_STYLES['blue']
        )

    with col4:
        _create_metric_card(
            "🔄 Total Shares",
            f"{total_shares:,}",
            "Total shares/retweets",
            GRADIENT_STYLES['green']
        )

    st.markdown("---")

    # Row 2: Engagement Metrics
    st.markdown("### 📈 Engagement Metrics")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        _create_metric_card(
            "👍 Avg Likes/Post",
            f"{avg_likes:.1f}",
            "Average likes per post",
            GRADIENT_STYLES['orange']
        )

    with col2:
        _create_metric_card(
            "💭 Avg Comments/Post",
            f"{avg_comments:.1f}",
            "Average comments per post",
            GRADIENT_STYLES['teal']
        )

    with col3:
        _create_metric_card(
            "🚀 Avg Engagement/Post",
            f"{avg_engagement:.1f}",
            "Average total engagement",
            GRADIENT_STYLES['green']
        )

    with col4:
        _create_metric_card(
            "🏆 Best Post",
            f"{best_engagement:,}",
            "Highest engagement post",
            GRADIENT_STYLES['pink']
        )

    # Platform-specific metrics
    if platform == "YouTube":
        st.markdown("---")
        st.markdown("### 🎥 YouTube Metrics")

        total_views = sum(p.get('views', 0) for p in posts)
        avg_views = total_views / total_posts if total_posts > 0 else 0

        col1, col2, col3 = st.columns(3)

        with col1:
            _create_metric_card(
                "👁️ Total Views",
                f"{total_views:,}",
                "Total video views",
                GRADIENT_STYLES['blue']
            )

        with col2:
            _create_metric_card(
                "📊 Avg Views/Video",
                f"{avg_views:.0f}",
                "Average views per video",
                GRADIENT_STYLES['purple']
            )

        with col3:
            engagement_rate = (total_likes + total_comments) / total_views * 100 if total_views > 0 else 0
            _create_metric_card(
                "⚡ Engagement Rate",
                f"{engagement_rate:.2f}%",
                "Engagement vs views",
                GRADIENT_STYLES['green']
            )


def _create_metric_card(title: str, value: str, description: str, gradient: str) -> None:
    """Create a styled metric card."""
    st.markdown(
        f"""
        <div style="
            background: {gradient};
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
            color: white;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 1rem;
        ">
            <h4 style="margin: 0; font-size: 1rem; opacity: 0.9;">{title}</h4>
            <h2 style="margin: 0.5rem 0; font-size: 2rem; font-weight: bold;">{value}</h2>
            <p style="margin: 0; font-size: 0.85rem; opacity: 0.8;">{description}</p>
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================================
# TREND ANALYSIS
# ============================================================================

def create_engagement_trend_chart(posts: List[Dict]) -> None:
    """
    Create interactive engagement trend chart over time.

    Args:
        posts: List of posts with published_at dates
    """
    st.markdown("## 📈 Engagement Trends Over Time")

    if not posts:
        st.warning("No data available for trend analysis")
        return

    # Prepare data
    df = pd.DataFrame(posts)

    if 'published_at' not in df.columns:
        st.error("No publication date information available")
        return

    # Convert to datetime
    df['published_at'] = pd.to_datetime(df['published_at'])
    df['date'] = df['published_at'].dt.date

    # Group by date and calculate metrics
    daily_metrics = df.groupby('date').agg({
        'likes': 'sum',
        'comments_count': 'sum',
        'shares_count': 'sum',
        'post_id': 'count'
    }).reset_index()

    daily_metrics.columns = ['date', 'likes', 'comments', 'shares', 'posts']
    daily_metrics['total_engagement'] = daily_metrics['likes'] + daily_metrics['comments'] + daily_metrics['shares']

    if PLOTLY_AVAILABLE:
        # Create multi-line chart
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=daily_metrics['date'],
            y=daily_metrics['likes'],
            name='Likes',
            mode='lines+markers',
            line=dict(color=THEME_COLORS['primary'], width=3),
            marker=dict(size=8)
        ))

        fig.add_trace(go.Scatter(
            x=daily_metrics['date'],
            y=daily_metrics['comments'],
            name='Comments',
            mode='lines+markers',
            line=dict(color=THEME_COLORS['secondary'], width=3),
            marker=dict(size=8)
        ))

        fig.add_trace(go.Scatter(
            x=daily_metrics['date'],
            y=daily_metrics['shares'],
            name='Shares',
            mode='lines+markers',
            line=dict(color=THEME_COLORS['info'], width=3),
            marker=dict(size=8)
        ))

        fig.update_layout(
            title="Daily Engagement Breakdown",
            xaxis_title="Date",
            yaxis_title="Count",
            hovermode='x unified',
            plot_bgcolor=THEME_COLORS['background'],
            paper_bgcolor=THEME_COLORS['background'],
            font=dict(color=THEME_COLORS['tertiary']),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )

        st.plotly_chart(fig, use_container_width=True)

        # Add total engagement trend
        fig2 = go.Figure()

        fig2.add_trace(go.Scatter(
            x=daily_metrics['date'],
            y=daily_metrics['total_engagement'],
            name='Total Engagement',
            mode='lines+markers',
            fill='tozeroy',
            line=dict(color=THEME_COLORS['success'], width=3),
            marker=dict(size=10)
        ))

        fig2.update_layout(
            title="Total Daily Engagement Trend",
            xaxis_title="Date",
            yaxis_title="Total Engagement",
            hovermode='x',
            plot_bgcolor=THEME_COLORS['background'],
            paper_bgcolor=THEME_COLORS['background'],
            font=dict(color=THEME_COLORS['tertiary'])
        )

        st.plotly_chart(fig2, use_container_width=True)
    else:
        # Fallback to Streamlit native charts
        st.line_chart(daily_metrics.set_index('date')[['likes', 'comments', 'shares']])


def create_posting_frequency_chart(posts: List[Dict]) -> None:
    """
    Create posting frequency visualization.

    Args:
        posts: List of posts
    """
    st.markdown("## 📅 Posting Frequency Analysis")

    if not posts:
        st.warning("No data available")
        return

    df = pd.DataFrame(posts)
    df['published_at'] = pd.to_datetime(df['published_at'])
    df['date'] = df['published_at'].dt.date
    df['weekday'] = df['published_at'].dt.day_name()
    df['hour'] = df['published_at'].dt.hour

    col1, col2 = st.columns(2)

    with col1:
        # Posts per day
        posts_per_day = df.groupby('date').size().reset_index(name='count')

        if PLOTLY_AVAILABLE:
            fig = px.bar(
                posts_per_day,
                x='date',
                y='count',
                title="Posts Per Day",
                color_discrete_sequence=[THEME_COLORS['primary']]
            )
            fig.update_layout(
                plot_bgcolor=THEME_COLORS['background'],
                paper_bgcolor=THEME_COLORS['background'],
                font=dict(color=THEME_COLORS['tertiary'])
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.bar_chart(posts_per_day.set_index('date'))

    with col2:
        # Posts by weekday
        posts_by_weekday = df.groupby('weekday').size().reset_index(name='count')
        weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        posts_by_weekday['weekday'] = pd.Categorical(posts_by_weekday['weekday'], categories=weekday_order, ordered=True)
        posts_by_weekday = posts_by_weekday.sort_values('weekday')

        if PLOTLY_AVAILABLE:
            fig = px.bar(
                posts_by_weekday,
                x='weekday',
                y='count',
                title="Posts By Day of Week",
                color_discrete_sequence=[THEME_COLORS['secondary']]
            )
            fig.update_layout(
                plot_bgcolor=THEME_COLORS['background'],
                paper_bgcolor=THEME_COLORS['background'],
                font=dict(color=THEME_COLORS['tertiary'])
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.bar_chart(posts_by_weekday.set_index('weekday'))


# ============================================================================
# PERFORMANCE COMPARISON
# ============================================================================

def create_performance_comparison(
    facebook_posts: Optional[List[Dict]] = None,
    instagram_posts: Optional[List[Dict]] = None,
    youtube_posts: Optional[List[Dict]] = None
) -> None:
    """
    Create cross-platform performance comparison.

    Args:
        facebook_posts: Facebook posts
        instagram_posts: Instagram posts
        youtube_posts: YouTube posts
    """
    st.markdown("## 🔄 Cross-Platform Performance Comparison")

    # Collect available platforms
    platforms_data = []

    if facebook_posts:
        platforms_data.append({
            'Platform': 'Facebook',
            'Posts': len(facebook_posts),
            'Total Likes': sum(p.get('likes', 0) for p in facebook_posts),
            'Total Comments': sum(p.get('comments_count', 0) for p in facebook_posts),
            'Total Shares': sum(p.get('shares_count', 0) for p in facebook_posts)
        })

    if instagram_posts:
        platforms_data.append({
            'Platform': 'Instagram',
            'Posts': len(instagram_posts),
            'Total Likes': sum(p.get('likes', 0) for p in instagram_posts),
            'Total Comments': sum(p.get('comments_count', 0) for p in instagram_posts),
            'Total Shares': 0  # Instagram doesn't have shares
        })

    if youtube_posts:
        platforms_data.append({
            'Platform': 'YouTube',
            'Posts': len(youtube_posts),
            'Total Likes': sum(p.get('likes', 0) for p in youtube_posts),
            'Total Comments': sum(p.get('comments_count', 0) for p in youtube_posts),
            'Total Shares': sum(p.get('shares_count', 0) for p in youtube_posts)
        })

    if not platforms_data:
        st.warning("No platform data available for comparison")
        return

    df = pd.DataFrame(platforms_data)

    # Calculate total engagement
    df['Total Engagement'] = df['Total Likes'] + df['Total Comments'] + df['Total Shares']
    df['Avg Engagement'] = df['Total Engagement'] / df['Posts']

    # Display comparison table
    st.dataframe(
        df.style.background_gradient(cmap='Greens', subset=['Total Engagement', 'Avg Engagement']),
        use_container_width=True
    )

    if PLOTLY_AVAILABLE:
        # Create comparison charts
        col1, col2 = st.columns(2)

        with col1:
            fig = px.bar(
                df,
                x='Platform',
                y='Total Engagement',
                title="Total Engagement by Platform",
                color='Platform',
                color_discrete_sequence=[THEME_COLORS['primary'], THEME_COLORS['secondary'], THEME_COLORS['info']]
            )
            fig.update_layout(
                plot_bgcolor=THEME_COLORS['background'],
                paper_bgcolor=THEME_COLORS['background'],
                font=dict(color=THEME_COLORS['tertiary']),
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.bar(
                df,
                x='Platform',
                y='Avg Engagement',
                title="Average Engagement per Post",
                color='Platform',
                color_discrete_sequence=[THEME_COLORS['primary'], THEME_COLORS['secondary'], THEME_COLORS['info']]
            )
            fig.update_layout(
                plot_bgcolor=THEME_COLORS['background'],
                paper_bgcolor=THEME_COLORS['background'],
                font=dict(color=THEME_COLORS['tertiary']),
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)

        # Engagement breakdown by type
        fig = go.Figure()

        fig.add_trace(go.Bar(
            name='Likes',
            x=df['Platform'],
            y=df['Total Likes'],
            marker_color=THEME_COLORS['primary']
        ))

        fig.add_trace(go.Bar(
            name='Comments',
            x=df['Platform'],
            y=df['Total Comments'],
            marker_color=THEME_COLORS['secondary']
        ))

        fig.add_trace(go.Bar(
            name='Shares',
            x=df['Platform'],
            y=df['Total Shares'],
            marker_color=THEME_COLORS['info']
        ))

        fig.update_layout(
            title="Engagement Breakdown by Platform",
            barmode='group',
            plot_bgcolor=THEME_COLORS['background'],
            paper_bgcolor=THEME_COLORS['background'],
            font=dict(color=THEME_COLORS['tertiary'])
        )

        st.plotly_chart(fig, use_container_width=True)


# ============================================================================
# INSIGHTS SUMMARY
# ============================================================================

def create_insights_summary(posts: List[Dict], platform: str) -> None:
    """
    Create automated insights summary.

    Args:
        posts: List of posts
        platform: Platform name
    """
    st.markdown("## 💡 Key Insights")

    if not posts or len(posts) < 2:
        st.info("Not enough data to generate insights")
        return

    # Calculate insights
    total_posts = len(posts)
    total_engagement = sum(p.get('likes', 0) + p.get('comments_count', 0) + p.get('shares_count', 0) for p in posts)
    avg_engagement = total_engagement / total_posts

    # Find best and worst posts
    posts_with_engagement = [(p, p.get('likes', 0) + p.get('comments_count', 0) + p.get('shares_count', 0)) for p in posts]
    best_post, best_engagement = max(posts_with_engagement, key=lambda x: x[1])
    worst_post, worst_engagement = min(posts_with_engagement, key=lambda x: x[1])

    # Engagement range
    engagement_range = best_engagement - worst_engagement

    # Display insights
    col1, col2, col3 = st.columns(3)

    with col1:
        st.success(f"**📊 {total_posts}** posts analyzed this month")
        st.info(f"**⚡ {avg_engagement:.0f}** average engagement per post")

    with col2:
        st.success(f"**🏆 Best Post:** {best_engagement:,} engagement")
        best_text = best_post.get('text', '')[:50]
        st.caption(f"_{best_text}..._" if len(best_text) > 47 else f"_{best_text}_")

    with col3:
        improvement = ((best_engagement - avg_engagement) / avg_engagement * 100) if avg_engagement > 0 else 0
        st.warning(f"**📈 Top post is {improvement:.0f}% above average**")
        st.caption(f"Performance range: {worst_engagement:,} - {best_engagement:,}")

    # Recommendations
    st.markdown("### 🎯 Recommendations")

    if avg_engagement < 100:
        st.write("- 📢 Consider increasing posting frequency to boost engagement")

    if best_engagement > avg_engagement * 2:
        st.write(f"- ✨ Analyze your best performing post to replicate success")

    st.write("- 💬 Engage with comments to build community and increase visibility")
    st.write("- 📅 Maintain consistent posting schedule for better reach")


# ============================================================================
# BACKWARD-COMPATIBILITY ALIASES
# ============================================================================

def create_trends_dashboard(posts: List[Dict]) -> None:
    """
    Backward-compatible wrapper expected by social_media_app imports.
    Renders engagement trends and posting frequency charts.
    """
    create_engagement_trend_chart(posts)
    st.markdown("---")
    create_posting_frequency_chart(posts)


def create_cross_platform_comparison(
    facebook_posts: Optional[List[Dict]] = None,
    instagram_posts: Optional[List[Dict]] = None,
    youtube_posts: Optional[List[Dict]] = None
) -> None:
    """
    Backward-compatible wrapper that delegates to create_performance_comparison.
    """
    create_performance_comparison(
        facebook_posts=facebook_posts,
        instagram_posts=instagram_posts,
        youtube_posts=youtube_posts,
    )
