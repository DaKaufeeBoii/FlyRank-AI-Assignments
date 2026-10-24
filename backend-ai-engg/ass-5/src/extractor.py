"""
HTML Extractor for Book Detail Pages.
Extracts 8 raw fields with full provenance.
"""
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import re
from bs4 import BeautifulSoup


def extract_raw_book_record(
    html_content: str, 
    product_url: str, 
    source_page: str, 
    fetched_at: Optional[str] = None
) -> Dict[str, Any]:
    """
    Parses a book detail page HTML and extracts the 8 raw fields.
    Guarantees that selectors target the product area (article.product_page).
    Stores None for missing optional description.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    product_page = soup.select_one("article.product_page")
    if not product_page:
        raise ValueError(f"Target product area 'article.product_page' not found in {product_url}")

    # Title
    title_el = product_page.select_one("h1")
    title = title_el.get_text(strip=True) if title_el else ""

    # Price text (e.g. "£51.77")
    price_el = product_page.select_one("p.price_color")
    raw_price = price_el.get_text(strip=True) if price_el else ""
    price_text = raw_price.replace("\u00c2", "").replace("Â", "").strip()

    # Availability text (e.g. "In stock (22 available)")
    avail_el = product_page.select_one("p.availability")
    if avail_el:
        # Clean multi-line whitespace inside availability block
        availability_text = " ".join(avail_el.get_text().split())
    else:
        availability_text = ""

    # Rating text (e.g. "Three")
    rating_el = product_page.select_one("p.star-rating")
    rating_text = ""
    if rating_el and rating_el.get("class"):
        classes = [c for c in rating_el["class"] if c != "star-rating"]
        if classes:
            rating_text = classes[0]

    # Description (#product_description ~ p) - None if absent
    desc_header = product_page.select_one("#product_description")
    description = None
    if desc_header:
        desc_p = desc_header.find_next_sibling("p")
        if desc_p:
            raw_desc = desc_p.get_text(strip=True)
            description = raw_desc if raw_desc else None

    if not fetched_at:
        fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    return {
        "title": title,
        "product_url": product_url,
        "price_text": price_text,
        "availability_text": availability_text,
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": fetched_at
    }


def get_book_cache_key(product_url: str) -> str:
    """Generates a clean cache key from a book URL."""
    # Example URL: https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html
    match = re.search(r"/catalogue/([^/]+)/index\.html", product_url)
    if match:
        return f"book-{match.group(1)}"
    clean = re.sub(r"[^a-zA-Z0-9_\-]", "_", product_url)
    return f"book-{clean}"
