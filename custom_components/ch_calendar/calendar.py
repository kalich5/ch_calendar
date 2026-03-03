"""Calendar platform for CH School & Work Calendar."""
from __future__ import annotations
import re
from datetime import date, datetime, timedelta
from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import CONF_BIRTHDAYS, CONF_CANTON, CONF_FAMILY_HOLIDAYS, DOMAIN
from .holidays import get_public_holidays, get_school_holidays


def _parse_custom(raw):
    results = []
    if not raw:
        return results
    lines = [l.strip() for l in raw.replace("\r","").split("\n") if l.strip()]
    import re
    D = re.compile(r"^(\d{1,2})\.(\d{1,2})$")
    I = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
    for line in lines:
        tokens = re.split(r"\s*\|\s*", line)
        i = 0
        while i < len(tokens)-1:
            ds, nm = tokens[i].strip(), tokens[i+1].strip()
            if not nm: i+=1; continue
            m = D.match(ds)
            if m: results.append(((int(m.group(2)),int(m.group(1))),nm)); i+=2; continue
            m = I.match(ds)
            if m:
                try: results.append((date(int(m.group(1)),int(m.group(2)),int(m.group(3))),nm)); i+=2; continue
                except ValueError: pass
            i+=1
    return results


async def async_setup_entry(hass, entry, async_add_entities):
    canton = entry.data.get(CONF_CANTON,"ZH")
    opts = entry.options
    async_add_entities([
        HolCal(entry, canton),
        VacCal(entry, canton),
        ComCal(entry, canton),
        CustCal(entry, canton, opts.get(CONF_BIRTHDAYS,""), opts.get(CONF_FAMILY_HOLIDAYS,"")),
    ], True)


class HolCal(CalendarEntity):
    _attr_icon = "mdi:calendar-star"
    def __init__(self, e, c):
        self._entry=e; self._canton=c
        self._attr_unique_id=f"{e.entry_id}_cal_h"
        self._attr_name="Swiss Public Holidays"; self._event=None
    @property
    def event(self): return self._event
    async def async_get_events(self, hass, s, e):
        ev=[]
        for yr in range(s.year,e.year+1):
            for d,n in get_public_holidays(yr,self._canton).items():
                if s.date()<=d<=e.date(): ev.append(CalendarEvent(start=d,end=d+timedelta(days=1),summary=n))
        return ev
    async def async_update(self):
        t=date.today()
        for yr in (t.year,t.year+1):
            h=get_public_holidays(yr,self._canton)
            for d in sorted(h):
                if d>=t: self._event=CalendarEvent(start=d,end=d+timedelta(days=1),summary=h[d]); return
        self._event=None


class VacCal(CalendarEntity):
    _attr_icon = "mdi:beach"
    def __init__(self, e, c):
        self._entry=e; self._canton=c
        self._attr_unique_id=f"{e.entry_id}_cal_v"
        self._attr_name="Swiss School Vacations"; self._event=None
    @property
    def event(self): return self._event
    async def async_get_events(self, hass, s, e):
        ev=[]
        for yr in range(s.year-1,e.year+2):
            for st,en,n in get_school_holidays(yr,self._canton):
                if st<=e.date() and en+timedelta(days=1)>=s.date():
                    ev.append(CalendarEvent(start=st,end=en+timedelta(days=1),summary=n))
        return ev
    async def async_update(self):
        t=date.today()
        for yr in (t.year-1,t.year,t.year+1):
            for s,e,n in sorted(get_school_holidays(yr,self._canton)):
                if s>=t: self._event=CalendarEvent(start=s,end=e+timedelta(days=1),summary=n); return
        self._event=None


class ComCal(CalendarEntity):
    _attr_icon = "mdi:calendar-multiple"
    def __init__(self, e, c):
        self._entry=e; self._canton=c
        self._attr_unique_id=f"{e.entry_id}_cal_c"
        self._attr_name="Swiss Holidays & Vacations"; self._event=None
    @property
    def event(self): return self._event
    async def async_get_events(self, hass, s, e):
        ev=[]
        for yr in range(s.year,e.year+1):
            for d,n in get_public_holidays(yr,self._canton).items():
                if s.date()<=d<=e.date(): ev.append(CalendarEvent(start=d,end=d+timedelta(days=1),summary=n))
        for yr in range(s.year-1,e.year+2):
            for st,en,n in get_school_holidays(yr,self._canton):
                if st<=e.date() and en+timedelta(days=1)>=s.date():
                    ev.append(CalendarEvent(start=st,end=en+timedelta(days=1),summary=n))
        return ev
    async def async_update(self):
        t=date.today(); c=[]
        for yr in (t.year,t.year+1):
            for d,n in get_public_holidays(yr,self._canton).items():
                if d>=t: c.append((d,d+timedelta(days=1),n))
        for yr in (t.year-1,t.year,t.year+1):
            for s,e,n in get_school_holidays(yr,self._canton):
                if s>=t: c.append((s,e+timedelta(days=1),n))
        if c: s,e,n=min(c,key=lambda x:x[0]); self._event=CalendarEvent(start=s,end=e,summary=n)
        else: self._event=None


class CustCal(CalendarEntity):
    _attr_icon = "mdi:account-heart"
    def __init__(self, e, c, br, fr):
        self._entry=e; self._canton=c; self._br=br; self._fr=fr
        self._attr_unique_id=f"{e.entry_id}_cal_cust"
        self._attr_name="Swiss Custom Events"; self._event=None
    def _evts(self, s, e):
        ev=[]
        for raw in (self._br, self._fr):
            for ed,n in _parse_custom(raw):
                if isinstance(ed,date):
                    if s<=ed<=e: ev.append(CalendarEvent(start=ed,end=ed+timedelta(days=1),summary=n))
                else:
                    mo,dy=ed
                    for yr in range(s.year,e.year+1):
                        try: d=date(yr,mo,dy)
                        except ValueError: continue
                        if s<=d<=e: ev.append(CalendarEvent(start=d,end=d+timedelta(days=1),summary=n))
        return ev
    @property
    def event(self): return self._event
    async def async_get_events(self, hass, s, e): return self._evts(s.date(), e.date())
    async def async_update(self):
        t=date.today(); evts=sorted(self._evts(t,t+timedelta(days=365)),key=lambda x:x.start)
        self._event=evts[0] if evts else None
