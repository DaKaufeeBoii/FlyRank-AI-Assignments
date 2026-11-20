# Assignment 5: The Prompt Ladder
**Track:** General AI Fluency  
**Week:** 2 | **Phase:** Foundations | **Workload:** 2h  
**Author:** Sai Tarun Reddy (`saitarunrdy@gmail.com`)  
**Deliverable Document:** [deliverable.md](./deliverable.md)

---

## 1. Overview & Discipline

The Prompt Ladder forces the discipline of engineering prompts one single layer at a time, evaluating the exact delta in output quality. Changing multiple variables at once hides which instruction produced the result. In this progression, we engineer a prompt to build a resilient, production-grade Python web scraper.

---

## 2. The 6 Runs (Baseline + 5 Incremental Layers)

### Run 0: The Weak Baseline (Embarrassing & Lazy)

#### The Prompt:
```text
Write a python scraper for books.
```

#### Output Excerpt:
```python
import requests
from bs4 import BeautifulSoup

url = "http://books.toscrape.com"
r = requests.get(url)
soup = BeautifulSoup(r.text, 'html.parser')

for book in soup.find_all('article', class_='product_pod'):
    title = book.h3.a['title']
    price = book.find('p', class_='price_color').text
    print(f"Title: {title}, Price: {price}")
```

#### Evaluation:
A fragile 10-line script. Hardcoded single-page URL, zero error handling, unthrottled requests, uncleaned string data (contains `£`), no schema validation, and zero testability.

---

### Run 1: Layer 1 — Adding a Clearer Goal & Scope

#### What Changed in the Prompt (Layer 1):
Added an explicit, measurable objective: scrape multiple catalog pages, extract 8 specific fields, and save to JSON.

#### The Prompt (v1):
```text
Write a python scraper for books.toscrape.com that paginates through the first 3 catalogue pages (60 books total), extracts 8 fields (title, url, price, availability, rating, description, source_page, fetched_at), and saves them into books.json.
```

#### Output Excerpt (v1):
```python
import requests, json
from bs4 import BeautifulSoup
from datetime import datetime

base_url = "http://books.toscrape.com/catalogue/page-{}.html"
books = []
for page in range(1, 4):
    res = requests.get(base_url.format(page))
    soup = BeautifulSoup(res.text, 'html.parser')
    for b in soup.find_all('article', class_='product_pod'):
        # Fetches detail page for description...
        detail_url = "http://books.toscrape.com/catalogue/" + b.h3.a['href']
        d_res = requests.get(detail_url)
        d_soup = BeautifulSoup(d_res.text, 'html.parser')
        books.append({
            "title": b.h3.a['title'],
            "price": b.find('p', class_='price_color').text,
            "description": d_soup.find('meta', attrs={'name': 'description'})['content'],
            "fetched_at": datetime.utcnow().isoformat()
        })
with open("books.json", "w") as f:
    json.dump(books, f, indent=2)
```

#### Four Notes for Version 1:
1. **What Changed in Prompt:** Added explicit goal, 3-page scope (60 books), 8 target fields, and JSON output destination.
2. **What Improved in Output:** The code actually implements pagination and detail page traversal; produces a structured JSON output instead of console print statements.
3. **What Still Failed:** Aggressive unthrottled requests (blasts 63 HTTP requests with zero delay); no error handling; crashes if any page returns a 404; prices are still dirty strings (`"£51.77"`).
4. **What to Try Next:** Add rate-limiting and networking constraints.

---

### Run 2: Layer 2 — Adding Operational Constraints (Rate-Limiting & Caching)

#### What Changed in the Prompt (Layer 2):
Enforced polite crawling rules: User-Agent headers, 500ms delay between requests, 10s timeouts, and local disk caching.

#### The Prompt (v2):
```text
Write a python scraper for books.toscrape.com that paginates through the first 3 catalogue pages (60 books total), extracts 8 fields (title, url, price, availability, rating, description, source_page, fetched_at), and saves them into books.json.

Operational Constraints:
1. Include a descriptive User-Agent header in all requests.
2. Add a minimum 500ms delay (time.sleep) between every external request.
3. Set a strict 10-second timeout on all network calls.
4. Implement a local disk cache directory (.cache/) so already-downloaded HTML files are never re-fetched.
```

#### Output Excerpt (v2):
```python
import os, time, requests, hashlib
from pathlib import Path

CACHE_DIR = Path(".cache")
CACHE_DIR.mkdir(exist_ok=True)
HEADERS = {"User-Agent": "FlyRankIntern-PoliteBot/1.0 (saitarunrdy@gmail.com)"}

def fetch_polite(url: str) -> str:
    cache_file = CACHE_DIR / (hashlib.md5(url.encode()).hexdigest() + ".html")
    if cache_file.exists():
        return cache_file.read_text(encoding="utf-8")
    
    time.sleep(0.5)
    res = requests.get(url, headers=HEADERS, timeout=10)
    res.raise_for_status()
    cache_file.write_text(res.text, encoding="utf-8")
    return res.text
```

#### Four Notes for Version 2:
1. **What Changed in Prompt:** Layered explicit networking boundaries (polite headers, 500ms sleep, caching, timeouts).
2. **What Improved in Output:** Created a dedicated `fetch_polite()` helper with hashing-based disk cache. Safe to re-run locally without spamming the remote server.
3. **What Still Failed:** Data validation is still non-existent; raw dictionaries with unverified schema types; a single corrupt HTML tag or 404 will cause `res.raise_for_status()` to abort the entire script.
4. **What to Try Next:** Enforce typed schema validation using Pydantic.

---

### Run 3: Layer 3 — Adding Specified Output Format & Data Schema (Pydantic v2)

#### What Changed in the Prompt (Layer 3):
Required Pydantic v2 data models with type conversions (cleaning price string to float).

#### The Prompt (v3):
```text
Write a python scraper for books.toscrape.com that paginates through the first 3 catalogue pages (60 books total), extracts 8 fields (title, url, price, availability, rating, description, source_page, fetched_at), and saves them into books.json.

Operational Constraints:
1. Include a descriptive User-Agent header in all requests.
2. Add a minimum 500ms delay (time.sleep) between every external request.
3. Set a strict 10-second timeout on all network calls.
4. Implement a local disk cache directory (.cache/) so already-downloaded HTML files are never re-fetched.

Data Schema (Pydantic v2):
Define a `BookRecord` model. Normalize `price_text` (e.g. "£51.77") into a validated float field `price_gbp: float`. Ensure `title` is non-empty and `rating` is normalized into an integer (1 to 5).
```

#### Output Excerpt (v3):
```python
from pydantic import BaseModel, Field, field_validator
import re

RATING_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}

class BookRecord(BaseModel):
    title: str = Field(min_length=1)
    product_url: str
    price_gbp: float = Field(ge=0.0)
    availability: str
    rating: int = Field(ge=1, le=5)
    description: str
    source_page: str
    fetched_at: str

    @classmethod
    def clean_price(cls, raw: str) -> float:
        cleaned = re.sub(r"[^\d.]", "", raw)
        return float(cleaned)
```

#### Four Notes for Version 3:
1. **What Changed in Prompt:** Added Pydantic v2 schema requirements with type normalization rules (rating mapping, currency regex stripping).
2. **What Improved in Output:** Replaced loose Python dictionaries with validated `BookRecord` instances. Clean, typed numeric values for pricing.
3. **What Still Failed:** The prompt gave no instructions on how to handle failures when an individual book record fails validation or encounters a network error.
4. **What to Try Next:** Add failure isolation and error resilience constraints.

---

### Run 4: Layer 4 — Adding Failure Isolation & Resilience Rules (The Honest "Made It Worse" Moment)

#### What Changed in the Prompt (Layer 4):
Added instructions to catch exceptions and survive broken links without terminating.

#### The Prompt (v4):
```text
[All text from v3]

Failure Resilience & Error Handling:
Never allow a single broken book URL, 404 status, or schema validation error to crash the script. Catch all exceptions inside the book processing loop, log the error, and continue with the next book.
```

#### Output Excerpt (v4):
```python
for book_summary in book_summaries:
    try:
        html = fetch_polite(book_summary.url)
        book = parse_and_validate(html)
        books.append(book)
    except Exception as e:
        # Silently caught to continue
        pass
```

#### Four Notes for Version 4 (The Honest Critique):
1. **What Changed in Prompt:** Instructed AI to catch errors in the loop so broken items don't kill the batch.
2. **What Actually Improved in Output:** The loop wraps individual items in try-except blocks.
3. **What Got WORSE / Failed (Honest Moment):**  
   > ⚠️ **This instruction made the code worse!**  
   > The model generated a dangerous `except Exception: pass` anti-pattern. While the script survived errors, it **silently swallowed all failures without counting them, logging telemetry, or alerting the developer that 50% of the books might be failing**. Silent error suppression is worse than an explicit crash because it gives false confidence in bad data!
4. **What to Try Next:** Explicitly forbid bare exception swallowing; demand structured error telemetry and an execution audit report (`run-report.json`).

---

### Run 5: Layer 5 — Adding Telemetry & Verification Requirements

#### What Changed in the Prompt (Layer 5):
Required execution telemetry tracking (pages visited, cache hits, errors captured with causes) written to `run-report.json`, and an automated CLI test flag (`--test-failure`).

#### The Prompt (v5):
```text
[All text from v3]

Failure Resilience & Execution Telemetry:
1. Wrap individual book parsing in targeted try-except blocks. Do NOT swallow exceptions silently.
2. Track execution metrics: total_pages_visited, cache_hits, total_books_parsed, error_count, and execution_duration_seconds.
3. If a book fails, record its URL and the exact exception reason into an `errors` list.
4. Output a verified `run-report.json` alongside `books.json`.
5. Support a `--test-failure` CLI argument that injects a simulated 404 URL to prove the pipeline records the failure and finishes successfully.
```

#### Output Excerpt (v5):
```python
import argparse, time

telemetry = {
    "start_time": time.time(),
    "pages_visited": 0,
    "cache_hits": 0,
    "books_parsed": 0,
    "errors": []
}

try:
    html = fetch_polite(url)
except requests.HTTPError as e:
    telemetry["errors"].append({"url": url, "error": str(e), "timestamp": time.time()})
    logger.warning(f"Failed to fetch {url}: {e}")
```

#### Four Notes for Version 5:
1. **What Changed in Prompt:** Banned silent exception swallowing; introduced execution metrics, audit reporting, and a test harness flag.
2. **What Improved in Output:** The code is now an enterprise-grade, observable pipeline. Every error is tracked, timed, and audited in `run-report.json`.
3. **What Still Failed:** The prompt is specific to books.toscrape.com; someone on another track would need to rewrite parts of it.
4. **What to Try Next:** Standardize into a modular, production-ready prompt template that any engineer can adapt for their own data source.

---

## 3. Final Reusable Prompt (Production-Ready)

*This is the final polished prompt that any backend engineer can use without me in the room:*

```markdown
# TASK: Build a Resilient, Polite Data Extraction Pipeline in Python

## 1. Core Objective & Scope
Build a deterministic, failure-tolerant web scraper in Python for target site: [INSERT TARGET URL].
Extract structured data across [INSERT PAGINATION RULES] to collect [INSERT EXPECTED COUNT] records.
Output clean records to `output/data.json` and tabular export to `output/data.csv`.

## 2. Operational & Networking Rules (Be Polite)
- Set custom User-Agent identifying the client: `[APP_NAME]/1.0 ([EMAIL])`.
- Enforce a minimum [INSERT SLEEP SECONDS, e.g. 0.5s] delay between real network requests.
- Set a strict 10-second timeout on all HTTP calls.
- Implement file-system disk caching in `.cache/` (keyed by MD5 hash of URL) to eliminate duplicate network hits.

## 3. Data Schema & Typing
- Define a Pydantic v2 `DataRecord` model.
- Strictly normalize and validate all fields (e.g. parse currency strings into `float`, clean whitespace, map ratings/statuses to enums/integers).
- Validate that required fields are non-empty and numerical fields satisfy realistic bounds.

## 4. Failure Tolerance & Observability (Zero Silent Swallowing)
- Isolate record-level processing in try-except blocks: a single 404, DOM change, or validation error must never crash the entire run.
- Record execution telemetry into `output/run-report.json`:
  - `total_requests`, `cache_hits`, `successful_records`, `failed_records`, `duration_seconds`.
  - Detailed log of every caught failure (URL, exception type, error message).
- Support a `--test-failure` flag that injects a simulated broken URL to verify that error handling records the failure without aborting the batch.
```

---

## 4. Pass / Revise Verification

- [x] **Six runs total:** Documented baseline plus 5 incremental versions.
- [x] **One named layer per version:** Goal, Constraints, Pydantic Schema, Resilience, Telemetry.
- [x] **Notes describe output changes:** Focuses on what improved and failed in the actual code generated.
- [x] **Honest "made it worse" moment:** Highlighted Run 4's dangerous `except Exception: pass` silent bug.
- [x] **Final prompt works for a stranger:** Modular, parameterized template suitable for any backend data pipeline.
