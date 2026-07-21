"""
Merger stage. Currently a pass-through while only one collector (OSM)
exists. Once Google Places / Connect.ae / Yellow Pages collectors are
added, this becomes the dedup/merge point across sources — combining
multiple collectors' Business lists into one before export.
"""

from models.business import Business
from utils.logger import get_logger

logger = get_logger(__name__)


def merge_sources(*source_lists: list[Business]) -> list[Business]:
    """
    Combine Business lists from multiple collectors into one list.
    Currently a simple concatenation (OSM is the only source); this is
    the seam where cross-source deduplication will be added once a
    second collector (e.g. Google Places) is implemented.
    """
    merged: list[Business] = []
    for source_list in source_lists:
        merged.extend(source_list)
    logger.info(f"Merged {len(source_lists)} source(s) into {len(merged)} businesses.")
    return merged