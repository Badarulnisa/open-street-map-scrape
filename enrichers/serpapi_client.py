"""
Thin, resilient wrapper around SerpAPI. Every enricher goes through this —
retry, backoff, timeout, and disk caching are handled in exactly one place.
"""
import hashlib
import json
import time
from pathlib import Path
from typing import Optional

import requests

import config
from utils.logger import get_logger

logger = get_logger(__name__)


class SerpAPIClient:
    def __init__(self) -> None:
        if not config.SERPAPI_KEY:
            raise RuntimeError(
                "SERPAPI_KEY is not set. Add it to your .env file."
            )
        config.CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def _cache_path(self, query: str) -> Path:
        digest = hashlib.sha256(query.encode("utf-8")).hexdigest()
        return config.CACHE_DIR / f"{digest}.json"

    def search(self, query: str, num: int = 5) -> list[dict]:
        """Return organic_results for a query, using cache if present."""
        cache_file = self._cache_path(query)
        if cache_file.exists():
            logger.debug(f"Cache hit: {query}")
            return json.loads(cache_file.read_text(encoding="utf-8"))

        params = {
            "q": query,
            "api_key": config.SERPAPI_KEY,
            "num": num,
            "engine": "google",
        }

        last_error: Optional[Exception] = None
        for attempt in range(1, config.SERPAPI_RETRIES + 1):
            try:
                resp = requests.get(
                    config.SERPAPI_BASE_URL,
                    params=params,
                    timeout=config.SERPAPI_TIMEOUT_SECONDS,
                )
                resp.raise_for_status()
                data = resp.json()
                results = data.get("organic_results", [])
                cache_file.write_text(json.dumps(results), encoding="utf-8")
                time.sleep(config.SERPAPI_RATE_LIMIT_DELAY_SECONDS)
                return results
            except requests.RequestException as exc:
                last_error = exc
                backoff = config.SERPAPI_BACKOFF_BASE_SECONDS * (2 ** (attempt - 1))
                logger.warning(
                    f"SerpAPI request failed (attempt {attempt}/{config.SERPAPI_RETRIES}): "
                    f"{exc}. Retrying in {backoff}s."
                )
                time.sleep(backoff)

        logger.error(f"SerpAPI query permanently failed: {query} ({last_error})")
        return []