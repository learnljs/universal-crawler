from __future__ import annotations

import html
import re
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "spm",
}


def clean_item(item: dict[str, Any], cleaning_config: dict[str, Any]) -> dict[str, Any]:
    cleaned = {}
    for key, value in item.items():
        cleaned[key] = _clean_value(value, cleaning_config)
    return cleaned


def _clean_value(value: Any, config: dict[str, Any]) -> Any:
    if isinstance(value, list):
        return [_clean_value(item, config) for item in value]
    if not isinstance(value, str):
        return value

    output = value
    if config.get("html_unescape", True):
        output = html.unescape(output)
    if config.get("normalize_space", True):
        output = re.sub(r"\s+", " ", output)
    if config.get("strip", True):
        output = output.strip()
    if config.get("remove_tracking_params", False) and output.startswith(("http://", "https://")):
        output = _remove_tracking_params(output)
    return output


def _remove_tracking_params(url: str) -> str:
    parts = urlsplit(url)
    query = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if key not in TRACKING_PARAMS
    ]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))
