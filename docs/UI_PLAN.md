# UI Redesign Plan — Best-in-Class Analytics SaaS

**Summary (for PR/commit):** Redesign focuses on a cleaner, premium analytics layout without changing core functionality. Introduced a small `app/ui` module (`page_header`, `kpi_cards`, `section`, `section_divider`, empty/error/loading states), aligned `.streamlit/config.toml` with the design system, and refactored the main app to use consistent KPI cards and hierarchy. Gradient KPI blocks were replaced with light bordered cards; section nav and data range use captions. All data logic and metrics are unchanged.

---

## A) Current State (Scan)

### Entrypoint & page structure
- **Single entrypoint**: `social_media_app.py` (one Streamlit app, no multi-page).
- **Conceptual sections** (one long scroll):
  1. **Sidebar**: Platform, Data source, Fetch settings, Comments, Analysis options, Load file/DB.
  2. **Main**: App title → URL input (or “Loaded from File/DB”) → TOC buttons (Overview, Trends, Insights, Post Details) → after fetch: data range radio → **Monthly Overview** (expander) → **Monthly Insights** → **Cross-Platform Comparison** (expander) → **Analytics** (expander) → **Posts Details** table → Export → **Post Details** (selected post drill-down).

### Layout patterns
- Sidebar: `st.sidebar.radio`, `st.sidebar.expander`, `st.sidebar.slider`/`date_input`.
- Main: `st.columns(4)` for metrics in many places; `st.expander` for sections; custom HTML for gradient KPI cards; mix of `st.metric` and `st.markdown`(gradient divs).
- Theme: `get_custom_css(theme)` injected once; CSS vars in `app/styles/theme.py`.

### Repeated UI worth componentizing
- **KPI rows**: 4-col metric blocks (Facebook reactions/comments/shares/avg engagement; YouTube views/likes/comments; save result metrics; post-detail metrics).
- **Section pattern**: Title + expander + content (e.g. Monthly Overview, Analytics, Cross-Platform).
- **Empty / loading / error**: `show_empty_state`, `show_loading_dots`, `show_progress_bar`, `ErrorHandler`, `show_warning` from `app.styles.loading` and `app.styles.errors`.

### Charts & tables
- **Charts**: `app.viz.charts` (Plotly/Matplotlib), `app.viz.dashboards`; colors from `app.styles.theme` (THEME_COLORS, SENTIMENT_COLORS, GRADIENT_STYLES).
- **Tables**: `st.dataframe(display_df)` for posts list; no shared formatting for numbers/alignment.

---

## B) New UI Blueprint

### Navigation model
- **Keep**: Single scroll + sidebar (no multi-page). Sidebar = filters + data source + settings.
- **Add**: Clear “page” mental model via a **sticky section nav** (or compact TOC) so users know where they are (Overview → Trends → Drivers → Details).

### Dashboard layout grid (12-col mental model)
- **Top**: Global bar = platform + data source label + primary action (Analyze / Load).
- **Row 1**: **KPI cards** (4 cards, equal width; same style everywhere).
- **Row 2+**: **Sections** in order: Overview (summary + period) → Trends (charts) → Drivers (reactions, sentiment, word cloud) → Details (table, export, post drill-down).
- Use `st.columns([3,3,3,3])` for 4 KPIs; `st.columns([8,4])` or `st.columns([6,6])` for charts vs sidebar insights where it helps.

### KPI row design
- **Unified KPI card**: One reusable component: label, value, optional delta, optional help. No inline gradient HTML in the main script; card style from design system (subtle border, padding, optional icon).
- **Consistent mapping**: Same metric = same color (e.g. reactions = purple, comments = blue, shares = teal, engagement = green).

### Filters placement
- **Global**: Platform + Data source + (when “Fetch”) URL + Analyze in sidebar + top of main.
- **Per-section**: “Data range” (Show All / Current Month) stays near the top of results; Analysis options (phrase analysis, sentiment colors) stay in sidebar.

### Drill-down
- **Sections**: Expanders for “Monthly Overview”, “Analytics”, “Cross-Platform” (keep current behavior).
- **Post detail**: Keep “Post Details” as a section at bottom with selector + metrics + comment analytics; no modal (Streamlit 1.33+ `st.dialog` could be used later for a “quick view” if we add it without breaking flow).

### Loading / empty / error
- **Loading**: Use existing `show_loading_dots` / `show_progress_bar`; add `show_skeleton_loader` for chart areas when applicable.
- **Empty**: Reusable `empty_state(icon, title, message, action_label, action_key)`.
- **Error**: Keep `ErrorHandler` and `show_warning`; present in a consistent “alert” strip so it’s visible but not cluttered.

### Design system (spacing, typography, colors, icons)
- **Spacing**: 8px base; 16px between sections; 24px before major blocks (KPI row, first chart).
- **Typography**: Rely on Streamlit + `config.toml` font; avoid random `<h1>`/`<h3>` in HTML; use `st.markdown("## ...")` for section titles.
- **Colors**: Align `config.toml` with `THEME_COLORS` (primary, background, secondary background); keep sentiment and metric colors from theme.py.
- **Icons**: Single style (emoji) for section headers; optional short labels (e.g. “Overview”, “Trends”) for clarity.

---

## ASCII wireframe

```
+------------------------------------------------------------------+
|  [Sidebar]  |  App title (compact)                               |
|  Platform   |  Platform • Data source   [Analyze]                 |
|  Data src   +----------------------------------------------------+
|  Fetch set  |  KPI 1    KPI 2    KPI 3    KPI 4                  |
|  Comments   |  (cards: same height, same style)                   |
|  Analysis   +----------------------------------------------------+
|  Load file  |  ## Overview                                        |
|             |  Period: ...  |  [Expandable content]              |
|             +----------------------------------------------------+
|             |  ## Monthly Insights                                |
|             |  [Word cloud | Sentiment]  or platform-specific     |
|             +----------------------------------------------------+
|             |  ## Trends / Analytics                              |
|             |  [Charts in expander]                               |
|             +----------------------------------------------------+
|             |  ## Posts Details                                   |
|             |  [Table]  [Export]                                  |
|             +----------------------------------------------------+
|             |  ## Post detail (selected)                          |
|             |  [Metrics] [Comment analytics]                     |
+------------------------------------------------------------------+
```

---

## C–E) Implementation summary

1. **app/ui** module: `page_header`, `kpi_cards`, `section`, `empty_state`, `error_state`, `loading_state` (wrappers that call existing loading/error helpers where appropriate).
2. **.streamlit/config.toml**: Premium light theme (primary, background, font); baseUiTheme = light.
3. **Minimal CSS**: Only for spacing Streamlit doesn’t provide (e.g. section gaps, KPI card padding) in theme or a small override.
4. **Refactor main app**: Replace ad-hoc gradient divs with `ui.kpi_cards`; use `ui.section` for expander sections; use `ui.page_header` at top; keep data logic unchanged.
5. **Charts/tables**: Use THEME_COLORS/SENTIMENT_COLORS consistently; right-align numbers in tables; add one-line captions where helpful.
6. **Polish**: Tooltips on KPIs; sane defaults; skeleton for slow ops; responsive columns (e.g. 2 cols on small if we detect or use Streamlit’s default behavior).

---

## Before/after checklist

- [x] **Visual hierarchy**: Clear order (page header → KPIs → Overview → Insights → Trends → Details). Compact app title; section dividers and captions.
- [x] **Consistency**: Single KPI card style via `app.ui.kpi_cards`; same color key per metric (reactions, comments, shares, engagement); `.streamlit/config.toml` aligned with theme.
- [x] **Reduced clutter**: Gradient divs replaced with light bordered KPI cards; TOC uses caption "Jump to section"; data range uses caption + collapsed label.
- [x] **Empty/loading/error**: Existing `show_empty_state`, `ErrorHandler`, `show_warning` unchanged; `app.ui` re-exports and adds `error_state`, `loading_state` for future use.
- [x] **Mobile**: Streamlit-native columns; no fixed px widths in new components; single-column friendly.

---

## What changed (implementation summary)

- **app/ui/**: New module with `page_header`, `kpi_cards`, `section`, `section_divider`, `empty_state`, `error_state`, `loading_state`, `KPI_COLORS`. Re-exports from `app.styles.loading` and `app.styles.errors`.
- **.streamlit/config.toml**: Theme set to primary `#6366f1`, background `#ffffff`, secondary background `#f8fafc`, text `#0f172a`.
- **app/styles/theme.py**: Added `.ui-page-header`, `.ui-kpi-card`, `.ui-section-gap` for consistency.
- **social_media_app.py**: Replaced centered app title with `page_header(...)`; replaced Facebook/YouTube/save-result metric blocks with `kpi_cards(...)`; added `section_divider()` before results; TOC and data range use captions and stable keys; Posts Details table has caption. No data or metric logic changed.
