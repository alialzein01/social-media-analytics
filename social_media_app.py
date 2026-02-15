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

# Config defaults for consistency with settings
from app.config.settings import DEFAULT_MAX_POSTS, DEFAULT_MAX_COMMENTS

# Platform adapters for data normalization
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
    analyze_text_with_emoji_sentiment
)
from app.viz.nlp_viz import (
    create_advanced_nlp_dashboard,
    create_topic_modeling_view,
    create_keyword_cloud,
    create_emoji_sentiment_chart,
    create_sentiment_comparison_view
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
    create_sentiment_pie_chart,
    create_instagram_metric_cards,
    create_top_posts_chart,
    create_hashtag_chart,
    create_content_type_chart,
    create_emoji_chart
)

# Dashboard components
from app.viz.dashboards import (
    create_kpi_dashboard,
    create_trends_dashboard,
    create_cross_platform_comparison
)

# UI/UX Components
from app.styles.theme import get_custom_css
from app.styles.loading import (
    show_spinner,
    show_loading_dots,
    show_progress_bar,
    show_status_indicator,
    show_empty_state,
    show_processing_steps,
    loading_state,
    with_loading
)
from app.styles.errors import (
    ErrorHandler,
    with_error_boundary,
    show_warning,
    show_info,
    show_success,
    validate_input
)
from app.utils.export import create_comprehensive_export_section
from app.viz.dashboards import (
    create_kpi_dashboard,
    create_engagement_trend_chart,
    create_posting_frequency_chart,
    create_performance_comparison,
    create_insights_summary
)

# Post detail analysis components
from app.viz.post_details import (
    create_enhanced_post_selector,
    create_post_performance_analytics,
    create_comment_analytics
)

# Analytics engine
from app.analytics import (
    aggregate_all_comments,
    analyze_emojis_in_comments,
    calculate_total_engagement,
    analyze_hashtags
)

# ============================================================================
# CONFIGURATION
# ============================================================================

# Apify Actor Names - Using full actor names for clarity and reliability
ACTOR_CONFIG = {
    # Use the community posts scraper explicitly for Facebook posts
    # (scraper_one/facebook-posts-scraper). The app will only call this posts actor for Facebook.
    "Facebook": "scraper_one/facebook-posts-scraper",
    "Instagram": "apify/instagram-scraper",
    "YouTube": "streamers/youtube-scraper"
}

# YouTube Comments Scraper Actor (full name)
YOUTUBE_COMMENTS_ACTOR_ID = "streamers/youtube-comments-scraper"

# Actor IDs for direct calls (when needed)
ACTOR_IDS = {
    # Keep actor name/ID mapping minimal and consistent; Facebook posts use the community posts actor.
    "Facebook": "scraper_one/facebook-posts-scraper",
    "Instagram": "shu8hvrXbJbY3Eb9W",
    "YouTube": "p7UMdpQnjKmmpR21D"
}

# Facebook Comments Scraper Actor
# Try different actors if one fails
FACEBOOK_COMMENTS_ACTOR_IDS = [
    # Only use the official Apify comments scraper for Facebook comments
    "apify/facebook-comments-scraper"
]
FACEBOOK_COMMENTS_ACTOR_ID = FACEBOOK_COMMENTS_ACTOR_IDS[0]

# Instagram Comments Scraper Actor
INSTAGRAM_COMMENTS_ACTOR_IDS = [
    "apify/instagram-comment-scraper",  # Primary Instagram comments scraper
    "SbK00X0JYCPblD2wp",  # Alternative Instagram comments scraper
    "instagram-comment-scraper",
    "apify/instagram-scraper"  # Fallback to main Instagram scraper
]
INSTAGRAM_COMMENTS_ACTOR_ID = INSTAGRAM_COMMENTS_ACTOR_IDS[0]  # Start with first one

# Arabic stopwords (basic set - expand as needed)
ARABIC_STOPWORDS = {
    'في', 'من', 'إلى', 'على', 'هذا', 'هذه', 'ذلك', 'التي', 'الذي',
    'أن', 'أو', 'لا', 'نعم', 'كان', 'يكون', 'ما', 'هل', 'قد', 'لقد',
    'عن', 'مع', 'بعد', 'قبل', 'عند', 'كل', 'بين', 'حتى', 'لكن', 'ثم',
    'و', 'أو', 'لم', 'لن', 'إن', 'أن', 'كما', 'لماذا', 'كيف', 'أين',
    'متى', 'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'
}

# Arabic text processing constants (pre-compiled for performance)
ARABIC_LETTERS = r"\u0621-\u064A\u0660-\u0669"
TOKEN_RE = re.compile(fr"[{ARABIC_LETTERS}A-Za-z0-9]+", re.UNICODE)
ARABIC_DIACRITICS = re.compile("""
        ّ    | # Tashdid
        َ    | # Fatha
        ً    | # Tanwin Fath
        ُ    | # Damma
        ٌ    | # Tanwin Damm
        ِ    | # Kasra
        ٍ    | # Tanwin Kasr
        ْ    | # Sukun
        ـ     # Tatwil/Kashida
    """, re.VERBOSE)
URL_PATTERN = re.compile(r'http\S+|www\S+')
MENTION_HASHTAG_PATTERN = re.compile(r'[@#]')

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
    text = ARABIC_DIACRITICS.sub('', text)
    text = URL_PATTERN.sub('', text)
    text = MENTION_HASHTAG_PATTERN.sub('', text)
    # Remove extra whitespace (optimized)
    text = ' '.join(text.split())

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
    all_text = ' '.join(comments)

    # Clean the text more thoroughly
    # Remove URLs, mentions, hashtags for better keyword extraction
    cleaned_text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', all_text)
    cleaned_text = re.sub(r'@\w+', '', cleaned_text)  # Remove mentions
    cleaned_text = re.sub(r'#\w+', '', cleaned_text)  # Remove hashtags
    cleaned_text = re.sub(r'[^\w\s]', ' ', cleaned_text)  # Remove special characters except spaces

    # Tokenize with improved regex
    tokens = re.findall(r'\b\w+\b', cleaned_text.lower())

    # Enhanced filtering
    # Common English stopwords
    english_stopwords = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
        'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
        'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those',
        'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their'
    }

    # Combine Arabic and English stopwords
    all_stopwords = ARABIC_STOPWORDS.union(english_stopwords)

    # Filter tokens
    filtered_tokens = [
        t for t in tokens
        if len(t) > 2 and
        t not in all_stopwords and
        not t.isdigit() and
        not t.startswith('www') and
        not t.startswith('http')
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
        return 'neutral'

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
            'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'awesome', 'love', 'like', 'best',
            'perfect', 'beautiful', 'nice', 'cool', 'brilliant', 'outstanding', 'superb', 'magnificent',
            'thank', 'thanks', 'appreciate', 'wow', 'incredible', 'fabulous', 'marvelous', 'splendid',
            # Arabic positive words
            'جيد', 'ممتاز', 'رائع', 'حلو', 'جميل', 'عظيم', 'مذهل', 'مثالي', 'أفضل', 'شكرا', 'شكر',
            # Emojis
            '😊', '😄', '😃', '😁', '😍', '🥰', '😘', '❤️', '💕', '💖', '💗', '💝', '👍', '👏', '🎉', '✨', '🌟', '💫'
        }

        # Enhanced negative indicators
        negative_indicators = {
            # English words
            'bad', 'terrible', 'awful', 'horrible', 'hate', 'dislike', 'worst', 'disgusting', 'ugly', 'stupid',
            'annoying', 'boring', 'disappointing', 'frustrating', 'angry', 'sad', 'depressed', 'upset',
            'no', 'not', 'never', 'hate', 'disgusting', 'awful', 'terrible', 'horrible',
            # Arabic negative words
            'سيء', 'سئ', 'فظيع', 'مقرف', 'كراهية', 'أسوأ', 'قبيح', 'غبي', 'ممل', 'محبط', 'لا', 'ليس',
            # Emojis
            '😢', '😭', '😡', '😠', '😞', '😔', '😕', '👎', '💔', '😤', '🤬', '😒', '😑'
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

def normalize_post_data(raw_data: List[Dict], platform: str, apify_token: str = None) -> List[Dict]:
    """
    Normalize actor response using new platform adapters.
    This is a wrapper that maintains backward compatibility.
    """
    if not apify_token:
        # Try Streamlit secrets first, then environment variable
        try:
            if hasattr(st, 'secrets') and 'APIFY_TOKEN' in st.secrets:
                apify_token = st.secrets['APIFY_TOKEN']
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
    month_end = (month_start + pd.offsets.MonthEnd(1))
    out = []
    for p in posts:
        d = p.get('published_at')
        d = pd.to_datetime(d, errors="coerce")
        if pd.isna(d):
            continue
        if month_start <= d <= month_end:
            out.append(p)
    return out

def calculate_total_reactions(posts: List[Dict]) -> int:
    """Calculate total reactions across all posts."""
    # Optimized: use generator expression and sum()
    return sum(
        sum(reactions.values()) if isinstance(reactions, dict)
        else reactions if isinstance(reactions, int)
        else 0
        for post in posts
        for reactions in [post.get('reactions', {})]
    )

def calculate_average_engagement(posts: List[Dict]) -> float:
    """Calculate average engagement per post (reactions/likes + comments + shares).

    NOTE: reactions and likes are NOT double-counted:
    - If reactions dict exists, use that (it includes all reaction types)
    - Otherwise, fall back to likes field
    """
    if not posts:
        return 0.0

    # Optimized: use generator expression with helper function
    def get_numeric_value(value, default=0):
        if isinstance(value, list):
            return len(value)
        elif isinstance(value, (int, float)):
            return value
        elif isinstance(value, dict):
            return sum(value.values())
        return default

    total_engagement = 0
    for post in posts:
        # Get reactions OR likes (not both to avoid double-counting)
        reactions_data = post.get('reactions', {})
        if isinstance(reactions_data, dict) and reactions_data:
            # Use detailed reactions breakdown if available
            reactions_count = sum(reactions_data.values())
        else:
            # Fall back to likes field if no reactions breakdown
            reactions_count = get_numeric_value(post.get('likes', 0))

        # Add engagement components (reactions already includes likes)
        total_engagement += (
            reactions_count +
            get_numeric_value(post.get('comments_count', 0)) +
            get_numeric_value(post.get('shares_count', 0))
        )

    return total_engagement / len(posts)

def calculate_youtube_metrics(posts: List[Dict]) -> Dict[str, Any]:
    """Calculate YouTube-specific metrics."""
    if not posts:
        return {}

    total_views = sum(post.get('views', 0) for post in posts)
    total_likes = sum(post.get('likes', 0) for post in posts)
    total_comments = sum(post.get('comments_count', 0) for post in posts)
    total_shares = sum(post.get('shares_count', 0) for post in posts)

    # Calculate average metrics
    avg_views = total_views / len(posts) if posts else 0
    avg_likes = total_likes / len(posts) if posts else 0
    avg_comments = total_comments / len(posts) if posts else 0
    avg_shares = total_shares / len(posts) if posts else 0

    # Calculate engagement rate (likes + comments + shares) / views
    total_engagement = total_likes + total_comments + total_shares
    engagement_rate = (total_engagement / total_views * 100) if total_views > 0 else 0

    return {
        'total_views': total_views,
        'total_likes': total_likes,
        'total_comments': total_comments,
        'total_shares': total_shares,
        'avg_views': avg_views,
        'avg_likes': avg_likes,
        'avg_comments': avg_comments,
        'avg_shares': avg_shares,
        'engagement_rate': engagement_rate
    }

@st.cache_data(ttl=3600, max_entries=32, show_spinner=False)
def fetch_youtube_comments(video_urls: List[str], _apify_token: str, max_comments_per_video: int = 10) -> List[Dict]:
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
            "commentsSortBy": "1"  # 1 = most relevant comments
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
                "commentsSortBy": "1"
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
        'positive': sentiment_counts.get('positive', 0),
        'negative': sentiment_counts.get('negative', 0),
        'neutral': sentiment_counts.get('neutral', 0)
    }

# ============================================================================
# FILE OPERATIONS
# ============================================================================

def save_data_to_files(raw_data: List[Dict], normalized_data: List[Dict], platform: str) -> tuple[str, str, str]:
    """
    Save raw and processed data to files using DataPersistenceService.
    Returns tuple of (json_file_path, csv_file_path, comments_csv_file_path)
    """
    try:
        # Use the new DataPersistenceService
        persistence = DataPersistenceService()
        json_path, csv_path, comments_path = persistence.save_dataset(
            raw_data=raw_data,
            normalized_data=normalized_data,
            platform=platform
        )
        return json_path, csv_path, comments_path
    except Exception as e:
        st.error(f"Error saving files: {str(e)}")
        return None, None, None

def load_data_from_file(file_path: str) -> Optional[List[Dict]]:
    """
    Load data from a saved file (JSON or CSV) using DataPersistenceService.
    Returns normalized data in the same format as from API.
    """
    try:
        # Use the new DataPersistenceService
        persistence = DataPersistenceService()
        normalized_data = persistence.load_dataset(file_path)
        return normalized_data
    except Exception as e:
        st.error(f"Error loading file: {str(e)}")
        return None


def save_data_to_files_only(raw_data: List[Dict], normalized_data: List[Dict], platform: str) -> Dict[str, Any]:
    """
    Fallback: Save data to files only (no database).
    Returns dict with file paths for consistent UI.
    """
    try:
        persistence = DataPersistenceService()
        json_path, csv_path, comments_path = persistence.save_dataset(
            raw_data=raw_data,
            normalized_data=normalized_data,
            platform=platform
        )
        return {
            'json_path': json_path,
            'csv_path': csv_path,
            'comments_path': comments_path,
            'total_posts': len(normalized_data),
            'total_comments': sum(len(p.get('comments_list', []) or []) for p in normalized_data if isinstance(p.get('comments_list'), list))
        }
    except Exception as e:
        st.error(f"Error saving files: {str(e)}")
        return {}


def save_data_to_database(raw_data: List[Dict], normalized_data: List[Dict], platform: str, url: str, max_posts: int) -> Dict[str, Any]:
    """
    Save data to MongoDB using MongoDBService, and to files as backup.
    Returns dict with job_id and statistics when DB is connected; otherwise falls back to files only.
    """
    try:
        db_service = st.session_state.get('db_service')
        if not db_service:
            st.warning("Database not initialized. Saving to files only.")
            return save_data_to_files_only(raw_data, normalized_data, platform)

        # Ensure all comments have required fields before saving
        for post in normalized_data:
            comments_list = post.get('comments_list', [])
            if isinstance(comments_list, list):
                for i, comment in enumerate(comments_list):
                    if not isinstance(comment, dict):
                        comments_list[i] = {'text': str(comment)}
                        comment = comments_list[i]

                    if 'comment_id' not in comment or not comment.get('comment_id'):
                        post_id = post.get('post_id', '')
                        comment_text = comment.get('text', '')
                        unique_string = f"{post_id}_{comment_text}_{i}_{platform}"
                        comment['comment_id'] = hashlib.md5(unique_string.encode()).hexdigest()

                    if 'text' not in comment:
                        comment['text'] = ''
                    if 'author_name' not in comment:
                        comment['author_name'] = comment.get('ownerUsername', '') or comment.get('authorDisplayName', '') or 'Unknown'
                    if 'created_time' not in comment:
                        comment['created_time'] = comment.get('timestamp', '') or comment.get('publishedAt', '') or ''
                    if 'likes_count' not in comment:
                        comment['likes_count'] = comment.get('likesCount', 0) or comment.get('likeCount', 0) or 0

        with st.spinner("💾 Saving to database..."):
            result = db_service.save_scraping_results(
                platform=platform,
                url=url,
                normalized_posts=normalized_data,
                max_posts=max_posts
            )

        persistence = DataPersistenceService()
        json_path, csv_path, comments_path = persistence.save_dataset(
            raw_data=raw_data,
            normalized_data=normalized_data,
            platform=platform
        )
        result['json_path'] = json_path
        result['csv_path'] = csv_path
        result['comments_path'] = comments_path

        return result

    except Exception as e:
        st.error(f"Error saving to database: {str(e)}")
        st.warning("Falling back to file-only storage...")
        return save_data_to_files_only(raw_data, normalized_data, platform)


def load_data_from_database(platform: str, days_back: int = 30, limit: int = 1000) -> Optional[List[Dict]]:
    """
    Load data from MongoDB for the specified platform and date range.
    Returns normalized data in the same format as from API.
    """
    try:
        db_service = st.session_state.get('db_service')
        if not db_service:
            st.warning("Database not initialized. Please use 'Load from File' option.")
            return None

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        with st.spinner(f"📊 Loading {platform} data from database..."):
            posts = db_service.get_posts_for_analysis(
                platform=platform,
                start_date=start_date,
                end_date=end_date,
                limit=limit
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
                    st.warning("⚠️ No posts matched the requested date range — showing recent posts for the platform instead.")
                for post in posts:
                    post_id = post.get('post_id')
                    if post_id:
                        comments = db_service.get_comments_for_analysis(
                            platform=platform,
                            post_id=post_id,
                            limit=500
                        )
                        post['comments_list'] = comments or []

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
        files = {
            'Facebook': [],
            'Instagram': [],
            'YouTube': []
        }

        # Optimized: combine glob patterns and use list comprehension
        all_files = glob.glob("data/raw/*.json") + glob.glob("data/processed/*.csv")

        for file_path in all_files:
            filename = os.path.basename(file_path)
            platform = filename.split('_')[0].title()
            if platform in files:
                files[platform].append(file_path)

        # Sort files by modification time (newest first) - optimized
        for platform in files:
            files[platform].sort(key=os.path.getmtime, reverse=True)

        return files

    except Exception as e:
        st.error(f"Error getting saved files: {str(e)}")
        return {'Facebook': [], 'Instagram': [], 'YouTube': []}


def extract_main_titles_from_source(file_path: str) -> List[str]:
    """
    Parse the Python source file and return a list of main UI titles.
    We consider st.title(...), st.header(...), st.markdown("##..."/"###...") and st.subheader(...)
    as main titles for the Table of Contents.
    """
    titles: List[str] = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
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
def fetch_apify_data(platform: str, url: str, _apify_token: str, max_posts: int = 10, from_date: str = None, to_date: str = None) -> Optional[List[Dict]]:
    """
    Fetch data from Apify actor for the given platform and URL.
    Cached for 1 hour per platform+URL combination.

    NOTE: Adjust the 'run_input' based on actual actor requirements.
    """
    try:
        client = ApifyClient(_apify_token)
        actor_name = ACTOR_CONFIG.get(platform)

        if not actor_name:
            st.error(f"No actor configured for {platform}")
            return None

        # Configure input based on platform with documented formats
        if platform == "Instagram":
            # Instagram scraper input format based on documentation
            run_input = {
                "directUrls": [url],
                "resultsType": "posts",
                "resultsLimit": max_posts,
                "searchLimit": 10  # Default search limit
            }
        elif platform == "Facebook":
            # Facebook posts actor: use the repo-configured actor_name to choose input shape.
            # The community `scraper_one/facebook-posts-scraper` expects `pageUrls` while
            # some official variants expect `startUrls`. Use the appropriate key.
            if actor_name and actor_name.startswith('scraper_one'):
                run_input = {
                    "pageUrls": [url],
                    "resultsLimit": max_posts
                }
            else:
                # Fallback to legacy startUrls shape for other actors
                run_input = {
                    "startUrls": [url],
                    "resultsLimit": max_posts
                }
            # Add date range parameters if specified (ISO format: YYYY-MM-DD or relative like "3 days ago")
            if from_date:
                run_input["onlyPostsNewerThan"] = from_date
            if to_date:
                run_input["onlyPostsOlderThan"] = to_date
        elif platform == "YouTube":
            # streamers/youtube-scraper input format
            # Use startUrls for direct channel/video URLs, searchQueries for keyword searches
            if url.startswith('http'):  # Direct URL (channel, video, playlist)
                run_input = {
                    "startUrls": [{"url": url}],
                    "maxResults": max_posts,
                    "maxResultsShorts": 0,
                    "maxResultStreams": 0,
                    "subtitlesLanguage": "en",
                    "subtitlesFormat": "srt"
                }
            else:  # Search query (keywords)
                run_input = {
                    "searchQueries": [url],
                    "maxResults": max_posts,
                    "maxResultsShorts": 0,
                    "maxResultStreams": 0,
                    "subtitlesLanguage": "en",
                    "subtitlesFormat": "srt"
                }
        else:
            run_input = {"startUrls": [{"url": url}], "maxPosts": max_posts}

        # Run the actor
        st.info(f"Calling Apify actor: {actor_name}")
        st.info(f"📊 Requesting {max_posts} posts from: {url}")
        st.info(f"🔧 Actor ID: {actor_name}")  # Debug info

        # Show date range information
        if from_date or to_date:
            date_info = "Date range: "
            if from_date:
                date_info += f"from {from_date} "
            if to_date:
                date_info += f"to {to_date}"
            st.info(f"📅 {date_info}")

        run = client.actor(actor_name).call(run_input=run_input)

        # Fetch results, respecting requested limit
        items = []
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            items.append(item)
            if len(items) >= max_posts:
                break

        st.info(f"✅ Received {len(items)} posts from actor (requested {max_posts})")
        return items

    except Exception as e:
        st.error(f"Apify API Error: {str(e)}")
        return None

@st.cache_data(ttl=3600, max_entries=256, show_spinner=False)
def fetch_post_comments(post_url: str, _apify_token: str, max_comments: int = DEFAULT_MAX_COMMENTS) -> Optional[List[Dict]]:
    """
    Fetch detailed comments for a specific Facebook post using the Comments Scraper actor.
    Tries different actors and input formats if one fails.
    Cached for 1 hour per post URL + max_comments.
    """
    # Validate URL format
    if not post_url or not post_url.startswith('http'):
        st.error(f"❌ Invalid URL format: {post_url}")
        return None

    client = ApifyClient(_apify_token)

    # Try different actors with unified input format
    # Only attempt the official Apify Facebook comments scraper.
    actor_configs = [
        {"actor_id": "apify/facebook-comments-scraper",
         "input": {"startUrls": [{"url": post_url}], "maxComments": max_comments, "includeNestedComments": False}}
    ]

    for i, config in enumerate(actor_configs):
        try:
            st.info(f"🔍 Attempt {i+1}: Using actor '{config['actor_id']}' for: {post_url}")

            # Run the actor
            run = client.actor(config["actor_id"]).call(run_input=config["input"])

            # Fetch results, respecting requested limit
            comments = []
            for item in client.dataset(run["defaultDatasetId"]).iterate_items():
                comments.append(item)
                if len(comments) >= max_comments:
                    break

            if comments:
                st.success(f"✅ Successfully fetched {len(comments)} comments using {config['actor_id']}")
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

def fetch_comments_for_posts_batch(posts: List[Dict], apify_token: str, max_comments_per_post: int = DEFAULT_MAX_COMMENTS) -> List[Dict]:
    """
    Fetch detailed comments for all Facebook posts using batch processing with the Comments Scraper actor.
    This uses the workflow where we extract all post URLs first, then batch process them for comments.
    """
    if not posts:
        return posts

    st.info(f"🔄 Starting batch comment extraction for {len(posts)} posts...")

    # Extract all post URLs
    post_urls = []
    for post in posts:
        post_url = post.get('post_url')
        if post_url and post_url.startswith('http'):
            post_urls.append({"url": post_url})

    if not post_urls:
        st.warning("⚠️ No valid post URLs found for comment extraction")
        return posts

    st.info(f"📋 Found {len(post_urls)} valid post URLs for comment extraction")

    # Prepare input for the comments scraper actor
    comments_input = {
        "startUrls": post_urls,
        "resultsLimit": max_comments_per_post,
        "includeNestedComments": False,
        "viewOption": "RANKED_UNFILTERED"
    }

    client = ApifyClient(apify_token)

    # Try different actors for comment extraction
    for i, actor_id in enumerate(FACEBOOK_COMMENTS_ACTOR_IDS):
        try:
            st.info(f"🔍 Attempt {i+1}: Using actor '{actor_id}' for batch comment extraction...")

            # Run the actor
            run = client.actor(actor_id).call(run_input=comments_input)

            # Fetch results, cap total to avoid over-reading
            max_total = len(posts) * max_comments_per_post
            comments_data = []
            for item in client.dataset(run["defaultDatasetId"]).iterate_items():
                comments_data.append(item)
                if len(comments_data) >= max_total:
                    break

            if comments_data:
                st.success(f"✅ Successfully fetched {len(comments_data)} comments using {actor_id}")

                # Process and assign comments to posts
                posts_with_comments = assign_comments_to_posts(posts, comments_data)
                return posts_with_comments
            else:
                st.warning(f"⚠️ No comments found with {actor_id}, trying next actor...")

        except Exception as e:
            st.warning(f"⚠️ Actor {actor_id} failed: {str(e)}")
            if i < len(FACEBOOK_COMMENTS_ACTOR_IDS) - 1:
                st.info("🔄 Trying next actor...")
            continue

    st.error("❌ All comment scrapers failed for batch processing")
    return posts

def assign_comments_to_posts(posts: List[Dict], comments_data: List[Dict]) -> List[Dict]:
    """
    Assign comments to their respective posts based on post URL matching.
    """
    # Create a mapping of post URLs to posts
    post_url_map = {}
    for post in posts:
        post_url = post.get('post_url')
        if post_url:
            post_url_map[post_url] = post
            post['comments_list'] = []  # Initialize empty comments list

    # DEBUG: Show what we're working with
    st.write(f"🔍 DEBUG: Have {len(post_url_map)} post URLs")
    st.write(f"🔍 DEBUG: Have {len(comments_data)} comments to assign")
    if post_url_map:
        st.write("🔍 DEBUG: Sample post URL:", list(post_url_map.keys())[0][:80])
    if comments_data:
        sample_comment = comments_data[0]
        comment_url = sample_comment.get('url') or sample_comment.get('postUrl') or sample_comment.get('facebookUrl')
        st.write(f"🔍 DEBUG: Sample comment URL field: {comment_url[:80] if comment_url else 'NONE'}")
        st.write(f"🔍 DEBUG: Sample comment keys: {list(sample_comment.keys())}")

    # Assign comments to posts
    assigned_comments = 0
    unmatched_comments = 0

    for comment in comments_data:
        # Try to find the post this comment belongs to
        comment_url = comment.get('url') or comment.get('postUrl') or comment.get('facebookUrl')

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
                    post['comments_list'].append(normalized_comment)
                    assigned_comments += 1
                    matched = True
                    break

        if not matched:
            unmatched_comments += 1

    st.info(f"📊 Assigned {assigned_comments} comments to {len(posts)} posts")
    if unmatched_comments > 0:
        st.warning(f"⚠️ {unmatched_comments} comments could not be matched to posts")
    return posts

def fetch_comments_for_posts(posts: List[Dict], apify_token: str, max_comments_per_post: int = DEFAULT_MAX_COMMENTS) -> List[Dict]:
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
        status_text.text(f"Fetching comments for post {i+1}/{len(posts)}: {post.get('post_id', 'Unknown')}")

        # Check if we need to fetch comments
        comments_list = post.get('comments_list', [])
        should_fetch = (
            not comments_list or
            (isinstance(comments_list, list) and len(comments_list) == 0) or
            isinstance(comments_list, int)  # If it's an int, it's a count, not actual comments
        )

        if should_fetch and post.get('post_url'):
            try:
                # Add rate limiting delay (2 seconds between calls)
                if i > 0:  # Skip delay for first post
                    time.sleep(2)

                # Fetch comments for this post
                raw_comments = fetch_post_comments(post['post_url'], apify_token, max_comments_per_post)
                if raw_comments:
                    # Normalize comment data
                    normalized_comments = []
                    for raw_comment in raw_comments:
                        normalized_comment = normalize_comment_data(raw_comment)
                        normalized_comments.append(normalized_comment)
                    post['comments_list'] = normalized_comments
                    st.success(f"✅ Fetched {len(normalized_comments)} comments for post {post.get('post_id', 'Unknown')}")
                else:
                    post['comments_list'] = []
                    st.warning(f"⚠️ No comments found for post {post.get('post_id', 'Unknown')}")
            except Exception as e:
                st.warning(f"❌ Failed to fetch comments for post {post.get('post_id', 'Unknown')}: {str(e)}")
                post['comments_list'] = []
        else:
            if not post.get('post_url'):
                st.warning(f"⚠️ No URL found for post {post.get('post_id', 'Unknown')}, skipping comment fetch")

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
        if 'from' in raw_comment and isinstance(raw_comment['from'], dict):
            author_name = raw_comment['from'].get('name', '')
        elif 'author' in raw_comment:
            if isinstance(raw_comment['author'], dict):
                author_name = raw_comment['author'].get('name', '')
            else:
                author_name = str(raw_comment['author'])

        # Extract comment text
        text = raw_comment.get('text', '') or raw_comment.get('message', '') or raw_comment.get('content', '')

        # Extract created time
        created_time = raw_comment.get('created_time', '') or raw_comment.get('timestamp', '') or raw_comment.get('date', '')

        # Extract likes count
        likes_count = 0
        if 'like_count' in raw_comment:
            likes_count = raw_comment['like_count']
        elif 'likes' in raw_comment:
            if isinstance(raw_comment['likes'], int):
                likes_count = raw_comment['likes']
            elif isinstance(raw_comment['likes'], list):
                likes_count = len(raw_comment['likes'])

        # Extract replies count
        replies_count = 0
        if 'comment_count' in raw_comment:
            replies_count = raw_comment['comment_count']
        elif 'replies' in raw_comment:
            if isinstance(raw_comment['replies'], int):
                replies_count = raw_comment['replies']
            elif isinstance(raw_comment['replies'], list):
                replies_count = len(raw_comment['replies'])

        normalized_comment = {
            'comment_id': raw_comment.get('id', ''),
            'text': text,
            'author_name': author_name,
            'created_time': created_time,
            'likes_count': likes_count,
            'replies_count': replies_count
        }

        return normalized_comment

    except Exception as e:
        st.warning(f"Failed to normalize comment: {str(e)}")
        return {
            'comment_id': '',
            'text': '',
            'author_name': '',
            'created_time': '',
            'likes_count': 0,
            'replies_count': 0
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
                if actor_id == INSTAGRAM_COMMENTS_ACTOR_ID:
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

    st.info(f"🔄 Starting Instagram comments extraction for {len(post_urls)} posts (concurrency: {max_workers})...")

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
                    st.success(f"✅ Extracted {len(comments_data)} comments from post ({done + 1}/{len(post_urls)} done)")
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
        post_id = comment.get('postId', '')
        if post_id:
            if post_id not in comments_by_post:
                comments_by_post[post_id] = []
            # Format comment for consistency
            formatted_comment = {
                'text': comment.get('text', ''),
                'ownerUsername': comment.get('ownerUsername', ''),
                'ownerId': comment.get('ownerId', ''),
                'timestamp': comment.get('timestamp', ''),
                'position': comment.get('position', 0),
                'ownerIsVerified': comment.get('ownerIsVerified', False),
                'ownerProfilePicUrl': comment.get('ownerProfilePicUrl', '')
            }
            comments_by_post[post_id].append(formatted_comment)

    # Assign comments to posts
    for post in posts:
        post_id = post.get('post_id', '')
        if post_id in comments_by_post:
            post['comments_list'] = comments_by_post[post_id]
            post['comments_count'] = len(comments_by_post[post_id])
        else:
            # Keep existing comments_count if no new comments found
            if 'comments_list' not in post:
                post['comments_list'] = []

    return posts

def create_monthly_overview_charts(df: pd.DataFrame):
    """Create overview charts for monthly data using Streamlit native charts."""

    # Optimized: vectorized datetime operations
    df_copy = df.copy()
    if 'published_at' in df_copy.columns:
        # Vectorized timezone conversion
        df_copy['published_at'] = pd.to_datetime(df_copy['published_at'], utc=True).dt.tz_localize(None)
        df_copy['date'] = df_copy['published_at'].dt.date
    else:
        df_copy['date'] = pd.to_datetime(df_copy['published_at']).dt.date

    posts_per_day = df_copy.groupby('date').size().reset_index(name='count')

    # Posts per day line chart
    st.subheader("📈 Posts Per Day")
    if PLOTLY_AVAILABLE:
        fig = px.line(posts_per_day, x="date", y="count", markers=True, title="Posts Per Day",
                     color_discrete_sequence=['#495E57'])
        fig.update_layout(
            plot_bgcolor='#F5F7F8',
            paper_bgcolor='#F5F7F8',
            font_color='#45474B'
        )
        st.plotly_chart(fig, width='stretch')
    else:
        st.line_chart(posts_per_day.set_index('date'))

    # Engagement comparison
    st.subheader("📊 Total Engagement Breakdown")
    engagement_data = pd.DataFrame({
        'Metric': ['Reactions/Likes', 'Comments', 'Shares'],
        'Count': [
            df['likes'].sum(),  # This is actually reactionsCount for Facebook
            df['comments_count'].sum(),
            df['shares_count'].sum()
        ]
    })
    if PLOTLY_AVAILABLE:
        fig = px.bar(engagement_data, x="Metric", y="Count", title="Total Engagement Breakdown",
                     color_discrete_sequence=['#495E57', '#F4CE14', '#45474B'])
        fig.update_layout(
            plot_bgcolor='#F5F7F8',
            paper_bgcolor='#F5F7F8',
            font_color='#45474B'
        )
        st.plotly_chart(fig, width='stretch')
    else:
        st.bar_chart(engagement_data.set_index('Metric'))

    # Top posts by engagement - optimized
    # Note: 'likes' field contains total reactions for Facebook, so no double-counting
    st.subheader("🏆 Top 5 Posts by Engagement")
    df['total_engagement'] = df['likes'] + df['comments_count'] + df['shares_count']
    top_posts = df.nlargest(5, 'total_engagement')[['text', 'total_engagement']].copy()
    top_posts['text'] = top_posts['text'].str[:50] + '...'
    if PLOTLY_AVAILABLE:
        fig = px.bar(top_posts.reset_index().rename(columns={'text':'Caption'}),
                     x="Caption", y="total_engagement", title="Top 5 Posts by Engagement",
                     color_discrete_sequence=['#495E57'])
        fig.update_layout(
            plot_bgcolor='#F5F7F8',
            paper_bgcolor='#F5F7F8',
            font_color='#45474B'
        )
        st.plotly_chart(fig, width='stretch')
    else:
        top_posts = top_posts.set_index('text')
    st.bar_chart(top_posts)

def create_reaction_pie_chart(reactions: Dict[str, int]):
    """Create reaction breakdown chart using Streamlit native charts."""
    # Filter out zero values
    reactions_filtered = {k: v for k, v in reactions.items() if v > 0}

    if not reactions_filtered:
        st.info("No reaction data available for this post")
        return

    # Create a more detailed display
    st.subheader("😊 Reaction Breakdown")

    # Show individual reaction counts with emojis
    cols = st.columns(len(reactions_filtered))
    for i, (reaction, count) in enumerate(reactions_filtered.items()):
        with cols[i]:
            # Add emoji for each reaction type
            emoji_map = {
                'like': '👍',
                'love': '❤️',
                'haha': '😂',
                'wow': '😮',
                'sad': '😢',
                'angry': '😠'
            }
            emoji = emoji_map.get(reaction, '👍')
            st.metric(f"{emoji} {reaction.title()}", count)

    # Create a bar chart for reactions
    reactions_df = pd.DataFrame(list(reactions_filtered.items()), columns=['Reaction', 'Count'])
    reactions_df = reactions_df.set_index('Reaction')
    st.bar_chart(reactions_df)

def create_wordcloud(comments: List[str], width: int = 800, height: int = 400, figsize: tuple = (10, 5)):
    """Generate and display word cloud from comments with phrase support."""
    if not comments:
        st.info("No comments available for word cloud")
        return

    # Get user preferences from session state
    use_phrase_analysis = st.session_state.get('use_phrase_analysis', True)
    use_sentiment_coloring = st.session_state.get('use_sentiment_coloring', True)
    use_simple_wordcloud = st.session_state.get('use_simple_wordcloud', False)

    # Try to use enhanced word cloud generator if available and not using simple mode
    if not use_simple_wordcloud:
        try:
            from app.viz.wordcloud_generator import create_phrase_wordcloud

            if use_phrase_analysis:
                fig, ax = create_phrase_wordcloud(
                    comments,
                    title="Comment Analysis - Phrases & Sentiment" if use_sentiment_coloring else "Comment Analysis - Phrases",
                    use_sentiment_coloring=use_sentiment_coloring,
                    language='auto'
                )

                # Check if the word cloud actually has content
                # If it shows "No meaningful content found", fall back to simple word cloud
                if hasattr(ax, 'texts') and any('No meaningful content found' in str(text.get_text()) for text in ax.texts):
                    st.warning("⚠️ Phrase analysis found no meaningful content. Falling back to simple word cloud.")
                    # Continue to fallback below
                else:
                    st.pyplot(fig)
                    return
        except ImportError:
            # Fallback to original word cloud generation
            pass
        except Exception as e:
            st.warning(f"⚠️ Enhanced word cloud failed: {str(e)}. Using fallback.")
            # Continue to fallback below

    # Original word cloud generation (fallback)
    st.info("🔄 Using simple word cloud generation...")
    keywords = extract_keywords_nlp(comments)

    if not keywords:
        st.warning("⚠️ No keywords extracted from comments")
        st.info("💡 **Possible reasons:**")
        st.info("• Comments are too short or contain only common words")
        st.info("• Comments are in a language not well supported")
        st.info("• Comments contain mostly emojis or special characters")
        st.info("• Comments may be empty or filtered out")
        st.info("• Try enabling 'Fetch Detailed Comments' to get actual comment text")

        # Show some sample comments for debugging
        if comments:
            st.info("📝 **Sample comments found:**")
            sample_comments = comments[:3]  # Show first 3 comments
            for i, comment in enumerate(sample_comments, 1):
                st.text(f"{i}. {comment[:100]}{'...' if len(comment) > 100 else ''}")
        else:
            st.info("📝 **No comments found in the data**")
        return

    # Generate word cloud with optional Arabic shaping
    wc_freqs = {_reshape_for_wc(k): v for k, v in keywords.items()}
    # Optionally set font_path if available; otherwise keep as-is
    wordcloud = WordCloud(
        width=width,
        height=height,
        background_color='#F5F7F8',  # Use theme background color
        colormap='viridis',
        relative_scaling=0.5,
        min_font_size=10
    ).generate_from_frequencies(wc_freqs)

    # Display
    fig, ax = plt.subplots(figsize=figsize, facecolor='#F5F7F8')
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    fig.patch.set_facecolor('#F5F7F8')
    st.pyplot(fig)

def create_instagram_monthly_analysis(posts: List[Dict], platform: str):
    """Create comprehensive monthly Instagram analysis using enhanced dashboard components."""
    if platform != "Instagram":
        return

    st.markdown("### 📸 Monthly Instagram Analysis")

    # Enhanced KPI Dashboard
    create_kpi_dashboard(posts, platform)

    # Engagement Trends
    st.markdown("---")
    create_engagement_trend_chart(posts)

    # Posting Frequency Analysis
    st.markdown("---")
    create_posting_frequency_chart(posts)

    # Top posts with enhanced visualization
    st.markdown("---")
    create_top_posts_chart(posts, top_n=5)

    # Content type analysis
    st.markdown("---")
    create_content_type_chart(posts)

    # Hashtag analysis
    st.markdown("---")
    create_hashtag_chart(posts, top_n=10)

    # Key Insights Summary
    st.markdown("---")
    create_insights_summary(posts, platform)

def create_instagram_monthly_insights(posts: List[Dict], platform: str):
    """Create monthly Instagram insights using new analytics and viz components."""
    if platform != "Instagram":
        return

    st.markdown("---")
    st.markdown("### 💡 Monthly Instagram Insights")

    # Use analytics module to aggregate comments
    all_comments = aggregate_all_comments(posts)

    # DEBUG: Show what we got
    st.write(f"🔍 DEBUG: aggregate_all_comments returned {len(all_comments)} comment texts")
    if posts:
        st.write(f"🔍 DEBUG: Total posts: {len(posts)}")
        posts_with_comments = sum(1 for p in posts if p.get('comments_list'))
        st.write(f"🔍 DEBUG: Posts with comments_list: {posts_with_comments}")
        if posts_with_comments > 0:
            sample_post = next(p for p in posts if p.get('comments_list'))
            st.write(f"🔍 DEBUG: Sample post has {len(sample_post.get('comments_list', []))} comments")
            if sample_post.get('comments_list'):
                st.write(f"🔍 DEBUG: Sample comment structure: {list(sample_post['comments_list'][0].keys())}")
                st.write(f"🔍 DEBUG: Sample comment text: {sample_post['comments_list'][0].get('text', 'NO TEXT')[:100]}")

    if all_comments:
        # Advanced NLP Analysis Dashboard (function adds its own title)
        create_advanced_nlp_dashboard(all_comments)

        st.markdown("---")

        # Create two columns for traditional insights
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 💬 Monthly Comments Word Cloud")
            create_wordcloud(all_comments, width=1200, height=600, figsize=(15, 8))

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
            if emoji_analysis.get('emoji_count', 0) > 0:
                st.markdown("---")
                st.markdown("#### 📊 Sentiment Comparison")
                create_sentiment_comparison_view(text_sentiment, emoji_analysis, combined_sentiment)
        except Exception as e:
            # Silently skip if sentiment comparison fails (emoji analysis already shown in dashboard)
            pass
    else:
        st.info("📊 No comment text available for monthly insights analysis")
        st.warning("💡 **To analyze comments:** Enable 'Fetch Detailed Comments' in the sidebar and re-analyze the page.")

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
    likes = selected_post.get('likes', 0)
    comments_count = selected_post.get('comments_count', 0)
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
        if selected_post.get('type'):
            st.metric("Type", selected_post['type'])

    # Comments analysis for this specific post
    comments_list = selected_post.get('comments_list', [])

    if isinstance(comments_list, list) and comments_list:
        st.markdown("#### 💬 Post Comments Analysis")

        # Extract comment texts
        comment_texts = []
        for comment in comments_list:
            if isinstance(comment, dict):
                text = comment.get('text', '')
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
                create_wordcloud(comment_texts, width=600, height=400, figsize=(10, 6))

            with col2:
                st.markdown("##### 😊 Comments Sentiment")
                sentiment_counts = analyze_all_sentiments(comment_texts)
                create_sentiment_pie_chart(sentiment_counts)

                # Show sentiment summary
                total_sentiment = sum(sentiment_counts.values())
                if total_sentiment > 0:
                    st.markdown("**Sentiment Summary:**")
                    st.markdown(f"- **Positive:** {sentiment_counts['positive']} ({sentiment_counts['positive']/total_sentiment*100:.1f}%)")
                    st.markdown(f"- **Negative:** {sentiment_counts['negative']} ({sentiment_counts['negative']/total_sentiment*100:.1f}%)")
                    st.markdown(f"- **Neutral:** {sentiment_counts['neutral']} ({sentiment_counts['neutral']/total_sentiment*100:.1f}%)")

            # Emoji analysis for this post
            st.markdown("---")
            st.markdown("##### 😀 Emojis in Post Comments")
            try:
                from app.nlp.advanced_nlp import analyze_text_emojis, analyze_text_with_emoji_sentiment
                from app.nlp.sentiment_analyzer import analyze_corpus_sentiment_phrases

                post_agg_text = " ".join([t for t in comment_texts if isinstance(t, str)])
                post_emoji_analysis = analyze_text_emojis(post_agg_text)
                post_text_sentiment = analyze_corpus_sentiment_phrases(comment_texts)
                post_combined = analyze_text_with_emoji_sentiment(post_agg_text)

                create_emoji_sentiment_chart(post_emoji_analysis)

                # Sentiment comparison
                st.markdown("---")
                create_sentiment_comparison_view(post_text_sentiment, post_emoji_analysis, post_combined)
            except Exception as e:
                st.warning(f"Post emoji sentiment section unavailable: {e}")
        else:
            st.info("No comment text available for this post's analysis")
    else:
        st.info("No comments available for this post")
        st.warning("💡 **To see post analysis:** Enable 'Fetch Detailed Comments' in the sidebar and re-analyze the page.")

def create_sentiment_pie_chart(sentiment_counts: Dict[str, int]):
    """Create sentiment distribution pie chart with custom colors."""
    if not sentiment_counts or sum(sentiment_counts.values()) == 0:
        st.info("No sentiment data available")
        return

    # Define colors using sage green palette
    colors = {
        'positive': '#495E57',  # Sage green
        'negative': '#F4CE14',  # Golden yellow
        'neutral': '#45474B'    # Dark grey
    }

    # Prepare data
    labels = []
    sizes = []
    color_list = []

    for sentiment, count in sentiment_counts.items():
        if count > 0:
            labels.append(sentiment.title())
            sizes.append(count)
            color_list.append(colors.get(sentiment, '#95a5a6'))

    if not sizes:
        st.info("No sentiment data to display")
        return

    # Calculate percentages
    total = sum(sizes)
    percentages = [f"{size/total*100:.1f}%" for size in sizes]

    # Create pie chart
    fig, ax = plt.subplots(figsize=(8, 6), facecolor='#F5F7F8')
    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        colors=color_list,
        autopct='%1.1f%%',
        startangle=90,
        textprops={'fontsize': 12, 'weight': 'bold', 'color': '#45474B'}
    )

    # Customize the chart
    ax.set_title('Sentiment Distribution', fontsize=16, fontweight='bold', pad=20, color='#45474B')
    fig.patch.set_facecolor('#F5F7F8')

    # Add count information to legend
    legend_labels = [f"{label}: {size} ({percent})" for label, size, percent in zip(labels, sizes, percentages)]
    ax.legend(wedges, legend_labels, title="Sentiment Analysis", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))

    plt.tight_layout()
    st.pyplot(fig)

# ============================================================================
# URL VALIDATION
# ============================================================================

# Pre-compiled URL validation patterns for performance
URL_PATTERNS = {
    "Facebook": re.compile(r"^https?://(www\.)?(facebook|fb)\.com/[^/?#]+", re.IGNORECASE),
    "Instagram": re.compile(r"^https?://(www\.)?instagram\.com/[^/?#]+", re.IGNORECASE),
    "YouTube": re.compile(r"^https?://(www\.)?(youtube\.com/(watch\?v=|channel/|@|c/|user/)|youtu\.be/)[^/?#]+", re.IGNORECASE),
}

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
        initial_sidebar_state="expanded"
    )

    # Custom theme disabled - using Streamlit's default light theme
    # if 'theme' not in st.session_state:
    #     st.session_state.theme = 'light'
    #
    # # Inject custom CSS
    # st.markdown(get_custom_css(st.session_state.theme), unsafe_allow_html=True)

    # App Header
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0 2rem 0;">
        <h1 style="margin-bottom: 0.5rem;">📊 Social Media Analytics Dashboard</h1>
        <p style="color: var(--text-secondary); font-size: 1.125rem; font-weight: 500;">
            Analyze Facebook, Instagram, and YouTube content with AI-powered insights
        </p>
    </div>
    """, unsafe_allow_html=True)

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
            if hasattr(st, 'secrets') and 'APIFY_TOKEN' in st.secrets:
                return st.secrets['APIFY_TOKEN']
            # Then try environment variable
            return os.environ.get('APIFY_TOKEN')
        except Exception:
            # Fallback to environment variable
            return os.environ.get("APIFY_TOKEN")

    apify_token = get_api_token()

    if not apify_token:
        show_warning(
            message="Please set your APIFY_TOKEN in environment variables or Streamlit secrets.",
            title="API Token Required"
        )
        st.stop()

    # Initialize MongoDB (optional); only set db_service when connection succeeds
    @st.cache_resource
    def _init_db():
        if not MONGODB_AVAILABLE or MongoDBService is None:
            return None
        try:
            from app.config.database import get_database
            if get_database().test_connection():
                return MongoDBService()
        except Exception:
            pass
        return None

    if 'db_service' not in st.session_state:
        st.session_state.db_service = _init_db()

    if st.session_state.db_service:
        st.sidebar.success("🗄️ Database connected")
    else:
        st.sidebar.caption("🗄️ Database not configured (optional)")

    # Sidebar - Platform Selection
    st.sidebar.markdown("### 📱 Platform Selection")
    platform = st.sidebar.radio(
        "Choose a platform:",
        ["Facebook", "Instagram", "YouTube"],
        help="Select the social media platform to analyze"
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown(f"### Current Selection\n**{platform}**")

    # Data Source Selection
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📁 Data Source")
    data_source_options = ["Fetch from API", "Load from File"]
    if st.session_state.get('db_service'):
        data_source_options = ["Fetch from API", "Load from Database", "Load from File"]
    data_source = st.sidebar.radio(
        "Choose data source:",
        data_source_options,
        help="Fetch new data, load from MongoDB, or load from saved files"
    )

    # Facebook Configuration Options
    if data_source == "Fetch from API" and platform == "Facebook":
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📊 Facebook Configuration")

        # Number of posts to extract
        max_posts = st.sidebar.slider(
            "Number of Posts to Extract",
            min_value=1,
            max_value=50,
            value=10,
            help="Maximum number of posts to extract from the Facebook page"
        )

        # Date range selection
        date_range_option = st.sidebar.radio(
            "Date Range:",
            ["All Posts", "Last 30 Days", "Last 7 Days", "Custom Range"],
            help="Choose the time range for posts to extract"
        )

        # Calculate date range
        today = datetime.now()

        if date_range_option == "Last 30 Days":
            from_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")
            to_date = None
        elif date_range_option == "Last 7 Days":
            from_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
            to_date = None
        elif date_range_option == "Custom Range":
            from_date = st.sidebar.date_input(
                "From Date",
                value=today - timedelta(days=30),
                help="Start date for posts extraction"
            ).strftime("%Y-%m-%d")
            to_date = st.sidebar.date_input(
                "To Date",
                value=today,
                help="End date for posts extraction"
            ).strftime("%Y-%m-%d")
        else:  # All Posts
            from_date = None
            to_date = None

        # Platform-specific comments section
        if platform == "Facebook":
            st.sidebar.markdown("### 💬 Facebook Comments")
            st.sidebar.info("⚠️ **Note:** Facebook Comments Scraper actors are currently experiencing issues. The app will try multiple actors but may fail.")
            st.sidebar.info("💡 **Tip:** The Facebook Posts Scraper only provides comment counts. Enable 'Fetch Detailed Comments' to get actual comment text for word clouds and sentiment analysis.")

            # Comment extraction method selection
            comment_method = st.sidebar.radio(
                "Comment Extraction Method:",
                ["Individual Posts", "Batch Processing"],
                index=1,  # Default to Batch Processing
                help="Choose how to extract comments: individual posts (slower but more reliable) or batch processing (faster but may have limitations)"
            )

            fetch_detailed_comments = st.sidebar.checkbox(
                "Fetch Detailed Comments",
                value=False,
                help="Fetch detailed comments for Facebook posts using the Comments Scraper actor (extra Apify runs; currently having issues - may fail)"
            )

        elif platform == "Instagram":
            st.sidebar.markdown("### 💬 Instagram Comments")
            st.sidebar.info("💡 **Tip:** Instagram Posts Scraper only provides comment counts. Enable 'Fetch Detailed Comments' to get actual comment text for word clouds and sentiment analysis.")
            st.sidebar.info("💰 **Cost:** Instagram comments cost $2.30 per 1,000 comments. Free plan includes $5 monthly credits (2,100+ comments).")

            fetch_detailed_comments = st.sidebar.checkbox(
                "Fetch Detailed Comments",
                value=False,
                help="Fetch detailed comments for Instagram posts using the Instagram Comments Scraper (pay-per-result pricing; extra Apify runs)"
            )

            # Instagram uses batch processing by default
            comment_method = "Batch Processing"

        else:
            # YouTube or other platforms
            st.sidebar.markdown("### 💬 Comments")
            if platform == "YouTube":
                st.sidebar.info("💡 **YouTube Two-Step Tip:** Step 1: Channel scraper gets videos. Step 2: Comments scraper analyzes comments from those videos. Enable 'Fetch Detailed Comments' for Step 2.")
            else:
                st.sidebar.info("💡 **Tip:** Enable 'Fetch Detailed Comments' to get actual comment text for word clouds and sentiment analysis.")

            fetch_detailed_comments = st.sidebar.checkbox(
                "Fetch Detailed Comments",
                value=False,
                help="Fetch detailed comments for posts (extra Apify actor runs)"
            )

            comment_method = "Batch Processing"

        # Additional options for batch processing
        if comment_method == "Batch Processing" and fetch_detailed_comments:
            max_comments_per_post = st.sidebar.slider(
                "Max Comments per Post",
                min_value=10,
                max_value=100,
                value=DEFAULT_MAX_COMMENTS,
                help="Maximum number of comments to extract per post"
            )
        else:
            max_comments_per_post = DEFAULT_MAX_COMMENTS
    else:
        fetch_detailed_comments = False
        comment_method = "Individual Posts"
        max_comments_per_post = DEFAULT_MAX_COMMENTS
        max_posts = DEFAULT_MAX_POSTS
        from_date = None
        to_date = None

    # Analysis Options
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔧 Analysis Options")
    use_phrase_analysis = st.sidebar.checkbox(
        "Use Phrase-Based Analysis",
        value=True,
        help="Extract meaningful phrases (like 'thank you', 'very good') instead of individual words for more accurate sentiment analysis"
    )
    use_sentiment_coloring = st.sidebar.checkbox(
        "Use Sentiment Coloring in Word Clouds",
        value=True,
        help="Color words/phrases in word clouds based on their sentiment (green=positive, red=negative, gray=neutral)"
    )

    use_simple_wordcloud = st.sidebar.checkbox(
        "Use Simple Word Cloud (Fallback)",
        value=False,
        help="Use simple word cloud instead of phrase-based analysis. Try this if you see 'No meaningful content found'."
    )

    # Entity Extraction (GLiNER) - REMOVED (too slow to build)
    # use_entity_extraction = st.sidebar.checkbox(
    #     "Enable Entity Extraction (GLiNER)",
    #     value=True,
    #     help="Extract named entities (people, locations, organizations, etc.) from comments using AI. Requires GLiNER library."
    # )

    # File selector for loading saved data
    if data_source == "Load from File":
        saved_files = get_saved_files()
        platform_files = saved_files.get(platform, [])

        if platform_files:
            st.sidebar.markdown("#### Available Files")
            file_options = []
            for file_path in platform_files:
                filename = os.path.basename(file_path)
                # Extract timestamp from filename for display
                try:
                    timestamp_part = filename.split('_', 1)[1].replace('.json', '').replace('.csv', '')
                    display_name = f"{timestamp_part} ({'JSON' if file_path.endswith('.json') else 'CSV'})"
                except (IndexError, ValueError, AttributeError):
                    display_name = filename
                file_options.append((display_name, file_path))

            selected_file_display = st.sidebar.selectbox(
                "Select a file:",
                options=[opt[0] for opt in file_options],
                help="Choose a previously saved data file to load"
            )

            # Get the actual file path
            selected_file_path = None
            for display_name, file_path in file_options:
                if display_name == selected_file_display:
                    selected_file_path = file_path
                    break

            if selected_file_path and st.sidebar.button("📂 Load Selected File", type="primary"):
                with st.spinner(f"Loading data from {os.path.basename(selected_file_path)}..."):
                    loaded_data = load_data_from_file(selected_file_path)

                if loaded_data:
                    st.session_state.posts_data = loaded_data
                    st.success(f"✅ Successfully loaded {len(loaded_data)} posts from file")
                    st.info(f"📁 File: {selected_file_path}")
                    st.rerun()
                else:
                    st.error("Failed to load data from file")
        else:
            st.sidebar.info(f"No saved files found for {platform}")
            st.sidebar.markdown("**Tip:** Fetch data from API first to create saved files")

    if data_source == "Load from Database" and st.session_state.get('db_service'):
        st.sidebar.markdown("#### Database Options")
        st.sidebar.caption("Configure load range below in the main area.")

    # Initialize session state
    if 'posts_data' not in st.session_state:
        st.session_state.posts_data = None
    if 'selected_post_idx' not in st.session_state:
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
                help=f"Paste the URL of the {platform} page/profile/channel"
            )

        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            analyze_button = st.button("🔍 Analyze", type="primary", width='stretch')
    else:
        # Load from File or Load from Database
        if data_source == "Load from Database":
            st.header(f"{platform} Analysis - Load from Database")
            days_back = st.slider("Days of history", 1, 365, 30, help="Load posts from the last N days")
            max_posts_db = st.slider("Maximum posts to load", 10, 1000, 100, help="Cap the number of posts to load")
            if st.session_state.get('db_service') and st.button("📊 Load from Database", type="primary"):
                posts_data = load_data_from_database(platform, days_back=days_back, limit=max_posts_db)
                if posts_data:
                    st.session_state.posts_data = posts_data
                    st.rerun()
            analyze_button = False
            url = ""
        else:
            st.header(f"{platform} Analysis - Loaded from File")
            analyze_button = False
            url = ""

    # In-page Table of Contents for expanders
    toc_items = [
        "📈 Monthly Overview",
        "💡 Monthly Insights",
        "📊 Analytics",
        "📝 Posts Details"
    ]

    with st.container():
        st.markdown("**Sections:**")
        cols = st.columns(len(toc_items))
        for i, item in enumerate(toc_items):
            if cols[i].button(item):
                st.session_state['selected_toc'] = item

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
                f"Invalid {platform} URL format. Please check and try again.",
                "Invalid URL"
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
                    message=f"No posts were found for this {platform} page/profile in the specified date range."
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
                "Data Loaded Successfully"
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
                st.info("💡 Note: Facebook Comments Scraper may have limitations. If it fails, the app will continue with post data only.")
                try:
                    if comment_method == "Batch Processing":
                        st.info("🚀 Using batch processing for comment extraction...")
                        normalized_data = fetch_comments_for_posts_batch(normalized_data, apify_token, max_comments_per_post)
                    else:
                        st.info("🔄 Using individual post processing for comment extraction...")
                        normalized_data = fetch_comments_for_posts(normalized_data, apify_token, max_comments_per_post)
                except Exception as e:
                    st.error(f"❌ Failed to fetch Facebook comments: {str(e)}")

            elif platform == "Instagram":
                st.info("💡 Note: Instagram Comments Scraper will extract comments from all posts. This may take some time.")
                try:
                    # ─────────────────────────────────────────────────────
                    # Extract post URLs from already-fetched posts (Step 1)
                    # ─────────────────────────────────────────────────────
                    post_urls = []
                    for post in normalized_data:
                        if post.get('post_id'):
                            # Construct Instagram post URL from shortCode
                            short_code = post.get('post_id')
                            post_url = f"https://www.instagram.com/p/{short_code}/"
                            post_urls.append(post_url)

                    if post_urls:
                        st.info(f"🔄 Found {len(post_urls)} Instagram posts to extract comments from...")
                        # ─────────────────────────────────────────────────────
                        # Call second actor: Instagram Comments Scraper
                        # ─────────────────────────────────────────────────────
                        comments_data = scrape_instagram_comments_batch(post_urls, apify_token, 25)  # Use 25 comments per post

                        if comments_data:
                            # ─────────────────────────────────────────────────────
                            # Assign comments back to their respective posts
                            # ─────────────────────────────────────────────────────
                            normalized_data = assign_instagram_comments_to_posts(normalized_data, comments_data)
                            st.success(f"✅ Successfully assigned {len(comments_data)} comments to posts")
                        else:
                            st.warning("⚠️ No Instagram comments were extracted")
                    else:
                        st.warning("⚠️ No Instagram post URLs found for comment extraction")

                except Exception as e:
                    st.error(f"❌ Failed to fetch Instagram comments: {str(e)}")
                    st.warning("⚠️ Continuing without detailed comments. You can uncheck 'Fetch Detailed Comments' to skip this step.")
                    # Continue with the posts without comments

        # Count total comments fetched
        total_comments = 0
        for post in normalized_data:
            comments_list = post.get('comments_list', [])
            if isinstance(comments_list, list):
                total_comments += len(comments_list)

        st.info(f"✅ Final result: {len(normalized_data)} posts with {total_comments} total comments")

        # Save: to database + files when DB connected, else files only
        if st.session_state.get('db_service'):
            save_result = save_data_to_database(raw_data, normalized_data, platform, url, max_posts)
            if save_result:
                st.success("✅ Data saved successfully!")
                if save_result.get('job_id'):
                    st.info("🗄️ **Database:** Saved to MongoDB")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Posts Saved", save_result.get('total_posts', 0))
                    with col2:
                        st.metric("Comments Saved", save_result.get('total_comments', 0))
                    with col3:
                        st.metric("Job ID", (save_result.get('job_id', '') or '')[:8] + "..." if save_result.get('job_id') else "—")
                if save_result.get('json_path'):
                    st.info(f"📄 Raw JSON: `{save_result.get('json_path')}`")
                    st.info(f"📊 Processed CSV: `{save_result.get('csv_path')}`")
                    if save_result.get('comments_path'):
                        st.info(f"💬 Comments CSV: `{save_result.get('comments_path')}`")
        else:
            with st.spinner("💾 Saving data to files..."):
                json_path, csv_path, comments_csv_path = save_data_to_files(raw_data, normalized_data, platform)
            if json_path and csv_path:
                st.success("✅ Data saved successfully!")
                st.info(f"📄 Raw JSON: `{json_path}`")
                st.info(f"📊 Processed CSV: `{csv_path}`")
                if comments_csv_path:
                    st.info(f"💬 Comments CSV: `{comments_csv_path}`")
            else:
                st.warning("⚠️ Failed to save data to files")

        # Option to show all posts or filter by current month
        filter_option = st.radio(
            "Choose data range:",
            ["Show All Posts", "Current Month Only"],
            help="Select whether to show all posts or filter to current month only"
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
        posts = st.session_state.posts_data
        df = pd.DataFrame(posts)

        # Optimized: vectorized operations for better performance
        numeric_cols = ['likes', 'comments_count', 'shares_count']
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce').fillna(0).astype(int)
        df['text'] = df['text'].fillna("").astype(str)

        # ═══════════════════════════════════════════════════════════
        # INSTAGRAM WORKFLOW - STEP 3: SHOW MONTHLY OVERVIEW
        # ═══════════════════════════════════════════════════════════
        # Enhanced KPI Cards for Facebook Data (wrapped in expander)
        title_section = "📈 Monthly Overview"
        expanded = st.session_state.get('selected_toc') == title_section
        with st.expander(title_section, expanded=expanded):
            # Analysis Period Display
            now = datetime.now()
            month_year = now.strftime("%B %Y")
            st.markdown(f"**Analysis Period:** {month_year}")
            st.markdown("---")

            # Platform-specific analysis
            if platform == "Instagram":
                # Show monthly Instagram analysis first
                create_instagram_monthly_analysis(posts, platform)
                # Show monthly insights with word cloud and sentiment
                create_instagram_monthly_insights(posts, platform)
            elif platform == "YouTube":
                # YouTube Two-Step Analysis: Channel Scraper + Comments Scraper
                youtube_metrics = calculate_youtube_metrics(posts)

                # Display YouTube video metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Views", f"{youtube_metrics.get('total_views', 0):,}")
                with col2:
                    st.metric("Total Likes", f"{youtube_metrics.get('total_likes', 0):,}")
                with col3:
                    st.metric("Total Comments", f"{youtube_metrics.get('total_comments', 0):,}")
                with col4:
                    st.metric("Engagement Rate", f"{youtube_metrics.get('engagement_rate', 0):.2f}%")

                # Additional YouTube metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Avg Views", f"{youtube_metrics.get('avg_views', 0):,.0f}")
                with col2:
                    st.metric("Avg Likes", f"{youtube_metrics.get('avg_likes', 0):,.0f}")
                with col3:
                    st.metric("Avg Comments", f"{youtube_metrics.get('avg_comments', 0):,.0f}")
                with col4:
                    st.metric("Total Shares", f"{youtube_metrics.get('total_shares', 0):,}")

                # Step 2: Extract comments from videos if enabled
                if fetch_detailed_comments:
                    st.markdown("#### 💬 Comments Analysis")
                    st.info("🔄 **Step 2:** Extracting comments from videos...")

                    # Extract video URLs from posts
                    video_urls = [post.get('url') for post in posts if post.get('url')]
                    video_urls = [url for url in video_urls if url]  # Remove empty URLs

                    if video_urls:
                        st.write(f"Found {len(video_urls)} videos to analyze for comments")

                        # Fetch comments from all videos
                        with st.spinner("Fetching comments from videos..."):
                            all_comments = fetch_youtube_comments(video_urls, apify_token, max_posts)

                        if all_comments:
                            st.success(f"✅ Successfully fetched {len(all_comments)} comments")

                            # Display comment metrics
                            total_comment_likes = sum(comment.get('voteCount', 0) for comment in all_comments)
                            unique_comment_authors = len(set(comment.get('author', '') for comment in all_comments if comment.get('author')))

                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Total Comments", f"{len(all_comments):,}")
                            with col2:
                                st.metric("Comment Likes", f"{total_comment_likes:,}")
                            with col3:
                                st.metric("Unique Authors", f"{unique_comment_authors:,}")
                            with col4:
                                st.metric("Avg Likes/Comment", f"{total_comment_likes / len(all_comments):.1f}" if all_comments else "0")

                            # Comments word cloud
                            st.markdown("#### 📊 Comments Word Cloud")
                            comment_texts = [comment.get('comment', '') for comment in all_comments if comment.get('comment')]
                            if comment_texts:
                                st.write(f"Analyzing {len(comment_texts)} comments...")
                                create_wordcloud(comment_texts)
                            else:
                                st.info("No comment text available for word cloud.")
                        else:
                            st.warning("No comments found for the videos.")
                    else:
                        st.warning("No video URLs found to extract comments from.")
                else:
                    st.info("💡 **Tip:** Enable 'Fetch Detailed Comments' to analyze comments from the videos.")
            else:
                # Facebook analysis (existing code)
                # Calculate metrics
                total_reactions = calculate_total_reactions(posts)
                total_comments = df['comments_count'].sum()
                total_shares = df['shares_count'].sum()
                avg_engagement = calculate_average_engagement(posts)

                # Calculate detailed reactions breakdown
                reactions_breakdown = {}
                for post in posts:
                    reactions = post.get('reactions', {})
                    if isinstance(reactions, dict):
                        for reaction_type, count in reactions.items():
                            reactions_breakdown[reaction_type] = reactions_breakdown.get(reaction_type, 0) + count

                # Create 4-column card layout
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.markdown("""
                    <div style="
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        padding: 1rem;
                        border-radius: 10px;
                        text-align: center;
                        color: white;
                        margin-bottom: 1rem;
                    ">
                        <h3 style="margin: 0; font-size: 2rem;">😊</h3>
                        <h2 style="margin: 0.5rem 0; font-size: 1.5rem;">Total Reactions</h2>
                    </div>
                    """, unsafe_allow_html=True)
                    st.metric("Total Reactions", f"{total_reactions:,}", help="Sum of all reaction types (like, love, wow, etc.)", label_visibility="collapsed")

                with col2:
                    st.markdown("""
                    <div style="
                        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                        padding: 1rem;
                        border-radius: 10px;
                        text-align: center;
                        color: white;
                        margin-bottom: 1rem;
                    ">
                        <h3 style="margin: 0; font-size: 2rem;">💬</h3>
                        <h2 style="margin: 0.5rem 0; font-size: 1.5rem;">Total Comments</h2>
                    </div>
                    """, unsafe_allow_html=True)
                    st.metric("Total Comments", f"{total_comments:,}", help="Total number of comments across all posts", label_visibility="collapsed")

                with col3:
                    st.markdown("""
                    <div style="
                        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                        padding: 1rem;
                        border-radius: 10px;
                        text-align: center;
                        color: white;
                        margin-bottom: 1rem;
                    ">
                        <h3 style="margin: 0; font-size: 2rem;">📤</h3>
                        <h2 style="margin: 0.5rem 0; font-size: 1.5rem;">Total Shares</h2>
                    </div>
                    """, unsafe_allow_html=True)
                    st.metric("Total Shares", f"{total_shares:,}", help="Total number of shares across all posts", label_visibility="collapsed")

                with col4:
                    st.markdown("""
                    <div style="
                        background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
                        padding: 1rem;
                        border-radius: 10px;
                        text-align: center;
                        color: white;
                        margin-bottom: 1rem;
                    ">
                        <h3 style="margin: 0; font-size: 2rem;">📊</h3>
                        <h2 style="margin: 0.5rem 0; font-size: 1.5rem;">Avg Engagement</h2>
                    </div>
                    """, unsafe_allow_html=True)
                    st.metric("Avg Engagement", f"{avg_engagement:.1f}", help="Average engagement per post (likes + comments + shares + reactions)", label_visibility="collapsed")

                # Show reactions breakdown if available (not for Instagram)
                if reactions_breakdown and platform != "Instagram":
                    st.markdown("---")
                    st.markdown("### 😊 Reactions Breakdown")
                    create_reaction_pie_chart(reactions_breakdown)

        st.markdown("---")

        # Monthly Insights Section
        st.markdown("### 💡 Monthly Insights")

        # Aggregate all comments for analysis
        all_comments = aggregate_all_comments(posts)

        # DEBUG: Show what we got
        st.write(f"🔍 DEBUG: aggregate_all_comments returned {len(all_comments)} comment texts")
        if posts:
            st.write(f"🔍 DEBUG: Total posts: {len(posts)}")
            posts_with_comments = sum(1 for p in posts if p.get('comments_list'))
            st.write(f"🔍 DEBUG: Posts with comments_list: {posts_with_comments}")
            if posts_with_comments > 0:
                sample_post = next(p for p in posts if p.get('comments_list'))
                st.write(f"🔍 DEBUG: Sample post has {len(sample_post.get('comments_list', []))} comments")
                if sample_post.get('comments_list'):
                    st.write(f"🔍 DEBUG: Sample comment structure: {list(sample_post['comments_list'][0].keys())}")
                    st.write(f"🔍 DEBUG: Sample comment text: {sample_post['comments_list'][0].get('text', 'NO TEXT')[:100]}")

        if all_comments:
            # Advanced NLP Analysis Dashboard (function adds its own title)
            create_advanced_nlp_dashboard(all_comments)

            st.markdown("---")

            # Create two columns for traditional insights
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### 💬 Most Discussed Topics This Month")
                # Create larger word cloud for monthly insights
                create_wordcloud(all_comments, width=1200, height=600, figsize=(15, 8))

            with col2:
                st.markdown("#### 😊 Sentiment Distribution")
                # Analyze sentiment for all comments
                sentiment_counts = analyze_all_sentiments(all_comments)
                create_sentiment_pie_chart(sentiment_counts)

                # Display summary statistics
                total_comments = sum(sentiment_counts.values())
                if total_comments > 0:
                    st.markdown("**Summary:**")
                    st.markdown(f"- **Total Comments Analyzed:** {total_comments:,}")
                    st.markdown(f"- **Positive:** {sentiment_counts['positive']:,} ({sentiment_counts['positive']/total_comments*100:.1f}%)")
                    st.markdown(f"- **Negative:** {sentiment_counts['negative']:,} ({sentiment_counts['negative']/total_comments*100:.1f}%)")
                    st.markdown(f"- **Neutral:** {sentiment_counts['neutral']:,} ({sentiment_counts['neutral']/total_comments*100:.1f}%)")

            # Sentiment Comparison View (Emoji analysis already included in Advanced NLP Dashboard above)
            # Only show comparison if we have enough data
            try:
                from app.nlp.advanced_nlp import analyze_text_emojis, analyze_text_with_emoji_sentiment
                from app.nlp.sentiment_analyzer import analyze_corpus_sentiment_phrases

                monthly_agg_text = " ".join([t for t in all_comments if isinstance(t, str)])
                monthly_emoji = analyze_text_emojis(monthly_agg_text)
                monthly_text_sent = analyze_corpus_sentiment_phrases(all_comments)
                monthly_combined = analyze_text_with_emoji_sentiment(monthly_agg_text)

                # Only show sentiment comparison if we have meaningful data
                if monthly_emoji.get('emoji_count', 0) > 0:
                    st.markdown("---")
                    st.markdown("#### 📊 Sentiment Comparison")
                    create_sentiment_comparison_view(monthly_text_sent, monthly_emoji, monthly_combined)
            except Exception as e:
                # Silently skip if sentiment comparison fails (emoji analysis already shown in dashboard)
                pass
        else:
            st.info("📊 No comment text available for monthly insights analysis")
            st.warning("💡 **To analyze comments:** Enable 'Fetch Detailed Comments' in the sidebar and re-analyze the page.")
            st.info("This will extract actual comment text for word clouds and sentiment analysis.")

            # Show some debugging info
            total_posts = len(posts)
            posts_with_comments = sum(1 for post in posts if post.get('comments_count', 0) > 0)
            st.info(f"📈 **Data Summary:** {total_posts} posts found, {posts_with_comments} posts have comments")

            if posts_with_comments > 0:
                st.info("💡 Comments are available but not being processed. Check the comment extraction logic.")

        st.markdown("---")

        # ═══════════════════════════════════════════════════════════
        # CROSS-PLATFORM COMPARISON (if data available)
        # ═══════════════════════════════════════════════════════════
        comparison_title = "🔄 Cross-Platform Comparison"
        expanded_comparison = st.session_state.get('selected_toc') == comparison_title

        # Check if we have saved data from other platforms
        saved_files = get_saved_files()
        all_platforms_data = {}

        # Add current platform data
        all_platforms_data[platform] = posts

        # Try to load recent data from other platforms
        for other_platform in ["Facebook", "Instagram", "YouTube"]:
            if other_platform != platform and other_platform in saved_files:
                platform_files = saved_files[other_platform]
                if platform_files:
                    # Load the most recent file
                    latest_file = platform_files[0]
                    try:
                        loaded_data = load_data_from_file(latest_file)
                        if loaded_data:
                            all_platforms_data[other_platform] = loaded_data
                    except Exception:
                        pass  # Skip if loading fails

        # Show comparison if we have data from multiple platforms
        if len(all_platforms_data) > 1:
            with st.expander(comparison_title, expanded=expanded_comparison):
                st.markdown("### 🔄 Multi-Platform Performance Analysis")
                st.info(f"Comparing data across {len(all_platforms_data)} platforms")

                create_performance_comparison(
                    facebook_posts=all_platforms_data.get("Facebook"),
                    instagram_posts=all_platforms_data.get("Instagram"),
                    youtube_posts=all_platforms_data.get("YouTube")
                )

        st.markdown("---")

        # Analytics charts (expander)
        analytics_title = "📊 Analytics"
        expanded_analytics = st.session_state.get('selected_toc') == analytics_title
        with st.expander(analytics_title, expanded=expanded_analytics):
            create_monthly_overview_charts(df)

        st.markdown("---")

        # Posts table
        st.markdown("### 📝 Posts Details")
        display_df = df[['published_at', 'text', 'likes', 'comments_count', 'shares_count']].copy()
        display_df['text'] = display_df['text'].str[:100] + '...'

        # Optimized: vectorized datetime formatting
        display_df['published_at'] = pd.to_datetime(display_df['published_at'], utc=True).dt.tz_localize(None)
        display_df['published_at'] = display_df['published_at'].dt.strftime('%Y-%m-%d %H:%M').fillna('Unknown')
        display_df.columns = ['Date', 'Caption', 'Likes', 'Comments', 'Shares']

        st.dataframe(display_df, use_container_width=True, height=300)

        st.markdown("---")

        # Comprehensive Export Section
        create_comprehensive_export_section(posts, platform)

        # ═══════════════════════════════════════════════════════════
        # ENHANCED POST DETAIL ANALYSIS - STEP 4
        # ═══════════════════════════════════════════════════════════
        # Use new enhanced post selector
        selected_post = create_enhanced_post_selector(posts, platform)

        if selected_post:
            st.markdown("---")
            st.markdown("### 🔍 Post Details")

            # Post info
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown(f"**Caption:** {selected_post['text']}")
                # Robustly format published_at regardless of original type (str, datetime, Timestamp, None)
                pub_date = _to_naive_dt(selected_post.get('published_at'))
                pub_date_display = pub_date.strftime('%Y-%m-%d %H:%M') if pub_date else "Unknown"
                st.markdown(f"**Published:** {pub_date_display}")

            with col2:
                if platform == "Instagram":
                    # Instagram-specific metrics
                    st.metric("Likes", selected_post['likes'])
                    st.metric("Comments", selected_post['comments_count'])
                    if selected_post.get('type'):
                        st.metric("Type", selected_post['type'])
                elif platform == "YouTube":
                    # YouTube Video-specific metrics
                    st.metric("Views", f"{selected_post.get('views', 0):,}")
                    st.metric("Likes", f"{selected_post.get('likes', 0):,}")
                    st.metric("Comments", f"{selected_post.get('comments_count', 0):,}")
                    if selected_post.get('duration'):
                        st.metric("Duration", selected_post['duration'])
                else:
                    # Facebook metrics
                    st.metric("Shares", selected_post['shares_count'])
                    st.metric("Comments", selected_post['comments_count'])

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
                    if selected_post.get('hashtags'):
                        st.markdown("#### #️⃣ Hashtags")
                        hashtags = selected_post['hashtags']
                        if isinstance(hashtags, list) and hashtags:
                            st.write(", ".join([f"#{tag}" for tag in hashtags]))
                        else:
                            st.info("No hashtags found")

                    if selected_post.get('mentions'):
                        st.markdown("#### 👥 Mentions")
                        mentions = selected_post['mentions']
                        if isinstance(mentions, list) and mentions:
                            st.write(", ".join([f"@{mention}" for mention in mentions]))
                        else:
                            st.info("No mentions found")

                with col2:
                    if selected_post.get('ownerUsername'):
                        st.markdown("#### 👤 Post Owner")
                        st.write(f"**Username:** @{selected_post['ownerUsername']}")
                        if selected_post.get('ownerFullName'):
                            st.write(f"**Full Name:** {selected_post['ownerFullName']}")

                    if selected_post.get('displayUrl'):
                        st.markdown("#### 🖼️ Media")
                        st.image(selected_post['displayUrl'], width=300)

            elif platform == "YouTube":
                col1, col2 = st.columns(2)

                with col1:
                    if selected_post.get('channel'):
                        st.markdown("#### � Channel Information")
                        st.write(f"**Channel:** {selected_post['channel']}")
                        if selected_post.get('channel_username'):
                            st.write(f"**Username:** {selected_post['channel_username']}")
                        if selected_post.get('subscriber_count'):
                            st.write(f"**Subscribers:** {selected_post['subscriber_count']:,}")

                    if selected_post.get('url'):
                        st.markdown("#### 🔗 Video Link")
                        st.markdown(f"[Watch on YouTube]({selected_post['url']})")

                with col2:
                    if selected_post.get('thumbnail_url'):
                        st.markdown("#### �️ Thumbnail")
                        st.image(selected_post['thumbnail_url'], width=400)

            else:  # Facebook
                # Facebook reactions breakdown
                reactions = selected_post.get('reactions', {})
                if isinstance(reactions, dict) and reactions:
                    st.markdown("#### � Reaction Breakdown")
                    create_reaction_pie_chart(reactions)
                else:
                    st.info("Detailed reaction data not available for this post")

if __name__ == "__main__":
    main()
