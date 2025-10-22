"""
Social Media Analytics Dashboard
=================================

How to run:
1. Set your Apify API token:
   export APIFY_TOKEN=your_token_here

2. Install dependencies:
   pip install -r requirements.txt

3. Run the app:
   streamlit run app.py

This app connects to Apify actors to analyze social media posts from Facebook, 
Instagram, and YouTube for the current month.
"""

import os
import re
import json
import glob
import time
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
# CONFIGURATION
# ============================================================================

# Apify Actor Names - Replace with actual actor IDs/names
ACTOR_CONFIG = {
    "Facebook": "zanTWNqB3Poz44qdY",  # Actor ID: scraper_one/facebook-posts-scraper (better reactions data)
    "Instagram": "apify/instagram-scraper",  # Updated with correct actor name
    "YouTube": "streamers/youtube-comments-scraper"  # Updated with correct actor name
}

# Actor IDs for direct calls (when needed)
ACTOR_IDS = {
    "Facebook": "KoJrdxJCTtpon81KY",  # Placeholder
    "Instagram": "shu8hvrXbJbY3Eb9W",  # Instagram scraper actor ID
    "YouTube": "p7UMdpQnjKmmpR21D"  # Placeholder
}

# Facebook Comments Scraper Actor
# Try different actors if one fails
FACEBOOK_COMMENTS_ACTOR_IDS = [
    "us5srxAYnsrkgUv2v",  # Primary actor from the API client example
    "apify/facebook-comments-scraper", 
    "facebook-comments-scraper",
    "alien_force/facebook-posts-comments-scraper"
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
        return extract_phrases_simple(comments, top_n)
    except ImportError:
        # Fallback to improved word-based extraction
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
# DATA NORMALIZATION
# ============================================================================

def _to_naive_dt(x):
    """Convert input to timezone-naive datetime, returning None on failure."""
    ts = pd.to_datetime(x, errors="coerce", utc=True)
    if pd.isna(ts):
        return None
    return ts.tz_convert(None)

def normalize_post_data(raw_data: List[Dict], platform: str) -> List[Dict]:
    """
    Normalize actor response into consistent schema.
    Adjust field mappings based on actual actor responses.
    """
    normalized = []
    
    for item in raw_data:
        try:
            # Platform-specific field mapping
            if platform == "Instagram":
                # Instagram scraper output format based on documentation
                post = {
                    'post_id': item.get('shortCode') or item.get('id', ''),
                    'published_at': item.get('timestamp', ''),
                    'text': item.get('caption', ''),
                    'likes': item.get('likesCount', 0),
                    'comments_count': item.get('commentsCount', 0),
                    'shares_count': 0,  # Instagram doesn't have shares
                    'reactions': {},  # Instagram doesn't have detailed reactions like Facebook
                    'comments_list': item.get('latestComments', []),
                    'type': item.get('type', ''),
                    'displayUrl': item.get('displayUrl', ''),
                    'ownerUsername': item.get('ownerUsername', ''),
                    'ownerFullName': item.get('ownerFullName', ''),
                    'hashtags': item.get('hashtags', []),
                    'mentions': item.get('mentions', []),
                    'dimensionsHeight': item.get('dimensionsHeight', 0),
                    'dimensionsWidth': item.get('dimensionsWidth', 0),
                    'isSponsored': item.get('isSponsored', False),
                    'post_url': f"https://www.instagram.com/p/{item.get('shortCode', '')}/" if item.get('shortCode') else ''
                }
            elif platform == "Facebook":
                # Handle both old and new Facebook scraper formats
                post = {
                    'post_id': item.get('postId') or item.get('id', ''),
                    'published_at': item.get('time') or item.get('timestamp') or item.get('createdTime', ''),
                    'text': item.get('postText') or item.get('text') or item.get('message') or item.get('caption', ''),
                    'likes': item.get('reactionsCount', 0) or item.get('likes', 0),
                    'comments_count': item.get('commentsCount', 0) or item.get('comments', 0),
                    'shares_count': item.get('shares', 0),  # New actor may not provide shares
                    'reactions': item.get('reactions', {}),
                    'comments_list': item.get('commentsList', []) or item.get('comments', [])
                }
            elif platform == "YouTube":
                post = {
                    'post_id': item.get('id') or item.get('videoId', ''),
                    'published_at': item.get('publishedAt') or item.get('timestamp') or item.get('date', ''),
                    'text': item.get('text') or item.get('title') or item.get('description', ''),
                    'likes': item.get('likesCount') or item.get('likes', 0),
                    'comments_count': item.get('commentsCount') or item.get('comments', 0),
                    'shares_count': item.get('sharesCount') or item.get('shares', 0),
                    'reactions': item.get('reactions', {}),
                    'comments_list': item.get('comments') or item.get('commentsList', [])
                }
            else:
                # Generic fallback
                post = {
                    'post_id': item.get('id') or item.get('postId') or item.get('videoId', ''),
                    'published_at': item.get('time') or item.get('timestamp') or item.get('publishedAt', ''),
                    'text': item.get('text') or item.get('caption') or item.get('title', ''),
                    'likes': item.get('likes', 0) or item.get('likesCount', 0),
                    'comments_count': item.get('comments', 0) or item.get('commentsCount', 0),
                    'shares_count': item.get('shares', 0) or item.get('sharesCount', 0),
                    'reactions': item.get('reactions', {}),
                    'comments_list': item.get('commentsList', []) or item.get('comments_data', [])
                }
            
            # Parse timestamp using robust helper
            post['published_at'] = _to_naive_dt(post['published_at'])
            
            # Store original post URL for traceability and comment fetching
            post_url = item.get('url') or item.get('postUrl') or item.get('link') or item.get('facebookUrl') or item.get('pageUrl')
            post['post_url'] = post_url
            
            normalized.append(post)
        except Exception as e:
            st.warning(f"Failed to normalize post: {str(e)}")
            continue
    
    return normalized

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

def aggregate_all_comments(posts: List[Dict]) -> List[str]:
    """
    Aggregate all comments from all posts into a single list.
    Returns list of comment text strings.
    """
    all_comments = []
    for post in posts:
        comments_list = post.get('comments_list', [])
        
        if isinstance(comments_list, list):
            for comment in comments_list:
                if isinstance(comment, str):
                    # Clean and validate string comments
                    cleaned = comment.strip()
                    if cleaned and len(cleaned) > 2:  # Filter out very short comments
                        all_comments.append(cleaned)
                elif isinstance(comment, dict):
                    # Extract text from comment object with multiple field options
                    text = (comment.get('text') or 
                           comment.get('comment') or 
                           comment.get('message') or 
                           comment.get('content', ''))
                    if text and text.strip() and len(text.strip()) > 2:
                        all_comments.append(text.strip())
        elif isinstance(comments_list, int):
            # This is just a count, skip
            continue
    
    # Filter out empty or very short comments
    filtered_comments = [c for c in all_comments if c and len(c.strip()) > 2]
    return filtered_comments

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
    Save raw and processed data to files.
    Returns tuple of (json_file_path, csv_file_path, comments_csv_file_path)
    """
    try:
        # Create timestamp for file naming
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Ensure directories exist
        os.makedirs("data/raw", exist_ok=True)
        os.makedirs("data/processed", exist_ok=True)
        
        # Save raw JSON data
        json_filename = f"data/raw/{platform.lower()}_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(raw_data, f, ensure_ascii=False, indent=2, default=str)
        
        # Prepare CSV data with required columns
        csv_data = []
        comments_data = []
        
        for post in normalized_data:
            csv_row = {
                'post_id': post.get('post_id', ''),
                'published_at': post.get('published_at', ''),
                'text': post.get('text', ''),
                'likes': post.get('likes', 0),
                'comments_count': post.get('comments_count', 0),
                'shares_count': post.get('shares_count', 0),
                'reactions': json.dumps(post.get('reactions', {}), ensure_ascii=False),
                'comments_list': json.dumps(post.get('comments_list', []), ensure_ascii=False)
            }
            csv_data.append(csv_row)
            
            # Extract comments for separate CSV file
            comments_list = post.get('comments_list', [])
            if isinstance(comments_list, list):
                for comment in comments_list:
                    if isinstance(comment, dict):
                        comment_row = {
                            'post_id': post.get('post_id', ''),
                            'comment_id': comment.get('comment_id', ''),
                            'text': comment.get('text', ''),
                            'author_name': comment.get('author_name', ''),
                            'created_time': comment.get('created_time', ''),
                            'likes_count': comment.get('likes_count', 0)
                        }
                        comments_data.append(comment_row)
                    elif isinstance(comment, str):
                        comments_data.append({
                            'post_id': post.get('post_id', ''),
                            'comment_id': '',
                            'text': comment,
                            'author_name': '',
                            'created_time': '',
                            'likes_count': 0
                        })
        
        # Save processed CSV data
        csv_filename = f"data/processed/{platform.lower()}_{timestamp}.csv"
        df = pd.DataFrame(csv_data)
        df.to_csv(csv_filename, index=False, encoding='utf-8')
        
        # Save comments CSV data (if any comments exist)
        comments_csv_filename = None
        if comments_data:
            comments_csv_filename = f"data/processed/{platform.lower()}_comments_{timestamp}.csv"
            comments_df = pd.DataFrame(comments_data)
            comments_df.to_csv(comments_csv_filename, index=False, encoding='utf-8')
        
        return json_filename, csv_filename, comments_csv_filename
        
    except Exception as e:
        st.error(f"Error saving files: {str(e)}")
        return None, None, None

def load_data_from_file(file_path: str) -> Optional[List[Dict]]:
    """
    Load data from a saved file (JSON or CSV).
    Returns normalized data in the same format as from API.
    """
    try:
        if file_path.endswith('.json'):
            # Load raw JSON data
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
            
            # Extract platform from filename
            filename = os.path.basename(file_path)
            platform = filename.split('_')[0].title()
            
            # Normalize the data
            normalized_data = normalize_post_data(raw_data, platform)
            return normalized_data
            
        elif file_path.endswith('.csv'):
            # Load processed CSV data
            df = pd.read_csv(file_path, encoding='utf-8')
            
            # Convert back to list of dictionaries
            normalized_data = []
            for _, row in df.iterrows():
                post = {
                    'post_id': row.get('post_id', ''),
                    'published_at': pd.to_datetime(row.get('published_at', '')),
                    'text': row.get('text', ''),
                    'likes': int(pd.to_numeric(row.get('likes', 0), errors='coerce') or 0),
                    'comments_count': int(pd.to_numeric(row.get('comments_count', 0), errors='coerce') or 0),
                    'shares_count': int(pd.to_numeric(row.get('shares_count', 0), errors='coerce') or 0),
                    'reactions': json.loads(row.get('reactions', '{}')),
                    'comments_list': json.loads(row.get('comments_list', '[]'))
                }
                normalized_data.append(post)
            
            return normalized_data
            
    except Exception as e:
        st.error(f"Error loading file: {str(e)}")
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
@functools.lru_cache(maxsize=32)
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
            # New scraper_one/facebook-posts-scraper format (better reactions data)
            run_input = {"pageUrls": [url], "resultsLimit": max_posts}
            # Add date range parameters if specified
            if from_date:
                run_input["fromDate"] = from_date
            if to_date:
                run_input["toDate"] = to_date
        elif platform == "YouTube":
            run_input = {"startUrls": [{"url": url}], "maxComments": max_posts, "commentsSortBy": "top"}
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
        
        # Fetch results
        items = []
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            items.append(item)
        
        st.info(f"✅ Received {len(items)} posts from actor (requested {max_posts})")
        return items
    
    except Exception as e:
        st.error(f"Apify API Error: {str(e)}")
        return None

@st.cache_data(ttl=3600, max_entries=256, show_spinner=False)
@functools.lru_cache(maxsize=128)
def fetch_post_comments(post_url: str, _apify_token: str) -> Optional[List[Dict]]:
    """
    Fetch detailed comments for a specific Facebook post using the Comments Scraper actor.
    Tries different actors and input formats if one fails.
    Cached for 1 hour per post URL.
    """
    # Validate URL format
    if not post_url or not post_url.startswith('http'):
        st.error(f"❌ Invalid URL format: {post_url}")
        return None
    
    client = ApifyClient(_apify_token)
    
    # Try different actors with unified input format
    actor_configs = [
        {"actor_id": "apify/facebook-comments-scraper",
         "input": {"startUrls": [{"url": post_url}], "maxComments": 50, "includeNestedComments": False}},
        {"actor_id": "facebook-comments-scraper",
         "input": {"startUrls": [{"url": post_url}], "maxComments": 50, "includeNestedComments": False}},
        {"actor_id": "alien_force/facebook-posts-comments-scraper",
         "input": {"startUrls": [{"url": post_url}], "maxComments": 50}}
    ]
    
    for i, config in enumerate(actor_configs):
        try:
            st.info(f"🔍 Attempt {i+1}: Using actor '{config['actor_id']}' for: {post_url}")
            
            # Run the actor
            run = client.actor(config["actor_id"]).call(run_input=config["input"])
            
            # Fetch results
            comments = []
            for item in client.dataset(run["defaultDatasetId"]).iterate_items():
                comments.append(item)
            
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

def fetch_comments_for_posts_batch(posts: List[Dict], apify_token: str, max_comments_per_post: int = 25) -> List[Dict]:
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
            
            # Fetch results
            comments_data = []
            for item in client.dataset(run["defaultDatasetId"]).iterate_items():
                comments_data.append(item)
            
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
    
    # Assign comments to posts
    assigned_comments = 0
    for comment in comments_data:
        # Try to find the post this comment belongs to
        comment_url = comment.get('url') or comment.get('postUrl') or comment.get('facebookUrl')
        
        if comment_url:
            # Find matching post
            for post_url, post in post_url_map.items():
                if comment_url in post_url or post_url in comment_url:
                    # Normalize comment data
                    normalized_comment = normalize_comment_data(comment)
                    post['comments_list'].append(normalized_comment)
                    assigned_comments += 1
                    break
    
    st.info(f"📊 Assigned {assigned_comments} comments to {len(posts)} posts")
    return posts

def fetch_comments_for_posts(posts: List[Dict], apify_token: str) -> List[Dict]:
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
                raw_comments = fetch_post_comments(post['post_url'], apify_token)
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

def scrape_instagram_comments_batch(post_urls: List[str], apify_token: str, max_comments_per_post: int = 25) -> List[Dict]:
    """Scrape Instagram comments from multiple post URLs using batch processing."""
    if not post_urls:
        return []
    
    client = ApifyClient(apify_token)
    all_comments = []
    
    st.info(f"🔄 Starting Instagram comments extraction for {len(post_urls)} posts...")
    
    # Process posts in batches to avoid overwhelming the API
    batch_size = 5  # Process 5 posts at a time
    for i in range(0, len(post_urls), batch_size):
        batch_urls = post_urls[i:i + batch_size]
        st.info(f"📊 Processing batch {i//batch_size + 1}/{(len(post_urls) + batch_size - 1)//batch_size} ({len(batch_urls)} posts)")
        
        for post_url in batch_urls:
            try:
                # Try different Instagram comments actors
                for actor_id in INSTAGRAM_COMMENTS_ACTOR_IDS:
                    try:
                        st.info(f"🔍 Trying Instagram comments actor: {actor_id}")
                        
                        # Configure input for Instagram comments scraper
                        # Try with higher limits to get more comments
                        run_input = {
                            "directUrls": [post_url],
                            "resultsLimit": 50,  # Try to get more comments initially
                            "maxComments": 50,   # Additional parameter for maximum comments
                            "includeReplies": True,  # Include comment replies
                            "sortBy": "newest",  # Get newest comments first
                            "maxResults": 50,   # Another parameter for max results
                            "limit": 50        # Alternative limit parameter
                        }
                        
                        # Run the actor
                        run = client.actor(actor_id).call(run_input=run_input)
                        
                        if run and run.get("status") == "SUCCEEDED":
                            # Get the results
                            dataset = client.dataset(run["defaultDatasetId"])
                            comments_data = list(dataset.iterate_items())
                            
                            if comments_data:
                                st.success(f"✅ Extracted {len(comments_data)} comments from {post_url}")
                                st.info(f"📊 Comment extraction details:")
                                st.info(f"   - Requested: 50 comments (max)")
                                st.info(f"   - Retrieved: {len(comments_data)} comments")
                                st.info(f"   - Post URL: {post_url}")
                                if len(comments_data) < 25:
                                    st.warning(f"⚠️ Only {len(comments_data)} comments retrieved. Instagram may have limited comment access for this post.")
                                all_comments.extend(comments_data)
                                break  # Success, move to next post
                            else:
                                st.warning(f"⚠️ No comments found for {post_url}")
                                st.info(f"🔍 Debug info: Actor {actor_id} returned empty results")
                                break
                        else:
                            st.warning(f"⚠️ Actor {actor_id} failed for {post_url}")
                            continue
                            
                    except Exception as e:
                        st.warning(f"⚠️ Actor {actor_id} error for {post_url}: {str(e)}")
                        continue
                
                # Small delay between posts to be respectful
                time.sleep(2)
                
            except Exception as e:
                st.error(f"❌ Error processing {post_url}: {str(e)}")
                continue
    
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
    """Create comprehensive monthly Instagram analysis with real data."""
    if platform != "Instagram":
        return
    
    st.markdown("### 📸 Monthly Instagram Analysis")
    
    # Basic metrics
    total_posts = len(posts)
    total_likes = sum(post.get('likes', 0) for post in posts)
    total_comments = sum(post.get('comments_count', 0) for post in posts)
    avg_engagement = (total_likes + total_comments) / total_posts if total_posts > 0 else 0
    
    # Create metrics cards
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
            <h3 style="margin: 0; font-size: 2rem;">📸</h3>
            <h2 style="margin: 0.5rem 0; font-size: 1.5rem;">Total Posts</h2>
        </div>
        """, unsafe_allow_html=True)
        st.metric("Total Posts", f"{total_posts:,}", help="Total number of Instagram posts", label_visibility="collapsed")
    
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
            <h3 style="margin: 0; font-size: 2rem;">❤️</h3>
            <h2 style="margin: 0.5rem 0; font-size: 1.5rem;">Total Likes</h2>
        </div>
        """, unsafe_allow_html=True)
        st.metric("Total Likes", f"{total_likes:,}", help="Total likes across all posts", label_visibility="collapsed")
    
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
            <h3 style="margin: 0; font-size: 2rem;">💬</h3>
            <h2 style="margin: 0.5rem 0; font-size: 1.5rem;">Total Comments</h2>
        </div>
        """, unsafe_allow_html=True)
        st.metric("Total Comments", f"{total_comments:,}", help="Total comments across all posts", label_visibility="collapsed")
    
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
        st.metric("Avg Engagement", f"{avg_engagement:.1f}", help="Average engagement per post (likes + comments)", label_visibility="collapsed")
    
    # Top 5 Posts by Engagement
    st.markdown("---")
    st.markdown("### 🏆 Top 5 Posts by Engagement")
    
    # Calculate engagement for each post
    posts_with_engagement = []
    for post in posts:
        likes = post.get('likes', 0)
        comments = post.get('comments_count', 0)
        engagement = likes + comments
        posts_with_engagement.append({
            'post_id': post.get('post_id', ''),
            'text': post.get('text', '')[:100] + '...' if len(post.get('text', '')) > 100 else post.get('text', ''),
            'likes': likes,
            'comments': comments,
            'engagement': engagement,
            'type': post.get('type', 'Unknown')
        })
    
    # Sort by engagement and get top 5
    top_posts = sorted(posts_with_engagement, key=lambda x: x['engagement'], reverse=True)[:5]
    
    if top_posts:
        top_posts_df = pd.DataFrame(top_posts)
        if PLOTLY_AVAILABLE:
            fig = px.bar(top_posts_df, x='engagement', y='text', orientation='h', 
                        title="Top 5 Posts by Engagement",
                        color_discrete_sequence=['#495E57'])
            fig.update_layout(
                plot_bgcolor='#F5F7F8',
                paper_bgcolor='#F5F7F8',
                font_color='#45474B',
                height=400
            )
            st.plotly_chart(fig, width='stretch')
        else:
            st.bar_chart(top_posts_df.set_index('text')['engagement'])
    
    # Total Engagement Breakdown
    st.markdown("---")
    st.markdown("### 📊 Total Engagement Breakdown")
    
    engagement_data = pd.DataFrame({
        'Metric': ['Likes', 'Comments'],
        'Count': [total_likes, total_comments]
    })
    
    if PLOTLY_AVAILABLE:
        fig = px.bar(engagement_data, x='Metric', y='Count', title="Total Engagement Breakdown",
                    color_discrete_sequence=['#495E57', '#F4CE14'])
        fig.update_layout(
            plot_bgcolor='#F5F7F8',
            paper_bgcolor='#F5F7F8',
            font_color='#45474B'
        )
        st.plotly_chart(fig, width='stretch')
    else:
        st.bar_chart(engagement_data.set_index('Metric'))
    
    # Content Type Analysis
    content_types = Counter(post.get('type', 'Unknown') for post in posts)
    if content_types:
        st.markdown("---")
        st.markdown("### 📱 Content Type Distribution")
        content_df = pd.DataFrame(list(content_types.items()), columns=['Type', 'Count'])
        if PLOTLY_AVAILABLE:
            fig = px.pie(content_df, values='Count', names='Type', title="Content Type Distribution",
                        color_discrete_sequence=['#495E57', '#F4CE14', '#45474B'])
            fig.update_layout(
                plot_bgcolor='#F5F7F8',
                paper_bgcolor='#F5F7F8',
                font_color='#45474B'
            )
            st.plotly_chart(fig, width='stretch')
        else:
            st.bar_chart(content_df.set_index('Type'))
    
    # Hashtag Analysis
    all_hashtags = []
    for post in posts:
        hashtags = post.get('hashtags', [])
        if isinstance(hashtags, list):
            all_hashtags.extend(hashtags)
    
    if all_hashtags:
        st.markdown("---")
        st.markdown("### #️⃣ Top Hashtags")
        top_hashtags = Counter(all_hashtags).most_common(10)
        hashtag_df = pd.DataFrame(top_hashtags, columns=['Hashtag', 'Count'])
        if PLOTLY_AVAILABLE:
            fig = px.bar(hashtag_df, x='Count', y='Hashtag', orientation='h', title="Top Hashtags",
                        color_discrete_sequence=['#495E57'])
            fig.update_layout(
                plot_bgcolor='#F5F7F8',
                paper_bgcolor='#F5F7F8',
                font_color='#45474B'
            )
            st.plotly_chart(fig, width='stretch')
        else:
            st.bar_chart(hashtag_df.set_index('Hashtag'))

def create_instagram_monthly_insights(posts: List[Dict], platform: str):
    """Create monthly Instagram insights with word cloud, sentiment, and emoji analysis."""
    if platform != "Instagram":
        return
    
    st.markdown("---")
    st.markdown("### 💡 Monthly Instagram Insights")
    
    # Aggregate all comments for analysis
    all_comments = aggregate_all_comments(posts)
    
    if all_comments:
        # Create two columns for insights
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 💬 Monthly Comments Word Cloud")
            # Create larger word cloud for monthly insights
            create_wordcloud(all_comments, width=1200, height=600, figsize=(15, 8))
        
        with col2:
            st.markdown("#### 😊 Monthly Sentiment Distribution")
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
        
        # Emoji Analysis
        st.markdown("---")
        st.markdown("#### 😀 Emoji Analysis")
        emoji_analysis = analyze_emojis_in_comments(all_comments)
        if emoji_analysis:
            emoji_df = pd.DataFrame(list(emoji_analysis.items()), columns=['Emoji', 'Count'])
            if PLOTLY_AVAILABLE:
                fig = px.bar(emoji_df.head(15), x='Count', y='Emoji', orientation='h', 
                            title="Most Used Emojis in Comments",
                            color_discrete_sequence=['#495E57'])
                fig.update_layout(
                    plot_bgcolor='#F5F7F8',
                    paper_bgcolor='#F5F7F8',
                    font_color='#45474B'
                )
                st.plotly_chart(fig, width='stretch')
            else:
                st.bar_chart(emoji_df.set_index('Emoji'))
        else:
            st.info("No emojis found in comments")
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

def analyze_emojis_in_comments(comments: List[str]) -> Dict[str, int]:
    """Analyze emojis in comments and return frequency count."""
    # Emoji regex pattern
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    
    emoji_counts = Counter()
    
    for comment in comments:
        if comment:
            emojis = emoji_pattern.findall(comment)
            emoji_counts.update(emojis)
    
    return dict(emoji_counts.most_common(20))  # Top 20 emojis

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
            # Create two columns for analysis
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
            emoji_analysis = analyze_emojis_in_comments(comment_texts)
            if emoji_analysis:
                emoji_df = pd.DataFrame(list(emoji_analysis.items()), columns=['Emoji', 'Count'])
                if PLOTLY_AVAILABLE:
                    fig = px.bar(emoji_df.head(10), x='Count', y='Emoji', orientation='h', 
                                title="Most Used Emojis in This Post's Comments",
                                color_discrete_sequence=['#495E57'])
                    fig.update_layout(
                        plot_bgcolor='#F5F7F8',
                        paper_bgcolor='#F5F7F8',
                        font_color='#45474B'
                    )
                    st.plotly_chart(fig, width='stretch')
                else:
                    st.bar_chart(emoji_df.set_index('Emoji'))
            else:
                st.info("No emojis found in this post's comments")
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
    "YouTube": re.compile(r"^https?://(www\.)?(youtube\.com/(watch\?v=|channel/|@)|youtu\.be/)[^/?#]+", re.IGNORECASE),
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
        layout="wide"
    )
    
    st.title("📊 Social Media Analytics Dashboard")
    st.markdown("Analyze Facebook, Instagram, and YouTube content with AI-powered insights")
    
    # Check for API token
    try:
        apify_token = os.environ.get('APIFY_TOKEN', 'apify_api_14gYxq0ETCby20EvyECx9plcTt0DgO4uSyss')

        # apify_token = st.secrets.get("APIFY_TOKEN") or os.environ.get("APIFY_TOKEN")
    except Exception:
        apify_token = os.environ.get("APIFY_TOKEN")
    
    if not apify_token:
        st.error("⚠️ APIFY_TOKEN not set (st.secrets or environment).")
        st.stop()
    
    # Sidebar - Platform Selection
    st.sidebar.title("Platform Selection")
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
    data_source = st.sidebar.radio(
        "Choose data source:",
        ["Fetch from API", "Load from File"],
        help="Select whether to fetch new data from API or load previously saved data"
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
                help="Choose how to extract comments: individual posts (slower but more reliable) or batch processing (faster but may have limitations)"
            )
            
            fetch_detailed_comments = st.sidebar.checkbox(
                "Fetch Detailed Comments",
                value=False,  # Default to False due to actor issues
                help="Fetch detailed comments for Facebook posts using the Comments Scraper actor (currently having issues - may fail)"
            )
            
        elif platform == "Instagram":
            st.sidebar.markdown("### 💬 Instagram Comments")
            st.sidebar.info("💡 **Tip:** Instagram Posts Scraper only provides comment counts. Enable 'Fetch Detailed Comments' to get actual comment text for word clouds and sentiment analysis.")
            st.sidebar.info("💰 **Cost:** Instagram comments cost $2.30 per 1,000 comments. Free plan includes $5 monthly credits (2,100+ comments).")
            
            fetch_detailed_comments = st.sidebar.checkbox(
                "Fetch Detailed Comments",
                value=False,  # Default to False to avoid costs
                help="Fetch detailed comments for Instagram posts using the Instagram Comments Scraper (pay-per-result pricing)"
            )
            
            # Instagram uses batch processing by default
            comment_method = "Batch Processing"
            
        else:
            # YouTube or other platforms
            st.sidebar.markdown("### 💬 Comments")
            st.sidebar.info("💡 **Tip:** Enable 'Fetch Detailed Comments' to get actual comment text for word clouds and sentiment analysis.")
            
            fetch_detailed_comments = st.sidebar.checkbox(
                "Fetch Detailed Comments",
                value=False,
                help="Fetch detailed comments for posts"
            )
            
            comment_method = "Batch Processing"
        
        # Additional options for batch processing
        if comment_method == "Batch Processing" and fetch_detailed_comments:
            max_comments_per_post = st.sidebar.slider(
                "Max Comments per Post",
                min_value=10,
                max_value=100,
                value=25,
                help="Maximum number of comments to extract per post"
            )
        else:
            max_comments_per_post = 25
    else:
        fetch_detailed_comments = False
        comment_method = "Individual Posts"
        max_comments_per_post = 25
        max_posts = 10
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
    
    # Initialize session state
    if 'posts_data' not in st.session_state:
        st.session_state.posts_data = None
    if 'selected_post_idx' not in st.session_state:
        st.session_state.selected_post_idx = None
    
    # Store analysis preferences in session state
    st.session_state.use_phrase_analysis = use_phrase_analysis
    st.session_state.use_sentiment_coloring = use_sentiment_coloring
    st.session_state.use_simple_wordcloud = use_simple_wordcloud
    
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
        # For file loading, we don't need URL input
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
            st.warning("Please enter a URL")
            st.stop()
        
        if not validate_url(url, platform):
            st.error(f"Invalid {platform} URL. Please check and try again.")
            st.stop()
        
        # ═══════════════════════════════════════════════════════════
        # INSTAGRAM WORKFLOW - STEP 1: FETCH POSTS (First Scraper)
        # ═══════════════════════════════════════════════════════════
        # Fetch data
        with st.spinner(f"Fetching data from {platform}..."):
            raw_data = fetch_apify_data(platform, url, apify_token, max_posts, from_date, to_date)
        
        if not raw_data:
            st.error("No data returned from Apify. Check your actor configuration and URL.")
            st.stop()
        
        # Phase 1: Normalize posts (without comment fetching)
        with st.spinner("🔄 Processing posts..."):
                normalized_data = normalize_post_data(raw_data, platform)
        
        st.info(f"✅ Successfully processed {len(normalized_data)} posts")
        
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
                        normalized_data = fetch_comments_for_posts(normalized_data, apify_token)
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
        
        # Save data to files
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
            else:
                # Facebook/YouTube analysis (existing code)
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
        
        if all_comments:
            # Create two columns for insights
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
        
        st.dataframe(display_df, width='stretch', height=300)
        
        # CSV Download Button
        st.download_button(
            "⬇️ Download processed CSV",
            data=df.to_csv(index=False).encode('utf-8'),
            file_name=f"{platform.lower()}_{datetime.now().strftime('%Y_%m')}.csv",
            mime="text/csv",
            width='stretch',
        )
        
        # ═══════════════════════════════════════════════════════════
        # INSTAGRAM WORKFLOW - STEP 4: SHOW POST DETAILS ANALYSIS
        # ═══════════════════════════════════════════════════════════
        # Post selection
        st.markdown("### 🎯 Select a Post for Detailed Analysis")
        post_options = []
        for i, p in enumerate(posts):
            text = p.get('text', '')
            # Handle case where text might be a float or None
            if isinstance(text, (int, float)):
                text = str(text)
            elif text is None:
                text = "No text content"
            else:
                text = str(text)
            
            # Truncate text for display
            display_text = text[:60] + "..." if len(text) > 60 else text
            post_options.append(f"Post {i+1}: {display_text}")
        
        selected_idx = st.selectbox("Choose a post:", range(len(posts)), format_func=lambda x: post_options[x])
        
        if selected_idx is not None:
            st.session_state.selected_post_idx = selected_idx
            selected_post = posts[selected_idx]
            
            st.markdown("---")
            st.markdown("### 🔍 Post Details")
            
            # Post info
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown(f"**Caption:** {selected_post['text']}")
                # Handle timezone-aware datetime objects and None values for display
                pub_date = selected_post['published_at']
                if pub_date is None:
                    pub_date_display = "Unknown"
                else:
                    if hasattr(pub_date, 'tz') and pub_date.tz is not None:
                        pub_date = pub_date.tz_localize(None)
                    pub_date_display = pub_date.strftime('%Y-%m-%d %H:%M') if pd.notna(pub_date) else "Unknown"
                st.markdown(f"**Published:** {pub_date_display}")
            
            with col2:
                if platform == "Instagram":
                    # Instagram-specific metrics
                    st.metric("Likes", selected_post['likes'])
                    st.metric("Comments", selected_post['comments_count'])
                    if selected_post.get('type'):
                        st.metric("Type", selected_post['type'])
                else:
                    # Facebook/YouTube metrics
                    st.metric("Shares", selected_post['shares_count'])
                    st.metric("Comments", selected_post['comments_count'])
            
            # Platform-specific analysis
            if platform == "Instagram":
                # Instagram-specific post details
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
                
                if selected_post.get('ownerUsername'):
                    st.markdown("#### 👤 Post Owner")
                    st.write(f"**Username:** @{selected_post['ownerUsername']}")
                    if selected_post.get('ownerFullName'):
                        st.write(f"**Full Name:** {selected_post['ownerFullName']}")
                
                if selected_post.get('displayUrl'):
                    st.markdown("#### 🖼️ Media")
                    st.image(selected_post['displayUrl'], width=300)
                
                # Individual post analysis
                create_instagram_post_analysis(selected_post, platform)
            else:
                # Facebook/YouTube reactions pie chart
                reactions = selected_post.get('reactions', {})
                if isinstance(reactions, dict) and reactions:
                    st.markdown("#### Reaction Breakdown")
                    create_reaction_pie_chart(reactions)
                else:
                    # If no reaction breakdown, show simple metrics
                    st.info("Detailed reaction data not available for this post")
            
            # Comments section - platform-specific display
            if platform == "Instagram":
                st.markdown("#### 💬 Instagram Comments")
                comments_list = selected_post.get('comments_list', [])
                
                if isinstance(comments_list, list) and comments_list:
                    # Show individual Instagram comments
                    st.info(f"📊 Found {len(comments_list)} comments for this post")
                    
                    # Display comments in a nice format
                    for i, comment in enumerate(comments_list, 1):
                        if isinstance(comment, dict):
                            # Instagram comment format
                            comment_text = comment.get('text', '')
                            owner_username = comment.get('ownerUsername', 'Unknown')
                            timestamp = comment.get('timestamp', '')
                            
                            if comment_text:
                                with st.expander(f"💬 Comment {i} by @{owner_username}", expanded=False):
                                    st.write(f"**@{owner_username}:** {comment_text}")
                                    if timestamp:
                                        st.caption(f"Posted: {timestamp}")
                        elif isinstance(comment, str) and comment.strip():
                            st.write(f"**Comment {i}:** {comment}")
                elif isinstance(comments_list, int):
                    st.info(f"📊 Comments count: {comments_list}")
                    st.warning("💡 **To see actual comments:** Enable 'Fetch Detailed Comments' in the sidebar and re-analyze the page.")
                    st.info("This will use the Instagram Comments Scraper to extract actual comment text.")
                else:
                    st.info("No comments found for this Instagram post.")
            else:
                # Facebook/YouTube comments word cloud
                st.markdown("#### 💬 Comments Word Cloud")
                comments_list = selected_post.get('comments_list', [])
                
                # Extract text from comments (handle various formats)
                comment_texts = []
                
                # Check if comments_list is actually a list, not just a count
                if isinstance(comments_list, list):
                    for comment in comments_list:
                        if isinstance(comment, str):
                            comment_texts.append(comment)
                        elif isinstance(comment, dict):
                            text = comment.get('text') or comment.get('comment') or comment.get('message', '')
                            if text:
                                comment_texts.append(text)
                elif isinstance(comments_list, int):
                    st.info(f"📊 Comments count: {comments_list}")
                    st.warning("💡 **To see comment word clouds:** Enable 'Fetch Detailed Comments' in the sidebar and re-analyze the page.")
                    st.info("This will use the Facebook Comments Scraper to extract actual comment text for analysis.")
                else:
                    st.info("No comment data available for word cloud.")
            
            # Only show word cloud for Facebook/YouTube (not Instagram)
            if platform != "Instagram" and comment_texts:
                create_wordcloud(comment_texts)
                
                # Optional: Show sentiment distribution
                with st.expander("📊 Sentiment Analysis (Beta)"):
                    sentiments = [analyze_sentiment_placeholder(c) for c in comment_texts]
                    sentiment_counts = pd.Series(sentiments).value_counts()
                    
                    st.subheader("💭 Comment Sentiment Distribution")
                    sentiment_df = pd.DataFrame({
                        'Sentiment': sentiment_counts.index,
                        'Count': sentiment_counts.values
                    }).set_index('Sentiment')
                    st.bar_chart(sentiment_df)
            elif platform != "Instagram":
                st.info("No comments available for this post")

if __name__ == "__main__":
    main()
