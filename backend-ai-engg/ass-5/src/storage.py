"""
Storage and Validation Module.
Handles schema validation, deduplication (idempotency), errors segregation, and file storage.
"""
import os
import json
from typing import List, Dict, Any, Tuple
from pydantic import ValidationError

from src.schema import BookSchema, normalize_record


class BookStorage:
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        self.books_file = os.path.join(self.output_dir, "books.json")
        self.errors_file = os.path.join(self.output_dir, "errors.json")
        os.makedirs(self.output_dir, exist_ok=True)

    def validate_and_store(self, raw_records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Validates records against BookSchema.
        Deduplicates by canonical product_url.
        Saves valid records to books.json and invalid records to errors.json.
        Returns: (valid_records, invalid_records)
        """
        valid_map: Dict[str, Dict[str, Any]] = {}
        invalid_records: List[Dict[str, Any]] = []

        for raw in raw_records:
            url = raw.get("product_url", "unknown_url")
            try:
                normalized = normalize_record(raw)
                validated = BookSchema(**normalized)
                # Canonical URL identity deduplication (idempotency)
                valid_map[validated.product_url] = validated.model_dump()
            except (ValidationError, ValueError, Exception) as err:
                invalid_records.append({
                    "raw_record": raw,
                    "reason": str(err)
                })

        valid_list = list(valid_map.values())

        # Write good records (idempotent overwrite)
        with open(self.books_file, "w", encoding="utf-8") as f:
            json.dump(valid_list, f, indent=2, ensure_ascii=False)

        # Write error records
        with open(self.errors_file, "w", encoding="utf-8") as f:
            json.dump(invalid_records, f, indent=2, ensure_ascii=False)

        return valid_list, invalid_records
