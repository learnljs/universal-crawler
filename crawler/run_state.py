from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class TaskLogger:
    def __init__(self, config: dict[str, Any], task_name: str) -> None:
        self.config = config or {}
        self.enabled = self.config.get("enabled", True)
        self.level = str(self.config.get("level", "INFO")).upper()
        log_dir = Path(self.config.get("dir", "data/logs"))
        log_dir.mkdir(parents=True, exist_ok=True)
        self.request_log = Path(self.config.get("request_log", log_dir / f"{task_name}_requests.jsonl"))
        self.error_log = Path(self.config.get("error_log", log_dir / f"{task_name}_errors.jsonl"))
        self.summary_log = Path(self.config.get("summary_log", log_dir / f"{task_name}_summary.jsonl"))
        for path in (self.request_log, self.error_log, self.summary_log):
            path.parent.mkdir(parents=True, exist_ok=True)

    def request(self, event: str, **payload: Any) -> None:
        self._write(self.request_log, event, payload)

    def error(self, event: str, **payload: Any) -> None:
        self._write(self.error_log, event, payload)

    def summary(self, **payload: Any) -> None:
        self._write(self.summary_log, "summary", payload)

    def _write(self, path: Path, event: str, payload: dict[str, Any]) -> None:
        if not self.enabled:
            return
        record = {
            "ts": datetime.now().isoformat(timespec="seconds"),
            "event": event,
            **payload,
        }
        with path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")


class ResumeState:
    def __init__(self, config: dict[str, Any], task_name: str) -> None:
        self.config = config or {}
        self.enabled = bool(self.config.get("enabled", False))
        state_dir = Path(self.config.get("dir", "data/state"))
        state_dir.mkdir(parents=True, exist_ok=True)
        self.completed_path = Path(
            self.config.get("completed_path", state_dir / f"{task_name}_completed_urls.txt")
        )
        self.failed_path = Path(self.config.get("failed_path", state_dir / f"{task_name}_failed.jsonl"))
        self.retry_failed_first = bool(self.config.get("retry_failed_first", False))
        self.clear_failed_on_success = bool(self.config.get("clear_failed_on_success", True))
        self.completed: set[str] = set()
        self.failed_records: list[dict[str, Any]] = []
        self._load()

    def should_skip(self, key: str) -> bool:
        return self.enabled and key in self.completed

    def mark_completed(self, key: str) -> None:
        if not self.enabled or key in self.completed:
            return
        self.completed.add(key)
        self.completed_path.parent.mkdir(parents=True, exist_ok=True)
        with self.completed_path.open("a", encoding="utf-8") as file:
            file.write(key + "\n")

    def mark_failed(self, key: str, url: str, params: dict[str, Any] | None, error: Exception) -> None:
        if not self.enabled:
            return
        self.failed_path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "ts": datetime.now().isoformat(timespec="seconds"),
            "key": key,
            "url": url,
            "params": params or {},
            "error": str(error),
        }
        with self.failed_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")

    def failed_page_requests(self) -> list[Any]:
        if not self.enabled or not self.retry_failed_first:
            return []
        from crawler.paginator import PageRequest

        output = []
        for record in self.failed_records:
            key = record.get("key")
            if key and key not in self.completed:
                output.append(PageRequest(record["url"], record.get("params") or {}))
        return output

    def _load(self) -> None:
        if not self.enabled:
            return
        if self.completed_path.exists():
            with self.completed_path.open("r", encoding="utf-8") as file:
                self.completed = {line.strip() for line in file if line.strip()}
        if self.failed_path.exists():
            with self.failed_path.open("r", encoding="utf-8") as file:
                for line in file:
                    if not line.strip():
                        continue
                    try:
                        self.failed_records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue


def page_key(url: str, params: dict[str, Any] | None = None) -> str:
    params = params or {}
    if not params:
        return url
    encoded = json.dumps(params, ensure_ascii=False, sort_keys=True, default=str)
    return f"{url}::{encoded}"
