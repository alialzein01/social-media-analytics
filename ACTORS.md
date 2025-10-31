# Apify Actors Used in This App

This document lists each Apify actor the app calls, grouped by platform, with IDs/names and where they are used in the code.

## Facebook (3-Actor Workflow)

### 1. Posts Scraper
  - **Identifier:** `apify~facebook-posts-scraper` (KoJrdxJCTtpon81KY)
  - **Purpose:** Fetches posts from Facebook pages
  - **Input:** `startUrls`, `resultsLimit`, `proxy`
  - **Output:** Posts with basic engagement data
  - **Used in:** `app/services/data_fetcher.py` (ACTOR_CONFIG["Facebook"])

### 2. Reactions Scraper
  - **Identifier:** `scraper_one~facebook-reactions-scraper` (ZwTmldxYpNvDnWW5f)
  - **Purpose:** Fetches detailed reaction breakdown (Like, Love, Haha, Wow, Sad, Angry)
  - **Input:** `postUrls` (array), `resultsLimit`
  - **Output:** Individual reactions (aggregated by app into counts)
  - **Used in:** `app/services/__init__.py` (FACEBOOK_REACTIONS_ACTOR_ID; `fetch_facebook_reactions`)

### 3. Comments Scrapers (fallback sequence)
  - `us5srxAYnsrkgUv2v` (primary)
  - `apify/facebook-comments-scraper` (fallback 1)
  - `facebook-comments-scraper` (fallback 2)
  - `alien_force/facebook-posts-comments-scraper` (fallback 3)
  - **Purpose:** Fetches comment text for word clouds and sentiment analysis
  - **Used in:** `app/services/data_fetcher.py` (FACEBOOK_COMMENTS_ACTOR_IDS; `_fetch_facebook_comments_batch`)

## Instagram

- Posts Scraper

  - Identifier: `apify/instagram-scraper`
  - Used in: `social_media_app.py` (ACTOR_CONFIG["Instagram"]) and as fallback in Instagram comments list

- Alternative/Legacy ID

  - `shu8hvrXbJbY3Eb9W` (Instagram scraper actor ID seen in ACTOR_IDS mapping)
  - Used in: `social_media_app.py` (ACTOR_IDS["Instagram"]) – not primary path

- Comments Scrapers (fallback sequence)
  - `apify/instagram-comment-scraper`
  - `SbK00X0JYCPblD2wp` (alternative)
  - `instagram-comment-scraper`
  - Fallback to `apify/instagram-scraper`
  - Used in: `social_media_app.py` (INSTAGRAM_COMMENTS_ACTOR_IDS)

## YouTube

- Channel/Videos Scraper

  - Identifier: `h7sDV53CddomktSi5`
  - Notes: Comment indicates `streamers~youtube-scraper`
  - Used in: `social_media_app.py` (ACTOR_CONFIG["YouTube"])

- Comments Scraper
  - Identifier: `p7UMdpQnjKmmpR21D`
  - Used in: `social_media_app.py` (YOUTUBE_COMMENTS_ACTOR_ID; `fetch_youtube_comments`)

## Reference in Code

- Main configuration and usage live in `social_media_app.py`:
  - `ACTOR_CONFIG` for posts by platform
  - `FACEBOOK_COMMENTS_ACTOR_IDS` fallback list
  - `INSTAGRAM_COMMENTS_ACTOR_IDS` fallback list
  - `YOUTUBE_COMMENTS_ACTOR_ID` for YouTube comments
  - Direct calls via `ApifyClient(...).actor(<id_or_name>).call(...)`

If you replace any actor, update the constants in `social_media_app.py` accordingly.
