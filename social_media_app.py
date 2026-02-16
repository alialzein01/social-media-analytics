"""
Social Media Analytics Dashboard
=================================

How to run:
1. Set your Apify API token:
    export APIFY_TOKEN=your_token_here

2. Install dependencies:
    pip install -r requirements.txt

3. Run the app:
    streamlit run social_media_app.py

This app connects to Apify actors to analyze social media posts from Facebook,
Instagram, and YouTube for the current month.

Dashboard Improvement Report (insight + UI quality):
- Dashboard Audit Summary:
  - Removed: duplicated "Analytics" section and duplicated monthly sentiment/word-cloud views.
  - Replaced: section flow with Overview -> Trends -> Drivers -> Breakdown -> Details.
  - Kept: core metric definitions and core charts that answer clear business questions.
  - Reasoning: increase insight density, reduce clutter, and improve executive scanability.
- Implementation focus:
  - KPI structure tightened to high-signal metrics with prior-window deltas where baseline exists.
  - Layout standardized (global filters -> KPI row -> primary trends -> breakdown -> tables/details).
  - Visual noise reduced by trimming repeated captions/charts and overuse of expanders.
"""

import os
import re
import json
import glob
import time
import hashlib
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import streamlit as st
import pandas as pd
from apify_client import ApifyClient

from app.services.apify_client import (
    create_apify_client,
    run_actor_and_fetch_dataset,
    ApifyClientError,
)
from wordcloud import WordCloud  # type: ignore
import matplotlib.pyplot as plt  # type: ignore
from collections import Counter
import functools

# Optional Plotly for interactive charts
try:
    import plotly.express as px  # type: ignore

    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# ============================================================================
# IMPORT NEW MODULAR COMPONENTS
# ============================================================================

# Config: single source of truth (no duplicate actor/config in this file)
from app.config.settings import (
    DEFAULT_MAX_POSTS,
    DEFAULT_MAX_COMMENTS,
    DEFAULT_TIMEOUT,
    ACTOR_CONFIG,
    YOUTUBE_COMMENTS_ACTOR_ID,
    FACEBOOK_COMMENTS_ACTOR_IDS,
    INSTAGRAM_COMMENTS_ACTOR_IDS,
    ARABIC_STOPWORDS,
    URL_PATTERN,
    MENTION_HASHTAG_PATTERN,
    TOKEN_RE,
    ARABIC_DIACRITICS,
    CACHE_TTL,
)
from app.config import URL_PATTERNS

# Platform adapters for data normalization
from app.adapters import parse_published_at
from app.adapters.facebook import FacebookAdapter
from app.adapters.instagram import InstagramAdapter
from app.adapters.youtube import YouTubeAdapter

# Data services for fetching and persistence
from app.services import DataFetchingService

# Advanced NLP and visualization components
from app.nlp.advanced_nlp import (
    analyze_corpus_advanced,
    extract_topics_from_texts,
    extract_keywords_tfidf,
    analyze_text_with_emoji_sentiment,
)
from app.viz.nlp_viz import (
    create_advanced_nlp_dashboard,
    create_topic_modeling_view,
    create_keyword_cloud,
    create_emoji_sentiment_chart,
    create_sentiment_comparison_view,
    create_sentiment_themes_view,
)
from app.services.persistence import DataPersistenceService

try:
    from app.services.mongodb_service import MongoDBService

    MONGODB_AVAILABLE = True
except Exception:
    MongoDBService = None
    MONGODB_AVAILABLE = False

# Visualization components
from app.viz.charts import (
    create_monthly_overview_charts,
    create_reaction_pie_chart,
    create_reaction_donut_with_summary,
    create_engagement_over_time_chart,
    create_sentiment_pie_chart,
    create_instagram_metric_cards,
    create_top_posts_chart,
    create_hashtag_chart,
    create_content_type_chart,
    create_emoji_chart,
)

# Dashboard components (single import block)
from app.viz.dashboards import (
    create_kpi_dashboard,
    create_trends_dashboard,
    create_cross_platform_comparison,
    create_engagement_trend_chart,
    create_posting_frequency_chart,
    create_performance_comparison,
    create_insights_summary,
)

# UI/UX Components
from app.styles.theme import get_custom_css, THEME_COLORS, SENTIMENT_COLORS
from app.ui import (
    page_header,
    kpi_cards,
    section,
    section_divider,
    empty_state,
    KPI_COLORS,
)
from app.styles.loading import (
    show_spinner,
    show_loading_dots,
    show_progress_bar,
    show_status_indicator,
    show_empty_state,
    show_processing_steps,
    loading_state,
    with_loading,
)
from app.styles.errors import (
    ErrorHandler,
    with_error_boundary,
    show_warning,
    show_info,
    show_success,
    validate_input,
)
from app.utils.export import create_comprehensive_export_section

# Post detail analysis components
from app.viz.post_details import (
    create_enhanced_post_selector,
    create_post_performance_analytics,
    create_comment_analytics,
)

# Analytics engine
from app.analytics import (
    aggregate_all_comments,
    analyze_emojis_in_comments,
    calculate_total_engagement,
    get_post_reactions_count,
    get_post_engagement,
    analyze_hashtags,
)
from app.types import normalize_posts_to_schema

# ============================================================================
# NLP UTILITIES (Arabic-capable, pluggable design)
# ============================================================================

# Optional Arabic text shaping support
try:
    import arabic_reshaper  # type: ignore
    from bidi.algorithm import get_display  # type: ignore

    def _reshape_for_wc(s: str) -> str:
        return get_display(arabic_reshaper.reshape(s))
except Exception:

    def _reshape_for_wc(s: str) -> str:
        return s


def clean_arabic_text(text: str) -> str:
    """Clean Arabic text by removing diacritics, extra spaces, and noise."""
    if not text:
        return ""

    # Use pre-compiled patterns for better performance
    text = ARABIC_DIACRITICS.sub("", text)
    text = URL_PATTERN.sub("", text)
    text = MENTION_HASHTAG_PATTERN.sub("", text)
    # Remove extra whitespace (optimized)
    text = " ".join(text.split())

    return text


def tokenize_arabic(text: str) -> List[str]:
    """Tokenize text and filter stopwords using improved Arabic regex."""
    text = clean_arabic_text(text)
    tokens = TOKEN_RE.findall(text)
    return [t for t in tokens if t.lower() not in ARABIC_STOPWORDS and len(t) > 2]


def extract_keywords_nlp(comments: List[str], top_n: int = 50) -> Dict[str, int]:
    """
    Extract keywords from comments using improved frequency analysis.
    Handles multiple languages and improves keyword extraction.
    """
    if not comments:
        return {}

    # Try to use phrase extraction if available
    try:
        from app.nlp.phrase_extractor import extract_phrases_simple

        phrases = extract_phrases_simple(comments, top_n)
        # If phrase extraction returns results, use them
        if phrases:
            return phrases
        # Otherwise fall back to word-based extraction
    except Exception as e:
        # Fallback to improved word-based extraction on any error
        pass

    # Improved fallback: Better text processing
    all_text = " ".join(comments)

    # Clean the text more thoroughly
    # Remove URLs, mentions, hashtags for better keyword extraction
    cleaned_text = re.sub(
        r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
        "",
        all_text,
    )
    cleaned_text = re.sub(r"@\w+", "", cleaned_text)  # Remove mentions
    cleaned_text = re.sub(r"#\w+", "", cleaned_text)  # Remove hashtags
    cleaned_text = re.sub(r"[^\w\s]", " ", cleaned_text)  # Remove special characters except spaces

    # Tokenize with improved regex
    tokens = re.findall(r"\b\w+\b", cleaned_text.lower())

    # Enhanced filtering
    # Common English stopwords
    english_stopwords = {
        "the",
        "a",
        "an",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "must",
        "can",
        "this",
        "that",
        "these",
        "those",
        "i",
        "you",
        "he",
        "she",
        "it",
        "we",
        "they",
        "me",
        "him",
        "her",
        "us",
        "them",
        "my",
        "your",
        "his",
        "her",
        "its",
        "our",
        "their",
    }

    # Combine Arabic and English stopwords
    all_stopwords = ARABIC_STOPWORDS.union(english_stopwords)

    # Filter tokens
    filtered_tokens = [
        t
        for t in tokens
        if len(t) > 2
        and t not in all_stopwords
        and not t.isdigit()
        and not t.startswith("www")
        and not t.startswith("http")
    ]

    # Count frequencies
    word_freq = Counter(filtered_tokens)

    # Return top N most frequent words
    return dict(word_freq.most_common(top_n))


def analyze_sentiment_placeholder(text: str) -> str:
    """
    Enhanced sentiment analysis with improved emoji and multi-language support.

    For production, use:
    - AraBERT for Arabic sentiment
    - Multilingual BERT fine-tuned on Arabic
    - CAMeL Tools + rule-based sentiment
    """
    if not text or not text.strip():
        return "neutral"

    # Try to use phrase-based sentiment analysis if available
    try:
        from app.nlp.sentiment_analyzer import analyze_sentiment_phrases

        return analyze_sentiment_phrases(text)
    except ImportError:
        # Enhanced fallback analysis
        text_lower = text.lower().strip()

        # Enhanced positive indicators
        positive_indicators = {
            # English words
            "good",
            "great",
            "excellent",
            "amazing",
            "wonderful",
            "fantastic",
            "awesome",
            "love",
            "like",
            "best",
            "perfect",
            "beautiful",
            "nice",
            "cool",
            "brilliant",
            "outstanding",
            "superb",
            "magnificent",
            "thank",
            "thanks",
            "appreciate",
            "wow",
            "incredible",
            "fabulous",
            "marvelous",
            "splendid",
            # Arabic positive words
            "جيد",
            "ممتاز",
            "رائع",
            "حلو",
            "جميل",
            "عظيم",
            "مذهل",
            "مثالي",
            "أفضل",
            "شكرا",
            "شكر",
            # Emojis
            "😊",
            "😄",
            "😃",
            "😁",
            "😍",
            "🥰",
            "😘",
            "❤️",
            "💕",
            "💖",
            "💗",
            "💝",
            "👍",
            "👏",
            "🎉",
            "✨",
            "🌟",
            "💫",
        }

        # Enhanced negative indicators
        negative_indicators = {
            # English words
            "bad",
            "terrible",
            "awful",
            "horrible",
            "hate",
            "dislike",
            "worst",
            "disgusting",
            "ugly",
            "stupid",
            "annoying",
            "boring",
            "disappointing",
            "frustrating",
            "angry",
            "sad",
            "depressed",
            "upset",
            "no",
            "not",
            "never",
            "hate",
            "disgusting",
            "awful",
            "terrible",
            "horrible",
            # Arabic negative words
            "سيء",
            "سئ",
            "فظيع",
            "مقرف",
            "كراهية",
            "أسوأ",
            "قبيح",
            "غبي",
            "ممل",
            "محبط",
            "لا",
            "ليس",
            # Emojis
            "😢",
            "😭",
            "😡",
            "😠",
            "😞",
            "😔",
            "😕",
            "👎",
            "💔",
            "😤",
            "🤬",
            "😒",
            "😑",
        }

        # Count indicators
        pos_count = sum(1 for indicator in positive_indicators if indicator in text_lower)
        neg_count = sum(1 for indicator in negative_indicators if indicator in text_lower)

        # Determine sentiment
        if pos_count > neg_count and pos_count > 0:
            return "positive"
        elif neg_count > pos_count and neg_count > 0:
            return "negative"
        else:
            return "neutral"


# ============================================================================
# DATA NORMALIZATION (Using New Adapters)
# ============================================================================


def _to_naive_dt(x):
    """Convert input to timezone-naive datetime, returning None on failure."""
    ts = pd.to_datetime(x, errors="coerce", utc=True)
    if pd.isna(ts):
        return None
    return ts.tz_convert(None)


def _get_posts_date_range_str(posts: List[Dict]) -> Optional[str]:
    """Return a string like '2024-01-05 to 2024-02-10' from posts' published_at, or None if no valid dates."""
    dates = []
    for p in posts:
        dt = _to_naive_dt(p.get("published_at"))
        if dt is not None:
            dates.append(dt)
    if not dates:
        return None
    min_d, max_d = min(dates), max(dates)
    return f"{min_d.strftime('%Y-%m-%d')} to {max_d.strftime('%Y-%m-%d')}"


def normalize_post_data(raw_data: List[Dict], platform: str, apify_token: str = None) -> List[Dict]:
    """
    Normalize actor response using new platform adapters.
    This is a wrapper that maintains backward compatibility.
    """
    if not apify_token:
        # Try Streamlit secrets first, then environment variable
        try:
            if hasattr(st, "secrets") and "APIFY_TOKEN" in st.secrets:
                apify_token = st.secrets["APIFY_TOKEN"]
            else:
                apify_token = os.getenv("APIFY_TOKEN")
        except Exception:
            apify_token = os.getenv("APIFY_TOKEN")

    # Select appropriate adapter
    if platform == "Facebook":
        adapter = FacebookAdapter(apify_token)
    elif platform == "Instagram":
        adapter = InstagramAdapter(apify_token)
    elif platform == "YouTube":
        adapter = YouTubeAdapter(apify_token)
    else:
        # Fallback to generic normalization
        st.warning(f"Unknown platform: {platform}, using generic normalization")
        return raw_data

    # Use adapter to normalize posts
    try:
        normalized = adapter.normalize_posts(raw_data)
        return normalized
    except Exception as e:
        st.error(f"Error normalizing {platform} data: {str(e)}")
        # Fallback to empty list
        return []


def filter_current_month(posts: List[Dict]) -> List[Dict]:
    """Filter posts to current month only, skipping posts with invalid dates."""
    if not posts:
        return []
    now = pd.Timestamp.now().normalize()
    month_start = now.replace(day=1)
    month_end = month_start + pd.offsets.MonthEnd(1)
    out = []
    for p in posts:
        d = p.get("published_at")
        d = pd.to_datetime(d, errors="coerce")
        if pd.isna(d):
            continue
        if month_start <= d <= month_end:
            out.append(p)
    return out


def calculate_total_reactions(posts: List[Dict]) -> int:
    """Total reactions across all posts. Uses reactions dict with fallback to likes per post."""
    return sum(get_post_reactions_count(p) for p in posts)


def calculate_average_engagement(posts: List[Dict], platform: Optional[str] = None) -> float:
    """Average engagement per post (reactions/likes + comments + shares). Platform-aware for Facebook (sum reactions)."""
    if not posts:
        return 0.0
    total = sum(get_post_engagement(p, platform) for p in posts)
    return total / len(posts)


def calculate_youtube_metrics(posts: List[Dict]) -> Dict[str, Any]:
    """Calculate YouTube-specific metrics."""
    if not posts:
        return {}

    total_views = sum(post.get("views", 0) for post in posts)
    total_likes = sum(post.get("likes", 0) for post in posts)
    total_comments = sum(post.get("comments_count", 0) for post in posts)
    total_shares = sum(post.get("shares_count", 0) for post in posts)

    # Calculate average metrics
    avg_views = total_views / len(posts) if posts else 0
    avg_likes = total_likes / len(posts) if posts else 0
    avg_comments = total_comments / len(posts) if posts else 0
    avg_shares = total_shares / len(posts) if posts else 0

    # Calculate engagement rate (likes + comments + shares) / views
    total_engagement = total_likes + total_comments + total_shares
    engagement_rate = (total_engagement / total_views * 100) if total_views > 0 else 0

    return {
        "total_views": total_views,
        "total_likes": total_likes,
        "total_comments": total_comments,
        "total_shares": total_shares,
        "avg_views": avg_views,
        "avg_likes": avg_likes,
        "avg_comments": avg_comments,
        "avg_shares": avg_shares,
        "engagement_rate": engagement_rate,
    }


def _split_recent_windows(posts: List[Dict], window_days: int = 7) -> tuple[List[Dict], List[Dict]]:
    """Split posts into current and previous rolling windows by publish date."""
    if not posts:
        return [], []

    dated_posts = []
    for post in posts:
        dt = _to_naive_dt(post.get("published_at"))
        if dt is not None:
            dated_posts.append((post, dt))

    if not dated_posts:
        return [], []

    latest_dt = max(dt for _, dt in dated_posts)
    current_start = latest_dt - timedelta(days=window_days - 1)
    previous_end = current_start - timedelta(seconds=1)
    previous_start = previous_end - timedelta(days=window_days - 1)

    current_posts = [post for post, dt in dated_posts if current_start <= dt <= latest_dt]
    previous_posts = [post for post, dt in dated_posts if previous_start <= dt <= previous_end]
    return current_posts, previous_posts


def _compute_delta_pct(posts: List[Dict], metric_fn, window_days: int = 7) -> Optional[float]:
    """Compute percentage delta between current and previous rolling windows."""
    current_posts, previous_posts = _split_recent_windows(posts, window_days=window_days)
    if not current_posts or not previous_posts:
        return None

    current_value = metric_fn(current_posts)
    previous_value = metric_fn(previous_posts)
    if previous_value == 0:
        return None

    return ((current_value - previous_value) / previous_value) * 100


def _delta_suffix(delta_pct: Optional[float], window_days: int = 7) -> str:
    """Render helper-text suffix for KPI delta context."""
    if delta_pct is None:
        return f"No prior {window_days}-day baseline in current dataset."
    return f"{delta_pct:+.1f}% vs previous {window_days}-day window."


def _compute_insights(
    posts: List[Dict],
    platform: str,
    reactions_breakdown: Optional[Dict[str, int]] = None,
) -> List[str]:
    """Return a short list of insight strings (alerts / highlights) from the current run."""
    out: List[str] = []
    if not posts:
        return out
    window_days = 7
    # 1) Reactions/engagement down vs prior 7 days (Facebook)
    if platform == "Facebook":
        reactions_delta = _compute_delta_pct(posts, calculate_total_reactions, window_days)
        if reactions_delta is not None and reactions_delta < -15:
            out.append(
                f"⚠️ Total reactions are down {abs(reactions_delta):.0f}% vs previous {window_days} days."
            )
        engagement_delta = _compute_delta_pct(
            posts,
            lambda items: calculate_average_engagement(items, platform) if items else 0.0,
            window_days,
        )
        if engagement_delta is not None and engagement_delta > 20:
            out.append(
                f"✅ Engagement is up {engagement_delta:.0f}% vs previous {window_days} days."
            )
    # 2) Last N posts with no comments
    try:
        sorted_by_date = sorted(
            posts,
            key=lambda p: (
                pd.to_datetime(p.get("published_at"), errors="coerce") or pd.Timestamp.min
            ),
            reverse=True,
        )
        last_3 = sorted_by_date[:3]
        if len(last_3) >= 2 and all((p.get("comments_count") or 0) == 0 for p in last_3):
            out.append("ℹ️ Last 2+ posts have no comments.")
    except Exception:
        pass
    # 3) Facebook: reactions mostly positive (Like + Love > 80%)
    if reactions_breakdown and platform == "Facebook":
        total = sum(reactions_breakdown.values())
        if total:
            like_love = reactions_breakdown.get("like", 0) + reactions_breakdown.get("love", 0)
            if like_love / total > 0.8:
                out.append("✅ Reactions are mostly positive (Like + Love > 80%).")
    return out


@st.cache_data(ttl=3600, max_entries=32, show_spinner=False)
def fetch_youtube_comments(
    video_urls: List[str], _apify_token: str, max_comments_per_video: int = 10
) -> List[Dict]:
    """
    Fetch comments from YouTube videos using the YouTube Comments Scraper.
    Tries one batched run with all URLs when supported; falls back to per-video runs on failure.
    Cached for 1 hour per video URL combination.
    """
    if not video_urls:
        return []

    try:
        client = ApifyClient(_apify_token)
        all_comments = []

        # Try batched run: single actor call with all video URLs
        batch_input = {
            "startUrls": [{"url": u} for u in video_urls],
            "maxComments": max_comments_per_video,
            "commentsSortBy": "1",  # 1 = most relevant comments
        }
        try:
            st.info(f"Fetching comments from {len(video_urls)} video(s) in one batch...")
            run = client.actor(YOUTUBE_COMMENTS_ACTOR_ID).call(run_input=batch_input)
            cap = len(video_urls) * max_comments_per_video
            for item in client.dataset(run["defaultDatasetId"]).iterate_items():
                all_comments.append(item)
                if len(all_comments) >= cap:
                    break
            if all_comments:
                return all_comments
        except Exception:
            all_comments = []

        # Fallback: per-video runs
        for video_url in video_urls:
            st.info(f"Fetching comments from: {video_url}")
            run_input = {
                "startUrls": [{"url": video_url}],
                "maxComments": max_comments_per_video,
                "commentsSortBy": "1",
            }
            run = client.actor(YOUTUBE_COMMENTS_ACTOR_ID).call(run_input=run_input)
            n = 0
            for item in client.dataset(run["defaultDatasetId"]).iterate_items():
                all_comments.append(item)
                n += 1
                if n >= max_comments_per_video:
                    break

        return all_comments

    except Exception as e:
        st.error(f"Error fetching YouTube comments: {str(e)}")
        return []


# Note: aggregate_all_comments is now imported from app.analytics


def analyze_all_sentiments(comments: List[str]) -> Dict[str, int]:
    """
    Analyze sentiment for all comments and return count by sentiment type.
    Returns dict with 'positive', 'negative', 'neutral' counts.
    """
    # Optimized: use Counter for efficient counting
    sentiment_counts = Counter(
        analyze_sentiment_placeholder(comment)
        for comment in comments
        if comment and comment.strip()
    )

    # Ensure all keys exist
    return {
        "positive": sentiment_counts.get("positive", 0),
        "negative": sentiment_counts.get("negative", 0),
        "neutral": sentiment_counts.get("neutral", 0),
    }


# ============================================================================
# FILE OPERATIONS
# ============================================================================


def save_data_to_files(
    raw_data: List[Dict], normalized_data: List[Dict], platform: str
) -> tuple[str, str, str]:
    """
    Save raw and processed data to files using DataPersistenceService.
    Returns tuple of (json_file_path, csv_file_path, comments_csv_file_path)
    """
    try:
        # Use the new DataPersistenceService
        persistence = DataPersistenceService()
        json_path, csv_path, comments_path = persistence.save_dataset(
            raw_data=raw_data, normalized_data=normalized_data, platform=platform
        )
        return json_path, csv_path, comments_path
    except Exception as e:
        st.error(f"Error saving files: {str(e)}")
        return None, None, None


def load_data_from_file(file_path: str) -> Optional[List[Dict]]:
    """
    Load data from a saved file (JSON or CSV) using DataPersistenceService.
    Returns normalized data in the same schema (missing keys filled) so it matches API output.
    """
    try:
        persistence = DataPersistenceService()
        data = persistence.load_dataset(file_path)
        return normalize_posts_to_schema(data) if data else None
    except Exception as e:
        st.error(f"Error loading file: {str(e)}")
        return None


def save_data_to_files_only(
    raw_data: List[Dict], normalized_data: List[Dict], platform: str
) -> Dict[str, Any]:
    """
    Fallback: Save data to files only (no database).
    Returns dict with file paths for consistent UI.
    """
    try:
        persistence = DataPersistenceService()
        json_path, csv_path, comments_path = persistence.save_dataset(
            raw_data=raw_data, normalized_data=normalized_data, platform=platform
        )
        return {
            "json_path": json_path,
            "csv_path": csv_path,
            "comments_path": comments_path,
            "total_posts": len(normalized_data),
            "total_comments": sum(
                len(p.get("comments_list", []) or [])
                for p in normalized_data
                if isinstance(p.get("comments_list"), list)
            ),
        }
    except Exception as e:
        st.error(f"Error saving files: {str(e)}")
        return {}


def save_data_to_database(
    raw_data: List[Dict], normalized_data: List[Dict], platform: str, url: str, max_posts: int
) -> Dict[str, Any]:
    """
    Save data to MongoDB using MongoDBService, and to files as backup.
    Returns dict with job_id and statistics when DB is connected; otherwise falls back to files only.
    """
    try:
        db_service = st.session_state.get("db_service")
        if not db_service:
            st.warning("Database not initialized. Saving to files only.")
            return save_data_to_files_only(raw_data, normalized_data, platform)

        # Ensure all comments have required fields before saving
        for post in normalized_data:
            comments_list = post.get("comments_list", [])
            if isinstance(comments_list, list):
                for i, comment in enumerate(comments_list):
                    if not isinstance(comment, dict):
                        comments_list[i] = {"text": str(comment)}
                        comment = comments_list[i]

                    if "comment_id" not in comment or not comment.get("comment_id"):
                        post_id = post.get("post_id", "")
                        comment_text = comment.get("text", "")
                        unique_string = f"{post_id}_{comment_text}_{i}_{platform}"
                        comment["comment_id"] = hashlib.md5(unique_string.encode()).hexdigest()

                    if "text" not in comment:
                        comment["text"] = ""
                    if "author_name" not in comment:
                        comment["author_name"] = (
                            comment.get("ownerUsername", "")
                            or comment.get("authorDisplayName", "")
                            or "Unknown"
                        )
                    if "created_time" not in comment:
                        comment["created_time"] = (
                            comment.get("timestamp", "") or comment.get("publishedAt", "") or ""
                        )
                    if "likes_count" not in comment:
                        comment["likes_count"] = (
                            comment.get("likesCount", 0) or comment.get("likeCount", 0) or 0
                        )

        with st.spinner("💾 Saving to database..."):
            result = db_service.save_scraping_results(
                platform=platform, url=url, normalized_posts=normalized_data, max_posts=max_posts
            )

        persistence = DataPersistenceService()
        json_path, csv_path, comments_path = persistence.save_dataset(
            raw_data=raw_data, normalized_data=normalized_data, platform=platform
        )
        result["json_path"] = json_path
        result["csv_path"] = csv_path
        result["comments_path"] = comments_path

        return result

    except Exception as e:
        st.error(f"Error saving to database: {str(e)}")
        st.warning("Falling back to file-only storage...")
        return save_data_to_files_only(raw_data, normalized_data, platform)


def load_data_from_database(
    platform: str, days_back: int = 30, limit: int = 1000
) -> Optional[List[Dict]]:
    """
    Load data from MongoDB for the specified platform and date range.
    Returns normalized data in the same format as from API.
    """
    try:
        db_service = st.session_state.get("db_service")
        if not db_service:
            st.warning("Database not initialized. Please use 'Load from File' option.")
            return None

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        with st.spinner(f"📊 Loading {platform} data from database..."):
            posts = db_service.get_posts_for_analysis(
                platform=platform, start_date=start_date, end_date=end_date, limit=limit
            )
            fallback_used = False

            if not posts:
                try:
                    posts = db_service.get_posts_for_analysis(platform=platform, limit=limit)
                    fallback_used = True
                except Exception:
                    posts = None

            if posts:
                if fallback_used:
                    st.warning(
                        "⚠️ No posts matched the requested date range — showing recent posts for the platform instead."
                    )
                for post in posts:
                    post_id = post.get("post_id")
                    if post_id:
                        comments = db_service.get_comments_for_analysis(
                            platform=platform, post_id=post_id, limit=500
                        )
                        post["comments_list"] = comments or []

                st.success(f"✅ Loaded {len(posts)} posts from database")
                return posts
            else:
                st.info(f"No {platform} data found in database for the last {days_back} days")
                return None

    except Exception as e:
        st.error(f"Error loading from database: {str(e)}")
        return None


@functools.lru_cache(maxsize=1)
def get_saved_files() -> Dict[str, List[str]]:
    """
    Get list of saved files organized by platform.
    Returns dict with platform as key and list of file paths as value.
    """
    try:
        files = {"Facebook": [], "Instagram": [], "YouTube": []}

        # Optimized: combine glob patterns and use list comprehension
        all_files = glob.glob("data/raw/*.json") + glob.glob("data/processed/*.csv")

        for file_path in all_files:
            filename = os.path.basename(file_path)
            platform = filename.split("_")[0].title()
            if platform in files:
                files[platform].append(file_path)

        # Sort files by modification time (newest first) - optimized
        for platform in files:
            files[platform].sort(key=os.path.getmtime, reverse=True)

        return files

    except Exception as e:
        st.error(f"Error getting saved files: {str(e)}")
        return {"Facebook": [], "Instagram": [], "YouTube": []}


def extract_main_titles_from_source(file_path: str) -> List[str]:
    """
    Parse the Python source file and return a list of main UI titles.
    We consider st.title(...), st.header(...), st.markdown("##..."/"###...") and st.subheader(...)
    as main titles for the Table of Contents.
    """
    titles: List[str] = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

        # Patterns to extract simple literal titles
        patterns = [
            r"st\.title\(\s*[rR]?[\'\"](.+?)[\'\"]\s*\)",
            r"st\.header\(\s*[rR]?[\'\"](.+?)[\'\"]\s*\)",
            r"st\.subheader\(\s*[rR]?[\'\"](.+?)[\'\"]\s*\)",
        ]

        for pat in patterns:
            for m in re.findall(pat, text, flags=re.DOTALL):
                cleaned = m.strip()
                if cleaned and cleaned not in titles:
                    titles.append(cleaned)

        # Look for st.markdown lines that start with hashes (##, ###)
        for m in re.findall(r"st\.markdown\(\s*[rR]?[\'\"]\s*(#{1,6})\s*(.+?)[\'\"]", text):
            hashes, title_text = m
            cleaned = title_text.strip()
            if cleaned and cleaned not in titles:
                titles.append(cleaned)

    except Exception:
        # Silent failure — this is a helper for UI convenience
        return []

    return titles


# ============================================================================
# APIFY INTEGRATION
# ============================================================================


@st.cache_data(ttl=3600, max_entries=64, show_spinner=False)
def fetch_apify_data(
    platform: str,
    url: str,
    _apify_token: str,
    max_posts: int = 10,
    from_date: str = None,
    to_date: str = None,
) -> Optional[List[Dict]]:
    """
    Fetch data from Apify actor for the given platform and URL.
    Cached for 1 hour per platform+URL combination.
    Uses production Apify client (retries, timeout, user-friendly errors).
    """
    try:
        client = create_apify_client(_apify_token)
        actor_name = ACTOR_CONFIG.get(platform)

        if not actor_name:
            st.error(f"No actor configured for {platform}")
            return None

        # Configure input based on platform with documented formats
        if platform == "Instagram":
            run_input = {
                "directUrls": [url],
                "resultsType": "posts",
                "resultsLimit": max_posts,
                "searchLimit": 10,
            }
        elif platform == "Facebook":
            if actor_name and actor_name.startswith("scraper_one"):
                run_input = {"pageUrls": [url], "resultsLimit": max_posts}
            else:
                run_input = {"startUrls": [url], "resultsLimit": max_posts}
            if from_date:
                run_input["onlyPostsNewerThan"] = from_date
            if to_date:
                run_input["onlyPostsOlderThan"] = to_date
        elif platform == "YouTube":
            if url.startswith("http"):
                run_input = {
                    "startUrls": [{"url": url}],
                    "maxResults": max_posts,
                    "maxResultsShorts": 0,
                    "maxResultStreams": 0,
                    "subtitlesLanguage": "en",
                    "subtitlesFormat": "srt",
                }
            else:
                run_input = {
                    "searchQueries": [url],
                    "maxResults": max_posts,
                    "maxResultsShorts": 0,
                    "maxResultStreams": 0,
                    "subtitlesLanguage": "en",
                    "subtitlesFormat": "srt",
                }
        else:
            run_input = {"startUrls": [{"url": url}], "maxPosts": max_posts}

        st.info(f"Calling Apify actor: {actor_name}")
        st.info(f"Requesting {max_posts} posts from: {url}")
        if from_date or to_date:
            date_info = "Date range: " + (from_date or "") + " " + (to_date or "")
            st.info(f"Date range: {date_info.strip()}")

        _, items = run_actor_and_fetch_dataset(
            client, actor_name, run_input, timeout_secs=DEFAULT_TIMEOUT, max_items=max_posts
        )
        st.info(f"Received {len(items)} posts from actor (requested {max_posts})")
        return items

    except ApifyClientError as e:
        st.error(getattr(e, "user_message", str(e)))
        return None
    except Exception as e:
        st.error(f"Apify API Error: {str(e)}")
        return None


@st.cache_data(ttl=3600, max_entries=256, show_spinner=False)
def fetch_post_comments(
    post_url: str, _apify_token: str, max_comments: int = DEFAULT_MAX_COMMENTS
) -> Optional[List[Dict]]:
    """
    Fetch detailed comments for a specific Facebook post using the Comments Scraper actor.
    Tries different actors and input formats if one fails.
    Cached for 1 hour per post URL + max_comments.
    """
    # Validate URL format
    if not post_url or not post_url.startswith("http"):
        st.error(f"❌ Invalid URL format: {post_url}")
        return None

    client = ApifyClient(_apify_token)

    # Try different actors with unified input format
    # Only attempt the official Apify Facebook comments scraper.
    actor_configs = [
        {
            "actor_id": "apify/facebook-comments-scraper",
            "input": {
                "startUrls": [{"url": post_url}],
                "maxComments": max_comments,
                "includeNestedComments": False,
            },
        }
    ]

    for i, config in enumerate(actor_configs):
        try:
            st.info(f"🔍 Attempt {i + 1}: Using actor '{config['actor_id']}' for: {post_url}")

            # Run the actor
            run = client.actor(config["actor_id"]).call(run_input=config["input"])

            # Fetch results, respecting requested limit
            comments = []
            for item in client.dataset(run["defaultDatasetId"]).iterate_items():
                comments.append(item)
                if len(comments) >= max_comments:
                    break

            if comments:
                st.success(
                    f"✅ Successfully fetched {len(comments)} comments using {config['actor_id']}"
                )
                return comments
            else:
                st.warning(f"⚠️ No comments found with {config['actor_id']}, trying next actor...")

        except Exception as e:
            st.warning(f"⚠️ Actor {config['actor_id']} failed: {str(e)}")
            if i < len(actor_configs) - 1:
                st.info("🔄 Trying next actor...")
            continue

    st.error(f"❌ All comment scrapers failed for post: {post_url}")
    return None


@st.cache_data(ttl=3600, max_entries=32, show_spinner=False)
def _fetch_facebook_comments_batch_data(
    post_urls_tuple: tuple,
    max_comments_per_post: int,
    _apify_token: str,
) -> Optional[List[Dict]]:
    """
    Fetch comment items from Facebook Comments Scraper in one batch run.
    Cached by (sorted URLs, max_comments) to avoid duplicate Apify runs.
    Returns raw comment dicts or None on failure.
    """
    if not post_urls_tuple:
        return None
    post_urls = [{"url": u} for u in post_urls_tuple]
    comments_input = {
        "startUrls": post_urls,
        "resultsLimit": max_comments_per_post,
        "includeNestedComments": False,
        "viewOption": "RANKED_UNFILTERED",
    }
    client = ApifyClient(_apify_token)
    for actor_id in FACEBOOK_COMMENTS_ACTOR_IDS:
        try:
            run = client.actor(actor_id).call(run_input=comments_input)
            max_total = len(post_urls_tuple) * max_comments_per_post
            comments_data = []
            for item in client.dataset(run["defaultDatasetId"]).iterate_items():
                comments_data.append(item)
                if len(comments_data) >= max_total:
                    break
            if comments_data:
                return comments_data
        except Exception:
            continue
    return None


def fetch_comments_for_posts_batch(
    posts: List[Dict], apify_token: str, max_comments_per_post: int = DEFAULT_MAX_COMMENTS
) -> List[Dict]:
    """
    Fetch detailed comments for all Facebook posts using batch processing with the Comments Scraper actor.
    This uses the workflow where we extract all post URLs first, then batch process them for comments.
    Results are cached so the same page + settings do not trigger a new Apify run for 1 hour.
    """
    if not posts:
        return posts

    post_urls = []
    for post in posts:
        post_url = post.get("post_url")
        if post_url and post_url.startswith("http"):
            post_urls.append(post_url)

    if not post_urls:
        st.warning("⚠️ No valid post URLs found for comment extraction")
        return posts

    st.info(f"🔄 Batch comment extraction for {len(post_urls)} posts (cached 1h for same URLs)...")
    urls_key = tuple(sorted(post_urls))
    comments_data = _fetch_facebook_comments_batch_data(
        urls_key, max_comments_per_post, apify_token
    )

    if not comments_data:
        st.error("❌ Batch comment scraper failed or returned no comments")
        return posts

    st.success(f"✅ Fetched {len(comments_data)} comments (from cache or API)")
    return assign_comments_to_posts(posts, comments_data)


def assign_comments_to_posts(posts: List[Dict], comments_data: List[Dict]) -> List[Dict]:
    """
    Assign comments to their respective posts based on post URL matching.
    """
    # Create a mapping of post URLs to posts
    post_url_map = {}
    for post in posts:
        post_url = post.get("post_url")
        if post_url:
            post_url_map[post_url] = post
            post["comments_list"] = []  # Initialize empty comments list

    # Assign comments to posts
    assigned_comments = 0
    unmatched_comments = 0

    for comment in comments_data:
        # Try to find the post this comment belongs to
        comment_url = comment.get("url") or comment.get("postUrl") or comment.get("facebookUrl")

        if not comment_url:
            unmatched_comments += 1
            continue

        matched = False
        if comment_url:
            # Find matching post
            for post_url, post in post_url_map.items():
                if comment_url in post_url or post_url in comment_url:
                    # Normalize comment data
                    normalized_comment = normalize_comment_data(comment)
                    post["comments_list"].append(normalized_comment)
                    assigned_comments += 1
                    matched = True
                    break

        if not matched:
            unmatched_comments += 1

    st.info(f"📊 Assigned {assigned_comments} comments to {len(posts)} posts")
    if unmatched_comments > 0:
        st.warning(f"⚠️ {unmatched_comments} comments could not be matched to posts")
    return posts


def fetch_comments_for_posts(
    posts: List[Dict], apify_token: str, max_comments_per_post: int = DEFAULT_MAX_COMMENTS
) -> List[Dict]:
    """
    Fetch detailed comments for all Facebook posts using the Comments Scraper actor.
    This is a separate phase after initial post normalization.
    """
    if not posts:
        return posts

    st.info(f"🔄 Fetching detailed comments for {len(posts)} posts...")

    # Create progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, post in enumerate(posts):
        # Update progress
        progress = (i + 1) / len(posts)
        progress_bar.progress(progress)
        status_text.text(
            f"Fetching comments for post {i + 1}/{len(posts)}: {post.get('post_id', 'Unknown')}"
        )

        # Check if we need to fetch comments
        comments_list = post.get("comments_list", [])
        should_fetch = (
            not comments_list
            or (isinstance(comments_list, list) and len(comments_list) == 0)
            or isinstance(comments_list, int)  # If it's an int, it's a count, not actual comments
        )

        if should_fetch and post.get("post_url"):
            try:
                # Add rate limiting delay (2 seconds between calls)
                if i > 0:  # Skip delay for first post
                    time.sleep(2)

                # Fetch comments for this post
                raw_comments = fetch_post_comments(
                    post["post_url"], apify_token, max_comments_per_post
                )
                if raw_comments:
                    # Normalize comment data
                    normalized_comments = []
                    for raw_comment in raw_comments:
                        normalized_comment = normalize_comment_data(raw_comment)
                        normalized_comments.append(normalized_comment)
                    post["comments_list"] = normalized_comments
                    st.success(
                        f"✅ Fetched {len(normalized_comments)} comments for post {post.get('post_id', 'Unknown')}"
                    )
                else:
                    post["comments_list"] = []
                    st.warning(f"⚠️ No comments found for post {post.get('post_id', 'Unknown')}")
            except Exception as e:
                st.warning(
                    f"❌ Failed to fetch comments for post {post.get('post_id', 'Unknown')}: {str(e)}"
                )
                post["comments_list"] = []
        else:
            if not post.get("post_url"):
                st.warning(
                    f"⚠️ No URL found for post {post.get('post_id', 'Unknown')}, skipping comment fetch"
                )

    # Clear progress indicators
    progress_bar.empty()
    status_text.empty()

    return posts


def normalize_comment_data(raw_comment: Dict) -> Dict:
    """
    Normalize comment data to consistent schema.
    Maps various field names to standard format.
    """
    try:
        # Extract author name from various possible fields
        author_name = ""
        if "from" in raw_comment and isinstance(raw_comment["from"], dict):
            author_name = raw_comment["from"].get("name", "")
        elif "author" in raw_comment:
            if isinstance(raw_comment["author"], dict):
                author_name = raw_comment["author"].get("name", "")
            else:
                author_name = str(raw_comment["author"])

        # Extract comment text
        text = (
            raw_comment.get("text", "")
            or raw_comment.get("message", "")
            or raw_comment.get("content", "")
        )

        # Extract created time
        created_time = (
            raw_comment.get("created_time", "")
            or raw_comment.get("timestamp", "")
            or raw_comment.get("date", "")
        )

        # Extract likes count
        likes_count = 0
        if "like_count" in raw_comment:
            likes_count = raw_comment["like_count"]
        elif "likes" in raw_comment:
            if isinstance(raw_comment["likes"], int):
                likes_count = raw_comment["likes"]
            elif isinstance(raw_comment["likes"], list):
                likes_count = len(raw_comment["likes"])

        # Extract replies count
        replies_count = 0
        if "comment_count" in raw_comment:
            replies_count = raw_comment["comment_count"]
        elif "replies" in raw_comment:
            if isinstance(raw_comment["replies"], int):
                replies_count = raw_comment["replies"]
            elif isinstance(raw_comment["replies"], list):
                replies_count = len(raw_comment["replies"])

        normalized_comment = {
            "comment_id": raw_comment.get("id", ""),
            "text": text,
            "author_name": author_name,
            "created_time": created_time,
            "likes_count": likes_count,
            "replies_count": replies_count,
        }

        return normalized_comment

    except Exception as e:
        st.warning(f"Failed to normalize comment: {str(e)}")
        return {
            "comment_id": "",
            "text": "",
            "author_name": "",
            "created_time": "",
            "likes_count": 0,
            "replies_count": 0,
        }


# ============================================================================
# VISUALIZATION FUNCTIONS
# ============================================================================


def _fetch_one_instagram_post_comments(
    post_url: str,
    client: ApifyClient,
    max_comments_per_post: int,
) -> List[Dict]:
    """
    Fetch comments for a single Instagram post. Tries primary actor first, then fallbacks on failure.
    Safe to call from a thread (no st.* calls).
    """
    run_input = {
        "directUrls": [post_url],
        "resultsLimit": max_comments_per_post,
        "includeNestedComments": True,
        "isNewestComments": False,
    }
    # Primary actor first
    for actor_id in INSTAGRAM_COMMENTS_ACTOR_IDS:
        try:
            run = client.actor(actor_id).call(run_input=run_input)
            if run and run.get("status") == "SUCCEEDED":
                dataset = client.dataset(run["defaultDatasetId"])
                comments_data = []
                for item in dataset.iterate_items():
                    comments_data.append(item)
                    if len(comments_data) >= max_comments_per_post:
                        break
                if comments_data:
                    return comments_data
                # Empty result: try next actor only if there are fallbacks
                if actor_id == INSTAGRAM_COMMENTS_ACTOR_IDS[0]:
                    continue
                return []
        except Exception:
            continue
    return []


def scrape_instagram_comments_batch(
    post_urls: List[str], apify_token: str, max_comments_per_post: int = DEFAULT_MAX_COMMENTS
) -> List[Dict]:
    """Scrape Instagram comments from multiple post URLs with limited concurrency."""
    if not post_urls:
        return []

    client = ApifyClient(apify_token)
    all_comments = []
    max_workers = 3

    st.info(
        f"🔄 Starting Instagram comments extraction for {len(post_urls)} posts (concurrency: {max_workers})..."
    )

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {
            executor.submit(
                _fetch_one_instagram_post_comments,
                post_url,
                client,
                max_comments_per_post,
            ): post_url
            for post_url in post_urls
        }
        done = 0
        for future in as_completed(future_to_url):
            post_url = future_to_url[future]
            try:
                comments_data = future.result()
                if comments_data:
                    all_comments.extend(comments_data)
                    st.success(
                        f"✅ Extracted {len(comments_data)} comments from post ({done + 1}/{len(post_urls)} done)"
                    )
                done += 1
                if done % max_workers == 0:
                    time.sleep(2)  # Brief delay between batches to avoid rate limits
            except Exception as e:
                st.warning(f"❌ Error processing {post_url}: {str(e)}")

    st.success(f"🎉 Instagram comments extraction complete! Total comments: {len(all_comments)}")
    return all_comments


def assign_instagram_comments_to_posts(posts: List[Dict], comments_data: List[Dict]) -> List[Dict]:
    """Assign Instagram comments to their corresponding posts based on postId."""
    if not comments_data:
        return posts

    # Create a mapping of postId to comments
    comments_by_post = {}
    for comment in comments_data:
        post_id = comment.get("postId", "")
        if post_id:
            if post_id not in comments_by_post:
                comments_by_post[post_id] = []
            # Format comment for consistency
            formatted_comment = {
                "text": comment.get("text", ""),
                "ownerUsername": comment.get("ownerUsername", ""),
                "ownerId": comment.get("ownerId", ""),
                "timestamp": comment.get("timestamp", ""),
                "position": comment.get("position", 0),
                "ownerIsVerified": comment.get("ownerIsVerified", False),
                "ownerProfilePicUrl": comment.get("ownerProfilePicUrl", ""),
            }
            comments_by_post[post_id].append(formatted_comment)

    # Assign comments to posts
    for post in posts:
        post_id = post.get("post_id", "")
        if post_id in comments_by_post:
            post["comments_list"] = comments_by_post[post_id]
            post["comments_count"] = len(comments_by_post[post_id])
        else:
            # Keep existing comments_count if no new comments found
            if "comments_list" not in post:
                post["comments_list"] = []

    return posts


def create_wordcloud(
    comments: List[str],
    width: int = 800,
    height: int = 400,
    figsize: tuple = (10, 5),
    section_key: str = "main",
):
    """Generate and display a premium, insight-focused word cloud."""
    if not comments:
        st.info("No comments available for word cloud")
        return

    from app.viz.wordcloud_generator import render_wordcloud

    bigram_key = f"wc_bigrams_{section_key}"
    max_words_key = f"wc_max_words_{section_key}"
    min_freq_key = f"wc_min_freq_{section_key}"
    hashtag_key = f"wc_keep_hashtags_{section_key}"

    controls = st.columns([1, 1, 1, 1])
    with controls[0]:
        include_bigrams = st.checkbox(
            "Include bigrams",
            value=True,
            key=bigram_key,
            help="Show two-word themes like 'customer service'.",
        )
    with controls[1]:
        max_words = st.slider("Max words", 30, 180, 90, 10, key=max_words_key)
    with controls[2]:
        min_frequency = st.slider("Min frequency", 1, 10, 2, 1, key=min_freq_key)
    with controls[3]:
        keep_hashtag_words = st.checkbox(
            "Keep hashtag words",
            value=True,
            key=hashtag_key,
            help="Convert #launch -> launch instead of dropping hashtag terms.",
        )

    render_wordcloud(
        comments,
        {
            "width": max(width, 1400),
            "height": max(height, 700),
            "max_words": max_words,
            "min_frequency": min_frequency,
            "include_bigrams": include_bigrams,
            "keep_hashtag_words": keep_hashtag_words,
            "background_mode": "theme",
            "caption": (
                "Themes extracted after URL/mention cleanup, stopword removal, and "
                "light lemmatization for clearer topic signal."
            ),
            "section_key": section_key,
        },
    )


def create_instagram_monthly_analysis(posts: List[Dict], platform: str):
    """Create focused monthly Instagram analysis with high-signal visuals."""
    if platform != "Instagram":
        return

    total_posts = len(posts)
    total_likes = sum(post.get("likes", 0) for post in posts)
    total_comments = sum(post.get("comments_count", 0) for post in posts)
    avg_engagement = (total_likes + total_comments) / total_posts if total_posts else 0.0
    window_days = 7

    post_delta = _compute_delta_pct(posts, lambda items: len(items), window_days)
    likes_delta = _compute_delta_pct(
        posts, lambda items: sum(p.get("likes", 0) for p in items), window_days
    )
    comments_delta = _compute_delta_pct(
        posts, lambda items: sum(p.get("comments_count", 0) for p in items), window_days
    )
    engagement_delta = _compute_delta_pct(
        posts,
        lambda items: (
            (sum(p.get("likes", 0) + p.get("comments_count", 0) for p in items) / len(items))
            if items
            else 0.0
        ),
        window_days,
    )

    kpi_cards(
        [
            {
                "label": "Total Posts",
                "value": f"{total_posts:,}",
                "color_key": "default",
                "help_text": _delta_suffix(post_delta, window_days),
            },
            {
                "label": "Total Likes",
                "value": f"{total_likes:,}",
                "color_key": "likes",
                "help_text": _delta_suffix(likes_delta, window_days),
            },
            {
                "label": "Total Comments",
                "value": f"{total_comments:,}",
                "color_key": "comments",
                "help_text": _delta_suffix(comments_delta, window_days),
            },
            {
                "label": "Avg Engagement",
                "value": f"{avg_engagement:.1f}",
                "color_key": "engagement",
                "help_text": _delta_suffix(engagement_delta, window_days),
            },
        ]
    )

    st.markdown("#### Trend and Drivers")
    create_engagement_trend_chart(posts)

    st.markdown("---")
    create_posting_frequency_chart(posts)

    st.markdown("---")
    create_top_posts_chart(posts, top_n=5)

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        create_content_type_chart(posts)
    with col2:
        create_hashtag_chart(posts, top_n=10)


def create_instagram_monthly_insights(posts: List[Dict], platform: str):
    """Create monthly Instagram insights using new analytics and viz components."""
    if platform != "Instagram":
        return

    st.markdown("---")
    st.markdown("### 💡 Monthly Instagram Insights")

    # Use analytics module to aggregate comments
    all_comments = aggregate_all_comments(posts)

    if all_comments:
        # Advanced NLP Analysis Dashboard (function adds its own title)
        create_advanced_nlp_dashboard(all_comments)

        st.markdown("---")

        # Create two columns for traditional insights
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 💬 Monthly Comments Word Cloud")
            create_wordcloud(
                all_comments,
                width=1200,
                height=600,
                figsize=(15, 8),
                section_key="ig_monthly_comments",
            )

        with col2:
            st.markdown("#### 😊 Monthly Sentiment Distribution")
            sentiment_counts = analyze_all_sentiments(all_comments)
            create_sentiment_pie_chart(sentiment_counts)

            # Display summary with new component
            from app.viz.charts import create_sentiment_summary

            create_sentiment_summary(sentiment_counts)

        # Sentiment Comparison View (Emoji analysis already included in Advanced NLP Dashboard above)
        # Only show comparison if we have enough data
        try:
            from app.nlp.advanced_nlp import analyze_text_emojis, analyze_text_with_emoji_sentiment
            from app.nlp.sentiment_analyzer import analyze_corpus_sentiment_phrases

            aggregated_text = " ".join([t for t in all_comments if isinstance(t, str)])
            emoji_analysis = analyze_text_emojis(aggregated_text)
            text_sentiment = analyze_corpus_sentiment_phrases(all_comments)
            combined_sentiment = analyze_text_with_emoji_sentiment(aggregated_text)

            # Only show sentiment comparison if we have meaningful data
            if emoji_analysis.get("emoji_count", 0) > 0:
                st.markdown("---")
                st.markdown("#### 📊 Sentiment Comparison")
                create_sentiment_comparison_view(text_sentiment, emoji_analysis, combined_sentiment)
        except Exception as e:
            # Silently skip if sentiment comparison fails (emoji analysis already shown in dashboard)
            pass
    else:
        st.info("📊 No comment text available for monthly insights analysis")
        st.warning(
            "💡 **To analyze comments:** Enable 'Fetch Detailed Comments' in the sidebar and re-analyze the page."
        )


def analyze_emojis_in_comments_legacy(comments: List[str]) -> Dict[str, int]:
    """Legacy function - use app.analytics.analyze_emojis_in_comments instead."""
    from app.analytics import analyze_emojis_in_comments as analyze_emojis

    return analyze_emojis(comments)


def create_instagram_post_analysis(selected_post: Dict, platform: str):
    """Create individual Instagram post analysis with word cloud and sentiment."""
    if platform != "Instagram":
        return

    st.markdown("---")
    st.markdown("### 🔍 Individual Post Analysis")

    # Post metrics
    likes = selected_post.get("likes", 0)
    comments_count = selected_post.get("comments_count", 0)
    engagement = likes + comments_count

    # Display post metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Likes", f"{likes:,}")
    with col2:
        st.metric("Comments", f"{comments_count:,}")
    with col3:
        st.metric("Total Engagement", f"{engagement:,}")
    with col4:
        if selected_post.get("type"):
            st.metric("Type", selected_post["type"])

    # Comments analysis for this specific post
    comments_list = selected_post.get("comments_list", [])

    if isinstance(comments_list, list) and comments_list:
        st.markdown("#### 💬 Post Comments Analysis")

        # Extract comment texts
        comment_texts = []
        for comment in comments_list:
            if isinstance(comment, dict):
                text = comment.get("text", "")
                if text and text.strip():
                    comment_texts.append(text.strip())
            elif isinstance(comment, str) and comment.strip():
                comment_texts.append(comment.strip())

        if comment_texts:
            # Advanced NLP Analysis for Post Comments
            st.markdown("##### 🧠 Advanced Comment Analysis")
            create_advanced_nlp_dashboard(comment_texts)

            st.markdown("---")

            # Create two columns for traditional analysis
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("##### 📊 Comments Word Cloud")
                create_wordcloud(
                    comment_texts,
                    width=600,
                    height=400,
                    figsize=(10, 6),
                    section_key="ig_post_comments",
                )

            with col2:
                st.markdown("##### 😊 Comments Sentiment")
                sentiment_counts = analyze_all_sentiments(comment_texts)
                create_sentiment_pie_chart(sentiment_counts)

                # Show sentiment summary
                total_sentiment = sum(sentiment_counts.values())
                if total_sentiment > 0:
                    st.markdown("**Sentiment Summary:**")
                    st.markdown(
                        f"- **Positive:** {sentiment_counts['positive']} ({sentiment_counts['positive'] / total_sentiment * 100:.1f}%)"
                    )
                    st.markdown(
                        f"- **Negative:** {sentiment_counts['negative']} ({sentiment_counts['negative'] / total_sentiment * 100:.1f}%)"
                    )
                    st.markdown(
                        f"- **Neutral:** {sentiment_counts['neutral']} ({sentiment_counts['neutral'] / total_sentiment * 100:.1f}%)"
                    )

            # Emoji analysis for this post
            st.markdown("---")
            st.markdown("##### 😀 Emojis in Post Comments")
            try:
                from app.nlp.advanced_nlp import (
                    analyze_text_emojis,
                    analyze_text_with_emoji_sentiment,
                )
                from app.nlp.sentiment_analyzer import analyze_corpus_sentiment_phrases

                post_agg_text = " ".join([t for t in comment_texts if isinstance(t, str)])
                post_emoji_analysis = analyze_text_emojis(post_agg_text)
                post_text_sentiment = analyze_corpus_sentiment_phrases(comment_texts)
                post_combined = analyze_text_with_emoji_sentiment(post_agg_text)

                create_emoji_sentiment_chart(post_emoji_analysis)

                # Sentiment comparison
                st.markdown("---")
                create_sentiment_comparison_view(
                    post_text_sentiment, post_emoji_analysis, post_combined
                )
            except Exception as e:
                st.warning(f"Post emoji sentiment section unavailable: {e}")
        else:
            st.info("No comment text available for this post's analysis")
    else:
        st.info("No comments available for this post")
        st.warning(
            "💡 **To see post analysis:** Enable 'Fetch Detailed Comments' in the sidebar and re-analyze the page."
        )


# ============================================================================
# URL VALIDATION (uses URL_PATTERNS from app.config)
# ============================================================================


def validate_url(url: str, platform: str) -> bool:
    """Tighten platform URL validation with pre-compiled regex patterns."""
    pattern = URL_PATTERNS.get(platform)
    return bool(pattern.match(url)) if pattern else False


# ============================================================================
# MAIN STREAMLIT APP
# ============================================================================


def main():
    st.set_page_config(
        page_title="Social Media Analytics",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    if "theme" not in st.session_state:
        st.session_state.theme = "light"
    st.markdown(get_custom_css(st.session_state.theme), unsafe_allow_html=True)

    # App header: compact, premium hierarchy (title from config for rebranding)
    try:
        from app.config.settings import REPORT_TITLE

        header_title = REPORT_TITLE or "Social Media Analytics"
    except Exception:
        header_title = "Social Media Analytics"
    page_header(
        header_title,
        subtitle="Analyze Facebook, Instagram & YouTube with AI-powered insights",
    )

    # Theme Toggle disabled - using Streamlit's default light theme
    # st.sidebar.markdown("### ⚙️ Settings")
    # theme_toggle = st.sidebar.checkbox(
    #     "🌙 Dark Mode",
    #     value=st.session_state.theme == 'dark',
    #     help="Toggle between light and dark themes"
    # )
    #
    # if theme_toggle and st.session_state.theme != 'dark':
    #     st.session_state.theme = 'dark'
    #     st.rerun()
    # elif not theme_toggle and st.session_state.theme != 'light':
    #     st.session_state.theme = 'light'
    #     st.rerun()
    #
    # st.sidebar.markdown("---")

    # Check for API token with better error handling
    @with_error_boundary("API Token Error", show_details=True)
    def get_api_token():
        try:
            # First try Streamlit secrets
            if hasattr(st, "secrets") and "APIFY_TOKEN" in st.secrets:
                return st.secrets["APIFY_TOKEN"]
            # Then try environment variable
            return os.environ.get("APIFY_TOKEN")
        except Exception:
            # Fallback to environment variable
            return os.environ.get("APIFY_TOKEN")

    apify_token = get_api_token()

    if not apify_token:
        show_warning(
            message="Please set your APIFY_TOKEN in environment variables or Streamlit secrets.",
            title="API Token Required",
        )
        st.stop()

    # Initialize MongoDB (optional); only set db_service when connection succeeds
    @st.cache_resource
    def _init_db():
        if not MONGODB_AVAILABLE or MongoDBService is None:
            return None, "pymongo not installed (pip install pymongo)"
        try:
            from app.config.database import get_database

            db = get_database()
            if db.test_connection():
                return MongoDBService(), None
            return None, "Connection test failed (is MongoDB running?)"
        except Exception as e:
            return None, str(e)

    if "db_service" not in st.session_state:
        _db, _err = _init_db()
        st.session_state.db_service = _db
        st.session_state.db_error = _err

    # ---- Sidebar header ----
    st.sidebar.markdown("## 📊 Social Analytics")
    st.sidebar.caption("Analyze Facebook, Instagram & YouTube")
    st.sidebar.markdown("---")

    # Database status (compact)
    if st.session_state.db_service:
        st.sidebar.caption("🗄️ Database connected")
    else:
        st.sidebar.caption("🗄️ No database (optional)")
        err = st.session_state.get("db_error")
        if err:
            st.sidebar.caption(f"ℹ️ {err[:60]}{'…' if len(err) > 60 else ''}")
    st.sidebar.markdown("---")

    # Platform & data source
    st.sidebar.markdown("### 📱 Platform")
    platform = st.sidebar.radio(
        "Platform",
        ["Facebook", "Instagram", "YouTube"],
        label_visibility="collapsed",
        help="Select the social media platform to analyze",
    )

    st.sidebar.markdown("### 📁 Data source")
    data_source_options = ["Fetch from API", "Load from File"]
    if st.session_state.get("db_service"):
        data_source_options = ["Fetch from API", "Load from Database", "Load from File"]
    data_source = st.sidebar.radio(
        "Data source",
        data_source_options,
        label_visibility="collapsed",
        help="Fetch new data, load from DB, or load from saved files",
    )

    # ---- Fetch-from-API options (all platforms) ----
    fetch_detailed_comments = False
    comment_method = "Batch Processing"
    max_comments_per_post = DEFAULT_MAX_COMMENTS
    max_posts = DEFAULT_MAX_POSTS
    from_date = None
    to_date = None

    if data_source == "Fetch from API":
        with st.sidebar.expander("⚙️ Fetch settings", expanded=True):
            # Persist max_posts in session for better UX
            if "max_posts" not in st.session_state:
                st.session_state.max_posts = 10
            preset = st.sidebar.radio(
                "Preset",
                ["Quick (10)", "Standard (25)", "Full (50)", "Custom"],
                help="Quick = faster run. Higher = more data and Apify usage.",
                horizontal=True,
            )
            if preset == "Quick (10)":
                max_posts = 10
            elif preset == "Standard (25)":
                max_posts = 25
            elif preset == "Full (50)":
                max_posts = 50
            else:
                max_posts = st.sidebar.slider(
                    "Posts to fetch",
                    min_value=5,
                    max_value=100,
                    value=st.session_state.max_posts,
                    help="Maximum posts per run. Higher values take longer and use more Apify units.",
                )
                st.session_state.max_posts = max_posts
            if preset != "Custom":
                st.session_state.max_posts = max_posts
            if platform == "Facebook":
                date_range_option = st.sidebar.radio(
                    "Date range",
                    ["All Posts", "Last 30 Days", "Last 7 Days", "Custom Range"],
                    help="Time range for posts (Facebook only)",
                )
                today = datetime.now()
                if date_range_option == "Last 30 Days":
                    from_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")
                    to_date = None
                elif date_range_option == "Last 7 Days":
                    from_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
                    to_date = None
                elif date_range_option == "Custom Range":
                    from_date = st.sidebar.date_input(
                        "From",
                        value=today - timedelta(days=30),
                        help="Start date",
                    ).strftime("%Y-%m-%d")
                    to_date = st.sidebar.date_input(
                        "To",
                        value=today,
                        help="End date",
                    ).strftime("%Y-%m-%d")
                else:
                    from_date = None
                    to_date = None

        with st.sidebar.expander("💬 Comments (word clouds & sentiment)", expanded=True):
            if platform == "Facebook":
                st.sidebar.caption(
                    "**Batch** = one Apify run for all posts (recommended). **Individual** = one run per post."
                )
                comment_method = st.sidebar.radio(
                    "Method",
                    ["Batch Processing", "Individual Posts"],
                    help="Batch is cheaper and faster. Use Individual only if Batch fails for your page.",
                    label_visibility="collapsed",
                )
                st.sidebar.caption("Facebook Comments Scraper may have limitations on some pages.")
                fetch_detailed_comments = st.sidebar.checkbox(
                    "Fetch detailed comments",
                    value=True,
                    help="Fetch comment text for word clouds and sentiment. Adds one or more Apify runs.",
                )
            elif platform == "Instagram":
                st.sidebar.caption("~$2.30 per 1,000 comments. Free plan: $5/month.")
                fetch_detailed_comments = st.sidebar.checkbox(
                    "Fetch detailed comments",
                    value=True,
                    help="Get comment text for word clouds and sentiment",
                )
            else:
                st.sidebar.caption("Step 2: fetch comments from videos.")
                fetch_detailed_comments = st.sidebar.checkbox(
                    "Fetch detailed comments",
                    value=True,
                    help="Get comment text from videos (extra Apify run)",
                )

            if fetch_detailed_comments:
                max_comments_per_post = st.sidebar.slider(
                    "Max comments per post",
                    min_value=10,
                    max_value=100,
                    value=DEFAULT_MAX_COMMENTS,
                    help="Maximum comments to fetch per post or video. Lower values are faster and use fewer Apify units.",
                )

    # ---- Analysis options (collapsible) ----
    with st.sidebar.expander("🔧 Analysis options", expanded=False):
        use_phrase_analysis = st.sidebar.checkbox(
            "Phrase-based analysis",
            value=True,
            help="Extract phrases (e.g. 'thank you') for better sentiment",
        )
        use_sentiment_coloring = st.sidebar.checkbox(
            "Sentiment colors in word cloud",
            value=True,
            help="Green=positive, red=negative, gray=neutral",
        )
        use_simple_wordcloud = st.sidebar.checkbox(
            "Simple word cloud (fallback)",
            value=False,
            help="Use if phrase analysis shows 'No meaningful content'",
        )

    # ---- Load from file ----
    if data_source == "Load from File":
        st.sidebar.markdown("---")
        saved_files = get_saved_files()
        platform_files = saved_files.get(platform, [])

        if platform_files:
            st.sidebar.markdown("### 📂 Saved files")
            file_options = []
            for file_path in platform_files:
                filename = os.path.basename(file_path)
                try:
                    timestamp_part = (
                        filename.split("_", 1)[1].replace(".json", "").replace(".csv", "")
                    )
                    display_name = (
                        f"{timestamp_part} ({'JSON' if file_path.endswith('.json') else 'CSV'})"
                    )
                except (IndexError, ValueError, AttributeError):
                    display_name = filename
                file_options.append((display_name, file_path))

            selected_file_display = st.sidebar.selectbox(
                "File",
                options=[opt[0] for opt in file_options],
                label_visibility="collapsed",
                help="Choose a saved file to load",
            )
            selected_file_path = next(
                (fp for d, fp in file_options if d == selected_file_display), None
            )

            if selected_file_path and st.sidebar.button("📂 Load file", type="primary"):
                with st.spinner(f"Loading {os.path.basename(selected_file_path)}..."):
                    loaded_data = load_data_from_file(selected_file_path)
                if loaded_data:
                    st.session_state.posts_data = loaded_data
                    st.success(f"✅ Loaded {len(loaded_data)} posts")
                    st.rerun()
                else:
                    st.error("Failed to load file")
        else:
            st.sidebar.info(
                f"No saved files for **{platform}**. Fetch from API first to create files."
            )

    if data_source == "Load from Database" and st.session_state.get("db_service"):
        st.sidebar.markdown("---")
        st.sidebar.caption("Configure date range and limit in the main area.")

    # Initialize session state
    if "posts_data" not in st.session_state:
        st.session_state.posts_data = None
    if "selected_post_idx" not in st.session_state:
        st.session_state.selected_post_idx = None

    # Store analysis preferences in session state
    st.session_state.use_phrase_analysis = use_phrase_analysis
    st.session_state.use_sentiment_coloring = use_sentiment_coloring
    st.session_state.use_simple_wordcloud = use_simple_wordcloud
    # st.session_state.use_entity_extraction = use_entity_extraction  # REMOVED (GLiNER disabled)

    # Main area - URL Input (only for API fetch)
    if data_source == "Fetch from API":
        st.header(f"{platform} Analysis")

        col1, col2 = st.columns([3, 1])
        with col1:
            url = st.text_input(
                f"Enter {platform} URL:",
                placeholder=f"https://www.{platform.lower()}.com/...",
                help=f"Paste the URL of the {platform} page/profile/channel",
            )

        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            analyze_button = st.button("🔍 Analyze", type="primary")
    else:
        # Load from File or Load from Database
        if data_source == "Load from Database":
            st.header(f"{platform} Analysis - Load from Database")
            days_back = st.slider(
                "Days of history", 1, 365, 30, help="Load posts from the last N days"
            )
            max_posts_db = st.slider(
                "Maximum posts to load", 10, 1000, 100, help="Cap the number of posts to load"
            )
            if st.session_state.get("db_service") and st.button(
                "📊 Load from Database", type="primary"
            ):
                posts_data = load_data_from_database(
                    platform, days_back=days_back, limit=max_posts_db
                )
                if posts_data:
                    st.session_state.posts_data = normalize_posts_to_schema(posts_data)
                    st.rerun()
            analyze_button = False
            url = ""
        else:
            st.header(f"{platform} Analysis - Loaded from File")
            analyze_button = False
            url = ""

    # Refresh button
    if st.session_state.posts_data is not None:
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.session_state.posts_data = None
            st.session_state.selected_post_idx = None
            st.rerun()

    # Process analysis
    if analyze_button:
        if not url:
            show_warning("Please enter a URL to analyze", "URL Required")
            st.stop()

        if not validate_url(url, platform):
            show_warning(
                f"Invalid {platform} URL format. Please check and try again.", "Invalid URL"
            )
            st.stop()

        # ═══════════════════════════════════════════════════════════
        # DATA FETCHING WITH LOADING STATES
        # ═══════════════════════════════════════════════════════════

        data_placeholder = st.empty()

        try:
            # Fetch data
            with data_placeholder.container():
                show_loading_dots(f"Fetching data from {platform}...")

            raw_data = fetch_apify_data(platform, url, apify_token, max_posts, from_date, to_date)

            if not raw_data:
                data_placeholder.empty()
                show_empty_state(
                    icon="📭",
                    title="No Data Found",
                    message=f"No posts were found for this {platform} page/profile in the specified date range.",
                )
                st.stop()

            # Process and normalize data
            with data_placeholder.container():
                show_progress_bar(0.6, "Processing and normalizing data...")

            # Normalize and save data
            with data_placeholder.container():
                show_progress_bar(0.9, "Normalizing and saving data...")

            # Phase 1: Normalize posts (without comment fetching)
            normalized_data = normalize_post_data(raw_data, platform)

            # Clear loading indicators
            data_placeholder.empty()

            # Show success message
            show_success(
                f"Successfully processed {len(normalized_data)} posts from {platform}",
                "Data Loaded Successfully",
            )

        except Exception as e:
            data_placeholder.empty()
            ErrorHandler.handle_api_error(e, platform)
            st.stop()

        # ═══════════════════════════════════════════════════════════
        # INSTAGRAM WORKFLOW - STEP 2: FETCH COMMENTS (Second Actor)
        # ═══════════════════════════════════════════════════════════
        # Phase 2: Fetch detailed comments if requested (Facebook and Instagram)
        if fetch_detailed_comments:
            if platform == "Facebook":
                st.info(
                    "💡 Note: Facebook Comments Scraper may have limitations. If it fails, the app will continue with post data only."
                )
                try:
                    if comment_method == "Batch Processing":
                        st.info("🚀 Using batch processing for comment extraction...")
                        normalized_data = fetch_comments_for_posts_batch(
                            normalized_data, apify_token, max_comments_per_post
                        )
                    else:
                        st.info("🔄 Using individual post processing for comment extraction...")
                        normalized_data = fetch_comments_for_posts(
                            normalized_data, apify_token, max_comments_per_post
                        )
                except Exception as e:
                    st.error(f"❌ Failed to fetch Facebook comments: {str(e)}")

            elif platform == "Instagram":
                st.info(
                    "💡 Note: Instagram Comments Scraper will extract comments from all posts. This may take some time."
                )
                try:
                    # ─────────────────────────────────────────────────────
                    # Extract post URLs from already-fetched posts (Step 1)
                    # ─────────────────────────────────────────────────────
                    post_urls = []
                    for post in normalized_data:
                        if post.get("post_id"):
                            # Construct Instagram post URL from shortCode
                            short_code = post.get("post_id")
                            post_url = f"https://www.instagram.com/p/{short_code}/"
                            post_urls.append(post_url)

                    if post_urls:
                        st.info(
                            f"🔄 Found {len(post_urls)} Instagram posts to extract comments from..."
                        )
                        # ─────────────────────────────────────────────────────
                        # Call second actor: Instagram Comments Scraper
                        # ─────────────────────────────────────────────────────
                        comments_data = scrape_instagram_comments_batch(
                            post_urls, apify_token, 25
                        )  # Use 25 comments per post

                        if comments_data:
                            # ─────────────────────────────────────────────────────
                            # Assign comments back to their respective posts
                            # ─────────────────────────────────────────────────────
                            normalized_data = assign_instagram_comments_to_posts(
                                normalized_data, comments_data
                            )
                            st.success(
                                f"✅ Successfully assigned {len(comments_data)} comments to posts"
                            )
                        else:
                            st.warning("⚠️ No Instagram comments were extracted")
                    else:
                        st.warning("⚠️ No Instagram post URLs found for comment extraction")

                except Exception as e:
                    st.error(f"❌ Failed to fetch Instagram comments: {str(e)}")
                    st.warning(
                        "⚠️ Continuing without detailed comments. You can uncheck 'Fetch Detailed Comments' to skip this step."
                    )
                    # Continue with the posts without comments

        # Count total comments fetched
        total_comments = 0
        for post in normalized_data:
            comments_list = post.get("comments_list", [])
            if isinstance(comments_list, list):
                total_comments += len(comments_list)

        st.info(
            f"✅ Final result: {len(normalized_data)} posts with {total_comments} total comments"
        )

        # Save: to database + files when DB connected, else files only
        if st.session_state.get("db_service"):
            save_result = save_data_to_database(raw_data, normalized_data, platform, url, max_posts)
            if save_result:
                st.success("✅ Data saved successfully!")
                if save_result.get("job_id"):
                    st.info("🗄️ **Database:** Saved to MongoDB")
                    kpi_cards(
                        [
                            {
                                "label": "Posts Saved",
                                "value": str(save_result.get("total_posts", 0)),
                                "color_key": "default",
                            },
                            {
                                "label": "Comments Saved",
                                "value": str(save_result.get("total_comments", 0)),
                                "color_key": "comments",
                            },
                            {
                                "label": "Job ID",
                                "value": (save_result.get("job_id", "") or "")[:8] + "…"
                                if save_result.get("job_id")
                                else "—",
                                "color_key": "default",
                            },
                        ],
                        columns=3,
                    )
                if save_result.get("json_path"):
                    st.info(f"📄 Raw JSON: `{save_result.get('json_path')}`")
                    st.info(f"📊 Processed CSV: `{save_result.get('csv_path')}`")
                    if save_result.get("comments_path"):
                        st.info(f"💬 Comments CSV: `{save_result.get('comments_path')}`")
        else:
            with st.spinner("💾 Saving data to files..."):
                json_path, csv_path, comments_csv_path = save_data_to_files(
                    raw_data, normalized_data, platform
                )
            if json_path and csv_path:
                st.success("✅ Data saved successfully!")
                st.info(f"📄 Raw JSON: `{json_path}`")
                st.info(f"📊 Processed CSV: `{csv_path}`")
                if comments_csv_path:
                    st.info(f"💬 Comments CSV: `{comments_csv_path}`")
            else:
                st.warning("⚠️ Failed to save data to files")

        # Data range filter
        st.caption("Data range")
        filter_option = st.radio(
            "Choose data range:",
            ["Show All Posts", "Current Month Only"],
            help="Show all fetched posts or limit to current month only",
            label_visibility="collapsed",
            key="filter_data_range",
        )

        if filter_option == "Current Month Only":
            current_month_posts = filter_current_month(normalized_data)
            st.info(f"Current month posts: {len(current_month_posts)} items")

            if not current_month_posts:
                st.warning("No posts found for the current month.")
                st.info("This could be because:")
                st.info("1. The posts are from a different month")
                st.info("2. The date field mapping is incorrect")
                st.info("3. The date format is not being parsed correctly")

                # Debug option: Show all posts regardless of month
                if st.button("🔍 Show All Posts Instead"):
                    st.session_state.posts_data = normalized_data
                    st.success(f"✅ Showing all {len(normalized_data)} posts")
                    st.rerun()
                st.stop()

            st.session_state.posts_data = current_month_posts
            st.success(f"✅ Fetched {len(current_month_posts)} posts from current month")
        else:
            st.session_state.posts_data = normalized_data
            st.success(f"✅ Showing all {len(normalized_data)} posts")

    # Display results
    if st.session_state.posts_data:
        section_divider()
        posts = st.session_state.posts_data
        df = pd.DataFrame(posts)

        # Optimized: vectorized operations for better performance
        numeric_cols = ["likes", "comments_count", "shares_count"]
        df[numeric_cols] = (
            df[numeric_cols].apply(pd.to_numeric, errors="coerce").fillna(0).astype(int)
        )
        df["text"] = df["text"].fillna("").astype(str)
        # Platform-aware engagement (Facebook = sum reactions + comments + shares)
        df["engagement"] = [get_post_engagement(p, platform) for p in posts]

        # Date range from actual data (show "Posts from X to Y")
        date_range_str = _get_posts_date_range_str(posts)
        if date_range_str:
            st.caption(f"📅 **Data range:** {date_range_str}")

        # ═══════════════════════════════════════════════════════════
        # INSTAGRAM WORKFLOW - STEP 3: SHOW MONTHLY OVERVIEW
        # ═══════════════════════════════════════════════════════════
        st.markdown("### 📈 Monthly Overview")
        now = datetime.now()
        month_year = now.strftime("%B %Y")
        st.caption(f"Analysis period: {month_year}")
        st.markdown("---")

        # Platform-specific analysis (reactions_breakdown used in Overview tab)
        reactions_breakdown = {}
        if platform == "Instagram":
            # Single insight path for Instagram: avoid duplicated monthly-insight sections.
            create_instagram_monthly_analysis(posts, platform)
        elif platform == "YouTube":
            # YouTube Two-Step Analysis: Channel Scraper + Comments Scraper
            youtube_metrics = calculate_youtube_metrics(posts)
            window_days = 7
            views_delta = _compute_delta_pct(
                posts, lambda items: sum(p.get("views", 0) for p in items), window_days
            )
            likes_delta = _compute_delta_pct(
                posts, lambda items: sum(p.get("likes", 0) for p in items), window_days
            )
            comments_delta = _compute_delta_pct(
                posts, lambda items: sum(p.get("comments_count", 0) for p in items), window_days
            )
            engagement_delta = _compute_delta_pct(
                posts,
                lambda items: calculate_youtube_metrics(items).get("engagement_rate", 0.0),
                window_days,
            )

            # Keep high-signal KPI set for faster executive scanning.
            kpi_cards(
                [
                    {
                        "label": "Total Views",
                        "value": f"{youtube_metrics.get('total_views', 0):,}",
                        "color_key": "views",
                        "help_text": _delta_suffix(views_delta, window_days),
                    },
                    {
                        "label": "Total Likes",
                        "value": f"{youtube_metrics.get('total_likes', 0):,}",
                        "color_key": "likes",
                        "help_text": _delta_suffix(likes_delta, window_days),
                    },
                    {
                        "label": "Total Comments",
                        "value": f"{youtube_metrics.get('total_comments', 0):,}",
                        "color_key": "comments",
                        "help_text": _delta_suffix(comments_delta, window_days),
                    },
                    {
                        "label": "Engagement Rate",
                        "value": f"{youtube_metrics.get('engagement_rate', 0):.2f}%",
                        "color_key": "engagement",
                        "help_text": _delta_suffix(engagement_delta, window_days),
                    },
                ]
            )

            # Step 2: Extract comments from videos if enabled
            if fetch_detailed_comments:
                st.markdown("#### 💬 Comments Analysis")
                st.info("🔄 **Step 2:** Extracting comments from videos...")

                # Extract video URLs from posts
                video_urls = [post.get("url") for post in posts if post.get("url")]
                video_urls = [url for url in video_urls if url]  # Remove empty URLs

                if video_urls:
                    st.write(f"Found {len(video_urls)} videos to analyze for comments")

                    # Fetch comments from all videos
                    with st.spinner("Fetching comments from videos..."):
                        all_comments = fetch_youtube_comments(video_urls, apify_token, max_posts)

                    if all_comments:
                        st.success(f"✅ Successfully fetched {len(all_comments)} comments")

                        # Display comment metrics
                        total_comment_likes = sum(
                            comment.get("voteCount", 0) for comment in all_comments
                        )
                        unique_comment_authors = len(
                            set(
                                comment.get("author", "")
                                for comment in all_comments
                                if comment.get("author")
                            )
                        )

                        kpi_cards(
                            [
                                {
                                    "label": "Total Comments",
                                    "value": f"{len(all_comments):,}",
                                    "color_key": "comments",
                                },
                                {
                                    "label": "Comment Likes",
                                    "value": f"{total_comment_likes:,}",
                                    "color_key": "likes",
                                },
                                {
                                    "label": "Unique Authors",
                                    "value": f"{unique_comment_authors:,}",
                                    "color_key": "default",
                                },
                                {
                                    "label": "Avg Likes/Comment",
                                    "value": f"{total_comment_likes / len(all_comments):.1f}"
                                    if all_comments
                                    else "0",
                                    "color_key": "engagement",
                                },
                            ]
                        )

                        # Comments word cloud
                        st.markdown("#### 📊 Comments Word Cloud")
                        comment_texts = [
                            comment.get("comment", "")
                            for comment in all_comments
                            if comment.get("comment")
                        ]
                        if comment_texts:
                            st.write(f"Analyzing {len(comment_texts)} comments...")
                            create_wordcloud(comment_texts, section_key="yt_video_comments")
                        else:
                            st.info("No comment text available for word cloud.")
                    else:
                        st.warning("No comments found for the videos.")
                else:
                    st.warning("No video URLs found to extract comments from.")
            else:
                st.info(
                    "💡 **Tip:** Enable 'Fetch Detailed Comments' to analyze comments from the videos."
                )
        else:
            # Facebook analysis
            total_reactions = calculate_total_reactions(posts)
            total_comments = df["comments_count"].sum()
            total_shares = df["shares_count"].sum()
            avg_engagement = calculate_average_engagement(posts, platform)
            window_days = 7
            reactions_delta = _compute_delta_pct(posts, calculate_total_reactions, window_days)
            comments_delta = _compute_delta_pct(
                posts, lambda items: sum(p.get("comments_count", 0) for p in items), window_days
            )
            shares_delta = _compute_delta_pct(
                posts, lambda items: sum(p.get("shares_count", 0) for p in items), window_days
            )
            engagement_delta = _compute_delta_pct(
                posts,
                lambda items: calculate_average_engagement(items, platform) if items else 0.0,
                window_days,
            )

            # Calculate detailed reactions breakdown
            reactions_breakdown = {}
            for post in posts:
                reactions = post.get("reactions", {})
                if isinstance(reactions, dict):
                    for reaction_type, count in reactions.items():
                        reactions_breakdown[reaction_type] = (
                            reactions_breakdown.get(reaction_type, 0) + count
                        )

            # KPI row: consistent cards (reactions, comments, shares, engagement)
            kpi_cards(
                [
                    {
                        "label": "Total Reactions",
                        "value": f"{total_reactions:,}",
                        "help_text": f"Sum of all reaction types. {_delta_suffix(reactions_delta, window_days)}",
                        "color_key": "reactions",
                    },
                    {
                        "label": "Total Comments",
                        "value": f"{total_comments:,}",
                        "help_text": f"Total comments across all posts. {_delta_suffix(comments_delta, window_days)}",
                        "color_key": "comments",
                    },
                    {
                        "label": "Total Shares",
                        "value": f"{total_shares:,}",
                        "help_text": f"Total shares across all posts. {_delta_suffix(shares_delta, window_days)}",
                        "color_key": "shares",
                    },
                    {
                        "label": "Avg Engagement",
                        "value": f"{avg_engagement:.1f}",
                        "help_text": f"Average engagement per post. {_delta_suffix(engagement_delta, window_days)}",
                        "color_key": "engagement",
                    },
                ]
            )

            # Reactions breakdown moved to Overview tab

        insights_list = _compute_insights(posts, platform, reactions_breakdown)
        if insights_list:
            st.markdown("### 💡 Insights")
            for msg in insights_list:
                st.markdown(f"- {msg}")

        st.markdown("---")

        # Cross-platform data for Overview tab (and comparison)
        saved_files = get_saved_files()
        all_platforms_data = {platform: posts}
        for other_platform in ["Facebook", "Instagram", "YouTube"]:
            if other_platform != platform and other_platform in saved_files:
                platform_files = saved_files[other_platform]
                if platform_files:
                    try:
                        loaded_data = load_data_from_file(platform_files[0])
                        if loaded_data:
                            all_platforms_data[other_platform] = loaded_data
                    except Exception:
                        pass

        all_comments = aggregate_all_comments(posts)

        tab_overview, tab_trends, tab_audience, tab_posts, tab_export = st.tabs(
            ["📊 Overview", "📈 Trends", "💡 Audience", "📝 Posts", "📤 Export"]
        )

        with tab_overview:
            if reactions_breakdown and platform != "Instagram":
                st.markdown("### 😊 Reactions Breakdown")
                create_reaction_donut_with_summary(reactions_breakdown)
            # Compare with previous run (same platform, saved file)
            platform_files = saved_files.get(platform, [])
            if platform_files:
                st.markdown("### 📊 Compare with previous run")
                compare_options = ["(none)"] + [os.path.basename(f) for f in platform_files[:5]]
                compare_choice = st.selectbox(
                    "Load a saved run to compare",
                    compare_options,
                    help="Select a previously saved file to compare metrics with this run.",
                )
                if compare_choice and compare_choice != "(none)":
                    compare_path = next(
                        (f for f in platform_files if os.path.basename(f) == compare_choice), None
                    )
                    if compare_path:
                        prev_posts = load_data_from_file(compare_path)
                        if prev_posts:
                            cur_r = calculate_total_reactions(posts)
                            prev_r = calculate_total_reactions(prev_posts)
                            cur_c = sum(p.get("comments_count", 0) for p in posts)
                            prev_c = sum(p.get("comments_count", 0) for p in prev_posts)
                            cur_s = sum(p.get("shares_count", 0) for p in posts)
                            prev_s = sum(p.get("shares_count", 0) for p in prev_posts)
                            cur_eng = calculate_average_engagement(posts, platform)
                            prev_eng = calculate_average_engagement(prev_posts, platform)

                            def _pct(a: float, b: float) -> str:
                                if not b:
                                    return "—"
                                return f"{((a - b) / b) * 100:+.1f}%"

                            st.caption("Current run vs selected saved run.")
                            comp_df = pd.DataFrame(
                                {
                                    "Metric": [
                                        "Total Reactions",
                                        "Total Comments",
                                        "Total Shares",
                                        "Avg Engagement",
                                    ],
                                    "Current": [cur_r, cur_c, cur_s, f"{cur_eng:.1f}"],
                                    "Previous": [prev_r, prev_c, prev_s, f"{prev_eng:.1f}"],
                                    "Change": [
                                        _pct(cur_r, prev_r),
                                        _pct(cur_c, prev_c),
                                        _pct(cur_s, prev_s),
                                        _pct(cur_eng, prev_eng),
                                    ],
                                }
                            )
                            st.dataframe(comp_df, use_container_width=True, hide_index=True)
                        else:
                            st.warning("Could not load the selected file.")
            if len(all_platforms_data) > 1:
                st.markdown("### 🔄 Cross-Platform Comparison")
                st.caption(f"Benchmarking across {len(all_platforms_data)} platforms.")
                create_performance_comparison(
                    facebook_posts=all_platforms_data.get("Facebook"),
                    instagram_posts=all_platforms_data.get("Instagram"),
                    youtube_posts=all_platforms_data.get("YouTube"),
                )
            if not reactions_breakdown and len(all_platforms_data) <= 1 and not platform_files:
                st.caption(
                    "KPIs and reactions are above. Add more platform data or save runs to see comparison here."
                )

        with tab_trends:
            st.markdown("### 📈 Trends")
            st.caption("Volume and engagement over time.")
            create_monthly_overview_charts(df)
            create_engagement_over_time_chart(df)

        with tab_audience:
            st.markdown("### 💡 Audience Breakdown")
            if all_comments:
                st.caption("Topic, keyword, and sentiment drivers from comment text.")
                create_advanced_nlp_dashboard(all_comments)
                st.markdown("---")
                st.markdown("#### 🧭 Top Themes in Content")
                create_wordcloud(
                    all_comments,
                    width=1200,
                    height=600,
                    figsize=(15, 8),
                    section_key="audience_breakdown",
                )
                st.markdown("---")
                create_sentiment_themes_view(all_comments, top_n=15)
            else:
                posts_with_comments = sum(1 for post in posts if post.get("comments_count", 0) > 0)
                st.info(
                    "**No comment text available for audience insights.** "
                    "To see topics, keywords, and sentiment: enable **Fetch detailed comments** in the sidebar and run the analysis again."
                )
                if posts_with_comments:
                    st.caption(
                        f"{posts_with_comments:,} posts have comment counts but no comment text was fetched."
                    )

        with tab_posts:
            st.caption(
                "Sorted by engagement so you can spot top posts. Click a row to explore; use the selector below for full post analysis."
            )
            engagement_list = [get_post_engagement(p, platform) for p in posts]
            display_df = df[
                ["published_at", "text", "likes", "comments_count", "shares_count"]
            ].copy()
            display_df["engagement"] = engagement_list
            display_df["rank"] = (
                pd.Series(engagement_list).rank(method="min", ascending=False).astype(int)
            )
            display_df["text"] = display_df["text"].str[:100] + "..."

            def _safe_published_at(val):
                if isinstance(val, (int, float)) and val != 0:
                    return parse_published_at(val)
                return val

            display_df["published_at"] = display_df["published_at"].apply(_safe_published_at)
            display_df["published_at"] = pd.to_datetime(
                display_df["published_at"], utc=True
            ).dt.tz_localize(None)
            display_df["published_at"] = (
                display_df["published_at"].dt.strftime("%Y-%m-%d %H:%M").fillna("Unknown")
            )
            display_df = display_df.sort_values("engagement", ascending=False)[
                [
                    "published_at",
                    "rank",
                    "engagement",
                    "text",
                    "likes",
                    "comments_count",
                    "shares_count",
                ]
            ]
            display_df.columns = [
                "Date",
                "Rank",
                "Engagement",
                "Caption",
                "Likes",
                "Comments",
                "Shares",
            ]
            st.dataframe(display_df, use_container_width=True, height=300)
            st.markdown("---")
            selected_post = create_enhanced_post_selector(posts, platform)

        with tab_export:
            create_comprehensive_export_section(posts, platform, date_range_str=date_range_str)

        if selected_post:
            st.markdown("---")
            st.markdown("### 🔍 Post Details")

            # Post info
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown(f"**Caption:** {selected_post['text']}")
                # Robustly format published_at regardless of original type (str, datetime, Timestamp, None)
                pub_date = _to_naive_dt(selected_post.get("published_at"))
                pub_date_display = pub_date.strftime("%Y-%m-%d %H:%M") if pub_date else "Unknown"
                st.markdown(f"**Published:** {pub_date_display}")

            with col2:
                if platform == "Instagram":
                    # Instagram-specific metrics
                    st.metric("Likes", selected_post["likes"])
                    st.metric("Comments", selected_post["comments_count"])
                    if selected_post.get("type"):
                        st.metric("Type", selected_post["type"])
                elif platform == "YouTube":
                    # YouTube Video-specific metrics
                    st.metric("Views", f"{selected_post.get('views', 0):,}")
                    st.metric("Likes", f"{selected_post.get('likes', 0):,}")
                    st.metric("Comments", f"{selected_post.get('comments_count', 0):,}")
                    if selected_post.get("duration"):
                        st.metric("Duration", selected_post["duration"])
                else:
                    # Facebook metrics
                    st.metric("Shares", selected_post["shares_count"])
                    st.metric("Comments", selected_post["comments_count"])

            # Enhanced performance analytics
            st.markdown("---")
            create_post_performance_analytics(selected_post, posts, platform)

            # Enhanced comment analytics
            st.markdown("---")
            create_comment_analytics(selected_post, platform)

            # Platform-specific additional details
            st.markdown("---")
            st.markdown("### 📋 Additional Details")

            if platform == "Instagram":
                col1, col2 = st.columns(2)

                with col1:
                    if selected_post.get("hashtags"):
                        st.markdown("#### #️⃣ Hashtags")
                        hashtags = selected_post["hashtags"]
                        if isinstance(hashtags, list) and hashtags:
                            st.write(", ".join([f"#{tag}" for tag in hashtags]))
                        else:
                            st.info("No hashtags found")

                    if selected_post.get("mentions"):
                        st.markdown("#### 👥 Mentions")
                        mentions = selected_post["mentions"]
                        if isinstance(mentions, list) and mentions:
                            st.write(", ".join([f"@{mention}" for mention in mentions]))
                        else:
                            st.info("No mentions found")

                with col2:
                    if selected_post.get("ownerUsername"):
                        st.markdown("#### 👤 Post Owner")
                        st.write(f"**Username:** @{selected_post['ownerUsername']}")
                        if selected_post.get("ownerFullName"):
                            st.write(f"**Full Name:** {selected_post['ownerFullName']}")

                    if selected_post.get("displayUrl"):
                        st.markdown("#### 🖼️ Media")
                        st.image(selected_post["displayUrl"], width=300)

            elif platform == "YouTube":
                col1, col2 = st.columns(2)

                with col1:
                    if selected_post.get("channel"):
                        st.markdown("#### � Channel Information")
                        st.write(f"**Channel:** {selected_post['channel']}")
                        if selected_post.get("channel_username"):
                            st.write(f"**Username:** {selected_post['channel_username']}")
                        if selected_post.get("subscriber_count"):
                            st.write(f"**Subscribers:** {selected_post['subscriber_count']:,}")

                    if selected_post.get("url"):
                        st.markdown("#### 🔗 Video Link")
                        st.markdown(f"[Watch on YouTube]({selected_post['url']})")

                with col2:
                    if selected_post.get("thumbnail_url"):
                        st.markdown("#### �️ Thumbnail")
                        st.image(selected_post["thumbnail_url"], width=400)

            else:  # Facebook
                # Facebook reactions breakdown
                reactions = selected_post.get("reactions", {})
                if isinstance(reactions, dict) and reactions:
                    st.markdown("#### � Reaction Breakdown")
                    create_reaction_pie_chart(reactions)
                else:
                    st.info("Detailed reaction data not available for this post")


if __name__ == "__main__":
    main()
