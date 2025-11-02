"""
Application Settings
===================

All configuration constants for the Social Media Analytics application.
"""

import re

# ============================================================================
# APIFY ACTOR CONFIGURATIONS
# ============================================================================

# Apify Actor Names/IDs - Main actors for fetching posts
ACTOR_CONFIG = {
    "Facebook": "zanTWNqB3Poz44qdY",  # Actor ID: scraper_one/facebook-posts-scraper
    "Instagram": "apify/instagram-scraper",
    "YouTube": "h7sDV53CddomktSi5"  # streamers~youtube-scraper
}

# YouTube Comments Scraper Actor ID (for second step)
YOUTUBE_COMMENTS_ACTOR_ID = "p7UMdpQnjKmmpR21D"

# Actor IDs for direct calls (when needed)
ACTOR_IDS = {
    "Facebook": "KoJrdxJCTtpon81KY",
    "Instagram": "shu8hvrXbJbY3Eb9W",
    "YouTube": "p7UMdpQnjKmmpR21D"
}

# Facebook Comments Scraper Actors (tried in order)
FACEBOOK_COMMENTS_ACTOR_IDS = [
    "us5srxAYnsrkgUv2v",  # Primary actor
    "apify/facebook-comments-scraper",
    "facebook-comments-scraper",
    "alien_force/facebook-posts-comments-scraper"
]

# Instagram Comments Scraper Actors (tried in order)
INSTAGRAM_COMMENTS_ACTOR_IDS = [
    "apify/instagram-comment-scraper",  # Primary
    "SbK00X0JYCPblD2wp",  # Alternative
    "instagram-comment-scraper",
    "apify/instagram-scraper"  # Fallback
]

# ============================================================================
# NLP CONFIGURATIONS
# ============================================================================

# Arabic stopwords (basic set - can be expanded)
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
# URL VALIDATION PATTERNS
# ============================================================================

# Pre-compiled URL validation patterns for performance
URL_PATTERNS = {
    "Facebook": re.compile(
        r"^https?://(www\.)?(facebook|fb)\.com/[^/?#]+",
        re.IGNORECASE
    ),
    "Instagram": re.compile(
        r"^https?://(www\.)?instagram\.com/[^/?#]+",
        re.IGNORECASE
    ),
    "YouTube": re.compile(
        r"^https?://(www\.)?(youtube\.com/(watch\?v=|channel/|@|c/|user/)|youtu\.be/)[^/?#]+",
        re.IGNORECASE
    ),
}

# ============================================================================
# APPLICATION SETTINGS
# ============================================================================

# Cache settings
CACHE_TTL = 3600  # 1 hour in seconds
MAX_CACHE_ENTRIES = 64

# Data fetching defaults
DEFAULT_MAX_POSTS = 10
DEFAULT_MAX_COMMENTS = 25
DEFAULT_TIMEOUT = 300  # 5 minutes in seconds

# Visualization defaults
WORDCLOUD_WIDTH = 800
WORDCLOUD_HEIGHT = 400
WORDCLOUD_FIGSIZE = (10, 5)
DEFAULT_TOP_N = 50

# File paths
DATA_RAW_DIR = "data/raw"
DATA_PROCESSED_DIR = "data/processed"

# Theme colors
THEME_COLORS = {
    'sage_green': '#495E57',
    'golden_yellow': '#F4CE14',
    'dark_grey': '#45474B',
    'light_grey': '#F5F7F8'
}
