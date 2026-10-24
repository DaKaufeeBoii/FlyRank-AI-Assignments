"""
Quarantined AI Version Scraper (Rematch Iteration 2).
Generated from structured specification prompt.
"""
import os
import re
import time
import json
from datetime import datetime, timezone
from urllib.parse import urljoin
from typing import Optional, List, Dict, Any

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field, field_validator

USER_AGENT = "FlyRankInternship-A9/1.0 (+https://github.com/DaKaufeeBoii/FlyRank-AI-Assignments)"
TIMEOUT = 10.0
MIN_DELAY = 0.5


class AIQuarantineBookModel(BaseModel):
    title: str
    product_url: str
    price_text: str
    price_gbp: float = Field(..., ge=0.0)
    availability_text: str
    rating_text: str
    description: Optional[str] = None
    source_page: str
    fetched_at: str

    @field_validator("product_url", "source_page")
    @classmethod
    def check_https(cls, v: str) -> str:
        if not v.startswith("https://"):
            raise ValueError(f"Insecure or invalid URL: {v}")
        return v


class AIScraperPipeline:
    def __init__(self, cache_dir: str = "cache", output_dir: str = "output"):
        self.cache_dir = cache_dir
        self.output_dir = output_dir
        self.last_req_time = 0.0
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)

        self.pages_fetched = 0
        self.cache_hits = 0

    def polite_get(self, url: str, cache_name: str) -> Tuple[str, bool]:
        cache_path = os.path.join(self.cache_dir, f"{cache_name}.html")
        if os.path.exists(cache_path):
            with open(cache_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.cache_hits += 1
            return content, True

        for attempt in (1, 2):
            elapsed = time.time() - self.last_req_time
            if elapsed < MIN_DELAY:
                time.sleep(MIN_DELAY - elapsed)

            self.last_req_time = time.time()
            try:
                res = self.session.get(url, timeout=TIMEOUT)
                if res.status_code == 200:
                    self.pages_fetched += 1
                    res.encoding = "utf-8"
                    with open(cache_path, "w", encoding="utf-8") as f:
                        f.write(res.text)
                    return res.text, False
                if res.status_code in (404, 403):
                    raise RuntimeError(f"HTTP {res.status_code} Non-retryable: {url}")
                if attempt == 1 and 500 <= res.status_code < 600:
                    time.sleep(1.0)
                    continue
                raise RuntimeError(f"HTTP {res.status_code} for {url}")
            except (requests.Timeout, requests.ConnectionError):
                if attempt == 1:
                    time.sleep(1.0)
                    continue
                raise

        raise RuntimeError(f"Failed to fetch {url}")

    def run(self):
        start_ts = time.time()
        start_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Discover
        current_page = "https://books.toscrape.com/catalogue/page-1.html"
        discovered = []
        pages_seen = 0

        while current_page and pages_seen < 3:
            pages_seen += 1
            html, _ = self.polite_get(current_page, f"ai-catalogue-page-{pages_seen}")
            soup = BeautifulSoup(html, "html.parser")
            for pod in soup.select("article.product_pod"):
                link = pod.select_one("h3 a")
                if link and link.get("href"):
                    discovered.append({
                        "product_url": urljoin(current_page, link["href"]),
                        "source_page": current_page
                    })
            next_a = soup.select_one("li.next a")
            current_page = urljoin(current_page, next_a["href"]) if next_a else None

        records_map = {}
        errors = []
        failed_pages = 0
        failed_urls = []

        for item in discovered:
            url = item["product_url"]
            source = item["source_page"]
            slug_match = re.search(r"/catalogue/([^/]+)/index\.html", url)
            slug = slug_match.group(1) if slug_match else "unknown"

            try:
                html, _ = self.polite_get(url, f"ai-book-{slug}")
                soup = BeautifulSoup(html, "html.parser")
                prod = soup.select_one("article.product_page")
                if not prod:
                    raise ValueError("Missing article.product_page")

                title = prod.select_one("h1").get_text(strip=True)
                raw_price = prod.select_one("p.price_color").get_text(strip=True)
                clean_price_text = raw_price.replace("Â", "").strip()

                p_match = re.search(r"(\d+(?:\.\d+)?)", clean_price_text)
                price_gbp = round(float(p_match.group(1)), 2) if p_match else 0.0

                avail = " ".join(prod.select_one("p.availability").get_text().split())
                rating_classes = prod.select_one("p.star-rating").get("class", [])
                rating = [c for c in rating_classes if c != "star-rating"][0] if rating_classes else ""

                desc_h = prod.select_one("#product_description")
                desc = None
                if desc_h:
                    desc_sib = desc_h.find_next_sibling("p")
                    desc = desc_sib.get_text(strip=True) if desc_sib else None

                record_data = {
                    "title": title,
                    "product_url": url,
                    "price_text": clean_price_text,
                    "price_gbp": price_gbp,
                    "availability_text": avail,
                    "rating_text": rating,
                    "description": desc,
                    "source_page": source,
                    "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                }

                validated = AIQuarantineBookModel(**record_data)
                records_map[validated.product_url] = validated.model_dump()
            except Exception as e:
                failed_pages += 1
                failed_urls.append({"url": url, "error": str(e)})

        # Save books
        with open(os.path.join(self.output_dir, "ai_books.json"), "w", encoding="utf-8") as f:
            json.dump(list(records_map.values()), f, indent=2, ensure_ascii=False)

        duration = time.time() - start_ts
        report = {
            "start_time": start_iso,
            "end_time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "duration_seconds": round(duration, 2),
            "pages_fetched": self.pages_fetched,
            "cache_hits": self.cache_hits,
            "valid_records": len(records_map),
            "failed_pages": failed_pages,
            "failed_urls": failed_urls
        }
        with open(os.path.join(self.output_dir, "ai_run_report.json"), "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        print(f"[AI-Version] Finished: Valid records={len(records_map)}, Failed pages={failed_pages}")
        return report


if __name__ == "__main__":
    AIScraperPipeline().run()
