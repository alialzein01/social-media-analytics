"""
Main Content View
=================

Renders the main content area including data input, analysis results,
and all visualization sections.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, List, Optional
from .state import UIState


def render_main_content(config: Dict[str, Any], apify_token: str):
    """
    Render the main content area based on configuration.

    Args:
        config: Configuration from sidebar
        apify_token: Apify API token
    """
    platform = config['platform']

    # =========================================================================
    # DATA INPUT SECTION (Always API mode)
    # =========================================================================
    url, analyze_button = _render_data_input_section(platform)
    config['url'] = url
    config['analyze_button'] = analyze_button

    # =========================================================================
    # ANALYSIS RESULTS SECTION
    # =========================================================================
    if UIState.has_data():
        _render_analysis_results(config)


def _render_data_input_section(platform: str) -> tuple[str, bool]:
    """
    Render data input section for API fetch mode.

    Args:
        platform: Selected platform name

    Returns:
        Tuple of (url, analyze_button)
    """
    st.header(f"{platform} Analysis")

    col1, col2 = st.columns([3, 1])

    with col1:
        url = st.text_input(
            f"Enter {platform} URL:",
            placeholder=f"https://www.{platform.lower()}.com/...",
            help=f"Paste the URL of the {platform} page/profile/channel"
        )

    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        analyze_button = st.button("🔍 Analyze", type="primary", use_container_width=True)

    return url, analyze_button


def _render_table_of_contents():
    """Render table of contents for expandable sections."""
    toc_items = [
        "📈 Monthly Overview",
        "💡 Monthly Insights",
        "📊 Analytics",
        "📝 Posts Details"
    ]

    with st.container():
        st.markdown("**Sections:**")
        cols = st.columns(len(toc_items))
        for col, item in zip(cols, toc_items):
            with col:
                st.markdown(f"- {item}")


def _render_analysis_results(config: Dict[str, Any]):
    """
    Render analysis results in 2-tab layout for Facebook.

    Args:
        config: Configuration from sidebar
    """
    normalized_data = UIState.get_normalized_data()
    platform = config['platform']

    if not normalized_data:
        st.info("No data to display. Please fetch data or load from file.")
        return

    # Convert to DataFrame
    df = pd.DataFrame(normalized_data)

    # =========================================================================
    # DATA SUMMARY (Always show)
    # =========================================================================
    _render_data_summary(df, platform)

    st.markdown("---")

    # =========================================================================
    # TWO-TAB LAYOUT FOR FACEBOOK
    # =========================================================================
    if platform == "Facebook":
        tab1, tab2 = st.tabs(["📊 Monthly Analysis", "📝 Individual Posts"])
        
        with tab1:
            _render_monthly_analysis_tab(normalized_data, df, config)
        
        with tab2:
            _render_individual_posts_tab(normalized_data, config)
    else:
        # For other platforms, keep existing layout
        _render_monthly_overview(df, platform)
        _render_monthly_insights(normalized_data, platform)
        _render_analytics_dashboard(df, normalized_data, platform, config)
        _render_post_details(normalized_data, platform)

    # =========================================================================
    # EXPORT SECTION
    # =========================================================================
    st.markdown("---")
    _render_export_section(normalized_data, platform)


def _render_data_summary(df: pd.DataFrame, platform: str):
    """Render data summary section."""
    st.markdown("---")
    st.subheader("📊 Data Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Posts", len(df))

    with col2:
        total_engagement = df['likes'].sum() + df.get('comments_count', pd.Series([0])).sum()
        st.metric("Total Engagement", f"{total_engagement:,}")

    with col3:
        avg_likes = df['likes'].mean()
        st.metric("Avg Likes", f"{avg_likes:.1f}")

    with col4:
        if 'views' in df.columns and platform == "YouTube":
            total_views = df['views'].sum()
            st.metric("Total Views", f"{total_views:,}")
        else:
            avg_comments = df.get('comments_count', pd.Series([0])).mean()
            st.metric("Avg Comments", f"{avg_comments:.1f}")


def _render_monthly_overview(df: pd.DataFrame, platform: str):
    """Render monthly overview section."""
    from app.viz.charts import create_monthly_overview_charts

    with st.expander("📈 Monthly Overview", expanded=True):
        create_monthly_overview_charts(df)


def _render_monthly_insights(posts: List[Dict], platform: str):
    """Render monthly insights section."""
    with st.expander("💡 Monthly Insights", expanded=False):
        _create_monthly_insights(posts, platform)


def _render_analytics_dashboard(df: pd.DataFrame, posts: List[Dict], platform: str, config: Dict[str, Any]):
    """Render analytics dashboard section."""
    from app.viz.dashboards import create_kpi_dashboard
    from app.analytics import aggregate_all_comments, analyze_emojis_in_comments, analyze_hashtags

    with st.expander("📊 Analytics Dashboard", expanded=False):
        # KPI Dashboard
        create_kpi_dashboard(posts, platform)

        st.markdown("---")

        # Comments Analysis
        all_comments = aggregate_all_comments(posts)

        if all_comments:
            st.subheader("💬 Comments Analysis")

            # Word Cloud
            _render_wordcloud(all_comments, config)

            # Emoji Analysis
            emoji_counts = analyze_emojis_in_comments(all_comments)
            if emoji_counts:
                from app.viz.charts import create_emoji_chart
                create_emoji_chart(emoji_counts)

        # Hashtag Analysis
        if platform in ["Instagram", "Facebook"]:
            hashtag_counts = analyze_hashtags(posts)
            if hashtag_counts:
                from app.viz.charts import create_hashtag_chart
                create_hashtag_chart(hashtag_counts)


def _render_post_details(posts: List[Dict], platform: str):
    """Render post details section."""
    from app.viz.post_details import create_enhanced_post_selector, create_post_performance_analytics

    with st.expander("📝 Post Details", expanded=False):
        selected_post = create_enhanced_post_selector(posts, platform)

        if selected_post:
            create_post_performance_analytics(selected_post, posts, platform)


def _render_export_section(posts: List[Dict], platform: str):
    """Render data export section."""
    from app.utils.export import create_comprehensive_export_section

    st.markdown("---")
    st.subheader("💾 Export Data")
    create_comprehensive_export_section(posts, platform)


def _render_wordcloud(comments: List[str], config: Dict[str, Any]):
    """Render word cloud based on configuration."""
    use_phrase_analysis = config.get('use_phrase_analysis', True)
    use_sentiment_coloring = config.get('use_sentiment_coloring', True)
    use_simple_wordcloud = config.get('use_simple_wordcloud', False)

    if use_simple_wordcloud:
        # Use simple word cloud
        from app.viz.wordcloud_generator import create_simple_wordcloud
        st.subheader("☁️ Word Cloud (Simple)")
        create_simple_wordcloud(comments)
    elif use_phrase_analysis:
        # Use phrase-based word cloud
        from app.viz.wordcloud_generator import create_phrase_wordcloud
        st.subheader("☁️ Phrase Cloud")
        create_phrase_wordcloud(
            comments,
            use_sentiment_coloring=use_sentiment_coloring
        )
    else:
        # Default word cloud
        from app.viz.wordcloud_generator import create_simple_wordcloud
        st.subheader("☁️ Word Cloud")
        create_simple_wordcloud(comments)


def _create_monthly_insights(posts: List[Dict], platform: str):
    """
    Create monthly insights section.

    This is a placeholder - the actual implementation should use
    the insights modules from app.viz.dashboards
    """
    from app.viz.dashboards import create_insights_summary

    create_insights_summary(posts, platform)


def _render_monthly_analysis_tab(posts: List[Dict], df: pd.DataFrame, config: Dict[str, Any]):
    """
    Render Tab 1: Monthly Analysis with reactions, comments, shares, and word cloud.

    Args:
        posts: List of normalized posts
        df: Posts as DataFrame
        config: Configuration dictionary
    """
    from app.analytics import aggregate_all_comments
    from app.viz.wordcloud_generator import create_phrase_wordcloud
    
    st.markdown("## 📊 Monthly Analysis")
    st.markdown("Overview of all posts and engagement for the selected period")
    
    # =========================================================================
    # REACTION DISTRIBUTION
    # =========================================================================
    st.markdown("### 🎭 Reaction Distribution")
    _render_reaction_distribution(posts)
    
    st.markdown("---")
    
    # =========================================================================
    # ENGAGEMENT METRICS
    # =========================================================================
    st.markdown("### 💬 Engagement Metrics")
    col1, col2, col3 = st.columns(3)
    
    total_comments = df['comments_count'].sum()
    total_shares = df['shares_count'].sum()
    total_reactions = sum(
        sum(post.get('reactions', {}).values()) if isinstance(post.get('reactions'), dict) else 0
        for post in posts
    )
    
    with col1:
        st.metric("Total Comments", f"{int(total_comments):,}")
    
    with col2:
        st.metric("Total Shares", f"{int(total_shares):,}")
    
    with col3:
        st.metric("Total Reactions", f"{int(total_reactions):,}")
    
    st.markdown("---")
    
    # =========================================================================
    # WORD CLOUD FROM ALL COMMENTS
    # =========================================================================
    st.markdown("### ☁️ Comments Word Cloud")
    st.markdown("Word cloud generated from all comments across all posts")
    
    all_comments = aggregate_all_comments(posts)
    
    if all_comments and len(all_comments) > 0:
        create_phrase_wordcloud(
            all_comments,
            use_sentiment_coloring=config.get('use_sentiment_coloring', True)
        )
    else:
        st.info("No comments available to generate word cloud. Comments may not have been fetched yet.")


def _render_individual_posts_tab(posts: List[Dict], config: Dict[str, Any]):
    """
    Render Tab 2: Individual Posts sorted by engagement with detailed analysis.

    Args:
        posts: List of normalized posts
        config: Configuration dictionary
    """
    from app.analytics import aggregate_all_comments
    from app.viz.wordcloud_generator import create_phrase_wordcloud
    
    st.markdown("## 📝 Individual Posts Analysis")
    st.markdown("Posts sorted by engagement (highest to lowest)")
    
    # =========================================================================
    # SORT POSTS BY ENGAGEMENT
    # =========================================================================
    posts_with_engagement = []
    for post in posts:
        reactions = sum(post.get('reactions', {}).values()) if isinstance(post.get('reactions'), dict) else 0
        comments = post.get('comments_count', 0)
        shares = post.get('shares_count', 0)
        total_engagement = reactions + comments + shares
        
        posts_with_engagement.append({
            **post,
            'total_engagement': total_engagement,
            'total_reactions': reactions
        })
    
    # Sort by engagement
    sorted_posts = sorted(posts_with_engagement, key=lambda x: x['total_engagement'], reverse=True)
    
    if not sorted_posts:
        st.warning("No posts available")
        return
    
    # =========================================================================
    # POST SELECTION
    # =========================================================================
    st.markdown("### 📋 Select a Post")
    
    # Create post selector with engagement info
    post_options = []
    for i, post in enumerate(sorted_posts):
        text = post.get('text', 'No text')[:60]
        if len(post.get('text', '')) > 60:
            text += "..."
        engagement = post['total_engagement']
        post_options.append(f"#{i+1} - {text} (👥 {engagement:,})")
    
    selected_index = st.selectbox(
        "Choose a post to analyze:",
        range(len(post_options)),
        format_func=lambda x: post_options[x]
    )
    
    selected_post = sorted_posts[selected_index]
    
    st.markdown("---")
    
    # =========================================================================
    # POST DETAILS
    # =========================================================================
    st.markdown("### 📄 Post Details")
    
    # Post text
    st.markdown("**Post Text:**")
    st.info(selected_post.get('text', 'No text available'))
    
    # Post metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Reactions", f"{int(selected_post['total_reactions']):,}")
    
    with col2:
        st.metric("Comments", f"{int(selected_post.get('comments_count', 0)):,}")
    
    with col3:
        st.metric("Shares", f"{int(selected_post.get('shares_count', 0)):,}")
    
    with col4:
        st.metric("Total Engagement", f"{int(selected_post['total_engagement']):,}")
    
    st.markdown("---")
    
    # =========================================================================
    # REACTION BREAKDOWN FOR THIS POST
    # =========================================================================
    st.markdown("### 🎭 Reaction Breakdown")
    reactions = selected_post.get('reactions', {})
    
    if reactions and isinstance(reactions, dict):
        reaction_df = pd.DataFrame([
            {'Reaction': reaction.capitalize(), 'Count': count}
            for reaction, count in reactions.items()
            if count > 0
        ])
        
        if not reaction_df.empty:
            # Display as columns
            reaction_cols = st.columns(len(reaction_df))
            for idx, (col, row) in enumerate(zip(reaction_cols, reaction_df.itertuples())):
                with col:
                    st.metric(f"{row.Reaction}", f"{row.Count:,}")
        else:
            st.info("No reactions for this post")
    else:
        st.info("No reaction data available")
    
    st.markdown("---")
    
    # =========================================================================
    # COMMENTS FOR THIS POST
    # =========================================================================
    st.markdown("### 💬 Comments")
    
    comments_list = selected_post.get('comments_list', [])
    
    # Handle case where comments_list might be an int (count) instead of a list
    if isinstance(comments_list, int):
        st.info(f"This post has {comments_list} comments, but comment text was not fetched.")
    elif isinstance(comments_list, list) and len(comments_list) > 0:
        st.markdown(f"**{len(comments_list)} comments**")
        
        # Extract comment texts
        comment_texts = []
        for comment in comments_list:
            if isinstance(comment, dict):
                text = comment.get('text', '')
                if text and text.strip():
                    comment_texts.append(text.strip())
            elif isinstance(comment, str) and comment.strip():
                comment_texts.append(comment.strip())
        
        # Show comments in expander
        with st.expander("View Comments", expanded=False):
            for i, comment_text in enumerate(comment_texts[:20], 1):  # Show first 20
                st.markdown(f"{i}. {comment_text}")
            
            if len(comment_texts) > 20:
                st.info(f"Showing 20 of {len(comment_texts)} comments")
        
        # Word cloud for this post's comments
        st.markdown("#### ☁️ Comments Word Cloud")
        if comment_texts:
            create_phrase_wordcloud(
                comment_texts,
                use_sentiment_coloring=config.get('use_sentiment_coloring', True)
            )
        else:
            st.info("No comment text available for word cloud")
    else:
        st.info("No comments available for this post")


def _render_reaction_distribution(posts: List[Dict]):
    """
    Render reaction distribution chart for Facebook posts.

    Args:
        posts: List of normalized posts with reactions
    """
    # Aggregate all reactions
    total_reactions = {}
    
    for post in posts:
        reactions = post.get('reactions', {})
        if isinstance(reactions, dict):
            for reaction_type, count in reactions.items():
                if isinstance(count, (int, float)) and count > 0:
                    total_reactions[reaction_type] = total_reactions.get(reaction_type, 0) + count
    
    if not total_reactions:
        st.info("No reaction data available")
        return
    
    # Create DataFrame
    reaction_df = pd.DataFrame([
        {'Reaction': reaction.capitalize(), 'Count': count}
        for reaction, count in total_reactions.items()
    ]).sort_values('Count', ascending=False)
    
    # Try using Plotly if available
    try:
        import plotly.express as px
        
        fig = px.pie(
            reaction_df,
            values='Count',
            names='Reaction',
            title='Reaction Distribution',
            hole=0.3
        )
        
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
    except ImportError:
        # Fallback to bar chart
        st.bar_chart(reaction_df.set_index('Reaction'))
