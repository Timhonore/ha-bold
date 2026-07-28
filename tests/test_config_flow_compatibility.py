"""Guard against config-flow imports unavailable in older Home Assistant releases."""

from pathlib import Path

CONFIG_FLOW = Path(__file__).parents[1] / "custom_components/bold_dk/config_flow.py"


def test_config_flow_uses_stable_multi_select() -> None:
    """The flow must not depend on the newer selector-mode enum at import time."""
    source = CONFIG_FLOW.read_text(encoding="utf-8")
    assert "cv.multi_select" in source
    assert "SelectSelectorMode" not in source
