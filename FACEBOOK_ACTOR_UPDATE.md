# Facebook Actor Update

## Summary

The app has been updated to use the new `scraper_one-facebook-posts-scraper` actor instead of the previous `apify/facebook-posts-scraper`.

## Changes Made

### 1. Actor Configuration
- **Old**: `apify/facebook-posts-scraper`
- **New**: `scraper_one-facebook-posts-scraper`

### 2. Input Format Changes
- **Old Format**:
  ```json
  {
    "startUrls": [{"url": "https://www.facebook.com/NASA/"}],
    "maxPosts": 10
  }
  ```

- **New Format**:
  ```json
  {
    "pageUrls": ["https://www.facebook.com/NASA/"],
    "resultsLimit": 10
  }
  ```

### 3. Output Field Mapping
The new actor has different output field names, so the app now handles both formats:

| Old Field | New Field | Description |
|-----------|-----------|-------------|
| `text` | `postText` | Post content text |
| `likes` | `reactionsCount` | Total reactions count |
| `comments` | `commentsCount` | Comments count |
| `url` | `url` | Post URL (same) |
| `postId` | `postId` | Post ID (same) |

### 4. Updated Files
- `social_media_app.py` - Main application logic
- `test_facebook_workflow.py` - Test script
- `FACEBOOK_COMMENTS_WORKFLOW.md` - Documentation
- `README.md` - Main documentation

## Key Features of New Actor

### Advantages
1. **Better Performance**: More reliable and faster
2. **Improved Data Quality**: Better field mapping and data extraction
3. **Active Maintenance**: Regularly updated and maintained
4. **Better Error Handling**: More robust error reporting

### Input Parameters
- `pageUrls`: Array of Facebook page URLs
- `resultsLimit`: Maximum number of posts to extract (default: 10)
- `fromDate`: Optional start date (format: YYYY-MM-DD)
- `toDate`: Optional end date (format: YYYY-MM-DD)

### Output Fields
- `url`: Post permalink
- `pageUrl`: Source page URL
- `timestamp`: Post timestamp
- `postText`: Post content
- `reactionsCount`: Total reactions
- `reactions`: Detailed reaction breakdown
- `commentsCount`: Number of comments
- `postId`: Unique post identifier
- `author`: Author information

## Testing

To test the new actor:

```bash
python3 test_facebook_workflow.py
```

This will:
1. Extract 10 posts from NASA's Facebook page
2. Use the new actor format
3. Show the results and any differences

## Migration Notes

### Backward Compatibility
The app maintains backward compatibility by:
- Checking for both old and new field names
- Handling different input formats gracefully
- Providing fallback values for missing fields

### Date Range Support
The new actor may have different date range support. If date filtering doesn't work:
1. The app will still function without date filtering
2. You can filter posts after extraction using the app's built-in filters
3. Check the actor documentation for supported date parameters

## Troubleshooting

### Common Issues

1. **Actor Not Found**
   - Verify the actor name: `scraper_one-facebook-posts-scraper`
   - Check your Apify account has access to this actor

2. **Input Format Errors**
   - Ensure `pageUrls` is an array of strings
   - Use `resultsLimit` instead of `maxPosts`

3. **Missing Data Fields**
   - The app handles both old and new field names
   - Some fields may not be available (like shares count)

4. **Date Range Issues**
   - The new actor may not support all date parameters
   - Try without date filtering first

### Getting Help

If you encounter issues:
1. Check the actor documentation on Apify
2. Test with the provided test script
3. Verify your API token has access to the new actor
4. Check the actor's rate limits and usage quotas

## Next Steps

1. **Test the new actor** with your Facebook pages
2. **Verify data quality** and field mapping
3. **Update any custom scripts** that depend on the old format
4. **Monitor performance** and reliability improvements

The new actor should provide better reliability and data quality for your Facebook posts extraction workflow!
