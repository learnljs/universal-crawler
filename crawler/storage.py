from __future__ import annotations

import csv
import json
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any


class Storage:
    def save_many(self, items: list[dict[str, Any]]) -> int:
        raise NotImplementedError


class JsonlStorage(Storage):
    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save_many(self, items: list[dict[str, Any]]) -> int:
        with self.path.open("a", encoding="utf-8") as file:
            for item in items:
                file.write(json.dumps(item, ensure_ascii=False, default=str) + "\n")
        return len(items)


class CsvStorage(Storage):
    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save_many(self, items: list[dict[str, Any]]) -> int:
        if not items:
            return 0
        fields = sorted({key for item in items for key in item.keys()})
        exists = self.path.exists() and self.path.stat().st_size > 0
        with self.path.open("a", encoding="utf-8-sig", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fields)
            if not exists:
                writer.writeheader()
            writer.writerows(items)
        return len(items)


class SqliteStorage(Storage):
    def __init__(self, path: str, table: str) -> None:
        self.path = Path(path)
        self.table = _quote_sqlite_identifier(table)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save_many(self, items: list[dict[str, Any]]) -> int:
        if not items:
            return 0
        with closing(sqlite3.connect(self.path)) as conn:
            with conn:
                conn.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {self.table} (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        data TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
                conn.executemany(
                    f"INSERT INTO {self.table} (data) VALUES (?)",
                    [(json.dumps(item, ensure_ascii=False, default=str),) for item in items],
                )
        return len(items)


def build_storage(storage_type: str, path: str, table: str = "items") -> Storage:
    normalized = storage_type.lower()
    if normalized == "csv":
        return CsvStorage(path)
    if normalized == "sqlite":
        return SqliteStorage(path, table)
    if normalized == "jsonl":
        return JsonlStorage(path)
    raise ValueError(f"Unsupported storage type: {storage_type}")


def _quote_sqlite_identifier(value: str) -> str:
    identifier = str(value or "items")
    return '"' + identifier.replace('"', '""') + '"'
