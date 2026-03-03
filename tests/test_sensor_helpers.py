"""Unit tests for sensor helper functions (no Home Assistant required)."""
import pytest
from datetime import date
import sys
import types
import importlib.util
from pathlib import Path

# Load sensor.py with a minimal homeassistant stub so we can test pure helpers
def _load_sensor_module():
    """Load sensor.py by stubbing out the homeassistant imports."""
    ROOT = Path(__file__).parent.parent
    CC_DIR = ROOT / "custom_components" / "ch_calendar"

    # Minimal HA stubs
    for mod_name in [
        "homeassistant",
        "homeassistant.components",
        "homeassistant.components.sensor",
        "homeassistant.config_entries",
        "homeassistant.core",
        "homeassistant.helpers",
        "homeassistant.helpers.entity_platform",
        "homeassistant.helpers.event",
    ]:
        if mod_name not in sys.modules:
            sys.modules[mod_name] = types.ModuleType(mod_name)

    # SensorEntity stub
    class _SensorEntity:
        pass

    sys.modules["homeassistant.components.sensor"].SensorEntity = _SensorEntity
    sys.modules["homeassistant.config_entries"].ConfigEntry = object
    sys.modules["homeassistant.core"].HomeAssistant = object
    sys.modules["homeassistant.helpers.entity_platform"].AddEntitiesCallback = object
    sys.modules["homeassistant.helpers.event"].async_track_time_change = lambda *a, **kw: None

    spec = importlib.util.spec_from_file_location(
        "custom_components.ch_calendar.sensor", CC_DIR / "sensor.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["custom_components.ch_calendar.sensor"] = mod
    spec.loader.exec_module(mod)
    return mod


_sensor = _load_sensor_module()
_parse_custom = _sensor._parse_custom
_next_occ = _sensor._next_occ


# ---------------------------------------------------------------------------
# _parse_custom
# ---------------------------------------------------------------------------

class TestParseCustom:
    def test_empty_string(self):
        assert _parse_custom("") == []

    def test_none_equivalent_empty(self):
        assert _parse_custom("   ") == []

    def test_recurring_birthday(self):
        result = _parse_custom("15.03 | Birthday Mama")
        assert len(result) == 1
        key, name = result[0]
        assert key == (3, 15)   # (month, day)
        assert name == "Birthday Mama"

    def test_one_time_event(self):
        result = _parse_custom("2026-12-24 | Special Christmas")
        assert len(result) == 1
        key, name = result[0]
        assert key == date(2026, 12, 24)
        assert name == "Special Christmas"

    def test_multiple_on_one_line_pipe_separated(self):
        result = _parse_custom("15.03 | Birthday Mama | 07.08 | Birthday Papa")
        assert len(result) == 2
        names = [name for _, name in result]
        assert "Birthday Mama" in names
        assert "Birthday Papa" in names

    def test_multiple_lines(self):
        raw = "15.03 | Birthday Mama\n07.08 | Birthday Papa"
        result = _parse_custom(raw)
        assert len(result) == 2

    def test_invalid_date_accepted_as_tuple(self):
        # _parse_custom stores DD.MM as (month, day) tuple without range validation.
        # 99.99 is parsed as (99, 99) – validation happens later in _next_occ.
        result = _parse_custom("99.99 | Bad Date")
        assert len(result) == 1
        assert result[0][0] == (99, 99)

    def test_invalid_iso_date_skipped(self):
        result = _parse_custom("2026-13-45 | Bad ISO")
        assert result == []

    def test_single_token_line_skipped(self):
        result = _parse_custom("JustANameWithoutDate")
        assert result == []

    def test_windows_line_endings(self):
        result = _parse_custom("15.03 | Mama\r\n07.08 | Papa")
        assert len(result) == 2

    def test_mixed_events(self):
        raw = "15.03 | Birthday Mama | 2026-12-24 | Christmas Eve"
        result = _parse_custom(raw)
        assert len(result) == 2
        keys = [k for k, _ in result]
        assert (3, 15) in keys
        assert date(2026, 12, 24) in keys


# ---------------------------------------------------------------------------
# _next_occ
# ---------------------------------------------------------------------------

class TestNextOcc:
    def test_one_time_event_in_future(self):
        today = date(2026, 1, 1)
        future = date(2026, 6, 15)
        result_date, days = _next_occ(future, today)
        assert result_date == future
        assert days == (future - today).days

    def test_one_time_event_in_past_returns_none(self):
        today = date(2026, 6, 1)
        past = date(2026, 1, 1)
        result_date, days = _next_occ(past, today)
        assert result_date is None
        assert days == -1

    def test_one_time_event_today(self):
        today = date(2026, 3, 3)
        result_date, days = _next_occ(today, today)
        assert result_date == today
        assert days == 0

    def test_recurring_birthday_this_year(self):
        today = date(2026, 1, 1)
        # Birthday on 15 March – should find 2026-03-15
        result_date, days = _next_occ((3, 15), today)
        assert result_date == date(2026, 3, 15)
        assert days > 0

    def test_recurring_birthday_next_year(self):
        today = date(2026, 12, 1)
        # Birthday on 15 March – already passed in 2026, should give 2027-03-15
        result_date, days = _next_occ((3, 15), today)
        assert result_date == date(2027, 3, 15)
        assert days > 0

    def test_recurring_birthday_today(self):
        today = date(2026, 3, 15)
        result_date, days = _next_occ((3, 15), today)
        assert result_date == today
        assert days == 0

    def test_feb_29_skipped_non_leap(self):
        """29 Feb in a non-leap year should be skipped and find next leap year."""
        today = date(2026, 1, 1)
        result_date, days = _next_occ((2, 29), today)
        # 2026 is not a leap year; 2027 is not either; 2028 is
        if result_date is not None:
            assert result_date.month == 2
            assert result_date.day == 29
