# AI Rematch Prompts

## Iteration 1: Initial Prompt

```text
Write a polite web scraper in Python using requests and BeautifulSoup for https://books.toscrape.com.
Scrape the first 3 catalogue pages and extract all book detail pages.
For each book, extract the title, product_url, price, availability, star rating, and description.
Validate the records with Pydantic and save them to output/books.json.
Include local caching so we don't re-download HTML, wait half a second between requests, and send an identifying user agent.
Do not crash if a page fails. Output a report at the end.
```

### What Iteration 1 Got Wrong or Silently Skipped:
1. **Provenance Fields Omitted:** Did not capture `source_page` or `fetched_at` timestamps because the prompt didn't explicitly mandate provenance keys.
2. **Missing Description Handling:** Hardcoded empty string `""` instead of `None` / `null` when `#product_description` was absent.
3. **Idempotency Flaw:** Used a plain list append rather than keying by canonical `product_url`, causing rerun duplication if cache was bypassed or updated.
4. **Retry Rules:** Retried on all failures indiscriminately including 404 Not Found, rather than respecting HTTP error semantics (no retrying 404/403).

---

## Iteration 2: Rematch Prompt (Engineered Specification)

```text
Build a polite, failure-tolerant web scraping pipeline in Python 3.10+ using requests, BeautifulSoup4, and Pydantic v2 for https://books.toscrape.com.

Strict Requirements:
1. Scope: Start at catalogue/page-1.html and discover subsequent pages by parsing the 'li.next a' link until exactly 3 catalogue pages are traversed (discovering exactly 60 books). Use urllib.parse.urljoin for all relative URLs.
2. Politeness & Network: Send User-Agent 'FlyRankInternship-A9/1.0 (+https://github.com/DaKaufeeBoii/FlyRank-AI-Assignments)', enforce a 10s timeout, check status code 200, and pause at least 500ms between live network requests.
3. Local Caching: Save fetched HTML to cache/ with predictable filenames. On subsequent runs, load from cache and report CACHE HIT with file size without making live HTTP calls.
4. Product Extraction (Targeted Area): Scope selectors strictly to 'article.product_page'. Extract 8 raw fields: title, product_url (canonical absolute URL), price_text (raw £ price), availability_text, rating_text (word string), description (store None if missing, never invent placeholders), source_page (provenance catalogue URL), and fetched_at (ISO 8601 UTC timestamp).
5. Schema Validation & Normalization: Add numeric price_gbp (float parsed from price_text). Validate against Pydantic model requiring https:// URLs. Write valid records idempotently to output/books.json (keyed by canonical product_url) and invalid records to output/errors.json.
6. Failure Tolerance & Retry Policy: Isolate each detail page fetch in a try/except. Retry once on 5xx server errors or timeouts after 1s backoff. NEVER retry 404 or 403 status codes.
7. Run Report: Generate output/run-report.json reporting start_time, end_time, duration_seconds, pages_fetched, cache_hits, valid_records, invalid_records, failed_pages, and failed_urls.
```
