# The Prompt Ladder — Deliverable
**Intern:** Sai Tarun Reddy  
**Track:** General AI Fluency  
**Assignment Code:** FL-PromptLadder  
**Date:** November 2026  

---

## The 6 Runs (Baseline + 5 Layers)

* **Run 0 (Weak Baseline):** `"Write a python scraper for books."`  
  *Result:* Fragile 10-line script, single page only, no error handling, dirty strings, unthrottled requests.
* **Run 1 (Layer: Clear Goal & Scope):** Added 3-page scope (60 books), 8 named fields, and JSON destination.  
  *Output:* Code traverses pages and details, outputting JSON structure. Failed on unthrottled network and 404 crashes.
* **Run 2 (Layer: Operational Constraints):** Added User-Agent, 500ms sleep delay, 10s timeout, and local disk cache.  
  *Output:* Created `fetch_polite()` with disk caching to prevent spamming target. Failed on data typing and schema validation.
* **Run 3 (Layer: Pydantic v2 Schema):** Added typed `BookRecord` model with regex string-to-float price cleaner.  
  *Output:* Normalized numeric types instead of raw strings. Failed to handle errors when individual items broke.
* **Run 4 (Layer: Resilience & Error Handling — *The "Made It Worse" Moment*):** Instructed AI to catch errors in loop.  
  *Output:* ⚠️ Model generated `except Exception: pass`, which silently swallowed errors without logging. Silent failures are worse than crashes.
* **Run 5 (Layer: Telemetry & Verification):** Banned silent swallowing; added `run-report.json` telemetry and `--test-failure` verification CLI flag.  
  *Output:* Production-grade, observable pipeline tracking error counts, cache ratios, and runtime duration.

---

## Final Reusable Prompt for Backend Engineers

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
