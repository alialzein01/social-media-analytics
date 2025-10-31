"""
Data Fetching Service
====================

Handles all Apify API interactions for fetching posts and comments
from social media platforms.
"""

from typing import List, Dict, Optional, Any
from apify_client import ApifyClient
import streamlit as st
from datetime import datetime


class ApifyService:
    """
    Service for interacting with Apify actors.

    Handles API calls, error handling, and retry logic for fetching
    social media data.
    """

    def __init__(self, api_token: str):
        """
        Initialize Apify service.

        Args:
            api_token: Apify API token for authentication
        """
        self.client = ApifyClient(api_token)
        self.api_token = api_token

    def fetch_posts(
        self,
        actor_id: str,
        actor_input: Dict[str, Any],
        timeout: int = 300
    ) -> Optional[List[Dict]]:
        """
        Fetch posts from an Apify actor.

        Args:
            actor_id: Apify actor identifier (e.g., "apify/facebook-posts-scraper")
            actor_input: Input configuration for the actor
            timeout: Maximum time to wait for actor run (seconds)

        Returns:
            List of raw post data from actor, or None on failure
        """
        try:
            # Run the actor
            with st.spinner(f"🔍 Fetching data using {actor_id}..."):
                run = self.client.actor(actor_id).call(
                    run_input=actor_input,
                    timeout_secs=timeout
                )

            # Check if run was successful
            if run['status'] != 'SUCCEEDED':
                st.error(f"❌ Actor run failed with status: {run['status']}")
                return None

            # Get dataset items
            items = []
            for item in self.client.dataset(run['defaultDatasetId']).iterate_items():
                items.append(item)

            if not items:
                st.warning("⚠️ No data returned from actor")
                return None

            st.success(f"✅ Fetched {len(items)} items")
            return items

        except Exception as e:
            st.error(f"❌ Error fetching data: {str(e)}")
            return None

    def fetch_comments(
        self,
        post_url: str,
        platform: str,
        max_comments: int = 50
    ) -> Optional[List[Dict]]:
        """
        Fetch comments for a specific post.

        Args:
            post_url: URL of the post
            platform: Platform name ('Facebook', 'Instagram', 'YouTube')
            max_comments: Maximum number of comments to fetch

        Returns:
            List of raw comment data, or None on failure
        """
        # Platform-specific comment actors
        comment_actors = {
            'Facebook': [
                {
                    'actor_id': 'apify/facebook-comments-scraper',
                    'input': {
                        'startUrls': [{'url': post_url}],
                        'maxComments': max_comments,
                        'includeNestedComments': False
                    }
                }
            ],
            'Instagram': [
                {
                    'actor_id': 'apify/instagram-comment-scraper',
                    'input': {
                        'startUrls': [{'url': post_url}],
                        'maxComments': max_comments,
                        'includeNestedComments': False
                    }
                }
            ],
            'YouTube': [
                {
                    'actor_id': 'apify/youtube-scraper',
                    'input': {
                        'startUrls': [{'url': post_url}],
                        'maxComments': max_comments
                    }
                }
            ]
        }

        configs = comment_actors.get(platform, [])

        # Try each actor configuration
        for i, config in enumerate(configs):
            try:
                st.info(f"🔍 Attempt {i+1}: Using actor '{config['actor_id']}' for: {post_url}")

                run = self.client.actor(config['actor_id']).call(
                    run_input=config['input'],
                    timeout_secs=180
                )

                if run['status'] == 'SUCCEEDED':
                    items = []
                    for item in self.client.dataset(run['defaultDatasetId']).iterate_items():
                        items.append(item)

                    if items:
                        st.success(f"✅ Fetched {len(items)} comments")
                        return items
                    else:
                        st.warning(f"⚠️ Actor succeeded but returned no comments")
                else:
                    st.warning(f"⚠️ Actor run failed with status: {run['status']}")

            except Exception as e:
                st.warning(f"⚠️ Attempt {i+1} failed: {str(e)}")
                continue

        st.error(f"❌ All comment scrapers failed for post: {post_url}")
        return None

    def fetch_comments_batch(
        self,
        post_urls: List[str],
        platform: str,
        max_comments_per_post: int = 25,
        max_posts: int = None
    ) -> List[Dict]:
        """
        Fetch comments for multiple posts in batch.

        Args:
            post_urls: List of post URLs
            platform: Platform name
            max_comments_per_post: Max comments to fetch per post
            max_posts: Limit number of posts to process (None = all)

        Returns:
            List of all fetched comments with post_url reference
        """
        all_comments = []

        # Limit number of posts if specified
        urls_to_process = post_urls[:max_posts] if max_posts else post_urls

        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, post_url in enumerate(urls_to_process):
            # Update progress
            progress = (i + 1) / len(urls_to_process)
            progress_bar.progress(progress)
            status_text.text(f"Fetching comments {i+1}/{len(urls_to_process)}...")

            # Fetch comments for this post
            comments = self.fetch_comments(post_url, platform, max_comments_per_post)

            if comments:
                # Add post_url reference to each comment
                for comment in comments:
                    comment['post_url'] = post_url
                all_comments.extend(comments)

        progress_bar.empty()
        status_text.empty()

        return all_comments


class DataFetchingService:
    """
    High-level service for fetching social media data.

    Combines ApifyService with platform adapters to provide
    a clean interface for the main application.
    """

    def __init__(self, apify_token: str):
        """
        Initialize data fetching service.

        Args:
            apify_token: Apify API token
        """
        self.apify = ApifyService(apify_token)
        self.apify_token = apify_token

    def fetch_platform_posts(
        self,
        adapter,
        url: str,
        max_posts: int = 10,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> Optional[List[Dict]]:
        """
        Fetch and normalize posts for a platform.

        Args:
            adapter: Platform adapter instance (FacebookAdapter, etc.)
            url: Platform URL to scrape
            max_posts: Maximum number of posts
            from_date: Start date filter (optional)
            to_date: End date filter (optional)

        Returns:
            List of normalized posts, or None on failure
        """
        # Validate URL
        if not adapter.validate_url(url):
            st.error(f"❌ Invalid {adapter.platform_name} URL: {url}")
            return None

        # Build actor input
        actor_input = adapter.build_actor_input(
            url=url,
            max_posts=max_posts,
            from_date=from_date,
            to_date=to_date
        )

        # Fetch raw data
        raw_data = self.apify.fetch_posts(
            actor_id=adapter.get_actor_id(),
            actor_input=actor_input
        )

        if not raw_data:
            return None

        # Normalize data
        normalized = adapter.normalize_posts(raw_data)

        st.success(f"✅ Normalized {len(normalized)} {adapter.platform_name} posts")

        return normalized

    def fetch_post_comments(
        self,
        adapter,
        posts: List[Dict],
        max_comments_per_post: int = 25,
        max_posts_to_fetch: int = None
    ) -> List[Dict]:
        """
        Fetch comments for posts and attach them.

        Args:
            adapter: Platform adapter instance
            posts: List of normalized posts
            max_comments_per_post: Max comments per post
            max_posts_to_fetch: Limit posts to fetch comments for

        Returns:
            Updated posts list with comments attached
        """
        if not posts:
            return posts

        # Extract post URLs
        post_urls = [p.get('post_url') for p in posts if p.get('post_url')]

        if not post_urls:
            st.warning("⚠️ No post URLs found to fetch comments")
            return posts

        # Fetch comments in batch
        all_comments = self.apify.fetch_comments_batch(
            post_urls=post_urls,
            platform=adapter.platform_name,
            max_comments_per_post=max_comments_per_post,
            max_posts=max_posts_to_fetch
        )

        if not all_comments:
            st.info("ℹ️ No comments fetched")
            return posts

        # Normalize comments
        normalized_comments = adapter.normalize_comments(all_comments)

        # Group comments by post URL
        comments_by_url = {}
        for comment in normalized_comments:
            post_url = comment.get('post_url', '')
            if post_url not in comments_by_url:
                comments_by_url[post_url] = []
            comments_by_url[post_url].append(comment)

        # Attach comments to posts
        for post in posts:
            post_url = post.get('post_url', '')
            if post_url in comments_by_url:
                post['comments_list'] = comments_by_url[post_url]
                post['comments_count'] = len(comments_by_url[post_url])

        st.success(f"✅ Attached {len(normalized_comments)} comments to posts")

        return posts

    def fetch_complete_dataset(
        self,
        adapter,
        url: str,
        max_posts: int = 10,
        fetch_comments: bool = True,
        max_comments_per_post: int = 25,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> Optional[List[Dict]]:
        """
        Fetch complete dataset with posts, reactions, and comments.

        Args:
            adapter: Platform adapter instance
            url: Platform URL
            max_posts: Maximum posts to fetch
            fetch_comments: Whether to fetch comments
            max_comments_per_post: Max comments per post
            from_date: Start date filter
            to_date: End date filter

        Returns:
            Complete dataset with posts, reactions, and comments
        """
        # Step 1: Fetch posts
        posts = self.fetch_platform_posts(
            adapter=adapter,
            url=url,
            max_posts=max_posts,
            from_date=from_date,
            to_date=to_date
        )

        if not posts:
            return None

        # Step 2: Fetch detailed reactions for Facebook
        if adapter.platform_name == "Facebook":
            posts = self.fetch_facebook_reactions(posts)

        # Step 3: Fetch comments if requested
        if fetch_comments:
            posts = self.fetch_post_comments(
                adapter=adapter,
                posts=posts,
                max_comments_per_post=max_comments_per_post
            )

        return posts
    
    def fetch_facebook_reactions(self, posts: List[Dict]) -> List[Dict]:
        """
        Fetch detailed reaction breakdown for Facebook posts.
        
        Uses scraper_one~facebook-reactions-scraper to get individual reactions,
        then aggregates them by post and reaction type.
        
        NOTE: Actor only accepts max 5 post URLs per request, so we batch them.
        
        Args:
            posts: List of Facebook posts with URLs
            
        Returns:
            Posts with detailed reaction counts added
        """
        if not posts:
            return posts
        
        # Extract post URLs
        post_urls = [p.get('post_url') for p in posts if p.get('post_url')]
        
        if not post_urls:
            st.warning("⚠️ No post URLs found for reaction fetching")
            return posts
        
        st.info(f"🎭 Fetching detailed reactions for {len(post_urls)} posts (batched in groups of 5)...")
        
        # Batch post URLs into chunks of 5 (actor limit)
        batch_size = 5
        all_reactions = []
        
        # Import actor ID
        from app.services.data_fetcher import FACEBOOK_REACTIONS_ACTOR_ID
        
        # Process in batches
        total_batches = (len(post_urls) + batch_size - 1) // batch_size
        for i in range(0, len(post_urls), batch_size):
            batch_urls = post_urls[i:i+batch_size]
            batch_num = i // batch_size + 1
            
            st.info(f"🔄 Processing reactions batch {batch_num}/{total_batches} ({len(batch_urls)} posts)...")
            
            try:
                # Build reactions actor input for this batch
                reactions_input = {
                    "postUrls": batch_urls,
                    "resultsLimit": 500  # Optimized: 500 reactions per batch
                }
                
                # Call reactions scraper actor
                run = self.apify.client.actor(FACEBOOK_REACTIONS_ACTOR_ID).call(
                    run_input=reactions_input
                )
                
                # Fetch reaction data for this batch
                batch_reactions = []
                for item in self.apify.client.dataset(run["defaultDatasetId"]).iterate_items():
                    batch_reactions.append(item)
                
                all_reactions.extend(batch_reactions)
                st.success(f"✅ Batch {batch_num}: Fetched {len(batch_reactions)} reactions")
                
            except Exception as e:
                st.warning(f"⚠️ Batch {batch_num} failed: {str(e)}")
                st.info("Continuing with next batch...")
                continue
        
        if not all_reactions:
            st.info("ℹ️ No reactions data returned from any batch")
            return posts
        
        st.success(f"✅ Total: Fetched {len(all_reactions)} individual reactions from {len(post_urls)} posts")
        
        # Aggregate reactions by post URL and type
        reactions_by_post = self._aggregate_reactions(all_reactions)
        
        # Merge reactions back into posts
        for post in posts:
            post_url = post.get('post_url')
            if post_url and post_url in reactions_by_post:
                post['reactions'] = reactions_by_post[post_url]
                # Update total likes count
                post['likes'] = sum(reactions_by_post[post_url].values())
        
        st.success(f"✅ Added detailed reaction breakdown to posts")
        
        return posts
    
    def _aggregate_reactions(self, reactions_data: List[Dict]) -> Dict[str, Dict[str, int]]:
        """
        Aggregate individual reactions into counts by post and type.
        
        Args:
            reactions_data: List of individual reaction objects from reactions scraper
            
        Returns:
            Dict mapping post URL to reaction type counts
            {
                "post_url": {
                    "like": 100,
                    "love": 50,
                    "haha": 30,
                    "wow": 20,
                    "sad": 10,
                    "angry": 5
                }
            }
        """
        from collections import defaultdict
        
        aggregated = defaultdict(lambda: defaultdict(int))
        
        for reaction in reactions_data:
            post_url = reaction.get('postUrl', '')
            reaction_type = reaction.get('reactionType', '').lower()
            
            if post_url and reaction_type:
                aggregated[post_url][reaction_type] += 1
        
        # Convert defaultdict to regular dict
        return {url: dict(counts) for url, counts in aggregated.items()}
