"""
Books to Scrape - Polite Scraping Pipeline
Stage 2 Entry point: Discover three catalogue pages.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.fetcher import PoliteFetcher
from src.crawler import CatalogueCrawler


def stage_2_discovery():
    print("=== Stage 2: Discover Three Catalogue Pages ===")
    fetcher = PoliteFetcher(cache_dir="cache")
    crawler = CatalogueCrawler(fetcher, max_pages=3)
    
    discovered, catalogue_pages, total_discovered, unique_urls = crawler.discover_books()
    print(f"catalogue_pages={catalogue_pages}, discovered={total_discovered}, unique_urls={unique_urls}")
    return discovered


def main():
    stage_2_discovery()


if __name__ == "__main__":
    main()
