from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class BrowserFetchResult:
    url: str
    status_code: int
    text: str
    json_data: Any | None = None


class BrowserFetcher:
    def __init__(self, browser_config: dict[str, Any]) -> None:
        self.config = browser_config

    def fetch(self, url: str) -> BrowserFetchResult:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RuntimeError(
                "Dynamic crawling requires Playwright. Run: pip install playwright; playwright install"
            ) from exc

        with sync_playwright() as playwright:
            engine = self.config.get("engine", "chromium")
            browser_type = getattr(playwright, engine)
            browser = browser_type.launch(headless=self.config.get("headless", True))
            context = browser.new_context(
                user_agent=self.config.get("user_agent"),
                viewport=self.config.get("viewport") or {"width": 1366, "height": 768},
            )
            page = context.new_page()
            response = page.goto(url, wait_until=self.config.get("wait_until", "networkidle"))

            for action in self.config.get("actions") or []:
                self._run_action(page, action)

            wait_selector = self.config.get("wait_selector")
            if wait_selector:
                page.wait_for_selector(wait_selector, timeout=self.config.get("wait_timeout", 15000))

            html = page.content()
            final_url = page.url
            status_code = response.status if response else 200
            browser.close()
        return BrowserFetchResult(url=final_url, status_code=status_code, text=html)

    def _run_action(self, page: Any, action: dict[str, Any]) -> None:
        action_type = action.get("type")
        if action_type == "wait":
            page.wait_for_timeout(int(float(action.get("seconds", 1)) * 1000))
        elif action_type == "click":
            page.click(action["selector"])
        elif action_type == "fill":
            page.fill(action["selector"], str(action.get("value", "")))
        elif action_type == "scroll":
            times = int(action.get("times", 1))
            pause = int(float(action.get("pause", 1)) * 1000)
            for _ in range(times):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(pause)
