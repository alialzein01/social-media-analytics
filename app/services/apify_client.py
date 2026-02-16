"""
Production Apify client with retries, timeouts, and typed responses.

- Token must be supplied from server env (never from frontend).
- All actor/dataset calls go through this module for consistent retry and validation.
"""

import logging
import random
import time
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar

from apify_client import ApifyClient

from app.config.settings import DEFAULT_TIMEOUT

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

DEFAULT_BASE_URL = "https://api.apify.com"
MAX_RETRIES = 4
INITIAL_BACKOFF_SECS = 1.0
MAX_BACKOFF_SECS = 60.0
JITTER_FRACTION = 0.2

# Run statuses we treat as terminal
TERMINAL_STATUSES = frozenset({"SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"})


# -----------------------------------------------------------------------------
# Errors (user-friendly catalog)
# -----------------------------------------------------------------------------


class ApifyClientError(Exception):
    """Base for Apify client errors."""

    def __init__(self, message: str, user_message: Optional[str] = None):
        super().__init__(message)
        self.user_message = user_message or message


class ApifyRunError(ApifyClientError):
    """Actor run failed or timed out."""


class ApifyRateLimitError(ApifyClientError):
    """Rate limited by Apify."""


class ApifyAuthError(ApifyClientError):
    """Invalid or missing API token."""


def _user_message_for_exception(e: Exception) -> str:
    """Map known Apify/HTTP errors to user-friendly messages."""
    err_str = str(e).lower()
    if "401" in err_str or "unauthorized" in err_str or "token" in err_str:
        return "Invalid or expired Apify API token. Check APIFY_TOKEN in your environment."
    if "429" in err_str or "rate" in err_str or "limit" in err_str:
        return "Apify rate limit reached. Please wait a moment and try again."
    if "timeout" in err_str or "timed out" in err_str:
        return "The request took too long. Try fewer posts or a shorter date range."
    if "502" in err_str or "503" in err_str or "504" in err_str:
        return "Apify is temporarily unavailable. Please try again in a few minutes."
    return "An error occurred while calling Apify. Check the logs for details."


# -----------------------------------------------------------------------------
# Client factory
# -----------------------------------------------------------------------------


def create_apify_client(
    token: str,
    base_url: Optional[str] = None,
) -> ApifyClient:
    """
    Create an Apify client instance.

    Args:
        token: Apify API token (must come from server env).
        base_url: Optional API base URL (default: https://api.apify.com).

    Returns:
        ApifyClient instance.
    """
    if not token or not token.strip():
        raise ApifyAuthError("APIFY_TOKEN is empty", "Please set APIFY_TOKEN in your environment.")
    url = (base_url or DEFAULT_BASE_URL).rstrip("/")
    return ApifyClient(token=token, api_url=url)


# -----------------------------------------------------------------------------
# Retry helper
# -----------------------------------------------------------------------------


def _should_retry(e: Exception) -> bool:
    """Whether to retry on this exception."""
    err_str = str(e).lower()
    if "401" in err_str or "unauthorized" in err_str:
        return False
    if "429" in err_str or "rate" in err_str or "limit" in err_str:
        return True
    if "502" in err_str or "503" in err_str or "504" in err_str or "timeout" in err_str:
        return True
    if "connection" in err_str or "network" in err_str:
        return True
    return False


def _backoff_with_jitter(attempt: int) -> float:
    """Exponential backoff with jitter."""
    backoff = min(INITIAL_BACKOFF_SECS * (2**attempt), MAX_BACKOFF_SECS)
    jitter = backoff * JITTER_FRACTION * (2 * random.random() - 1)
    return max(0.1, backoff + jitter)


T = TypeVar("T")


def _with_retry(fn: Callable[[], T]) -> T:
    """Run fn with exponential backoff + jitter on retryable errors."""
    last_error: Optional[Exception] = None
    for attempt in range(MAX_RETRIES):
        try:
            return fn()
        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES - 1 and _should_retry(e):
                sleep_secs = _backoff_with_jitter(attempt)
                logger.warning(
                    "Apify call failed (attempt %s/%s), retrying in %.1fs: %s",
                    attempt + 1,
                    MAX_RETRIES,
                    sleep_secs,
                    e,
                )
                time.sleep(sleep_secs)
            else:
                raise
    raise last_error or RuntimeError("retry loop exited without result")


# -----------------------------------------------------------------------------
# Run / Dataset / Key-Value
# -----------------------------------------------------------------------------


def run_actor(
    client: ApifyClient,
    actor_id: str,
    run_input: Dict[str, Any],
    *,
    timeout_secs: Optional[int] = None,
    memory_mbytes: Optional[int] = None,
    build: Optional[str] = None,
    wait_for_finish: bool = True,
    wait_secs: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Run an Apify actor with optional retry and timeout.

    Args:
        client: ApifyClient from create_apify_client().
        actor_id: Actor ID (e.g. "apify/facebook-comments-scraper").
        run_input: Actor input dict.
        timeout_secs: Actor run timeout (seconds).
        memory_mbytes: Memory limit for the run (MB).
        build: Build tag or number.
        wait_for_finish: If True, call() and wait; if False, start() and return run id.
        wait_secs: Max seconds to wait for run to finish (only if wait_for_finish).

    Returns:
        Run object (dict with id, status, defaultDatasetId, etc.).
    """
    timeout_secs = timeout_secs or DEFAULT_TIMEOUT

    def _call() -> Dict[str, Any]:
        actor_client = client.actor(actor_id)
        if wait_for_finish:
            run = actor_client.call(
                run_input=run_input,
                timeout_secs=timeout_secs,
                memory_mbytes=memory_mbytes,
                build=build,
                wait_secs=wait_secs,
            )
        else:
            run = actor_client.start(
                run_input=run_input,
                timeout_secs=timeout_secs,
                memory_mbytes=memory_mbytes,
                build=build,
            )
        return _validate_run(run, actor_id)

    return _with_retry(_call)


def _validate_run(run: Any, actor_id: str) -> Dict[str, Any]:
    """Ensure run dict has required fields."""
    if not run or not isinstance(run, dict):
        raise ApifyRunError(
            f"Actor {actor_id} returned invalid run object",
            "The scraper did not return a valid response. Try again later.",
        )
    status = run.get("status")
    if status in TERMINAL_STATUSES and status != "SUCCEEDED":
        msg = run.get("statusMessage") or f"Run status: {status}"
        raise ApifyRunError(
            f"Actor run failed: {msg}",
            _user_message_for_exception(Exception(msg)),
        )
    return run


def get_run_status(client: ApifyClient, run_id: str) -> Dict[str, Any]:
    """Get status of an actor run by ID."""

    # ApifyClient has client.run(run_id).get()
    def _get():
        run = client.run(run_id).get()
        if not run or not isinstance(run, dict):
            raise ApifyRunError(f"Invalid run response for {run_id}", "Could not get run status.")
        return run

    return _with_retry(_get)


def get_dataset_items(
    client: ApifyClient,
    dataset_id: str,
    *,
    limit: Optional[int] = None,
    offset: int = 0,
    clean: bool = True,
) -> List[Dict[str, Any]]:
    """
    Get items from a dataset with optional pagination.

    Args:
        client: ApifyClient.
        dataset_id: Dataset ID from run["defaultDatasetId"].
        limit: Max items to return (None = use default pagination).
        offset: Skip this many items.
        clean: If True, filter out None/invalid items.

    Returns:
        List of item dicts.
    """

    def _fetch() -> List[Dict[str, Any]]:
        dataset = client.dataset(dataset_id)
        items: List[Dict[str, Any]] = []
        # Use iterate_items for compatibility; we slice by offset/limit ourselves
        for i, item in enumerate(dataset.iterate_items()):
            if i < offset:
                continue
            if limit is not None and len(items) >= limit:
                break
            if clean and (item is None or not isinstance(item, dict)):
                continue
            items.append(item if isinstance(item, dict) else {})
        return items

    return _with_retry(_fetch)


def get_key_value_store_record(
    client: ApifyClient,
    store_id: str,
    key: str,
) -> Any:
    """Get a record from a key-value store."""

    def _get():
        return client.key_value_store(store_id).get_record(key)

    return _with_retry(_get)


def run_actor_and_fetch_dataset(
    client: ApifyClient,
    actor_id: str,
    run_input: Dict[str, Any],
    *,
    timeout_secs: Optional[int] = None,
    max_items: Optional[int] = None,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Run actor, wait for finish, and return run + dataset items.
    Convenience for the common "call then iterate" pattern.
    """
    run = run_actor(
        client,
        actor_id,
        run_input,
        timeout_secs=timeout_secs or DEFAULT_TIMEOUT,
        wait_for_finish=True,
    )
    dataset_id = run.get("defaultDatasetId")
    if not dataset_id:
        raise ApifyRunError(
            "Run has no defaultDatasetId",
            "The scraper run did not produce a dataset. Try again.",
        )
    items = get_dataset_items(client, dataset_id, limit=max_items, clean=True)
    return run, items
