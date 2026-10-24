"""
Unit and Integration Tests for Books to Scrape Polite Pipeline.
Covers:
1. Price normalization
2. Relative -> Absolute URLs resolution
3. Missing description handling (null preservation)
4. Duplicate URLs deduplication (idempotency)
5. Malformed HTML fixture handling
6. Pydantic schema validation
7. CSV export formatting
"""
import os
import pytest
from urllib.parse import urljoin

from src.schema import BookSchema, normalize_price_gbp, normalize_record
from src.extractor import extract_raw_book_record
from src.storage import BookStorage
from src.extras import export_to_csv, detect_changes

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def read_fixture(filename: str) -> str:
    path = os.path.join(FIXTURES_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def test_price_normalization():
    """Verify raw price strings with currency symbols and artifacts convert accurately to floats."""
    assert normalize_price_gbp("£51.77") == 51.77
    assert normalize_price_gbp("£10.00") == 10.00
    assert normalize_price_gbp("Â£42.50") == 42.50
    assert normalize_price_gbp("0.99") == 0.99
    assert normalize_price_gbp("£1,234.56") == 1234.56

    with pytest.raises(ValueError):
        normalize_price_gbp("Free")


def test_relative_to_absolute_urls():
    """Verify relative catalogue URLs are properly resolved using standard urljoin."""
    base_url = "https://books.toscrape.com/catalogue/page-1.html"
    rel_1 = "a-light-in-the-attic_1000/index.html"
    assert urljoin(base_url, rel_1) == "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"

    rel_next = "page-2.html"
    assert urljoin(base_url, rel_next) == "https://books.toscrape.com/catalogue/page-2.html"

    rel_parent = "../tipping-the-velvet_999/index.html"
    assert urljoin(base_url, rel_parent) == "https://books.toscrape.com/tipping-the-velvet_999/index.html"


def test_missing_description_stored_as_none():
    """Verify book without #product_description assigns None and never invents placeholder text."""
    html = read_fixture("sample_book_no_description.html")
    url = "https://books.toscrape.com/catalogue/sample_no_desc/index.html"
    record = extract_raw_book_record(html, product_url=url, source_page="https://books.toscrape.com/catalogue/page-1.html")

    assert record["title"] == "Book With Missing Synopsis"
    assert record["price_text"] == "£14.50"
    assert record["description"] is None
    assert record["rating_text"] == "Two"


def test_whitespace_and_dirty_chars_cleaning():
    """Verify dirty whitespace and Â currency artifacts are cleaned properly."""
    html = read_fixture("sample_book_whitespace_dirty.html")
    url = "https://books.toscrape.com/catalogue/sample_dirty/index.html"
    record = extract_raw_book_record(html, product_url=url, source_page="https://books.toscrape.com/catalogue/page-1.html")

    assert record["title"] == "Wild   Spaces   and   Tides"
    assert record["price_text"] == "£42.00"
    assert record["availability_text"] == "In stock (8 available)"
    assert record["description"] == "An adventure through untamed lands."


def test_malformed_html_fixture():
    """Verify malformed HTML without article.product_page raises clean ValueError."""
    html = read_fixture("sample_book_malformed.html")
    url = "https://books.toscrape.com/catalogue/broken/index.html"
    with pytest.raises(ValueError) as excinfo:
        extract_raw_book_record(html, product_url=url, source_page="https://books.toscrape.com/catalogue/page-1.html")
    assert "article.product_page" in str(excinfo.value)


def test_duplicate_urls_deduplication(tmp_path):
    """Verify identical product URLs are deduplicated idempotently."""
    storage = BookStorage(output_dir=str(tmp_path))
    raw_item = {
        "title": "Clean Architecture",
        "product_url": "https://books.toscrape.com/catalogue/clean-architecture_1/index.html",
        "price_text": "£29.99",
        "availability_text": "In stock (10 available)",
        "rating_text": "Five",
        "description": "Solid designs.",
        "source_page": "https://books.toscrape.com/catalogue/page-1.html",
        "fetched_at": "2026-10-24T12:00:00Z"
    }

    # Pass duplicates in input list
    valid, invalid = storage.validate_and_store([raw_item, raw_item, raw_item])
    assert len(valid) == 1
    assert len(invalid) == 0
    assert valid[0]["price_gbp"] == 29.99


def test_schema_validation_rejects_non_https():
    """Verify BookSchema rejects insecure or malformed non-https URLs."""
    bad_data = {
        "title": "Insecure Book",
        "product_url": "http://books.toscrape.com/catalogue/insecure/index.html",
        "price_text": "£10.00",
        "price_gbp": 10.0,
        "availability_text": "In stock",
        "rating_text": "One",
        "description": None,
        "source_page": "https://books.toscrape.com/catalogue/page-1.html",
        "fetched_at": "2026-10-24T12:00:00Z"
    }
    with pytest.raises(Exception):
        BookSchema(**bad_data)


def test_csv_export_flattens_description(tmp_path):
    """Verify CSV export flattens multiline text cleanly into single cells."""
    records = [{
        "title": "Multiline Book",
        "product_url": "https://books.toscrape.com/catalogue/test/index.html",
        "price_text": "£15.00",
        "price_gbp": 15.00,
        "availability_text": "In stock",
        "rating_text": "Three",
        "description": "Line 1\nLine 2\n\nLine 3",
        "source_page": "https://books.toscrape.com/catalogue/page-1.html",
        "fetched_at": "2026-10-24T12:00:00Z"
    }]
    csv_file = os.path.join(tmp_path, "test.csv")
    export_to_csv(records, csv_file)
    with open(csv_file, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Line 1 Line 2 Line 3" in content
