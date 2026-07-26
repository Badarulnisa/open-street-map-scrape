"""
Pipeline entry point.

Flow: Collect -> Deduplicate (done inside the collector) -> Enrichment
(LinkedIn, website, socials, maps, company/registration) -> Export Excel
-> return Business objects.
"""

import json
import time

import config
from collectors import osm
from collectors import shams_directory
from enrichers.pipeline import run_enrichment
from exporters.excel import save_to_excel, save_enriched_excel
from models.business import Business
from utils.logger import get_logger

logger = get_logger(__name__)


def _load_cached_businesses() -> list[Business] | None:
    if not config.USE_OSM_CACHE or not config.OSM_CACHE_FILE.exists():
        return None
    try:
        with config.OSM_CACHE_FILE.open("r", encoding="utf-8") as f:
            raw = json.load(f)
        businesses = [Business.from_dict(item) for item in raw]
        logger.info(f"Loaded {len(businesses)} businesses from cache: {config.OSM_CACHE_FILE}")
        return businesses
    except Exception as exc:
        logger.warning(f"Failed to load OSM cache ({exc}); will re-collect.")
        return None


def _save_osm_cache(businesses: list[Business]) -> None:
    config.OSM_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with config.OSM_CACHE_FILE.open("w", encoding="utf-8") as f:
        json.dump([b.to_dict() for b in businesses], f)
    logger.info(f"Cached {len(businesses)} businesses to {config.OSM_CACHE_FILE}")


def run(geofence_key: str = config.ACTIVE_GEOFENCE) -> list[Business]:
    config.ensure_directories()
    start_time = time.monotonic()

    geofence_label = config.GEOFENCES[geofence_key]["label"]
    logger.info(f"=== Pipeline run started for {geofence_label} ===")

    businesses = _load_cached_businesses()
    if businesses is None:
        logger.info(f"Collecting {geofence_label}...")
        businesses = osm.collect(geofence_key)
        logger.info(f"{len(businesses)} unique businesses found.")

        logger.info("Collecting SHAMS directory...")
        shams_businesses = shams_directory.collect("sharjah")
        logger.info(f"{len(shams_businesses)} SHAMS businesses found.")

        businesses.extend(shams_businesses)
        _save_osm_cache(businesses)

    logger.info("Exporting raw Excel...")
    raw_output_path = config.OUTPUT_DIR / f"{geofence_key.capitalize()}.xlsx"
    save_to_excel(businesses, raw_output_path)

    logger.info(f"Enriching first {config.ENRICHMENT_LIMIT or 'all'} businesses via SerpAPI...")
    enriched = run_enrichment(businesses)

    logger.info("Exporting enriched Excel...")
    save_enriched_excel(enriched, config.ENRICHMENT_OUTPUT_PATH)

    elapsed = time.monotonic() - start_time
    logger.info(
        "=== Pipeline Complete ===\n"
        f"Businesses found: {len(businesses)}\n"
        f"Raw output: {raw_output_path}\n"
        f"Enriched output: {config.ENRICHMENT_OUTPUT_PATH}\n"
        f"Runtime: {elapsed:.1f}s"
    )
    return businesses


if __name__ == "__main__":
    run()