"""
Analytics Engine for Social Media Data
======================================

Core analytics and metrics calculation functions.
Extracted from monolithic app for better organization.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from collections import Counter
import pandas as pd
import re


# ============================================================================
# EMOJI ANALYSIS
# ============================================================================

def analyze_emojis_in_comments(comments: List[str]) -> Dict[str, int]:
    """
    Analyze emojis in comments and return frequency count.

    Args:
        comments: List of comment texts

    Returns:
        Dictionary of emoji -> count (top 20)
    """
    # Emoji regex pattern
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "]+",
        flags=re.UNICODE
    )

    emoji_counts = Counter()

    for comment in comments:
        if comment:
            emojis = emoji_pattern.findall(comment)
            emoji_counts.update(emojis)

    return dict(emoji_counts.most_common(20))


# ============================================================================
# COMMENT AGGREGATION
# ============================================================================

def aggregate_all_comments(posts: List[Dict]) -> List[str]:
    """
    Aggregate all comments from posts into a single list.

    Args:
        posts: List of posts with comments

    Returns:
        List of comment texts
    """
    all_comments = []

    for post in posts:
        comments_list = post.get('comments_list', [])

        if isinstance(comments_list, list):
            for comment in comments_list:
                if isinstance(comment, dict):
                    text = comment.get('text', '')
                    if text and text.strip():
                        all_comments.append(text.strip())
                elif isinstance(comment, str) and comment.strip():
                    all_comments.append(comment.strip())

    return all_comments


def extract_comment_texts(comments_list: List[Any]) -> List[str]:
    """
    Extract text from various comment formats.

    Args:
        comments_list: List of comments (can be dicts or strings)

    Returns:
        List of comment texts
    """
    comment_texts = []

    for comment in comments_list:
        if isinstance(comment, dict):
            text = comment.get('text', '')
            if text and text.strip():
                comment_texts.append(text.strip())
        elif isinstance(comment, str) and comment.strip():
            comment_texts.append(comment.strip())

    return comment_texts


# ============================================================================
# ENGAGEMENT METRICS
# ============================================================================

def calculate_engagement_rate(post: Dict) -> float:
    """
    Calculate engagement rate for a post.

    Args:
        post: Post dictionary

    Returns:
        Engagement rate as percentage
    """
    likes = post.get('likes', 0)
    comments = post.get('comments_count', 0)
    shares = post.get('shares_count', 0)
    followers = post.get('followers', 0)

    total_engagement = likes + comments + shares

    if followers > 0:
        return (total_engagement / followers) * 100
    else:
        # Fallback: return raw engagement count
        return total_engagement


def calculate_total_engagement(posts: List[Dict]) -> Dict[str, int]:
    """
    Calculate total engagement metrics across all posts.

    Args:
        posts: List of posts

    Returns:
        Dictionary with total likes, comments, shares, and engagement
    """
    total_likes = sum(post.get('likes', 0) for post in posts)
    total_comments = sum(post.get('comments_count', 0) for post in posts)
    total_shares = sum(post.get('shares_count', 0) for post in posts)

    return {
        'total_likes': total_likes,
        'total_comments': total_comments,
        'total_shares': total_shares,
        'total_engagement': total_likes + total_comments + total_shares
    }


def calculate_average_engagement(posts: List[Dict]) -> Dict[str, float]:
    """
    Calculate average engagement metrics per post.

    Args:
        posts: List of posts

    Returns:
        Dictionary with average likes, comments, shares, and engagement
    """
    if not posts:
        return {
            'avg_likes': 0.0,
            'avg_comments': 0.0,
            'avg_shares': 0.0,
            'avg_engagement': 0.0
        }

    totals = calculate_total_engagement(posts)
    num_posts = len(posts)

    return {
        'avg_likes': totals['total_likes'] / num_posts,
        'avg_comments': totals['total_comments'] / num_posts,
        'avg_shares': totals['total_shares'] / num_posts,
        'avg_engagement': totals['total_engagement'] / num_posts
    }


def get_top_posts_by_metric(
    posts: List[Dict],
    metric: str = 'engagement',
    top_n: int = 5
) -> List[Dict]:
    """
    Get top N posts by specified metric.

    Args:
        posts: List of posts
        metric: Metric to sort by ('engagement', 'likes', 'comments', 'shares')
        top_n: Number of top posts to return

    Returns:
        List of top posts
    """
    posts_with_metrics = []

    for post in posts:
        likes = post.get('likes', 0)
        comments = post.get('comments_count', 0)
        shares = post.get('shares_count', 0)
        engagement = likes + comments + shares

        posts_with_metrics.append({
            **post,
            'total_engagement': engagement,
            'metric_value': {
                'engagement': engagement,
                'likes': likes,
                'comments': comments,
                'shares': shares
            }.get(metric, engagement)
        })

    # Sort by metric and return top N
    sorted_posts = sorted(
        posts_with_metrics,
        key=lambda x: x['metric_value'],
        reverse=True
    )

    return sorted_posts[:top_n]


# ============================================================================
# CONTENT ANALYSIS
# ============================================================================

def analyze_posting_frequency(posts: List[Dict]) -> Dict[str, Any]:
    """
    Analyze posting frequency patterns.

    Args:
        posts: List of posts

    Returns:
        Dictionary with posting frequency metrics
    """
    if not posts:
        return {
            'posts_per_day': {},
            'posts_per_week': {},
            'avg_posts_per_day': 0.0,
            'most_active_day': None
        }

    # Parse dates
    dates = []
    for post in posts:
        pub_date = post.get('published_at')
        if pub_date:
            if isinstance(pub_date, str):
                try:
                    dates.append(pd.to_datetime(pub_date).date())
                except:
                    pass
            elif isinstance(pub_date, datetime):
                dates.append(pub_date.date())

    if not dates:
        return {
            'posts_per_day': {},
            'posts_per_week': {},
            'avg_posts_per_day': 0.0,
            'most_active_day': None
        }

    # Count posts per day
    posts_per_day = Counter(dates)

    # Calculate average
    total_days = (max(dates) - min(dates)).days + 1
    avg_posts_per_day = len(dates) / total_days if total_days > 0 else 0

    # Find most active day
    most_active_day = max(posts_per_day.items(), key=lambda x: x[1])[0]

    return {
        'posts_per_day': dict(posts_per_day),
        'avg_posts_per_day': avg_posts_per_day,
        'most_active_day': most_active_day,
        'total_days': total_days,
        'date_range': (min(dates), max(dates))
    }


def analyze_content_types(posts: List[Dict]) -> Dict[str, int]:
    """
    Analyze distribution of content types (Instagram).

    Args:
        posts: List of posts

    Returns:
        Dictionary of content type -> count
    """
    content_types = Counter(post.get('type', 'Unknown') for post in posts)
    return dict(content_types)


def analyze_hashtags(posts: List[Dict], top_n: int = 20) -> List[Tuple[str, int]]:
    """
    Analyze hashtag usage across posts.

    Args:
        posts: List of posts
        top_n: Number of top hashtags to return

    Returns:
        List of (hashtag, count) tuples
    """
    all_hashtags = []

    for post in posts:
        hashtags = post.get('hashtags', [])
        if isinstance(hashtags, list):
            all_hashtags.extend(hashtags)

    hashtag_counts = Counter(all_hashtags)
    return hashtag_counts.most_common(top_n)


# ============================================================================
# VIDEO METRICS (Instagram/YouTube)
# ============================================================================

def calculate_video_metrics(posts: List[Dict]) -> Dict[str, Any]:
    """
    Calculate video-specific metrics.

    Args:
        posts: List of posts

    Returns:
        Dictionary with video metrics
    """
    video_posts = [p for p in posts if p.get('type') == 'Video']

    if not video_posts:
        return {
            'total_videos': 0,
            'total_video_views': 0,
            'avg_views_per_video': 0.0,
            'total_play_count': 0
        }

    total_views = sum(p.get('video_view_count', 0) for p in video_posts)
    total_play_count = sum(p.get('video_play_count', 0) for p in video_posts)

    return {
        'total_videos': len(video_posts),
        'total_video_views': total_views,
        'avg_views_per_video': total_views / len(video_posts),
        'total_play_count': total_play_count
    }


# ============================================================================
# REACTION ANALYSIS (Facebook)
# ============================================================================

def analyze_reactions(posts: List[Dict]) -> Dict[str, int]:
    """
    Analyze reaction breakdown across all posts.

    Args:
        posts: List of Facebook posts

    Returns:
        Dictionary of reaction type -> total count
    """
    total_reactions = {
        'like': 0,
        'love': 0,
        'haha': 0,
        'wow': 0,
        'sad': 0,
        'angry': 0
    }

    for post in posts:
        reactions = post.get('reactions', {})
        if isinstance(reactions, dict):
            for reaction_type, count in reactions.items():
                if reaction_type in total_reactions:
                    total_reactions[reaction_type] += count

    return total_reactions


def get_dominant_reaction(post: Dict) -> str:
    """
    Get the dominant reaction type for a post.

    Args:
        post: Post dictionary

    Returns:
        Dominant reaction type or 'none'
    """
    reactions = post.get('reactions', {})

    if not reactions or not isinstance(reactions, dict):
        return 'none'

    # Filter out zero values
    reactions_filtered = {k: v for k, v in reactions.items() if v > 0}

    if not reactions_filtered:
        return 'none'

    # Return reaction with max count
    return max(reactions_filtered.items(), key=lambda x: x[1])[0]


# ============================================================================
# TIME-BASED ANALYSIS
# ============================================================================

def group_posts_by_date(posts: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Group posts by publication date.

    Args:
        posts: List of posts

    Returns:
        Dictionary of date -> list of posts
    """
    grouped = {}

    for post in posts:
        pub_date = post.get('published_at')
        if pub_date:
            if isinstance(pub_date, str):
                try:
                    date = pd.to_datetime(pub_date).date()
                except:
                    continue
            elif isinstance(pub_date, datetime):
                date = pub_date.date()
            else:
                continue

            date_str = str(date)
            if date_str not in grouped:
                grouped[date_str] = []
            grouped[date_str].append(post)

    return grouped


def calculate_engagement_trend(posts: List[Dict]) -> List[Dict[str, Any]]:
    """
    Calculate engagement trend over time.

    Args:
        posts: List of posts

    Returns:
        List of dictionaries with date and engagement metrics
    """
    grouped = group_posts_by_date(posts)

    trend = []
    for date_str, date_posts in sorted(grouped.items()):
        metrics = calculate_total_engagement(date_posts)
        trend.append({
            'date': date_str,
            'posts': len(date_posts),
            **metrics
        })

    return trend


# ============================================================================
# PERFORMANCE BENCHMARKS
# ============================================================================

def calculate_performance_percentiles(posts: List[Dict]) -> Dict[str, Dict[str, float]]:
    """
    Calculate performance percentiles for engagement metrics.

    Args:
        posts: List of posts

    Returns:
        Dictionary with percentile values for each metric
    """
    if not posts:
        return {}

    df = pd.DataFrame(posts)

    metrics = {}
    for col in ['likes', 'comments_count', 'shares_count']:
        if col in df.columns:
            metrics[col] = {
                'p25': df[col].quantile(0.25),
                'p50': df[col].quantile(0.50),
                'p75': df[col].quantile(0.75),
                'p90': df[col].quantile(0.90),
                'max': df[col].max()
            }

    return metrics


def identify_viral_posts(
    posts: List[Dict],
    percentile: float = 0.9
) -> List[Dict]:
    """
    Identify viral posts (top percentile by engagement).

    Args:
        posts: List of posts
        percentile: Percentile threshold (0.9 = top 10%)

    Returns:
        List of viral posts
    """
    if not posts:
        return []

    # Calculate engagement for each post
    posts_with_engagement = []
    for post in posts:
        engagement = (
            post.get('likes', 0) +
            post.get('comments_count', 0) +
            post.get('shares_count', 0)
        )
        posts_with_engagement.append({
            **post,
            'total_engagement': engagement
        })

    # Calculate threshold
    engagements = [p['total_engagement'] for p in posts_with_engagement]
    threshold = pd.Series(engagements).quantile(percentile)

    # Filter viral posts
    viral_posts = [
        p for p in posts_with_engagement
        if p['total_engagement'] >= threshold
    ]

    return sorted(viral_posts, key=lambda x: x['total_engagement'], reverse=True)
