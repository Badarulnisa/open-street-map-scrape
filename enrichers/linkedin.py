"""
LinkedIn company page discovery.

Does NOT scrape LinkedIn or Google search results directly - that would
violate their Terms of Service at any real volume and is exactly the
kind of scraper this project's brief says it isn't. Instead this module
calls a configurable search API (Bing Web Search, SerpAPI, Google
Programmable Search - whichever key you put in config.py) and reads a
LinkedIn company URL out of the results if one appears.

If no API key is configured, enrichment is skipped entirely and every
business gets linkedin_url = None - the pipeline still runs end to end,
it just doesn't guess.
"""

import requests

import config
from models.business import Business
from utils.logger import get_logger

logger = get_logger(__name__)

_cache: dict[str, str | None] = {}


def _search_backend_configured() -> bool:
    return bool(config.LINKEDIN_SEARCH_API_KEY)


def _query_search_api(company_name: str, city: str) -> str | None:
    """
    Call the configured search API and return the first linkedin.com/company
    URL found in the results, or None. Currently wired for Bing Web Search
    API - swap the request/parsing below if you use SerpAPI or Google
    Programmable Search instead.
    """
    query = f'"{company_name}" {city} site:linkedin.com/company'

    try:
        response = requests.get(
            config.LINKEDIN_SEARCH_API_URL,
            headers={"Ocp-Apim-Subscription-Key": config.LINKEDIN_SEARCH_API_KEY},
            params={"q": query, "count": 5},
            timeout=config.LINKEDIN_SEARCH_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        results = response.json()

        for item in results.get("webPages", {}).get("value", []):
            url = item.get("url", "")
            if "linkedin.com/company" in url:
                return url

    except requests.RequestException as exc:
        logger.warning(f"LinkedIn search failed for '{company_name}': {exc}")

    return None


def enrich(businesses: list[Business]) -> list[Business]:
    """
    Populate linkedin_url on every Business, caching by normalized company
    name so businesses sharing a name (chains, duplicate listings) only
    trigger one search.
    """
    if not _search_backend_configured():
        logger.warning(
            "No LINKEDIN_SEARCH_API_KEY configured in config.py - skipping "
            "LinkedIn enrichment. All businesses will have linkedin_url=None."
        )
        return businesses

    found_count = 0
    for business in businesses:
        cache_key = business.name.strip().lower()

        if cache_key in _cache:
            business.linkedin_url = _cache[cache_key]
        else:
            linkedin_url = _query_search_api(business.name, business.city)
            _cache[cache_key] = linkedin_url
            business.linkedin_url = linkedin_url

        if business.linkedin_url:
            found_count += 1
            if business.verification_status == "OSM":
                business.verification_status = "OSM+LinkedIn"
                business.confidence_score = max(business.confidence_score, 0.70)

    logger.info(f"LinkedIn found for {found_count}/{len(businesses)} companies.")
    return businesses