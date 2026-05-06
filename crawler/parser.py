from __future__ import annotations

import re
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from lxml import html


def parse_list_items(html_text: str, list_config: dict[str, Any], base_url: str) -> list[dict[str, Any]]:
    item_selector = list_config.get("item_selector")
    fields = list_config.get("fields") or {}
    if not item_selector:
        return [parse_html_fields(html_text, fields, base_url)]

    soup = BeautifulSoup(html_text, "lxml")
    items = []
    for element in soup.select(item_selector):
        item_html = str(element)
        item = parse_html_fields(item_html, fields, base_url)
        if item:
            items.append(item)
    return items


def parse_html_fields(html_text: str, fields: dict[str, Any], base_url: str) -> dict[str, Any]:
    soup = BeautifulSoup(html_text, "lxml")
    tree = html.fromstring(html_text)
    output: dict[str, Any] = {}

    for name, rule in fields.items():
        if isinstance(rule, str):
            rule = {"selector": rule}

        value = None
        selector = rule.get("selector", "")
        mode = rule.get("mode", "css")

        if mode == "xpath" or selector.startswith("/"):
            value = _extract_xpath(tree, selector, rule)
        elif mode == "regex":
            value = _extract_regex(html_text, selector, rule)
        else:
            value = _extract_css(soup, selector, rule)

        if rule.get("transform") == "absolute_url" and value:
            if isinstance(value, list):
                value = [urljoin(base_url, item) for item in value]
            else:
                value = urljoin(base_url, str(value))

        if value in (None, "", []):
            if rule.get("required"):
                output[name] = None
            continue
        output[name] = value

    return output


def parse_json_items(json_data: Any, api_config: dict[str, Any]) -> list[dict[str, Any]]:
    data_path = api_config.get("data_path", "$")
    fields = api_config.get("fields") or {}
    nodes = json_path(json_data, data_path)
    if not isinstance(nodes, list):
        nodes = [nodes]

    items = []
    for node in nodes:
        if node is None:
            continue
        item = {}
        for name, path in fields.items():
            value = json_path(node, path)
            item[name] = value
        items.append(item)
    return items


def extract_next_page(html_text: str, selector: str, base_url: str) -> str | None:
    if not selector:
        return None
    soup = BeautifulSoup(html_text, "lxml")
    element = soup.select_one(selector)
    if not element:
        return None
    href = element.get("href")
    if not href:
        return None
    return urljoin(base_url, href)


def _extract_css(soup: BeautifulSoup, selector: str, rule: dict[str, Any]) -> Any:
    attr = None
    clean_selector = selector
    if "::attr(" in selector and selector.endswith(")"):
        clean_selector, attr_part = selector.split("::attr(", 1)
        attr = attr_part[:-1]
    elif selector.endswith("::text"):
        clean_selector = selector[:-6]

    elements = soup.select(clean_selector) if clean_selector else []
    values = []
    for element in elements:
        if attr:
            values.append(element.get(attr))
        else:
            values.append(element.get_text(" ", strip=True))
    values = [value for value in values if value not in (None, "")]
    return _format_values(values, rule)


def _extract_xpath(tree: html.HtmlElement, selector: str, rule: dict[str, Any]) -> Any:
    values = tree.xpath(selector)
    normalized = []
    for value in values:
        if hasattr(value, "text_content"):
            normalized.append(value.text_content().strip())
        else:
            normalized.append(str(value).strip())
    normalized = [value for value in normalized if value]
    return _format_values(normalized, rule)


def _extract_regex(text: str, pattern: str, rule: dict[str, Any]) -> Any:
    values = re.findall(pattern, text, flags=re.S)
    return _format_values(values, rule)


def _format_values(values: list[Any], rule: dict[str, Any]) -> Any:
    if rule.get("many"):
        joiner = rule.get("join")
        if joiner is not None:
            return joiner.join(str(value) for value in values)
        return values
    return values[0] if values else None


def json_path(data: Any, path: str) -> Any:
    if path in ("", "$"):
        return data
    if path.startswith("$."):
        path = path[2:]
    elif path.startswith("$"):
        path = path[1:]

    current = data
    for part in path.split("."):
        if current is None:
            return None
        if part.endswith("[*]"):
            key = part[:-3]
            current = current.get(key, []) if isinstance(current, dict) else []
            continue
        if isinstance(current, list):
            current = [item.get(part) for item in current if isinstance(item, dict)]
        elif isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current
