"""
Database Initialization Script
==============================

Run this script once to set up MongoDB database and indexes.

Usage:
    python init_database.py
"""

import sys
from app.config.database import initialize_database, get_database


def main():
    """Initialize database with collections and indexes."""
    print("=" * 60)
    print("MongoDB Database Initialization")
    print("=" * 60)
    print()
    
    # Test connection first
    print("Testing database connection...")
    db = get_database()
    
    if not db.test_connection():
        print("❌ ERROR: Could not connect to MongoDB!")
        print("\nPlease check:")
        print("  1. MongoDB is running")
        print("  2. Connection string in .env or secrets.toml is correct")
        print("  3. Network/firewall settings allow connection")
        sys.exit(1)
    
    print("✅ Successfully connected to MongoDB")
    print(f"   Database: {db.database_name}")
    print()
    
    # Initialize database
    print("Creating collections and indexes...")
    if initialize_database():
        print()
        print("=" * 60)
        print("✅ Database initialized successfully!")
        print("=" * 60)
        print()
        print("Collections created:")
        print("  - posts (with indexes on post_id, platform, published_at)")
        print("  - comments (with indexes on comment_id, platform, post_id)")
        print("  - scraping_jobs (with indexes on created_at, platform)")
        print("  - analytics_cache (with indexes on cache_key)")
        print()
        print("You can now run your Streamlit application:")
        print("  streamlit run social_media_app.py")
        print()
    else:
        print("❌ Failed to initialize database!")
        sys.exit(1)


if __name__ == "__main__":
    main()
