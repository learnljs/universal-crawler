from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Any

import httpx

from crawler.config import RequestConfig, RetryConfig


@dataclass(slots=True)
class FetchResult:
    url: str
    status_code: int
    text: str
    json_data: Any | None = None


class HttpFetcher:
    def __init__(self, request: RequestConfig, retry: RetryConfig) -> None:
        timeout = httpx.Timeout(
            connect=request.timeout.get("connect", 10),
            read=request.timeout.get("read", 30),
            write=30,
            pool=30,
        )
        self.request = request
        self.retry = retry
        self.client = httpx.Client(
            headers=request.headers,
            cookies=request.cookies,
            timeout=timeout,
            follow_redirects=True,
        )

    def close(self) -> None:
        self.client.close()

    def fetch(self, url: str, params: dict[str, Any] | None = None) -> FetchResult:
        method = self.request.method.upper()
        merged_params = dict(self.request.params)
        if params:
            merged_params.update(params)

        last_error: Exception | None = None
        for attempt in range(self.retry.times + 1):
            try:
                response = self.client.request(
                    method,
                    url,
                    params=merged_params if method == "GET" else None,
                    json=self.request.payload if method != "GET" else None,
                )
                if response.status_code not in self.retry.retry_status:
                    text = self._decode_response(response)
                    return FetchResult(
                        url=str(response.url),
                        status_code=response.status_code,
                        text=text,
                        json_data=self._safe_json(response),
                    )
            except httpx.HTTPError as exc:
                last_error = exc

            if attempt < self.retry.times:
                sleep_seconds = self.retry.backoff * (2**attempt) + random.random()
                time.sleep(sleep_seconds)

        if last_error:
            raise RuntimeError(f"Fetch failed for {url}: {last_error}") from last_error
        raise RuntimeError(f"Fetch failed for {url}: retry status exceeded")

    def _decode_response(self, response: httpx.Response) -> str:
        if self.request.encoding and self.request.encoding != "auto":
            response.encoding = self.request.encoding
        return response.text

    @staticmethod
    def _safe_json(response: httpx.Response) -> Any | None:
        try:
            return response.json()
        except ValueError:
            return None
