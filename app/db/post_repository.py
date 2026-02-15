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
        """
        def _parse_published_at(val):
            if val is None:
                return None
            if isinstance(val, datetime):
                return val
            if isinstance(val, str):
                s = val.strip()
                try:
                    s2 = s[:-1] if s.endswith('Z') else s
                    return datetime.fromisoformat(s2)
                except Exception:
                    for fmt in ('%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%dT%H:%M:%S'):
                        try:
                            return datetime.strptime(s2, fmt)
                        except Exception:
                            continue
                    return None
            return None

        query = {'platform': {'$regex': f'^{platform}$', '$options': 'i'}}
        cursor = self.collection.find(query).sort('published_at', DESCENDING).limit(limit * 2)

        results = []
        for p in cursor:
            pa_raw = p.get('published_at')
            pa = _parse_published_at(pa_raw)
            if pa is None:
                continue
            if start_date <= pa <= end_date:
                results.append(p)

        results.sort(key=lambda x: _parse_published_at(x.get('published_at')) or datetime.min, reverse=True)
        return results[:limit]

    def get_posts_by_job(self, scraping_job_id: str) -> List[Dict[str, Any]]:
        """
        Get all posts from a specific scraping job.
        """
        return list(
            self.collection.find({'scraping_job_id': scraping_job_id})
            .sort('published_at', DESCENDING)
        )

    def get_engagement_stats(
        self,
        platform: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get aggregated engagement statistics.
        """
        match_query = {'platform': {'$regex': f'^{platform}$', '$options': 'i'}}

        if start_date and end_date:
            match_query['published_at'] = {
                '$gte': start_date,
                '$lte': end_date
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

    def count_posts(self, platform: Optional[str] = None) -> int:
        """
        Count total posts, optionally filtered by platform.
        """
        query = {'platform': platform} if platform else {}
        return self.collection.count_documents(query)
