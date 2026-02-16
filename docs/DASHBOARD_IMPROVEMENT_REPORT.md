# Dashboard Improvement Report

## Dashboard Audit Summary

- **Removed:** (1) Total Engagement Breakdown chart from Analytics section — same information is already in Overview KPI row (Reactions, Comments, Shares). (2) Duplicate Monthly Insights block for Instagram — Advanced NLP, word cloud, and sentiment already appear in Monthly Overview; replaced with a single pointer. (3) Per-reaction metric row in Reaction Breakdown — kept one bar chart only for clarity.
- **Replaced:** None (chart types were appropriate: line for time, bar for comparison/distribution).
- **Kept:** Posts per day, Top 5 posts by engagement, Cross-platform comparison, Posts table, Export, Post Details drill-down, sentiment pie, word cloud (once per context), all KPI cards, reaction bar chart, posting frequency, content type, hashtags, insights summary.
- **Reasoning:** Reduce redundancy so each visualization answers one clear question; avoid showing the same breakdown twice (KPIs vs bar); consolidate Instagram comment insights in one place (Overview) so Monthly Insights doesn’t repeat them.

---

## Phase 1 — Visualization Audit (Insight Quality)

### Inventory (all charts, tables, KPIs)

| Location | Item | Type | Question answered |
|----------|------|------|--------------------|
| Monthly Overview (FB) | 4 KPI cards | KPI | Totals & avg engagement |
| Monthly Overview (FB) | Reaction breakdown | Bar + metrics | How do reaction types break down? |
| Monthly Overview (IG) | KPI dashboard | 8 cards | Totals, averages, best post |
| Monthly Overview (IG) | Engagement trend | Line | Engagement by day? |
| Monthly Overview (IG) | Posting frequency | 2 bars | When do we post? |
| Monthly Overview (IG) | Top 5 posts | Bar | Best performers? |
| Monthly Overview (IG) | Content type | Pie | Content mix? |
| Monthly Overview (IG) | Hashtag | Bar | Top hashtags? |
| Monthly Overview (IG) | Insights summary | Text | Key takeaways |
| Monthly Overview (IG) | Advanced NLP + word cloud + sentiment | Mixed | Comment insights (drivers) |
| Monthly Insights | Advanced NLP / word cloud / sentiment | (same) | Duplicate for IG → removed |
| Monthly Insights | Sentiment comparison | Metrics + bar | Text vs emoji vs combined |
| Cross-Platform | Table + 3 charts | Table + bars | How do platforms compare? |
| Analytics expander | Posts per day | Line | Posting over time |
| Analytics expander | ~~Engagement breakdown~~ | ~~Bar~~ | **Removed** (same as Overview KPIs) |
| Analytics expander | Top 5 posts | Bar | Top performers |
| Posts Details | Dataframe | Table | List of posts |
| Post Details (drill) | Metrics + performance + comment analytics | KPI + charts | Single-post story |

### Evaluation (purpose, signal vs noise, chart-type fit)

- **Engagement Breakdown (bar) in Analytics:** Redundant with Overview KPIs (Reactions, Comments, Shares). Removed.
- **Monthly Insights for Instagram:** Full NLP + word cloud + sentiment duplicate Overview content. Replaced with one line: comment insights are in Monthly Overview above.
- **Reaction breakdown:** Metrics row + bar both show the same breakdown. Kept bar only; removed per-reaction metric row to reduce clutter.
- **Posts per day / Top 5 posts:** Good for trends and drivers; kept. Chart types (line, horizontal bar) fit.
- **Cross-platform:** Table + bars answer “how do platforms compare”; kept.

---

## Phase 2 — KPI & Insight Structure

- **KPIs:** Kept high-signal set (totals, averages, engagement). No deltas (no prior-period data in scope).
- **Formatting:** Thousands separators and consistent value formatting retained.
- **Colors:** KPI color keys (reactions, comments, shares, engagement) aligned with theme; chart colors unchanged.

---

## Phase 3 — UI / Visual Quality

- **Chart height:** Standardized Plotly chart height to 340px where missing for consistent layout.
- **Reaction section:** Single bar chart only (no duplicate metric row).
- **Section order:** Unchanged — Overview → Insights → Cross-Platform → Analytics → Table → Export → Post Details.
- **Spacing:** Existing dividers and section structure kept.

---

## Files Modified

- `app/viz/charts.py`: create_monthly_overview_charts — removed Engagement Breakdown; standardized height. create_reaction_pie_chart — bar chart only (no per-reaction metric row).
- `social_media_app.py`: Local create_monthly_overview_charts — same removals. Monthly Insights — when platform is Instagram, show pointer to Overview instead of duplicating NLP/word cloud/sentiment.
- `app/viz/dashboards.py`: create_engagement_trend_chart, create_posting_frequency_chart — add height=340 to Plotly layouts where applicable.
