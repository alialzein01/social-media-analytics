from app.config.database import get_database
from datetime import datetime, timedelta
from collections import Counter


def main():
    db = get_database()
    posts = db.get_collection('posts')
    platform_filter = {'$regex': '^Instagram$', '$options': 'i'}

    total = posts.count_documents({'platform': platform_filter})
    has_pa = posts.count_documents({'platform': platform_filter, 'published_at': {'$exists': True}})
    print('Total Instagram posts:', total)
    print('Posts with published_at field:', has_pa)

    print('\nSample posts (up to 10) - published_at and type:')
    for i, p in enumerate(posts.find({'platform': platform_filter}).limit(10), 1):
        pa = p.get('published_at')
        print(f"{i}. post_id={p.get('post_id')}  published_at={repr(pa)}  type={type(pa).__name__}")

    ctr = Counter()
    for p in posts.find({'platform': platform_filter}, {'published_at': 1}):
        pa = p.get('published_at')
        ctr[type(pa).__name__ if pa is not None else 'None'] += 1

    print('\npublished_at types distribution:')
    for k, v in ctr.items():
        print(f"  {k}: {v}")

    now = datetime.utcnow()
    start = now - timedelta(days=30)
    count_dt = posts.count_documents({'platform': platform_filter, 'published_at': {'$gte': start, '$lte': now}})
    print(f"\nPosts with datetime published_at in last 30 days: {count_dt}")

    ym_prefix = now.strftime('%Y-%m')
    count_str_prefix = posts.count_documents({'platform': platform_filter, 'published_at': {'$regex': f'^{ym_prefix}'}})
    print(f"Posts with published_at string starting with {ym_prefix}: {count_str_prefix}")

    print('\nEarliest 3 published_at values:')
    for p in posts.find({'platform': platform_filter, 'published_at': {'$exists': True}}).sort('published_at', 1).limit(3):
        print(' ', p.get('published_at'))

    print('\nLatest 3 published_at values:')
    for p in posts.find({'platform': platform_filter, 'published_at': {'$exists': True}}).sort('published_at', -1).limit(3):
        print(' ', p.get('published_at'))


if __name__ == '__main__':
    main()
