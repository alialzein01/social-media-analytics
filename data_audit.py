#!/usr/bin/env python3
"""
Data Audit Script
=================

This script audits data from all platforms to verify completeness
and identify any issues with data extraction and normalization.

Usage:
    python data_audit.py
"""

import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.data.validators import (
    calculate_data_completeness,
    print_completeness_report,
    validate_all_platforms,
)


def audit_saved_data():
    """Audit data from saved files in data/processed/"""

    print("\n" + "=" * 70)
    print("SOCIAL MEDIA ANALYTICS - DATA AUDIT")
    print("=" * 70)
    print(f"Audit Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70 + "\n")

    import glob
    import json
    import pandas as pd

    data_dir = os.path.join(os.path.dirname(__file__), "data", "processed")

    if not os.path.exists(data_dir):
        print(f"❌ Data directory not found: {data_dir}")
        print("💡 Run the app first to generate some data, then run this audit.\n")
        return

    # Find CSV files for each platform (exclude comments files)
    platforms = {
        "Facebook": [
            f for f in glob.glob(os.path.join(data_dir, "facebook_*.csv")) if "comments" not in f
        ],
        "Instagram": [
            f for f in glob.glob(os.path.join(data_dir, "instagram_*.csv")) if "comments" not in f
        ],
        "YouTube": [
            f for f in glob.glob(os.path.join(data_dir, "youtube_*.csv")) if "comments" not in f
        ],
    }

    all_results = {}

    for platform, files in platforms.items():
        if not files:
            print(f"⚠️  No {platform} data files found")
            continue

        print(f"\n📊 Auditing {platform} Data...")
        print(f"Found {len(files)} file(s)")

        # Use most recent file
        latest_file = max(files, key=os.path.getmtime)
        print(f"Using: {os.path.basename(latest_file)}\n")

        try:
            # Load CSV data
            df = pd.read_csv(latest_file)

            # Convert to list of dicts
            posts = df.to_dict("records")

            # Parse JSON fields
            for post in posts:
                if "reactions" in post and isinstance(post["reactions"], str):
                    try:
                        post["reactions"] = json.loads(post["reactions"])
                    except:
                        post["reactions"] = {}

                if "comments_list" in post and isinstance(post["comments_list"], str):
                    try:
                        post["comments_list"] = json.loads(post["comments_list"])
                    except:
                        post["comments_list"] = []

                # Convert published_at to datetime
                if "published_at" in post:
                    try:
                        post["published_at"] = pd.to_datetime(post["published_at"])
                    except:
                        pass

            # Calculate completeness
            completeness = calculate_data_completeness(posts, platform)
            all_results[platform] = completeness

            # Print report
            print_completeness_report(completeness, platform)

            # Show sample data structure
            if posts:
                print(f"Sample {platform} Post Structure:")
                print("-" * 60)
                sample = posts[0]
                for key, value in sample.items():
                    value_str = str(value)
                    if len(value_str) > 50:
                        value_str = value_str[:50] + "..."
                    print(f"  {key}: {type(value).__name__} = {value_str}")
                print("\n")

        except Exception as e:
            print(f"❌ Error processing {platform} data: {str(e)}\n")

    # Summary
    print("\n" + "=" * 70)
    print("AUDIT SUMMARY")
    print("=" * 70 + "\n")

    for platform, results in all_results.items():
        status = (
            "✅"
            if results["completeness_rate"] >= 80
            else "⚠️"
            if results["completeness_rate"] >= 50
            else "❌"
        )
        print(
            f"{status} {platform}: {results['completeness_rate']:.1f}% complete ({results['valid_posts']}/{results['total_posts']} valid posts)"
        )

    print("\n" + "=" * 70)

    # Recommendations
    print("\n💡 RECOMMENDATIONS:\n")

    for platform, results in all_results.items():
        if results["completeness_rate"] < 100:
            print(f"\n{platform}:")

            # Find fields with low completeness
            incomplete_fields = [
                (field, stats)
                for field, stats in results["field_completeness"].items()
                if stats["percentage"] < 80
            ]

            if incomplete_fields:
                print("  Fields needing attention:")
                for field, stats in sorted(incomplete_fields, key=lambda x: x[1]["percentage"]):
                    print(f"    - {field}: {stats['percentage']:.1f}% complete")
                    if field == "comments_list" and stats["percentage"] < 50:
                        print(f"      💡 Enable 'Fetch Detailed Comments' to get comment content")
                    elif field == "reactions" and stats["percentage"] < 80:
                        print(f"      💡 Verify Facebook actor returns reaction breakdown")

            if results["common_errors"]:
                print("  Common issues:")
                for error_info in results["common_errors"][:3]:
                    print(f"    - {error_info['error']}")

    print("\n" + "=" * 70 + "\n")


def show_platform_schemas():
    """Display expected data schemas for each platform"""

    print("\n" + "=" * 70)
    print("EXPECTED DATA SCHEMAS")
    print("=" * 70 + "\n")

    schemas = {
        "Facebook": {
            "Required Fields": [
                "post_id (str)",
                "published_at (datetime/str)",
                "text (str)",
                "post_url (str)",
            ],
            "Numeric Fields": [
                "likes (int) - sum of all reactions",
                "comments_count (int)",
                "shares_count (int)",
            ],
            "Complex Fields": [
                "reactions (dict) - {type: count}",
                "comments_list (list[dict]/list[str])",
            ],
        },
        "Instagram": {
            "Required Fields": [
                "post_id (str)",
                "published_at (datetime/str)",
                "text (str)",
                "post_url (str)",
            ],
            "Numeric Fields": ["likes (int)", "comments_count (int)"],
            "Platform-Specific": [
                "ownerUsername (str)",
                "type (str) - photo/video/carousel",
                "hashtags (list[str])",
                "mentions (list[str])",
            ],
        },
        "YouTube": {
            "Required Fields": [
                "post_id (str) - video ID",
                "published_at (datetime/str)",
                "text (str) - title or description",
            ],
            "Numeric Fields": ["views (int)", "likes (int)", "comments_count (int)"],
            "Platform-Specific": ["url (str) - video URL", "duration (str)", "channel (str)"],
        },
    }

    for platform, schema in schemas.items():
        print(f"\n{platform} Schema:")
        print("-" * 60)
        for category, fields in schema.items():
            print(f"\n  {category}:")
            for field in fields:
                print(f"    • {field}")
        print()

    print("=" * 70 + "\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Audit social media data quality")
    parser.add_argument("--schema", action="store_true", help="Show expected data schemas")
    args = parser.parse_args()

    if args.schema:
        show_platform_schemas()
    else:
        audit_saved_data()
