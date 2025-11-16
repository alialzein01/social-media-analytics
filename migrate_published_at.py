"""
Migration script to normalize `published_at` fields in the `posts` collection.

It converts ISO-formatted string timestamps (e.g. "2024-11-27T18:59:49.000Z") into
proper Python datetimes which MongoDB stores as BSON datetimes. This makes date-range
queries reliable and consistent.

Usage:
    python migrate_published_at.py --dry-run --platform Instagram
    python migrate_published_at.py --platform Instagram

Options:
    --platform <name>   Optional platform filter (Instagram, Facebook, YouTube)
    --dry-run           Show what would be changed without modifying the DB

Safety:
- The script is idempotent: it only converts string `published_at` values to datetimes.
- It will NOT touch documents where `published_at` is already a BSON datetime.
- Still, please backup your database before running the non-dry-run migration.
"""

from __future__ import annotations

import sys
import argparse
from datetime import datetime, timezone
from typing import Optional

from app.config.database import get_database


def parse_iso_to_dt(s: str) -> Optional[datetime]:
    if not isinstance(s, str):
        return None
    s = s.strip()
    if not s:
        return None
    # Remove trailing Z
    if s.endswith('Z'):
        s2 = s[:-1]
    else:
        s2 = s
    # Some strings may include newline or whitespace
    s2 = s2.strip()
    # Try fromisoformat (handles YYYY-MM-DDTHH:MM:SS[.ffffff])
    try:
        # fromisoformat expects no Z; assume UTC
        dt = datetime.fromisoformat(s2)
        # If dt is naive, treat as UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        # Fallback formats
        for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
            try:
                dt = datetime.strptime(s2, fmt)
                dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except Exception:
                continue
    return None


def migrate_published_at(platform: Optional[str] = None, dry_run: bool = True):
    db = get_database()
    posts = db.get_collection('posts')

    query = {}
    if platform:
        query['platform'] = {'$regex': f'^{platform}$', '$options': 'i'}

    # Find posts where published_at exists and is a string
    query['published_at'] = {'$exists': True}

    cursor = posts.find(query, {'_id': 1, 'post_id': 1, 'published_at': 1})

    total = 0
    convertible = []

    for doc in cursor:
        total += 1
        pa = doc.get('published_at')
        if isinstance(pa, str):
            dt = parse_iso_to_dt(pa)
            if dt:
                convertible.append((doc['_id'], doc.get('post_id'), pa, dt))

    print(f"Total posts inspected: {total}")
    print(f"Convertible published_at strings found: {len(convertible)}")

    if dry_run:
        print("\nDry run mode - the following documents would be updated:")
        for _id, pid, old, new in convertible[:20]:
            print(f" - post_id={pid}  _id={_id}  old={old}  -> new={new.isoformat()}")
        if len(convertible) > 20:
            print(f"   ... and {len(convertible)-20} more")
        print("\nNo changes made (dry-run). Run without --dry-run to apply updates.")
        return

    # Apply updates in batches
    updated = 0
    for _id, pid, old, new in convertible:
        res = posts.update_one({'_id': _id, 'published_at': old}, {'$set': {'published_at': new}})
        if res.modified_count:
            updated += 1

    print(f"\nMigration complete. Documents updated: {updated}")


def main(argv=None):
    parser = argparse.ArgumentParser(description='Normalize published_at fields in posts collection')
    parser.add_argument('--platform', help='Platform to filter (Instagram, Facebook, YouTube)', default=None)
    parser.add_argument('--dry-run', help='Preview changes without modifying DB', action='store_true')
    args = parser.parse_args(argv)

    if not args.dry_run:
        print("⚠️  You are about to modify your database. Make a backup before continuing.")
        resp = input('Continue? (yes/no): ').strip().lower()
        if resp not in ('yes', 'y'):
            print('Migration cancelled.')
            sys.exit(0)

    migrate_published_at(platform=args.platform, dry_run=args.dry_run)


if __name__ == '__main__':
    main()
