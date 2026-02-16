"""
Platform Adapter Base Class
===========================

Defines the interface that all platform adapters must implement.
This ensures consistent behavior across Facebook, Instagram, and YouTube.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from datetime import datetime
import pandas as pd


def parse_published_at(timestamp) -> Optional[Any]:
    """
    Parse a timestamp from platform APIs into a timezone-naive datetime.

    Many APIs return milliseconds since Unix epoch; pandas treats numbers as
    nanoseconds by default, which produces 1970-01-01 for large ms values.
    This helper uses unit='ms' when the value is >= 1e12, else 's'.
    """
    if timestamp is None or (isinstance(timestamp, (int, float)) and timestamp == 0):
        return None
    try:
        if isinstance(timestamp, (int, float)):
            unit = "ms" if abs(timestamp) >= 1e12 else "s"
            dt = pd.to_datetime(timestamp, unit=unit, utc=True)
        else:
            dt = pd.to_datetime(timestamp, errors="coerce", utc=True)
        if pd.isna(dt):
            return None
        return dt.tz_convert(None)
    except Exception:
        return None


class PlatformAdapter(ABC):
    """
    Abstract base class for platform-specific data adapters.

    Each platform (Facebook, Instagram, YouTube) implements this interface
    to provide consistent data access and normalization.
    """

    def __init__(self, apify_token: str):
        """
        Initialize the adapter with Apify API credentials.

        Args:
            apify_token: Apify API token for authentication
        """
        self.apify_token = apify_token
        self.platform_name = self._get_platform_name()

    @abstractmethod
    def _get_platform_name(self) -> str:
        """Return the platform name (e.g., 'Facebook', 'Instagram', 'YouTube')."""
        pass

    @abstractmethod
    def get_actor_id(self) -> str:
        """Return the Apify actor ID for this platform."""
        pass

    @abstractmethod
    def validate_url(self, url: str) -> bool:
        """
        Validate if a URL is valid for this platform.

        Args:
            url: URL to validate

        Returns:
            True if URL is valid for this platform
        """
        pass

    @abstractmethod
    def build_actor_input(
        self,
        url: str,
        max_posts: int = 10,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build the input configuration for the Apify actor.

        Args:
            url: Platform URL to scrape
            max_posts: Maximum number of posts to fetch
            from_date: Start date for filtering (optional)
            to_date: End date for filtering (optional)

        Returns:
            Dictionary with actor input configuration
        """
        pass

    @abstractmethod
    def normalize_post(self, raw_post: Dict) -> Dict:
        """
        Normalize a single raw post from Apify into standard schema.

        Args:
            raw_post: Raw post data from Apify actor

        Returns:
            Normalized post with standard fields:
            - post_id: str
            - published_at: datetime/str
            - text: str
            - likes: int
            - comments_count: int
            - shares_count: int (if applicable)
            - reactions: dict (if applicable)
            - comments_list: list
            - post_url: str
            - [platform-specific fields]
        """
        pass

    @abstractmethod
    def normalize_comment(self, raw_comment: Dict) -> Dict:
        """
        Normalize a single raw comment into standard schema.

        Args:
            raw_comment: Raw comment data from Apify actor

        Returns:
            Normalized comment with standard fields:
            - comment_id: str
            - text: str
            - author_name: str
            - created_time: str/datetime
            - likes_count: int
        """
        pass

    @abstractmethod
    def calculate_engagement_rate(self, post: Dict) -> float:
        """
        Calculate engagement rate for a post.
        Platform-specific formula (e.g., YouTube uses views, FB uses reactions).

        Args:
            post: Normalized post data

        Returns:
            Engagement rate as percentage
        """
        pass

    def normalize_posts(self, raw_posts: List[Dict]) -> List[Dict]:
        """
        Normalize multiple posts.

        Args:
            raw_posts: List of raw post data from Apify

        Returns:
            List of normalized posts
        """
        normalized = []
        for raw_post in raw_posts:
            try:
                normalized_post = self.normalize_post(raw_post)
                normalized.append(normalized_post)
            except Exception as e:
                print(f"⚠️ Failed to normalize post: {e}")
                continue
        return normalized

    def normalize_comments(self, raw_comments: List[Dict]) -> List[Dict]:
        """
        Normalize multiple comments.

        Args:
            raw_comments: List of raw comment data

        Returns:
            List of normalized comments
        """
        normalized = []
        for raw_comment in raw_comments:
            try:
                normalized_comment = self.normalize_comment(raw_comment)
                normalized.append(normalized_comment)
            except Exception as e:
                print(f"⚠️ Failed to normalize comment: {e}")
                continue
        return normalized

    def filter_by_date_range(
        self,
        posts: List[Dict],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict]:
        """
        Filter posts by date range.

        Args:
            posts: List of normalized posts
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            Filtered list of posts
        """
        if not posts:
            return []

        filtered = []
        for post in posts:
            try:
                pub_date = pd.to_datetime(post.get("published_at"), errors="coerce")
                if pd.isna(pub_date):
                    continue

                if start_date and pub_date < start_date:
                    continue
                if end_date and pub_date > end_date:
                    continue

                filtered.append(post)
            except:
                continue

        return filtered

    def calculate_total_engagement(self, posts: List[Dict]) -> Dict[str, int]:
        """
        Calculate total engagement metrics across all posts.

        Args:
            posts: List of normalized posts

        Returns:
            Dictionary with engagement totals
        """
        total_likes = sum(post.get("likes", 0) for post in posts)
        total_comments = sum(post.get("comments_count", 0) for post in posts)
        total_shares = sum(post.get("shares_count", 0) for post in posts)

        return {
            "total_likes": total_likes,
            "total_comments": total_comments,
            "total_shares": total_shares,
            "total_posts": len(posts),
        }

    def get_top_posts(
        self, posts: List[Dict], top_n: int = 10, sort_by: str = "likes"
    ) -> List[Dict]:
        """
        Get top posts sorted by engagement metric.

        Args:
            posts: List of normalized posts
            top_n: Number of top posts to return
            sort_by: Metric to sort by ('likes', 'comments_count', 'engagement_rate')

        Returns:
            List of top posts
        """
        if not posts:
            return []

        # Calculate engagement rate for each post if not present
        for post in posts:
            if "engagement_rate" not in post:
                post["engagement_rate"] = self.calculate_engagement_rate(post)

        # Sort and return top N
        sorted_posts = sorted(posts, key=lambda p: p.get(sort_by, 0), reverse=True)

        return sorted_posts[:top_n]
