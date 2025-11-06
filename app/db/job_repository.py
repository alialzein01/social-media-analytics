"""
MongoDB Repository for Scraping Jobs
====================================

Handles tracking and management of scraping job sessions.
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
from pymongo.collection import Collection
from pymongo import DESCENDING


class ScrapingJobRepository:
    """
    Repository for tracking scraping job metadata.
    """
    
    def __init__(self, collection: Collection):
        """
        Initialize repository with collection.
        
        Args:
            collection: MongoDB collection instance
        """
        self.collection = collection
    
    def create_job(
        self,
        platform: str,
        url: str,
        max_posts: int,
        filters: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new scraping job.
        
        Args:
            platform: Platform name (Facebook, Instagram, YouTube)
            url: Target URL
            max_posts: Maximum posts to scrape
            filters: Optional filters (date range, etc.)
            
        Returns:
            Job ID
        """
        job = {
            'platform': platform,
            'url': url,
            'max_posts': max_posts,
            'filters': filters or {},
            'status': 'started',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'posts_scraped': 0,
            'comments_scraped': 0,
            'errors': []
        }
        
        result = self.collection.insert_one(job)
        return str(result.inserted_id)
    
    def update_job_status(
        self,
        job_id: str,
        status: str,
        posts_count: int = 0,
        comments_count: int = 0,
        error: Optional[str] = None
    ):
        """
        Update job status and metrics.
        
        Args:
            job_id: Job identifier
            status: Job status (started, running, completed, failed)
            posts_count: Number of posts scraped
            comments_count: Number of comments scraped
            error: Optional error message
        """
        from bson import ObjectId
        
        update = {
            '$set': {
                'status': status,
                'updated_at': datetime.utcnow(),
                'posts_scraped': posts_count,
                'comments_scraped': comments_count
            }
        }
        
        if error:
            update['$push'] = {'errors': {'message': error, 'timestamp': datetime.utcnow()}}
        
        self.collection.update_one(
            {'_id': ObjectId(job_id)},
            update
        )
    
    def complete_job(
        self,
        job_id: str,
        posts_count: int,
        comments_count: int,
        success: bool = True
    ):
        """
        Mark job as completed.
        
        Args:
            job_id: Job identifier
            posts_count: Total posts scraped
            comments_count: Total comments scraped
            success: Whether job completed successfully
        """
        from bson import ObjectId
        
        self.collection.update_one(
            {'_id': ObjectId(job_id)},
            {
                '$set': {
                    'status': 'completed' if success else 'failed',
                    'completed_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow(),
                    'posts_scraped': posts_count,
                    'comments_scraped': comments_count
                }
            }
        )
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get job by ID.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Job document or None
        """
        from bson import ObjectId
        return self.collection.find_one({'_id': ObjectId(job_id)})
    
    def get_recent_jobs(
        self,
        platform: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get recent scraping jobs.
        
        Args:
            platform: Optional platform filter
            limit: Maximum number of jobs
            
        Returns:
            List of job documents
        """
        query = {'platform': platform} if platform else {}
        
        return list(
            self.collection.find(query)
            .sort('created_at', DESCENDING)
            .limit(limit)
        )
    
    def get_job_statistics(self) -> Dict[str, Any]:
        """
        Get overall job statistics.
        
        Returns:
            Dict with aggregated stats
        """
        pipeline = [
            {
                '$group': {
                    '_id': '$platform',
                    'total_jobs': {'$sum': 1},
                    'completed_jobs': {
                        '$sum': {'$cond': [{'$eq': ['$status', 'completed']}, 1, 0]}
                    },
                    'failed_jobs': {
                        '$sum': {'$cond': [{'$eq': ['$status', 'failed']}, 1, 0]}
                    },
                    'total_posts': {'$sum': '$posts_scraped'},
                    'total_comments': {'$sum': '$comments_scraped'}
                }
            }
        ]
        
        results = list(self.collection.aggregate(pipeline))
        return {item['_id']: item for item in results}
