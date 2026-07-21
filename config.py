"""
Central configuration for the OSINT business discovery pipeline.
No hardcoded values should exist outside this file.
"""

from pathlib import Path

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
# Each geofence is a bounding box: (south, west, north, east) in WGS84.
# Start with Dubai; add more emirates/GCC cities here as they're onboarded.
GEOFENCES: dict[str, dict] = {
    "dubai": {
        "label": "Dubai, UAE",
        "bbox": (24.7921, 54.8951, 25.3574, 55.5651),  # south, west, north, east
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
OVERPASS_REQUEST_TIMEOUT: int = 120  # HTTP client timeout, seconds
OVERPASS_RETRY_DELAY_SECONDS: int = 5  # pause before trying the next mirror
OVERPASS_RETRIES_PER_ENDPOINT: int = 2  # retry attempts on the SAME endpoint before moving on
OVERPASS_BACKOFF_BASE_SECONDS: int = 4  # exponential backoff base between same-endpoint retries

# Dubai's full bbox times out as a single query on public Overpass servers,
# so it's split into a grid of smaller tiles queried sequentially.
OSM_GRID_ROWS: int = 4
OSM_GRID_COLS: int = 4
OSM_TILE_DELAY_SECONDS: int = 3  # pause between tile requests (be a good API citizen)

# OSM tags that indicate a "business" (commercial/office/shop presence).
# Kept broad on purpose — recruiter requirement is coverage over precision.
OSM_BUSINESS_TAG_KEYS: list[str] = ["shop", "office", "craft", "amenity"]

# --- Logging ----------------------------------------------------------
LOG_DIR: Path = ROOT_DIR / "logs"
LOG_LEVEL: str = "INFO"
LOG_FORMAT: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

# --- LinkedIn enrichment -------------------------------------------------
# Leave LINKEDIN_SEARCH_API_KEY empty to skip enrichment entirely (safe
# default). Fill it in once you've signed up for a real search API - Bing
# Web Search API is what enrichers/linkedin.py is wired for by default.
LINKEDIN_SEARCH_API_KEY: str = ""
LINKEDIN_SEARCH_API_URL: str = "https://api.bing.microsoft.com/v7.0/search"
LINKEDIN_SEARCH_TIMEOUT_SECONDS: int = 15
LINKEDIN_SEARCH_API_KEY: str = ""
LINKEDIN_SEARCH_API_URL: str = "https://api.bing.microsoft.com/v7.0/search"
LINKEDIN_SEARCH_TIMEOUT_SECONDS: int = 15
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
    ):
        path.mkdir(parents=True, exist_ok=True)