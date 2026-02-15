# Codebase Cleanup & Optimization Recommendations

This document summarizes findings from a full codebase review and suggests concrete improvements for cleaner, more maintainable, and better-performing code.

---

## 1. **Monolithic entry point (~2,780 lines)**

**Issue:** `social_media_app.py` is a single large file that mixes:

- Configuration (actor IDs, URL patterns)
- Data fetching (Apify, comments, YouTube)
- Data normalization and persistence
- NLP helpers (Arabic, keywords, sentiment)
- Chart/UI helpers (word cloud, overview charts, reaction pie)
- Platform-specific analysis (Instagram monthly, post analysis)
- Main Streamlit UI and flow

**Recommendations:**

- **Split by domain** into modules under `app/`:
  - `app/fetch/` or extend `app/services/`: move `fetch_apify_data`, `fetch_post_comments`, `fetch_comments_for_posts`, `fetch_comments_for_posts_batch`, `fetch_youtube_comments`, `assign_comments_to_posts`, `scrape_instagram_comments_batch`, `assign_instagram_comments_to_posts`, `normalize_comment_data`.
  - `app/pages/` or `app/ui/`: move platform-specific rendering (e.g. `create_instagram_monthly_analysis`, `create_instagram_monthly_insights`, `create_instagram_post_analysis`, Facebook block in the expander, YouTube block) into dedicated modules (e.g. `facebook_analysis.py`, `instagram_analysis.py`, `youtube_analysis.py`) and call them from `main()`.
  - Keep `social_media_app.py` as a thin entry point: config, routing to pages, and high-level layout only.
- **Move pure logic out of the UI file:**
  - `analyze_sentiment_placeholder`, `analyze_all_sentiments` → `app/nlp/sentiment_analyzer.py` or a small `app/nlp/fallback_sentiment.py`.
  - `clean_arabic_text`, `tokenize_arabic`, `extract_keywords_nlp` → `app/nlp/` (e.g. `arabic_processor` or a shared `text_utils`).
  - `normalize_post_data`, `filter_current_month`, `calculate_total_reactions`, `calculate_average_engagement`, `calculate_youtube_metrics` → `app/analytics/metrics.py` or `app/adapters/` where they fit.
  - `save_data_to_files`, `load_data_from_file`, `save_data_to_database`, `load_data_from_database`, `get_saved_files` → already have `app/services/persistence.py` and DB layer; consolidate there and call from the app.

---

## 2. **Duplicate configuration**

**Issue:** The same configuration is defined in two places:

- `app/config/settings.py`: `ACTOR_CONFIG`, `ACTOR_IDS`, `FACEBOOK_COMMENTS_ACTOR_IDS`, `URL_PATTERNS`, etc.
- `social_media_app.py`: local `ACTOR_CONFIG`, `ACTOR_IDS`, `FACEBOOK_COMMENTS_ACTOR_IDS`, `FACEBOOK_COMMENTS_ACTOR_ID`, `INSTAGRAM_COMMENTS_ACTOR_IDS`, `URL_PATTERNS`, and slightly different values (e.g. YouTube actor name vs ID).

**Recommendations:**

- Use a **single source of truth**: import all of these from `app.config` (e.g. `from app.config import ACTOR_CONFIG, FACEBOOK_COMMENTS_ACTOR_IDS, URL_PATTERNS`).
- Align actor identifiers in `app/config/settings.py` with what the Apify client expects (name vs ID) and document which is which. Remove duplicate definitions from `social_media_app.py`.
- Keep `URL_PATTERNS` only in config and use it in `validate_url` (e.g. in `app/data/validators.py` or next to config).

---

## 3. **Duplicate imports**

**Issue:** `create_kpi_dashboard` (and other dashboard helpers) are imported from `app.viz.dashboards` twice in `social_media_app.py` (two separate `from app.viz.dashboards import ...` blocks).

**Recommendation:** Merge into a single `from app.viz.dashboards import ...` and list every symbol once.

---

## 4. **Duplicate / shadowed chart implementation**

**Issue:** `create_sentiment_pie_chart` is both:

- Imported from `app.viz.charts`, and
- Defined again locally in `social_media_app.py` (with a slightly different legend).

So the import is shadowed and two implementations exist.

**Recommendation:** Use only the version in `app.viz.charts`. Remove the local definition from `social_media_app.py`. If the extra legend is desired, add an optional parameter (e.g. `show_legend_with_counts=True`) in `app/viz/charts.py` and use it from the app.

---

## 5. **Comment text extraction (DRY)**

**Issue:** Comment text is read in several places with `comment.get('text', '')` only. Facebook and some APIs use `message` or `content`.

**Status:** Already improved in `app/analytics/metrics.py` (`aggregate_all_comments`, `extract_comment_texts`) and `app/viz/post_details.py` to support `text` / `message` / `content`.

**Recommendation:** Anywhere else that reads comment text (e.g. `app/utils/export.py`, `app/services/persistence.py`, `app/services/comment_service.py`) should use the same pattern or a shared helper (e.g. `extract_comment_texts` or a small `get_comment_text(comment)` in `app/analytics/metrics.py`) so all platforms and formats are handled in one place.

---

## 6. **Engagement / reaction naming**

**Issue:** The app has both:

- `app.analytics.metrics`: `calculate_total_engagement(posts)` and `calculate_average_engagement(posts)` returning dicts of metrics.
- `social_media_app.py`: `calculate_total_reactions(posts)` (sum of reaction counts) and `calculate_average_engagement(posts)` (single float).

Same name “average engagement” with different signatures and return types can cause confusion.

**Recommendation:** Rename or relocate for clarity, e.g.:

- Keep in the main app (or move to `app/analytics/metrics.py`) and name explicitly: e.g. `sum_reactions(posts)` and `average_engagement_per_post(posts)`.
- Or keep the analytics module names but avoid reusing “calculate_average_engagement” in the main app; use a name that reflects “per-post engagement average” and document the difference.

---

## 7. **Exception handling**

**Issue:** There are many broad `except Exception` blocks (and some `except:`). They can hide bugs and make debugging harder.

**Recommendations:**

- Prefer catching specific exceptions (e.g. `ApifyApiError`, `ConnectionError`, `ValueError`) where known.
- In UI code, catch a broad exception only at the top level to show a user-friendly message, and log the full traceback (and optionally re-raise in development).
- Replace `except:` with `except Exception:` and add logging; avoid swallowing errors without logging.

---

## 8. **Caching and performance**

**Issue:** `fetch_apify_data` and `fetch_post_comments` use `@st.cache_data(ttl=3600, ...)`. Other heavy or repeated work (e.g. NLP, aggregation) is not cached.

**Recommendations:**

- Consider caching (e.g. `st.cache_data`) for:
  - `normalize_post_data` (keyed by platform + hash of raw data or run id).
  - `aggregate_all_comments` / comment aggregation when posts haven’t changed.
  - Expensive NLP results (e.g. sentiment, topic extraction) keyed by text or comment list hash.
- Use consistent TTL and key strategy (e.g. from `app/config/settings.py`: `CACHE_TTL`, `MAX_CACHE_ENTRIES`) to avoid stale data and unbounded growth.
- For large comment sets, consider batching or chunking sentiment/NLP so the UI stays responsive (e.g. process in chunks and show progress).

---

## 9. **Type hints and docstrings**

**Issue:** Some functions have full type hints and docstrings; others have none. Inconsistent style makes refactoring and IDE support harder.

**Recommendations:**

- Add type hints to all public functions (parameters and return types), especially in `app/` (adapters, analytics, services, viz).
- Prefer one-line docstrings for obvious functions and short “Args/Returns” for non-trivial ones.
- Use `TypedDict` or small dataclasses for recurring structures (e.g. “post”, “comment”) to document and validate shapes.

---

## 10. **Tests and dead code**

**Issue:** Tests exist for some adapters and DB persistence; the main app and many helpers are not covered. Unused or legacy code (e.g. “legacy” in names) may still be present.

**Recommendations:**

- Add tests for:
  - Sentiment and comment aggregation (e.g. `aggregate_all_comments` with `text`/`message`/`content`).
  - URL validation and config (e.g. `validate_url` with `URL_PATTERNS`).
  - Data normalization (adapters) and key metrics (e.g. `calculate_total_reactions`).
- Search for “legacy”, “deprecated”, “TODO”, “FIXME” and either remove, replace, or document and track.
- Remove or guard optional dependencies (e.g. Plotly, MongoDB) with a single place that checks availability and a clear fallback (e.g. “Plotly not installed, using static charts”).

---

## 11. **Optional dependencies**

**Issue:** Plotly and MongoDB are imported inside try/except; the app uses `PLOTLY_AVAILABLE` and `MONGODB_AVAILABLE`. Other optional deps may be scattered.

**Recommendation:** Centralize optional features in a small module (e.g. `app/optional_deps.py` or in `app/config`) that sets flags and optional imports, and use those flags everywhere so the main app and viz code stay clean and consistent.

---

## 12. **Quick wins (already applied or easy to do)**

- Merge duplicate `from app.viz.dashboards import ...` into one block.
- Remove local `create_sentiment_pie_chart` and use `app.viz.charts.create_sentiment_pie_chart` everywhere.
- Use `URL_PATTERNS` from `app.config` in `validate_url` and remove local `URL_PATTERNS` from `social_media_app.py`.
- Move `validate_url` to `app.data.validators` and call it from the app (validators already exist).

---

## Summary priority

| Priority | Area                     | Action                                              |
|----------|---------------------------|-----------------------------------------------------|
| High     | Single config source      | Use `app.config` only; remove duplicates in app.  |
| High     | One sentiment chart       | Use charts module; remove local duplicate.         |
| High     | Imports                   | Merge duplicate dashboard imports.                  |
| Medium   | Split main app            | Extract fetch, persistence, NLP, platform UI.        |
| Medium   | Comment text              | Use shared helper everywhere (text/message/content).|
| Medium   | Naming                    | Clarify engagement vs reactions; consistent names. |
| Low      | Exceptions                 | Narrow catches; add logging.                        |
| Low      | Caching                   | Add cache for normalization and heavy NLP.          |
| Low      | Types and docs            | Add hints and short docstrings.                      |
| Low      | Tests                     | Cover aggregation, validation, normalization.      |

Implementing the high-priority and selected medium-priority items will give a cleaner, more consistent, and easier-to-extend codebase without changing behavior for users.
