"""
Polite HTTP Fetcher with Local Caching, Rate Limiting, and Intelligent Retries.
"""
import os
import time
import requests
from typing import Tuple, Optional

USER_AGENT = "FlyRankInternship-A9/1.0 (+https://github.com/DaKaufeeBoii/FlyRank-AI-Assignments)"
DEFAULT_TIMEOUT = 10.0
MIN_DELAY_SECONDS = 0.5


class NonRetryableHttpError(Exception):
    """Raised when encountering 404, 403 or other non-retryable status codes."""
    def __init__(self, url: str, status_code: int):
        super().__init__(f"Non-retryable HTTP {status_code} for URL: {url}")
        self.url = url
        self.status_code = status_code


class PoliteFetcher:
    def __init__(self, cache_dir: str = "cache", timeout: float = DEFAULT_TIMEOUT, min_delay: float = MIN_DELAY_SECONDS):
        self.cache_dir = cache_dir
        self.timeout = timeout
        self.min_delay = min_delay
        self.last_request_time = 0.0
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Metrics tracking
        self.pages_fetched = 0
        self.cache_hits = 0

    def _url_to_cache_path(self, cache_key: Optional[str], url: str) -> str:
        if cache_key:
            filename = cache_key if cache_key.endswith(".html") else f"{cache_key}.html"
        else:
            clean = url.replace("https://", "").replace("http://", "").replace("/", "_").replace("?", "_").replace("&", "_")
            filename = f"{clean}.html"
        return os.path.join(self.cache_dir, filename)

    def fetch(self, url: str, cache_key: Optional[str] = None, force_refresh: bool = False) -> Tuple[str, bool, int, int]:
        """
        Fetches a URL, reading from cache if available.
        Retries once on timeout or 5xx server error.
        Never retries 404 Not Found or 403 Forbidden.
        Returns: (html_content, is_cache_hit, status_code, size_bytes)
        """
        cache_path = self._url_to_cache_path(cache_key, url)

        # Cache check
        if not force_refresh and os.path.exists(cache_path):
            with open(cache_path, "r", encoding="utf-8") as f:
                content = f.read()
            size = len(content.encode("utf-8"))
            self.cache_hits += 1
            print(f"CACHE HIT  {cache_path} ({size:,} bytes)")
            return content, True, 200, size

        # Network fetch with single polite retry for 5xx/timeouts
        max_attempts = 2
        last_exception = None

        for attempt in range(1, max_attempts + 1):
            # Enforce polite delay between real network requests
            elapsed = time.time() - self.last_request_time
            if elapsed < self.min_delay:
                time.sleep(self.min_delay - elapsed)

            print(f"FETCH      {url} (attempt {attempt}/{max_attempts}) ...")
            self.last_request_time = time.time()

            try:
                response = self.session.get(url, timeout=self.timeout)
                status_code = response.status_code

                if status_code == 200:
                    self.pages_fetched += 1
                    response.encoding = "utf-8"
                    content = response.text
                    size = len(content.encode("utf-8"))

                    with open(cache_path, "w", encoding="utf-8") as f:
                        f.write(content)

                    print(f"SAVED      {cache_path} ({size:,} bytes, HTTP 200)")
                    return content, False, 200, size

                # Strict Rule: Do not retry 404 or 403
                if status_code in (404, 403):
                    print(f"FAILED     {url} returned HTTP {status_code} (Non-retryable: will not hammer)")
                    raise NonRetryableHttpError(url, status_code)

                # Server error (5xx)
                if 500 <= status_code < 600:
                    print(f"WARN       {url} returned HTTP {status_code} server error.")
                    if attempt < max_attempts:
                        time.sleep(1.0)
                        continue
                    raise RuntimeError(f"Server error HTTP {status_code} after {max_attempts} attempts: {url}")

                raise RuntimeError(f"Unexpected status code {status_code} for {url}")

            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                last_exception = e
                print(f"WARN       Network error for {url}: {e}")
                if attempt < max_attempts:
                    print("RETRYING   Waiting 1.0s before polite retry...")
                    time.sleep(1.0)
                    continue
                raise RuntimeError(f"Request failed after {max_attempts} attempts: {e}") from e

        if last_exception:
            raise last_exception
        raise RuntimeError(f"Failed to fetch {url}")
