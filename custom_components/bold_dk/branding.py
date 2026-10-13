"""Official Bold.dk branding and public club image URLs."""

from urllib.parse import quote

BOLD_ICON_URL = (
    "https://static-bolddk-prod.s3.eu-central-1.amazonaws.com/img/icons/apple-touch-icon.png"
)


def club_logo_url(team: dict) -> str | None:
    """Build a public image URL from the filename supplied by Bold.dk."""
    image = team.get("image_name")
    if not isinstance(image, str) or not image or "/" in image or "\\" in image:
        return None
    return f"https://bold.dk/img/tag/128x128/{quote(image, safe='')}"
