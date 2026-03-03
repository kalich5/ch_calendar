"""Swiss public holiday and school holiday calculations."""
from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from .const import CANTON_HOLIDAYS, HOLIDAY_NAMES, SCHOOL_HOLIDAY_NAMES


# ---------------------------------------------------------------------------
# Easter (Gregorian Computus)
# ---------------------------------------------------------------------------

def easter_sunday(year: int) -> date:
    """Return Easter Sunday for given year using the Anonymous Gregorian algorithm."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


# ---------------------------------------------------------------------------
# Moving holidays
# ---------------------------------------------------------------------------

def nth_weekday_of_month(year: int, month: int, weekday: int, n: int) -> date:
    """Return the n-th occurrence of weekday (0=Mon…6=Sun) in year/month."""
    d = date(year, month, 1)
    offset = (weekday - d.weekday()) % 7
    d = d + timedelta(days=offset)
    return d + timedelta(weeks=n - 1)


def first_sunday_of_month(year: int, month: int) -> date:
    return nth_weekday_of_month(year, month, 6, 1)


def third_sunday_of_month(year: int, month: int) -> date:
    return nth_weekday_of_month(year, month, 6, 3)


def geneva_fast_date(year: int) -> date:
    """Geneva Fast: Thursday after the first Sunday of September."""
    first_sun = first_sunday_of_month(year, 9)
    return first_sun + timedelta(days=4)


def federal_fast_date(year: int) -> date:
    """Federal Fast (Vaud): Monday after the third Sunday of September."""
    third_sun = third_sunday_of_month(year, 9)
    return third_sun + timedelta(days=1)


def knabenschiessen_date(year: int) -> date:
    """Knabenschiessen (Zürich): Third Monday of September."""
    return nth_weekday_of_month(year, 9, 0, 3)


def corpus_christi_date(year: int) -> date:
    """Corpus Christi: 60 days after Easter Sunday."""
    return easter_sunday(year) + timedelta(days=60)


# ---------------------------------------------------------------------------
# Public holidays for a given year and canton
# ---------------------------------------------------------------------------

def get_public_holidays(year: int, canton: str) -> dict[date, str]:
    """Return {date: holiday_name} for the given year and canton."""
    easter = easter_sunday(year)
    holidays: dict[date, str] = {}

    candidate: dict[str, date] = {
        "new_year":              date(year, 1, 1),
        "berchtoldstag":         date(year, 1, 2),
        "good_friday":           easter - timedelta(days=2),
        "easter_monday":         easter + timedelta(days=1),
        "labor_day":             date(year, 5, 1),
        "ascension":             easter + timedelta(days=39),
        "whit_monday":           easter + timedelta(days=50),
        "corpus_christi":        corpus_christi_date(year),
        "national_day":          date(year, 8, 1),
        "assumption":            date(year, 8, 15),
        "all_saints":            date(year, 11, 1),
        "immaculate_conception": date(year, 12, 8),
        "christmas":             date(year, 12, 25),
        "boxing_day":            date(year, 12, 26),
        "restored_republic":     date(year, 12, 31),
        "geneva_fast":           geneva_fast_date(year),
        "federal_fast":          federal_fast_date(year),
        "st_nicholas_flue":      date(year, 9, 25),
        "knabenschiessen":       knabenschiessen_date(year),
    }

    for key, holiday_date in candidate.items():
        cantons = CANTON_HOLIDAYS.get(key, set())
        if cantons == "ALL" or canton in cantons:
            holidays[holiday_date] = HOLIDAY_NAMES[key]

    return holidays


def is_public_holiday(d: date, canton: str) -> tuple[bool, Optional[str]]:
    """Check if a date is a public holiday for the given canton."""
    holidays = get_public_holidays(d.year, canton)
    name = holidays.get(d)
    return (name is not None, name)


# ---------------------------------------------------------------------------
# School holidays per canton
# Based on typical/official dates for 2024-2026; uses a rolling window
# approach for future years based on known patterns.
# ---------------------------------------------------------------------------

def _week_start(year: int, week: int) -> date:
    """Return the Monday of ISO week 'week' in 'year'."""
    jan4 = date(year, 1, 4)
    start_of_week1 = jan4 - timedelta(days=jan4.weekday())
    return start_of_week1 + timedelta(weeks=week - 1)


def get_school_holidays(year: int, canton: str) -> list[tuple[date, date, str]]:
    """
    Return list of (start_date, end_date, name) school holiday periods
    for the given canton and school year starting in 'year'.
    Dates are inclusive. End date is the last day of the holiday.
    """
    easter = easter_sunday(year)
    holidays: list[tuple[date, date, str]] = []

    # --- Helper to add a holiday ---
    def add(start: date, end: date, name_key: str) -> None:
        if start <= end:
            holidays.append((start, end, SCHOOL_HOLIDAY_NAMES[name_key]))

    # -----------------------------------------------------------------------
    # Summer holidays (July–August, canton specific)
    # -----------------------------------------------------------------------
    summer_map: dict[str, tuple[tuple[int, int], tuple[int, int]]] = {
        # (month_start, day_start), (month_end, day_end)
        "ZH": ((7, 7), (8, 10)),
        "BE": ((7, 7), (8, 9)),
        "LU": ((7, 7), (8, 16)),
        "UR": ((7, 7), (8, 16)),
        "SZ": ((7, 7), (8, 16)),
        "OW": ((7, 7), (8, 16)),
        "NW": ((7, 7), (8, 16)),
        "GL": ((7, 7), (8, 16)),
        "ZG": ((7, 7), (8, 16)),
        "FR": ((7, 14), (8, 21)),
        "SO": ((7, 7), (8, 16)),
        "BS": ((6, 30), (8, 8)),
        "BL": ((7, 7), (8, 10)),
        "SH": ((7, 7), (8, 16)),
        "AR": ((7, 7), (8, 7)),
        "AI": ((7, 7), (8, 16)),
        "SG": ((7, 7), (8, 16)),
        "GR": ((7, 7), (8, 16)),  # varies by municipality; approx
        "AG": ((7, 20), (8, 7)),
        "TG": ((7, 7), (8, 16)),
        "TI": ((6, 15), (9, 5)),
        "VD": ((7, 7), (8, 28)),
        "VS": ((7, 7), (8, 14)),
        "NE": ((7, 7), (8, 14)),
        "GE": ((7, 7), (8, 21)),
        "JU": ((7, 7), (8, 14)),
    }
    sm = summer_map.get(canton, ((7, 7), (8, 16)))
    add(date(year, sm[0][0], sm[0][1]), date(year, sm[1][0], sm[1][1]), "summer")

    # -----------------------------------------------------------------------
    # Autumn holidays (October, canton specific)
    # -----------------------------------------------------------------------
    autumn_map: dict[str, tuple[tuple[int, int], tuple[int, int]]] = {
        "ZH": ((10, 5), (10, 16)),
        "BE": ((9, 20), (10, 11)),
        "LU": ((10, 3), (10, 16)),
        "UR": ((9, 26), (10, 11)),
        "SZ": ((9, 26), (10, 11)),
        "OW": ((9, 26), (10, 11)),
        "NW": ((9, 26), (10, 11)),
        "GL": ((9, 26), (10, 11)),
        "ZG": ((9, 26), (10, 11)),
        "FR": ((10, 12), (10, 23)),
        "SO": ((10, 5), (10, 16)),
        "BS": ((10, 3), (10, 16)),
        "BL": ((10, 3), (10, 12)),
        "SH": ((10, 5), (10, 16)),
        "AR": ((10, 5), (10, 16)),
        "AI": ((9, 26), (10, 18)),
        "SG": ((10, 5), (10, 16)),
        "GR": ((10, 31), (11, 8)),
        "AG": ((9, 28), (10, 9)),
        "TG": ((10, 5), (10, 16)),
        "TI": ((10, 26), (10, 30)),
        "VD": ((10, 12), (10, 23)),
        "VS": ((10, 19), (10, 30)),
        "NE": ((10, 5), (10, 16)),
        "GE": ((10, 12), (10, 23)),
        "JU": ((10, 5), (10, 16)),
    }
    am = autumn_map.get(canton, ((10, 5), (10, 16)))
    add(date(year, am[0][0], am[0][1]), date(year, am[1][0], am[1][1]), "autumn")

    # -----------------------------------------------------------------------
    # Christmas holidays (December–January)
    # Stored as start in current year, end in next year
    # -----------------------------------------------------------------------
    christmas_map: dict[str, tuple[tuple[int, int], tuple[int, int]]] = {
        "ZH": ((12, 24), (1, 2)),
        "BE": ((12, 24), (1, 4)),
        "LU": ((12, 21), (1, 4)),
        "UR": ((12, 21), (1, 4)),
        "SZ": ((12, 21), (1, 4)),
        "OW": ((12, 21), (1, 4)),
        "NW": ((12, 21), (1, 4)),
        "GL": ((12, 21), (1, 2)),
        "ZG": ((12, 21), (1, 4)),
        "FR": ((12, 22), (1, 4)),
        "SO": ((12, 21), (1, 4)),
        "BS": ((12, 20), (1, 3)),
        "BL": ((12, 20), (1, 4)),
        "SH": ((12, 21), (1, 4)),
        "AR": ((12, 21), (1, 1)),
        "AI": ((12, 21), (1, 4)),
        "SG": ((12, 21), (1, 4)),
        "GR": ((12, 24), (1, 6)),
        "AG": ((12, 21), (12, 31)),
        "TG": ((12, 21), (1, 4)),
        "TI": ((12, 24), (1, 6)),
        "VD": ((12, 22), (1, 4)),
        "VS": ((12, 22), (1, 9)),
        "NE": ((12, 21), (1, 1)),
        "GE": ((12, 22), (1, 4)),
        "JU": ((12, 24), (1, 8)),
    }
    cm = christmas_map.get(canton, ((12, 22), (1, 4)))
    add(
        date(year, cm[0][0], cm[0][1]),
        date(year + 1, cm[1][0], cm[1][1]),
        "christmas"
    )

    # -----------------------------------------------------------------------
    # Sports / Winter holidays (February, canton specific)
    # -----------------------------------------------------------------------
    sports_map: dict[str, tuple[tuple[int, int], tuple[int, int]] | None] = {
        "ZH": None,  # no sports holidays
        "BE": None,
        "LU": ((2, 7), (2, 22)),
        "UR": ((2, 7), (2, 22)),
        "SZ": ((2, 7), (2, 22)),
        "OW": ((2, 12), (2, 22)),
        "NW": ((2, 7), (2, 22)),
        "GL": ((2, 14), (2, 28)),
        "ZG": ((2, 14), (2, 28)),
        "FR": ((2, 16), (2, 20)),
        "SO": ((2, 14), (2, 28)),
        "BS": ((2, 14), (2, 28)),
        "BL": ((2, 14), (3, 2)),
        "SH": None,
        "AR": None,
        "AI": ((1, 24), (2, 1)),
        "SG": None,
        "GR": None,
        "AG": None,
        "TG": None,
        "TI": ((2, 14), (2, 28)),
        "VD": ((2, 14), (2, 28)),
        "VS": ((2, 14), (2, 28)),
        "NE": ((2, 23), (2, 27)),
        "GE": ((2, 14), (2, 28)),
        "JU": ((2, 16), (2, 20)),
    }
    sp = sports_map.get(canton)
    if sp is not None:
        add(date(year, sp[0][0], sp[0][1]), date(year, sp[1][0], sp[1][1]), "sports")

    # -----------------------------------------------------------------------
    # Spring / Easter holidays (Easter-relative, canton specific)
    # -----------------------------------------------------------------------
    spring_map: dict[str, tuple[int, int]] = {
        # (days_before_easter, days_after_easter) – relative to Good Friday
        "ZH": (-2, 13),   # Good Friday to Monday after Easter+1 week
        "BE": (-3, 16),
        "LU": (-3, 16),
        "UR": (-3, 16),
        "SZ": (-3, 16),
        "OW": (-3, 16),
        "NW": (-3, 16),
        "GL": (-3, 16),
        "ZG": (-3, 16),
        "FR": (-3, 14),
        "SO": (-3, 14),
        "BS": (-3, 8),
        "BL": (-3, 14),
        "SH": (-3, 14),
        "AR": (-3, 14),
        "AI": (-3, 16),
        "SG": (-3, 14),
        "GR": (-3, 16),
        "AG": (-3, 10),
        "TG": (-3, 14),
        "TI": (-3, 14),
        "VD": (-3, 14),
        "VS": (-3, 14),
        "NE": (-3, 14),
        "GE": (-3, 14),
        "JU": (-3, 14),
    }
    sr = spring_map.get(canton, (-3, 14))
    spring_start = easter + timedelta(days=sr[0])
    spring_end = easter + timedelta(days=sr[1])
    add(spring_start, spring_end, "spring")

    return holidays


def is_school_holiday(d: date, canton: str) -> tuple[bool, Optional[str]]:
    """Check if date is a school holiday for the given canton."""
    # Check school year starting in current year and previous year (for Jan holidays)
    for year in (d.year - 1, d.year):
        for start, end, name in get_school_holidays(year, canton):
            if start <= d <= end:
                return True, name
    return False, None
