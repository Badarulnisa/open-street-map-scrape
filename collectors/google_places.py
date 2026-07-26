"""
Collects businesses from Google Places API (New) Text Search, per category,
tiled across the active geofence to respect per-request result caps.

Search terms below target genuine B2B/corporate entities (trading
companies, consultancies, law firms, etc.) rather than consumer
storefronts, since Google Places reliably returns verified phone numbers
for this — a stronger phone-number source than OSM tagging.
"""
import time
from typing import Optional

import requests

import config
from models.business import Business
from utils.logger import get_logger

logger = get_logger(__name__)

SEARCH_TERMS: list[str] = [
    "trading company", "consultancy", "real estate agency", "law firm",
    "logistics company", "import export company", "manufacturing company",
    "IT company", "construction company", "accounting firm",
]


def _search_text(query: str, api_key: str) -> list[dict]:
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": (
            "places.displayName,places.formattedAddress,places.location,"
            "places.websiteUri,places.internationalPhoneNumber,"
            "places.primaryTypeDisplayName"
        ),
    }
    payload = {"textQuery": query}

    for attempt in range(1, config.GOOGLE_PLACES_RETRIES + 1):
        try:
            resp = requests.post(
                config.GOOGLE_PLACES_BASE_URL,
                json=payload,
                headers=headers,
                timeout=config.GOOGLE_PLACES_TIMEOUT_SECONDS,
            )
            resp.raise_for_status()
            return resp.json().get("places", [])
        except requests.RequestException as exc:
            logger.warning(f"Places API failed (attempt {attempt}): {exc}")
            time.sleep(2 ** attempt)

    logger.error(f"Places API permanently failed for query: {query}")
    return []


def collect(geofence_key: str) -> list[Business]:
    if not config.GOOGLE_PLACES_API_KEY:
        logger.warning("GOOGLE_PLACES_API_KEY not set — skipping Google Places collection.")
        return []

    geofence = config.GEOFENCES[geofence_key]
    city_label = geofence["label"].split(",")[0]

    businesses: list[Business] = []
    seen_keys: set[str] = set()

    for term in SEARCH_TERMS:
        query = f"{term} in {city_label}"
        logger.info(f"Google Places query: {query}")
        places = _search_text(query, config.GOOGLE_PLACES_API_KEY)

        for place in places:
            name = place.get("displayName", {}).get("text")
            if not name:
                continue

            key = f"{name.lower()}|{place.get('formattedAddress', '').lower()}"
            if key in seen_keys:
                continue
            seen_keys.add(key)

            location = place.get("location", {})
            businesses.append(
                Business(
                    name=name,
                    city=city_label,
                    category=place.get("primaryTypeDisplayName", {}).get("text"),
                    address=place.get("formattedAddress"),
                    latitude=location.get("latitude"),
                    longitude=location.get("longitude"),
                    website=place.get("websiteUri"),
                    phone=place.get("internationalPhoneNumber"),
                    source="google_places",
                    verification_status="Google Places",
                    confidence_score=0.65,
                )
            )

        time.sleep(1)

    logger.info(f"Google Places collection complete: {len(businesses)} unique businesses.")
    return businesses