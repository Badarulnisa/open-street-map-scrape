"""Verifies/discovers official website when missing or unverified."""
from models.business import Business
from enrichers.serpapi_client import SerpAPIClient
from utils.logger import get_logger

logger = get_logger(__name__)


def enrich_website(business: Business, client: SerpAPIClient) -> None:
    if business.website:
        business.website_verified = business.website
        business.website_confidence = 100
        return

    query = f'"{business.name}" {business.city} official website'
    results = client.search(query, num=3)

    for r in results:
        link = r.get("link", "")
        if link and "linkedin.com" not in link and "facebook.com" not in link:
            business.website_verified = link
            business.website_confidence = 60
            logger.info(f"Website discovered: {link}")
            return

    business.website_confidence = 0