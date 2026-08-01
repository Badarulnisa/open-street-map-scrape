"""
Pipeline entry point.

Flow: Collect from directory sources (SHAMS, DIFC) -> Export Excel ->
return Business objects.

OSM and SerpAPI enrichment have been removed from the active pipeline:
- OSM gives physical/virtual presence signals but not verified
  registration status, which is what this project actually needs.
- SerpAPI enrichment is disabled since the trial key is exhausted;
  re-enable enrichers.pipeline.run_enrichment() once a paid key or
  alternative search backend is in place.
"""

import time

import config
from collectors import shams_directory, difc_register
from exporters.excel import save_to_excel
from models.business import Business
from utils.logger import get_logger

logger = get_logger(__name__)


def run() -> list[Business]:
    config.ensure_directories()
    start_time = time.monotonic()

    logger.info("=== Pipeline run started (directory sources only) ===")

    businesses: list[Business] = []

    logger.info("Collecting SHAMS directory...")
    shams_businesses = shams_directory.collect("sharjah")
    logger.info(f"{len(shams_businesses)} SHAMS businesses found.")
    businesses.extend(shams_businesses)

    logger.info("Collecting DIFC public register...")
    difc_businesses = difc_register.collect("dubai")
    logger.info(f"{len(difc_businesses)} DIFC companies found.")
    businesses.extend(difc_businesses)

    logger.info("Exporting Excel...")
    output_path = config.OUTPUT_DIR / "UAE_Registered_Companies.xlsx"
    save_to_excel(businesses, output_path)

    elapsed = time.monotonic() - start_time
    logger.info(
        "=== Pipeline Complete ===\n"
        f"Total companies found: {len(businesses)}\n"
        f"Output: {output_path}\n"
        f"Runtime: {elapsed:.1f}s"
    )
    return businesses


if __name__ == "__main__":
    run()