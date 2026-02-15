"""
MongoDB Database Configuration
==============================

Centralized database configuration and connection management.
"""

import os
from typing import Optional
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.database import Database
from pymongo.collection import Collection
from datetime import datetime


class DatabaseConfig:
    """
    MongoDB configuration and connection manager.
    """

    def __init__(self):
        """Initialize database configuration from environment or Streamlit secrets."""
        try:
            import streamlit as st
            self.connection_string = st.secrets.get("MONGODB_URI", os.getenv("MONGODB_URI", "mongodb://localhost:27017/"))
            self.database_name = st.secrets.get("MONGODB_DATABASE", os.getenv("MONGODB_DATABASE", "social_media_analytics"))
        except Exception:
            self.connection_string = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
            self.database_name = os.getenv("MONGODB_DATABASE", "social_media_analytics")

        self._client: Optional[MongoClient] = None
        self._db: Optional[Database] = None

    @property
    def client(self) -> MongoClient:
        """Get or create MongoDB client (singleton pattern)."""
        if self._client is None:
            self._client = MongoClient(self.connection_string)
        return self._client

    @property
    def db(self) -> Database:
        """Get or create database instance."""
        if self._db is None:
            self._db = self.client[self.database_name]
        return self._db

    def get_collection(self, collection_name: str) -> Collection:
        """
        Get a collection from the database.

        Args:
            collection_name: Name of the collection

        Returns:
            MongoDB collection instance
        """
        return self.db[collection_name]

    def close(self):
        """Close database connection."""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None

    def test_connection(self) -> bool:
        """
        Test database connection.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.client.admin.command('ping')
            return True
        except Exception as e:
            print(f"Database connection failed: {e}")
            return False

    def setup_indexes(self):
        """
        Create indexes for optimal query performance.
        """
        posts = self.get_collection('posts')
        posts.create_index([('post_id', ASCENDING), ('platform', ASCENDING)], unique=True)
        posts.create_index([('platform', ASCENDING)])
        posts.create_index([('published_at', DESCENDING)])
        posts.create_index([('scraping_job_id', ASCENDING)])

        comments = self.get_collection('comments')
        comments.create_index([('comment_id', ASCENDING), ('platform', ASCENDING)], unique=True)
        comments.create_index([('post_id', ASCENDING)])
        comments.create_index([('platform', ASCENDING)])
        comments.create_index([('created_time', DESCENDING)])

        jobs = self.get_collection('scraping_jobs')
        jobs.create_index([('created_at', DESCENDING)])
        jobs.create_index([('platform', ASCENDING)])
        jobs.create_index([('status', ASCENDING)])


_db_config: Optional[DatabaseConfig] = None


def get_database() -> DatabaseConfig:
    """
    Get global database configuration instance (singleton).

    Returns:
        DatabaseConfig instance
    """
    global _db_config
    if _db_config is None:
        _db_config = DatabaseConfig()
    return _db_config


def initialize_database() -> bool:
    """
    Initialize database with indexes and collections.
    Call this once during application startup.
    """
    db = get_database()
    if db.test_connection():
        db.setup_indexes()
        return True
    return False
