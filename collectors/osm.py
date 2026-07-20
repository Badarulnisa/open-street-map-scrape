"""
OpenStreetMap collector.

Queries the Overpass API for all nodes/ways/relations inside a geofence
bounding box that carry a business-indicating tag (shop, office, craft,
amenity), and converts them into Business objects.
"""

import time
from typing import Optional

import requests

import config
from models.business import Business
from utils.logger import get_logger

logger = get_logger(__name__)


def _split_bbox(
    bbox: tuple[float, float, float, float], rows: int, cols: int
) -> list[tuple[float, float, float, float]]:
    """
    Split a (south, west, north, east) bbox into a rows x cols grid of
    smaller tiles. Overpass's public servers gateway-timeout on large
    whole-city queries, so tiling is required, not optional, for a bbox
    the size of Dubai.
    """
    south, west, north, east = bbox
    lat_step = (north - south) / rows
    lon_step = (east - west) / cols

    tiles: list[tuple[float, float, float, float]] = []
    for r in range(rows):
        tile_south = south + r * lat_step
        tile_north = tile_south + lat_step
        for c in range(cols):
            tile_west = west + c * lon_step
            tile_east = tile_west + lon_step
            tiles.append((tile_south, tile_west, tile_north, tile_east))
    return tiles


def _build_overpass_query(bbox: tuple[float, float, float, float]) -> str:
    """
    Build an Overpass QL query for all business-tagged elements in bbox.
    bbox is (south, west, north, east).
    """
    south, west, north, east = bbox
    bbox_str = f"{south},{west},{north},{east}"

    tag_clauses = "\n  ".join(
        f'node["{tag}"]({bbox_str});\n  way["{tag}"]({bbox_str});'
        for tag in config.OSM_BUSINESS_TAG_KEYS
    )

    query = f"""
    [out:json][timeout:{config.OVERPASS_TIMEOUT_SECONDS}];
    (
      {tag_clauses}
    );
    out center tags;
    """
    return query


def _request_overpass(query: str) -> Optional[dict]:
    """Try each configured Overpass endpoint until one succeeds."""
    headers = {
        # Overpass etiquette requires an identifying User-Agent; the default
        # python-requests UA gets rejected (406) by the main instance.
        "User-Agent": "OSINT-Business-Discovery-Pipeline/0.1 (contact: internal-use)",
        "Accept": "application/json",
    }

    for attempt, endpoint in enumerate(config.OVERPASS_ENDPOINTS):
        if attempt > 0:
            # Give the next mirror breathing room instead of hammering it
            # immediately after the previous endpoint just failed.
            time.sleep(config.OVERPASS_RETRY_DELAY_SECONDS)
        try:
            logger.info(f"Querying Overpass endpoint: {endpoint}")
            response = requests.post(
                endpoint,
                data={"data": query},
                headers=headers,
                timeout=config.OVERPASS_REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            logger.warning(f"Overpass endpoint failed ({endpoint}): {exc}")
            continue
    logger.error("All Overpass endpoints failed.")
    return None


def _element_to_business(element: dict, city_label: str) -> Optional[Business]:
    """Convert a single Overpass element into a Business, or None if unnamed."""
    tags = element.get("tags", {})
    name = tags.get("name")
    if not name:
        # Coverage matters, but an unnamed node is not an actionable lead.
        return None

    # Nodes have lat/lon directly; ways/relations have a "center" object.
    lat = element.get("lat") or element.get("center", {}).get("lat")
    lon = element.get("lon") or element.get("center", {}).get("lon")

    category = (
        tags.get("shop")
        or tags.get("office")
        or tags.get("craft")
        or tags.get("amenity")
    )

    address_parts = [
        tags.get("addr:housenumber"),
        tags.get("addr:street"),
        tags.get("addr:neighbourhood"),
    ]
    address = " ".join(part for part in address_parts if part) or None

    return Business(
        name=name,
        city=city_label,
        area=tags.get("addr:neighbourhood") or tags.get("addr:suburb"),
        category=category,
        latitude=lat,
        longitude=lon,
        address=address,
        website=tags.get("website") or tags.get("contact:website"),
        phone=tags.get("phone") or tags.get("contact:phone"),
        source="osm",
    )


def collect(geofence_key: str = config.ACTIVE_GEOFENCE) -> list[Business]:
    """
    Run the OSM collector for the given geofence key (must exist in
    config.GEOFENCES) and return a list of Business objects.

    The geofence bbox is split into a grid of tiles and queried one tile
    at a time, since a single whole-city query gateway-times-out on
    Overpass's public servers.
    """
    geofence = config.GEOFENCES[geofence_key]
    bbox = geofence["bbox"]
    city_label = geofence["label"]

    tiles = _split_bbox(bbox, config.OSM_GRID_ROWS, config.OSM_GRID_COLS)
    logger.info(
        f"Starting OSM collection for {city_label}: {len(tiles)} tiles "
        f"({config.OSM_GRID_ROWS}x{config.OSM_GRID_COLS} grid)"
    )

    businesses: list[Business] = []
    skipped_unnamed = 0

    for i, tile_bbox in enumerate(tiles, start=1):
        logger.info(f"Tile {i}/{len(tiles)}: bbox={tile_bbox}")
        query = _build_overpass_query(tile_bbox)
        result = _request_overpass(query)

        if result is None:
            logger.warning(f"Tile {i}/{len(tiles)} failed after all endpoints; skipping.")
            continue

        elements = result.get("elements", [])
        logger.info(f"Tile {i}/{len(tiles)} returned {len(elements)} raw elements.")

        for element in elements:
            business = _element_to_business(element, city_label)
            if business is None:
                skipped_unnamed += 1
                continue
            businesses.append(business)

        if i < len(tiles):
            time.sleep(config.OSM_TILE_DELAY_SECONDS)

    logger.info(
        f"OSM collection complete: {len(businesses)} named businesses "
        f"({skipped_unnamed} unnamed elements skipped across {len(tiles)} tiles)."
    )
    return businesses