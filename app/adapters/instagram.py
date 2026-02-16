"""
Instagram Platform Adapter
==========================

Handles Instagram-specific data fetching, normalization, and analysis.
"""

from typing import List, Dict, Optional, Any
import pandas as pd
from . import PlatformAdapter, parse_published_at


class InstagramAdapter(PlatformAdapter):
    """
    Adapter for Instagram data from Apify.

    Handles posts, comments, hashtags, and engagement from Instagram profiles.
    """

    def _get_platform_name(self) -> str:
        return "Instagram"

    def get_actor_id(self) -> str:
        """
        Return the Apify actor ID for Instagram scraping.
        Uses apify/instagram-scraper (single source of truth with app.config.settings.ACTOR_CONFIG).
        """
        return "apify/instagram-scraper"

    def validate_url(self, url: str) -> bool:
        """
        Validate Instagram URL format.

        Accepts:
        - https://www.instagram.com/username/
        - https://instagram.com/username
        - instagram.com/username
        """
        if not url:
            return False

        url_lower = url.lower()
        return "instagram.com" in url_lower

    def build_actor_input(
        self,
        url: str,
        max_posts: int = 10,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build Instagram actor input configuration.

        Returns input dict for apify/instagram-scraper (profile/post URLs).
        """
        actor_input = {
            "directUrls": [url],
            "resultsType": "posts",
            "resultsLimit": max_posts,
            "searchLimit": 10,
        }
        # apify/instagram-scraper supports onlyPostsNewerThan (YYYY-MM-DD or relative e.g. "30 days")
        if from_date:
            actor_input["onlyPostsNewerThan"] = from_date
        return actor_input

    def normalize_post(self, raw_post: Dict) -> Dict:
        """
        Normalize Instagram post from Apify actor response.

        Maps actor fields to standard schema with Instagram-specific additions.
        """
        # Extract post_id (shortCode is Instagram's post identifier)
        post_id = raw_post.get("shortCode") or raw_post.get("id", "")

        # Build normalized post
        post = {
            # Required fields
            "post_id": str(post_id) if post_id else "",
            "published_at": parse_published_at(raw_post.get("timestamp")),
            "text": raw_post.get("caption", ""),
            # Engagement metrics
            "likes": raw_post.get("likesCount", 0),
            "comments_count": raw_post.get("commentsCount", 0),
            "shares_count": 0,  # Instagram doesn't have public shares
            # Instagram doesn't have Facebook-style reactions
            "reactions": {},
            "comments_list": raw_post.get("latestComments", []),
            # Instagram-specific fields
            "post_url": f"https://www.instagram.com/p/{post_id}/" if post_id else "",
            "type": raw_post.get("type", ""),
            "displayUrl": raw_post.get("displayUrl", ""),
            "ownerUsername": raw_post.get("ownerUsername", ""),
            "ownerFullName": raw_post.get("ownerFullName", ""),
            "hashtags": raw_post.get("hashtags", []),
            "mentions": raw_post.get("mentions", []),
            "dimensionsHeight": raw_post.get("dimensionsHeight", 0),
            "dimensionsWidth": raw_post.get("dimensionsWidth", 0),
            "isSponsored": raw_post.get("isSponsored", False),
            "videoViewCount": raw_post.get("videoViewCount", 0),
            "videoPlayCount": raw_post.get("videoPlayCount", 0),
        }

        return post

    def normalize_comment(self, raw_comment: Dict) -> Dict:
        """
        Normalize Instagram comment from Apify actor.
        """
        return {
            "comment_id": raw_comment.get("id") or raw_comment.get("comment_id", ""),
            "text": raw_comment.get("text") or raw_comment.get("caption", ""),
            "author_name": raw_comment.get("ownerUsername") or raw_comment.get("author_name", ""),
            "created_time": raw_comment.get("timestamp") or raw_comment.get("created_time", ""),
            "likes_count": raw_comment.get("likesCount") or raw_comment.get("likes_count", 0),
        }

    def calculate_engagement_rate(self, post: Dict) -> float:
        """
        Calculate Instagram engagement rate.

        Formula: (Likes + Comments) / Total Posts * 100
        Note: Without follower count, we return raw engagement.
        """
        likes = post.get("likes", 0)
        comments = post.get("comments_count", 0)

        return float(likes + comments)

    def extract_hashtags(self, posts: List[Dict]) -> Dict[str, int]:
        """
        Extract and count all hashtags from posts.

        Args:
            posts: List of normalized Instagram posts

        Returns:
            Dict mapping hashtag to frequency count
        """
        hashtag_counts = {}

        for post in posts:
            hashtags = post.get("hashtags", [])
            if isinstance(hashtags, list):
                for tag in hashtags:
                    if tag:
                        # Remove # if present
                        clean_tag = tag.lstrip("#")
                        hashtag_counts[clean_tag] = hashtag_counts.get(clean_tag, 0) + 1

        return hashtag_counts

    def get_top_hashtags(self, posts: List[Dict], top_n: int = 20) -> List[tuple]:
        """
        Get most frequently used hashtags.

        Args:
            posts: List of normalized posts
            top_n: Number of top hashtags to return

        Returns:
            List of (hashtag, count) tuples sorted by frequency
        """
        hashtag_counts = self.extract_hashtags(posts)

        # Sort by count descending
        sorted_tags = sorted(hashtag_counts.items(), key=lambda x: x[1], reverse=True)

        return sorted_tags[:top_n]

    def get_posts_by_type(self, posts: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Group posts by type (Image, Video, Sidecar).

        Args:
            posts: List of normalized posts

        Returns:
            Dict mapping post type to list of posts
        """
        by_type = {}

        for post in posts:
            post_type = post.get("type", "Unknown")
            if post_type not in by_type:
                by_type[post_type] = []
            by_type[post_type].append(post)

        return by_type

    def calculate_video_metrics(self, posts: List[Dict]) -> Dict[str, Any]:
        """
        Calculate metrics specific to video posts.

        Args:
            posts: List of normalized posts

        Returns:
            Dict with video-specific metrics
        """
        video_posts = [p for p in posts if p.get("type") == "Video"]

        if not video_posts:
            return {"total_videos": 0, "total_views": 0, "avg_views_per_video": 0}

        total_views = sum(p.get("videoViewCount", 0) for p in video_posts)

        return {
            "total_videos": len(video_posts),
            "total_views": total_views,
            "avg_views_per_video": total_views / len(video_posts) if video_posts else 0,
            "most_viewed": max(video_posts, key=lambda p: p.get("videoViewCount", 0))
            if video_posts
            else None,
        }
