"""
Catalogue Crawler for discovering book URLs across catalogue pages.
"""
from typing import List, Tuple, Dict
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from src.fetcher import PoliteFetcher

BASE_CATALOGUE_URL = "https://books.toscrape.com/catalogue/page-1.html"


class CatalogueCrawler:
    def __init__(self, fetcher: PoliteFetcher, max_pages: int = 3):
        self.fetcher = fetcher
        self.max_pages = max_pages

    def discover_books(self, start_url: str = BASE_CATALOGUE_URL) -> Tuple[List[Dict[str, str]], int, int, int]:
        """
        Discovers book URLs up to max_pages following the pagination 'next' link.
        Returns:
            (discovered_items, catalogue_pages_count, total_discovered, unique_urls_count)
            where discovered_items is a list of dicts: {"product_url": ..., "source_page": ...}
        """
        current_url = start_url
        catalogue_pages = 0
        discovered: List[Dict[str, str]] = []
        seen_urls = set()

        while current_url and catalogue_pages < self.max_pages:
            catalogue_pages += 1
            cache_key = f"catalogue-page-{catalogue_pages}"
            html_content, _, _, _ = self.fetcher.fetch(current_url, cache_key=cache_key)

            soup = BeautifulSoup(html_content, "html.parser")

            # Extract book links from product pods
            pods = soup.select("article.product_pod")
            for pod in pods:
                link_el = pod.select_one("h3 a")
                if link_el and link_el.get("href"):
                    relative_href = link_el["href"]
                    # Absolute URL resolution with urljoin
                    absolute_url = urljoin(current_url, relative_href)
                    if absolute_url not in seen_urls:
                        seen_urls.add(absolute_url)
                        discovered.append({
                            "product_url": absolute_url,
                            "source_page": current_url
                        })

            # Follow next link
            next_el = soup.select_one("li.next a")
            if next_el and next_el.get("href"):
                next_rel = next_el["href"]
                current_url = urljoin(current_url, next_rel)
            else:
                current_url = None

        total_discovered = len(discovered)
        unique_urls = len(seen_urls)
        return discovered, catalogue_pages, total_discovered, unique_urls
