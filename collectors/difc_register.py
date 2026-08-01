"""
Collects companies from the DIFC (Dubai International Financial Centre)
Public Register: https://www.difc.com/business/public-register

Backend: Salesforce Experience Cloud, custom Apex REST endpoint.
Confirmed via live DevTools inspection and manual endpoint testing
(2026-08-01):
- offset-based pagination confirmed real (non-overlapping pages at
  offset 0/10/20/30)
- no hard ceiling near Salesforce's typical OFFSET<=2000 governor limit
  (offset=1990 returned a normal, fresh page)
- end-of-dataset behavior confirmed: past the real end, the API returns
  {"Data": null, "IsSuccess": true, "StatusCode": 200} -- NOT an empty
  companyList and NOT an error. This is handled explicitly below.

NOTE: No explicit reproduction/scraping prohibition was found on this
page (unlike DMCC's directory, which explicitly forbids it). This is a
public government-adjacent regulatory register (DIFC, regulated by the
DFSA). Confirm DIFC's own Terms of Use independently before running this
at full volume in a production context -- this collector was built after
confirming the technical mechanism only, not after a full legal review.
"""
import time
from typing import Optional

import requests

import config
from models.business import Business
from utils.logger import get_logger

logger = get_logger(__name__)

DIFC_ENDPOINT = "https://www.difc.com/api/handleRequest"
PAGE_SIZE = 10  # confirmed empirically -- companyList returns exactly 10 per call
REQUEST_TIMEOUT_SECONDS = 15
REQUEST_DELAY_SECONDS = 1.5  # be polite -- no documented rate limit, so we self-impose one
MAX_RETRIES = 3
MAX_PAGES = 1000  # safety cap -- DIFC reports ~8,844 companies / 10 per page ~= 885 pages


def _fetch_page(offset: int) -> Optional[list[dict]]:
    payload = {
        "name": "",
        "licenseType": "",
        "licenseNo": "",
        "status": "",
        "offset": offset,
        "slug": "/CRM/public-register",
        "method": "POST",
    }
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (compatible; OSINT-research-bot/1.0)",
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.post(
                DIFC_ENDPOINT,
                json=payload,
                headers=headers,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            resp.raise_for_status()
            data = resp.json()

            if not data.get("IsSuccess", False):
                logger.warning(
                    f"DIFC register returned IsSuccess=false at offset {offset}: "
                    f"{data.get('Message')}"
                )
                return None

            result_data = data.get("Data")
            if result_data is None:
                # Confirmed behavior: end of dataset returns Data:null with
                # IsSuccess:true, NOT an empty list and NOT an error. This is
                # the legitimate "we've reached the end" signal, not a failure.
                logger.info(
                    f"DIFC register: Data=null at offset {offset} -- "
                    f"reached end of register."
                )
                return []

            return result_data.get("companyList", [])

        except requests.RequestException as exc:
            logger.warning(f"DIFC register fetch failed (offset {offset}, attempt {attempt}): {exc}")
            time.sleep(2 ** attempt)

    logger.error(f"DIFC register permanently failed at offset {offset}.")
    return None


def collect(geofence_key: str = "dubai") -> list[Business]:
    """DIFC is a Dubai financial free zone -- city is always Dubai
    regardless of which geofence the rest of the pipeline is running."""
    businesses: list[Business] = []
    offset = 0
    page_num = 0

    while page_num < MAX_PAGES:
        page_num += 1
        logger.info(f"DIFC register: fetching offset {offset} (page {page_num})...")
        companies = _fetch_page(offset)

        if companies is None:
            logger.warning(f"DIFC register: stopping due to fetch failure at offset {offset}.")
            break

        if not companies:
            logger.info(f"DIFC register: empty result at offset {offset} -- reached end of register.")
            break

        for company in companies:
            name = company.get("Name")
            if not name:
                continue

            businesses.append(
                Business(
                    name=name,
                    city="Dubai",
                    category=company.get("Company_Type__c"),
                    address=company.get("Registered_Address__c"),
                    website=company.get("Website"),
                    source="difc_register",
                    verification_status="DIFC",
                    confidence_score=0.9,  # official regulatory register, highest-confidence source found
                    registration_status=(
                        "registered" if company.get("ROC_Status__c") == "Active" else "deregistered"
                    ),
                    trade_license_authority="DIFC",
                    registration_confidence=95,
                    founded=company.get("ROC_reg_incorp_Date__c"),
                    industry=company.get("Nature_of_business__c") or company.get("License_Activity_Details__c"),
                    company_description=company.get("License_Activity_Details__c"),
                    search_notes=(
                        f"License #{company.get('Registration_License_No__c')}, "
                        f"status: {company.get('ROC_Status__c')}, "
                        f"entity type: {company.get('Legal_Entity_Type__c')}"
                    ),
                )
            )

        offset += PAGE_SIZE
        time.sleep(REQUEST_DELAY_SECONDS)

    logger.info(f"DIFC register collection complete: {len(businesses)} companies across {page_num} pages.")
    return businesses