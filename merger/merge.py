"""
Merger stage. For now (OSM-only phase) this just serializes a single
collector's output to an Excel file. Once multiple collectors exist,
this becomes the dedup/merge point across sources.
"""

from pathlib import Path

import pandas as pd

import config
from models.business import Business
from utils.logger import get_logger

logger = get_logger(__name__)


def write_to_excel(businesses: list[Business], geofence_key: str) -> Path:
    """Write a list of Business objects to a single Excel file in output/."""
    if not businesses:
        logger.warning(f"No businesses to write for geofence '{geofence_key}'.")

    rows = [b.to_dict() for b in businesses]
    df = pd.DataFrame(rows)

    output_path = config.OUTPUT_DIR / f"{geofence_key}_osm.xlsx"
    df.to_excel(output_path, index=False, engine=config.EXCEL_ENGINE)

    logger.info(f"Wrote {len(businesses)} rows to {output_path}")
    return output_path