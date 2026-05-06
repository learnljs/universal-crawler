from __future__ import annotations

from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any

import yaml


@dataclass(slots=True)
class TaskConfig:
    name: str = "crawler-task"
    purpose: str = "information_collection"
    description: str = ""


@dataclass(slots=True)
class TargetConfig:
    site_name: str = ""
    base_url: str = ""
    entry_urls: list[str] = field(default_factory=list)
    allowed_domains: list[str] = field(default_factory=list)


@dataclass(slots=True)
class RequestConfig:
    method: str = "GET"
    type: str = "static"
    headers: dict[str, str] = field(default_factory=dict)
    cookies: dict[str, str] = field(default_factory=dict)
    params: dict[str, Any] = field(default_factory=dict)
    payload: dict[str, Any] = field(default_factory=dict)
    encoding: str = "auto"
    timeout: dict[str, float] = field(default_factory=lambda: {"connect": 10, "read": 30})


@dataclass(slots=True)
class PaginationConfig:
    enabled: bool = False
    type: str = "none"
    page_param: str = "page"
    start_page: int = 1
    end_page: int = 1
    url_template: str = ""
    next_page_selector: str = ""
    max_pages: int = 1
    cursor_param: str = "cursor"
    cursor_start: str = ""
    next_cursor_path: str = "$.next_cursor"
    stop_when_empty_path: str = "$.data.items"


@dataclass(slots=True)
class StorageConfig:
    type: str = "jsonl"
    path: str = "data/output/items.jsonl"
    table: str = "items"


@dataclass(slots=True)
class RateLimitConfig:
    delay_min: float = 0
    delay_max: float = 0
    concurrency: int = 1


@dataclass(slots=True)
class RetryConfig:
    times: int = 2
    backoff: float = 1
    retry_status: list[int] = field(default_factory=lambda: [429, 500, 502, 503, 504])


@dataclass(slots=True)
class DedupeConfig:
    enabled: bool = True
    type: str = "memory"
    key_fields: list[str] = field(default_factory=list)
    path: str = "data/state/dedupe_keys.txt"


@dataclass(slots=True)
class CrawlerConfig:
    task: TaskConfig
    target: TargetConfig
    request: RequestConfig
    pagination: PaginationConfig
    list_config: dict[str, Any]
    detail: dict[str, Any]
    api: dict[str, Any]
    auth: dict[str, Any]
    browser: dict[str, Any]
    media: dict[str, Any]
    filters: dict[str, Any]
    schedule: dict[str, Any]
    logging: dict[str, Any]
    monitoring: dict[str, Any]
    anti_bot: dict[str, Any]
    cleaning: dict[str, Any]
    dedupe: DedupeConfig
    rate_limit: RateLimitConfig
    retry: RetryConfig
    storage: StorageConfig
    raw: dict[str, Any]

    @classmethod
    def from_yaml(cls, path: Path) -> "CrawlerConfig":
        with path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file) or {}
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CrawlerConfig":
        if not isinstance(data, dict):
            raise ValueError("Top-level crawler config must be a mapping/object")
        return cls(
            task=_build(TaskConfig, data.get("task") or {}),
            target=_build(TargetConfig, data.get("target") or {}),
            request=_build(RequestConfig, data.get("request") or {}),
            pagination=_build(PaginationConfig, data.get("pagination") or {}),
            list_config=data.get("list") or {},
            detail=data.get("detail") or {},
            api=data.get("api") or {},
            auth=data.get("auth") or {},
            browser=data.get("browser") or {},
            media=data.get("media") or {},
            filters=data.get("filters") or {},
            schedule=data.get("schedule") or {},
            logging=data.get("logging") or {},
            monitoring=data.get("monitoring") or {},
            anti_bot=data.get("anti_bot") or {},
            cleaning=data.get("cleaning") or {},
            dedupe=_build(DedupeConfig, data.get("dedupe") or {}),
            rate_limit=_build(RateLimitConfig, data.get("rate_limit") or {}),
            retry=_build(RetryConfig, data.get("retry") or {}),
            storage=_build(StorageConfig, data.get("storage") or {}),
            raw=data,
        )


def _build(cls: type[Any], data: dict[str, Any]) -> Any:
    if not isinstance(data, dict):
        return cls()
    allowed = {item.name for item in fields(cls)}
    filtered = {key: value for key, value in data.items() if key in allowed}
    return cls(**filtered)
