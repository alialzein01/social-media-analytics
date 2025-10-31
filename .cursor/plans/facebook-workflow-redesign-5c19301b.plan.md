<!-- 5c19301b-514b-4ca3-bd9a-052bac0e7ae7 bbd022db-2a24-47ad-8fa9-c2c24bcbf721 -->
# Facebook Workflow Redesign

## Overview

Restructure the app to provide a streamlined Facebook experience with automatic comment fetching, simplified configuration, and a clean 2-tab interface for analysis.

## Changes Required

### 1. Sidebar Simplification (`app/ui/sidebar.py`)

- Remove all configuration toggles except:
- Platform selection (Facebook/Instagram/YouTube)
- Date range selector (default: Last 30 Days)
- Remove:
- Data source selection (always API)
- Fetch detailed comments toggle (always on)
- Comment extraction method selection (always batch)
- Max posts slider
- Analysis options (phrase analysis, sentiment coloring)
- Load from file option

### 2. Facebook Adapter Update (`app/adapters/facebook.py`)

- Ensure default date range is 30 days
- Verify all necessary fields are captured:
- Post captions/text
- Reaction breakdown (like, love, haha, wow, sad, angry)
- Comments count
- Shares count
- Post URL for comment fetching

### 3. Main View Restructure (`app/ui/main_view.py`)

Replace current expandable sections with 2 tabs:

**Tab 1: Monthly Analysis**

- Reaction distribution chart (pie/bar chart showing likes, love, angry, etc.)
- Total comments count metric
- Total shares count metric
- Word cloud from ALL comments across all posts
- Key metrics cards (total posts, total engagement, avg engagement)

**Tab 2: Individual Posts**

- Posts sorted by engagement (highest to lowest)
- Display as cards or table with:
- Post text preview
- Engagement metrics (reactions, comments, shares)
- Click to expand for detailed view
- Individual post analysis on selection:
- Full text
- Reaction breakdown for that post
- Comments list
- Word cloud for that post's comments

### 4. Data Fetching Flow (`social_media_app.py`)

- Auto-fetch posts when user clicks "Analyze" button
- Always fetch comments using batch processing
- Default to last 30 days if no date range specified
- Show loading states for both posts and comments phases

### 5. Word Cloud Generation (`app/viz/wordcloud_generator.py`)

- Ensure word cloud generation is always enabled
- Create two functions:
- `create_monthly_wordcloud()`: Aggregates all comments
- `create_post_wordcloud()`: Single post comments
- Use phrase-based analysis by default

### 6. Analytics Updates (`app/viz/dashboards.py`)

- Create new function `create_facebook_monthly_tab()` with:
- Reaction distribution visualization
- Comment count summary
- Share count summary
- Aggregated word cloud

### 7. Post Sorting & Selection

- Add sorting function to analytics module
- Sort by total engagement (reactions + comments + shares)
- Create post card component for display

## Implementation Steps

1. Simplify sidebar configuration
2. Update data fetching to always include comments
3. Create 2-tab layout in main_view
4. Build Tab 1: Monthly Analysis components
5. Build Tab 2: Posts selection interface
6. Test end-to-end workflow
7. Remove unused code and options

### To-dos

- [ ] Simplify sidebar to only show platform selection and date range (default 30 days)
- [ ] Update data fetching to always fetch comments in batch mode
- [ ] Create 2-tab layout structure in main_view.py
- [ ] Build Tab 1 with reaction distribution, comments/shares stats, and aggregated word cloud
- [ ] Build Tab 2 with sorted posts list and individual post analysis
- [ ] Test complete Facebook workflow end-to-end