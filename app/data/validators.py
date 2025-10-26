"""
Data Validation and Quality Checks
==================================

This module provides validation functions to ensure data integrity
from different social media platforms (Facebook, Instagram, YouTube).
"""

from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import pandas as pd


def validate_facebook_post(post: Dict) -> Tuple[bool, List[str]]:
    """
    Validate Facebook post has required fields and correct data types.

    Args:
        post: Dictionary containing Facebook post data

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    # Core required fields (must be present)
    core_required = {
        'post_id': str,
        'published_at': (datetime, str),  # Can be datetime or string
        'text': str
    }

    # Optional but recommended fields
    recommended_fields = {'post_url': str}

    # Check core required fields
    for field, expected_type in core_required.items():
        if field not in post:
            errors.append(f"Missing required field: {field}")
        elif post[field] is None:
            errors.append(f"Field '{field}' is None")
        elif not isinstance(post[field], expected_type if isinstance(expected_type, tuple) else (expected_type,)):
            errors.append(f"Field '{field}' has wrong type: expected {expected_type}, got {type(post[field])}")

    # Check recommended fields (warning only)
    for field, expected_type in recommended_fields.items():
        if field not in post or post[field] is None or post[field] == '':
            errors.append(f"⚠️  Missing recommended field: {field}")

    # Check numeric fields
    numeric_fields = ['likes', 'comments_count', 'shares_count']
    for field in numeric_fields:
        if field in post and post[field] is not None:
            if not isinstance(post[field], (int, float)):
                errors.append(f"Field '{field}' should be numeric, got {type(post[field])}")
            elif post[field] < 0:
                errors.append(f"Field '{field}' should be non-negative, got {post[field]}")

    # Check reactions field
    if 'reactions' in post and post['reactions'] is not None:
        if not isinstance(post['reactions'], dict):
            errors.append(f"Field 'reactions' should be dict, got {type(post['reactions'])}")
        else:
            # Verify reaction values are numeric
            for reaction_type, count in post['reactions'].items():
                if not isinstance(count, (int, float)):
                    errors.append(f"Reaction '{reaction_type}' count should be numeric, got {type(count)}")
                elif count < 0:
                    errors.append(f"Reaction '{reaction_type}' count should be non-negative, got {count}")

    # Check comments_list structure
    if 'comments_list' in post and post['comments_list'] is not None:
        if isinstance(post['comments_list'], list):
            # Comments should be either dict objects or strings
            for i, comment in enumerate(post['comments_list']):
                if not isinstance(comment, (dict, str)):
                    errors.append(f"Comment at index {i} has invalid type: {type(comment)}")
        elif not isinstance(post['comments_list'], int):
            # Could be an int (count) instead of list
            errors.append(f"Field 'comments_list' should be list or int, got {type(post['comments_list'])}")

    is_valid = len(errors) == 0
    return is_valid, errors


def validate_instagram_post(post: Dict) -> Tuple[bool, List[str]]:
    """
    Validate Instagram post has required fields and correct data types.

    Args:
        post: Dictionary containing Instagram post data

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    # Core required fields
    core_required = {
        'post_id': str,
        'published_at': (datetime, str),
        'text': str
    }

    # Optional but recommended fields
    recommended_fields = {
        'post_url': str,
        'ownerUsername': str,
        'hashtags': list
    }

    # Check core required fields
    for field, expected_type in core_required.items():
        if field not in post:
            errors.append(f"Missing required field: {field}")
        elif post[field] is None:
            errors.append(f"Field '{field}' is None")
        elif not isinstance(post[field], expected_type if isinstance(expected_type, tuple) else (expected_type,)):
            errors.append(f"Field '{field}' has wrong type: expected {expected_type}, got {type(post[field])}")

    # Check recommended fields (warning only)
    for field, expected_type in recommended_fields.items():
        if field not in post or post[field] is None or post[field] == '' or post[field] == []:
            errors.append(f"⚠️  Missing recommended field: {field}")

    # Check numeric fields
    numeric_fields = ['likes', 'comments_count']
    for field in numeric_fields:
        if field in post and post[field] is not None:
            if not isinstance(post[field], (int, float)):
                errors.append(f"Field '{field}' should be numeric, got {type(post[field])}")
            elif post[field] < 0:
                errors.append(f"Field '{field}' should be non-negative, got {post[field]}")

    # Instagram-specific fields
    instagram_fields = ['ownerUsername', 'type', 'hashtags']
    for field in instagram_fields:
        if field in post and post[field] is not None:
            if field == 'hashtags' and not isinstance(post[field], list):
                errors.append(f"Field 'hashtags' should be list, got {type(post[field])}")
            elif field in ['ownerUsername', 'type'] and not isinstance(post[field], str):
                errors.append(f"Field '{field}' should be string, got {type(post[field])}")

    is_valid = len(errors) == 0
    return is_valid, errors


def validate_youtube_video(video: Dict) -> Tuple[bool, List[str]]:
    """
    Validate YouTube video has required fields and correct data types.

    Args:
        video: Dictionary containing YouTube video data

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    required_fields = {
        'post_id': str,
        'published_at': (datetime, str),
        'text': str  # Could be title or description
    }

    # Check required fields
    for field, expected_type in required_fields.items():
        if field not in video:
            errors.append(f"Missing required field: {field}")
        elif video[field] is None:
            errors.append(f"Field '{field}' is None")
        elif not isinstance(video[field], expected_type if isinstance(expected_type, tuple) else (expected_type,)):
            errors.append(f"Field '{field}' has wrong type: expected {expected_type}, got {type(video[field])}")

    # Check numeric fields
    numeric_fields = ['likes', 'comments_count', 'views']
    for field in numeric_fields:
        if field in video and video[field] is not None:
            if not isinstance(video[field], (int, float)):
                errors.append(f"Field '{field}' should be numeric, got {type(video[field])}")
            elif video[field] < 0:
                errors.append(f"Field '{field}' should be non-negative, got {video[field]}")

    # YouTube-specific fields
    if 'url' in video and video['url'] is not None:
        if not isinstance(video['url'], str):
            errors.append(f"Field 'url' should be string, got {type(video['url'])}")
        elif not video['url'].startswith('http'):
            errors.append(f"Field 'url' should be valid URL, got {video['url']}")

    is_valid = len(errors) == 0
    return is_valid, errors


def calculate_data_completeness(posts: List[Dict], platform: str) -> Dict[str, Any]:
    """
    Calculate data completeness metrics for a list of posts.

    Args:
        posts: List of post dictionaries
        platform: Platform name ('Facebook', 'Instagram', 'YouTube')

    Returns:
        Dictionary with completeness metrics
    """
    if not posts:
        return {
            'total_posts': 0,
            'valid_posts': 0,
            'invalid_posts': 0,
            'completeness_rate': 0.0,
            'field_completeness': {},
            'common_errors': []
        }

    # Select validator based on platform
    validators = {
        'Facebook': validate_facebook_post,
        'Instagram': validate_instagram_post,
        'YouTube': validate_youtube_video
    }

    validator = validators.get(platform, validate_facebook_post)

    # Validate all posts
    validation_results = [validator(post) for post in posts]

    # Count posts with actual errors (not warnings)
    valid_count = sum(1 for is_valid, errors in validation_results
                     if is_valid or all(e.startswith('⚠️') for e in errors))
    invalid_count = len(posts) - valid_count

    # Collect all errors (including warnings)
    all_errors = []
    for is_valid, errors in validation_results:
        all_errors.extend(errors)

    # Count error frequency
    from collections import Counter
    error_counter = Counter(all_errors)
    common_errors = [{'error': error, 'count': count} for error, count in error_counter.most_common(10)]

    # Calculate field-level completeness
    field_completeness = {}

    # Common fields to check
    common_fields = ['post_id', 'published_at', 'text', 'likes', 'comments_count', 'comments_list']
    if platform == 'Facebook':
        common_fields.extend(['reactions', 'shares_count', 'post_url'])
    elif platform == 'Instagram':
        common_fields.extend(['hashtags', 'ownerUsername', 'post_url'])
    elif platform == 'YouTube':
        common_fields.extend(['views', 'url', 'duration'])

    for field in common_fields:
        present_count = sum(1 for post in posts if field in post and post[field] is not None)
        if field == 'comments_list':
            # For comments_list, check if it has actual content (not empty list)
            present_count = sum(1 for post in posts
                              if field in post and post[field] and
                              (isinstance(post[field], list) and len(post[field]) > 0 or
                               isinstance(post[field], int) and post[field] > 0))

        field_completeness[field] = {
            'present': present_count,
            'missing': len(posts) - present_count,
            'percentage': (present_count / len(posts)) * 100 if posts else 0
        }

    return {
        'total_posts': len(posts),
        'valid_posts': valid_count,
        'invalid_posts': invalid_count,
        'completeness_rate': (valid_count / len(posts)) * 100 if posts else 0,
        'field_completeness': field_completeness,
        'common_errors': common_errors
    }


def print_completeness_report(completeness: Dict[str, Any], platform: str):
    """
    Print a formatted data completeness report.

    Args:
        completeness: Dictionary from calculate_data_completeness
        platform: Platform name
    """
    print(f"\n{'='*60}")
    print(f"Data Completeness Report - {platform}")
    print(f"{'='*60}\n")

    print(f"Total Posts: {completeness['total_posts']}")
    print(f"Valid Posts: {completeness['valid_posts']}")
    print(f"Invalid Posts: {completeness['invalid_posts']}")
    print(f"Completeness Rate: {completeness['completeness_rate']:.1f}%\n")

    print("Field Completeness:")
    print(f"{'Field':<20} {'Present':<10} {'Missing':<10} {'Percentage':<12}")
    print("-" * 60)

    for field, stats in completeness['field_completeness'].items():
        print(f"{field:<20} {stats['present']:<10} {stats['missing']:<10} {stats['percentage']:.1f}%")

    if completeness['common_errors']:
        print(f"\nMost Common Errors:")
        for error_info in completeness['common_errors'][:5]:
            print(f"  - {error_info['error']} (occurred {error_info['count']} times)")

    print(f"\n{'='*60}\n")


# Additional helper functions

def validate_all_platforms(facebook_posts: List[Dict] = None,
                          instagram_posts: List[Dict] = None,
                          youtube_videos: List[Dict] = None) -> Dict[str, Dict]:
    """
    Validate posts from all platforms and return comprehensive report.

    Args:
        facebook_posts: List of Facebook posts
        instagram_posts: List of Instagram posts
        youtube_videos: List of YouTube videos

    Returns:
        Dictionary with validation results for each platform
    """
    results = {}

    if facebook_posts:
        results['Facebook'] = calculate_data_completeness(facebook_posts, 'Facebook')

    if instagram_posts:
        results['Instagram'] = calculate_data_completeness(instagram_posts, 'Instagram')

    if youtube_videos:
        results['YouTube'] = calculate_data_completeness(youtube_videos, 'YouTube')

    return results


def get_posts_with_complete_data(posts: List[Dict], platform: str) -> List[Dict]:
    """
    Filter posts to only include those with complete, valid data.

    Args:
        posts: List of posts
        platform: Platform name

    Returns:
        List of valid posts only
    """
    validators = {
        'Facebook': validate_facebook_post,
        'Instagram': validate_instagram_post,
        'YouTube': validate_youtube_video
    }

    validator = validators.get(platform, validate_facebook_post)

    valid_posts = []
    for post in posts:
        is_valid, errors = validator(post)
        if is_valid:
            valid_posts.append(post)

    return valid_posts
