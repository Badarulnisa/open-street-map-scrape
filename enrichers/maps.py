"""Google Maps URL discovery."""
from models.business import Business
from enrichers.serpapi_client import SerpAPIClient
from utils.logger import get_logger

logger = get_logger(__name__)


def enrich_maps(business: Business, client: SerpAPIClient) -> None:
    query = f'"{business.name}" {business.city} site:google.com/maps'
    results = client.search(query, num=2)

    for r in results:
        link = r.get("link", "")
        if "google.com/maps" in link:
            business.google_maps_url = link
            logger.info(f"Google Maps: {link}")
            return