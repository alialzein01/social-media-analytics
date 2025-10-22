# Instagram Workflow Documentation

## ✅ Workflow Verification Complete

The Instagram tab follows the correct 4-step workflow as specified:

---

## 📋 Workflow Steps

### Step 1: Extract Posts (First Scraper)
**Location:** Line 2019 in `social_media_app.py`  
**Function:** `fetch_apify_data()`  
**Actor:** `apify/instagram-scraper`  
**What it does:**
- Fetches Instagram posts from the specified profile/page URL
- Retrieves post metadata: caption, likes count, comments count, hashtags, etc.
- Returns basic post information (comments are just counts at this stage)

```python
# Line 2019
raw_data = fetch_apify_data(platform, url, apify_token, max_posts, from_date, to_date)
```

**Output:**
- List of Instagram posts with:
  - Post ID (shortCode)
  - Caption text
  - Likes count
  - Comments count (just a number)
  - Media URLs
  - Owner information
  - Hashtags and mentions

---

### Step 2: Extract Comments (Second Actor)
**Location:** Lines 2045-2074 in `social_media_app.py`  
**Function:** `scrape_instagram_comments_batch()`  
**Actor:** `apify/instagram-comment-scraper`  
**Trigger:** Only runs if "Fetch Detailed Comments" is enabled in sidebar  
**What it does:**
- Takes the posts extracted in Step 1
- Constructs post URLs from post IDs (shortCodes)
- Calls the Instagram Comments Scraper for each post
- Retrieves actual comment text and metadata

```python
# Lines 2048-2055: Extract post URLs from already-fetched posts
post_urls = []
for post in normalized_data:
    if post.get('post_id'):
        short_code = post.get('post_id')
        post_url = f"https://www.instagram.com/p/{short_code}/"
        post_urls.append(post_url)

# Line 2060: Call second actor to get comments
comments_data = scrape_instagram_comments_batch(post_urls, apify_token, 25)

# Line 2064: Assign comments back to their posts
normalized_data = assign_instagram_comments_to_posts(normalized_data, comments_data)
```

**Output:**
- List of comments with:
  - Comment text
  - Comment author username
  - Timestamp
  - Owner verification status
- Comments are matched to their respective posts via postId

---

### Step 3: Show Monthly Overview
**Location:** Lines 2142-2154 in `social_media_app.py`  
**Functions:** 
- `create_instagram_monthly_analysis()` - Displays Instagram-specific metrics
- `create_instagram_monthly_insights()` - Shows word clouds and sentiment analysis

**What it displays:**
- **Engagement Metrics:**
  - Total posts
  - Total likes
  - Total comments
  - Average engagement per post
  - Top performing posts

- **Content Analysis:**
  - Hashtag frequency
  - Most used words in captions
  - Post type distribution (photos, videos, carousels)

- **Monthly Insights:**
  - Word cloud of most discussed topics (from comments)
  - Sentiment distribution (positive/negative/neutral)
  - Emoji analysis

```python
# Lines 2150-2154
if platform == "Instagram":
    # Show monthly Instagram analysis first
    create_instagram_monthly_analysis(posts, platform)
    # Show monthly insights with word cloud and sentiment
    create_instagram_monthly_insights(posts, platform)
```

---

### Step 4: Show Post Details Analysis
**Location:** Lines 2336-2486 in `social_media_app.py`  
**Section:** "Select a Post for Detailed Analysis"  
**What it displays:**

For each individual post:
- **Post Information:**
  - Caption text
  - Published date
  - Post URL
  - Media preview (if available)
  - Owner username and full name

- **Engagement Metrics:**
  - Likes count
  - Comments count
  - Total engagement

- **Comments Section:**
  - Individual comment display with usernames
  - Timestamps
  - If no detailed comments: Shows message to enable comment fetching

```python
# Line 2336: Post selection dropdown
selected_idx = st.selectbox("Choose a post:", range(len(posts)), ...)

# Lines 2414-2448: Instagram-specific comment display
if platform == "Instagram":
    st.markdown("#### 💬 Instagram Comments")
    comments_list = selected_post.get('comments_list', [])
    
    if isinstance(comments_list, list) and comments_list:
        # Show individual Instagram comments
        for i, comment in enumerate(comments_list, 1):
            # Display comment with username and text
```

---

## 🔄 Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     USER ACTIONS                             │
│  1. Enter Instagram URL                                      │
│  2. Set max posts (optional)                                 │
│  3. Enable "Fetch Detailed Comments" (optional)              │
│  4. Click "Analyze"                                          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│             STEP 1: FETCH POSTS (First Scraper)              │
│                                                              │
│  Actor: apify/instagram-scraper                              │
│  Input: Instagram URL, max_posts                             │
│  Output: Posts with metadata (shortCode, caption, likes,     │
│          commentsCount, hashtags, etc.)                      │
│                                                              │
│  ✅ Posts extracted: 10 posts                                │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│               NORMALIZE POST DATA                            │
│                                                              │
│  Function: normalize_post_data()                             │
│  - Maps Instagram fields to standard schema                  │
│  - Creates post URLs: instagram.com/p/{shortCode}/           │
│  - Sets comments_list to empty initially                     │
└─────────────────────────────────────────────────────────────┘
                              ↓
                    ┌─────────────────┐
                    │ Fetch Comments? │
                    │ (sidebar option)│
                    └─────────────────┘
                    ↙                  ↘
              NO ↙                      ↘ YES
               ↓                          ↓
       ┌──────────────┐    ┌─────────────────────────────────────┐
       │ Skip Step 2  │    │ STEP 2: FETCH COMMENTS (Second Actor)│
       └──────────────┘    │                                       │
               ↓            │ Actor: apify/instagram-comment-      │
               │            │        scraper                        │
               │            │ Input: Post URLs extracted from Step 1│
               │            │ Output: Comments with text, username, │
               │            │         timestamp                     │
               │            │                                       │
               │            │ ✅ Comments extracted: 250 comments   │
               │            └───────────────────────────────────────┘
               │                           ↓
               │            ┌──────────────────────────────────────┐
               │            │     ASSIGN COMMENTS TO POSTS         │
               │            │                                      │
               │            │ Function: assign_instagram_          │
               │            │           comments_to_posts()        │
               │            │ - Matches comments to posts via      │
               │            │   postId                             │
               │            │ - Updates comments_list field        │
               │            └──────────────────────────────────────┘
               │                           ↓
               └──────────────┬────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│           STEP 3: SHOW MONTHLY OVERVIEW                      │
│                                                              │
│  Section: "📈 Monthly Overview"                              │
│                                                              │
│  A. Instagram Monthly Analysis:                              │
│     - Total posts, likes, comments                           │
│     - Average engagement                                     │
│     - Top performing posts                                   │
│     - Hashtag analysis                                       │
│     - Post type distribution                                 │
│                                                              │
│  B. Monthly Insights:                                        │
│     - Word cloud (from comments)                             │
│     - Sentiment distribution                                 │
│     - Emoji analysis                                         │
│     - Most discussed topics                                  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│         STEP 4: SHOW POST DETAILS ANALYSIS                   │
│                                                              │
│  Section: "🎯 Select a Post for Detailed Analysis"           │
│                                                              │
│  User selects a post from dropdown                           │
│  ↓                                                           │
│  Display:                                                    │
│  - Post caption and metadata                                 │
│  - Media preview                                             │
│  - Owner information                                         │
│  - Engagement metrics (likes, comments)                      │
│  - Individual comments with usernames                        │
│  - Post-specific analysis                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 💡 Key Features

### Sequential Processing
✅ **Correct:** Posts are fetched first, then comments are extracted from those posts
- This ensures we have valid post URLs before attempting to fetch comments
- Comments are always associated with existing posts

### Optional Comment Fetching
✅ **User Control:** Comments are only fetched if user enables "Fetch Detailed Comments"
- Saves API credits when full comment text isn't needed
- Comment counts are always available from Step 1
- Detailed comment text requires Step 2

### Two-Actor Architecture
✅ **Separation of Concerns:**
1. **Posts Actor** (`apify/instagram-scraper`): Fast, retrieves post metadata
2. **Comments Actor** (`apify/instagram-comment-scraper`): Detailed, gets comment text

This is more efficient than a single actor doing everything.

---

## 🔍 Data Flow

### After Step 1 (Posts Only)
```python
post = {
    'post_id': 'ABC123xyz',  # Instagram shortCode
    'post_url': 'https://www.instagram.com/p/ABC123xyz/',
    'text': 'Beautiful sunset today 🌅 #nature',
    'likes': 1523,
    'comments_count': 47,  # ⚠️ Just a count, not actual comments
    'comments_list': [],   # ⚠️ Empty at this stage
    'hashtags': ['nature'],
    'ownerUsername': 'john_doe'
}
```

### After Step 2 (Posts + Comments)
```python
post = {
    'post_id': 'ABC123xyz',
    'post_url': 'https://www.instagram.com/p/ABC123xyz/',
    'text': 'Beautiful sunset today 🌅 #nature',
    'likes': 1523,
    'comments_count': 47,  # Updated if different
    'comments_list': [      # ✅ Now populated with actual comments
        {
            'text': 'Amazing photo! 😍',
            'ownerUsername': 'jane_smith',
            'timestamp': '2025-10-22T14:30:00.000Z',
            'ownerIsVerified': False
        },
        {
            'text': 'Love this view!',
            'ownerUsername': 'mike_jones',
            'timestamp': '2025-10-22T15:45:00.000Z',
            'ownerIsVerified': False
        }
        # ... more comments
    ],
    'hashtags': ['nature'],
    'ownerUsername': 'john_doe'
}
```

---

## 📊 UI Sections Breakdown

### 1. Sidebar Configuration
**Location:** Lines 1841-1850
- Toggle: "Fetch Detailed Comments"
- Info about costs and credits
- User can choose to skip comment fetching

### 2. Monthly Overview
**Location:** Lines 2142-2154
- **Always shows:** Post-level metrics (from Step 1)
- **Shows if comments fetched:** Comment analysis, word clouds, sentiment

### 3. Posts Table
**Location:** Lines 2298-2308
- Scrollable table of all posts
- Shows: Date, Caption, Likes, Comments, Shares
- Download CSV button

### 4. Individual Post Analysis
**Location:** Lines 2336-2486
- Dropdown to select any post
- Shows full caption and metadata
- **If comments fetched:** Displays individual comments with usernames
- **If not fetched:** Message to enable comment fetching

---

## ⚙️ Configuration

### Instagram Comments Actor Configuration
**Location:** Lines 69-76 in `social_media_app.py`

```python
INSTAGRAM_COMMENTS_ACTOR_IDS = [
    "apify/instagram-comment-scraper",  # Primary
    "SbK00X0JYCPblD2wp",                # Alternative
    "instagram-comment-scraper",         # Fallback
    "apify/instagram-scraper"            # Last resort
]
```

The app tries multiple actors in order if one fails.

### Input Configuration for Comments Scraper
**Location:** Lines 1027-1035 in `scrape_instagram_comments_batch()`

```python
run_input = {
    "directUrls": [post_url],
    "resultsType": "comments",
    "resultsLimit": 50,  # Max 50 comments per post
    "searchType": "hashtag",
    "searchLimit": 1
}
```

---

## ✅ Workflow Validation Checklist

- [x] **Step 1: Posts Extraction**
  - ✅ First scraper runs: `fetch_apify_data()` with Instagram actor
  - ✅ Posts are fetched with metadata
  - ✅ Post URLs are constructed from shortCodes
  
- [x] **Step 2: Comments Extraction**
  - ✅ Second actor runs: `scrape_instagram_comments_batch()`
  - ✅ Comments are fetched only for posts from Step 1
  - ✅ Comments are assigned back to posts
  - ✅ Optional: User can skip this step
  
- [x] **Step 3: Monthly Overview**
  - ✅ `create_instagram_monthly_analysis()` displays metrics
  - ✅ `create_instagram_monthly_insights()` shows analysis
  - ✅ Word clouds and sentiment work with comments
  
- [x] **Step 4: Post Details**
  - ✅ User can select any post
  - ✅ Individual post analysis is shown
  - ✅ Comments are displayed per post
  - ✅ Helpful message if comments not fetched

---

## 🎯 User Experience Flow

1. **User enters Instagram URL** → e.g., `https://www.instagram.com/natgeo/`
2. **User enables "Fetch Detailed Comments"** (optional)
3. **User clicks "Analyze"**
4. **App shows progress:**
   ```
   ℹ️ Calling Apify actor: apify/instagram-scraper
   ℹ️ Requesting 10 posts from: https://www.instagram.com/natgeo/
   ✅ Successfully processed 10 posts
   ```
5. **If comments enabled:**
   ```
   💡 Note: Instagram Comments Scraper will extract comments...
   🔄 Found 10 Instagram posts to extract comments from...
   ✅ Successfully assigned 250 comments to posts
   ```
6. **Monthly overview displays** with all metrics and insights
7. **User scrolls to post details** and selects a post
8. **Individual post analysis shows** with comments

---

## 🐛 Error Handling

The workflow includes robust error handling:

```python
# If comments fail, app continues with posts only
except Exception as e:
    st.error(f"❌ Failed to fetch Instagram comments: {str(e)}")
    st.warning("⚠️ Continuing without detailed comments...")
    # Continue with the posts without comments
```

This ensures the app doesn't crash if Step 2 fails.

---

## 📝 Summary

**The Instagram workflow is correctly implemented as specified:**

1. ✅ First scraper extracts posts
2. ✅ Second actor extracts comments from those posts
3. ✅ Monthly overview displays aggregated analysis
4. ✅ Post details section shows per-post analysis

**All steps are sequential and data flows correctly from one step to the next.**

---

## 🔗 Related Files

- **Main App:** `social_media_app.py`
- **NLP Processing:** `app/nlp/sentiment_analyzer.py`
- **Visualization:** `app/viz/wordcloud_generator.py`
- **Test Files:** `tests/test_instagram.py`

---

**Workflow Status:** ✅ **VERIFIED AND WORKING CORRECTLY**

