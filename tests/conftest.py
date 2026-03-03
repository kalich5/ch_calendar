"""
conftest.py – bootstrap custom_components.ch_calendar without Home Assistant.

holidays.py and const.py have no HA dependency, so we can import them directly.
We register stub packages so that relative imports (.const) resolve correctly
without triggering the real __init__.py (which needs homeassistant).
"""
import sys
import types
import importlib.util
from pathlib import Path

ROOT = Path(__file__).parent.parent
CC_DIR = ROOT / "custom_components" / "ch_calendar"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def pytest_configure(config):
    """Load ch_calendar modules once before any test is collected."""
    # Stub top-level packages so relative imports work
    for pkg in ("custom_components", "custom_components.ch_calendar"):
        if pkg not in sys.modules:
            sys.modules[pkg] = types.ModuleType(pkg)

    _load("custom_components.ch_calendar.const",    CC_DIR / "const.py")
    _load("custom_components.ch_calendar.holidays", CC_DIR / "holidays.py")
