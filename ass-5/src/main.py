"""
Books to Scrape - Polite Scraping Pipeline
Stage 3 Entry point: Extract raw records from detail pages.
"""
import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.fetcher import PoliteFetcher
from src.crawler import CatalogueCrawler
from src.extractor import extract_raw_book_record, get_book_cache_key


def stage_3_extract_details():
    print("=== Stage 3: Extract the Raw Records ===")
    fetcher = PoliteFetcher(cache_dir="cache")
    crawler = CatalogueCrawler(fetcher, max_pages=3)

    discovered, catalogue_pages, total_discovered, unique_urls = crawler.discover_books()
    print(f"Discovered {unique_urls} books across {catalogue_pages} catalogue pages.")

    raw_records = []
    print("Fetching and extracting detail pages...")
    for item in discovered:
        url = item["product_url"]
        source = item["source_page"]
        cache_key = get_book_cache_key(url)

        html, is_cache, status, size = fetcher.fetch(url, cache_key=cache_key)
        record = extract_raw_book_record(html, product_url=url, source_page=source)
        raw_records.append(record)

    print("\n--- Checkpoint Output: One Complete Raw Record ---")
    print(json.dumps(raw_records[0], indent=2))
    print(f"\ndetail_pages={len(raw_records)}")
    return raw_records


def main():
    stage_3_extract_details()


if __name__ == "__main__":
    main()
