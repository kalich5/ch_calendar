"""Sensor platform for CH School & Work Calendar - part 1."""
from __future__ import annotations
import re
from datetime import date
from typing import Any
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_change
from .const import CONF_BIRTHDAYS, CONF_CANTON, CONF_FAMILY_HOLIDAYS, DOMAIN
from .holidays import get_public_holidays, get_school_holidays, is_public_holiday, is_school_holiday


def _parse_custom(raw: str) -> list:
    results = []
    if not raw:
        return results
    lines = [l.strip() for l in raw.replace("\r","").split("\n") if l.strip()]
    D = re.compile(r"^(\d{1,2})\.(\d{1,2})$")
    I = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
    for line in lines:
        tokens = re.split(r"\s*\|\s*", line)
        i = 0
        while i < len(tokens) - 1:
            ds, name = tokens[i].strip(), tokens[i+1].strip()
            if not name:
                i += 1; continue
            m = D.match(ds)
            if m:
                results.append(((int(m.group(2)), int(m.group(1))), name)); i += 2; continue
            m = I.match(ds)
            if m:
                try:
                    d = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                    results.append((d, name)); i += 2; continue
                except ValueError:
                    pass
            i += 1
    return results


def _next_occ(entry_date, today: date):
    if isinstance(entry_date, date):
        return entry_date, (entry_date - today).days
    month, day = entry_date
    for year in (today.year, today.year + 1):
        try:
            c = date(year, month, day)
        except ValueError:
            continue
        if c >= today:
            return c, (c - today).days
    return None, -1


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    canton = entry.data.get(CONF_CANTON, "ZH")
    opts = entry.options
    b_raw = opts.get(CONF_BIRTHDAYS, "")
    f_raw = opts.get(CONF_FAMILY_HOLIDAYS, "")
    entities = [
        WorkdaySensor(entry, canton),
        SchoolDaySensor(entry, canton),
        HolidaySensor(entry, canton),
        VacationSensor(entry, canton),
        HolidayNameSensor(entry, canton),
        VacationNameSensor(entry, canton),
        NextHolidaySensor(entry, canton),
        DaysToHolidaySensor(entry, canton),
        NextVacationSensor(entry, canton),
        DaysToVacationSensor(entry, canton),
        NextBirthdaySensor(entry, canton, b_raw),
        DaysToBirthdaySensor(entry, canton, b_raw),
        NextFamilySensor(entry, canton, f_raw),
        DaysToFamilySensor(entry, canton, f_raw),
    ]
    async_add_entities(entities, True)


class Base(SensorEntity):
    def __init__(self, entry: ConfigEntry, canton: str) -> None:
        self._entry = entry; self._canton = canton
        self._attr_extra_state_attributes: dict[str, Any] = {}

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self._entry.entry_id)}, "name": f"CH Calendar ({self._canton})", "manufacturer": "Custom Integration", "model": "CH School & Work Calendar"}

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(async_track_time_change(self.hass, self._upd, hour=0, minute=0, second=5))

    async def _upd(self, _now) -> None:
        self.async_schedule_update_ha_state(True)


class WorkdaySensor(Base):
    _attr_icon = "mdi:briefcase"
    def __init__(self, e, c): super().__init__(e, c); self._attr_unique_id = f"{e.entry_id}_workday"; self._attr_name = "Workday"
    def update(self):
        t = date.today(); wk = t.weekday() >= 5; h, _ = is_public_holiday(t, self._canton)
        self._attr_native_value = str(not (wk or h))


class SchoolDaySensor(Base):
    _attr_icon = "mdi:school"
    def __init__(self, e, c): super().__init__(e, c); self._attr_unique_id = f"{e.entry_id}_school_day"; self._attr_name = "School Day"
    def update(self):
        t = date.today(); wk = t.weekday() >= 5; h, _ = is_public_holiday(t, self._canton); v, _ = is_school_holiday(t, self._canton)
        self._attr_native_value = str(not (wk or h or v))


class HolidaySensor(Base):
    _attr_icon = "mdi:star"
    def __init__(self, e, c): super().__init__(e, c); self._attr_unique_id = f"{e.entry_id}_holiday"; self._attr_name = "Holiday"
    def update(self):
        h, n = is_public_holiday(date.today(), self._canton)
        self._attr_native_value = str(h); self._attr_extra_state_attributes = {"holiday_name": n}


class VacationSensor(Base):
    _attr_icon = "mdi:beach"
    def __init__(self, e, c): super().__init__(e, c); self._attr_unique_id = f"{e.entry_id}_vacation"; self._attr_name = "Vacation"
    def update(self):
        v, n = is_school_holiday(date.today(), self._canton)
        self._attr_native_value = str(v); self._attr_extra_state_attributes = {"vacation_name": n}


class HolidayNameSensor(Base):
    _attr_icon = "mdi:calendar-star"
    def __init__(self, e, c): super().__init__(e, c); self._attr_unique_id = f"{e.entry_id}_holiday_name"; self._attr_name = "Holiday Name"
    def update(self):
        _, n = is_public_holiday(date.today(), self._canton); self._attr_native_value = n


class VacationNameSensor(Base):
    _attr_icon = "mdi:calendar-clock"
    def __init__(self, e, c): super().__init__(e, c); self._attr_unique_id = f"{e.entry_id}_vacation_name"; self._attr_name = "Vacation Name"
    def update(self):
        _, n = is_school_holiday(date.today(), self._canton); self._attr_native_value = n


class NextHolidaySensor(Base):
    _attr_icon = "mdi:calendar-arrow-right"
    def __init__(self, e, c): super().__init__(e, c); self._attr_unique_id = f"{e.entry_id}_next_holiday"; self._attr_name = "Next Holiday"
    def update(self):
        t = date.today()
        for yr in (t.year, t.year + 1):
            for d in sorted(get_public_holidays(yr, self._canton)):
                if d > t: self._attr_native_value = get_public_holidays(yr, self._canton)[d]; self._attr_extra_state_attributes = {"date": str(d)}; return
        self._attr_native_value = None


class DaysToHolidaySensor(Base):
    _attr_icon = "mdi:counter"
    def __init__(self, e, c): super().__init__(e, c); self._attr_unique_id = f"{e.entry_id}_days_to_holiday"; self._attr_name = "Days to Holiday"
    def update(self):
        t = date.today()
        for yr in (t.year, t.year + 1):
            hols = get_public_holidays(yr, self._canton)
            for d in sorted(hols):
                if d > t: self._attr_native_value = (d - t).days; self._attr_extra_state_attributes = {"next_holiday": hols[d], "date": str(d)}; return
        self._attr_native_value = None


class NextVacationSensor(Base):
    _attr_icon = "mdi:airplane-takeoff"
    def __init__(self, e, c): super().__init__(e, c); self._attr_unique_id = f"{e.entry_id}_next_vacation"; self._attr_name = "Next Vacation"
    def update(self):
        t = date.today()
        for yr in (t.year - 1, t.year, t.year + 1):
            for s, e, n in sorted(get_school_holidays(yr, self._canton)):
                if s > t: self._attr_native_value = n; self._attr_extra_state_attributes = {"start": str(s), "end": str(e)}; return
        self._attr_native_value = None


class DaysToVacationSensor(Base):
    _attr_icon = "mdi:counter"
    def __init__(self, e, c): super().__init__(e, c); self._attr_unique_id = f"{e.entry_id}_days_to_vacation"; self._attr_name = "Days to Vacation"
    def update(self):
        t = date.today()
        for yr in (t.year - 1, t.year, t.year + 1):
            for s, e, n in sorted(get_school_holidays(yr, self._canton)):
                if s > t: self._attr_native_value = (s - t).days; self._attr_extra_state_attributes = {"next_vacation": n, "start": str(s)}; return
        self._attr_native_value = None


class NextBirthdaySensor(Base):
    _attr_icon = "mdi:cake-variant"
    def __init__(self, e, c, raw): super().__init__(e, c); self._raw = raw; self._attr_unique_id = f"{e.entry_id}_next_birthday"; self._attr_name = "Next Birthday"
    def update(self):
        t = date.today(); evts = _parse_custom(self._raw); bd, bn, bdays = None, None, 9999
        for ed, name in evts:
            d, days = _next_occ(ed, t)
            if d and 0 <= days < bdays: bdays, bd, bn = days, d, name
        self._attr_native_value = bn; self._attr_extra_state_attributes = {"date": str(bd) if bd else None, "days": bdays if bn else None}


class DaysToBirthdaySensor(Base):
    _attr_icon = "mdi:counter"
    def __init__(self, e, c, raw): super().__init__(e, c); self._raw = raw; self._attr_unique_id = f"{e.entry_id}_days_to_birthday"; self._attr_name = "Days to Birthday"
    def update(self):
        t = date.today(); evts = _parse_custom(self._raw); bd, bn, bdays = None, None, 9999
        for ed, name in evts:
            d, days = _next_occ(ed, t)
            if d and 0 <= days < bdays: bdays, bd, bn = days, d, name
        self._attr_native_value = bdays if bn else None; self._attr_extra_state_attributes = {"next_birthday": bn, "date": str(bd) if bd else None}


class NextFamilySensor(Base):
    _attr_icon = "mdi:account-group"
    def __init__(self, e, c, raw): super().__init__(e, c); self._raw = raw; self._attr_unique_id = f"{e.entry_id}_next_family"; self._attr_name = "Next Family Holiday"
    def update(self):
        t = date.today(); evts = _parse_custom(self._raw); bd, bn, bdays = None, None, 9999
        for ed, name in evts:
            d, days = _next_occ(ed, t)
            if d and 0 <= days < bdays: bdays, bd, bn = days, d, name
        self._attr_native_value = bn; self._attr_extra_state_attributes = {"date": str(bd) if bd else None, "days": bdays if bn else None}


class DaysToFamilySensor(Base):
    _attr_icon = "mdi:counter"
    def __init__(self, e, c, raw): super().__init__(e, c); self._raw = raw; self._attr_unique_id = f"{e.entry_id}_days_to_family"; self._attr_name = "Days to Family Holiday"
    def update(self):
        t = date.today(); evts = _parse_custom(self._raw); bd, bn, bdays = None, None, 9999
        for ed, name in evts:
            d, days = _next_occ(ed, t)
            if d and 0 <= days < bdays: bdays, bd, bn = days, d, name
        self._attr_native_value = bdays if bn else None; self._attr_extra_state_attributes = {"next_family_holiday": bn, "date": str(bd) if bd else None}
