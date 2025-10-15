# Facebook Comments Extraction Workflow

This document explains the new two-phase workflow for extracting Facebook posts and their comments using Apify actors.

## Overview

The workflow consists of two main phases:

1. **Phase 1**: Extract posts from a Facebook page using the Facebook Posts Scraper
2. **Phase 2**: Extract comments from all posts using the Facebook Comments Scraper

## Workflow Architecture

```
Facebook Page URL
       ↓
   [Phase 1: Posts Extraction]
       ↓
   Array of Post URLs
       ↓
   [Phase 2: Comments Extraction]
       ↓
   Posts + Comments Data
       ↓
   [Analysis & Visualization]
       ↓
   Word Clouds & Insights
```

## Phase 1: Posts Extraction

**Actor**: `zanTWNqB3Poz44qdY` (scraper_one/facebook-posts-scraper)

**Input**:
```json
{
  "pageUrls": ["https://www.facebook.com/NASA/"],
  "resultsLimit": 10,
  "fromDate": "2025-09-15",
  "toDate": "2025-10-15"
}
```

**Output**: Array of post objects with URLs, text, engagement metrics, etc.

### Date Range Parameters

The Facebook Posts Scraper supports date filtering:

- **`fromDate`**: Start date for posts (format: "YYYY-MM-DD")
- **`toDate`**: End date for posts (format: "YYYY-MM-DD")
- **Examples**:
  - Last 30 days: `"fromDate": "2025-09-15"` (30 days ago)
  - Last 7 days: `"fromDate": "2025-10-08"` (7 days ago)
  - Custom range: `"fromDate": "2025-09-01", "toDate": "2025-09-30"`

## Phase 2: Comments Extraction

**Actor**: `us5srxAYnsrkgUv2v` (apify-facebook-comments-scraper)

**Input**:
```json
{
  "startUrls": [
    {"url": "https://www.facebook.com/NASA/posts/123456789"},
    {"url": "https://www.facebook.com/NASA/posts/987654321"}
  ],
  "resultsLimit": 50,
  "includeNestedComments": false,
  "viewOption": "RANKED_UNFILTERED"
}
```

**Output**: Array of comment objects with text, author, timestamps, etc.

## Implementation Details

### Batch Processing vs Individual Processing

The app now supports two comment extraction methods:

#### 1. Batch Processing (Recommended)
- **Method**: `fetch_comments_for_posts_batch()`
- **Advantages**: Faster, more efficient, single API call
- **How it works**: Collects all post URLs and sends them to the comments scraper in one batch
- **Best for**: Multiple posts, better performance

#### 2. Individual Processing
- **Method**: `fetch_comments_for_posts()`
- **Advantages**: More reliable, better error handling per post
- **How it works**: Processes each post URL individually with rate limiting
- **Best for**: When batch processing fails, debugging

### Key Functions

#### `fetch_comments_for_posts_batch(posts, apify_token, max_comments_per_post)`
- Extracts all post URLs from the posts array
- Creates a batch input for the comments scraper
- Processes all posts in a single API call
- Assigns comments back to their respective posts

#### `assign_comments_to_posts(posts, comments_data)`
- Maps comments to their respective posts based on URL matching
- Handles various URL formats and variations
- Returns posts with populated comments_list

#### `normalize_comment_data(raw_comment)`
- Standardizes comment data format
- Extracts author names, text, timestamps, likes
- Handles different field names from various actors

## Usage in the App

### UI Controls

1. **Platform Selection**: Choose "Facebook"
2. **Data Source**: Select "Fetch from API"
3. **Facebook Configuration**:
   - **Number of Posts**: Set how many posts to extract (1-50)
   - **Date Range**: Choose "All Posts", "Last 30 Days", "Last 7 Days", or "Custom Range"
4. **Comment Extraction Method**: Choose between "Individual Posts" or "Batch Processing"
5. **Fetch Detailed Comments**: Enable comment extraction
6. **Max Comments per Post**: Set limit (10-100 comments)

### Workflow Steps

1. Enter Facebook page URL
2. Click "Analyze"
3. App extracts posts (Phase 1)
4. If comments enabled, app extracts comments (Phase 2)
5. App analyzes comments and creates word clouds
6. Results are saved to files

## Error Handling

The app includes robust error handling:

- **Multiple Actor Fallback**: Tries different comment scraper actors if one fails
- **Graceful Degradation**: Continues with posts data if comment extraction fails
- **Rate Limiting**: Includes delays between individual post processing
- **URL Validation**: Validates post URLs before comment extraction

## File Outputs

The workflow generates several output files:

- **Raw JSON**: `data/raw/facebook_YYYYMMDD_HHMMSS.json` (posts data)
- **Processed CSV**: `data/processed/facebook_YYYYMMDD_HHMMSS.csv` (posts data)
- **Comments CSV**: `data/processed/facebook_comments_YYYYMMDD_HHMMSS.csv` (comments data)

## Testing

Use the test script to verify the workflow:

```bash
python test_facebook_workflow.py
```

This will:
1. Extract 5 posts from NASA's Facebook page
2. Extract comments from those posts
3. Save results to test files
4. Display summary statistics

## Configuration

### Actor IDs
```python
FACEBOOK_POSTS_ACTOR = "apify/facebook-posts-scraper"
FACEBOOK_COMMENTS_ACTOR_IDS = [
    "us5srxAYnsrkgUv2v",  # Primary actor
    "apify/facebook-comments-scraper", 
    "facebook-comments-scraper",
    "alien_force/facebook-posts-comments-scraper"
]
```

### Input Parameters
- `maxPosts`: Number of posts to extract (default: 10)
- `resultsLimit`: Max comments per post (default: 50)
- `includeNestedComments`: Include reply comments (default: false)
- `viewOption`: Comment sorting (default: "RANKED_UNFILTERED")

## Troubleshooting

### Common Issues

1. **No Comments Found**
   - Check if posts have comments
   - Try different comment extraction method
   - Verify post URLs are valid

2. **Actor Failures**
   - App automatically tries multiple actors
   - Check Apify token validity
   - Verify actor availability

3. **Rate Limiting**
   - Use batch processing for better performance
   - Reduce number of posts/comments
   - Add delays between requests

### Debug Mode

Enable debug logging by setting:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Performance Tips

1. **Use Batch Processing**: More efficient for multiple posts
2. **Limit Comments**: Set reasonable limits (20-50 per post)
3. **Filter Posts**: Only extract comments for posts with high engagement
4. **Cache Results**: Use saved files to avoid re-extraction

## Future Enhancements

- [ ] Real-time comment monitoring
- [ ] Sentiment analysis integration
- [ ] Comment thread visualization
- [ ] Export to different formats
- [ ] Scheduled extraction
- [ ] Multi-page support
