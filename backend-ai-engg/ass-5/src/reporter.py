"""
Run Reporter Module.
Generates output/run-report.json with execution telemetry and honest metrics.
"""
import os
import json
from typing import List, Dict, Any


class RunReporter:
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        self.report_file = os.path.join(self.output_dir, "run-report.json")
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_report(
        self,
        start_time: str,
        end_time: str,
        duration_seconds: float,
        pages_fetched: int,
        cache_hits: int,
        valid_records: int,
        invalid_records: int,
        failed_pages: int,
        failed_urls: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Creates, writes, and returns the run report dictionary.
        """
        report_data = {
            "start_time": start_time,
            "end_time": end_time,
            "duration_seconds": round(duration_seconds, 2),
            "pages_fetched": pages_fetched,
            "cache_hits": cache_hits,
            "valid_records": valid_records,
            "invalid_records": invalid_records,
            "failed_pages": failed_pages,
            "failed_urls": failed_urls
        }

        with open(self.report_file, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        return report_data
