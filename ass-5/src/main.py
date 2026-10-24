"""
Books to Scrape - Polite Scraping Pipeline
Stage 4 Entry point: Validate normalized records and store idempotently.
"""
import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.fetcher import PoliteFetcher
from src.crawler import CatalogueCrawler
from src.extractor import extract_raw_book_record, get_book_cache_key
from src.storage import BookStorage


def run_pipeline():
    print("=== Stage 4: Clean It, Check It, Store It ===")
    fetcher = PoliteFetcher(cache_dir="cache")
    crawler = CatalogueCrawler(fetcher, max_pages=3)
    storage = BookStorage(output_dir="output")

    discovered, catalogue_pages, total_discovered, unique_urls = crawler.discover_books()
    print(f"Discovered {unique_urls} books across {catalogue_pages} catalogue pages.")

    raw_records = []
    for item in discovered:
        url = item["product_url"]
        source = item["source_page"]
        cache_key = get_book_cache_key(url)

        html, is_cache, status, size = fetcher.fetch(url, cache_key=cache_key)
        record = extract_raw_book_record(html, product_url=url, source_page=source)
        raw_records.append(record)

    valid_records, invalid_records = storage.validate_and_store(raw_records)

    # Verification checks
    books_count = len(valid_records)
    all_prices_numeric = all(isinstance(r["price_gbp"], (float, int)) for r in valid_records)
    all_urls_https = all(r["product_url"].startswith("https://") for r in valid_records)

    print("\n--- Checkpoint Stage 4 Results ---")
    print(f"Stored valid books count: {books_count}")
    print(f"All price_gbp are numeric: {all_prices_numeric}")
    print(f"All URLs start with https://: {all_urls_https}")
    print(f"Invalid records stored in errors.json: {len(invalid_records)}")
    return valid_records


def main():
    run_pipeline()


if __name__ == "__main__":
    main()
