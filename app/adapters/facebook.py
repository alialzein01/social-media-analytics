"""
Facebook Platform Adapter
=========================

Handles Facebook-specific data fetching, normalization, and analysis.
"""

from typing import List, Dict, Optional, Any
import pandas as pd
from . import PlatformAdapter, parse_published_at


class FacebookAdapter(PlatformAdapter):
    """
    Adapter for Facebook data from Apify.

    Handles posts, comments, and reactions from Facebook pages.
    """

    def _get_platform_name(self) -> str:
        return "Facebook"

    def get_actor_id(self) -> str:
        """
        Return the Apify actor name for Facebook scraping.
        Uses the repository-standard posts actor `scraper_one/facebook-posts-scraper`.
        """
        return "scraper_one/facebook-posts-scraper"

    def validate_url(self, url: str) -> bool:
        """
        Validate Facebook URL format.

        Accepts:
        - https://www.facebook.com/PageName
        - https://facebook.com/PageName
        - facebook.com/PageName
        """
        if not url:
            return False

        url_lower = url.lower()
        return "facebook.com" in url_lower

    def build_actor_input(
        self,
        url: str,
        max_posts: int = 10,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build Facebook actor input configuration.
        Build input compatible with `scraper_one/facebook-posts-scraper`.
        This actor expects `pageUrls` (list) and `resultsLimit` (int).
        Date filtering is not universally supported by that actor; if
        `from_date`/`to_date` are provided they will be included where
        supported as `onlyPostsNewerThan` / `onlyPostsOlderThan`.
        """
        actor_input = {"pageUrls": [url], "resultsLimit": max_posts}

        # Add date filters if provided (ISO format: YYYY-MM-DD or relative like "3 days ago")
        if from_date:
            actor_input["onlyPostsNewerThan"] = from_date
        if to_date:
            actor_input["onlyPostsOlderThan"] = to_date

        return actor_input

    def normalize_post(self, raw_post: Dict) -> Dict:
        """
        Normalize Facebook post from Apify actor response.

        Maps actor fields to standard schema with Facebook-specific additions.
        """
        # Extract post_id and ensure it's a string
        post_id = raw_post.get("postId") or raw_post.get("id", "")

        # Extract text with fallback options
        post_text = (
            raw_post.get("postText")
            or raw_post.get("text")
            or raw_post.get("message")
            or raw_post.get("caption", "")
        )

        # Build normalized post
        post = {
            # Required fields
            "post_id": str(post_id) if post_id else "",
            "published_at": parse_published_at(
                raw_post.get("time") or raw_post.get("timestamp") or raw_post.get("createdTime", "")
            ),
            "text": str(post_text) if post_text and post_text != "" else "",
            # Engagement metrics
            "likes": raw_post.get("reactionsCount", 0) or raw_post.get("likes", 0),
            "comments_count": raw_post.get("commentsCount", 0) or raw_post.get("comments", 0),
            "shares_count": raw_post.get("shares", 0),
            # Facebook-specific
            "reactions": raw_post.get("reactions", {}),
            "comments_list": raw_post.get("commentsList", []) or raw_post.get("comments", []),
            # Metadata
            "post_url": (
                raw_post.get("url")
                or raw_post.get("postUrl")
                or raw_post.get("link")
                or raw_post.get("facebookUrl")
                or raw_post.get("pageUrl", "")
            ),
            "author": raw_post.get("author", {}),
            "attachments": raw_post.get("attachments", []),
        }

        return post

    def normalize_comment(self, raw_comment: Dict) -> Dict:
        """
        Normalize Facebook comment from Apify actor.
        """
        # Normalize common key variations from different actors
        likes = None
        # numeric-like values may be strings in some actor outputs
        if "likes_count" in raw_comment:
            likes = raw_comment.get("likes_count")
        elif "like_count" in raw_comment:
            likes = raw_comment.get("like_count")
        elif "likesCount" in raw_comment:
            likes = raw_comment.get("likesCount")

        # try to coerce likes to int
        try:
            likes_count = int(likes) if likes is not None and likes != "" else 0
        except Exception:
            likes_count = 0

        # map possible text fields
        text = (
            raw_comment.get("text")
            or raw_comment.get("message")
            or raw_comment.get("commentText")
            or raw_comment.get("comment", "")
        )

        # author name
        author = (
            raw_comment.get("author_name")
            or (raw_comment.get("from") or {}).get("name", "")
            or raw_comment.get("author")
        )

        # map facebookUrl -> post_url for backward compatibility
        post_url = (
            raw_comment.get("post_url")
            or raw_comment.get("facebookUrl")
            or raw_comment.get("facebook_url")
            or raw_comment.get("postUrl")
        )

        return {
            "comment_id": raw_comment.get("comment_id")
            or raw_comment.get("id", "")
            or raw_comment.get("cid", ""),
            "text": text,
            "author_name": author if isinstance(author, str) else str(author),
            "created_time": raw_comment.get("created_time")
            or raw_comment.get("created_at")
            or raw_comment.get("timestamp", ""),
            "likes_count": likes_count,
            "parent_id": raw_comment.get("parent_id", "") or raw_comment.get("replyToCid", ""),
            "replies_count": raw_comment.get("replies_count", 0)
            or raw_comment.get("replyCount", 0),
            "post_url": post_url,
        }

    def calculate_engagement_rate(self, post: Dict) -> float:
        """
        Calculate Facebook engagement rate.

        Formula: (Reactions + Comments + Shares) / Total Posts * 100
        Note: We don't have follower count, so we normalize per post.
        """
        reactions = self._count_total_reactions(post.get("reactions", {}))
        comments = post.get("comments_count", 0)
        shares = post.get("shares_count", 0)

        total_engagement = reactions + comments + shares

        # Return raw engagement if we don't have reach data
        return float(total_engagement)

    def _count_total_reactions(self, reactions: Dict) -> int:
        """
        Count total reactions from reactions dict.

        Args:
            reactions: Dict like {'like': 100, 'love': 50, ...}

        Returns:
            Total reaction count
        """
        if not isinstance(reactions, dict):
            return 0

        return sum(v for v in reactions.values() if isinstance(v, (int, float)))

    def get_reaction_breakdown(self, posts: List[Dict]) -> Dict[str, int]:
        """
        Get aggregated reaction breakdown across all posts.

        Args:
            posts: List of normalized Facebook posts

        Returns:
            Dict with total counts per reaction type
        """
        total_reactions = {}

        for post in posts:
            reactions = post.get("reactions", {})
            if isinstance(reactions, dict):
                for reaction_type, count in reactions.items():
                    if isinstance(count, (int, float)):
                        total_reactions[reaction_type] = (
                            total_reactions.get(reaction_type, 0) + count
                        )

        return total_reactions

    def get_posts_with_most_reactions(self, posts: List[Dict], top_n: int = 10) -> List[Dict]:
        """
        Get posts with highest reaction counts.

        Args:
            posts: List of normalized posts
            top_n: Number of top posts to return

        Returns:
            List of posts sorted by total reactions
        """
        # Add total_reactions field to each post
        for post in posts:
            post["total_reactions"] = self._count_total_reactions(post.get("reactions", {}))

        # Sort by total reactions
        sorted_posts = sorted(posts, key=lambda p: p.get("total_reactions", 0), reverse=True)

        return sorted_posts[:top_n]
