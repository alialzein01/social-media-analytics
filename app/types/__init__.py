"""
Shared types and type aliases for the application.
"""

from typing import Any, Dict, List, Optional

from app.types.post_schema import (
    NORMALIZED_POST_DEFAULTS,
    normalize_post_to_schema,
    normalize_posts_to_schema,
)

# Generic JSON-serializable structure
JSONDict = Dict[str, Any]
JSONList = List[Dict[str, Any]]

__all__ = [
    "JSONDict",
    "JSONList",
    "NORMALIZED_POST_DEFAULTS",
    "normalize_post_to_schema",
    "normalize_posts_to_schema",
]
