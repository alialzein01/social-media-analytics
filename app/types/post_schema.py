"""
Normalized post schema and normalization-on-load.

Single source of truth for post shape so adapters, load-from-file, and DB
all produce the same structure. Missing keys are filled with defaults.
"""

from typing import Any, Dict, List

# Keys that every normalized post must have (with defaults if missing)
NORMALIZED_POST_DEFAULTS: Dict[str, Any] = {
    "post_id": "",
    "published_at": None,
    "text": "",
    "likes": 0,
    "comments_count": 0,
    "shares_count": 0,
    "reactions": {},
    "comments_list": [],
    "post_url": "",
    "author": {},
    "attachments": [],
}

# Optional platform-specific keys we preserve but don't require
OPTIONAL_KEYS = frozenset({
    "type", "views", "duration", "hashtags", "mentions",
    "displayUrl", "thumbnail_url", "channel", "channel_username",
    "subscriber_count", "ownerUsername", "ownerFullName", "url",
})


def normalize_post_to_schema(post: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure a post has the normalized schema. Fills missing keys with defaults.
    Preserves any extra keys (e.g. platform-specific) already on the post.

    Use after load from file or DB so older saves with different shape still work.
    """
    if not post or not isinstance(post, dict):
        return dict(NORMALIZED_POST_DEFAULTS)

    out = dict(NORMALIZED_POST_DEFAULTS)
    for key, default in NORMALIZED_POST_DEFAULTS.items():
        if key in post:
            val = post[key]
            # Ensure types
            if key == "reactions" and not isinstance(val, dict):
                val = {}
            if key == "comments_list" and not isinstance(val, list):
                val = []
            if key == "author" and not isinstance(val, dict):
                val = {}
            if key == "attachments" and not isinstance(val, list):
                val = []
            if key in ("likes", "comments_count", "shares_count") and not isinstance(val, (int, float)):
                try:
                    val = int(val) if val is not None else 0
                except (TypeError, ValueError):
                    val = 0
            out[key] = val
        else:
            out[key] = default

    # Preserve any other keys (platform-specific)
    for key, value in post.items():
        if key not in out:
            out[key] = value

    return out


def normalize_posts_to_schema(posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize a list of posts to the schema. Safe for empty or None."""
    if not posts:
        return []
    return [normalize_post_to_schema(p) for p in posts]
