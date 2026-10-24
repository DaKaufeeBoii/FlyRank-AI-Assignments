# The Polite Scraper — Books to Scrape Pipeline

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://python.org)
[![Requests](https://img.shields.io/badge/HTTP-Requests-red)](https://requests.readthedocs.io)
[![BeautifulSoup](https://img.shields.io/badge/HTML-BeautifulSoup4-green)](https://www.crummy.com/software/BeautifulSoup/)
[![Pydantic](https://img.shields.io/badge/Schema-Pydantic%20v2-e92063?logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)

A deterministic, polite, failure-tolerant web scraping pipeline designed to extract structured book data from [Books to Scrape](https://books.toscrape.com), perform schema validation, store clean JSON/CSV records, survive network/page anomalies, and report execution metrics.

---

## Stage 0: Target Classification

| Metric / Dimension | Specification & Finding |
|---|---|
| **Target Website** | `https://books.toscrape.com` (Subdomain of `toscrape.com`) |
| **Site Purpose & Authorization** | As stated directly on `https://toscrape.com`: *"Books: A fictional bookstore that desperately wants to be scraped. It's a safe place for beginners learning web scraping and for developers validating their scraping technologies as well."* This explicit public declaration grants clear permission to scrape this sandbox. |
| **Robots Exclusion Protocol** | Requested `https://books.toscrape.com/robots.txt`: Result was `HTTP 404 Not Found` (**no robots file found**). A missing file is not permission in itself, but indicates no automated crawler restrictions were published by the webmaster. |
| **Scraping Scope** | Exactly the first **3 catalogue pages** (`page-1.html`, `page-2.html`, `page-3.html`), discovering and visiting exactly **60 unique book detail pages**. |
| **Data Collected** | 8 raw attributes (`title`, `product_url`, `price_text`, `availability_text`, `rating_text`, `description`, `source_page`, `fetched_at`) plus normalized numeric `price_gbp`. |
| **Appropriateness Assessment** | The sandbox specifically welcomes scraping traffic; the scope is strictly constrained to 3 pages / 60 books; rate limiting enforces a minimum 500ms delay between real requests; local caching eliminates repetitive load; and no private, copyrighted, or user-sensitive data is processed. |

> **Ethical Commitment:**  
> "I will not reuse this code on another site without checking its rules and terms first."

---
