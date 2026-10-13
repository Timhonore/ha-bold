"""Logo metadata survives older configs and reaches Home Assistant entities."""

from test_structured import payload_html

from custom_components.bold_dk.branding import club_logo_url
from custom_components.bold_dk.models import Club
from custom_components.bold_dk.parser import parse_club_data, parse_clubs


def test_logo_from_standings_is_saved_with_club():
    html = payload_html(
        {
            "fetch-tournament-page-?slug=superligaen": {
                "tournamentData": {
                    "phases": [
                        {
                            "standings": {
                                "data": [
                                    {
                                        "rank": 4,
                                        "team": {
                                            "name": "Randers FC",
                                            "pretty_url": "randers-fc",
                                            "image_name": "4301.png",
                                        },
                                    }
                                ]
                            }
                        }
                    ]
                }
            }
        }
    )
    clubs = parse_clubs(html, "https://bold.dk")
    assert clubs[0].logo_url == "https://bold.dk/img/tag/128x128/4301.png"


def test_club_refresh_adds_logo_to_old_config():
    club = Club(**{"name": "Randers FC", "url": "https://bold.dk/fodbold/klubber/randers-fc"})
    html = payload_html({"fetch-teams": {"team": {"image_name": "4301.png", "matches": {}}}})
    data = parse_club_data(html, club.url, club)
    assert club.logo_url is None
    assert data.club.logo_url == "https://bold.dk/img/tag/128x128/4301.png"


def test_missing_logo_and_unsafe_filenames():
    for value in [None, 4, "", "../../file.png", "https://example.com/logo.png", "a\\b.png"]:
        assert club_logo_url({"image_name": value}) is None
    assert club_logo_url({"image_name": "club logo.webp"}).endswith("club%20logo.webp")
