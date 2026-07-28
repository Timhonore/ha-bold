"""Tests for league and club parsing."""

from custom_components.bold_dk.models import Club
from custom_components.bold_dk.parser import parse_club_data, parse_clubs, parse_standings

LEAGUE_HTML = """
<nav><a href="/fodbold/resultater">Seneste resultater</a></nav>
<table>
  <tr><th>Placering</th><th>Hold</th><th>Point</th></tr>
  <tr><td>1.</td><td><a href="/fodbold/klubber/fc-midtjylland">
    FC Midtjylland</a></td><td>51</td></tr>
  <tr><td>2</td><td><a href="/fodbold/klubber/randers-fc">Randers FC</a></td><td>47</td></tr>
</table>
"""


def test_parse_clubs_ignores_navigation_links() -> None:
    clubs = parse_clubs(LEAGUE_HTML, "https://bold.dk/fodbold/stillinger/superligaen")
    assert clubs == [
        Club("FC Midtjylland", "https://bold.dk/fodbold/klubber/fc-midtjylland"),
        Club("Randers FC", "https://bold.dk/fodbold/klubber/randers-fc"),
    ]


def test_parse_standings() -> None:
    assert parse_standings(LEAGUE_HTML, "https://bold.dk") == [
        (1, "FC Midtjylland"),
        (2, "Randers FC"),
    ]


def test_parse_club_statistics() -> None:
    html = """
      <h2>Seneste kamp</h2><div>Randers FC - Viborg FF 2-1</div>
      <h2>Næste kamp</h2><div>AGF - Randers FC søndag 18:00</div>
      <h2>Topscorer</h2><div>Mohamed Touré - 9 mål</div>
    """
    club = Club("Randers FC", "https://bold.dk/fodbold/klubber/randers-fc")
    data = parse_club_data(html, club.url, club)
    assert data.last_match and data.last_match.description == "Randers FC - Viborg FF (2-1)"
    assert data.next_match and data.next_match.description == "AGF - Randers FC søndag 18:00"
    assert data.top_scorer == "Mohamed Touré"
    assert data.top_scorer_goals == 9
"""Tests for the HTML parser."""

from custom_components.bold_dk.parser import parse_stories


def test_parse_json_ld_and_remove_duplicates() -> None:
    html = """
      <script type="application/ld+json">
      {"@graph": [
        {"@type":"NewsArticle", "headline":"Brøndby henter ny spiller",
         "url":"/fodbold/nyheder/broendby-henter", "datePublished":"2026-07-27"},
        {"@type":"NewsArticle", "headline":"Brøndby henter ny spiller",
         "url":"/fodbold/nyheder/broendby-henter"}
      ]}
      </script>
    """
    stories = parse_stories(html, "https://bold.dk/fodbold/klub")
    assert len(stories) == 1
    assert stories[0].title == "Brøndby henter ny spiller"
    assert stories[0].url == "https://bold.dk/fodbold/nyheder/broendby-henter"
    assert stories[0].published == "2026-07-27"


def test_falls_back_to_article_links() -> None:
    stories = parse_stories(
        '<a href="/fodbold/nyheder/en-rigtig-lang-nyhed"> En rigtig lang nyhed </a>',
        "https://bold.dk/",
    )
    assert [story.title for story in stories] == ["En rigtig lang nyhed"]


def test_combines_structured_stories_and_page_links() -> None:
    html = """
      <script type="application/ld+json">
        {"@type":"NewsArticle", "headline":"Første historie fra klubben",
         "url":"/fodbold/nyheder/foerste"}
      </script>
      <a href="/fodbold/nyheder/anden">Anden historie fra klubben</a>
    """
    stories = parse_stories(html, "https://bold.dk/fodbold/klubber/klub")
    assert [story.title for story in stories] == [
        "Første historie fra klubben",
        "Anden historie fra klubben",
    ]
