from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


class DedupeSet:
    def __init__(self, key_fields: list[str] | None = None, path: str | None = None) -> None:
        self.key_fields = key_fields or []
        self.path = Path(path) if path else None
        self.seen: set[str] = set()
        self._load()

    def add(self, item: dict[str, Any]) -> bool:
        key = self._make_key(item)
        if key in self.seen:
            return False
        self.seen.add(key)
        self._append(key)
        return True

    def _make_key(self, item: dict[str, Any]) -> str:
        if self.key_fields:
            values = [item.get(field) for field in self.key_fields]
        else:
            values = item
        raw = json.dumps(values, ensure_ascii=False, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _load(self) -> None:
        if not self.path or not self.path.exists():
            return
        with self.path.open("r", encoding="utf-8") as file:
            self.seen = {line.strip() for line in file if line.strip()}

    def _append(self, key: str) -> None:
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as file:
            file.write(key + "\n")
