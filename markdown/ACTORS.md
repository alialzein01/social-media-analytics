# Apify Actors Used in This App

This document lists each Apify actor the app calls, grouped by platform, with IDs/names and where they are used in the code.

## Facebook

- Posts Scraper

  - Identifier: `zanTWNqB3Poz44qdY`
  - Notes: Alias in comments refers to `scraper_one/facebook-posts-scraper` (better reactions data)
  - Used in: `social_media_app.py` (ACTOR_CONFIG["Facebook"])

- Comments Scrapers (fallback sequence)
  - `us5srxAYnsrkgUv2v` (primary example)
  - `apify/facebook-comments-scraper`
  - `facebook-comments-scraper`
  - `alien_force/facebook-posts-comments-scraper`
  - Used in: `social_media_app.py` (FACEBOOK_COMMENTS_ACTOR_IDS; `fetch_post_comments`, `fetch_comments_for_posts_batch`)

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
