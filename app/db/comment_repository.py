"""
MongoDB Repository for Comments
===============================

Handles all database operations for social media comments.
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
from pymongo.collection import Collection
from pymongo import DESCENDING


class CommentRepository:
    """
    Repository pattern for Comments collection.
    """
    
    def __init__(self, collection: Collection):
        """
        Initialize repository with collection.
        
        Args:
            collection: MongoDB collection instance
        """
        self.collection = collection
    
    def insert_comment(self, comment_data: Dict[str, Any]) -> str:
        """
        Insert a single comment into database.
        
        Args:
            comment_data: Normalized comment data
            
        Returns:
            Inserted document ID
        """
        comment_data['created_at'] = datetime.utcnow()
        comment_data['updated_at'] = datetime.utcnow()
        
        result = self.collection.insert_one(comment_data)
        return str(result.inserted_id)
    
    def bulk_upsert_comments(self, comments: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Bulk upsert comments (insert new, update existing).
        
        Args:
            comments: List of normalized comment data
            
        Returns:
            Dict with counts of inserted and updated documents
        """
        if not comments:
            return {'inserted': 0, 'updated': 0}
        
        from pymongo import UpdateOne
        
        now = datetime.utcnow()
        operations = []
        
        for comment in comments:
            query = {
                'comment_id': comment['comment_id'],
                'platform': comment['platform']
            }
            
            if 'created_at' not in comment:
                comment['created_at'] = now
            comment['updated_at'] = now
            
            operations.append(
                UpdateOne(
                    query,
                    {'$set': comment},
                    upsert=True
                )
            )
        
        result = self.collection.bulk_write(operations, ordered=False)
        
        return {
            'inserted': result.upserted_count,
            'updated': result.modified_count,
            'matched': result.matched_count
        }
    
    def get_comments_by_post(
        self,
        post_id: str,
        platform: str,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Get all comments for a specific post.
        
        Args:
            post_id: Post identifier
            platform: Platform name
            limit: Maximum number of comments
            
        Returns:
            List of comment documents
        """
        return list(
            self.collection.find({
                'post_id': post_id,
                'platform': platform
            })
            .sort('created_time', DESCENDING)
            .limit(limit)
        )
    
    def get_comments_by_platform(
        self,
        platform: str,
        limit: int = 1000,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get comments for a specific platform.
        
        Args:
            platform: Platform name
            limit: Maximum number of comments
            skip: Number to skip
            
        Returns:
            List of comment documents
        """
        return list(
            self.collection.find({'platform': platform})
            .sort('created_time', DESCENDING)
            .skip(skip)
            .limit(limit)
        )
    
    def search_comments(
        self,
        search_text: str,
        platform: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Full-text search in comments.
        
        Args:
            search_text: Search query
            platform: Optional platform filter
            limit: Maximum results
            
        Returns:
            List of matching comments
        """
        query = {'$text': {'$search': search_text}}
        
        if platform:
            query['platform'] = platform
        
        return list(
            self.collection.find(query)
            .limit(limit)
        )
    
    def get_top_commenters(
        self,
        platform: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get most active commenters by platform.
        
        Args:
            platform: Platform name
            limit: Number of top commenters
            
        Returns:
            List of commenters with counts
        """
        pipeline = [
            {'$match': {'platform': platform}},
            {
                '$group': {
                    '_id': '$author_name',
                    'comment_count': {'$sum': 1},
                    'total_likes': {'$sum': '$likes_count'}
                }
            },
            {'$sort': {'comment_count': -1}},
            {'$limit': limit}
        ]
        
        return list(self.collection.aggregate(pipeline))
    
    def count_comments(
        self,
        platform: Optional[str] = None,
        post_id: Optional[str] = None
    ) -> int:
        """
        Count comments with optional filters.
        
        Args:
            platform: Optional platform filter
            post_id: Optional post_id filter
            
        Returns:
            Count of comments
        """
        query = {}
        if platform:
            query['platform'] = platform
        if post_id:
            query['post_id'] = post_id
        
        return self.collection.count_documents(query)
