# Phase 0 — Quick Audit

## 1. Framework Stack

| Layer | Technology |
|-------|------------|
| **Frontend / Backend** | Single app: **Streamlit** (Python). No separate React/Node frontend. |
| **Build** | `pip` + `requirements.txt`; no webpack/vite. |
| **Routing** | Streamlit sidebar + session state (no URL routes). |
| **State** | `st.session_state`, `@st.cache_data`, `@st.cache_resource`. |
| **Styling** | Custom CSS via `app/styles/theme.py` (`get_custom_css`), `app/styles/loading.py`, `app/styles/errors.py`. Streamlit components. |
| **API layer** | Direct `ApifyClient` usage in `social_media_app.py` and in `app/services/` (ApifyService, CommentFetchingService). No REST API; token and all logic run in the Streamlit server process. |

---

## 2. Apify Usage

| Item | Location / behavior |
|------|----------------------|
| **Token** | Read from `st.secrets['APIFY_TOKEN']` or `os.environ.get('APIFY_TOKEN')` in `social_media_app.py` (e.g. `get_api_token()`, `normalize_post_data()`). Never sent to browser; Streamlit secrets are server-side. |
| **Calls** | • `fetch_apify_data()` — main post fetch (actor `.call()`, then `dataset().iterate_items()`).<br>• `fetch_post_comments()` — single Facebook post comments.<br>• `_fetch_facebook_comments_batch_data()` — batch Facebook comments.<br>• `fetch_youtube_comments()` — YouTube comments (batch or per-video).<br>• `fetch_comments_for_posts_batch()` / `fetch_comments_for_posts()` — orchestration + cache.<br>• `app/services/comment_service.py`: `CommentFetchingService` — Instagram/Facebook/YouTube comments (own `ApifyClient`).<br>• `app/services/__init__.py`: `ApifyService` / `DataFetchingService` — alternate path (not used by main fetch flow). |
| **Webhooks** | None. All runs are synchronous (`.call()` then iterate dataset). |
| **Actor runs** | Via `client.actor(actor_id).call(run_input=...)`; no explicit `runActor` → `getRunStatus` → `getDatasetItems` flow; no async run + poll. |
| **Dataset items** | Fetched with `client.dataset(run["defaultDatasetId"]).iterate_items()`; no pagination (iterate until limit). |

---

## 3. Top 10 Issues

1. **Duplicate / conflicting config**  
   Actor IDs and names defined in both `social_media_app.py` (e.g. `ACTOR_CONFIG`, `YOUTUBE_COMMENTS_ACTOR_ID = "streamers/youtube-comments-scraper"`) and `app/config/settings.py` (e.g. `YouTube: "h7sDV53CddomktSi5"`, `YOUTUBE_COMMENTS_ACTOR_ID = "p7UMdpQnjKmmpR21D"`). Main app uses local constants; `comment_service` uses `app.config.settings`. Risk of different actors/IDs for same platform.

2. **Apify logic duplicated and unused service**  
   Main flow uses inline `fetch_apify_data`, `fetch_post_comments`, etc. in `social_media_app.py`. `app/services/__init__.py` defines `ApifyService` and `DataFetchingService` but the main “Fetch from API” flow does not use them. Two parallel implementations.

3. **No retries or backoff**  
   All Apify calls use a single attempt. Transient failures (rate limits, timeouts) cause immediate user-visible errors with no retry.

4. **No central timeout / abort**  
   No `timeout_secs` or AbortController-style limits on many paths. Long-running runs can hang the app.

5. **Unsafe token handling in code paths**  
   Token is correctly server-side (env/secrets), but it is passed through many function signatures and cached (e.g. cache keys include token). Prefer reading token once from env in a single place and not passing it through cache keys.

6. **Magic strings**  
   Actor IDs, platform names, and error messages are string literals in multiple files. No shared constants/enums for run status, actor names, or user-facing error catalog.

7. **Monolithic entrypoint**  
   `social_media_app.py` is 2600+ lines: config, NLP helpers, normalization, Apify fetch, UI, and session logic in one file. Hard to test and refactor.

8. **Inconsistent error handling**  
   Mix of `st.error`, `st.warning`, generic `Exception`, and no structured logging. No user-friendly mapping from Apify errors (e.g. rate limit, invalid token) to messages.

9. **No validation layer**  
   No Pydantic/zod-style validation for actor inputs, run responses, or dataset items. Invalid or changed API shapes can cause runtime errors.

10. **UI inconsistencies**  
    Mix of emoji and plain text in messages; no shared “Run Actor” / “Runs” / “Results” patterns; loading and empty states implemented ad hoc in different places.

---

## 4. Notes for Phases 1–4

- **Stack is Python/Streamlit only.** “Server endpoints” (e.g. `POST /api/apify/run`) can be implemented later as a separate FastAPI/Flask app; for this pass we implement a **production-ready Apify service layer** in Python and have Streamlit call it. Token remains in server env only.
- **Single source of truth for config:** All actor IDs and app constants should live in `app/config/settings.py`; `social_media_app.py` should import from `app.config` and remove its duplicate definitions.
- **Apify service:** Add `app/services/apify_client.py` (or equivalent) with `run_actor`, `get_run_status`, `get_dataset_items`, retry with exponential backoff + jitter, timeouts, and typed/validated responses. Refactor existing fetch functions to use it.
- **Tests:** Add tests for the new Apify client (retry/backoff, validation), and keep/extend existing pytest suite for adapters and persistence.
