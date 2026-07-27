"""Data models used by the Bold.dk integration."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Club:
    """A club available in a league."""

    name: str
    url: str


@dataclass(frozen=True, slots=True)
class Match:
    """A played or scheduled match."""

    home_team: str
    away_team: str
    kickoff: str | None = None
    score: str | None = None

    @property
    def description(self) -> str:
        """Return a concise state-friendly description."""
        suffix = self.score or self.kickoff
        return f"{self.home_team} - {self.away_team}" + (f" ({suffix})" if suffix else "")


@dataclass(frozen=True, slots=True)
class ClubData:
    """The values exposed for a club."""

    club: Club
    position: int | None = None
    last_match: Match | None = None
    next_match: Match | None = None
    top_scorer: str | None = None
    top_scorer_goals: int | None = None


@dataclass(frozen=True, slots=True)
class LeagueData:
    """League table and selected club data."""

    name: str
    url: str
    standings: tuple[tuple[int, str], ...] = ()
    clubs: dict[str, ClubData] = field(default_factory=dict)
