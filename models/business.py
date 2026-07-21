"""
Canonical Business record. Every collector must return a list[Business].
This is the contract the merger and all downstream stages rely on.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Business:
    name: str
    city: str
    area: Optional[str] = None
    category: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    source: str = "unknown"

    # Enrichment fields — populated in a later stage.
    linkedin_url: Optional[str] = None
    emails: Optional[str] = None
    employees: Optional[str] = None
    dns_records: Optional[str] = None
    whois_data: Optional[str] = None
    social_media: Optional[str] = None

    # Verification/confidence — every collector sets a baseline; later
    # sources (website confirmed, Google Places match, manual check) raise it.
    verification_status: str = "OSM"
    confidence_score: float = 0.40

    def to_dict(self) -> dict:
        return asdict(self)