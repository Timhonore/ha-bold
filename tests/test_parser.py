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
