# 📊 Social Media Analytics Dashboard

A Streamlit application that analyzes Facebook, Instagram, and YouTube content using Apify actors. It provides KPIs, trend charts, audience insights (NLP, sentiment, word clouds), post-level analysis, PDF reports, and run comparison—with optional MongoDB persistence.

---

## Table of contents

- [Features](#-features)
- [Quick start](#-quick-start)
- [Data sources](#-data-sources)
- [Report dashboard (tabs)](#-report-dashboard-tabs)
- [Export & PDF report](#-export--pdf-report)
- [Compare runs & insights](#-compare-runs--insights)
- [Rebranding (white-label)](#-rebranding-white-label)
- [Configuration](#-configuration)
- [Facebook workflow](#-facebook-comments-workflow)
- [Supported URLs](#-supported-url-formats)
- [Project structure](#-project-structure)
- [Development](#-development)
- [Environment variables](#-environment-variables-reference)
- [Support](#-support)

---

## ✨ Features

### Platforms & data

- **Multi-platform**: Facebook, Instagram, YouTube
- **Three data sources**: Fetch from API (Apify), Load from File (saved JSON/CSV), Load from Database (MongoDB)
- **Normalized data**: Single post schema; load-from-file and DB are normalized so older saves work
- **Date range**: Data range (e.g. “Posts from 2024-01-05 to 2024-02-10”) shown at the top of the report

### Fetch & analysis

- **Fetch from API**: Live data via Apify actors (posts + optional comments)
- **Facebook**: Two-phase workflow — posts first, then comments (batch or per-post)
- **Presets**: Quick (10), Standard (25), Full (50), or Custom slider for max posts; session-persisted
- **Facebook date range**: All posts, Last 30 days, Last 7 days, or custom From/To
- **Comments**: Optional “Fetch detailed comments” for word clouds and sentiment (platform-specific actors)

### Report dashboard (tabbed)

- **Overview**: Reactions breakdown (Facebook donut + top reaction summary), Cross-platform comparison (when multiple platforms loaded), Compare with previous run (same platform, saved file)
- **Trends**: Posts per day, Top 5 posts by engagement, Engagement over time (daily total)
- **Audience**: Advanced NLP (topics, keywords, emoji sentiment), “Top themes” word cloud, **Sentiment view** (positive vs negative themes from phrases)
- **Posts**: Table with Date, Rank, Engagement, Caption, Likes, Comments, Shares (sorted by engagement); post selector; full post details (metrics, performance, comments, platform-specific blocks)
- **Export**: PDF report download, Posts CSV/JSON, Comments CSV/JSON, Summary statistics CSV

### Metrics & engagement

- **Facebook**: Total reactions (sum of reaction types, with likes fallback), comments, shares, avg engagement; platform-aware so “engagement” = reactions + comments + shares
- **Insights block**: Short alerts (e.g. “Reactions down X% vs previous 7 days”, “Last 2+ posts have no comments”, “Reactions mostly positive (Like + Love > 80%)”)
- **Posts table**: Engagement column and rank; meaningful caption and default sort by engagement

### Export & PDF

- **PDF report**: One-click download (KPIs, data range, top 5 posts). Requires `reportlab`. See [Export & PDF report](#-export--pdf-report).
- **CSV/JSON**: Posts, comments, and summary stats with timestamped filenames

### Rebranding

- **White-label**: Report title and footer configurable in `app/config/settings.py` (used in app header and PDF). See [Rebranding](#-rebranding-white-label).

### Technical

- **Arabic-capable NLP**: Phrase-based sentiment, stopwords, word clouds; optional arabic-reshaper/python-bidi
- **Optional MongoDB**: Save/load jobs; “Load from Database” when `MONGODB_URI` is set
- **Apify**: Retries, timeouts, user-friendly errors via `app/services/apify_client.py`

---

## 🚀 Quick start

### Prerequisites

- Python 3.8+
- [Apify](https://apify.com) API token (for “Fetch from API”)

### Installation

1. **Clone and enter the project**
   ```bash
   git clone https://github.com/alialzein01/social-media-analytics.git
   cd social-media-analytics
   ```

2. **Create virtual environment and install dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Set Apify token**  
   Either:
   - `export APIFY_TOKEN=your_apify_token_here`
   - Or in `.streamlit/secrets.toml`: `APIFY_TOKEN = "your_apify_token_here"`

4. **Run the app**
   ```bash
   streamlit run social_media_app.py
   ```
   Open the URL (e.g. http://localhost:8501).

### Optional: MongoDB (for “Load from Database”)

- Create `.streamlit/secrets.toml` and add:
  ```toml
  APIFY_TOKEN = "your_apify_token_here"
  MONGODB_URI = "mongodb://localhost:27017/"
  MONGODB_DATABASE = "social_media_analytics"
  ```
- Use a local MongoDB or [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) URI. If not set, the app runs without DB (Fetch from API + Load from File only).

---

## 📥 Data sources

| Source | Description |
|--------|-------------|
| **Fetch from API** | Fetches posts (and optionally comments) from Apify actors. Requires `APIFY_TOKEN`. |
| **Load from File** | Loads a previously saved run from `data/processed/` or `data/raw/` (JSON/CSV). Data is normalized on load. |
| **Load from Database** | Loads posts from MongoDB (when `MONGODB_URI` is set). Use sliders for “Days of history” and “Maximum posts to load”. |

After a fetch, you can save to MongoDB (if connected) and/or to files; then use “Load from File” or “Load from Database” to revisit or compare runs.

---

## 📊 Report dashboard (tabs)

Once data is loaded, the report is organized into **five tabs** below the KPI row and insights.

| Tab | Contents |
|-----|----------|
| **📊 Overview** | Reactions breakdown (Facebook: donut + “Top reaction” summary). Cross-platform comparison when multiple platforms are loaded. **Compare with previous run**: choose a saved file for the same platform to see Current vs Previous metrics and % change. |
| **📈 Trends** | Posts per day (line), Top 5 posts by engagement (bar), Engagement over time (daily total, line). |
| **💡 Audience** | Advanced NLP dashboard (topics, keywords, emoji sentiment). “Top themes” word cloud. **Sentiment view**: positive vs negative themes (phrase-based). If no comment text: clear CTA to enable “Fetch detailed comments” and re-run. |
| **📝 Posts** | Table: Date, Rank, Engagement, Caption, Likes, Comments, Shares (sorted by engagement). Post selector (sort/filter) and full post details (metrics, performance, comments, platform-specific section). |
| **📤 Export** | PDF report button, then Posts CSV/JSON, Comments CSV/JSON, Summary CSV. See below. |

The **data range** (e.g. “Posts from 2024-01-05 to 2024-02-10”) is shown at the top of the report when dates are available.

---

## 📄 Export & PDF report

- **Where**: **Export** tab → expand **“📥 Export Data”** → first section **“📄 Report (PDF)”**.
- **What it includes**: Report title (from config), platform, generated date, data range, KPI table (reactions/comments/shares/avg engagement for Facebook; platform-appropriate for Instagram/YouTube), top 5 posts by engagement, footer (from config).
- **Requirement**: `reportlab` is in `requirements.txt`; if it’s installed, the **“📥 Download report (PDF)”** button appears. If not, install with `pip install reportlab`.

Other exports in the same expander: **Posts CSV/JSON**, **Comments CSV/JSON**, **Summary statistics CSV** (with timestamped filenames).

---

## 📊 Compare runs & insights

- **Compare with previous run**: In the **Overview** tab, under “Compare with previous run”, select a saved file from the dropdown. The app loads that run and shows a table: **Metric | Current | Previous | Change** (Total Reactions, Total Comments, Total Shares, Avg Engagement) with % change. Use this to compare the current in-memory run with any saved run for the same platform.
- **Insights block**: Shown under the KPI row when applicable. Examples:
  - “Total reactions are down X% vs previous 7 days” (Facebook, when delta &lt; -15%).
  - “Engagement is up X% vs previous 7 days” (Facebook, when delta &gt; 20%).
  - “Last 2+ posts have no comments.”
  - “Reactions are mostly positive (Like + Love > 80%).” (Facebook.)

---

## 🏷️ Rebranding (white-label)

In **`app/config/settings.py`** you can set:

| Setting | Default | Description |
|--------|--------|-------------|
| `REPORT_TITLE` | `"Social Media Analytics Report"` | Main app header title and PDF report title. |
| `REPORT_FOOTER` | `"Generated by Social Media Analytics"` | Footer text in the PDF. |
| `REPORT_LOGO_PATH` | `""` | Reserved for a logo image path (not yet rendered in PDF). |

Change these to your product or client name for a white-label look in both the app and the PDF.

---

## 🛠️ Configuration

### Single source of truth: `app/config/settings.py`

- **Apify actors**: `ACTOR_CONFIG` (Facebook/Instagram/YouTube posts), `FACEBOOK_COMMENTS_ACTOR_IDS`, `INSTAGRAM_COMMENTS_ACTOR_IDS`, `YOUTUBE_COMMENTS_ACTOR_ID`.
- **Defaults**: `DEFAULT_MAX_POSTS`, `DEFAULT_MAX_COMMENTS`, `DEFAULT_TIMEOUT`, `CACHE_TTL`, `WORDCLOUD_*`, `DATA_RAW_DIR`, `DATA_PROCESSED_DIR`.
- **Rebranding**: `REPORT_TITLE`, `REPORT_FOOTER`, `REPORT_LOGO_PATH`.
- **NLP / URLs**: `ARABIC_STOPWORDS`, `URL_PATTERNS`, etc.

The production Apify client in **`app/services/apify_client.py`** handles retries, timeouts, and user-facing errors. See **`docs/ERROR_CATALOG.md`** for common Apify errors and messages.

### Sidebar (at runtime)

- **Preset**: Quick (10) / Standard (25) / Full (50) / Custom (slider). Session-persisted.
- **Facebook**: Date range (All, Last 30/7 days, Custom), Comment method (Batch / Individual), “Fetch detailed comments”, Max comments per post.
- **Analysis options**: Phrase-based analysis, Sentiment colors in word cloud, Simple word cloud (fallback).

---

## 🔄 Facebook Comments Workflow

1. **Phase 1 – Posts**: Fetches posts from the Facebook page using `scraper_one/facebook-posts-scraper` (page URL, results limit, optional date range).
2. **Phase 2 – Comments** (optional): If “Fetch detailed comments” is enabled, uses `apify/facebook-comments-scraper` to get comment text—either **Batch** (one run for all post URLs) or **Individual** (one run per post). Batch is faster and cheaper; use Individual if Batch fails for your page.

Then the report uses that comment text for Audience (NLP, word clouds, sentiment view). If comments are not fetched, the Audience tab shows a CTA to enable “Fetch detailed comments” and re-run.

For more detail, see [FACEBOOK_COMMENTS_WORKFLOW.md](FACEBOOK_COMMENTS_WORKFLOW.md) if present.

---

## 🔗 Supported URL formats

- **Facebook**: `https://www.facebook.com/PageName/`, `https://facebook.com/PageName`
- **Instagram**: `https://www.instagram.com/username/`
- **YouTube**: `https://www.youtube.com/@Channel`, `https://www.youtube.com/channel/...`, `https://www.youtube.com/c/...`, `https://youtube.com/watch?v=...`

---

## 📁 Project structure

```
social-media-analytics/
├── social_media_app.py          # Main Streamlit app
├── requirements.txt
├── pyproject.toml               # Ruff, pytest
├── README.md
├── .streamlit/
│   └── secrets.toml             # APIFY_TOKEN, MONGODB_URI, MONGODB_DATABASE
├── app/
│   ├── config/
│   │   └── settings.py          # Actors, defaults, REPORT_TITLE/FOOTER
│   ├── types/
│   │   ├── post_schema.py       # Normalized post schema, normalize_posts_to_schema
│   │   └── __init__.py
│   ├── adapters/                # Facebook, Instagram, YouTube normalization
│   ├── analytics/               # metrics.py (engagement, reactions, etc.)
│   ├── services/
│   │   ├── apify_client.py      # Production Apify client
│   │   ├── __init__.py          # DataFetchingService
│   │   ├── persistence.py       # Save/load files
│   │   └── mongodb_service.py   # Optional DB
│   ├── viz/
│   │   ├── charts.py            # Overview charts, engagement over time, reaction donut
│   │   ├── dashboards.py        # KPI dashboard, performance comparison
│   │   ├── nlp_viz.py           # NLP dashboard, sentiment themes view
│   │   ├── post_details.py      # Post selector, performance, comments
│   │   └── wordcloud_generator.py
│   ├── utils/
│   │   ├── export.py            # CSV/JSON/PDF export section
│   │   └── pdf_report.py        # PDF report builder (reportlab)
│   ├── nlp/                     # Sentiment, phrases, advanced_nlp
│   ├── styles/                  # Theme, loading, errors
│   ├── ui/                      # page_header, kpi_cards, section
│   └── db/                      # MongoDB repositories (optional)
├── data/
│   ├── raw/                     # Saved JSON
│   └── processed/              # Saved CSV
├── docs/
│   └── ERROR_CATALOG.md        # Apify errors and user messages
└── tests/                       # pytest
```

---

## 🔧 Development

- **Lint**: `ruff check .`
- **Format**: `ruff format .` (or `ruff format --check .` in CI)
- **Tests**: `pytest tests/ -q`
- **Run app**: `streamlit run social_media_app.py`

---

## Environment variables (reference)

| Variable | Required | Description |
|----------|----------|-------------|
| `APIFY_TOKEN` | Yes (for Fetch from API) | Apify API token. Set in env or `.streamlit/secrets.toml`. Do not expose in frontend. |
| `MONGODB_URI` | No | MongoDB connection string for “Load from Database”. |
| `MONGODB_DATABASE` | No | Database name (default: `social_media_analytics`). |
| `DATA_RAW_DIR` | No | Override raw data directory (default: `data/raw`). |
| `DATA_PROCESSED_DIR` | No | Override processed data directory (default: `data/processed`). |

For production (e.g. Streamlit Cloud, Docker), set `APIFY_TOKEN` as a secret in the host environment.

---

## 📞 Support

- Check [Issues](https://github.com/alialzein01/social-media-analytics/issues).
- Open a new issue with details.
- Contact: [@alialzein01](https://github.com/alialzein01).

---

## 📝 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Apify](https://apify.com/) for web scraping infrastructure
- [Streamlit](https://streamlit.io/) for the web framework
- [Pandas](https://pandas.pydata.org/) for data processing

---

**Made with ❤️ by [Ali Alzein](https://github.com/alialzein01)**
