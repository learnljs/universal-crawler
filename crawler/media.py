from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import httpx

from crawler.attachment_parser import parse_attachment, write_parsed_text


SUBTITLE_EXTENSIONS = {".srt", ".vtt", ".ass"}


class MediaDownloader:
    def __init__(self, config: dict[str, Any], headers: dict[str, str] | None = None) -> None:
        self.config = config
        self.enabled = bool(config.get("enabled"))
        self.output_dir = Path(config.get("output_dir", "data/media"))
        self.timeout = httpx.Timeout(60)
        self.client = httpx.Client(headers=headers or {}, timeout=self.timeout, follow_redirects=True)

    def close(self) -> None:
        self.client.close()

    def process_item(self, item: dict[str, Any]) -> dict[str, Any]:
        if not self.enabled:
            return item

        downloaded: dict[str, Any] = {}
        for resource in self.config.get("resources") or []:
            name = resource.get("name", "media")
            url_fields = resource.get("url_fields") or []
            urls = self._collect_urls(item, url_fields)
            if not urls and resource.get("auto_extract"):
                urls = self._auto_extract_urls(item, resource.get("types") or [])

            paths = []
            parsed_texts = []
            parsed_paths = []
            for url in urls:
                path = self._download(url, resource)
                if path:
                    paths.append(path)
                    if resource.get("type") == "subtitle" or Path(path).suffix.lower() in SUBTITLE_EXTENSIONS:
                        text_path = self._subtitle_to_text(path)
                        if text_path:
                            paths.append(text_path)
                    if resource.get("parse") or self.config.get("parse_attachments"):
                        parsed_text = parse_attachment(path, resource.get("parse_config") or self.config.get("parse_config"))
                        if parsed_text:
                            parsed_texts.append(parsed_text)
                            parsed_paths.append(write_parsed_text(path, parsed_text))
            downloaded[f"{name}_files"] = paths
            if parsed_paths:
                downloaded[f"{name}_parsed_files"] = parsed_paths
            if parsed_texts and resource.get("include_text", True):
                downloaded[f"{name}_text"] = "\n\n".join(parsed_texts)

        item.update(downloaded)
        return item

    def _collect_urls(self, item: dict[str, Any], fields: list[str]) -> list[str]:
        urls = []
        for field in fields:
            value = item.get(field)
            if isinstance(value, list):
                urls.extend(str(item) for item in value if item)
            elif value:
                urls.append(str(value))
        return _unique_urls(urls)

    def _auto_extract_urls(self, item: dict[str, Any], types: list[str]) -> list[str]:
        text = " ".join(str(value) for value in item.values())
        patterns = []
        if not types or "image" in types:
            patterns.append(r"https?://[^\s\"']+\.(?:jpg|jpeg|png|webp|gif)(?:\?[^\s\"']*)?")
        if not types or "audio" in types:
            patterns.append(r"https?://[^\s\"']+\.(?:mp3|m4a|wav|aac)(?:\?[^\s\"']*)?")
        if not types or "video" in types:
            patterns.append(r"https?://[^\s\"']+\.(?:mp4|m3u8)(?:\?[^\s\"']*)?")
        if not types or "subtitle" in types:
            patterns.append(r"https?://[^\s\"']+\.(?:srt|vtt|ass)(?:\?[^\s\"']*)?")
        urls = []
        for pattern in patterns:
            urls.extend(re.findall(pattern, text, flags=re.I))
        return _unique_urls(urls)

    def _download(self, url: str, resource: dict[str, Any]) -> str | None:
        category = resource.get("type", "file")
        target_dir = self.output_dir / category
        target_dir.mkdir(parents=True, exist_ok=True)
        filename = self._filename(url, resource)
        target_path = target_dir / filename
        if target_path.exists() and self.config.get("skip_existing", True):
            return str(target_path)

        try:
            with self.client.stream("GET", url) as response:
                response.raise_for_status()
                with target_path.open("wb") as file:
                    for chunk in response.iter_bytes():
                        file.write(chunk)
            return str(target_path)
        except httpx.HTTPError as exc:
            print(f"[failed] media {url}: {exc}")
            return None

    def _filename(self, url: str, resource: dict[str, Any]) -> str:
        parts = urlsplit(url)
        suffix = Path(parts.path).suffix or resource.get("default_ext", ".bin")
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
        prefix = resource.get("filename_prefix", resource.get("name", "media"))
        return f"{prefix}_{digest}{suffix}"

    def _subtitle_to_text(self, subtitle_path: str) -> str | None:
        path = Path(subtitle_path)
        if path.suffix.lower() not in SUBTITLE_EXTENSIONS:
            return None
        text = path.read_text(encoding=self.config.get("subtitle_encoding", "utf-8"), errors="ignore")
        text = subtitle_to_plain_text(text, path.suffix.lower())
        output_path = path.with_suffix(".txt")
        output_path.write_text(text, encoding="utf-8")
        return str(output_path)


def subtitle_to_plain_text(text: str, suffix: str) -> str:
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if suffix == ".vtt" and stripped.upper().startswith("WEBVTT"):
            continue
        if re.fullmatch(r"\d+", stripped):
            continue
        if "-->" in stripped:
            continue
        if suffix == ".ass" and stripped.startswith(("Script Info", "[", "Format:", "Style:")):
            continue
        if suffix == ".ass" and stripped.startswith("Dialogue:"):
            parts = stripped.split(",", 9)
            stripped = parts[-1] if parts else stripped
        stripped = re.sub(r"<[^>]+>", "", stripped)
        stripped = re.sub(r"\{\\.*?\}", "", stripped)
        if stripped:
            lines.append(stripped)
    return "\n".join(lines).strip() + "\n"


def _unique_urls(urls: list[str]) -> list[str]:
    seen = set()
    output = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            output.append(url)
    return output
