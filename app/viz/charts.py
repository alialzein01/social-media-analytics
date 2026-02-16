"""
Visualization Components for Social Media Analytics
===================================================

This module contains all chart creation functions for the dashboard.
Extracted from monolithic app for better maintainability.

Features:
- Monthly overview charts
- Engagement breakdowns
- Reaction/sentiment pie charts
- Top posts visualizations
- Platform-specific charts
"""

from typing import Dict, List, Optional, Any
import streamlit as st
import pandas as pd
from collections import Counter
import matplotlib.pyplot as plt

# Optional Plotly for interactive charts
try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False


# ============================================================================
# THEME CONFIGURATION (colors from app.styles.theme)
# ============================================================================

from app.styles.theme import THEME_COLORS, SENTIMENT_COLORS, GRADIENT_STYLES

REACTION_EMOJIS = {
    'like': '👍',
    'love': '❤️',
    'haha': '😂',
    'wow': '😮',
    'sad': '😢',
    'angry': '😠'
}


# ============================================================================
# MONTHLY OVERVIEW CHARTS
# ============================================================================

# Standard chart height for consistent layout
CHART_HEIGHT = 340


def create_monthly_overview_charts(df: pd.DataFrame) -> None:
    """
    Create monthly overview charts: posting trend and top performers.

    Charts: Posts per day (line), Top 5 posts by engagement (bar).
    Engagement breakdown is shown in Overview KPIs only to avoid redundancy.
    """
    df_copy = df.copy()

    if 'published_at' in df_copy.columns:
        df_copy['published_at'] = pd.to_datetime(df_copy['published_at'], utc=True).dt.tz_localize(None)
        df_copy['date'] = df_copy['published_at'].dt.date
    else:
        df_copy['date'] = pd.to_datetime(df_copy['published_at']).dt.date

    # Posts per day — when did we post?
    st.subheader("📈 Posts Per Day")
    posts_per_day = df_copy.groupby('date').size().reset_index(name='count')

    if PLOTLY_AVAILABLE:
        fig = px.line(
            posts_per_day,
            x="date",
            y="count",
            markers=True,
            title="Posts Per Day",
            color_discrete_sequence=[THEME_COLORS['primary']]
        )
        fig.update_layout(
            plot_bgcolor=THEME_COLORS['background'],
            paper_bgcolor=THEME_COLORS['background'],
            font_color=THEME_COLORS['text'],
            height=CHART_HEIGHT,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.line_chart(posts_per_day.set_index('date'))

    # Top posts — which content performed best?
    st.subheader("🏆 Top 5 Posts by Engagement")
    df_work = df.copy()
    df_work['total_engagement'] = df_work['likes'] + df_work['comments_count'] + df_work['shares_count']
    top_posts = df_work.nlargest(5, 'total_engagement')[['text', 'total_engagement']].copy()
    top_posts['text'] = top_posts['text'].str[:50] + '...'

    if PLOTLY_AVAILABLE:
        fig = px.bar(
            top_posts.reset_index().rename(columns={'text': 'Caption'}),
            x="Caption",
            y="total_engagement",
            title="Top 5 Posts by Engagement",
            color_discrete_sequence=[THEME_COLORS['primary']]
        )
        fig.update_layout(
            plot_bgcolor=THEME_COLORS['background'],
            paper_bgcolor=THEME_COLORS['background'],
            font_color=THEME_COLORS['text'],
            height=CHART_HEIGHT,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.bar_chart(top_posts.set_index('text'))


# ============================================================================
# REACTION CHARTS
# ============================================================================

def create_reaction_pie_chart(reactions: Dict[str, int]) -> None:
    """
    Create reaction breakdown: single bar chart (avoids duplicating metrics).
    """
    reactions_filtered = {k: v for k, v in reactions.items() if v > 0}

    if not reactions_filtered:
        st.info("No reaction data available for this post")
        return

    st.subheader("😊 Reaction Breakdown")
    reactions_df = pd.DataFrame(
        list(reactions_filtered.items()),
        columns=['Reaction', 'Count']
    )
    # Use emoji in labels for clarity
    reactions_df['Reaction'] = reactions_df['Reaction'].apply(
        lambda r: f"{REACTION_EMOJIS.get(r, '👍')} {str(r).title()}"
    )
    reactions_df = reactions_df.set_index('Reaction')
    st.bar_chart(reactions_df)


def create_reaction_breakdown_detailed(reactions: Dict[str, int]) -> None:
    """
    Create detailed reaction breakdown with pie chart.

    Args:
        reactions: Dictionary of reaction type -> count
    """
    reactions_filtered = {k: v for k, v in reactions.items() if v > 0}

    if not reactions_filtered:
        st.info("No reaction data available")
        return

    if PLOTLY_AVAILABLE:
        reactions_df = pd.DataFrame(
            list(reactions_filtered.items()),
            columns=['Reaction', 'Count']
        )
        fig = px.pie(
            reactions_df,
            values='Count',
            names='Reaction',
            title='Reaction Distribution',
            color_discrete_sequence=[
                THEME_COLORS['primary'],
                THEME_COLORS['secondary'],
                THEME_COLORS['tertiary'],
                '#667eea',
                '#f093fb',
                '#4facfe'
            ]
        )
        fig.update_layout(
            plot_bgcolor=THEME_COLORS['background'],
            paper_bgcolor=THEME_COLORS['background'],
            font_color=THEME_COLORS['text']
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        create_reaction_pie_chart(reactions)


# ============================================================================
# SENTIMENT CHARTS
# ============================================================================

def create_sentiment_pie_chart(sentiment_counts: Dict[str, int]) -> None:
    """
    Create sentiment distribution pie chart.

    Args:
        sentiment_counts: Dictionary of sentiment -> count
    """
    if not sentiment_counts or sum(sentiment_counts.values()) == 0:
        st.info("No sentiment data available")
        return

    # Prepare data
    labels = []
    sizes = []
    color_list = []

    for sentiment, count in sentiment_counts.items():
        if count > 0:
            labels.append(sentiment.title())
            sizes.append(count)
            color_list.append(SENTIMENT_COLORS.get(sentiment, '#95a5a6'))

    if not sizes:
        st.info("No sentiment data to display")
        return

    # Create pie chart
    fig, ax = plt.subplots(figsize=(8, 6), facecolor=THEME_COLORS['background'])
    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        colors=color_list,
        autopct='%1.1f%%',
        startangle=90,
        textprops={'fontsize': 12, 'weight': 'bold', 'color': THEME_COLORS['text']}
    )

    ax.set_title(
        'Sentiment Distribution',
        fontsize=16,
        fontweight='bold',
        pad=20,
        color=THEME_COLORS['text']
    )
    fig.patch.set_facecolor(THEME_COLORS['background'])

    st.pyplot(fig)


def create_sentiment_summary(sentiment_counts: Dict[str, int]) -> None:
    """
    Create sentiment summary with metrics.

    Args:
        sentiment_counts: Dictionary of sentiment -> count
    """
    total_comments = sum(sentiment_counts.values())

    if total_comments == 0:
        st.info("No sentiment data available")
        return

    st.markdown("**Sentiment Summary:**")

    col1, col2, col3 = st.columns(3)

    with col1:
        positive_pct = sentiment_counts.get('positive', 0) / total_comments * 100
        st.metric(
            "😊 Positive",
            f"{sentiment_counts.get('positive', 0):,}",
            f"{positive_pct:.1f}%"
        )

    with col2:
        negative_pct = sentiment_counts.get('negative', 0) / total_comments * 100
        st.metric(
            "😢 Negative",
            f"{sentiment_counts.get('negative', 0):,}",
            f"{negative_pct:.1f}%"
        )

    with col3:
        neutral_pct = sentiment_counts.get('neutral', 0) / total_comments * 100
        st.metric(
            "😐 Neutral",
            f"{sentiment_counts.get('neutral', 0):,}",
            f"{neutral_pct:.1f}%"
        )


# ============================================================================
# INSTAGRAM-SPECIFIC CHARTS
# ============================================================================

def create_content_type_chart(posts: List[Dict]) -> None:
    """
    Create content type distribution chart for Instagram.

    Args:
        posts: List of Instagram posts
    """
    content_types = Counter(post.get('type', 'Unknown') for post in posts)

    if not content_types:
        st.info("No content type data available")
        return

    st.markdown("### 📱 Content Type Distribution")
    content_df = pd.DataFrame(
        list(content_types.items()),
        columns=['Type', 'Count']
    )

    if PLOTLY_AVAILABLE:
        fig = px.pie(
            content_df,
            values='Count',
            names='Type',
            title="Content Type Distribution",
            color_discrete_sequence=[
                THEME_COLORS['primary'],
                THEME_COLORS['secondary'],
                THEME_COLORS['tertiary']
            ]
        )
        fig.update_layout(
            plot_bgcolor=THEME_COLORS['background'],
            paper_bgcolor=THEME_COLORS['background'],
            font_color=THEME_COLORS['text']
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.bar_chart(content_df.set_index('Type'))


def create_hashtag_chart(posts: List[Dict], top_n: int = 10) -> None:
    """
    Create top hashtags chart for Instagram.

    Args:
        posts: List of Instagram posts
        top_n: Number of top hashtags to show
    """
    all_hashtags = []
    for post in posts:
        hashtags = post.get('hashtags', [])
        if isinstance(hashtags, list):
            all_hashtags.extend(hashtags)

    if not all_hashtags:
        st.info("No hashtag data available")
        return

    st.markdown("### #️⃣ Top Hashtags")
    top_hashtags = Counter(all_hashtags).most_common(top_n)
    hashtag_df = pd.DataFrame(top_hashtags, columns=['Hashtag', 'Count'])

    if PLOTLY_AVAILABLE:
        fig = px.bar(
            hashtag_df,
            x='Count',
            y='Hashtag',
            orientation='h',
            title=f"Top {top_n} Hashtags",
            color_discrete_sequence=[THEME_COLORS['primary']]
        )
        fig.update_layout(
            plot_bgcolor=THEME_COLORS['background'],
            paper_bgcolor=THEME_COLORS['background'],
            font_color=THEME_COLORS['text']
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.bar_chart(hashtag_df.set_index('Hashtag'))


def create_instagram_engagement_chart(posts: List[Dict]) -> None:
    """
    Create engagement breakdown chart for Instagram.

    Args:
        posts: List of Instagram posts
    """
    total_likes = sum(post.get('likes', 0) for post in posts)
    total_comments = sum(post.get('comments_count', 0) for post in posts)

    st.markdown("### 📊 Total Engagement Breakdown")

    engagement_data = pd.DataFrame({
        'Metric': ['Likes', 'Comments'],
        'Count': [total_likes, total_comments]
    })

    if PLOTLY_AVAILABLE:
        fig = px.bar(
            engagement_data,
            x='Metric',
            y='Count',
            title="Total Engagement Breakdown",
            color_discrete_sequence=[THEME_COLORS['primary'], THEME_COLORS['secondary']]
        )
        fig.update_layout(
            plot_bgcolor=THEME_COLORS['background'],
            paper_bgcolor=THEME_COLORS['background'],
            font_color=THEME_COLORS['text']
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.bar_chart(engagement_data.set_index('Metric'))


def create_top_posts_chart(posts: List[Dict], top_n: int = 5) -> None:
    """
    Create top posts by engagement chart.

    Args:
        posts: List of posts
        top_n: Number of top posts to show
    """
    st.markdown(f"### 🏆 Top {top_n} Posts by Engagement")

    # Calculate engagement for each post
    posts_with_engagement = []
    for post in posts:
        likes = post.get('likes', 0)
        comments = post.get('comments_count', 0)
        engagement = likes + comments

        # Safely handle text field (might be float/NaN)
        text = post.get('text', '')
        if not isinstance(text, str):
            text = str(text) if text is not None else ''
        text_preview = text[:100] + '...' if len(text) > 100 else text

        posts_with_engagement.append({
            'post_id': post.get('post_id', ''),
            'text': text_preview,
            'likes': likes,
            'comments': comments,
            'engagement': engagement,
            'type': post.get('type', 'Unknown')
        })

    # Sort and get top N
    top_posts = sorted(posts_with_engagement, key=lambda x: x['engagement'], reverse=True)[:top_n]

    if not top_posts:
        st.info("No posts data available")
        return

    top_posts_df = pd.DataFrame(top_posts)

    if PLOTLY_AVAILABLE:
        fig = px.bar(
            top_posts_df,
            x='engagement',
            y='text',
            orientation='h',
            title=f"Top {top_n} Posts by Engagement",
            color_discrete_sequence=[THEME_COLORS['primary']]
        )
        fig.update_layout(
            plot_bgcolor=THEME_COLORS['background'],
            paper_bgcolor=THEME_COLORS['background'],
            font_color=THEME_COLORS['text'],
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.bar_chart(top_posts_df.set_index('text')['engagement'])


# ============================================================================
# EMOJI ANALYSIS CHARTS
# ============================================================================

def create_emoji_chart(emoji_counts: Dict[str, int], top_n: int = 15) -> None:
    """
    Create emoji usage chart.

    Args:
        emoji_counts: Dictionary of emoji -> count
        top_n: Number of top emojis to show
    """
    if not emoji_counts:
        st.info("No emojis found in comments")
        return

    st.markdown("#### 😀 Emoji Analysis")

    # Get top emojis
    top_emojis = sorted(emoji_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]
    emoji_df = pd.DataFrame(top_emojis, columns=['Emoji', 'Count'])

    if PLOTLY_AVAILABLE:
        fig = px.bar(
            emoji_df,
            x='Count',
            y='Emoji',
            orientation='h',
            title=f"Most Used Emojis (Top {top_n})",
            color_discrete_sequence=[THEME_COLORS['primary']]
        )
        fig.update_layout(
            plot_bgcolor=THEME_COLORS['background'],
            paper_bgcolor=THEME_COLORS['background'],
            font_color=THEME_COLORS['text']
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.bar_chart(emoji_df.set_index('Emoji'))


# ============================================================================
# METRIC CARDS
# ============================================================================

def create_metric_card(
    title: str,
    value: str,
    emoji: str,
    gradient: str,
    help_text: Optional[str] = None
) -> None:
    """
    Create a styled metric card with gradient background.

    Args:
        title: Card title
        value: Metric value
        emoji: Emoji icon
        gradient: CSS gradient string
        help_text: Optional help text
    """
    st.markdown(
        f"""
        <div style="
            background: {gradient};
            padding: 1rem;
            border-radius: 10px;
            text-align: center;
            color: white;
            margin-bottom: 1rem;
        ">
            <h3 style="margin: 0; font-size: 2rem;">{emoji}</h3>
            <h2 style="margin: 0.5rem 0; font-size: 1.5rem;">{title}</h2>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.metric(title, value, help=help_text, label_visibility="collapsed")


def create_instagram_metric_cards(posts: List[Dict]) -> None:
    """
    Create Instagram-specific metric cards.

    Args:
        posts: List of Instagram posts
    """
    total_posts = len(posts)
    total_likes = sum(post.get('likes', 0) for post in posts)
    total_comments = sum(post.get('comments_count', 0) for post in posts)
    avg_engagement = (total_likes + total_comments) / total_posts if total_posts > 0 else 0

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        create_metric_card(
            "Total Posts",
            f"{total_posts:,}",
            "📸",
            GRADIENT_STYLES['purple'],
            "Total number of Instagram posts"
        )

    with col2:
        create_metric_card(
            "Total Likes",
            f"{total_likes:,}",
            "❤️",
            GRADIENT_STYLES['pink'],
            "Total likes across all posts"
        )

    with col3:
        create_metric_card(
            "Total Comments",
            f"{total_comments:,}",
            "💬",
            GRADIENT_STYLES['blue'],
            "Total comments across all posts"
        )

    with col4:
        create_metric_card(
            "Avg Engagement",
            f"{avg_engagement:.1f}",
            "📊",
            GRADIENT_STYLES['green'],
            "Average engagement per post (likes + comments)"
        )


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def format_number(num: int) -> str:
    """
    Format large numbers with K/M/B suffixes.

    Args:
        num: Number to format

    Returns:
        Formatted string
    """
    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.1f}B"
    elif num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.1f}K"
    else:
        return str(num)


def create_comparison_chart(data: Dict[str, float], title: str) -> None:
    """
    Create a comparison chart for multiple metrics.

    Args:
        data: Dictionary of metric name -> value
        title: Chart title
    """
    df = pd.DataFrame(list(data.items()), columns=['Metric', 'Value'])

    if PLOTLY_AVAILABLE:
        fig = px.bar(
            df,
            x='Metric',
            y='Value',
            title=title,
            color_discrete_sequence=[THEME_COLORS['primary']]
        )
        fig.update_layout(
            plot_bgcolor=THEME_COLORS['background'],
            paper_bgcolor=THEME_COLORS['background'],
            font_color=THEME_COLORS['text']
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.bar_chart(df.set_index('Metric'))
