# Platform Adapters - Architecture Guide

## Overview

The platform adapter pattern provides a **clean, consistent interface** for working with different social media platforms (Facebook, Instagram, YouTube). Each adapter handles platform-specific data normalization, validation, and metrics calculation.

---

## Architecture

```
app/adapters/
├── __init__.py          # PlatformAdapter base class
├── facebook.py          # FacebookAdapter
├── instagram.py         # InstagramAdapter
└── youtube.py           # YouTubeAdapter
```

### Class Hierarchy

```
PlatformAdapter (Abstract Base Class)
├── FacebookAdapter
├── InstagramAdapter
└── YouTubeAdapter
```

---

## Core Concepts

### 1. Consistent Interface

All adapters implement the same methods:

- `normalize_post()` - Convert raw data to standard schema
- `normalize_comment()` - Convert raw comments
- `calculate_engagement_rate()` - Platform-specific engagement calculation
- `validate_url()` - URL validation
- `build_actor_input()` - Apify actor configuration

### 2. Platform-Specific Features

Each adapter adds platform-specific methods:

**Facebook:**

- `get_reaction_breakdown()` - Aggregate reactions (like, love, wow, etc.)
- `get_posts_with_most_reactions()` - Top posts by reactions

**Instagram:**

- `extract_hashtags()` - Extract all hashtags
- `get_top_hashtags()` - Most used hashtags
- `get_posts_by_type()` - Group by Image/Video/Sidecar
- `calculate_video_metrics()` - Video-specific analytics

**YouTube:**

- `calculate_watch_time_estimate()` - Estimate total watch hours
- `get_viral_videos()` - Identify viral content
- `calculate_like_dislike_ratio()` - Like/dislike metrics

---

## Usage Examples

### Basic Usage

```python
from app.adapters.facebook import FacebookAdapter

# Initialize adapter
adapter = FacebookAdapter(apify_token="your_token")

# Validate URL
if adapter.validate_url("https://facebook.com/NASA"):
    print("Valid Facebook URL")

# Normalize raw data from Apify
raw_posts = [...]  # From Apify actor
normalized = adapter.normalize_posts(raw_posts)

# Calculate engagement
engagement = adapter.calculate_total_engagement(normalized)
print(f"Total likes: {engagement['total_likes']}")
```

### Facebook-Specific Features

```python
from app.adapters.facebook import FacebookAdapter

adapter = FacebookAdapter(apify_token="token")
posts = adapter.normalize_posts(raw_data)

# Get reaction breakdown
reactions = adapter.get_reaction_breakdown(posts)
# {'like': 1000, 'love': 500, 'wow': 200, ...}

# Get top posts by reactions
top_posts = adapter.get_posts_with_most_reactions(posts, top_n=10)
for post in top_posts:
    print(f"{post['total_reactions']} reactions - {post['text'][:50]}")
```

### Instagram-Specific Features

```python
from app.adapters.instagram import InstagramAdapter

adapter = InstagramAdapter(apify_token="token")
posts = adapter.normalize_posts(raw_data)

# Extract hashtags
top_tags = adapter.get_top_hashtags(posts, top_n=20)
for tag, count in top_tags:
    print(f"#{tag}: {count} posts")

# Group by post type
by_type = adapter.get_posts_by_type(posts)
print(f"Images: {len(by_type.get('Image', []))}")
print(f"Videos: {len(by_type.get('Video', []))}")

# Video metrics
video_stats = adapter.calculate_video_metrics(posts)
print(f"Avg views per video: {video_stats['avg_views_per_video']}")
```

### YouTube-Specific Features

```python
from app.adapters.youtube import YouTubeAdapter

adapter = YouTubeAdapter(apify_token="token")
videos = adapter.normalize_posts(raw_data)

# Engagement rate (includes views)
for video in videos:
    rate = adapter.calculate_engagement_rate(video)
    print(f"{video['text'][:40]}: {rate}% engagement")

# Watch time estimates
watch_metrics = adapter.calculate_watch_time_estimate(videos)
print(f"Estimated watch hours: {watch_metrics['estimated_watch_hours']}")

# Find viral videos
viral = adapter.get_viral_videos(videos, threshold_percentile=0.9)
print(f"Found {len(viral)} viral videos (top 10%)")
```

---

## Standard Schema

All adapters normalize data to this common schema:

### Post Schema

```python
{
    # Required fields (all platforms)
    'post_id': str,
    'published_at': datetime/str,
    'text': str,
    'likes': int,
    'comments_count': int,
    'comments_list': list,

    # Common optional
    'shares_count': int,
    'reactions': dict,
    'post_url': str,

    # Platform-specific fields
    # ... (see below)
}
```

### Facebook-Specific Fields

```python
{
    'reactions': dict,           # {'like': 100, 'love': 50, ...}
    'shares_count': int,
    'post_url': str,
    'author': dict,
    'attachments': list
}
```

### Instagram-Specific Fields

```python
{
    'post_url': str,             # https://instagram.com/p/{shortCode}/
    'type': str,                 # 'Image', 'Video', 'Sidecar'
    'ownerUsername': str,
    'ownerFullName': str,
    'hashtags': list,
    'mentions': list,
    'displayUrl': str,
    'dimensionsHeight': int,
    'dimensionsWidth': int,
    'isSponsored': bool,
    'videoViewCount': int,
    'videoPlayCount': int
}
```

### YouTube-Specific Fields

```python
{
    'views': int,
    'duration': str,             # ISO 8601 format (PT1H2M3S)
    'channel': str,
    'url': str,                  # Video URL
    'video_id': str,
    'video_title': str,
    'thumbnail_url': str,
    'channel_id': str,
    'channel_username': str,
    'subscriber_count': int,
    'dislikes': int,
    'category': str
}
```

---

## Testing

All adapters are tested with real Apify data:

```bash
# Run adapter tests
python3 test_adapters.py
```

### Test Results

```
✅ FACEBOOK ADAPTER: PASS
  - URL validation ✓
  - Post normalization ✓
  - Reaction breakdown ✓
  - Top posts ✓

✅ INSTAGRAM ADAPTER: PASS
  - URL validation ✓
  - Post normalization ✓
  - Hashtag extraction ✓
  - Video metrics ✓

✅ YOUTUBE ADAPTER: PASS
  - URL validation ✓
  - Video normalization ✓
  - Watch time calculation ✓
  - Viral detection ✓
```

---

## Benefits

### 1. **Separation of Concerns**

- Platform logic isolated from UI code
- Easy to test each platform independently
- Clear responsibility boundaries

### 2. **Extensibility**

- Easy to add new platforms (TikTok, Twitter, etc.)
- Platform-specific features don't pollute common code
- Consistent interface for all platforms

### 3. **Maintainability**

- Changes to one platform don't affect others
- Clear documentation of platform differences
- Type hints and docstrings for better IDE support

### 4. **Testability**

- Each adapter can be tested in isolation
- Mock data easy to create
- Platform-specific edge cases handled locally

---

## Migration from Monolithic Code

### Before (Monolithic)

```python
def normalize_post_data(raw_data, platform):
    normalized = []
    for item in raw_data:
        if platform == "Facebook":
            # 50 lines of FB logic
        elif platform == "Instagram":
            # 50 lines of IG logic
        elif platform == "YouTube":
            # 50 lines of YT logic
    return normalized
```

### After (Adapter Pattern)

```python
# Get the right adapter
adapters = {
    'Facebook': FacebookAdapter(token),
    'Instagram': InstagramAdapter(token),
    'YouTube': YouTubeAdapter(token)
}

adapter = adapters[platform]

# One line of code!
normalized = adapter.normalize_posts(raw_data)
```

---

## Next Steps

### Integration with Main App

1. **Replace normalization code:**

   ```python
   # OLD: normalize_post_data(raw_data, platform)
   # NEW: adapter.normalize_posts(raw_data)
   ```

2. **Use platform-specific features:**

   ```python
   if platform == "Facebook":
       reactions = adapter.get_reaction_breakdown(posts)
       # Show reaction pie chart
   elif platform == "Instagram":
       top_tags = adapter.get_top_hashtags(posts)
       # Show hashtag cloud
   ```

3. **Simplify data fetching:**
   ```python
   actor_input = adapter.build_actor_input(url, max_posts=50)
   # Pass to Apify client
   ```

---

## File Organization

```
app/adapters/
│
├── __init__.py              # Base class + exports
│   └── PlatformAdapter      # Abstract base class (280 lines)
│
├── facebook.py              # Facebook implementation
│   └── FacebookAdapter      # (230 lines)
│       ├── normalize_post()
│       ├── get_reaction_breakdown()
│       └── get_posts_with_most_reactions()
│
├── instagram.py             # Instagram implementation
│   └── InstagramAdapter     # (220 lines)
│       ├── normalize_post()
│       ├── extract_hashtags()
│       ├── get_top_hashtags()
│       ├── get_posts_by_type()
│       └── calculate_video_metrics()
│
└── youtube.py               # YouTube implementation
    └── YouTubeAdapter       # (270 lines)
        ├── normalize_post()
        ├── calculate_watch_time_estimate()
        ├── get_viral_videos()
        └── calculate_like_dislike_ratio()
```

**Total:** ~1000 lines of clean, tested, documented code replacing ~500 lines of tangled monolithic logic.

---

## API Reference

### PlatformAdapter (Base Class)

```python
class PlatformAdapter(ABC):
    def __init__(self, apify_token: str)

    # Abstract methods (must implement)
    @abstractmethod
    def normalize_post(raw_post: Dict) -> Dict
    @abstractmethod
    def normalize_comment(raw_comment: Dict) -> Dict
    @abstractmethod
    def calculate_engagement_rate(post: Dict) -> float
    @abstractmethod
    def validate_url(url: str) -> bool
    @abstractmethod
    def build_actor_input(...) -> Dict

    # Concrete methods (inherited)
    def normalize_posts(raw_posts: List[Dict]) -> List[Dict]
    def normalize_comments(raw_comments: List[Dict]) -> List[Dict]
    def filter_by_date_range(...) -> List[Dict]
    def calculate_total_engagement(posts: List[Dict]) -> Dict
    def get_top_posts(posts: List[Dict], ...) -> List[Dict]
```

---

**Status:** ✅ Adapters complete and tested  
**Next:** Create data fetching service layer
