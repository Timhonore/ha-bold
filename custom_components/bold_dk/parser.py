"""Parse stories from Bold.dk pages without third-party dependencies."""

from __future__ import annotations

import json
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urljoin, urlparse

from .models import Story


class _BoldParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.in_json_ld = False
        self.json_chunks: list[str] = []
        self.current_href: str | None = None
        self.current_text: list[str] = []
        self.json_stories: list[Story] = []
        self.link_stories: list[Story] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "script" and "ld+json" in (values.get("type") or "").lower():
            self.in_json_ld = True
            self.json_chunks = []
        elif tag == "a" and values.get("href"):
            self.current_href = values["href"]
            self.current_text = []

    def handle_data(self, data: str) -> None:
        if self.in_json_ld:
            self.json_chunks.append(data)
        if self.current_href:
            self.current_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self.in_json_ld:
            self.in_json_ld = False
            try:
                self._walk_json(json.loads("".join(self.json_chunks)))
            except (json.JSONDecodeError, TypeError):
                pass
        elif tag == "a" and self.current_href:
            title = " ".join("".join(self.current_text).split())
            url = urljoin(self.base_url, self.current_href)
            if _is_story_link(url, title):
                self.link_stories.append(Story(title, url))
            self.current_href = None
            self.current_text = []

    def _walk_json(self, value: Any) -> None:
        if isinstance(value, list):
            for item in value:
                self._walk_json(item)
            return
        if not isinstance(value, dict):
            return
        item_type = value.get("@type")
        types = {item_type} if isinstance(item_type, str) else set(item_type or [])
        if types & {"NewsArticle", "Article", "SportsEvent"}:
            title = value.get("headline") or value.get("name")
            url = value.get("url") or value.get("mainEntityOfPage")
            if isinstance(url, dict):
                url = url.get("@id")
            if isinstance(title, str) and isinstance(url, str):
                self.json_stories.append(
                    Story(
                        " ".join(title.split()),
                        urljoin(self.base_url, url),
                        value.get("datePublished") or value.get("startDate"),
                    )
                )
        for child in value.values():
            if isinstance(child, (dict, list)):
                self._walk_json(child)


def _is_story_link(url: str, title: str) -> bool:
    parsed = urlparse(url)
    return (
        parsed.hostname in {"bold.dk", "www.bold.dk"}
        and len(title) >= 12
        and any(part in parsed.path.split("/") for part in ("nyheder", "fodbold", "artikel"))
    )


def parse_stories(html: str, base_url: str, limit: int = 10) -> list[Story]:
    """Return unique stories in the order presented by Bold.dk."""
    parser = _BoldParser(base_url)
    parser.feed(html)
    stories = parser.json_stories + parser.link_stories
    unique: list[Story] = []
    seen: set[str] = set()
    for story in stories:
        if story.url not in seen:
            unique.append(story)
            seen.add(story.url)
        if len(unique) == limit:
            break
    return unique
