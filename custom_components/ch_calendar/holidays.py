"""Swiss public holiday and school holiday calculations.

Priority:
  1. ICS files  (data/holidays/holidays_{canton}_{year}.ics)  -> exact public holidays
  2. JSON files (data/school/{school_year}.json)              -> exact school holidays
  3. Dynamic calculation via Computus (fallback for other years)
"""
from __future__ import annotations

import json
import os
import re
from datetime import date, timedelta
from functools import lru_cache
from typing import Optional

from .const import CANTON_HOLIDAYS, HOLIDAY_NAMES, SCHOOL_HOLIDAY_NAMES

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_HOLIDAYS_DIR = os.path.join(_DATA_DIR, "holidays")
_SCHOOL_DIR = os.path.join(_DATA_DIR, "school")


# ---------------------------------------------------------------------------
# Easter (Gregorian Computus) - used only as fallback
# ---------------------------------------------------------------------------

def easter_sunday(year: int) -> date:
    """Return Easter Sunday for given year."""
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
# Moving holidays (fallback only)
# ---------------------------------------------------------------------------

def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    d = date(year, month, 1)
    offset = (weekday - d.weekday()) % 7
    d = d + timedelta(days=offset)
    return d + timedelta(weeks=n - 1)

def _geneva_fast(year: int) -> date:
    return _nth_weekday(year, 9, 6, 1) + timedelta(days=4)

def _federal_fast(year: int) -> date:
    return _nth_weekday(year, 9, 6, 3) + timedelta(days=1)

def _knabenschiessen(year: int) -> date:
    return _nth_weekday(year, 9, 0, 3)


# ---------------------------------------------------------------------------
# ICS parser
# ---------------------------------------------------------------------------

def _parse_ics(path: str) -> dict[date, str]:
    """Parse an ICS file and return {date: summary}."""
    result: dict[date, str] = {}
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return result

    for block in content.split("BEGIN:VEVENT")[1:]:
        m_sum = re.search(r"SUMMARY:(.*)", block)
        m_start = re.search(r"DTSTART[^:]*:(\d{8})", block)
        if m_sum and m_start:
            s = m_start.group(1)
            try:
                d = date(int(s[:4]), int(s[4:6]), int(s[6:8]))
                summary = m_sum.group(1).strip()
                summary = summary.replace("\\,", ",").replace("\\;", ";").replace("\\\\", "\\")
                result[d] = summary
            except ValueError:
                pass
    return result


# ---------------------------------------------------------------------------
# Public holidays
# ---------------------------------------------------------------------------

@lru_cache(maxsize=128)
def _load_ics_holidays(year: int, canton: str) -> tuple:
    """Load public holidays from ICS - returns tuple of (date, name) pairs for caching."""
    path = os.path.join(_HOLIDAYS_DIR, f"holidays_{canton.lower()}_{year}.ics")
    parsed = _parse_ics(path)
    return tuple(parsed.items())


def get_public_holidays(year: int, canton: str) -> dict[date, str]:
    """Return {date: holiday_name} for given year and canton.
    Uses ICS file if available, otherwise dynamic calculation.
    """
    cached = _load_ics_holidays(year, canton)
    if cached:
        return dict(cached)

    # Dynamic fallback
    easter = easter_sunday(year)
    holidays: dict[date, str] = {}
    candidates: dict[str, date] = {
        "new_year":              date(year, 1, 1),
        "berchtoldstag":         date(year, 1, 2),
        "good_friday":           easter - timedelta(days=2),
        "easter_monday":         easter + timedelta(days=1),
        "labor_day":             date(year, 5, 1),
        "ascension":             easter + timedelta(days=39),
        "whit_monday":           easter + timedelta(days=50),
        "corpus_christi":        easter + timedelta(days=60),
        "national_day":          date(year, 8, 1),
        "assumption":            date(year, 8, 15),
        "all_saints":            date(year, 11, 1),
        "immaculate_conception": date(year, 12, 8),
        "christmas":             date(year, 12, 25),
        "boxing_day":            date(year, 12, 26),
        "restored_republic":     date(year, 12, 31),
        "geneva_fast":           _geneva_fast(year),
        "federal_fast":          _federal_fast(year),
        "st_nicholas_flue":      date(year, 9, 25),
        "knabenschiessen":       _knabenschiessen(year),
    }
    for key, holiday_date in candidates.items():
        cantons = CANTON_HOLIDAYS.get(key, set())
        if cantons == "ALL" or canton in cantons:
            holidays[holiday_date] = HOLIDAY_NAMES[key]
    return holidays


def is_public_holiday(d: date, canton: str) -> tuple[bool, Optional[str]]:
    name = get_public_holidays(d.year, canton).get(d)
    return (name is not None, name)


# ---------------------------------------------------------------------------
# School holidays - JSON loader
# ---------------------------------------------------------------------------

@lru_cache(maxsize=32)
def _load_school_json(school_year: int) -> dict:
    """Load school holiday JSON. school_year = calendar year of summer holidays."""
    path = os.path.join(_SCHOOL_DIR, f"{school_year}.json")
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except OSError:
        return {}


def _school_from_json(school_year: int, canton: str) -> list[tuple[date, date, str]]:
    data = _load_school_json(school_year)
    entries = data.get(canton.lower(), [])
    if not entries or not isinstance(entries, list):
        return []
    result = []
    for item in entries:
        try:
            start = date.fromisoformat(item["start"])
            end = date.fromisoformat(item["end"])
            name = item.get("name", "School Holiday")
            result.append((start, end, name))
        except (KeyError, ValueError):
            pass
    return result


# ---------------------------------------------------------------------------
# School holidays - dynamic fallback
# ---------------------------------------------------------------------------

def _school_dynamic(year: int, canton: str) -> list[tuple[date, date, str]]:
    easter = easter_sunday(year)
    holidays: list[tuple[date, date, str]] = []

    def add(start: date, end: date, name_key: str) -> None:
        if start <= end:
            holidays.append((start, end, SCHOOL_HOLIDAY_NAMES[name_key]))

    summer_map = {
        "ZH": ((7, 13), (8, 14)), "BE": ((7, 7), (8, 9)),
        "LU": ((6, 27), (8, 9)),  "UR": ((6, 27), (8, 9)),
        "SZ": ((7, 4), (8, 9)),   "OW": ((6, 27), (8, 9)),
        "NW": ((6, 27), (8, 9)),  "GL": ((6, 27), (8, 9)),
        "ZG": ((6, 29), (8, 8)),  "FR": ((7, 10), (8, 26)),
        "SO": ((7, 4), (8, 9)),   "BS": ((6, 29), (8, 8)),
        "BL": ((6, 29), (8, 7)),  "SH": ((6, 29), (8, 9)),
        "AR": ((7, 6), (8, 7)),   "AI": ((7, 4), (8, 16)),
        "SG": ((6, 27), (8, 16)), "GR": ((6, 27), (8, 16)),
        "AG": ((7, 6), (8, 7)),   "TG": ((6, 27), (8, 9)),
        "TI": ((6, 22), (8, 29)), "VD": ((7, 4), (8, 23)),
        "VS": ((6, 27), (8, 16)), "NE": ((6, 27), (8, 16)),
        "GE": ((6, 27), (8, 16)), "JU": ((7, 6), (8, 16)),
    }
    sm = summer_map.get(canton, ((7, 7), (8, 16)))
    add(date(year, sm[0][0], sm[0][1]), date(year, sm[1][0], sm[1][1]), "summer")

    autumn_map = {
        "ZH": ((10, 5), (10, 16)),  "BE": ((9, 20), (10, 11)),
        "LU": ((10, 3), (10, 18)),  "UR": ((10, 4), (10, 19)),
        "SZ": ((9, 26), (10, 11)), "OW": ((10, 4), (10, 19)),
        "NW": ((10, 4), (10, 19)), "GL": ((10, 4), (10, 19)),
        "ZG": ((10, 4), (10, 19)), "FR": ((10, 13), (10, 24)),
        "SO": ((9, 26), (10, 11)), "BS": ((9, 29), (10, 10)),
        "BL": ((9, 29), (10, 10)), "SH": ((10, 4), (10, 19)),
        "AR": ((10, 6), (10, 17)), "AI": ((10, 6), (10, 17)),
        "SG": ((10, 4), (10, 19)), "GR": ((10, 4), (10, 19)),
        "AG": ((9, 29), (10, 10)), "TG": ((10, 3), (10, 18)),
        "TI": ((10, 11), (10, 25)),"VD": ((10, 31), (11, 8)),
        "VS": ((10, 11), (10, 25)),"NE": ((10, 10), (10, 25)),
        "GE": ((10, 18), (10, 26)),"JU": ((10, 11), (10, 18)),
    }
    am = autumn_map.get(canton, ((10, 5), (10, 16)))
    add(date(year, am[0][0], am[0][1]), date(year, am[1][0], am[1][1]), "autumn")

    christmas_map = {
        "ZH": ((12, 24), (1, 2)),  "BE": ((12, 20), (1, 4)),
        "LU": ((12, 20), (1, 4)),  "UR": ((12, 20), (1, 4)),
        "SZ": ((12, 25), (1, 6)),  "OW": ((12, 22), (1, 3)),
        "NW": ((12, 20), (1, 4)),  "GL": ((12, 20), (1, 4)),
        "ZG": ((12, 20), (1, 4)),  "FR": ((12, 22), (1, 2)),
        "SO": ((12, 20), (1, 4)),  "BS": ((12, 22), (1, 4)),
        "BL": ((12, 22), (1, 4)),  "SH": ((12, 20), (1, 4)),
        "AR": ((12, 22), (1, 2)),  "AI": ((12, 22), (1, 4)),
        "SG": ((12, 22), (1, 4)),  "GR": ((12, 20), (1, 4)),
        "AG": ((12, 21), (12, 31)),"TG": ((12, 20), (1, 4)),
        "TI": ((12, 22), (1, 3)),  "VD": ((12, 22), (1, 4)),
        "VS": ((12, 20), (1, 4)),  "NE": ((12, 20), (1, 4)),
        "GE": ((12, 20), (1, 4)),  "JU": ((12, 22), (1, 4)),
    }
    cm = christmas_map.get(canton, ((12, 22), (1, 4)))
    add(date(year, cm[0][0], cm[0][1]), date(year + 1, cm[1][0], cm[1][1]), "christmas")

    sports_map = {
        "ZH": ((2, 9), (2, 20)),  "LU": ((2, 14), (3, 1)),
        "UR": ((2, 14), (2, 27)), "SZ": ((2, 21), (3, 1)),
        "OW": ((2, 14), (2, 20)), "NW": ((2, 14), (3, 1)),
        "GL": ((1, 24), (2, 1)),  "ZG": ((2, 14), (2, 27)),
        "FR": ((2, 16), (2, 20)), "SO": ((2, 9), (2, 20)),
        "BS": ((2, 16), (2, 27)), "BL": ((2, 16), (2, 27)),
        "AI": ((2, 9), (2, 20)),  "SH": ((2, 14), (2, 27)),
        "TI": ((2, 16), (2, 28)), "TG": ((2, 14), (3, 1)),
        "VD": ((2, 16), (2, 27)), "VS": ((2, 9), (2, 20)),
        "NE": ((2, 16), (2, 27)), "GE": ((2, 21), (3, 1)),
        "JU": ((2, 16), (2, 20)), "SG": ((2, 21), (3, 1)),
        "GR": ((2, 21), (3, 1)),
    }
    sp = sports_map.get(canton)
    if sp:
        add(date(year, sp[0][0], sp[0][1]), date(year, sp[1][0], sp[1][1]), "sports")

    spring_map = {
        "ZH": (-2, 13),  "BE": (-3, 16), "LU": (-7, 5),
        "UR": (-3, 14),  "SZ": (22, 37), "OW": (-3, 14),
        "NW": (-3, 14),  "GL": (-3, 16), "ZG": (-3, 14),
        "FR": (-3, 14),  "SO": (-3, 14), "BS": (-3, 7),
        "BL": (-3, 7),   "SH": (-3, 14), "AR": (-3, 14),
        "AI": (-3, 14),  "SG": (13, 28), "GR": (13, 28),
        "AG": (-3, 10),  "TG": (-3, 14), "TI": (-3, 16),
        "VD": (-3, 14),  "VS": (-3, 14), "NE": (-3, 14),
        "GE": (-3, 16),  "JU": (-3, 14),
    }
    sr = spring_map.get(canton, (-3, 14))
    add(easter + timedelta(days=sr[0]), easter + timedelta(days=sr[1]), "spring")

    return holidays


# ---------------------------------------------------------------------------
# School holidays - main API
# ---------------------------------------------------------------------------

def get_school_holidays(year: int, canton: str) -> list[tuple[date, date, str]]:
    """Return list of (start, end, name) school holiday periods.

    'year' is the calendar year in which summer holidays occur
    (e.g. 2026 = school year 2025/26).
    Uses JSON data if available, otherwise dynamic fallback.
    """
    from_json = _school_from_json(year, canton)
    if from_json:
        return from_json
    return _school_dynamic(year, canton)


def is_school_holiday(d: date, canton: str) -> tuple[bool, Optional[str]]:
    """Check if date is a school holiday for the given canton."""
    for year in (d.year - 1, d.year):
        for start, end, name in get_school_holidays(year, canton):
            if start <= d <= end:
                return True, name
    return False, None
