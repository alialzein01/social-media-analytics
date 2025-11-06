"""
MongoDB Repository for Posts
============================

Handles all database operations for social media posts.
"""

from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from pymongo.collection import Collection
from pymongo import DESCENDING


class PostRepository:
    """
    Repository pattern for Posts collection.
    """
    
    def __init__(self, collection: Collection):
        """
        Initialize repository with collection.
        
        Args:
            collection: MongoDB collection instance
        """
        self.collection = collection
    
    def insert_post(self, post_data: Dict[str, Any]) -> str:
        """
        Insert a single post into database.
        
        Args:
            post_data: Normalized post data
            
        Returns:
            Inserted document ID
        """
        # Add timestamp
        post_data['created_at'] = datetime.utcnow()
        post_data['updated_at'] = datetime.utcnow()
        
        result = self.collection.insert_one(post_data)
        return str(result.inserted_id)
    
    def insert_many_posts(self, posts: List[Dict[str, Any]]) -> List[str]:
        """
        Insert multiple posts in bulk.
        
        Args:
            posts: List of normalized post data
            
        Returns:
            List of inserted document IDs
        """
        if not posts:
            return []
        
        # Add timestamps
        now = datetime.utcnow()
        for post in posts:
            post['created_at'] = now
            post['updated_at'] = now
        
        result = self.collection.insert_many(posts, ordered=False)
        return [str(id) for id in result.inserted_ids]
    
    def upsert_post(self, post_data: Dict[str, Any]) -> str:
        """
        Insert or update post (based on post_id and platform).
        
        Args:
            post_data: Normalized post data
            
        Returns:
            Document ID
        """
        query = {
            'post_id': post_data['post_id'],
            'platform': post_data['platform']
        }
        
        # Add/update timestamps
        if 'created_at' not in post_data:
            post_data['created_at'] = datetime.utcnow()
        post_data['updated_at'] = datetime.utcnow()
        
        result = self.collection.update_one(
            query,
            {'$set': post_data},
            upsert=True
        )
        
        if result.upserted_id:
            return str(result.upserted_id)
        else:
            # Find the existing document
            doc = self.collection.find_one(query)
            return str(doc['_id']) if doc else ''
    
    def bulk_upsert_posts(self, posts: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Bulk upsert posts (insert new, update existing).
        
        Args:
            posts: List of normalized post data
            
        Returns:
            Dict with counts of inserted and updated documents
        """
        if not posts:
            return {'inserted': 0, 'updated': 0}
        
        from pymongo import UpdateOne
        
        now = datetime.utcnow()
        operations = []
        
        for post in posts:
            query = {
                'post_id': post['post_id'],
                'platform': post['platform']
            }
            
            # Set timestamps
            if 'created_at' not in post:
                post['created_at'] = now
            post['updated_at'] = now
            
            operations.append(
                UpdateOne(
                    query,
                    {'$set': post},
                    upsert=True
                )
            )
        
        result = self.collection.bulk_write(operations, ordered=False)
        
        return {
            'inserted': result.upserted_count,
            'updated': result.modified_count,
            'matched': result.matched_count
        }
    
    def get_post(self, post_id: str, platform: str) -> Optional[Dict[str, Any]]:
        """
        Get a single post by ID and platform.
        
        Args:
            post_id: Post identifier
            platform: Platform name (Facebook, Instagram, YouTube)
            
        Returns:
            Post document or None
        """
        return self.collection.find_one({
            'post_id': post_id,
            'platform': platform
        })
    
    def get_posts_by_platform(
        self,
        platform: str,
        limit: int = 100,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get posts for a specific platform.
        
        Args:
            platform: Platform name
            limit: Maximum number of posts to return
            skip: Number of posts to skip
            
        Returns:
            List of post documents
        """
        return list(
            self.collection.find({'platform': platform})
            .sort('published_at', DESCENDING)
            .skip(skip)
            .limit(limit)
        )
    
    def get_posts_by_date_range(
        self,
        platform: str,
        start_date: datetime,
        end_date: datetime,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Get posts within a date range.
        
        Args:
            platform: Platform name
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            limit: Maximum number of posts
            
        Returns:
            List of post documents
        """
        query = {
            'platform': platform,
            'published_at': {
                '$gte': start_date.isoformat(),
                '$lte': end_date.isoformat()
            }
        }
        
        return list(
            self.collection.find(query)
            .sort('published_at', DESCENDING)
            .limit(limit)
        )
    
    def get_posts_by_job(
        self,
        scraping_job_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all posts from a specific scraping job.
        
        Args:
            scraping_job_id: Scraping job identifier
            
        Returns:
            List of post documents
        """
        return list(
            self.collection.find({'scraping_job_id': scraping_job_id})
            .sort('published_at', DESCENDING)
        )
    
    def search_posts(
        self,
        search_text: str,
        platform: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Full-text search in posts.
        
        Args:
            search_text: Search query
            platform: Optional platform filter
            limit: Maximum results
            
        Returns:
            List of matching posts
        """
        query = {'$text': {'$search': search_text}}
        
        if platform:
            query['platform'] = platform
        
        return list(
            self.collection.find(query)
            .limit(limit)
        )
    
    def get_engagement_stats(
        self,
        platform: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get aggregated engagement statistics.
        
        Args:
            platform: Platform name
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            Dict with aggregated stats
        """
        match_query = {'platform': platform}
        
        if start_date and end_date:
            match_query['published_at'] = {
                '$gte': start_date.isoformat(),
                '$lte': end_date.isoformat()
            }
        
        pipeline = [
            {'$match': match_query},
            {
                '$group': {
                    '_id': '$platform',
                    'total_posts': {'$sum': 1},
                    'total_likes': {'$sum': '$likes'},
                    'total_comments': {'$sum': '$comments_count'},
                    'total_shares': {'$sum': '$shares_count'},
                    'avg_likes': {'$avg': '$likes'},
                    'avg_comments': {'$avg': '$comments_count'},
                    'avg_shares': {'$avg': '$shares_count'},
                    'max_likes': {'$max': '$likes'},
                    'max_comments': {'$max': '$comments_count'}
                }
            }
        ]
        
        result = list(self.collection.aggregate(pipeline))
        return result[0] if result else {}
    
    def delete_posts_by_job(self, scraping_job_id: str) -> int:
        """
        Delete all posts from a scraping job.
        
        Args:
            scraping_job_id: Scraping job identifier
            
        Returns:
            Number of deleted documents
        """
        result = self.collection.delete_many({'scraping_job_id': scraping_job_id})
        return result.deleted_count
    
    def count_posts(self, platform: Optional[str] = None) -> int:
        """
        Count total posts, optionally filtered by platform.
        
        Args:
            platform: Optional platform filter
            
        Returns:
            Count of posts
        """
        query = {'platform': platform} if platform else {}
        return self.collection.count_documents(query)
