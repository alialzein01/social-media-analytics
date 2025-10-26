"""Analytics Engine - __init__.py"""

from .metrics import (
    # Emoji analysis
    analyze_emojis_in_comments,

    # Comment aggregation
    aggregate_all_comments,
    extract_comment_texts,

    # Engagement metrics
    calculate_engagement_rate,
    calculate_total_engagement,
    calculate_average_engagement,
    get_top_posts_by_metric,

    # Content analysis
    analyze_posting_frequency,
    analyze_content_types,
    analyze_hashtags,

    # Video metrics
    calculate_video_metrics,

    # Reaction analysis
    analyze_reactions,
    get_dominant_reaction,

    # Time-based analysis
    group_posts_by_date,
    calculate_engagement_trend,

    # Performance benchmarks
    calculate_performance_percentiles,
    identify_viral_posts
)

__all__ = [
    'analyze_emojis_in_comments',
    'aggregate_all_comments',
    'extract_comment_texts',
    'calculate_engagement_rate',
    'calculate_total_engagement',
    'calculate_average_engagement',
    'get_top_posts_by_metric',
    'analyze_posting_frequency',
    'analyze_content_types',
    'analyze_hashtags',
    'calculate_video_metrics',
    'analyze_reactions',
    'get_dominant_reaction',
    'group_posts_by_date',
    'calculate_engagement_trend',
    'calculate_performance_percentiles',
    'identify_viral_posts'
]
