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
        """
        comment_data['created_at'] = datetime.utcnow()
        comment_data['updated_at'] = datetime.utcnow()

        result = self.collection.insert_one(comment_data)
        return str(result.inserted_id)

    def bulk_upsert_comments(self, comments: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Bulk upsert comments (insert new, update existing).
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
        """
        query = {
            'platform': {'$regex': f'^{platform}$', '$options': 'i'},
            '$or': [
                {'post_id': post_id},
                {'postId': post_id},
                {'post_url': {'$regex': post_id}},
                {'url': {'$regex': post_id}}
            ]
        }

        return list(
            self.collection.find(query)
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
        """
        query = {'platform': {'$regex': f'^{platform}$', '$options': 'i'}}
        return list(
            self.collection.find(query)
            .sort('created_time', DESCENDING)
            .skip(skip)
            .limit(limit)
        )

    def count_comments(
        self,
        platform: Optional[str] = None,
        post_id: Optional[str] = None
    ) -> int:
        """
        Count comments with optional filters.
        """
        query = {}
        if platform:
            query['platform'] = {'$regex': f'^{platform}$', '$options': 'i'}
        if post_id:
            query['$or'] = [
                {'post_id': post_id},
                {'postId': post_id},
                {'post_url': {'$regex': post_id}},
                {'url': {'$regex': post_id}}
            ]

        return self.collection.count_documents(query)
