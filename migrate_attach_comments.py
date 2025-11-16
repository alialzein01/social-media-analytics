"""
One-time migration to attach comments from the `comments` collection into
`posts.comments_list` for easier in-app analysis.

Usage:
    # Dry-run preview (recommended)
    python migrate_attach_comments.py --platform Instagram --dry-run

    # Apply changes
    python migrate_attach_comments.py --platform Instagram

Notes:
- Idempotent: repeated runs will produce the same result.
- Converts only when matching comments exist; won't remove existing comments_list.
- Back up your DB before running the non-dry-run.
"""

from datetime import datetime
import argparse
import sys
from collections import defaultdict

from app.config.database import get_database


def migrate_attach_comments(platform: str = None, dry_run: bool = True):
    db = get_database()
    posts_coll = db.get_collection('posts')
    comments_coll = db.get_collection('comments')

    # Build comment maps
    comment_query = {}
    if platform:
        comment_query['platform'] = {'$regex': f'^{platform}$', '$options': 'i'}

    print('Loading comments from database...')
    cursor = comments_coll.find(comment_query)

    comments_by_postid = defaultdict(list)
    comments_by_postId = defaultdict(list)
    comments_by_post_url = defaultdict(list)

    total_comments = 0
    for c in cursor:
        total_comments += 1
        pid = c.get('post_id') or c.get('postId') or None
        if pid:
            comments_by_postid[str(pid)].append(c)
        if c.get('postId'):
            comments_by_postId[str(c.get('postId'))].append(c)
        purl = c.get('post_url') or c.get('url') or c.get('postUrl') or None
        if purl:
            comments_by_post_url[str(purl)].append(c)

    print(f'Total comments loaded: {total_comments}')
    print(f'Unique post_id keys: {len(comments_by_postid)}')

    # Query posts
    post_query = {}
    if platform:
        post_query['platform'] = {'$regex': f'^{platform}$', '$options': 'i'}

    posts_cursor = posts_coll.find(post_query)

    updates = []
    inspected = 0
    matched_posts = 0

    for post in posts_cursor:
        inspected += 1
        post_id = post.get('post_id')
        post_url = post.get('post_url') or post.get('url')

        attached = []
        if post_id and str(post_id) in comments_by_postid:
            attached.extend(comments_by_postid[str(post_id)])
        if post_id and str(post_id) in comments_by_postId:
            attached.extend(comments_by_postId[str(post_id)])
        if post_url and str(post_url) in comments_by_post_url:
            attached.extend(comments_by_post_url.get(str(post_url), []))

        # fallback: look for any comment whose post_url contains the post_id
        if not attached and post_id:
            for purl, clist in comments_by_post_url.items():
                if str(post_id) in purl:
                    attached.extend(clist)
                    break

        # dedupe by comment_id
        seen = set()
        deduped = []
        for c in attached:
            cid = c.get('comment_id') or c.get('id') or None
            key = cid or str(c)
            if key not in seen:
                seen.add(key)
                deduped.append(c)

        if deduped:
            matched_posts += 1
            updates.append((post['_id'], post.get('post_id'), len(deduped)))

    print(f'Posts inspected: {inspected}')
    print(f'Posts matched with comments to attach: {matched_posts}')

    if dry_run:
        print('\nDry run mode - sample updates:')
        for _id, pid, count in updates[:20]:
            print(f' - post_id={pid}  _id={_id}  comments_to_attach={count}')
        if len(updates) > 20:
            print(f'   ... and {len(updates)-20} more')
        print('\nNo DB changes were made (dry-run).')
        return

    # Apply updates
    applied = 0
    for _id, pid, count in updates:
        # Recompute attached list to avoid stale memory
        post = posts_coll.find_one({'_id': _id})
        post_id = post.get('post_id')
        post_url = post.get('post_url') or post.get('url')

        attached = []
        if post_id and str(post_id) in comments_by_postid:
            attached.extend(comments_by_postid[str(post_id)])
        if post_id and str(post_id) in comments_by_postId:
            attached.extend(comments_by_postId[str(post_id)])
        if post_url and str(post_url) in comments_by_post_url:
            attached.extend(comments_by_post_url.get(str(post_url), []))
        if not attached and post_id:
            for purl, clist in comments_by_post_url.items():
                if str(post_id) in purl:
                    attached.extend(clist)
                    break

        seen = set()
        deduped = []
        for c in attached:
            cid = c.get('comment_id') or c.get('id') or None
            key = cid or str(c)
            if key not in seen:
                seen.add(key)
                deduped.append(c)

        # Only update if deduped non-empty
        if deduped:
            res = posts_coll.update_one({'_id': _id}, {'$set': {'comments_list': deduped}})
            if res.modified_count or res.matched_count:
                applied += 1

    print(f'\nMigration applied. Posts updated: {applied}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Attach comments into posts.comments_list')
    parser.add_argument('--platform', help='Platform to filter (Instagram, Facebook, YouTube)', default=None)
    parser.add_argument('--dry-run', help='Preview changes without modifying DB', action='store_true')
    args = parser.parse_args()

    if not args.dry_run:
        print('⚠️  You are about to modify your database. Make a backup before continuing.')
        resp = input('Continue? (yes/no): ').strip().lower()
        if resp not in ('yes', 'y'):
            print('Migration cancelled.')
            sys.exit(0)

    migrate_attach_comments(platform=args.platform, dry_run=args.dry_run)
