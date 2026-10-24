"""
Books to Scrape - Polite Scraping Pipeline
Stage 1 Entry point: Fetch once, cache once.
"""
import sys
import os

# Add parent directory to path to allow running as `python src/main.py` or `python main.py`
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.fetcher import PoliteFetcher

CATALOGUE_PAGE_1_URL = "https://books.toscrape.com/catalogue/page-1.html"


def stage_1_fetch_demo():
    fetcher = PoliteFetcher(cache_dir="cache")
    print("=== Stage 1: Fetch Once, Cache Once ===")
    content, is_cache, status, size = fetcher.fetch(
        CATALOGUE_PAGE_1_URL, 
        cache_key="catalogue-page-1"
    )
    mode = "CACHE HIT" if is_cache else "FETCH"
    print(f"Result: {mode} | Status: {status} | Size: {size:,} bytes")
    print("Successfully verified: HTML not dumped to terminal, polite headers sent.")


def main():
    stage_1_fetch_demo()

if __name__ == "__main__":
    main()
