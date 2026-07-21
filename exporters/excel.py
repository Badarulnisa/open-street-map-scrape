"""
Excel export. The single place responsible for turning Business objects
into the final .xlsx deliverable. Collectors and the merger never touch
pandas/openpyxl directly — they just produce/combine Business objects
and hand them here.
"""
from pathlib import Path
import pandas as pd
import config
from models.business import Business
from utils.logger import get_logger
logger = get_logger(__name__)
EXPORT_COLUMNS: list[str] = [
    "name", "city", "area", "category", "website", "phone",
    "linkedin_url", "latitude", "longitude", "source",
    "verification_status", "confidence_score",
]
def save_to_excel(businesses: list[Business], output_path: Path) -> Path:
    """Write a list of Business objects to a single Excel file at output_path."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not businesses:
        logger.warning(f"No businesses to write to {output_path}.")
    rows = [b.to_dict() for b in businesses]
    df = pd.DataFrame(rows)
    df = df.reindex(columns=EXPORT_COLUMNS)
    df.to_excel(output_path, index=False, engine=config.EXCEL_ENGINE)
    logger.info(f"Saved: {output_path} ({len(businesses)} rows)")
    return output_path