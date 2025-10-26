"""
YouTube Platform Adapter
========================

Handles YouTube-specific data fetching, normalization, and analysis.
"""

from typing import List, Dict, Optional, Any
import pandas as pd
from . import PlatformAdapter


class YouTubeAdapter(PlatformAdapter):
    """
    Adapter for YouTube data from Apify.

    Handles videos, comments, views, and engagement from YouTube channels.
    """

    def _get_platform_name(self) -> str:
        return "YouTube"

    def get_actor_id(self) -> str:
        """
        Return the Apify actor ID for YouTube scraping.
        Using the community actor for channel videos.
        """
        return "streamers/youtube-scraper"

    def validate_url(self, url: str) -> bool:
        """
        Validate YouTube URL format.

        Accepts:
        - https://www.youtube.com/@channel
        - https://youtube.com/channel/CHANNEL_ID
        - youtube.com/@username
        """
        if not url:
            return False

        url_lower = url.lower()
        return 'youtube.com' in url_lower or 'youtu.be' in url_lower

    def build_actor_input(
        self,
        url: str,
        max_posts: int = 10,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build YouTube actor input configuration.

        Returns input dict for streamers/youtube-scraper.
        """
        actor_input = {
            "startUrls": [{"url": url}],
            "maxResults": max_posts,
            "searchKeywords": "",
            "channelId": ""
        }

        return actor_input

    def normalize_post(self, raw_post: Dict) -> Dict:
        """
        Normalize YouTube video from Apify actor response.

        Maps actor fields to standard schema with YouTube-specific additions.
        """
        # Extract video_id
        video_id = raw_post.get('id') or raw_post.get('videoId', '')

        # Build normalized post (video)
        post = {
            # Required fields
            'post_id': str(video_id) if video_id else '',
            'published_at': (
                raw_post.get('publishedAt') or
                raw_post.get('uploadDate') or
                raw_post.get('timestamp') or
                raw_post.get('date', '')
            ),
            'text': raw_post.get('title') or raw_post.get('description') or raw_post.get('text', ''),

            # Engagement metrics
            'likes': raw_post.get('likeCount') or raw_post.get('likes') or raw_post.get('likesCount', 0),
            'comments_count': raw_post.get('commentCount') or raw_post.get('comments') or raw_post.get('commentsCount', 0),
            'shares_count': raw_post.get('shareCount') or raw_post.get('shares') or raw_post.get('sharesCount', 0),

            # YouTube doesn't have detailed reactions like Facebook
            'reactions': raw_post.get('reactions', {}),
            'comments_list': [],  # Will be populated separately if needed

            # YouTube-specific fields
            'views': raw_post.get('viewCount') or raw_post.get('views', 0),
            'duration': raw_post.get('duration') or raw_post.get('lengthSeconds', ''),
            'channel': raw_post.get('channelName') or raw_post.get('channel', ''),
            'url': raw_post.get('url') or raw_post.get('videoUrl') or f"https://www.youtube.com/watch?v={video_id}",
            'video_id': video_id,
            'video_title': raw_post.get('title') or raw_post.get('videoTitle', ''),
            'thumbnail_url': raw_post.get('thumbnailUrl') or raw_post.get('thumbnail', ''),
            'channel_id': raw_post.get('channelId', ''),
            'channel_username': raw_post.get('channelUsername', ''),
            'subscriber_count': raw_post.get('numberOfSubscribers') or raw_post.get('subscriberCount', 0),
            'dislikes': raw_post.get('dislikeCount') or raw_post.get('dislikes', 0),
            'category': raw_post.get('category', '')
        }

        return post

    def normalize_comment(self, raw_comment: Dict) -> Dict:
        """
        Normalize YouTube comment from Apify actor.
        """
        return {
            'comment_id': raw_comment.get('id') or raw_comment.get('comment_id', ''),
            'text': raw_comment.get('text') or raw_comment.get('textDisplay', ''),
            'author_name': raw_comment.get('authorDisplayName') or raw_comment.get('author_name', ''),
            'created_time': raw_comment.get('publishedAt') or raw_comment.get('created_time', ''),
            'likes_count': raw_comment.get('likeCount') or raw_comment.get('likes_count', 0),
            'reply_count': raw_comment.get('replyCount', 0)
        }

    def calculate_engagement_rate(self, post: Dict) -> float:
        """
        Calculate YouTube engagement rate.

        Formula: (Likes + Comments) / Views * 100
        """
        likes = post.get('likes', 0)
        comments = post.get('comments_count', 0)
        views = post.get('views', 0)

        if views == 0:
            return 0.0

        engagement_rate = ((likes + comments) / views) * 100
        return round(engagement_rate, 2)

    def calculate_watch_time_estimate(self, posts: List[Dict]) -> Dict[str, Any]:
        """
        Estimate total watch time from views and duration.

        Args:
            posts: List of normalized YouTube videos

        Returns:
            Dict with watch time estimates
        """
        total_views = 0
        total_duration_seconds = 0
        videos_with_duration = 0

        for post in posts:
            views = post.get('views', 0)
            duration = post.get('duration', 0)

            # Try to convert duration to seconds if it's a string
            if isinstance(duration, str):
                duration_seconds = self._parse_duration(duration)
            else:
                duration_seconds = duration

            if duration_seconds > 0:
                total_views += views
                total_duration_seconds += duration_seconds
                videos_with_duration += 1

        # Estimate watch time (assuming 50% average view duration)
        avg_duration = total_duration_seconds / videos_with_duration if videos_with_duration > 0 else 0
        estimated_watch_seconds = total_views * avg_duration * 0.5

        return {
            'total_views': total_views,
            'estimated_watch_hours': round(estimated_watch_seconds / 3600, 2),
            'avg_video_duration_seconds': round(avg_duration, 2),
            'videos_analyzed': videos_with_duration
        }

    def get_viral_videos(self, posts: List[Dict], threshold_percentile: float = 0.9) -> List[Dict]:
        """
        Identify viral videos based on view count percentile.

        Args:
            posts: List of normalized videos
            threshold_percentile: Percentile threshold (0.9 = top 10%)

        Returns:
            List of viral videos
        """
        if not posts:
            return []

        # Calculate view threshold
        view_counts = [p.get('views', 0) for p in posts]
        threshold = pd.Series(view_counts).quantile(threshold_percentile)

        # Filter viral videos
        viral = [p for p in posts if p.get('views', 0) >= threshold]

        # Sort by views descending
        viral.sort(key=lambda p: p.get('views', 0), reverse=True)

        return viral

    def calculate_like_dislike_ratio(self, posts: List[Dict]) -> Dict[str, Any]:
        """
        Calculate like/dislike ratio across all videos.

        Note: YouTube removed public dislike counts, so this may not be accurate.

        Args:
            posts: List of normalized videos

        Returns:
            Dict with like/dislike metrics
        """
        total_likes = sum(p.get('likes', 0) for p in posts)
        total_dislikes = sum(p.get('dislikes', 0) for p in posts)

        ratio = total_likes / total_dislikes if total_dislikes > 0 else float('inf')

        return {
            'total_likes': total_likes,
            'total_dislikes': total_dislikes,
            'like_dislike_ratio': round(ratio, 2),
            'like_percentage': round((total_likes / (total_likes + total_dislikes) * 100), 2) if (total_likes + total_dislikes) > 0 else 0
        }

    def _parse_duration(self, duration_str: str) -> int:
        """
        Parse YouTube duration string (PT1H2M3S) to seconds.

        Args:
            duration_str: ISO 8601 duration string

        Returns:
            Duration in seconds
        """
        if not duration_str or not isinstance(duration_str, str):
            return 0

        try:
            # Remove 'PT' prefix
            duration_str = duration_str.replace('PT', '')

            hours = 0
            minutes = 0
            seconds = 0

            # Parse hours
            if 'H' in duration_str:
                hours_str, duration_str = duration_str.split('H')
                hours = int(hours_str)

            # Parse minutes
            if 'M' in duration_str:
                minutes_str, duration_str = duration_str.split('M')
                minutes = int(minutes_str)

            # Parse seconds
            if 'S' in duration_str:
                seconds_str = duration_str.replace('S', '')
                seconds = int(seconds_str)

            return hours * 3600 + minutes * 60 + seconds
        except:
            return 0
