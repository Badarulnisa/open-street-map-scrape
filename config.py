"""
Central configuration for the OSINT business discovery pipeline.
No hardcoded values should exist outside this file.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# --- Project root & paths -------------------------------------------------
ROOT_DIR: Path = Path(__file__).resolve().parent
DATA_DIR: Path = ROOT_DIR / "data"
RAW_DIR: Path = DATA_DIR / "raw"
PROCESSED_DIR: Path = DATA_DIR / "processed"
OUTPUT_DIR: Path = ROOT_DIR / "output"

RAW_OSM_DIR: Path = RAW_DIR / "osm"
RAW_GOOGLE_DIR: Path = RAW_DIR / "google"
RAW_CONNECT_DIR: Path = RAW_DIR / "connect"
RAW_YELLOWPAGES_DIR: Path = RAW_DIR / "yellowpages"

# --- Geofences --------------------------------------------------------
GEOFENCES: dict[str, dict] = {
    "dubai": {
        "label": "Dubai, UAE",
        "bbox": (24.7921, 54.8951, 25.3574, 55.5651),
    },
    "abu_dhabi": {
        "label": "Abu Dhabi, UAE",
        "bbox": (22.6333, 51.4500, 24.9500, 55.6800),
    },
    "sharjah": {
        "label": "Sharjah, UAE",
        "bbox": (25.0500, 55.3000, 25.5500, 56.4000),
    },
    "ajman": {
        "label": "Ajman, UAE",
        "bbox": (25.3500, 55.4000, 25.4700, 55.6000),
    },
    "umm_al_quwain": {
        "label": "Umm Al Quwain, UAE",
        "bbox": (25.5000, 55.5000, 25.7000, 55.8000),
    },
    "ras_al_khaimah": {
        "label": "Ras Al Khaimah, UAE",
        "bbox": (25.5000, 55.7000, 26.1000, 56.3500),
    },
    "fujairah": {
        "label": "Fujairah, UAE",
        "bbox": (25.0000, 56.0500, 25.6000, 56.4500),
    },
}

ACTIVE_GEOFENCE: str = "dubai"

# --- Overpass API (OpenStreetMap) -----------------------------------------
OVERPASS_ENDPOINTS: list[str] = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]
OVERPASS_TIMEOUT_SECONDS: int = 180
OVERPASS_REQUEST_TIMEOUT: int = 120
OVERPASS_RETRY_DELAY_SECONDS: int = 5
OVERPASS_RETRIES_PER_ENDPOINT: int = 2
OVERPASS_BACKOFF_BASE_SECONDS: int = 4

OSM_GRID_ROWS: int = 4
OSM_GRID_COLS: int = 4
OSM_TILE_DELAY_SECONDS: int = 3

# Changed from ["shop", "office", "craft", "amenity"] to focus on
# genuine B2B/company entities instead of consumer storefronts
# (cafes, restaurants, bars were flooding in via "amenity" and "shop").
OSM_BUSINESS_TAG_KEYS: list[str] = ["office", "craft"]

# --- Logging ----------------------------------------------------------
LOG_DIR: Path = ROOT_DIR / "logs"
LOG_LEVEL: str = "INFO"
LOG_FORMAT: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

# --- SerpAPI (enrichment layer) --------------------------------------------
SERPAPI_KEY: str = os.getenv("SERPAPI_KEY", "")
SERPAPI_BASE_URL: str = "https://serpapi.com/search"
SERPAPI_TIMEOUT_SECONDS: int = 15
SERPAPI_RETRIES: int = 3
SERPAPI_BACKOFF_BASE_SECONDS: int = 2
SERPAPI_RATE_LIMIT_DELAY_SECONDS: float = 1.2

# --- Google Places (physical-presence + phone verification) --------------
GOOGLE_PLACES_API_KEY: str = os.getenv("GOOGLE_PLACES_API_KEY", "")
GOOGLE_PLACES_BASE_URL: str = "https://places.googleapis.com/v1/places:searchText"
GOOGLE_PLACES_TIMEOUT_SECONDS: int = 15
GOOGLE_PLACES_RETRIES: int = 3

# --- Enrichment control ------------------------------------------------
ENRICHMENT_LIMIT: int | None = 25  # demo run; raise to 250/1000/None later
CACHE_DIR: Path = ROOT_DIR / "cache"
ENRICHMENT_STATE_FILE: Path = DATA_DIR / "enrichment_state.jsonl"
ENRICHMENT_OUTPUT_PATH: Path = OUTPUT_DIR / "Dubai_Enriched.xlsx"

# --- OSM collection cache (avoids re-running the ~40min collection while debugging) ---
OSM_CACHE_FILE: Path = PROCESSED_DIR / "osm_collection_cache.json"
USE_OSM_CACHE: bool = True

# --- Output -------------------------------------------------------------
EXCEL_ENGINE: str = "openpyxl"


def ensure_directories() -> None:
    """Create all directories the pipeline depends on, if missing."""
    for path in (
        RAW_OSM_DIR,
        RAW_GOOGLE_DIR,
        RAW_CONNECT_DIR,
        RAW_YELLOWPAGES_DIR,
        PROCESSED_DIR,
        OUTPUT_DIR,
        LOG_DIR,
        CACHE_DIR,
        ENRICHMENT_STATE_FILE.parent,
    ):
        path.mkdir(parents=True, exist_ok=True)