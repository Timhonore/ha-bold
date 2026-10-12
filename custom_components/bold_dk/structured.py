"""Read the public Nuxt payload embedded in Bold.dk HTML."""

import json
from html.parser import HTMLParser
from typing import Any


class _PayloadParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.active = False
        self.chunks: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "script" and dict(attrs).get("id") == "__NUXT_DATA__":
            self.active = True

    def handle_data(self, data):
        if self.active:
            self.chunks.append(data)

    def handle_endtag(self, tag):
        if tag == "script":
            self.active = False


def page_data(html: str) -> dict[str, Any]:
    """Decode Nuxt's indexed JSON graph; never execute page JavaScript."""
    parser = _PayloadParser()
    parser.feed(html)
    cache: dict[int, Any] = {}
    try:
        pool = json.loads("".join(parser.chunks))
        if not isinstance(pool, list):
            return {}

        def decode(index):
            if not isinstance(index, int) or index < 0:
                return None
            if index in cache:
                return cache[index]
            value = pool[index]
            if isinstance(value, dict):
                result = {}
                cache[index] = result
                result.update({key: decode(ref) for key, ref in value.items()})
                return result
            if isinstance(value, list):
                if value and isinstance(value[0], str):
                    if value[0] in {"Reactive", "ShallowReactive", "Ref", "ShallowRef"}:
                        cache[index] = None
                        result = decode(value[1])
                        cache[index] = result
                        return result
                    return None
                result = []
                cache[index] = result
                result.extend(decode(ref) for ref in value)
                return result
            return value

        root = decode(0)
        data = root.get("data", {}) if isinstance(root, dict) else {}
        return data if isinstance(data, dict) else {}
    except (ValueError, TypeError, IndexError, RecursionError):
        return {}


def tournament_data(html: str) -> dict[str, Any]:
    """Return only the requested tournament, excluding navigation data."""
    for key, value in page_data(html).items():
        if key.startswith("fetch-tournament-page-") and isinstance(value, dict):
            tournament = value.get("tournamentData")
            if isinstance(tournament, dict):
                return tournament
    return {}


def standings_rows(html: str) -> list[dict[str, Any]]:
    phases = tournament_data(html).get("phases", [])
    current = [phase for phase in phases if phase.get("stage_is_current")]
    for phase in current or phases:
        rows = phase.get("standings", {}).get("data", [])
        if rows:
            return rows
    return []


def club_team(html: str) -> dict[str, Any]:
    value = page_data(html).get("fetch-teams", {})
    return value.get("team", {}) if isinstance(value, dict) else {}
