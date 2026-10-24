"""
Books to Scrape - Polite Scraping Pipeline
Stage 5 Entry point: Survive failures, isolate errors, and generate run report.
"""
import sys
import os
import time
import argparse
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.fetcher import PoliteFetcher
from src.crawler import CatalogueCrawler
from src.extractor import extract_raw_book_record, get_book_cache_key
from src.storage import BookStorage
from src.reporter import RunReporter


def run_pipeline(inject_fake_url: bool = False):
    start_dt = datetime.now(timezone.utc)
    start_time_iso = start_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    start_ts = time.time()

    print("=== Books to Scrape - Polite Pipeline ===")
    if inject_fake_url:
        print("[TEST MODE] Injecting 1 deliberately fake URL to prove failure tolerance...")

    fetcher = PoliteFetcher(cache_dir="cache")
    crawler = CatalogueCrawler(fetcher, max_pages=3)
    storage = BookStorage(output_dir="output")
    reporter = RunReporter(output_dir="output")

    # Step 1: Discover catalogue pages and book links
    discovered, catalogue_pages, total_discovered, unique_urls = crawler.discover_books()
    print(f"Discovered {unique_urls} books across {catalogue_pages} catalogue pages.")

    # Inject fake URL if testing failure
    if inject_fake_url:
        fake_book = {
            "product_url": "https://books.toscrape.com/catalogue/made-up-broken-book_9999/index.html",
            "source_page": "https://books.toscrape.com/catalogue/page-1.html"
        }
        discovered.append(fake_book)

    # Step 2: Detail page processing with per-page error isolation
    raw_records = []
    failed_pages = 0
    failed_urls = []

    for item in discovered:
        url = item["product_url"]
        source = item["source_page"]
        cache_key = get_book_cache_key(url)

        try:
            html, is_cache, status, size = fetcher.fetch(url, cache_key=cache_key)
            record = extract_raw_book_record(html, product_url=url, source_page=source)
            raw_records.append(record)
        except Exception as err:
            failed_pages += 1
            err_msg = str(err)
            print(f"SKIPPED    Failed page: {url} -> {err_msg}")
            failed_urls.append({"url": url, "error": err_msg})

    # Step 3: Validate and store
    valid_records, invalid_records = storage.validate_and_store(raw_records)

    end_dt = datetime.now(timezone.utc)
    end_time_iso = end_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    duration = time.time() - start_ts

    # Step 4: Write run report
    report = reporter.generate_report(
        start_time=start_time_iso,
        end_time=end_time_iso,
        duration_seconds=duration,
        pages_fetched=fetcher.pages_fetched,
        cache_hits=fetcher.cache_hits,
        valid_records=len(valid_records),
        invalid_records=len(invalid_records),
        failed_pages=failed_pages,
        failed_urls=failed_urls
    )

    print("\n--- Checkpoint Stage 5 Run Report Summary ---")
    print(f"Duration:         {report['duration_seconds']}s")
    print(f"Pages Fetched:    {report['pages_fetched']}")
    print(f"Cache Hits:       {report['cache_hits']}")
    print(f"Valid Records:    {report['valid_records']}")
    print(f"Invalid Records:  {report['invalid_records']}")
    print(f"Failed Pages:     {report['failed_pages']}")
    print(f"Report written to: output/run-report.json")

    return report


def main():
    parser = argparse.ArgumentParser(description="Polite Scraper for Books to Scrape")
    parser.add_argument("--test-failure", action="store_true", help="Inject one fake broken URL to prove failure tolerance")
    args = parser.parse_args()

    run_pipeline(inject_fake_url=args.test_failure)


if __name__ == "__main__":
    main()
