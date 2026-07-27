"""Data models used by the Bold.dk integration."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Target:
    """A club or league page followed by the user."""

    name: str
    url: str


@dataclass(frozen=True, slots=True)
class Story:
    """A story discovered on Bold.dk."""

    title: str
    url: str
    published: str | None = None
