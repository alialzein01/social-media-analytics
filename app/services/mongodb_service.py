"""
MongoDB Service Layer
=====================

High-level service that integrates repositories with adapters
for seamless database operations.
"""

from typing import List, Dict, Optional, Any
from datetime import datetime

from app.config.database import get_database
from app.db import PostRepository, CommentRepository, ScrapingJobRepository


class MongoDBService:
    """
    High-level service for MongoDB operations.
    Integrates repositories and provides business logic.
    """
    
    def __init__(self):
        """Initialize service with database connection."""
        db = get_database()
        
        # Initialize repositories
        self.post_repo = PostRepository(db.get_collection('posts'))
        self.comment_repo = CommentRepository(db.get_collection('comments'))
        self.job_repo = ScrapingJobRepository(db.get_collection('scraping_jobs'))
    
    def save_scraping_results(
        self,
        platform: str,
        url: str,
        normalized_posts: List[Dict[str, Any]],
        max_posts: int,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Save scraping results to database.
        
        Args:
            platform: Platform name (Facebook, Instagram, YouTube)
            url: Scraped URL
            normalized_posts: List of normalized posts from adapter
            max_posts: Maximum posts requested
            filters: Optional filters used
            
        Returns:
            Dict with job_id and save statistics
        """
        # Create scraping job
        job_id = self.job_repo.create_job(
            platform=platform,
            url=url,
            max_posts=max_posts,
            filters=filters
        )
        
        # Prepare posts with job_id and platform
        posts_to_save = []
        comments_to_save = []
        
        for post in normalized_posts:
            # Add metadata
            post['platform'] = platform
            post['scraping_job_id'] = job_id
            
            # Extract comments from post
            comments_list = post.pop('comments_list', [])
            
            posts_to_save.append(post)
            
            # Process comments
            for comment in comments_list:
                comment['platform'] = platform
                comment['post_id'] = post['post_id']
                comment['scraping_job_id'] = job_id
                comments_to_save.append(comment)
        
        # Save posts
        post_stats = self.post_repo.bulk_upsert_posts(posts_to_save)
        
        # Save comments
        comment_stats = self.comment_repo.bulk_upsert_comments(comments_to_save)
        
        # Update job status
        self.job_repo.complete_job(
            job_id=job_id,
            posts_count=len(posts_to_save),
            comments_count=len(comments_to_save),
            success=True
        )
        
        return {
            'job_id': job_id,
            'posts': post_stats,
            'comments': comment_stats,
            'total_posts': len(posts_to_save),
            'total_comments': len(comments_to_save)
        }
    
    def get_posts_for_analysis(
        self,
        platform: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Get posts for analysis and visualization.
        
        Args:
            platform: Platform name
            start_date: Optional start date filter
            end_date: Optional end date filter
            limit: Maximum posts to return
            
        Returns:
            List of posts
        """
        if start_date and end_date:
            return self.post_repo.get_posts_by_date_range(
                platform=platform,
                start_date=start_date,
                end_date=end_date,
                limit=limit
            )
        else:
            return self.post_repo.get_posts_by_platform(
                platform=platform,
                limit=limit
            )
    
    def get_comments_for_analysis(
        self,
        platform: str,
        post_id: Optional[str] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Get comments for analysis.
        
        Args:
            platform: Platform name
            post_id: Optional post filter
            limit: Maximum comments
            
        Returns:
            List of comments
        """
        if post_id:
            return self.comment_repo.get_comments_by_post(
                post_id=post_id,
                platform=platform,
                limit=limit
            )
        else:
            return self.comment_repo.get_comments_by_platform(
                platform=platform,
                limit=limit
            )
    
    def get_engagement_statistics(
        self,
        platform: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive engagement statistics.
        
        Args:
            platform: Platform name
            start_date: Optional start date
            end_date: Optional end date
            
        Returns:
            Dict with engagement stats
        """
        return self.post_repo.get_engagement_stats(
            platform=platform,
            start_date=start_date,
            end_date=end_date
        )
    
    def get_recent_jobs(
        self,
        platform: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get recent scraping jobs.
        
        Args:
            platform: Optional platform filter
            limit: Maximum jobs
            
        Returns:
            List of jobs
        """
        return self.job_repo.get_recent_jobs(platform=platform, limit=limit)
    
    def search_content(
        self,
        query: str,
        platform: str,
        search_comments: bool = False,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Full-text search across posts or comments.
        
        Args:
            query: Search query
            platform: Platform name
            search_comments: Search comments instead of posts
            limit: Maximum results
            
        Returns:
            List of matching documents
        """
        if search_comments:
            return self.comment_repo.search_comments(
                search_text=query,
                platform=platform,
                limit=limit
            )
        else:
            return self.post_repo.search_posts(
                search_text=query,
                platform=platform,
                limit=limit
            )
    
    def get_dashboard_overview(self) -> Dict[str, Any]:
        """
        Get overview statistics for dashboard.
        
        Returns:
            Dict with platform-wise statistics
        """
        platforms = ['Facebook', 'Instagram', 'YouTube']
        overview = {}
        
        for platform in platforms:
            overview[platform] = {
                'total_posts': self.post_repo.count_posts(platform=platform),
                'total_comments': self.comment_repo.count_comments(platform=platform),
                'engagement_stats': self.post_repo.get_engagement_stats(platform=platform)
            }
        
        # Add job statistics
        overview['jobs'] = self.job_repo.get_job_statistics()
        
        return overview
