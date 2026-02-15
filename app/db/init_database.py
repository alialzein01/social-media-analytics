"""
Database Initialization Script
==============================

Run this script once to set up MongoDB database and indexes.

Usage:
    python -m app.db.init_database
"""

import sys
from app.config.database import initialize_database, get_database


def main():
    """Initialize database with collections and indexes."""
    print("=" * 60)
    print("MongoDB Database Initialization")
    print("=" * 60)
    print()

    print("Testing database connection...")
    db = get_database()

    if not db.test_connection():
        print("ERROR: Could not connect to MongoDB!")
        print("\nPlease check:")
        print("  1. MongoDB is running")
        print("  2. Connection string in .env or .streamlit/secrets.toml is correct")
        print("  3. Network/firewall settings allow connection")
        sys.exit(1)

    print("Successfully connected to MongoDB")
    print(f"   Database: {db.database_name}")
    print()

    print("Creating collections and indexes...")
    if initialize_database():
        print()
        print("=" * 60)
        print("Database initialized successfully!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("Failed to initialize database!")
        sys.exit(1)


if __name__ == "__main__":
    main()
