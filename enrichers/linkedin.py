"""LinkedIn company page discovery via SerpAPI (never scrapes LinkedIn directly)."""
from models.business import Business
from enrichers.serpapi_client import SerpAPIClient
from utils.logger import get_logger

logger = get_logger(__name__)


def enrich_linkedin(business: Business, client: SerpAPIClient) -> None:
    query = f'site:linkedin.com/company "{business.name}" {business.city}'
    results = client.search(query, num=3)

    for r in results:
        link = r.get("link", "")
        if "linkedin.com/company" in link:
            business.linkedin_url = link
            business.linkedin_confidence = 90 if business.name.lower() in r.get("title", "").lower() else 65
            logger.info(f"LinkedIn found: {link} (confidence {business.linkedin_confidence})")
            return

    business.linkedin_confidence = 0
    logger.info("LinkedIn: no result")