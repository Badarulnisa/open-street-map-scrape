"""
Runs all enrichers over the first N businesses, with resume support.
State is tracked by a stable key (name + city), not row index, so
re-ordering the source data doesn't break resume.
"""
import json
from pathlib import Path

import config
from models.business import Business
from enrichers.serpapi_client import SerpAPIClient
from enrichers.linkedin import enrich_linkedin
from enrichers.website import enrich_website
from enrichers.socials import enrich_socials
from enrichers.maps import enrich_maps
from enrichers.company import enrich_company
from utils.logger import get_logger

logger = get_logger(__name__)


def _business_key(b: Business) -> str:
    return f"{b.name.strip().lower()}|{b.city.strip().lower()}"


def _load_completed_keys() -> set[str]:
    if not config.ENRICHMENT_STATE_FILE.exists():
        return set()
    keys = set()
    with config.ENRICHMENT_STATE_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            keys.add(record["key"])
    return keys


def _mark_completed(business: Business) -> None:
    config.ENRICHMENT_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with config.ENRICHMENT_STATE_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"key": _business_key(business)}) + "\n")


def run_enrichment(businesses: list[Business]) -> list[Business]:
    limit = config.ENRICHMENT_LIMIT
    target = businesses if limit is None else businesses[:limit]

    completed_keys = _load_completed_keys()
    client = SerpAPIClient()

    for idx, business in enumerate(target, start=1):
        key = _business_key(business)
        if key in completed_keys:
            logger.info(f"Business {idx}/{len(target)}: {business.name} — already enriched, skipping")
            continue

        logger.info(f"Business {idx}/{len(target)}: {business.name}")
        try:
            logger.info("Searching LinkedIn...")
            enrich_linkedin(business, client)

            logger.info("Searching Google Maps...")
            enrich_maps(business, client)

            logger.info("Searching Facebook/Instagram/Crunchbase...")
            enrich_socials(business, client)

            logger.info("Searching Website...")
            enrich_website(business, client)

            logger.info("Searching company profile + registration + careers...")
            enrich_company(business, client)

            business.search_status = "done"
            logger.info("Completed.")
        except Exception as exc:
            business.search_status = "failed"
            business.search_notes = str(exc)
            logger.error(f"Enrichment failed for {business.name}: {exc}")

        _mark_completed(business)

    return businesses