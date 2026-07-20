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

    # Enrichment fields — populated in a later stage. Left as None for now,
    # defined here so the schema doesn't change shape when enrichment lands.
    linkedin: Optional[str] = None
    emails: Optional[str] = None
    employees: Optional[str] = None
    dns_records: Optional[str] = None
    whois_data: Optional[str] = None
    verified: Optional[bool] = None
    social_media: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)