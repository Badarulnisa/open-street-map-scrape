"""
Pipeline entry point.

Flow: Collect -> Deduplicate (done inside the collector) -> LinkedIn
enrichment -> Export Excel -> return Business objects.
"""

import time

import config
from collectors import osm
from enrichers import linkedin
from exporters.excel import save_to_excel
from models.business import Business
from utils.logger import get_logger

logger = get_logger(__name__)


def run(geofence_key: str = config.ACTIVE_GEOFENCE) -> list[Business]:
    config.ensure_directories()
    start_time = time.monotonic()

    geofence_label = config.GEOFENCES[geofence_key]["label"]
    logger.info(f"=== Pipeline run started for {geofence_label} ===")

    logger.info(f"Collecting {geofence_label}...")
    businesses = osm.collect(geofence_key)
    logger.info(f"{len(businesses)} unique businesses found.")

    logger.info("Finding LinkedIn pages...")
    businesses = linkedin.enrich(businesses)

    logger.info("Exporting Excel...")
    output_path = config.OUTPUT_DIR / f"{geofence_key.capitalize()}.xlsx"
    save_to_excel(businesses, output_path)

    elapsed = time.monotonic() - start_time
    logger.info(
        "=== Pipeline Complete ===\n"
        f"Businesses found: {len(businesses)}\n"
        f"Output: {output_path}\n"
        f"Runtime: {elapsed:.1f}s"
    )
    return businesses


if __name__ == "__main__":
    run()