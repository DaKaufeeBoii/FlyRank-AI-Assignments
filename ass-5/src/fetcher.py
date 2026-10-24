"""
Polite HTTP Fetcher with Local Caching and Rate Limiting.
"""
import os
import time
import requests
from typing import Tuple, Optional

USER_AGENT = "FlyRankInternship-A9/1.0 (+https://github.com/DaKaufeeBoii/FlyRank-AI-Assignments)"
DEFAULT_TIMEOUT = 10.0
MIN_DELAY_SECONDS = 0.5  # Polite delay between network requests (500 ms)


class PoliteFetcher:
    def __init__(self, cache_dir: str = "cache", timeout: float = DEFAULT_TIMEOUT, min_delay: float = MIN_DELAY_SECONDS):
        self.cache_dir = cache_dir
        self.timeout = timeout
        self.min_delay = min_delay
        self.last_request_time = 0.0
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        os.makedirs(self.cache_dir, exist_ok=True)

    def _url_to_cache_path(self, cache_key: Optional[str], url: str) -> str:
        if cache_key:
            filename = cache_key if cache_key.endswith(".html") else f"{cache_key}.html"
        else:
            # Generate filename from URL
            clean = url.replace("https://", "").replace("http://", "").replace("/", "_").replace("?", "_").replace("&", "_")
            filename = f"{clean}.html"
        return os.path.join(self.cache_dir, filename)

    def fetch(self, url: str, cache_key: Optional[str] = None, force_refresh: bool = False) -> Tuple[str, bool, int, int]:
        """
        Fetches a URL, reading from cache if available.
        Returns: (html_content, is_cache_hit, status_code, size_bytes)
        """
        cache_path = self._url_to_cache_path(cache_key, url)

        # Check Cache
        if not force_refresh and os.path.exists(cache_path):
            with open(cache_path, "r", encoding="utf-8") as f:
                content = f.read()
            size = len(content.encode("utf-8"))
            print(f"CACHE HIT  {cache_path} ({size:,} bytes)")
            return content, True, 200, size

        # Enforce rate limit (polite delay) for actual network calls
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_delay:
            time.sleep(self.min_delay - elapsed)

        print(f"FETCH      {url} ...")
        self.last_request_time = time.time()

        try:
            response = self.session.get(url, timeout=self.timeout)
            status_code = response.status_code
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Request failed for {url}: {e}") from e

        if status_code != 200:
            raise RuntimeError(f"Failed fetch: {url} returned HTTP {status_code} (expected 200)")

        content = response.text
        size = len(content.encode("utf-8"))

        # Save to cache
        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"SAVED      {cache_path} ({size:,} bytes, HTTP {status_code})")
        return content, False, status_code, size
