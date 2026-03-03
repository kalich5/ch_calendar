"""Unit tests for custom_components.ch_calendar.holidays (no HA required)."""
import pytest
from datetime import date

from custom_components.ch_calendar.holidays import (
    easter_sunday,
    get_public_holidays,
    get_school_holidays,
    is_public_holiday,
    is_school_holiday,
)


# ---------------------------------------------------------------------------
# Easter (Computus)
# ---------------------------------------------------------------------------

class TestEaster:
    @pytest.mark.parametrize("year,expected", [
        (2024, date(2024, 3, 31)),
        (2025, date(2025, 4, 20)),
        (2026, date(2026, 4,  5)),
        (2027, date(2027, 3, 28)),
    ])
    def test_known_years(self, year, expected):
        assert easter_sunday(year) == expected

    def test_always_sunday(self):
        for year in range(2020, 2035):
            assert easter_sunday(year).weekday() == 6, f"{year} is not a Sunday"

    def test_always_march_or_april(self):
        for year in range(2020, 2035):
            assert easter_sunday(year).month in (3, 4)


# ---------------------------------------------------------------------------
# Public holidays
# ---------------------------------------------------------------------------

class TestPublicHolidays:
    def test_new_year_all_cantons(self):
        """1 January must be a holiday in every canton."""
        for canton in ["ZH", "BE", "GE", "TI", "VS", "LU", "BS"]:
            hols = get_public_holidays(2026, canton)
            assert date(2026, 1, 1) in hols, f"New Year missing for {canton}"

    def test_national_day_all_cantons(self):
        """1 August is the only federal holiday – must be present everywhere."""
        for canton in ["ZH", "GE", "TI", "VS", "NW", "OW"]:
            hols = get_public_holidays(2026, canton)
            assert date(2026, 8, 1) in hols, f"National day missing for {canton}"

    def test_zh_good_friday_2026(self):
        """Good Friday 2026 = 3 April (Easter 5 April - 2 days)."""
        hols = get_public_holidays(2026, "ZH")
        assert date(2026, 4, 3) in hols

    def test_zh_easter_monday_2026(self):
        """Easter Monday 2026 = 6 April."""
        hols = get_public_holidays(2026, "ZH")
        assert date(2026, 4, 6) in hols

    def test_zh_ascension_2026(self):
        """Ascension 2026 = Easter + 39 days = 14 May."""
        hols = get_public_holidays(2026, "ZH")
        assert date(2026, 5, 14) in hols

    def test_zh_whit_monday_2026(self):
        """Whit Monday 2026 = Easter + 50 days = 25 May."""
        hols = get_public_holidays(2026, "ZH")
        assert date(2026, 5, 25) in hols

    def test_zh_knabenschiessen(self):
        """Knabenschiessen is ZH-specific (3rd Monday of September)."""
        zh_hols = get_public_holidays(2026, "ZH")
        be_hols = get_public_holidays(2026, "BE")
        knaben = date(2026, 9, 14)
        assert knaben in zh_hols
        assert knaben not in be_hols

    def test_ge_geneva_fast(self):
        """Jeûne genevois is GE-specific."""
        ge_hols = get_public_holidays(2026, "GE")
        zh_hols = get_public_holidays(2026, "ZH")
        ge_fast = date(2026, 9, 10)
        assert ge_fast in ge_hols
        assert ge_fast not in zh_hols

    def test_corpus_christi_catholic_cantons(self):
        """Corpus Christi should be in LU (Catholic) but not ZH or GE."""
        corpus = date(2026, 6, 4)   # Easter(5.4) + 60 days
        assert corpus in get_public_holidays(2026, "LU")
        assert corpus not in get_public_holidays(2026, "ZH")
        assert corpus not in get_public_holidays(2026, "GE")

    def test_zh_returns_dict(self):
        result = get_public_holidays(2026, "ZH")
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_unknown_canton_fallback(self):
        """An unknown canton should still get the 3 universal holidays."""
        hols = get_public_holidays(2026, "XX")
        assert date(2026, 1, 1) in hols   # New Year
        assert date(2026, 8, 1) in hols   # National Day
        assert date(2026, 12, 25) in hols  # Christmas


# ---------------------------------------------------------------------------
# is_public_holiday
# ---------------------------------------------------------------------------

class TestIsPublicHoliday:
    def test_national_day_is_holiday(self):
        is_hol, name = is_public_holiday(date(2026, 8, 1), "ZH")
        assert is_hol is True
        assert name is not None
        assert len(name) > 0

    def test_regular_monday_not_holiday(self):
        # 2026-03-09 is an ordinary Monday
        is_hol, name = is_public_holiday(date(2026, 3, 9), "ZH")
        assert is_hol is False
        assert name is None

    def test_returns_tuple(self):
        result = is_public_holiday(date(2026, 1, 1), "ZH")
        assert isinstance(result, tuple)
        assert len(result) == 2


# ---------------------------------------------------------------------------
# School holidays
# ---------------------------------------------------------------------------

class TestSchoolHolidays:
    def test_zh_has_summer_holidays(self):
        holidays = get_school_holidays(2026, "ZH")
        names = [n for _, _, n in holidays]
        assert any("Summer" in n or "Sommer" in n for n in names)

    def test_zh_summer_dates_2026(self):
        """ZH summer 2026: 13 July – 14 August (from ICS/JSON)."""
        holidays = get_school_holidays(2026, "ZH")
        summer = [(s, e) for s, e, n in holidays if "Summer" in n or "Sommer" in n]
        assert summer, "No summer holiday found for ZH 2026"
        start, end = summer[0]
        assert start.month in (6, 7)
        assert end.month in (7, 8, 9)

    def test_returns_list_of_tuples(self):
        result = get_school_holidays(2026, "ZH")
        assert isinstance(result, list)
        assert len(result) > 0
        for item in result:
            assert len(item) == 3
            start, end, name = item
            assert isinstance(start, date)
            assert isinstance(end, date)
            assert isinstance(name, str)
            assert start <= end

    def test_all_cantons_return_holidays(self):
        """Every canton must return at least one holiday period."""
        cantons = ["ZH", "BE", "LU", "GE", "TI", "VS", "BS", "AG", "SG"]
        for canton in cantons:
            result = get_school_holidays(2026, canton)
            assert len(result) > 0, f"No school holidays for {canton}"

    def test_lu_has_sports_holidays(self):
        """LU has Sportferien (Feb/Mar)."""
        holidays = get_school_holidays(2026, "LU")
        names = [n for _, _, n in holidays]
        assert any("Sport" in n for n in names), f"No sports holidays in LU: {names}"


# ---------------------------------------------------------------------------
# is_school_holiday
# ---------------------------------------------------------------------------

class TestIsSchoolHoliday:
    def test_zh_summer_mid_july(self):
        """Mid-July should be school holiday in ZH."""
        is_hol, name = is_school_holiday(date(2026, 7, 20), "ZH")
        assert is_hol is True
        assert name is not None

    def test_regular_school_day_not_holiday(self):
        """A normal Tuesday in March should not be school holiday."""
        is_hol, _ = is_school_holiday(date(2026, 3, 3), "ZH")
        assert is_hol is False

    def test_returns_tuple(self):
        result = is_school_holiday(date(2026, 7, 20), "ZH")
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_lu_christmas_holidays_cross_year(self):
        """LU Christmas holidays: 20 Dec 2025 – 4 Jan 2026."""
        # 1 January is inside the Christmas holiday window for LU
        is_hol, name = is_school_holiday(date(2026, 1, 1), "LU")
        assert is_hol is True


# ---------------------------------------------------------------------------
# ICS data integrity
# ---------------------------------------------------------------------------

class TestIcsData:
    def test_ics_loaded_for_zh_2026(self):
        """ZH 2026 holidays come from ICS – should contain >5 entries."""
        hols = get_public_holidays(2026, "ZH")
        assert len(hols) >= 5

    def test_ics_loaded_for_ge_2026(self):
        hols = get_public_holidays(2026, "GE")
        assert len(hols) >= 5

    def test_all_cantons_have_ics_2026(self):
        cantons = [
            "AG","AI","AR","BE","BL","BS","FR","GE","GL","GR",
            "JU","LU","NE","NW","OW","SG","SH","SO","SZ","TG",
            "TI","UR","VD","VS","ZG","ZH"
        ]
        for canton in cantons:
            hols = get_public_holidays(2026, canton)
            assert len(hols) >= 3, f"Too few holidays for {canton}: {len(hols)}"
