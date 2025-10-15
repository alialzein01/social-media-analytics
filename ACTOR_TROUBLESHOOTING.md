# Facebook Actor Troubleshooting Guide

## "Actor was not found" Error

If you're getting this error, here are the steps to resolve it:

### 1. Check Actor Access

First, verify you have access to the actor:

1. **Go to Apify Console**: https://console.apify.com/
2. **Search for the actor**: `scraper_one-facebook-posts-scraper`
3. **Check if it's available** in your account
4. **Verify your subscription** allows access to this actor

### 2. Try Different Actor Identifiers

The actor might be referenced in different ways. Try these formats:

#### ✅ Correct Configuration (Use This)
```python
ACTOR_CONFIG = {
    "Facebook": "zanTWNqB3Poz44qdY"  # Actor ID: scraper_one/facebook-posts-scraper
}
```

#### Alternative Formats (if needed)
```python
# Actor name format
ACTOR_CONFIG = {
    "Facebook": "scraper_one/facebook-posts-scraper"
}

# Full actor path
ACTOR_CONFIG = {
    "Facebook": "scraper_one/facebook-posts-scraper"
}
```

### 3. Alternative Facebook Actors

If the scraper_one actor doesn't work, try these alternatives:

#### Option 1: Original Apify Actor
```python
ACTOR_CONFIG = {
    "Facebook": "apify/facebook-posts-scraper"
}
```

#### Option 2: Different Facebook Scraper
```python
ACTOR_CONFIG = {
    "Facebook": "facebook-posts-scraper"
}
```

#### Option 3: Use Actor ID
```python
ACTOR_CONFIG = {
    "Facebook": "KoJrdxJCTtpon81KY"  # Replace with actual actor ID
}
```

### 4. Test Actor Access

Create a simple test script to verify actor access:

```python
from apify_client import ApifyClient

# Test different actor identifiers
actors_to_test = [
    "scraper_one-facebook-posts-scraper",
    "zanTWNqB3Poz44qdY",
    "apify/facebook-posts-scraper",
    "facebook-posts-scraper"
]

client = ApifyClient("YOUR_API_TOKEN")

for actor_id in actors_to_test:
    try:
        actor_info = client.actor(actor_id).get()
        print(f"✅ {actor_id}: {actor_info.get('name', 'Unknown')}")
    except Exception as e:
        print(f"❌ {actor_id}: {str(e)}")
```

### 5. Check Input Format

Make sure the input format matches the actor's requirements:

#### For scraper_one-facebook-posts-scraper:
```json
{
  "pageUrls": ["https://www.facebook.com/NASA/"],
  "resultsLimit": 10
}
```

#### For apify/facebook-posts-scraper:
```json
{
  "startUrls": [{"url": "https://www.facebook.com/NASA/"}],
  "maxPosts": 10
}
```

### 6. Verify API Token

Make sure your API token is valid:

```bash
# Test your token
curl -H "Authorization: Bearer YOUR_API_TOKEN" \
     https://api.apify.com/v2/users/me
```

### 7. Check Rate Limits

The actor might be rate-limited:

1. **Check your usage** in Apify Console
2. **Wait a few minutes** and try again
3. **Upgrade your plan** if needed

### 8. Fallback to Original Actor

If nothing works, revert to the original actor:

```python
# In social_media_app.py, change:
ACTOR_CONFIG = {
    "Facebook": "apify/facebook-posts-scraper"  # Original actor
}

# And update the input format:
run_input = {
    "startUrls": [{"url": url}], 
    "maxPosts": max_posts
}
```

### 9. Contact Support

If you're still having issues:

1. **Check Apify Documentation**: https://docs.apify.com/
2. **Contact Apify Support**: support@apify.com
3. **Check Actor Issues**: Look for GitHub issues or Apify community posts

### 10. Quick Fix

For immediate testing, try this configuration:

```python
# Quick fix - use original actor
ACTOR_CONFIG = {
    "Facebook": "apify/facebook-posts-scraper"
}

# With original input format
run_input = {
    "startUrls": [{"url": url}], 
    "maxPosts": max_posts
}
```

## Testing Steps

1. **Set your API token**:
   ```bash
   export APIFY_TOKEN=your_token_here
   ```

2. **Test the configuration**:
   ```bash
   python3 test_actor_config.py
   ```

3. **Test with real data**:
   ```bash
   python3 test_facebook_workflow.py
   ```

4. **Run the app**:
   ```bash
   streamlit run social_media_app.py
   ```

## Common Solutions

- **Most Common**: Use `apify/facebook-posts-scraper` (original actor)
- **If you have access**: Use `scraper_one-facebook-posts-scraper`
- **For testing**: Use any working Facebook posts scraper
- **Check permissions**: Ensure your account can access the actor

The key is to find an actor that works with your account and subscription level!
