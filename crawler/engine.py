from __future__ import annotations

import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from crawler.browser_fetcher import BrowserFetcher
from crawler.cleaner import clean_item
from crawler.config import CrawlerConfig
from crawler.dedupe import DedupeSet
from crawler.fetcher import HttpFetcher
from crawler.media import MediaDownloader
from crawler.paginator import PageRequest, build_page_requests
from crawler.parser import extract_next_page, json_path, parse_html_fields, parse_json_items, parse_list_items
from crawler.run_state import ResumeState, TaskLogger, page_key
from crawler.storage import build_storage


@dataclass(slots=True)
class CrawlResult:
    fetched: int = 0
    parsed: int = 0
    saved: int = 0
    skipped: int = 0
    failed: int = 0


class CrawlerEngine:
    def __init__(self, config: CrawlerConfig) -> None:
        self.config = config
        self.fetcher = HttpFetcher(config.request, config.retry)
        self.browser_fetcher = BrowserFetcher(config.browser)
        self.storage = build_storage(config.storage.type, config.storage.path, config.storage.table)
        dedupe_path = config.dedupe.path if config.dedupe.type in {"file", "persistent"} else None
        self.dedupe = DedupeSet(config.dedupe.key_fields, dedupe_path)
        self.media_downloader = MediaDownloader(config.media, config.request.headers)
        self.logger = TaskLogger(config.logging, config.task.name)
        self.resume_state = ResumeState(config.raw.get("resume") or {}, config.task.name)

    @classmethod
    def from_yaml(cls, path: Path) -> "CrawlerEngine":
        return cls(CrawlerConfig.from_yaml(path))

    def run(self) -> CrawlResult:
        result = CrawlResult()
        try:
            page_requests = self.resume_state.failed_page_requests()
            page_requests.extend(build_page_requests(self.config.target.entry_urls, self.config.pagination))
            if self.config.pagination.enabled and self.config.pagination.type == "cursor":
                self._run_cursor_pages(page_requests, result)
            else:
                for page_request in page_requests:
                    self._run_page(page_request, result)
                    if self.config.pagination.type == "next_link":
                        self._run_next_links(page_request, result)
        finally:
            self.fetcher.close()
            self.media_downloader.close()
            self.logger.summary(
                task=self.config.task.name,
                fetched=result.fetched,
                parsed=result.parsed,
                saved=result.saved,
                skipped=result.skipped,
                failed=result.failed,
            )
        return result

    def _run_page(self, page_request: PageRequest, result: CrawlResult) -> None:
        key = page_key(page_request.url, page_request.params)
        if self.resume_state.should_skip(key):
            result.skipped += 1
            self.logger.request("skip_completed", url=page_request.url, params=page_request.params)
            return
        started = time.time()
        try:
            self.logger.request("fetch_start", url=page_request.url, params=page_request.params)
            fetch_result = self._fetch(page_request)
            result.fetched += 1
            items = self._parse_fetch_result(fetch_result.text, fetch_result.json_data)
            items = self._enrich_detail_items(items, result)
            result.parsed += len(items)
            cleaned_items = self._prepare_items(items, fetch_result.url)
            result.saved += self.storage.save_many(cleaned_items)
            result.skipped += len(items) - len(cleaned_items)
            self.resume_state.mark_completed(key)
            self.logger.request(
                "fetch_success",
                url=page_request.url,
                final_url=fetch_result.url,
                status_code=fetch_result.status_code,
                parsed=len(items),
                saved=len(cleaned_items),
                elapsed=round(time.time() - started, 3),
            )
        except Exception as exc:
            result.failed += 1
            self.resume_state.mark_failed(key, page_request.url, page_request.params, exc)
            self.logger.error("fetch_failed", url=page_request.url, params=page_request.params, error=str(exc))
            print(f"[failed] {page_request.url}: {exc}")
        self._sleep()

    def _fetch(self, page_request: PageRequest) -> Any:
        if self.config.request.type == "dynamic" or self.config.browser.get("enabled"):
            return self.browser_fetcher.fetch(page_request.url)
        return self.fetcher.fetch(page_request.url, page_request.params)

    def _run_next_links(self, first_request: PageRequest, result: CrawlResult) -> None:
        current_url = first_request.url
        seen_urls = {current_url}
        max_pages = max(self.config.pagination.max_pages, 1)

        for _ in range(max_pages - 1):
            try:
                fetch_result = self.fetcher.fetch(current_url)
                next_url = extract_next_page(
                    fetch_result.text,
                    self.config.pagination.next_page_selector,
                    self.config.target.base_url or fetch_result.url,
                )
                if not next_url or next_url in seen_urls:
                    return
                seen_urls.add(next_url)
                current_url = next_url
                self._run_page(PageRequest(current_url), result)
            except Exception as exc:
                result.failed += 1
                self.logger.error("next_link_failed", url=current_url, error=str(exc))
                print(f"[failed] next page from {current_url}: {exc}")
                return

    def _run_cursor_pages(self, page_requests: list[PageRequest], result: CrawlResult) -> None:
        for page_request in page_requests:
            cursor = self.config.pagination.cursor_start
            seen_cursors = set()
            for _ in range(max(self.config.pagination.max_pages, 1)):
                params = dict(page_request.params)
                if cursor:
                    params[self.config.pagination.cursor_param] = cursor
                try:
                    key = page_key(page_request.url, params)
                    if self.resume_state.should_skip(key):
                        result.skipped += 1
                        self.logger.request("skip_completed", url=page_request.url, params=params)
                        continue
                    self.logger.request("fetch_start", url=page_request.url, params=params)
                    fetch_result = self.fetcher.fetch(page_request.url, params)
                    result.fetched += 1
                    items = self._parse_fetch_result(fetch_result.text, fetch_result.json_data)
                    items = self._enrich_detail_items(items, result)
                    result.parsed += len(items)
                    cleaned_items = self._prepare_items(items, fetch_result.url)
                    result.saved += self.storage.save_many(cleaned_items)
                    result.skipped += len(items) - len(cleaned_items)
                    self.resume_state.mark_completed(key)
                    self.logger.request(
                        "fetch_success",
                        url=page_request.url,
                        final_url=fetch_result.url,
                        status_code=fetch_result.status_code,
                        parsed=len(items),
                        saved=len(cleaned_items),
                    )

                    if not items:
                        return
                    next_cursor = json_path(fetch_result.json_data, self.config.pagination.next_cursor_path)
                    if not next_cursor or next_cursor in seen_cursors:
                        return
                    seen_cursors.add(str(next_cursor))
                    cursor = str(next_cursor)
                except Exception as exc:
                    result.failed += 1
                    self.resume_state.mark_failed(page_key(page_request.url, params), page_request.url, params, exc)
                    self.logger.error("cursor_failed", url=page_request.url, params=params, error=str(exc))
                    print(f"[failed] cursor page {page_request.url}: {exc}")
                    return
                self._sleep()

    def _parse_fetch_result(self, html_text: str, json_data: Any | None) -> list[dict[str, Any]]:
        if self.config.request.type == "api" or self.config.api.get("enabled"):
            if json_data is None:
                return []
            return parse_json_items(json_data, self.config.api)
        return parse_list_items(html_text, self.config.list_config, self.config.target.base_url)

    def _prepare_items(self, items: list[dict[str, Any]], source_url: str) -> list[dict[str, Any]]:
        prepared = []
        for item in items:
            item.setdefault("_source_url", source_url)
            cleaned = clean_item(item, self.config.cleaning)
            if self.config.dedupe.enabled and not self.dedupe.add(cleaned):
                continue
            cleaned = self.media_downloader.process_item(cleaned)
            prepared.append(cleaned)
        return prepared

    def _enrich_detail_items(self, items: list[dict[str, Any]], result: CrawlResult) -> list[dict[str, Any]]:
        detail_config = self.config.detail or {}
        if not detail_config.get("enabled"):
            return items

        url_field = detail_config.get("url_field", "detail_url")
        fields = detail_config.get("fields") or {}
        if not fields:
            return items

        enriched_items = []
        for item in items:
            detail_url = item.get(url_field)
            if not detail_url:
                enriched_items.append(item)
                continue
            try:
                fetch_result = self.fetcher.fetch(str(detail_url))
                result.fetched += 1
                detail_fields = parse_html_fields(
                    fetch_result.text,
                    fields,
                    self.config.target.base_url or fetch_result.url,
                )
                merged = {**item, **detail_fields, "_detail_url": fetch_result.url}
                enriched_items.append(merged)
            except Exception as exc:
                result.failed += 1
                self.logger.error("detail_failed", url=str(detail_url), error=str(exc))
                print(f"[failed] detail {detail_url}: {exc}")
                if detail_config.get("keep_on_detail_failed", True):
                    enriched_items.append(item)
            self._sleep()
        return enriched_items

    def _sleep(self) -> None:
        delay_min = self.config.rate_limit.delay_min
        delay_max = self.config.rate_limit.delay_max
        if delay_max <= 0:
            return
        time.sleep(random.uniform(delay_min, delay_max))
