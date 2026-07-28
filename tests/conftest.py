"""Allow parser tests to run without installing Home Assistant."""

import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).parents[1]

custom_components = ModuleType("custom_components")
custom_components.__path__ = [str(ROOT / "custom_components")]
bold_dk = ModuleType("custom_components.bold_dk")
bold_dk.__path__ = [str(ROOT / "custom_components" / "bold_dk")]

sys.modules.setdefault("custom_components", custom_components)
sys.modules.setdefault("custom_components.bold_dk", bold_dk)
