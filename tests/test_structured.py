"""Regression tests for Bold.dk's indexed Nuxt page data."""

import json

from custom_components.bold_dk.models import Club
from custom_components.bold_dk.parser import (
    parse_club_data,
    parse_clubs,
    parse_standings,
    parse_top_scorers,
)
from custom_components.bold_dk.structured import page_data


def payload_html(value):
    pool = []

    def encode(item):
        index = len(pool)
        pool.append(None)
        if isinstance(item, dict):
            pool[index] = {key: encode(child) for key, child in item.items()}
        elif isinstance(item, list):
            pool[index] = [encode(child) for child in item]
        else:
            pool[index] = item
        return index

    encode({"data": value})
    return '<script id="__NUXT_DATA__" type="application/json">' + json.dumps(pool) + "</script>"


def test_current_table_excludes_navigation_and_old_phases():
    team = {"name": "Randers FC ", "pretty_url": "randers-fc"}
    html = payload_html(
        {
            "fetch-tournament-page-?slug=superligaen": {
                "tournamentData": {
                    "phases": [
                        {
                            "stage_is_current": False,
                            "standings": {"data": [{"rank": 12, "team": team}]},
                        },
                        {
                            "stage_is_current": True,
                            "standings": {"data": [{"rank": 4, "team": team}]},
                        },
                    ],
                    "topscorers": [
                        {"team": team, "person": {"name": "Spiller A"}, "goals": 3},
                        {"team": team, "person": {"name": "Spiller B"}, "goals": 7},
                    ],
                }
            }
        }
    )
    html += '<nav><a href="/fodbold/klubber/danmark">Landsholdet</a></nav>'
    assert parse_clubs(html, "https://bold.dk") == [
        Club("Randers FC", "https://bold.dk/fodbold/klubber/randers-fc")
    ]
    assert parse_standings(html, "https://bold.dk") == [(4, "Randers FC")]
    assert parse_top_scorers(html) == {"randers-fc": ("Spiller B", 7)}


def test_structured_matches_preserve_zero_scores_and_fixture_dates():
    club = Club("Randers FC", "https://bold.dk/fodbold/klubber/randers-fc")

    def match(date, score):
        return {
            "date": date,
            "home_team": {"name": "Randers FC", "score": score},
            "away_team": {"name": "Viborg FF ", "score": 2},
        }

    html = payload_html(
        {
            "fetch-teams": {
                "team": {
                    "matches": {
                        "results": [
                            match("2026-10-01 14:00:00", 1),
                            match("2026-10-11 14:00:00", 0),
                        ],
                        "fixtures": [
                            match("2026-10-25 19:00:00", 0),
                            match("2026-10-16 19:00:00", 0),
                        ],
                    }
                }
            }
        }
    )
    data = parse_club_data(html, club.url, club)
    assert data.last_match.score == "0-2"
    assert data.last_match.away_team == "Viborg FF"
    assert data.next_match.score is None
    assert data.next_match.kickoff == "2026-10-16 19:00:00"


def test_nuxt_reactive_wrappers_and_null_references():
    html = (
        '<script id="__NUXT_DATA__">'
        + json.dumps(
            [
                ["ShallowReactive", 1],
                {"data": 2},
                ["Reactive", 3],
                {"test": 4},
                {"name": 5, "missing": -1},
                "Randers FC",
            ]
        )
        + "</script>"
    )
    assert page_data(html) == {"test": {"name": "Randers FC", "missing": None}}


def test_invalid_payload_does_not_crash_parser():
    for payload in ["bad", "{}", '[{"data":999}]']:
        assert page_data('<script id="__NUXT_DATA__">' + payload + "</script>") == {}
