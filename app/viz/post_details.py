"""
Enhanced Post Detail Analysis Components
=========================================

Rich, interactive post-level analytics with performance metrics,
comment analysis, and audience insights.
"""

from typing import Dict, List, Optional, Any
import streamlit as st
import pandas as pd
from datetime import datetime

# Optional Plotly for interactive charts
try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False


# ============================================================================
# ENHANCED POST SELECTOR
# ============================================================================

def create_enhanced_post_selector(posts: List[Dict], platform: str) -> Optional[Dict]:
    """
    Create rich post selector with thumbnails, previews, and engagement scores.

    Args:
        posts: List of posts
        platform: Platform name

    Returns:
        Selected post dictionary or None
    """
    st.markdown("## 🎯 Post Detail Analysis")

    if not posts:
        st.warning("No posts available for analysis")
        return None

    # Calculate engagement scores for sorting
    posts_with_scores = []
    for i, post in enumerate(posts):
        engagement = post.get('likes', 0) + post.get('comments_count', 0) + post.get('shares_count', 0)
        if platform == "YouTube":
            engagement += post.get('views', 0) * 0.01  # Weight views lower

        posts_with_scores.append({
            'index': i,
            'post': post,
            'engagement': engagement
        })

    # Sort by engagement (highest first)
    posts_with_scores.sort(key=lambda x: x['engagement'], reverse=True)

    # Create selection options
    st.markdown("### 📋 Select a Post")

    # Filter options
    col1, col2, col3 = st.columns(3)

    with col1:
        sort_order = st.radio(
            "Sort by:",
            ["Most Engaging", "Most Recent", "Least Engaging"],
            help="Order posts by engagement or recency"
        )

    with col2:
        if platform == "Instagram":
            content_filter = st.selectbox(
                "Content Type:",
                ["All", "Photo", "Video", "Carousel"],
                help="Filter by content type"
            )
        else:
            content_filter = "All"

    with col3:
        min_engagement = st.slider(
            "Min Engagement:",
            min_value=0,
            max_value=int(max(p['engagement'] for p in posts_with_scores)),
            value=0,
            help="Filter posts by minimum engagement"
        )

    # Apply filters and sorting
    filtered_posts = []
    for item in posts_with_scores:
        post = item['post']

        # Engagement filter
        if item['engagement'] < min_engagement:
            continue

        # Content type filter (Instagram)
        if platform == "Instagram" and content_filter != "All":
            post_type = post.get('type', '').lower()
            if content_filter.lower() not in post_type:
                continue

        filtered_posts.append(item)

    # Apply sorting
    if sort_order == "Most Recent":
        filtered_posts.sort(
            key=lambda x: x['post'].get('published_at', datetime.min),
            reverse=True
        )
    elif sort_order == "Least Engaging":
        filtered_posts.sort(key=lambda x: x['engagement'])

    if not filtered_posts:
        st.warning("No posts match the current filters")
        return None

    st.info(f"Showing {len(filtered_posts)} of {len(posts)} posts")

    # Display post cards for selection
    st.markdown("---")

    # Use session state to track selection
    if 'selected_post_id' not in st.session_state:
        st.session_state.selected_post_id = None

    # Create post preview cards
    for rank, item in enumerate(filtered_posts[:10], 1):  # Show top 10
        post = item['post']
        idx = item['index']
        engagement = item['engagement']

        # Create card
        with st.container():
            col1, col2, col3, col4 = st.columns([1, 3, 2, 1])

            with col1:
                # Rank badge
                rank_color = "#FFD700" if rank == 1 else "#C0C0C0" if rank == 2 else "#CD7F32" if rank == 3 else "#45474B"
                st.markdown(
                    f"""
                    <div style="
                        background: {rank_color};
                        color: white;
                        padding: 0.5rem;
                        border-radius: 50%;
                        width: 50px;
                        height: 50px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 1.5rem;
                        font-weight: bold;
                        margin: auto;
                    ">#{rank}</div>
                    """,
                    unsafe_allow_html=True
                )

            with col2:
                # Post text preview
                text = post.get('text', 'No text')
                if isinstance(text, (int, float)):
                    text = str(text)
                text_preview = (text[:80] + "...") if len(str(text)) > 80 else text
                st.markdown(f"**{text_preview}**")

                # Publish date
                pub_date = post.get('published_at')
                if pub_date:
                    if hasattr(pub_date, 'strftime'):
                        date_str = pub_date.strftime('%Y-%m-%d %H:%M')
                    else:
                        date_str = str(pub_date)
                    st.caption(f"📅 {date_str}")

            with col3:
                # Engagement metrics
                likes = post.get('likes', 0)
                comments = post.get('comments_count', 0)
                shares = post.get('shares_count', 0)

                metric_text = f"❤️ {likes:,} | 💬 {comments:,}"
                if platform != "Instagram":
                    metric_text += f" | 🔄 {shares:,}"
                if platform == "YouTube":
                    views = post.get('views', 0)
                    metric_text += f" | 👁️ {views:,}"

                st.caption(metric_text)
                st.caption(f"⚡ Engagement: {engagement:,.0f}")

            with col4:
                # Select button
                if st.button("View", key=f"select_post_{idx}"):
                    st.session_state.selected_post_id = idx
                    st.rerun()

        st.markdown("---")

    # Show selected post
    if st.session_state.selected_post_id is not None:
        selected_idx = st.session_state.selected_post_id
        if 0 <= selected_idx < len(posts):
            return posts[selected_idx]

    return None


# ============================================================================
# POST PERFORMANCE ANALYTICS
# ============================================================================

def create_post_performance_analytics(
    post: Dict,
    all_posts: List[Dict],
    platform: str
) -> None:
    """
    Create detailed performance analytics for a post.

    Args:
        post: Selected post
        all_posts: All posts for comparison
        platform: Platform name
    """
    st.markdown("### 📊 Performance Analytics")

    # Calculate post metrics
    post_engagement = post.get('likes', 0) + post.get('comments_count', 0) + post.get('shares_count', 0)

    # Calculate averages across all posts
    avg_likes = sum(p.get('likes', 0) for p in all_posts) / len(all_posts) if all_posts else 0
    avg_comments = sum(p.get('comments_count', 0) for p in all_posts) / len(all_posts) if all_posts else 0
    avg_shares = sum(p.get('shares_count', 0) for p in all_posts) / len(all_posts) if all_posts else 0
    avg_engagement = (avg_likes + avg_comments + avg_shares)

    # Performance metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        likes = post.get('likes', 0)
        likes_delta = ((likes - avg_likes) / avg_likes * 100) if avg_likes > 0 else 0
        st.metric(
            "Likes",
            f"{likes:,}",
            delta=f"{likes_delta:+.1f}% vs avg",
            delta_color="normal"
        )

    with col2:
        comments = post.get('comments_count', 0)
        comments_delta = ((comments - avg_comments) / avg_comments * 100) if avg_comments > 0 else 0
        st.metric(
            "Comments",
            f"{comments:,}",
            delta=f"{comments_delta:+.1f}% vs avg",
            delta_color="normal"
        )

    with col3:
        shares = post.get('shares_count', 0)
        shares_delta = ((shares - avg_shares) / avg_shares * 100) if avg_shares > 0 else 0
        st.metric(
            "Shares" if platform != "Instagram" else "Engagement Rate",
            f"{shares:,}" if platform != "Instagram" else f"{(post_engagement / max(post.get('likes', 1), 1) * 100):.1f}%",
            delta=f"{shares_delta:+.1f}% vs avg" if platform != "Instagram" else "",
            delta_color="normal"
        )

    with col4:
        engagement_delta = ((post_engagement - avg_engagement) / avg_engagement * 100) if avg_engagement > 0 else 0
        st.metric(
            "Total Engagement",
            f"{post_engagement:,}",
            delta=f"{engagement_delta:+.1f}% vs avg",
            delta_color="normal"
        )

    # YouTube-specific metrics
    if platform == "YouTube":
        st.markdown("---")
        st.markdown("#### 📺 YouTube Video Metrics")

        col1, col2, col3, col4 = st.columns(4)

        avg_views = sum(p.get('views', 0) for p in all_posts) / len(all_posts) if all_posts else 0

        with col1:
            views = post.get('views', 0)
            views_delta = ((views - avg_views) / avg_views * 100) if avg_views > 0 else 0
            st.metric(
                "Views",
                f"{views:,}",
                delta=f"{views_delta:+.1f}% vs avg"
            )

        with col2:
            engagement_rate = (post_engagement / views * 100) if views > 0 else 0
            avg_eng_rate = (avg_engagement / avg_views * 100) if avg_views > 0 else 0
            eng_rate_delta = engagement_rate - avg_eng_rate
            st.metric(
                "Engagement Rate",
                f"{engagement_rate:.2f}%",
                delta=f"{eng_rate_delta:+.2f}%"
            )

        with col3:
            if post.get('duration'):
                st.metric("Duration", post['duration'])

        with col4:
            if post.get('subscriber_count'):
                st.metric("Subscribers", f"{post['subscriber_count']:,}")

    # Performance ranking
    st.markdown("---")
    st.markdown("#### 🏆 Performance Ranking")

    # Rank this post
    engagements = [(i, p.get('likes', 0) + p.get('comments_count', 0) + p.get('shares_count', 0))
                   for i, p in enumerate(all_posts)]
    engagements.sort(key=lambda x: x[1], reverse=True)

    post_rank = next((i + 1 for i, (idx, _) in enumerate(engagements)
                     if all_posts[idx] == post), None)

    if post_rank:
        col1, col2, col3 = st.columns(3)

        with col1:
            rank_emoji = "🥇" if post_rank == 1 else "🥈" if post_rank == 2 else "🥉" if post_rank == 3 else "📊"
            st.metric("Rank", f"{rank_emoji} #{post_rank}/{len(all_posts)}")

        with col2:
            percentile = ((len(all_posts) - post_rank + 1) / len(all_posts) * 100)
            st.metric("Percentile", f"Top {100 - percentile:.0f}%")

        with col3:
            if post_rank <= 3:
                st.success("⭐ Top Performer!")
            elif post_rank <= len(all_posts) * 0.25:
                st.info("✨ High Performer")
            elif post_rank <= len(all_posts) * 0.5:
                st.info("📊 Average Performance")
            else:
                st.warning("📉 Below Average")


# ============================================================================
# COMMENT ANALYTICS
# ============================================================================

def create_comment_analytics(post: Dict, platform: str) -> None:
    """
    Create detailed comment analysis for a post.

    Args:
        post: Post with comments
        platform: Platform name
    """
    st.markdown("### 💬 Comment Analytics")

    comments_list = post.get('comments_list', [])

    if not comments_list or (isinstance(comments_list, int)):
        st.info("💡 No detailed comments available. Enable 'Fetch Detailed Comments' to analyze comment text.")
        return

    # Extract comment texts
    comment_texts = []
    comment_data = []

    for comment in comments_list:
        if isinstance(comment, dict):
            text = comment.get('text', '')
            if text and text.strip():
                comment_texts.append(text.strip())
                comment_data.append({
                    'text': text,
                    'author': comment.get('ownerUsername', comment.get('author', 'Unknown')),
                    'timestamp': comment.get('timestamp', ''),
                    'likes': comment.get('likesCount', comment.get('voteCount', 0))
                })
        elif isinstance(comment, str) and comment.strip():
            comment_texts.append(comment.strip())
            comment_data.append({
                'text': comment,
                'author': 'Unknown',
                'timestamp': '',
                'likes': 0
            })

    if not comment_texts:
        st.info("No comment text available for analysis")
        return

    # DEBUG: Show comment extraction
    st.write(f"🔍 DEBUG (Post Details): Extracted {len(comment_texts)} comment texts")
    if comment_texts:
        st.write(f"🔍 DEBUG: Sample comment text: {comment_texts[0][:100]}")

    # Comment metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Comments", f"{len(comment_texts):,}")

    with col2:
        unique_authors = len(set(c['author'] for c in comment_data if c['author'] != 'Unknown'))
        st.metric("Unique Authors", f"{unique_authors:,}")

    with col3:
        total_comment_likes = sum(c['likes'] for c in comment_data)
        st.metric("Comment Likes", f"{total_comment_likes:,}")

    with col4:
        avg_comment_length = sum(len(text) for text in comment_texts) / len(comment_texts)
        st.metric("Avg Length", f"{avg_comment_length:.0f} chars")

    # Word cloud and sentiment
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📊 Comment Word Cloud")
        # Import word cloud function from main app
        from social_media_app import create_wordcloud
        create_wordcloud(comment_texts, width=600, height=400, figsize=(10, 6))

    with col2:
        st.markdown("#### 😊 Sentiment Distribution")
        from social_media_app import analyze_all_sentiments
        from app.viz.charts import create_sentiment_pie_chart

        sentiment_counts = analyze_all_sentiments(comment_texts)
        create_sentiment_pie_chart(sentiment_counts)

        # Sentiment summary
        total = sum(sentiment_counts.values())
        if total > 0:
            st.markdown("**Summary:**")
            st.markdown(f"- Positive: {sentiment_counts['positive']:,} ({sentiment_counts['positive']/total*100:.1f}%)")
            st.markdown(f"- Negative: {sentiment_counts['negative']:,} ({sentiment_counts['negative']/total*100:.1f}%)")
            st.markdown(f"- Neutral: {sentiment_counts['neutral']:,} ({sentiment_counts['neutral']/total*100:.1f}%)")

    # Top commenters
    if comment_data and any(c['author'] != 'Unknown' for c in comment_data):
        st.markdown("---")
        st.markdown("#### 👥 Top Commenters")

        author_counts = {}
        for c in comment_data:
            author = c['author']
            if author != 'Unknown':
                author_counts[author] = author_counts.get(author, 0) + 1

        if author_counts:
            top_authors = sorted(author_counts.items(), key=lambda x: x[1], reverse=True)[:10]

            df = pd.DataFrame(top_authors, columns=['Author', 'Comments'])

            if PLOTLY_AVAILABLE:
                fig = px.bar(
                    df,
                    x='Comments',
                    y='Author',
                    orientation='h',
                    title="Most Active Commenters",
                    color_discrete_sequence=['#495E57']
                )
                fig.update_layout(
                    plot_bgcolor='#F5F7F8',
                    paper_bgcolor='#F5F7F8',
                    font_color='#45474B',
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.bar_chart(df.set_index('Author'))

    # Emoji analysis (create_emoji_chart adds its own title)
    st.markdown("---")

    from app.analytics import analyze_emojis_in_comments
    from app.viz.charts import create_emoji_chart

    emoji_analysis = analyze_emojis_in_comments(comment_texts)
    if emoji_analysis:
        create_emoji_chart(emoji_analysis, top_n=15)
    else:
        st.info("No emojis found in comments")
