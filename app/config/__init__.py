"""
Configuration Module
===================

Centralized configuration for the Social Media Analytics application.
"""

from .settings import (
    # Actor configurations
    ACTOR_CONFIG,
    ACTOR_IDS,
    FACEBOOK_COMMENTS_ACTOR_IDS,
    INSTAGRAM_COMMENTS_ACTOR_IDS,
    YOUTUBE_COMMENTS_ACTOR_ID,
    
    # NLP configurations
    ARABIC_STOPWORDS,
    ARABIC_LETTERS,
    TOKEN_RE,
    ARABIC_DIACRITICS,
    URL_PATTERN,
    MENTION_HASHTAG_PATTERN,
    
    # URL validation patterns
    URL_PATTERNS,
)

__all__ = [
    'ACTOR_CONFIG',
    'ACTOR_IDS',
    'FACEBOOK_COMMENTS_ACTOR_IDS',
    'INSTAGRAM_COMMENTS_ACTOR_IDS',
    'YOUTUBE_COMMENTS_ACTOR_ID',
    'ARABIC_STOPWORDS',
    'ARABIC_LETTERS',
    'TOKEN_RE',
    'ARABIC_DIACRITICS',
    'URL_PATTERN',
    'MENTION_HASHTAG_PATTERN',
    'URL_PATTERNS',
]
