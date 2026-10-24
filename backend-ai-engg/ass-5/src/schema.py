"""
Pydantic Schema and Normalization for Book Records.
"""
from typing import Optional, Dict, Any
import re
from pydantic import BaseModel, Field, field_validator, ValidationError


class BookSchema(BaseModel):
    title: str = Field(..., min_length=1, description="Book title")
    product_url: str = Field(..., description="Canonical absolute product URL")
    price_text: str = Field(..., description="Raw price string, e.g. £51.77")
    price_gbp: float = Field(..., ge=0.0, description="Normalized numeric price in GBP")
    availability_text: str = Field(..., description="Raw availability string")
    rating_text: str = Field(..., description="Rating word (e.g. One, Two, Three, Four, Five)")
    description: Optional[str] = Field(None, description="Product description or None if absent")
    source_page: str = Field(..., description="Source catalogue page URL for provenance")
    fetched_at: str = Field(..., description="ISO 8601 UTC timestamp of fetch")

    @field_validator("product_url", "source_page")
    @classmethod
    def validate_https_url(cls, v: str) -> str:
        if not v.startswith("https://"):
            raise ValueError(f"URL must start with https://, received: {v}")
        return v


def normalize_price_gbp(price_text: str) -> float:
    """
    Parses currency strings like '£51.77' or '51.77' into a float 51.77.
    """
    cleaned = price_text.replace("£", "").replace("Â", "").replace(",", "").strip()
    match = re.search(r"(\d+(?:\.\d+)?)", cleaned)
    if not match:
        raise ValueError(f"Unable to parse numeric price from text: '{price_text}'")
    return round(float(match.group(1)), 2)


def normalize_record(raw_record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Takes a raw 8-field record, normalizes the price into price_gbp,
    and returns a combined dictionary ready for schema validation.
    """
    normalized = dict(raw_record)
    price_text = normalized.get("price_text", "")
    normalized["price_gbp"] = normalize_price_gbp(price_text)
    return normalized
