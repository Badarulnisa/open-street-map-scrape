"""Facebook, Instagram, X, YouTube, Crunchbase discovery."""
from models.business import Business
from enrichers.serpapi_client import SerpAPIClient
from utils.logger import get_logger

logger = get_logger(__name__)

PLATFORM_MAP = {
    "facebook.com": "facebook_url",
    "instagram.com": "instagram_url",
    "twitter.com": "twitter_url",
    "x.com": "twitter_url",
    "youtube.com": "youtube_url",
    "crunchbase.com": "crunchbase_url",
}


def enrich_socials(business: Business, client: SerpAPIClient) -> None:
    query = f'"{business.name}" {business.city} (facebook OR instagram OR crunchbase)'
    results = client.search(query, num=5)

    found_any = False
    for r in results:
        link = r.get("link", "")
        for domain, field_name in PLATFORM_MAP.items():
            if domain in link and getattr(business, field_name) is None:
                setattr(business, field_name, link)
                found_any = True
                logger.info(f"{field_name}: {link}")

    business.social_confidence = 70 if found_any else 0