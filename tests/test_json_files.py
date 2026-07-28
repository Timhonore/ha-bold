"""Validate JSON files shipped with the integration."""

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
JSON_FILES = (
    ROOT / "custom_components/bold_dk/manifest.json",
    ROOT / "custom_components/bold_dk/strings.json",
    ROOT / "custom_components/bold_dk/translations/da.json",
    ROOT / "hacs.json",
)


@pytest.mark.parametrize("path", JSON_FILES, ids=lambda path: path.name)
def test_json_file_is_valid_utf8(path: Path) -> None:
    """Ensure Home Assistant can decode every packaged JSON document."""
    with path.open(encoding="utf-8") as file:
        assert isinstance(json.load(file), dict)
