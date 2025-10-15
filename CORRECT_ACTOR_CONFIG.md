# ✅ Correct Facebook Actor Configuration

## Actor Information

- **Actor ID**: `zanTWNqB3Poz44qdY`
- **Actor Name**: `scraper_one/facebook-posts-scraper`
- **Input Format**: `pageUrls` array with `resultsLimit`

## Current Configuration

### In `social_media_app.py`:
```python
ACTOR_CONFIG = {
    "Facebook": "zanTWNqB3Poz44qdY",  # Actor ID: scraper_one/facebook-posts-scraper
    "Instagram": "apify/instagram-scraper",
    "YouTube": "streamers/youtube-comments-scraper"
}
```

### Input Format:
```python
run_input = {
    "pageUrls": [url],  # Array of Facebook page URLs
    "resultsLimit": max_posts,  # Number of posts to extract
    "fromDate": from_date,  # Optional: start date
    "toDate": to_date  # Optional: end date
}
```

## Testing

### 1. Test Configuration:
```bash
python3 test_actor_config.py
```

### 2. Test with Real Data:
```bash
# Set your API token
export APIFY_TOKEN=your_token_here

# Test the workflow
python3 test_facebook_workflow.py
```

### 3. Run the App:
```bash
streamlit run social_media_app.py
```

## Expected Output Format

The actor returns posts with these fields:
- `url`: Post permalink
- `pageUrl`: Source page URL
- `timestamp`: Post timestamp
- `postText`: Post content
- `reactionsCount`: Total reactions
- `reactions`: Detailed reaction breakdown
- `commentsCount`: Number of comments
- `postId`: Unique post identifier
- `author`: Author information

## Troubleshooting

If you still get "Actor was not found":

1. **Verify Access**: Check you have access to `scraper_one/facebook-posts-scraper` in your Apify account
2. **Check Subscription**: Ensure your plan includes access to this actor
3. **Try Alternative**: Use `apify/facebook-posts-scraper` as fallback
4. **Contact Support**: Reach out to Apify support if needed

## Fallback Configuration

If the new actor doesn't work, use the original:

```python
ACTOR_CONFIG = {
    "Facebook": "apify/facebook-posts-scraper"  # Original actor
}

# With original input format
run_input = {
    "startUrls": [{"url": url}], 
    "maxPosts": max_posts
}
```

The configuration is now correct and should work with your Apify account!
