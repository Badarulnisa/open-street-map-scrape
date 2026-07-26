"""
Collects businesses from the SHAMS (Sharjah Media City) public company
directory: https://www.shams.ae/community/company-directory

IMPORTANT — before running this for real data collection (not just demo):
1. CSS selectors below are PLACEHOLDERS. They must be verified against the
   live page's actual DOM structure (right-click -> Inspect a real listing)
   before this will return real data.
2. Terms of Service on shams.ae have NOT been confirmed to permit automated
   collection. robots.txt was checked and does not block this path, but
   robots.txt alone does not guarantee ToS compliance (see DMCC precedent,
   which explicitly forbids directory reproduction despite an open
   robots.txt). Confirm ToS before scaling this beyond a demo.
"""
import time
from typing import Optional

import requests
from bs4 import BeautifulSoup

import config
from models.business import Business
from utils.logger import get_logger

logger = get_logger(__name__)

DIRECTORY_URL = "https://www.shams.ae/community/company-directory"
REQUEST_DELAY_SECONDS = 2
REQUEST_TIMEOUT_SECONDS = 15
MAX_RETRIES = 3
MAX_PAGES = 50  # safety cap; adjust once real pagination behavior is known


def _fetch_page(page: int) -> Optional[str]:
    params = {"page": page}
    headers = {"User-Agent": "Mozilla/5.0 (compatible; OSINT-research-bot/1.0)"}

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(
                DIRECTORY_URL,
                params=params,
                headers=headers,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as exc:
            logger.warning(f"SHAMS directory fetch failed (page {page}, attempt {attempt}): {exc}")
            time.sleep(2 ** attempt)

    logger.error(f"SHAMS directory permanently failed for page {page}.")
    return None


def _parse_listings(html: str) -> list[dict]:
    """
    PLACEHOLDER SELECTORS — verify against the real page before use.
    Right-click -> Inspect on an actual company-directory listing at
    shams.ae/community/company-directory and update the selectors below
    to match reality.
    """
    soup = BeautifulSoup(html, "html.parser")
    listings = []

    for card in soup.select(".directory-listing"):  # <-- verify this selector
        name_el = card.select_one(".company-name")           # <-- verify
        category_el = card.select_one(".client-type")        # <-- verify
        website_el = card.select_one(".company-website a")   # <-- verify

        if not name_el:
            continue

        listings.append({
            "name": name_el.get_text(strip=True),
            "category": category_el.get_text(strip=True) if category_el else None,
            "website": website_el.get("href") if website_el else None,
        })

    return listings


def collect(geofence_key: str) -> list[Business]:
    city_label = "Sharjah"
    businesses: list[Business] = []
    seen_names: set[str] = set()

    for page in range(1, MAX_PAGES + 1):
        html = _fetch_page(page)
        if not html:
            break

        listings = _parse_listings(html)
        if not listings:
            logger.info(f"SHAMS directory: page {page} returned no listings, stopping.")
            break

        for listing in listings:
            key = listing["name"].lower()
            if key in seen_names:
                continue
            seen_names.add(key)

            businesses.append(
                Business(
                    name=listing["name"],
                    city=city_label,
                    category=listing.get("category"),
                    website=listing.get("website"),
                    source="shams_directory",
                    verification_status="SHAMS",
                    confidence_score=0.6,
                    registration_status="registered",
                    trade_license_authority="SHAMS",
                    registration_confidence=80,
                )
            )

        time.sleep(REQUEST_DELAY_SECONDS)

    logger.info(f"SHAMS directory collection complete: {len(businesses)} unique businesses.")
    return businesses