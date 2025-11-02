## Copilot / AI contributor quick guidance — Social Media Analytics

This file gives the key, actionable knowledge an AI coding agent needs to be productive in this repo.

### One-line summary

Streamlit-based social media analytics app that fetches posts & comments from Apify actors, normalizes data via platform adapters, performs NLP (Arabic + English), and renders dashboards in `social_media_app.py` and the `app/` package.

### Quick dev commands (what to run)

- Install deps: `pip install -r requirements.txt`
- Set Apify token: `export APIFY_TOKEN=your_apify_token_here`
- Run UI: `streamlit run social_media_app.py`
- Run tests: `pytest tests/`

### Big-picture architecture (what depends on what)

- `social_media_app.py` is the main Streamlit UI that orchestrates: adapters -> services -> NLP -> viz.
- Key directories:
  - `app/adapters/` — platform adapters (Facebook/Instagram/YouTube). Each adapter exposes `normalize_posts(...)` used by `normalize_post_data`.
  - `app/services/` — fetching/persistence services (e.g. `DataPersistenceService` in `app/services/persistence.py`).
  - `app/nlp/` — NLP helpers (sentiment, phrase_extractor, advanced_nlp).
  - `app/viz/` — visualization builders (charts, dashboards, wordcloud generator).
  - `data/raw` and `data/processed` — persisted actor outputs. Filenames use platform prefixes like `facebook_YYYYMMDD_*.json` or `.csv`.

### Important conventions & patterns (project-specific)

- Two-phase Facebook workflow: Phase 1 extracts posts (posts actor), Phase 2 extracts comments from those posts via a comments scraper. See `README.md` and functions: `fetch_apify_data`, `fetch_comments_for_posts_batch`, `fetch_post_comments` in `social_media_app.py`.
- Toggle for comment fetching: UI uses sidebar boolean `fetch_detailed_comments` and `comment_method` ("Batch Processing" vs "Individual Posts"). Code branches accordingly.
- Adapters contract: adapters must implement `normalize_posts(raw_data) -> List[Dict]` returning normalized posts with keys like `post_url`, `post_id`, `likes`/`reactions`, `comments_count`, `comments_list`.
- Persistence contract: `DataPersistenceService.save_dataset(...)` and `load_dataset(...)` are used by the UI — modify only cautiously.
- Caching: Streamlit caching decorators (`@st.cache_data`) and `functools.lru_cache` are used extensively. Clear caches (`st.cache_data.clear()`) when testing changes that affect cached data.

### External / integration points to watch

- Apify actors and token: actor IDs live in `app/config/settings.py` and are referenced directly in `social_media_app.py` (constants such as `ACTOR_CONFIG`, `FACEBOOK_COMMENTS_ACTOR_IDS`). Update actor IDs in `app/config/settings.py` when rotating actors.
- ApifyClient usage pattern: call `client.actor(<actor_id>).call(run_input=...)` then read via `client.dataset(run["defaultDatasetId"]).iterate_items()` — maintain the actor-specific `run_input` shapes.
- Optional integrations: `plotly`, `arabic_reshaper` + `bidi` are optional; code contains `try/except ImportError` fallbacks — preserve those if adding optional deps.

### Files / symbols worth referencing in edits

- Main app: `social_media_app.py`
- Actor config & regexes: `app/config/settings.py`
- Adapters: `app/adapters/facebook.py`, `app/adapters/instagram.py`, `app/adapters/youtube.py` (implement `normalize_posts`)
- Persistence: `app/services/persistence.py` (class `DataPersistenceService`)
- NLP entry points: `app/nlp/advanced_nlp.py`, `app/nlp/sentiment_analyzer.py`, `app/nlp/phrase_extractor.py`
- Viz entry points: `app/viz/wordcloud_generator.py`, `app/viz/charts.py`, `app/viz/dashboards.py`

### Typical data shapes / examples

- Normalized post (example keys):
  - `post_id`, `post_url`, `published_at`, `text`, `likes` or `reactions` (dict), `comments_count`, `shares_count`, `comments_list` (list of dicts)
- Comment item keys (see `normalize_comment_data`): `comment_id`, `text`, `author_name`, `created_time`, `likes_count`, `replies_count`.

### Quick debugging tips for agents

- Reproduce UI behavior locally: run the app and watch `st.info()`/`st.warning()` messages for actor call details and counts (they are used extensively in the UI).
- Inspect `data/processed/` after an actor run to verify normalized CSVs named `facebook_YYYYMMDD_*.csv`.
- When changing actor inputs or adapters, run a small actor call locally or mock `ApifyClient` responses to validate normalization.

If any section here is unclear or you want specific CI/credentials guidance, tell me which area to expand and I'll update this file.

### Concrete in-repo examples

- How posts are normalized: `social_media_app.py` -> `normalize_post_data(raw_data, platform)` calls `app.adapters.<Platform>Adapter.normalize_posts(raw_data)` (see `app/services/__init__.py` and `app/adapters/__init__.py`).
- Persistence: `app/services/persistence.py` defines `DataPersistenceService.save_dataset(...)` and `load_dataset(...)` used by `save_data_to_files` and `load_data_from_file` in `social_media_app.py`.
- Two-step Facebook comments: `fetch_apify_data(...)` (lines near top-level of `social_media_app.py`) then `fetch_comments_for_posts_batch(posts, apify_token, max_comments_per_post)` (search in `social_media_app.py`).
- Comment normalization example: `normalize_comment_data(raw_comment)` in `social_media_app.py` maps different actor fields (e.g., `message`, `text`, `from`) into a canonical comment dict.
