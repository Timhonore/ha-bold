"""Extract league and club facts from Bold.dk pages."""

from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urljoin, urlparse

from .models import Club, ClubData, Match, Story
from .structured import club_team, standings_rows, tournament_data

_CLUB_PATH = re.compile(r"^/fodbold/klubber/[^/]+/?$")
_POSITION = re.compile(r"^\s*(\d{1,2})\.?\s*$")
_SCORE = re.compile(r"\b\d+\s*[-–]\s*\d+\b")
_GOALS = re.compile(r"(?:mål|goals?)\D{0,8}(\d+)|\b(\d+)\s*(?:mål|goals?)\b", re.I)


class _PageParser(HTMLParser):
    """Collect links, table rows, headings and their following text."""

    def __init__(self, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.links: list[tuple[str, str]] = []
        self.rows: list[list[str]] = []
        self.sections: list[tuple[str, str]] = []
        self._href: str | None = None
        self._link_text: list[str] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None
        self._heading: list[str] | None = None
        self._section_heading: str | None = None
        self._section_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "a" and values.get("href"):
            self._href = values["href"]
            self._link_text = []
        if tag == "tr":
            self._row = []
        if tag in {"td", "th"} and self._row is not None:
            self._cell = []
        if tag in {"h1", "h2", "h3", "h4"}:
            self._finish_section()
            self._heading = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._link_text.append(data)
        if self._cell is not None:
            self._cell.append(data)
        if self._heading is not None:
            self._heading.append(data)
        elif self._section_heading:
            self._section_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._href is not None:
            text = _clean(" ".join(self._link_text))
            if text:
                self.links.append((text, urljoin(self.base_url, self._href)))
            self._href = None
        if tag in {"td", "th"} and self._cell is not None and self._row is not None:
            text = _clean(" ".join(self._cell))
            if text:
                self._row.append(text)
            self._cell = None
        if tag == "tr" and self._row is not None:
            if self._row:
                self.rows.append(self._row)
            self._row = None
        if tag in {"h1", "h2", "h3", "h4"} and self._heading is not None:
            self._section_heading = _clean(" ".join(self._heading))
            self._heading = None

    def close(self) -> None:
        super().close()
        self._finish_section()

    def _finish_section(self) -> None:
        if self._section_heading:
            self.sections.append((self._section_heading, _clean(" ".join(self._section_text))))
        self._section_heading = None
        self._section_text = []


def _clean(value: str) -> str:
    return " ".join(value.split())


def _page(html: str, base_url: str) -> _PageParser:
    parser = _PageParser(base_url)
    parser.feed(html)
    parser.close()
    return parser


def parse_clubs(html: str, base_url: str) -> list[Club]:
    """Return unique clubs linked from a Bold.dk league page."""
    rows = standings_rows(html)
    if rows:
        found = {}
        for row in rows:
            team = row.get("team", {})
            slug = team.get("pretty_url") or team.get("slug")
            if slug and team.get("name"):
                url = urljoin(base_url, f"/fodbold/klubber/{slug}")
                found[url] = Club(_clean(team["name"]), url)
        return list(found.values())
    found: dict[str, Club] = {}
    for name, url in _page(html, base_url).links:
        parsed = urlparse(url)
        if parsed.hostname in {"bold.dk", "www.bold.dk"} and _CLUB_PATH.match(parsed.path):
            found.setdefault(url.rstrip("/"), Club(name, url.rstrip("/")))
    return list(found.values())


def parse_standings(html: str, base_url: str) -> list[tuple[int, str]]:
    """Parse position and club name from standings table rows."""
    rows = standings_rows(html)
    if rows:
        return sorted(
            (row["rank"], _clean(row["team"]["name"]))
            for row in rows
            if isinstance(row.get("rank"), int) and row.get("team", {}).get("name")
        )
    page = _page(html, base_url)
    club_names = {name for name, url in page.links if _CLUB_PATH.match(urlparse(url).path)}
    standings: list[tuple[int, str]] = []
    for row in page.rows:
        position = next((int(cell.rstrip(".")) for cell in row if _POSITION.match(cell)), None)
        club = next((name for name in club_names if name in row), None)
        if position is not None and club and (position, club) not in standings:
            standings.append((position, club))
    return standings


def parse_club_data(html: str, base_url: str, club: Club) -> ClubData:
    """Parse latest match, next match and top scorer from a club page."""
    team = club_team(html)
    if team:
        matches = team.get("matches", {})
        results = sorted(
            matches.get("results", []), key=lambda item: item.get("date", ""), reverse=True
        )
        fixtures = sorted(matches.get("fixtures", []), key=lambda item: item.get("date", ""))
        return ClubData(
            club=club,
            last_match=_structured_match(results[0], played=True) if results else None,
            next_match=_structured_match(fixtures[0], played=False) if fixtures else None,
        )
    page = _page(html, base_url)
    last_match = _match_from_sections(page.sections, ("seneste kamp", "sidste kamp", "resultat"))
    next_match = _match_from_sections(page.sections, ("næste kamp", "kommende kamp", "kampprogram"))
    scorer, goals = _top_scorer(page.sections)
    return ClubData(
        club=club,
        last_match=last_match,
        next_match=next_match,
        top_scorer=scorer,
        top_scorer_goals=goals,
    )


def _structured_match(value: dict[str, Any], *, played: bool) -> Match | None:
    home = value.get("home_team", {})
    away = value.get("away_team", {})
    if not home.get("name") or not away.get("name"):
        return None
    score = None
    if played and home.get("score") is not None and away.get("score") is not None:
        score = f"{home['score']}-{away['score']}"
    return Match(_clean(home["name"]), _clean(away["name"]), value.get("date"), score)


def parse_top_scorers(html: str) -> dict[str, tuple[str, int]]:
    """Return the leading scorer per club in this league."""
    found = {}
    for row in tournament_data(html).get("topscorers", []):
        team = row.get("team", {})
        person = row.get("person", {})
        goals = row.get("goals")
        slug = team.get("pretty_url") or team.get("slug")
        if slug and person.get("name") and isinstance(goals, int):
            if slug not in found or goals > found[slug][1]:
                found[slug] = (_clean(person["name"]), goals)
    return found


def _match_from_sections(sections: list[tuple[str, str]], labels: tuple[str, ...]) -> Match | None:
    for heading, text in sections:
        if any(label in heading.lower() for label in labels):
            score = _SCORE.search(text)
            value = text[: score.start()] if score else text
            teams = re.split(r"\s+(?:-|–|vs\.?|mod)\s+", value, maxsplit=1, flags=re.I)
            if len(teams) == 2:
                return Match(
                    teams[0].strip(),
                    teams[1].strip(),
                    score=score.group() if score else None,
                )
    return None


def _top_scorer(sections: list[tuple[str, str]]) -> tuple[str | None, int | None]:
    for heading, text in sections:
        if "topscorer" not in heading.lower():
            continue
        goals = _GOALS.search(text)
        number = int(next(group for group in goals.groups() if group)) if goals else None
        name = _clean(text[: goals.start()] if goals else text).rstrip(" -–:")
        return (name or None, number)
    return None, None


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
