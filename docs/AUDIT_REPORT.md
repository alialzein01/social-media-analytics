# Social Media App – Apify & Data Pipeline Audit Report

**Scope:** Facebook, Instagram, YouTube – actor invocation, inputs/outputs, normalization, resilience, cost, and presentation readiness.  
**Codebase:** `social_media_app.py`, `app/config/settings.py`, `app/services/apify_client.py`, `app/services/__init__.py`, `app/adapters/*`, `app/types/post_schema.py`, `app/services/persistence.py`, `app/utils/export.py`, `app/utils/pdf_report.py`, `app/services/comment_service.py`, `app/analytics/metrics.py`, `app/data/validators.py`.

---

## A) Audit Summary (10 bullets)

1. **Dual fetch paths:** Main UI uses `fetch_apify_data()` + inline `run_input` (and `ACTOR_CONFIG`); `DataFetchingService` + adapters are used in tests/scripts only. Adapter `build_actor_input` / `get_actor_id` are **not** used for the main “Fetch from API” flow, causing **actor/input drift** (e.g. Instagram adapter assumes `apify/instagram-profile-scraper` and different input than `fetch_apify_data` for `apify/instagram-scraper`).

2. **Facebook batch comments limit bug:** `_fetch_facebook_comments_batch_data()` passes `resultsLimit: max_comments_per_post` (e.g. 25) for **all** posts. Apify’s `resultsLimit` is a **total** cap, so with 10 posts you only get 25 comments total instead of 25 per post. **Fix:** set `resultsLimit = len(post_urls) * max_comments_per_post`.

3. **Comment/phase 2 calls bypass production client:** `fetch_post_comments`, `_fetch_facebook_comments_batch_data`, `scrape_instagram_comments_batch`, `fetch_youtube_comments` use `ApifyClient(...).call()` directly. They get **no retries, no shared timeout from settings, no `ApifyClientError` user messages** (only `app/services/apify_client` provides these).

4. **YouTube “Fetch detailed comments” does not attach to posts:** Comments are fetched and shown in the YouTube analytics section (word cloud, KPIs) but are **never** written into `post["comments_list"]`. Compare runs, post details, and NLP that rely on `comments_list` will show no YouTube comment text for those posts.

5. **YouTube comments call uses wrong parameter:** `fetch_youtube_comments(video_urls, apify_token, max_posts)` passes `max_posts` as the third argument; the function expects `max_comments_per_video`. So the slider “Max comments per post” (e.g. 25) is sent as comments-per-video limit, which is acceptable but semantically wrong; if UI ever showed “comments per video” it would be misleading. Passing `max_comments_per_post` from the sidebar is the correct fix.

6. **Export comments schema mismatch:** `app/utils/export.py` `create_comments_export()` uses `comment.get("author", "Unknown")`, `comment.get("likes", 0)`, `comment.get("timestamp", "")`. Normalized comments use `author_name`, `likes_count`, `created_time`. Exported CSV/JSON show “Unknown” and 0 for author/likes when data is normalized.

7. **Instagram post URL for Phase 2:** Phase 2 builds post URLs as `https://www.instagram.com/p/{short_code}/` from `post.get("post_id")`. Adapter sets `post_id` from `raw_post.get("shortCode") or raw_post.get("id")`. If the actor used in `fetch_apify_data` returns a different id (e.g. full pk) and no `shortCode`, the URL may be wrong and comment scraper may fail or match incorrectly.

8. **validate_url with empty/None:** `validate_url()` uses `URL_PATTERNS.get(platform)` and `pattern.match(url)`. If `url` is `None`, `pattern.match(None)` can raise. The UI checks `if not url` before calling `validate_url`, so in practice this is safe, but a defensive check in `validate_url` would avoid future breakage.

9. **Cost/demo risk:** No per-actor timeout overrides; comment runs use hardcoded 180s or no timeout. Batch comment runs and “Individual” Facebook comment mode (one run per post) can be expensive; cache TTL is 1 hour and cache keys include token hash, so repeated runs with same URL/params are deduped. Demo-safe defaults: use **Batch** for Facebook, low “Max comments per post” (e.g. 10–25), and “Fetch detailed comments” off for a quick run.

10. **Idempotency / partial failure:** If Phase 2 (comments) fails, the app keeps Phase 1 (posts) and shows an error; it does not corrupt state. Re-running the same URL with same params hits cache. Saving to files/DB is append-by-timestamp, so repeated runs do not overwrite silently; “Compare runs” and “Load from File” are safe. No deduplication of runs by business key, so multiple saves for the same page/date can coexist (by design).

---

## B) Platform-by-Platform Findings

### Facebook

| Area | Finding | Fix |
|------|--------|-----|
| **Posts actor** | `fetch_apify_data()` uses `ACTOR_CONFIG["Facebook"]` = `scraper_one/facebook-posts-scraper`. Input: `pageUrls: [url]`, `resultsLimit: max_posts`, optional `onlyPostsNewerThan` / `onlyPostsOlderThan`. Matches adapter’s `build_actor_input` (pageUrls, resultsLimit, date fields). | Keep; ensure `from_date`/`to_date` from sidebar are passed through (already are). |
| **Post URLs** | Adapter sets `post_url` from `url` / `postUrl` / `link` / `facebookUrl` / `pageUrl`. Phase 2 uses `post.get("post_url")`; empty list is guarded. | Ensure no post is sent to comment actor with empty URL (already filtered in `fetch_comments_for_posts_batch` and `fetch_comments_for_posts`). |
| **Comments – Batch** | `_fetch_facebook_comments_batch_data()` in `social_media_app.py` builds `startUrls` from post URLs and sets **`resultsLimit: max_comments_per_post`**. Apify’s `resultsLimit` is total comments across all URLs. | Set `resultsLimit = len(post_urls_tuple) * max_comments_per_post`. |
| **Comments – Individual** | `fetch_post_comments()` uses `maxComments` (per-post). Correct. Uses `ApifyClient` directly (no retries). | Route through `apify_client.run_actor_and_fetch_dataset` or add retry wrapper. |
| **Comment assignment** | `assign_comments_to_posts()` matches by `comment.url` / `postUrl` / `facebookUrl` to `post_url` (substring match). Normalization in `normalize_comment_data()` and adapter both produce `text`, `author_name`, etc. | OK. |
| **Edge cases** | If batch comment run fails, only that phase fails; posts remain. No fallback to individual mode in main app. | Optional: on batch failure, offer “Retry with Individual posts” or auto-fallback. |

### Instagram

| Area | Finding | Fix |
|------|--------|-----|
| **Posts actor** | Main app uses `ACTOR_CONFIG["Instagram"]` = `apify/instagram-scraper`. Input in `fetch_apify_data`: `directUrls`, `resultsType: "posts"`, `resultsLimit`, `searchLimit: 10`. Adapter in code returns `apify/instagram-profile-scraper` and `build_actor_input` uses `searchType: "hashtag"` and different shape. **Adapter is not used for fetch**; normalization is. | Either (1) Use adapter’s `get_actor_id()` and `build_actor_input()` inside `fetch_apify_data()` for Instagram, or (2) Keep current actor/input and ensure adapter’s `normalize_post()` matches **apify/instagram-scraper** output (e.g. `shortCode`, `id`, `caption`, `likesCount`, `commentsCount`, `latestComments`, `timestamp`). Prefer single source of truth: adapters. |
| **Post URL for comments** | Phase 2 builds `https://www.instagram.com/p/{short_code}/` from `post.get("post_id")`. Adapter sets `post_id` from `shortCode` or `id`. If actor returns only `id` (numeric), URL may be invalid (Instagram uses shortcode in URL). | Verify actor output has `shortCode`; if only `id`, consider resolving or documenting limitation. |
| **Comments actor** | `scrape_instagram_comments_batch()` uses `INSTAGRAM_COMMENTS_ACTOR_IDS`; per-post input: `directUrls`, `resultsLimit`, `includeNestedComments`, `isNewestComments`. Uses `ApifyClient` directly, no retries. | Use production Apify client for retries/timeouts. |
| **Comment assignment** | `assign_instagram_comments_to_posts()` matches by `comment.get("postId")` to `post.get("post_id")`. Formatted comment uses `text`, `ownerUsername`, etc. NLP uses `comment.get("text", "")` – OK. | Ensure actor returns `postId` consistent with post’s `post_id` (shortCode or id). |

### YouTube

| Area | Finding | Fix |
|------|--------|-----|
| **Posts actor** | `fetch_apify_data()` uses `ACTOR_CONFIG["YouTube"]` = `streamers/youtube-scraper`. Input: `startUrls: [{url}]` or `searchQueries`, `maxResults`, `maxResultsShorts: 0`, `maxResultStreams: 0`, subtitles. Adapter matches (startUrls, maxResults). | OK. |
| **Comments** | Phase 2 for YouTube in main app calls `fetch_youtube_comments(video_urls, apify_token, max_posts)`. Third arg is documented as `max_comments_per_video`; UI passes `max_posts`. Comments are used only in the YouTube analytics block (word cloud, KPIs); **they are never attached to `post["comments_list"]`**. | (1) Pass `max_comments_per_post` from sidebar. (2) Optionally attach fetched comments to posts by video URL and set `post["comments_list"]` so “Compare runs”, post details, and NLP see them. |
| **Comment actor** | `YOUTUBE_COMMENTS_ACTOR_ID` = `streamers/youtube-comments-scraper`. Batch input: `startUrls`, `maxComments`, `commentsSortBy`. Uses `ApifyClient` directly. | Add retries/timeout via `apify_client`. |
| **Video URL** | `video_urls = [post.get("url") for post in posts if post.get("url")]`. Adapter sets `url` from `raw_post.get("url")` or `videoUrl` or constructed. | OK. |

---

## C) Actor Invocation Table

| Actor ID | Used in (file:function) | Inputs built where | Output normalized where | Issues | Fix |
|----------|-------------------------|--------------------|--------------------------|--------|-----|
| `scraper_one/facebook-posts-scraper` | `social_media_app.py:fetch_apify_data` | `fetch_apify_data` (inline: pageUrls, resultsLimit, onlyPostsNewerThan/OlderThan) | `normalize_post_data` → `FacebookAdapter.normalize_posts` | None | Keep; ensure date range from UI is applied. |
| `apify/facebook-comments-scraper` | `social_media_app.py:fetch_post_comments`, `_fetch_facebook_comments_batch_data`; `app/services/__init__.py:ApifyService.fetch_comments`; `app/services/comment_service.py:fetch_facebook_comments_batch` | `social_media_app`: startUrls, maxComments (individual) or startUrls + **resultsLimit** (batch); `comment_service`: startUrls, resultsLimit, includeNestedComments, viewOption | `assign_comments_to_posts` + `normalize_comment_data`; `FacebookAdapter.assign_comments_to_posts` + `normalize_comment` | Batch: resultsLimit is total, not per-post. All use raw client (no retries). | Set batch `resultsLimit = len(post_urls)*max_comments_per_post`. Route comment runs through `apify_client`. |
| `apify/instagram-scraper` | `social_media_app.py:fetch_apify_data` | Inline: directUrls, resultsType, resultsLimit, searchLimit | `normalize_post_data` → `InstagramAdapter.normalize_posts` | Adapter’s `get_actor_id()` returns profile-scraper; not used for fetch. Normalization must match this actor’s output. | Unify with adapter or document output schema for this actor. |
| `apify/instagram-profile-scraper` | Referenced only in `app/adapters/instagram.py:get_actor_id()` | `InstagramAdapter.build_actor_input`: directUrls, resultsLimit, searchLimit, searchType, addParentData | Same adapter normalizes | Not used by main app fetch. | Use adapter in fetch_apify_data for Instagram, or remove profile-scraper from adapter and align to instagram-scraper. |
| `apify/instagram-comment-scraper` (and fallbacks in INSTAGRAM_COMMENTS_ACTOR_IDS) | `social_media_app.py:_fetch_one_instagram_post_comments`, `scrape_instagram_comments_batch`; `app/services/comment_service.py:scrape_instagram_comments_batch` | directUrls, resultsLimit, includeNestedComments, isNewestComments | `assign_instagram_comments_to_posts` (formatted_comment: text, ownerUsername, …) | Raw client; no retries. Main app uses concurrency (ThreadPoolExecutor). | Use apify_client; consider rate delay. |
| `streamers/youtube-scraper` | `social_media_app.py:fetch_apify_data` | Inline: startUrls or searchQueries, maxResults, maxResultsShorts, maxResultStreams, subtitles | `normalize_post_data` → `YouTubeAdapter.normalize_posts` | None | OK. |
| `streamers/youtube-comments-scraper` | `social_media_app.py:fetch_youtube_comments` | startUrls, maxComments, commentsSortBy | Not attached to posts; used only in YouTube analytics section (word cloud, KPIs). Raw keys: comment, author, voteCount | Comments not in post schema; third arg passed as max_posts. | Pass max_comments_per_post; optionally attach comments to posts. |

---

## D) Top 10 Fixes (Prioritized)

### 1. Facebook batch comments: set total resultsLimit (cost + correctness)

**Why it matters:** With multiple posts, batch mode currently requests only `max_comments_per_post` total comments instead of per post, underusing the feature and confusing users.

**Where:** `social_media_app.py`, function `_fetch_facebook_comments_batch_data`.

**Change:**

```diff
     post_urls = [{"url": u} for u in post_urls_tuple]
     comments_input = {
         "startUrls": post_urls,
-        "resultsLimit": max_comments_per_post,
+        "resultsLimit": len(post_urls_tuple) * max_comments_per_post,
         "includeNestedComments": False,
         "viewOption": "RANKED_UNFILTERED",
     }
```

---

### 2. Use production Apify client for all comment runs (reliability)

**Why it matters:** Comment runs have no retries or user-friendly errors; 429/5xx/timeouts surface as raw exceptions.

**Where:** `social_media_app.py`: `fetch_post_comments`, `_fetch_facebook_comments_batch_data`, `scrape_instagram_comments_batch`, `fetch_youtube_comments`. Replace `ApifyClient( token ).actor(id).call(...)` with `run_actor_and_fetch_dataset( create_apify_client(token), actor_id, run_input, timeout_secs=... )` and handle `ApifyClientError` (user_message).

**Patch-style:** In each function, create client with `create_apify_client(_apify_token)`, then call `run_actor_and_fetch_dataset(client, actor_id, run_input, timeout_secs=180, max_items=<cap>)`, get `(run, items)`; on `ApifyClientError` show `e.user_message`. Remove direct `client.actor(...).call` and `client.dataset(...).iterate_items()`.

---

### 3. Export comments: use normalized comment keys (presentation)

**Why it matters:** Exported comment CSV/JSON show “Unknown” and 0 for author/likes when data is normalized (author_name, likes_count, created_time).

**Where:** `app/utils/export.py`, `create_comments_export()`.

**Change:**

```diff
                     comment_data = {
                         "post_id": post_id,
                         "comment_text": comment.get("text", ""),
-                        "comment_author": comment.get("author", "Unknown"),
-                        "comment_likes": comment.get("likes", 0),
-                        "comment_timestamp": comment.get("timestamp", ""),
+                        "comment_author": comment.get("author_name") or comment.get("author", "Unknown"),
+                        "comment_likes": comment.get("likes_count", comment.get("likes", 0)),
+                        "comment_timestamp": comment.get("created_time") or comment.get("timestamp", ""),
                     }
```

---

### 4. YouTube Phase 2: pass max_comments_per_post and optionally attach comments to posts

**Why it matters:** Correct semantics and consistent behavior with FB/IG (comments in `comments_list` for NLP and compare).

**Where:** `social_media_app.py`: call site `fetch_youtube_comments(video_urls, apify_token, max_posts)` and, if desired, logic after fetch to attach comments to posts by video URL.

**Change (call site):**

```diff
-                        all_comments = fetch_youtube_comments(video_urls, apify_token, max_posts)
+                        all_comments = fetch_youtube_comments(video_urls, apify_token, max_comments_per_post)
```

Optional: normalize each comment with `YouTubeAdapter.normalize_comment`, group by video URL, set `post["comments_list"]` and update `post["comments_count"]` so downstream tabs and “Compare runs” see YouTube comments.

---

### 5. Unify Instagram fetch with adapter (single source of truth)

**Why it matters:** One place for actor ID and input schema; avoids drift between ACTOR_CONFIG, inline input, and adapter.

**Where:** `social_media_app.py:fetch_apify_data`; use `InstagramAdapter(apify_token).get_actor_id()` and `build_actor_input(url, max_posts, from_date, to_date)` for Instagram instead of inline dict. Use same pattern for Facebook/YouTube so all platforms go through adapters.

**Patch-style:** For each platform, get adapter from a small helper (e.g. `get_adapter(platform, token)`), then `actor_id = adapter.get_actor_id()`, `run_input = adapter.build_actor_input(url=url, max_posts=max_posts, from_date=from_date, to_date=to_date)`. Remove platform-specific inline `run_input` blocks. Keep `ACTOR_CONFIG` or move to adapter-only.

---

### 6. Defensive URL validation

**Why it matters:** Avoids AttributeError if `validate_url` is ever called with `None` or non-string.

**Where:** `social_media_app.py`, function `validate_url`.

**Change:**

```diff
 def validate_url(url: str, platform: str) -> bool:
     """Tighten platform URL validation with pre-compiled regex patterns."""
+    if not url or not isinstance(url, str):
+        return False
     pattern = URL_PATTERNS.get(platform)
-    return bool(pattern.match(url)) if pattern else False
+    return bool(pattern and pattern.match(url))
```

---

### 7. PDF report: guard missing/None metrics

**Why it matters:** Avoid crashes or wrong numbers if a post has missing `views` or `likes` (e.g. YouTube) or malformed data.

**Where:** `app/utils/pdf_report.py`, `_kpi_row` and top-posts loop.

**Change:** Use `(p.get("views") or 0)`, `(p.get("likes") or 0)` etc., and skip or cap top-posts list if `get_post_engagement` or text access can raise. Already mostly safe; add one guard for `len(posts)` and for `get_post_engagement(p, platform)` returning non-numeric.

---

### 8. Facebook comment_service batch input alignment

**Why it matters:** `comment_service.fetch_facebook_comments_batch` uses `resultsLimit: max_comments_per_post` for the whole batch; same bug as main app batch.

**Where:** `app/services/comment_service.py`, `fetch_facebook_comments_batch`, input dict.

**Change:**

```diff
-        comments_input = {
+        comments_input = {
             "startUrls": post_urls,
-            "resultsLimit": max_comments_per_post,
+            "resultsLimit": len(post_urls) * max_comments_per_post,
             "includeNestedComments": False,
             "viewOption": "RANKED_UNFILTERED",
         }
```

(Note: `post_urls` here is list of dicts `[{"url": post_url}, ...]`, so total count is `len(post_urls)`.)

---

### 9. Ensure token never logged (security)

**Why it matters:** Accidental logging of APIFY_TOKEN would leak secrets.

**Where:** Grep for `logger.*token`, `print.*token`, `st.write.*token`, and any place token is interpolated into messages. `app/services/apify_client.py` does not log token. `scripts/test_facebook.py` prints token length – avoid in production paths; if kept for scripts, restrict to script and do not log token value.

**Action:** Confirm no `st.write(apify_token)`, no `logger.info("token=%s", token)`; if test script prints length, add comment that it must not run in production or print actual token.

---

### 10. Demo-safe defaults and messaging

**Why it matters:** Prevents runaway cost and slow runs during demo.

**Where:** `app/config/settings.py` (DEFAULT_MAX_POSTS, DEFAULT_MAX_COMMENTS); sidebar defaults in `social_media_app.py`.

**Change:** Ensure defaults are demo-safe (e.g. DEFAULT_MAX_POSTS=10, DEFAULT_MAX_COMMENTS=25). In sidebar, for “Fetch detailed comments”, consider default False for YouTube/Instagram or show estimated cost (e.g. “~$2.30 per 1,000 comments”). Add one-line copy: “For a quick demo: leave ‘Fetch detailed comments’ unchecked or use Batch + low comment limit.”

---

## E) Demo Checklist for Tomorrow

- **Settings**
  - **Facebook:** URL = one page; Posts to fetch = 10; Date range = “Last 7 Days”; Comments = “Batch Processing”, “Fetch detailed comments” optional (uncheck for fastest run); Max comments per post = 10–25.
  - **Instagram:** URL = one profile; Posts = 10; “Fetch detailed comments” optional (uncheck for speed).
  - **YouTube:** URL = one channel; Posts = 10; “Fetch detailed comments” optional (uncheck for speed).

- **Dry-run flow**
  1. Set `APIFY_TOKEN` in env or `.streamlit/secrets.toml` (do not show token in UI).
  2. Open app → choose platform → “Fetch from API” → enter URL.
  3. Leave “Fetch detailed comments” unchecked for first run → Analyze.
  4. Confirm posts load and KPIs render; then try “Load from File” for same platform.
  5. Enable “Fetch detailed comments” (Batch for Facebook, low max comments) and run again; confirm comments appear in word cloud / post details.
  6. Export → download CSV/JSON and PDF; confirm no token or run URLs in exports.
  7. “Compare with previous run” → select a saved file; confirm deltas and no errors.

- **Quick win:** For a single “no comments” run, use Facebook or YouTube with “Fetch detailed comments” unchecked so only one actor run (posts) is used.

---

*End of audit report. All file paths and function names refer to the repository as of the audit date.*
