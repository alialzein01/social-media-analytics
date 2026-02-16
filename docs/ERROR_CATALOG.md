# Apify Error Catalog

User-facing messages and recommended actions for common Apify-related errors.

## Authentication

| Condition | User message | Action |
|-----------|--------------|--------|
| Missing token | "Please set APIFY_TOKEN in your environment." | Set `APIFY_TOKEN` in `.env` or `.streamlit/secrets.toml`. |
| Invalid/expired token | "Invalid or expired Apify API token. Check APIFY_TOKEN in your environment." | Regenerate token at [Apify Console](https://console.apify.com/account/integrations). |

## Rate limits & availability

| Condition | User message | Action |
|-----------|--------------|--------|
| Rate limit (429) | "Apify rate limit reached. Please wait a moment and try again." | Wait 1–2 minutes; reduce posts/comments per request. |
| Timeout | "The request took too long. Try fewer posts or a shorter date range." | Lower "Posts to fetch" or "Max comments per post"; narrow date range. |
| Server error (502/503/504) | "Apify is temporarily unavailable. Please try again in a few minutes." | Retry later; check [Apify Status](https://status.apify.com). |

## Run / actor errors

| Condition | User message | Action |
|-----------|--------------|--------|
| Run failed / aborted | "The scraper did not return a valid response. Try again later." or status-specific | Check URL is public; try different post or platform. |
| No dataset | "The scraper run did not produce a dataset. Try again." | Re-run; some actors return empty for restricted content. |

## Generic

| Condition | User message | Action |
|-----------|--------------|--------|
| Other | "An error occurred while calling Apify. Check the logs for details." | Check app logs; verify actor IDs in `app/config/settings.py`. |

## Env vars reference

- **APIFY_TOKEN** (required): API token for Apify. Never commit or expose in frontend.
- **APIFY_WEBHOOK_SECRET** (optional): For webhook signature verification if you add async run completion.
