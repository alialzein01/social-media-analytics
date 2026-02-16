# Cleanup & Apify Integration — Deliverables

## 1) Summary of refactors and why

| Refactor | Why |
|----------|-----|
| **Single source of truth for config** | Actor IDs and constants were duplicated in `social_media_app.py` and `app/config/settings.py`, with conflicting values (e.g. YouTube actor). All now live in `app/config/settings.py`; main app imports from there. |
| **Production Apify client** | New `app/services/apify_client.py`: retry with exponential backoff + jitter, timeouts, run/dataset validation, and user-friendly error messages. Main fetch flow uses it so transient failures (rate limits, 5xx) are retried and users see clear messages. |
| **Removed duplicate code** | Deleted ~80 lines of duplicate ACTOR_CONFIG, Arabic/NLP constants, and URL patterns from `social_media_app.py`. |
| **Project layout** | Added `app/lib`, `app/types`, `docs/` (error catalog). Standardized on `app/config` for all app/actor settings. |
| **Lint/format** | Added `pyproject.toml` with Ruff (lint + format). CI runs Ruff on `app/config`, `app/services/apify_client.py`, `app/lib`, `app/types`, `docs`. |
| **UI copy** | Clearer helper text in sidebar (Fetch settings, Comments): cost/speed tradeoffs, recommended Batch method. Design-system note in `app/styles/theme.py`. |

---

## 2) New and changed files

**New**

- `app/services/apify_client.py` — Production Apify client (create_apify_client, run_actor, get_run_status, get_dataset_items, run_actor_and_fetch_dataset; retry; ApifyClientError, ApifyRunError, ApifyAuthError).
- `app/lib/__init__.py` — Placeholder for shared utils.
- `app/types/__init__.py` — JSONDict, JSONList type aliases.
- `docs/ERROR_CATALOG.md` — Apify error catalog (auth, rate limit, timeout, server errors) and env vars.
- `tests/test_apify_client.py` — Tests for client (auth, user messages, retry, backoff, run validation).
- `AUDIT_PHASE0.md` — Phase 0 audit (stack, Apify usage, top 10 issues).
- `DELIVERABLES.md` — This file.
- `pyproject.toml` — Ruff and pytest config.

**Changed**

- `app/config/settings.py` — Unified ACTOR_CONFIG and YOUTUBE_COMMENTS_ACTOR_ID (canonical actor names); removed duplicate set entries for Ruff.
- `app/config/__init__.py` — No change to exports (already had TOKEN_RE, ARABIC_DIACRITICS, etc.).
- `social_media_app.py` — Removed duplicate config block; imports from `app.config.settings`; `fetch_apify_data` uses `create_apify_client` and `run_actor_and_fetch_dataset`; catches `ApifyClientError` for user_message; DEFAULT_TIMEOUT import; improved sidebar help text.
- `app/services/__init__.py` — Re-exports from `apify_client` (create_apify_client, run_actor, get_run_status, get_dataset_items, run_actor_and_fetch_dataset, errors).
- `app/styles/theme.py` — Short design-system docstring.
- `README.md` — Env vars table, deployment note, config section points to settings + error catalog, project structure and Development (ruff, pytest).
- `.github/workflows/ci.yml` — Install pytest + ruff; lint step (Ruff on new/changed paths); format check on same paths.

---

## 3) How to run and required env vars

**Run locally**

```bash
pip install -r requirements.txt
export APIFY_TOKEN=your_token   # or set in .streamlit/secrets.toml
streamlit run social_media_app.py
```

**Env vars**

- **APIFY_TOKEN** (required for “Fetch from API”): Apify API token. Prefer env or `.streamlit/secrets.toml`; never expose in frontend.
- **MONGODB_URI**, **MONGODB_DATABASE** (optional): For “Load from Database”.
- **DATA_RAW_DIR**, **DATA_PROCESSED_DIR** (optional): Override data paths.

See README “Environment variables (reference)” and `docs/ERROR_CATALOG.md`.

---

## 4) Performance and reliability improvements

| Improvement | Effect |
|-------------|--------|
| **Retries (exponential backoff + jitter)** | Transient 429/5xx/connection errors are retried up to 4 times instead of failing immediately. |
| **Timeout** | Actor runs use `DEFAULT_TIMEOUT` (300s) so runaway runs don’t hang the app. |
| **Single config** | One actor name per platform; no divergent YouTube/Instagram IDs between main app and comment_service. |
| **Caching unchanged** | `fetch_apify_data`, `_fetch_facebook_comments_batch_data`, `fetch_post_comments`, `fetch_youtube_comments` remain cached (e.g. 1h) to avoid duplicate Apify runs. |
| **User-facing errors** | ApifyClientError.user_message and ERROR_CATALOG give clear guidance (token, rate limit, timeout) instead of raw API text. |

No new caching (e.g. Redis) was added; Streamlit’s `@st.cache_data` remains the cache. Poll-with-backoff for async runs was not implemented (current flow is synchronous `.call()`); it can be added later if you switch to async runs + webhooks.

---

## 5) Follow-up suggestions

1. **Migrate remaining Apify calls** — Use `create_apify_client` and `run_actor` / `run_actor_and_fetch_dataset` in `fetch_post_comments`, `_fetch_facebook_comments_batch_data`, `fetch_youtube_comments`, and `app/services/comment_service.py` so all paths get retries and consistent errors.
2. **Extend Ruff** — Gradually fix and enable Ruff across the rest of the repo (e.g. `social_media_app.py`) and run `ruff format .` project-wide.
3. **Optional REST API** — If you need a separate API (e.g. for a non-Streamlit frontend), add a small FastAPI app that reads `APIFY_TOKEN` from env and exposes POST `/api/apify/run`, GET `/api/apify/run/:id`, GET `/api/apify/dataset/:id/items` using the same `apify_client` layer.
4. **Webhooks** — For long-running actors, add POST `/api/apify/webhook` with `APIFY_WEBHOOK_SECRET` verification and update run status in cache/DB.
5. **Pydantic** — Validate actor inputs and run/dataset responses in `apify_client` or adapters with Pydantic models to fail fast on schema changes.
