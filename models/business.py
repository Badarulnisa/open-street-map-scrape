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

    # --- Social / web enrichment ---
    linkedin_url: Optional[str] = None
    linkedin_confidence: int = 0
    website_verified: Optional[str] = None
    website_confidence: int = 0
    google_maps_url: Optional[str] = None
    facebook_url: Optional[str] = None
    instagram_url: Optional[str] = None
    twitter_url: Optional[str] = None
    youtube_url: Optional[str] = None
    crunchbase_url: Optional[str] = None
    social_confidence: int = 0

    # --- Company intelligence ---
    company_description: Optional[str] = None
    industry: Optional[str] = None
    headquarters: Optional[str] = None
    email: Optional[str] = None
    company_size: Optional[str] = None
    founded: Optional[str] = None
    careers_url: Optional[str] = None

    # --- Registration status (boss's Apollo.io-style requirement) ---
    registration_status: str = "unverified"   # unverified | registered | unlicensed | unknown
    trade_license_authority: Optional[str] = None  # DED, DMCC, JAFZA, etc.
    registration_confidence: int = 0

    # --- Pipeline metadata ---
    verification_status: str = "OSM"
    confidence_score: float = 0.40
    search_status: str = "pending"   # pending | done | failed | skipped
    search_notes: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)
    @classmethod
    def from_dict(cls, data: dict) -> "Business":
        return cls(**data)