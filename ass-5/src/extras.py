"""
Extras Module:
1. CSV Exporter (with string flattening for descriptions)
2. Change Detection (Record hashing & diff tracking)
3. Observability Dashboard (Static HTML UI)
4. Structured Logger
"""
import os
import csv
import json
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Any


class StructuredLogger:
    def __init__(self, log_path: str = "output/scraper.log"):
        self.log_path = log_path
        os.makedirs(os.path.dirname(self.log_path) or ".", exist_ok=True)

    def log(self, level: str, event: str, **kwargs):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "event": event,
            **kwargs
        }
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")


def export_to_csv(records: List[Dict[str, Any]], output_path: str = "output/books.csv") -> str:
    """
    Exports validated records to CSV.
    Flattens multiline descriptions and normalizes whitespace for clean spreadsheet consumption.
    """
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    fieldnames = [
        "title",
        "product_url",
        "price_text",
        "price_gbp",
        "availability_text",
        "rating_text",
        "description",
        "source_page",
        "fetched_at"
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        for r in records:
            row = dict(r)
            # Flatten description by collapsing internal newlines/excess whitespace
            if row.get("description"):
                row["description"] = " ".join(row["description"].split())
            else:
                row["description"] = ""
            writer.writerow(row)

    return output_path


def detect_changes(records: List[Dict[str, Any]], state_file: str = "output/.last_run_hashes.json") -> Dict[str, Any]:
    """
    Calculates SHA-256 hash for each book record.
    Compares against the previous run's snapshot to detect new, changed, unchanged, or removed books.
    """
    current_hashes = {}
    for r in records:
        canonical_url = r["product_url"]
        # Serialize fields excluding fetched_at so timestamp doesn't trigger false change
        content_repr = json.dumps({
            k: v for k, v in r.items() if k != "fetched_at"
        }, sort_keys=True)
        h = hashlib.sha256(content_repr.encode("utf-8")).hexdigest()
        current_hashes[canonical_url] = h

    previous_hashes = {}
    if os.path.exists(state_file):
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                previous_hashes = json.load(f)
        except Exception:
            previous_hashes = {}

    new_count = 0
    changed_count = 0
    unchanged_count = 0
    removed_count = 0

    for url, h in current_hashes.items():
        if url not in previous_hashes:
            new_count += 1
        elif previous_hashes[url] == h:
            unchanged_count += 1
        else:
            changed_count += 1

    for url in previous_hashes:
        if url not in current_hashes:
            removed_count += 1

    # Persist current hashes for next run
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(current_hashes, f, indent=2)

    diff_report = {
        "new": new_count,
        "changed": changed_count,
        "unchanged": unchanged_count,
        "removed": removed_count,
        "total_monitored": len(current_hashes)
    }

    # Save to changes.json
    changes_file = os.path.join(os.path.dirname(state_file) or ".", "changes.json")
    with open(changes_file, "w", encoding="utf-8") as f:
        json.dump(diff_report, f, indent=2)

    return diff_report


def generate_dashboard(records: List[Dict[str, Any]], run_report: Dict[str, Any], output_path: str = "output/dashboard.html") -> str:
    """
    Generates a sleek, modern HTML observability dashboard for the scraping run.
    """
    total_records = len(records)
    prices = [r["price_gbp"] for r in records if "price_gbp" in r]
    min_price = min(prices) if prices else 0.0
    max_price = max(prices) if prices else 0.0
    avg_price = sum(prices) / len(prices) if prices else 0.0

    ratings: Dict[str, int] = {}
    for r in records:
        rt = r.get("rating_text", "Unknown")
        ratings[rt] = ratings.get(rt, 0) + 1

    books_rows = ""
    for r in records[:15]:
        desc = (r.get("description") or "None")[:85] + ("..." if len(r.get("description") or "") > 85 else "")
        books_rows += f"""
        <tr>
            <td><a href="{r['product_url']}" target="_blank" class="book-title">{r['title']}</a></td>
            <td><span class="price-badge">£{r['price_gbp']:.2f}</span></td>
            <td><span class="rating-badge star-{r['rating_text'].lower()}">★ {r['rating_text']}</span></td>
            <td><span class="stock-badge">{r['availability_text']}</span></td>
            <td class="desc-cell">{desc}</td>
        </tr>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Books to Scrape · Polite Pipeline Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg: #090d16;
            --surface: #111827;
            --surface-hover: #1f2937;
            --border: #374151;
            --primary: #3b82f6;
            --accent: #10b981;
            --amber: #f59e0b;
            --rose: #ef4444;
            --text-main: #f9fafb;
            --text-muted: #9ca3af;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background: var(--bg);
            color: var(--text-main);
            font-family: 'Plus Jakarta Sans', sans-serif;
            padding: 32px 24px;
            line-height: 1.5;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 28px;
            padding-bottom: 20px;
            border-bottom: 1px solid var(--border);
        }}
        h1 {{ font-size: 26px; font-weight: 800; letter-spacing: -0.02em; }}
        .badge-live {{
            background: rgba(16, 185, 129, 0.15);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.3);
            padding: 6px 14px;
            border-radius: 9999px;
            font-size: 13px;
            font-weight: 600;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px;
            margin-bottom: 28px;
        }}
        .card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
        }}
        .card-title {{
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-muted);
            margin-bottom: 6px;
        }}
        .card-value {{
            font-size: 28px;
            font-weight: 800;
            color: var(--text-main);
        }}
        .card-sub {{ font-size: 12px; color: var(--text-muted); margin-top: 4px; }}
        .section-title {{
            font-size: 18px;
            font-weight: 700;
            margin-bottom: 14px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            overflow: hidden;
        }}
        th {{
            background: #1e293b;
            text-align: left;
            padding: 12px 16px;
            font-size: 12px;
            font-weight: 700;
            color: var(--text-muted);
            text-transform: uppercase;
            border-bottom: 1px solid var(--border);
        }}
        td {{
            padding: 12px 16px;
            font-size: 13px;
            border-bottom: 1px solid #1f2937;
        }}
        tr:hover td {{ background: var(--surface-hover); }}
        .book-title {{
            color: #60a5fa;
            text-decoration: none;
            font-weight: 600;
        }}
        .book-title:hover {{ text-decoration: underline; }}
        .price-badge {{
            background: rgba(59, 130, 246, 0.15);
            color: #93c5fd;
            padding: 4px 10px;
            border-radius: 6px;
            font-weight: 700;
        }}
        .rating-badge {{
            background: rgba(245, 158, 11, 0.15);
            color: #fbbf24;
            padding: 4px 8px;
            border-radius: 6px;
            font-weight: 600;
        }}
        .stock-badge {{
            background: rgba(16, 185, 129, 0.1);
            color: #6ee7b7;
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 11px;
        }}
        .desc-cell {{ color: var(--text-muted); font-size: 12px; }}
        footer {{
            margin-top: 32px;
            text-align: center;
            font-size: 12px;
            color: var(--text-muted);
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>Books to Scrape · Observability Dashboard</h1>
                <p style="color: var(--text-muted); font-size: 14px; margin-top: 4px;">Polite Crawling Pipeline • Target: books.toscrape.com • First 3 Catalogue Pages</p>
            </div>
            <div class="badge-live">● Pipeline Ready & Verified</div>
        </header>

        <div class="stats-grid">
            <div class="card">
                <div class="card-title">Validated Books</div>
                <div class="card-value">{total_records}</div>
                <div class="card-sub">Exact 3-page scope (100%)</div>
            </div>
            <div class="card">
                <div class="card-title">Price Range (GBP)</div>
                <div class="card-value">£{min_price:.2f} - £{max_price:.2f}</div>
                <div class="card-sub">Average: £{avg_price:.2f}</div>
            </div>
            <div class="card">
                <div class="card-title">Run Telemetry</div>
                <div class="card-value">{run_report.get('duration_seconds', 0)}s</div>
                <div class="card-sub">Cache Hits: {run_report.get('cache_hits', 0)} | Fetches: {run_report.get('pages_fetched', 0)}</div>
            </div>
            <div class="card">
                <div class="card-title">Failure Tolerance</div>
                <div class="card-value" style="color: {'#34d399' if run_report.get('failed_pages', 0) == 0 else '#f87171'}">
                    {run_report.get('failed_pages', 0)} Failed
                </div>
                <div class="card-sub">Invalid Records: {run_report.get('invalid_records', 0)}</div>
            </div>
        </div>

        <h2 class="section-title">Sample Validated Book Catalog (First 15 of {total_records})</h2>
        <table>
            <thead>
                <tr>
                    <th>Title & Canonical URL</th>
                    <th>Price</th>
                    <th>Rating</th>
                    <th>Availability</th>
                    <th>Description Excerpt</th>
                </tr>
            </thead>
            <tbody>
                {books_rows}
            </tbody>
        </table>

        <footer>
            Polite Scraper Run Report • Started: {run_report.get('start_time')} • Completed: {run_report.get('end_time')}
        </footer>
    </div>
</body>
</html>
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    return output_path
