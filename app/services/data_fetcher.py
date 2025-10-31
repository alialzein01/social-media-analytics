"""
Data Fetching Service
=====================

Orchestrates all data fetching operations from Apify including:
- Posts/videos fetching
- Comments fetching (individual and batch)
- Data normalization coordination
"""

import time
import streamlit as st
from typing import List, Dict, Optional, Any
from apify_client import ApifyClient

from ..adapters.facebook import FacebookAdapter
from ..adapters.instagram import InstagramAdapter
from ..adapters.youtube import YouTubeAdapter


# Actor Configuration
ACTOR_CONFIG = {
    "Facebook": "apify~facebook-posts-scraper",  # KoJrdxJCTtpon81KY
    "Instagram": "apify/instagram-scraper",
    "YouTube": "h7sDV53CddomktSi5"
}

# Facebook Reactions Scraper
FACEBOOK_REACTIONS_ACTOR_ID = "scraper_one~facebook-reactions-scraper"  # ZwTmldxYpNvDnWW5f

# Comments Scraper Actors
FACEBOOK_COMMENTS_ACTOR_IDS = [
    "us5srxAYnsrkgUv2v",
    "apify/facebook-comments-scraper",
    "facebook-comments-scraper",
    "alien_force/facebook-posts-comments-scraper"
]

INSTAGRAM_COMMENTS_ACTOR_IDS = [
    "apify/instagram-comment-scraper",
    "SbK00X0JYCPblD2wp",
    "instagram-comment-scraper",
    "apify/instagram-scraper"
]

YOUTUBE_COMMENTS_ACTOR_ID = "p7UMdpQnjKmmpR21D"


class DataFetchingService:
    """
    Service for fetching and normalizing social media data from Apify.
    """

    def __init__(self, apify_token: str):
        """
        Initialize the data fetching service.

        Args:
            apify_token: Apify API token
        """
        self.apify_token = apify_token
        self.client = ApifyClient(apify_token)

        # Initialize adapters
        self.adapters = {
            'Facebook': FacebookAdapter(apify_token),
            'Instagram': InstagramAdapter(apify_token),
            'YouTube': YouTubeAdapter(apify_token)
        }

    def fetch_and_normalize_posts(
        self,
        platform: str,
        url: str,
        max_posts: int = 10,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> Optional[List[Dict]]:
        """
        Fetch posts from platform and normalize them.

        Args:
            platform: Platform name (Facebook, Instagram, YouTube)
            url: URL to scrape
            max_posts: Maximum number of posts to fetch
            from_date: Start date for filtering (YYYY-MM-DD)
            to_date: End date for filtering (YYYY-MM-DD)

        Returns:
            List of normalized posts or None if failed
        """
        # Fetch raw data
        raw_data = self._fetch_posts_raw(platform, url, max_posts, from_date, to_date)

        if not raw_data:
            return None

        # Normalize using adapter
        adapter = self.adapters.get(platform)
        if not adapter:
            st.error(f"No adapter found for {platform}")
            return None

        normalized_posts = []
        for raw_post in raw_data:
            try:
                normalized_post = adapter.normalize_post(raw_post)
                normalized_posts.append(normalized_post)
            except Exception as e:
                st.warning(f"Failed to normalize post: {str(e)}")
                continue

        st.success(f"✅ Normalized {len(normalized_posts)} posts")
        return normalized_posts

    def _fetch_posts_raw(
        self,
        platform: str,
        url: str,
        max_posts: int,
        from_date: Optional[str],
        to_date: Optional[str]
    ) -> Optional[List[Dict]]:
        """
        Fetch raw posts data from Apify actor.

        Args:
            platform: Platform name
            url: URL to scrape
            max_posts: Maximum posts
            from_date: Start date
            to_date: End date

        Returns:
            List of raw posts or None
        """
        try:
            actor_name = ACTOR_CONFIG.get(platform)
            if not actor_name:
                st.error(f"No actor configured for {platform}")
                return None

            # Build actor input
            run_input = self._build_actor_input(platform, url, max_posts, from_date, to_date)

            # Display info
            st.info(f"🔧 Actor: {actor_name}")
            st.info(f"📊 Requesting {max_posts} posts from: {url}")

            # Show date range (always show for Facebook)
            if from_date or to_date:
                date_info = "📅 Date range: "
                if from_date:
                    date_info += f"from {from_date} "
                if to_date:
                    date_info += f"to {to_date}"
                st.info(date_info)
            elif platform == "Facebook":
                # Show automatic 30-day range for Facebook
                from datetime import datetime, timedelta
                thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
                today = datetime.now().strftime("%Y-%m-%d")
                st.info(f"📅 Date range: Last 30 days ({thirty_days_ago} to {today})")

            # Run actor
            run = self.client.actor(actor_name).call(run_input=run_input)

            # Fetch results
            items = []
            for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                items.append(item)

            st.success(f"✅ Received {len(items)} posts from actor")
            return items

        except Exception as e:
            st.error(f"Apify API Error: {str(e)}")
            return None

    def _build_actor_input(
        self,
        platform: str,
        url: str,
        max_posts: int,
        from_date: Optional[str],
        to_date: Optional[str]
    ) -> Dict[str, Any]:
        """
        Build actor input configuration based on platform.

        Args:
            platform: Platform name
            url: URL to scrape
            max_posts: Maximum posts
            from_date: Start date
            to_date: End date

        Returns:
            Actor input dictionary
        """
        adapter = self.adapters.get(platform)
        if adapter:
            return adapter.build_actor_input(url, max_posts, from_date, to_date)

        # Fallback
        return {"startUrls": [{"url": url}], "maxPosts": max_posts}

    def fetch_comments_batch(
        self,
        posts: List[Dict],
        platform: str,
        max_comments_per_post: int = 25
    ) -> List[Dict]:
        """
        Fetch comments for all posts using batch processing.

        Args:
            posts: List of normalized posts
            platform: Platform name
            max_comments_per_post: Max comments per post

        Returns:
            Posts with comments added
        """
        if not posts:
            return posts

        st.info(f"🔄 Starting batch comment extraction for {len(posts)} posts...")

        # Extract post URLs
        post_urls = self._extract_post_urls(posts)

        if not post_urls:
            st.warning("⚠️ No valid post URLs found for comment extraction")
            return posts

        st.info(f"📋 Found {len(post_urls)} valid post URLs")

        # Fetch comments based on platform
        if platform == "Facebook":
            comments_data = self._fetch_facebook_comments_batch(post_urls, max_comments_per_post)
        elif platform == "Instagram":
            comments_data = self._fetch_instagram_comments_batch(post_urls, max_comments_per_post)
        elif platform == "YouTube":
            comments_data = self._fetch_youtube_comments_batch(post_urls, max_comments_per_post)
        else:
            st.error(f"Comment fetching not supported for {platform}")
            return posts

        if not comments_data:
            return posts

        # Assign comments to posts
        return self._assign_comments_to_posts(posts, comments_data, platform)

    def fetch_comments_individual(
        self,
        posts: List[Dict],
        platform: str
    ) -> List[Dict]:
        """
        Fetch comments for posts individually (slower but more reliable).

        Args:
            posts: List of normalized posts
            platform: Platform name

        Returns:
            Posts with comments added
        """
        if not posts:
            return posts

        st.info(f"🔄 Fetching detailed comments for {len(posts)} posts...")

        progress_bar = st.progress(0)
        status_text = st.empty()

        adapter = self.adapters.get(platform)

        for i, post in enumerate(posts):
            progress = (i + 1) / len(posts)
            progress_bar.progress(progress)
            status_text.text(f"Fetching comments for post {i+1}/{len(posts)}")

            # Check if comments needed
            if self._should_fetch_comments(post) and post.get('post_url'):
                try:
                    # Rate limiting
                    if i > 0:
                        time.sleep(2)

                    # Fetch and normalize comments
                    raw_comments = self._fetch_post_comments(post['post_url'], platform)

                    if raw_comments and adapter:
                        normalized_comments = [
                            adapter.normalize_comment(rc) for rc in raw_comments
                        ]
                        post['comments_list'] = normalized_comments
                        st.success(f"✅ Fetched {len(normalized_comments)} comments")
                    else:
                        post['comments_list'] = []

                except Exception as e:
                    st.warning(f"❌ Failed to fetch comments: {str(e)}")
                    post['comments_list'] = []

        progress_bar.empty()
        status_text.empty()

        return posts

    def _extract_post_urls(self, posts: List[Dict]) -> List[Dict[str, str]]:
        """Extract valid post URLs for comment scraping."""
        post_urls = []
        for post in posts:
            post_url = post.get('post_url') or post.get('url')
            if post_url and post_url.startswith('http'):
                post_urls.append({"url": post_url})
        return post_urls

    def _fetch_facebook_comments_batch(
        self,
        post_urls: List[Dict],
        max_comments: int
    ) -> List[Dict]:
        """
        Fetch Facebook comments in batch.
        
        Optimizations:
        - RANKED_UNFILTERED gets most relevant comments
        - maxDate/minDate for time filtering if needed
        - Enhanced data includes author info and reaction counts
        """
        comments_input = {
            "startUrls": post_urls,
            "resultsLimit": 3,  # Total limit across all posts
            "includeNestedComments": False,  # Set True to include up to 3 levels of replies
            "viewOption": "RANKED_UNFILTERED",  # Best balance of relevance and diversity
            # Additional optimizations
            "proxy": {
                "useApifyProxy": True,
                "apifyProxyGroups": ["RESIDENTIAL"]  # Better for avoiding blocks
            }
        }

        for i, actor_id in enumerate(FACEBOOK_COMMENTS_ACTOR_IDS):
            try:
                st.info(f"🔍 Attempt {i+1}: Using actor '{actor_id}'...")

                run = self.client.actor(actor_id).call(run_input=comments_input)

                comments_data = []
                for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                    comments_data.append(item)

                if comments_data:
                    st.success(f"✅ Fetched {len(comments_data)} comments using {actor_id}")
                    return comments_data
                else:
                    st.warning(f"⚠️ No comments found with {actor_id}")

            except Exception as e:
                st.warning(f"⚠️ Actor {actor_id} failed: {str(e)}")
                if i < len(FACEBOOK_COMMENTS_ACTOR_IDS) - 1:
                    st.info("🔄 Trying next actor...")
                continue

        st.error("❌ All comment scrapers failed")
        return []

    def _fetch_instagram_comments_batch(
        self,
        post_urls: List[Dict],
        max_comments: int
    ) -> List[Dict]:
        """Fetch Instagram comments in batch."""
        comments_input = {
            "directUrls": [u["url"] for u in post_urls],
            "resultsType": "comments",
            "resultsLimit": max_comments
        }

        for actor_id in INSTAGRAM_COMMENTS_ACTOR_IDS:
            try:
                st.info(f"🔍 Using actor '{actor_id}'...")

                run = self.client.actor(actor_id).call(run_input=comments_input)

                comments_data = []
                for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                    comments_data.append(item)

                if comments_data:
                    st.success(f"✅ Fetched {len(comments_data)} comments")
                    return comments_data

            except Exception as e:
                st.warning(f"⚠️ Actor {actor_id} failed: {str(e)}")
                continue

        return []

    def _fetch_youtube_comments_batch(
        self,
        post_urls: List[Dict],
        max_comments: int
    ) -> List[Dict]:
        """Fetch YouTube comments in batch."""
        video_urls = [u["url"] for u in post_urls]

        comments_input = {
            "startUrls": video_urls,
            "maxComments": max_comments,
            "maxReplies": 0
        }

        try:
            st.info(f"🔍 Using YouTube comments scraper...")

            run = self.client.actor(YOUTUBE_COMMENTS_ACTOR_ID).call(run_input=comments_input)

            comments_data = []
            for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                comments_data.append(item)

            if comments_data:
                st.success(f"✅ Fetched {len(comments_data)} comments")
                return comments_data

        except Exception as e:
            st.error(f"❌ YouTube comments fetch failed: {str(e)}")

        return []

    def _fetch_post_comments(self, post_url: str, platform: str) -> Optional[List[Dict]]:
        """Fetch comments for a single post."""
        # This would use the platform-specific comment fetching logic
        # Simplified for now - can be expanded based on platform
        return None

    def _assign_comments_to_posts(
        self,
        posts: List[Dict],
        comments_data: List[Dict],
        platform: str
    ) -> List[Dict]:
        """Assign comments to their respective posts."""
        adapter = self.adapters.get(platform)
        if not adapter:
            return posts

        # Create URL mapping
        post_url_map = {}
        for post in posts:
            post_url = post.get('post_url') or post.get('url')
            if post_url:
                post_url_map[post_url] = post
                post['comments_list'] = []

        # Assign comments
        assigned_comments = 0
        for comment in comments_data:
            comment_url = comment.get('url') or comment.get('postUrl') or comment.get('facebookUrl')

            if comment_url:
                for post_url, post in post_url_map.items():
                    if comment_url in post_url or post_url in comment_url:
                        normalized_comment = adapter.normalize_comment(comment)
                        post['comments_list'].append(normalized_comment)
                        assigned_comments += 1
                        break

        st.info(f"📊 Assigned {assigned_comments} comments to {len(posts)} posts")
        return posts

    def _should_fetch_comments(self, post: Dict) -> bool:
        """Check if comments should be fetched for a post."""
        comments_list = post.get('comments_list', [])
        return (
            not comments_list or
            (isinstance(comments_list, list) and len(comments_list) == 0) or
            isinstance(comments_list, int)
        )
