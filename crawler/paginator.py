from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from crawler.config import PaginationConfig


@dataclass(slots=True)
class PageRequest:
    url: str
    params: dict[str, Any] = field(default_factory=dict)


def build_page_requests(entry_urls: list[str], config: PaginationConfig) -> list[PageRequest]:
    if not config.enabled:
        return [PageRequest(url) for url in entry_urls]

    if config.type == "page_param":
        requests = []
        for url in entry_urls:
            for page in range(config.start_page, config.end_page + 1):
                requests.append(PageRequest(url=url, params={config.page_param: page}))
        return requests

    if config.type == "url_template":
        return [
            PageRequest(config.url_template.format(page=page))
            for page in range(config.start_page, config.end_page + 1)
        ]

    if config.type in {"next_link", "cursor"}:
        return [PageRequest(url) for url in entry_urls]

    raise ValueError(f"Unsupported pagination type: {config.type}")
