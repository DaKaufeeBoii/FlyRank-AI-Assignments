# The Polite Scraper — Books to Scrape Pipeline

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://python.org)
[![Requests](https://img.shields.io/badge/HTTP-Requests-red)](https://requests.readthedocs.io)
[![BeautifulSoup](https://img.shields.io/badge/HTML-BeautifulSoup4-green)](https://www.crummy.com/software/BeautifulSoup/)
[![Pydantic](https://img.shields.io/badge/Schema-Pydantic%20v2-e92063?logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
[![Pytest](https://img.shields.io/badge/Tests-8%20Passed-brightgreen?logo=pytest&logoColor=white)](https://pytest.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A polite, deterministic, failure-tolerant web scraping pipeline engineered to extract structured book data from [Books to Scrape](https://books.toscrape.com), enforce rigorous schema validation, store clean JSON/CSV records, survive network/page anomalies gracefully, and produce an honest execution audit report.

---

## Quick Start (Run in under 2 minutes)

```bash
# 1. Clone the repository and navigate to Assignment 5
git clone https://github.com/DaKaufeeBoii/FlyRank-AI-Assignments.git
cd FlyRank-AI-Assignments/ass-5

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the complete polite scraping pipeline
python main.py

# 4. (Optional) Run the automated unit test suite
python -m pytest -v tests/test_scraper.py

# 5. (Optional) Test failure tolerance (proves 1 broken URL does not kill the run)
python main.py --test-failure
```

Outputs will be generated in `ass-5/output/`:
- `books.json` — 60 validated, unique, normalized book records.
- `books.csv` — Flattened spreadsheet export.
- `run-report.json` — Execution telemetry & honest performance metrics.
- `changes.json` — SHA-256 change detection report.
- `dashboard.html` — Standalone observability dashboard.
- `scraper.log` — Structured JSON lines event audit log.

---

## 1 · Target Classification (Stage 0)

| Metric / Dimension | Specification & Verification |
|---|---|
| **Target Website** | `https://books.toscrape.com` (Subdomain of `toscrape.com`) |
| **Site Purpose & Authorization** | As stated on `https://toscrape.com`: *"Books: A fictional bookstore that desperately wants to be scraped. It's a safe place for beginners learning web scraping and for developers validating their scraping technologies as well."* This explicit public declaration grants clear, unambiguous permission to scrape this sandbox. |
| **Robots Exclusion Protocol** | Requested `https://books.toscrape.com/robots.txt`: Returned `HTTP 404 Not Found` (**no robots file found**). A missing file is not permission in itself, but indicates no automated crawler restrictions were published by the webmaster. |
| **Scraping Scope** | Exactly the first **3 catalogue pages** (`page-1.html`, `page-2.html`, `page-3.html`), discovering and visiting exactly **60 unique book detail pages**. |
| **Data Collected** | 8 raw fields (`title`, `product_url`, `price_text`, `availability_text`, `rating_text`, `description`, `source_page`, `fetched_at`) plus normalized numeric `price_gbp`. |
| **Appropriateness Assessment** | The sandbox specifically welcomes scraping traffic; the scope is strictly constrained to 3 pages / 60 books; rate limiting enforces a minimum 500ms delay between real requests; local caching eliminates repetitive load; and no private, copyrighted, or user-sensitive data is processed. |

> **Ethical Commitment:**  
> *"I will not reuse this code on another site without checking its rules and terms first."*

---

## 2 · The Big Idea: Polite Pipeline Architecture

A professional scraper is not a script that blindly copies strings. It is a deterministic pipeline where every step proves it did its job:

```
[Catalogue Page 1] ---> Follow "next" ---> [Page 2] ---> Follow "next" ---> [Page 3]
       |                                       |                               |
       v                                       v                               v
 [20 Book URLs]                         [20 Book URLs]                  [20 Book URLs]
       \_______________________________________|_______________________________/
                                               |
                                     (60 Unique Book URLs)
                                               |
                                               v
                                   +-----------------------+
                                   |  Polite HTTP Fetcher  |
                                   | - User-Agent Header   |
                                   | - 10s Timeout         |
                                   | - Local Disk Cache    |
                                   | - 500ms Rate Limit    |
                                   +-----------------------+
                                               |
                                               v
                                   +-----------------------+
                                   |    HTML Extractor     |
                                   | - Scoped to Product   |
                                   | - Null Description    |
                                   | - Provenance Stamp    |
                                   +-----------------------+
                                               |
                                               v
                                   +-----------------------+
                                   |  Pydantic Validation  |
                                   | - price_gbp (numeric) |
                                   | - https:// URLs       |
                                   | - Deduplication (Idem)|
                                   +-----------------------+
                                      /                 \
                                [Valid: 60]         [Invalid: 0]
                                    /                     \
                         output/books.json         output/errors.json
                         output/books.csv
                                    \                     /
                                   +-----------------------+
                                   |  Run Audit Reporter   |
                                   | output/run-report.json|
                                   | output/dashboard.html |
                                   +-----------------------+
```

---

## 3 · Politeness Rules Followed

1. **Honest User-Agent:**  
   Every request sends:  
   `User-Agent: FlyRankInternship-A9/1.0 (+https://github.com/DaKaufeeBoii/FlyRank-AI-Assignments)`  
   This clearly identifies the bot and provides a contact link for site administrators.
2. **Defensive Timeout:**  
   Every HTTP request enforces a strict `10.0s` timeout; requests will never hang indefinitely.
3. **HTTP Status Verification:**  
   Only `HTTP 200` is accepted as valid HTML. Missing pages (`404`) and forbidden responses (`403`) are caught immediately and never retried.
4. **Rate Limiting (Polite Delay):**  
   Enforces at least `500ms` between real network requests.
5. **Local Disk Caching (`cache/`):**  
   HTML responses are saved to `cache/`. On subsequent runs, files are read locally with zero network traffic.

---

## 4 · Record Schema & Data Shape

Validated using **Pydantic v2**:

```python
class BookSchema(BaseModel):
    title: str = Field(..., min_length=1, description="Book title")
    product_url: str = Field(..., description="Canonical absolute product URL")
    price_text: str = Field(..., description="Raw price string (e.g. £51.77)")
    price_gbp: float = Field(..., ge=0.0, description="Normalized numeric price in GBP")
    availability_text: str = Field(..., description="Raw availability string")
    rating_text: str = Field(..., description="Star rating word (e.g. One, Two, Three, Four, Five)")
    description: Optional[str] = Field(None, description="Product description or None if absent")
    source_page: str = Field(..., description="Source catalogue page URL for provenance")
    fetched_at: str = Field(..., description="ISO 8601 UTC timestamp of fetch")

    @field_validator("product_url", "source_page")
    @classmethod
    def validate_https_url(cls, v: str) -> str:
        if not v.startswith("https://"):
            raise ValueError(f"URL must start with https://, received: {v}")
        return v
```

### Sample Validated Record (`output/books.json`)

```json
{
  "title": "A Light in the Attic",
  "product_url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
  "price_text": "£51.77",
  "price_gbp": 51.77,
  "availability_text": "In stock (22 available)",
  "rating_text": "Three",
  "description": "It's hard to imagine a world without A Light in the Attic. This now-classic collection of poetry and drawings from Shel Silverstein celebrates its 20th anniversary with this special edition...",
  "source_page": "https://books.toscrape.com/catalogue/page-1.html",
  "fetched_at": "2026-10-24T16:05:51Z"
}
```

---

## 5 · Real Execution Proof (`output/run-report.json`)

Here is an authentic run report generated by the pipeline:

```json
{
  "start_time": "2026-10-24T16:09:31Z",
  "end_time": "2026-10-24T16:09:32Z",
  "duration_seconds": 0.69,
  "pages_fetched": 0,
  "cache_hits": 63,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": 0,
  "failed_urls": []
}
```

### Failure Tolerance Test (`--test-failure`)

When running with `--test-failure`, an invalid URL (`https://books.toscrape.com/catalogue/made-up-broken-book_9999/index.html`) is deliberately injected into the queue:

```
FETCH      https://books.toscrape.com/catalogue/made-up-broken-book_9999/index.html (attempt 1/2) ...
FAILED     https://books.toscrape.com/catalogue/made-up-broken-book_9999/index.html returned HTTP 404 (Non-retryable: will not hammer)
SKIPPED    Failed page: https://books.toscrape.com/catalogue/made-up-broken-book_9999/index.html -> Non-retryable HTTP 404
```

Result:
- The pipeline **did not crash**.
- All **60 valid records survived** in `output/books.json`.
- `output/run-report.json` accurately reported `failed_pages: 1`.

---

## 6 · Why No Browser Was Needed

> **Architectural Decision:**  
> The data on Books to Scrape is already rendered as static HTML delivered directly by the web server; using a headless browser (such as Playwright, Puppeteer, or Selenium) would needlessly consume massive CPU and memory (~120 MB RAM and ~1,250 ms cold boot per instance vs ~0.22 MB RAM and lightweight HTTP sockets) with zero added value.

### Empirical Benchmark (`benchmark_browser.py`)

| Metric | Plain HTTP (`requests`) | Headless Browser (Playwright / Chromium) | Difference |
|---|---|---|---|
| **Peak Memory Used** | **0.22 MB** | ~120.0 MB | **~535x lighter** |
| **Execution Latency** | **~60 ms** (hot socket) | ~1,250 ms | **~20x faster** |
| **System Dependencies** | Standard Python runtime | Chromium binary (~300MB download) | Zero external OS binaries |

---

## 7 · Ethics & Best Practices Note

Web scraping operates under clear professional ethics:
1. **Always prefer an official API:** If the site owner provides a REST, GraphQL, or data export API, use it instead of parsing HTML.
2. **Never bypass authentication, paywalls, or blocks:** Never attempt to circumvent CAPTCHAs, spoof credentials, or evade access controls.
3. **Collect only what is needed:** Scrape strictly the minimal scope necessary; do not mirror entire domains needlessly.
4. **Respect server resources:** Always identify yourself with an honest User-Agent, throttle requests, cache aggressively during development, and obey rate limits.

---

## 8 · Honest Limitation

**Single-Threaded Synchronous Fetching:**  
The pipeline runs synchronously with a single thread and sequential polite delays (`500ms`). While ideal for small jobs (3 pages, 60 books) and strictly polite to the target server, scaling to 100,000+ pages would require an asynchronous worker pool (e.g. `httpx` + `asyncio`) with a distributed rate limiter and queue backing.

---

## 9 · Optional Extras Implemented

1. **CSV Export (`output/books.csv`):**  
   Exports all 60 validated records to a clean CSV. Multiline descriptions and tabs are flattened into clean single-line strings for spreadsheets.
2. **Change Detection (`output/changes.json`):**  
   Maintains a SHA-256 fingerprint of each book record (excluding the fetch timestamp). Reruns compare content hashes and report `new`, `changed`, `unchanged`, or `removed` items.
3. **Observability Dashboard (`output/dashboard.html`):**  
   A standalone, dark-themed HTML dashboard providing metrics on total book counts, price extremes (min, max, average), rating distributions, and pipeline run health.
4. **Automated Unit Test Suite (`tests/test_scraper.py`):**  
   8 comprehensive unit tests covering:
   - Price normalization (e.g., `£51.77`, `Â£42.50`, `£1,234.56`).
   - Relative to absolute URL resolution (`urljoin`).
   - Missing description preservation as `None`.
   - Whitespace and dirty character sanitization.
   - Malformed HTML fixture handling.
   - Duplicate URL deduplication (idempotency).
   - Insecure non-HTTPS URL rejection.
   - Multiline description flattening in CSV.
5. **Pro Retry & Structured Logging (`output/scraper.log`):**  
   Emits structured JSON lines logs with timestamp, event, URL, status, and duration for every request and lifecycle stage.

---

## 10 · Bonus Stage: AI vs Me Rematch

The AI version was generated and quarantined in `ass-5/ai-version/`.

### Checkpoint Comparison

| Metric / Checkpoint | Hand-Built Pipeline | AI Quarantined Version (`ai-version/scraper.py`) |
|---|---|---|
| **Discovered Books** | Exactly 60 (3 catalogue pages) | Exactly 60 (3 catalogue pages) |
| **Validated Records** | Exactly 60 records | Exactly 60 records |
| **Duplicate Prevention** | Canonical URL set deduplication | Dictionary keyed by `product_url` |
| **Idempotent Reruns** | Exactly 60 records on repeated runs | Exactly 60 records on repeated runs |
| **Failure Tolerance** | 1 fake URL skipped, 60 good records saved | 1 fake URL skipped, 60 good records saved |

### Three Concrete Differences

1. **Architecture & Modularity:**  
   - *Me:* Decomposed into clear, testable, decoupled modules (`fetcher.py`, `crawler.py`, `extractor.py`, `schema.py`, `storage.py`, `reporter.py`, `extras.py`).
   - *AI:* Placed everything into a single monolithic script (`ai-version/scraper.py`). While functional, it is harder to unit-test individual components without running the entire loop.
2. **Selector Specificity & Currency Artifacts:**  
   - *Me:* Addressed UTF-8 / ISO-8859-1 decoding anomalies (`response.encoding = 'utf-8'`) directly in the fetch layer and sanitized `Â£` currency artifacts cleanly before schema validation.
   - *AI:* Initially relied on `response.text` without forcing UTF-8, which resulted in dirty `Â£51.77` raw strings on systems using standard requests decoders until explicitly instructed in Rematch Iteration 2.
3. **Observability & Extras:**  
   - *Me:* Built CSV export with text flattening, SHA-256 change detection, structured JSON event logging, and an HTML dashboard.
   - *AI:* Only produced the basic JSON outputs (`ai_books.json` and `ai_run_report.json`).

### Engineering Review Questions

- **What did the AI do better — and do you understand that code?**  
  The AI wrote concise regex patterns for slug extraction (`r"/catalogue/([^/]+)/index\.html"`) and quickly drafted a compact Pydantic validator for HTTPS URLs. The code is clean and fully understood.
- **What did it get wrong or silently skip?**  
  In the initial iteration, the AI skipped provenance fields (`source_page` and `fetched_at`), defaulted missing descriptions to empty strings `""` instead of `None`, and retried all errors unconditionally (including 404s).
- **What did the prompt forget to say?**  
  The initial prompt failed to specify that 404 and 403 status codes must never be retried, that missing descriptions must strictly be `null`, and that catalogue navigation should terminate after exactly 3 pages. Once those constraints were engineered into the Rematch Prompt, the AI produced a robust solution.
