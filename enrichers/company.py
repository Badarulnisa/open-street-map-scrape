"""General company intelligence + UAE registration-status signal."""
import re
from models.business import Business
from enrichers.serpapi_client import SerpAPIClient
from utils.logger import get_logger

logger = get_logger(__name__)

REGISTRATION_AUTHORITIES = ["DED", "DMCC", "JAFZA", "DIFC", "DAFZA", "RAKEZ", "SHAMS", "IFZA"]


def enrich_company(business: Business, client: SerpAPIClient) -> None:
    query = f'"{business.name}" {business.city} company profile'
    results = client.search(query, num=5)

    if results:
        top = results[0]
        business.company_description = top.get("snippet")

    for r in results:
        snippet = (r.get("snippet") or "") + " " + (r.get("title") or "")
        for authority in REGISTRATION_AUTHORITIES:
            if authority in snippet.upper():
                business.registration_status = "registered"
                business.trade_license_authority = authority
                business.registration_confidence = 75
                logger.info(f"Registration signal: {authority}")
                break
        if business.registration_status == "registered":
            break

    # Careers page
    careers_query = f'"{business.name}" careers OR jobs {business.city}'
    careers_results = client.search(careers_query, num=2)
    for r in careers_results:
        link = r.get("link", "")
        if "career" in link.lower() or "job" in link.lower():
            business.careers_url = link
            break

    # Founded year — cheap regex over snippets already fetched
    for r in results:
        snippet = r.get("snippet", "")
        match = re.search(r"\b(19|20)\d{2}\b", snippet)
        if match and "founded" in snippet.lower():
            business.founded = match.group(0)
            break

    if business.registration_status != "registered":
        business.registration_confidence = 20  # no positive signal found, not proof of absence