# Cost & Speed Optimization Guide

This document summarizes where the app spends **money** (Apify usage) and **time**, and how to reduce both.

---

## 1. Cost (Apify)

Apify bills by actor run time and memory. Fewer runs and smaller inputs = lower cost.

### What counts as a “run”

| Action | Runs | Cached? |
|--------|------|---------|
| Fetch posts (FB / IG / YouTube) | 1 per platform + URL + params | ✅ 1 hour |
| Facebook comments – **Batch** | **1** for all posts | ❌ No (add below) |
| Facebook comments – Individual | **N** (one per post) | ✅ 1 hour per post URL |
| Instagram comments | **N** (one per post, 3 concurrent) | ❌ No |
| YouTube comments | 1 batched, or N if fallback | ✅ 1 hour |

### Recommendations

1. **Prefer Batch for Facebook**  
   The UI already defaults to “Batch Processing”. One batch run is **one Apify run** for all posts; “Individual Posts” is **one run per post** (e.g. 20 posts = 20 runs). Keep default = Batch.

2. **Cache Facebook batch comment results**  
   Same post URLs + same `max_comments` → same comment data. Cache the batch comment API result (e.g. 1 hour) so re-runs or re-opening the same page don’t trigger new runs. *Implemented below.*

3. **Lower defaults when possible**  
   - `max_posts`: 10 is already reasonable; avoid raising unnecessarily.  
   - `max_comments_per_post`: 25 is good; slider can cap at 50 for cost control.

4. **Instagram comments**  
   Each post = one actor run. With 10 posts that’s 10 runs. Consider adding a “Max posts to fetch comments for” (e.g. 5) so users can limit cost.

5. **YouTube**  
   Already one batched run when possible; fallback is per-video. Cached. No change needed unless you add more comment sources.

---

## 2. Speed

### Bottlenecks

| Area | Why it’s slow | Mitigation |
|------|----------------|------------|
| Facebook comments (Individual) | 2 s `time.sleep` between **each** post | Use Batch; or reduce sleep to 1 s if rate limits allow |
| Instagram comments | N sequential/concurrent API calls | Already 3 workers; optional: cache by post URL list |
| Sentiment (N comments) | N calls to `analyze_sentiment_placeholder` | Cache per text (e.g. `@st.cache_data` on hashed text) |
| Advanced NLP dashboard | `analyze_corpus_advanced` every time | Cache by content hash; *implemented below* |
| Normalization | `normalize_post_data` on every load | Optional: cache by (platform, hash(raw_data)) |

### Implemented in this repo

- **Facebook batch comment cache**  
  Batch comment fetch is cached by (sorted post URLs, max_comments, token). Same page + same settings = no new Apify run for 1 hour.

- **Advanced NLP cache**  
  `analyze_corpus_advanced` result is cached by a hash of the comment list (TTL 10 min). Re-opening the same dashboard or re-running with same data reuses the result.

### Optional next steps

- **Sentiment cache**  
  Wrap `analyze_sentiment_placeholder(text)` in `@st.cache_data(ttl=3600)` keyed by `hashlib.sha256(text.encode()).hexdigest()` so repeated comments (or same session) don’t recompute.

- **Shorter sleep for Individual Facebook**  
  If Apify allows, reduce `time.sleep(2)` to `time.sleep(1)` in `fetch_comments_for_posts` to cut wait time in half (still prefer Batch).

- **Limit Instagram comment posts**  
  Add a slider “Max posts to fetch comments for” (e.g. 1–10) so heavy pages don’t trigger 20+ runs by default.

---

## 3. Cache settings (reference)

- **Posts fetch**: `ttl=3600`, `max_entries=64`  
- **Single post comments (Facebook)**: `ttl=3600`, `max_entries=256`  
- **YouTube comments**: `ttl=3600`, `max_entries=32`  
- **Facebook batch comments**: `ttl=3600`, `max_entries=32` (new)  
- **NLP corpus analysis**: `ttl=600`, `max_entries=16` (new)

All use `st.cache_data` so cache is per-session and respects Streamlit’s cache semantics.

---

## 4. Quick reference

| Goal | Action |
|------|--------|
| Lower Apify cost | Use Batch for Facebook; cache batch comments; lower max_posts / max_comments when possible |
| Faster dashboard | Cache NLP results; prefer Batch; optional sentiment cache |
| Safer for rate limits | Keep 2 s sleep for Individual; Batch avoids N runs so less risk |
