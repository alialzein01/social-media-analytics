"""
Comment Fetching Service
========================

Centralized service for fetching comments from all social media platforms.
Handles Instagram, Facebook, and YouTube comment extraction using Apify actors.
"""

import time
import json
import hashlib
import os
from typing import List, Dict, Optional
from apify_client import ApifyClient
import streamlit as st

from app.config.settings import (
    INSTAGRAM_COMMENTS_ACTOR_IDS,
    FACEBOOK_COMMENTS_ACTOR_IDS,
    YOUTUBE_COMMENTS_ACTOR_ID
)


class CommentFetchingService:
    """Service for fetching comments from social media platforms."""
    
    def __init__(self, apify_token: str):
        """
        Initialize the comment fetching service.
        
        Args:
            apify_token: Apify API token for authentication
        """
        self.client = ApifyClient(apify_token)
        self.apify_token = apify_token
    
    def scrape_instagram_comments_batch(
        self,
        post_urls: List[str],
        max_comments_per_post: int = 25
    ) -> List[Dict]:
        """
        Scrape Instagram comments from multiple post URLs using batch processing.
        
        Args:
            post_urls: List of Instagram post URLs
            max_comments_per_post: Maximum comments to fetch per post
            
        Returns:
            List of comment dictionaries
        """
        if not post_urls:
            return []
        
        all_comments = []
        
        st.info(f"🔄 Starting Instagram comments extraction for {len(post_urls)} posts...")
        
        # Process posts in batches to avoid overwhelming the API
        batch_size = 5  # Process 5 posts at a time
        for i in range(0, len(post_urls), batch_size):
            batch_urls = post_urls[i:i + batch_size]
            st.info(
                f"📊 Processing batch {i//batch_size + 1}/"
                f"{(len(post_urls) + batch_size - 1)//batch_size} "
                f"({len(batch_urls)} posts)"
            )
            
            for post_url in batch_urls:
                try:
                    # Collect unique comments from multiple attempts
                    post_comments = []
                    collected_comment_ids = set()
                    
                    # Try the first working actor only (don't iterate through all)
                    for actor_id in INSTAGRAM_COMMENTS_ACTOR_IDS:
                        try:
                            st.info(f"🔍 Trying Instagram comments actor: {actor_id}")

                            # Configure input for Instagram comments scraper
                            run_input = {
                                "directUrls": [post_url],
                                "resultsLimit": 50,
                                "maxComments": 50,
                                "includeReplies": True,
                                "sortBy": "newest",
                                "maxResults": 50,
                                "limit": 50
                            }

                            # Run the actor
                            run = self.client.actor(actor_id).call(run_input=run_input)

                            # Log run metadata for debugging
                            st.info(
                                f"   - Run id: {run.get('id', 'N/A')} | "
                                f"status: {run.get('status', 'N/A')}"
                            )

                            if run and run.get("status") == "SUCCEEDED":
                                # Get the results
                                dataset_id = run.get("defaultDatasetId")
                                st.info(f"   - Dataset id: {dataset_id}")
                                dataset = self.client.dataset(dataset_id)
                                comments_data = list(dataset.iterate_items())

                                # Save a copy of the raw dataset to data/raw for inspection
                                try:
                                    raw_dir = os.path.join("data", "raw")
                                    os.makedirs(raw_dir, exist_ok=True)
                                    fname = hashlib.sha1(post_url.encode("utf-8")).hexdigest()[:10]
                                    sample_path = os.path.join(
                                        raw_dir,
                                        f"instagram_comments_{fname}_{dataset_id}.json"
                                    )
                                    with open(sample_path, "w", encoding="utf-8") as wf:
                                        json.dump(comments_data, wf, ensure_ascii=False, indent=2)
                                    st.info(f"   - Saved raw dataset sample to: {sample_path}")
                                except Exception as e:
                                    st.warning(f"   - Could not save raw dataset: {e}")

                                if comments_data:
                                    # Deduplicate comments based on comment ID or text
                                    for comment in comments_data:
                                        comment_id = (
                                            comment.get('id') or
                                            comment.get('commentId') or
                                            comment.get('text', '')[:50]
                                        )
                                        if comment_id not in collected_comment_ids:
                                            collected_comment_ids.add(comment_id)
                                            post_comments.append(comment)
                                    
                                    st.success(
                                        f"✅ Extracted {len(post_comments)} unique comments from {post_url}"
                                    )
                                    st.info(f"📊 Comment extraction details:")
                                    st.info(f"   - Requested: 50 comments (max)")
                                    st.info(f"   - Retrieved: {len(post_comments)} unique comments")
                                    st.info(f"   - Actor: {actor_id}")
                                    st.info(f"   - Post URL: {post_url}")
                                    
                                    if len(post_comments) < 20:
                                        st.warning(
                                            f"⚠️ **Limited Comments Retrieved ({len(post_comments)} found)**"
                                        )
                                        st.info("**Why Instagram shows fewer comments:**")
                                        st.info("• Instagram API restricts comment access without login")
                                        st.info("• Only 'top' or 'recent' comments may be publicly visible")
                                        st.info("• Some comments are hidden by Instagram's spam filters")
                                        st.info("• Post owner may have restricted comment visibility")
                                        st.info("• Apify actors cannot access login-restricted content")
                                    
                                    # Add collected comments to all_comments
                                    all_comments.extend(post_comments)
                                    break  # Success with this actor, move to next post
                                else:
                                    st.warning(
                                        f"⚠️ No comments found for {post_url} using actor {actor_id}"
                                    )
                                    continue  # Try next actor
                            else:
                                st.warning(
                                    f"⚠️ Actor {actor_id} failed for {post_url} "
                                    f"(status: {run.get('status') if run else 'no run'})"
                                )
                                continue  # Try next actor

                        except Exception as e:
                            st.warning(f"⚠️ Actor {actor_id} error for {post_url}: {str(e)}")
                            continue  # Try next actor
                    
                    # Small delay between posts to be respectful
                    time.sleep(2)
                    
                except Exception as e:
                    st.error(f"❌ Error processing {post_url}: {str(e)}")
                    continue
        
        st.success(
            f"🎉 Instagram comments extraction complete! Total comments: {len(all_comments)}"
        )
        return all_comments
    
    def fetch_facebook_comments_batch(
        self,
        posts: List[Dict],
        max_comments_per_post: int = 25
    ) -> List[Dict]:
        """
        Fetch detailed comments for all Facebook posts using batch processing.
        
        Args:
            posts: List of post dictionaries with post_url
            max_comments_per_post: Maximum comments to fetch per post
            
        Returns:
            Updated posts list with comments assigned
        """
        if not posts:
            return posts
        
        st.info(f"🔄 Starting batch comment extraction for {len(posts)} posts...")
        
        # Extract all post URLs
        post_urls = []
        for post in posts:
            post_url = post.get('post_url')
            if post_url and post_url.startswith('http'):
                post_urls.append({"url": post_url})
        
        if not post_urls:
            st.warning("⚠️ No valid post URLs found for comment extraction")
            return posts
        
        st.info(f"📋 Found {len(post_urls)} valid post URLs for comment extraction")
        
        # Prepare input for the comments scraper actor
        comments_input = {
            "startUrls": post_urls,
            "resultsLimit": max_comments_per_post,
            "includeNestedComments": False,
            "viewOption": "RANKED_UNFILTERED"
        }
        
        # Try different actors for comment extraction
        for i, actor_id in enumerate(FACEBOOK_COMMENTS_ACTOR_IDS):
            try:
                st.info(
                    f"🔍 Attempt {i+1}: Using actor '{actor_id}' "
                    f"for batch comment extraction..."
                )
                
                # Run the actor
                run = self.client.actor(actor_id).call(run_input=comments_input)
                
                # Fetch results
                comments_data = []
                for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                    comments_data.append(item)
                
                if comments_data:
                    st.success(
                        f"✅ Successfully extracted {len(comments_data)} comments "
                        f"using actor '{actor_id}'"
                    )
                    # Assign comments to posts
                    from app.adapters.facebook import FacebookAdapter
                    adapter = FacebookAdapter(self.apify_token)
                    return adapter.assign_comments_to_posts(posts, comments_data)
                else:
                    st.warning(f"⚠️ No comments found using actor {actor_id}")
                    
            except Exception as e:
                st.warning(f"⚠️ Actor {actor_id} failed: {str(e)}")
                if i < len(FACEBOOK_COMMENTS_ACTOR_IDS) - 1:
                    st.info(f"Trying next actor...")
                continue
        
        st.error("❌ All comment scrapers failed for batch processing")
        return posts
    
    def fetch_youtube_comments(
        self,
        video_urls: List[str],
        max_comments_per_video: int = 10
    ) -> List[Dict]:
        """
        Fetch comments from YouTube videos.
        
        Args:
            video_urls: List of YouTube video URLs
            max_comments_per_video: Maximum comments to fetch per video
            
        Returns:
            List of comment dictionaries
        """
        try:
            all_comments = []
            
            for video_url in video_urls:
                try:
                    st.info(f"🔍 Fetching comments for video: {video_url}")
                    
                    # Configure input for YouTube comments scraper
                    run_input = {
                        "startUrls": [{"url": video_url}],
                        "maxComments": max_comments_per_video,
                        "maxReplies": 0  # Don't fetch replies to keep it simple
                    }
                    
                    # Run the actor
                    run = self.client.actor(YOUTUBE_COMMENTS_ACTOR_ID).call(
                        run_input=run_input
                    )
                    
                    # Fetch results
                    for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                        all_comments.append(item)
                    
                    st.success(f"✅ Fetched comments for {video_url}")
                    
                except Exception as e:
                    st.warning(f"⚠️ Failed to fetch comments for {video_url}: {str(e)}")
                    continue
            
            return all_comments
            
        except Exception as e:
            st.error(f"Error fetching YouTube comments: {str(e)}")
            return []
