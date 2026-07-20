"""
Pipeline entry point. Current stage: OSM collector only.
"""

import config
from collectors import osm
from merger.merge import write_to_excel
from utils.logger import get_logger

logger = get_logger(__name__)


def run(geofence_key: str = config.ACTIVE_GEOFENCE) -> None:
    config.ensure_directories()

    logger.info(f"=== Pipeline run started for geofence: {geofence_key} ===")

    businesses = osm.collect(geofence_key)
    write_to_excel(businesses, geofence_key)

    logger.info("=== Pipeline run complete ===")


if __name__ == "__main__":
    run()