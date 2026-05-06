#!/usr/bin/env -S uv run --quiet --with icalendar --with recurring-ical-events --with python-dateutil --with httpx python3
"""
caldav_lookup.py — résout un datetime → event de calendrier (lecture seule).

Mode unique : flux iCal (`text/calendar`) public ou authentifié, fetché via HTTP.
Compatible avec les shares de la plupart des plateformes calendrier
(OX App Suite, Google Calendar, iCloud, etc.).

Usage:
    caldav_lookup.py --datetime 2026-05-04T10:00:00+02:00 --window 15

Sortie JSON sur stdout :
    {
      "matched": true,
      "summary": "Synchro projet X",
      "start": "2026-05-04T10:00:00+02:00",
      "end":   "2026-05-04T10:30:00+02:00",
      "uid":   "abc@dinum.gouv.fr",
      "attendees": ["a@b.fr", "c@d.fr"],
      "rrule": "FREQ=WEEKLY;BYDAY=MO",
      "delta_seconds": 0,
      "candidates": [...]   # alternatives si match ambigu
    }

Variables d'environnement :
    CALDAV_ICS_URL   (requis) — URL du flux iCal (text/calendar)
    CALDAV_USERNAME  (optionnel) — pour auth basic si le flux la requiert
    CALDAV_PASSWORD  (optionnel)

Le script ne fait que des appels GET (lecture seule).
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta

import httpx
from dateutil import parser as dtparser
from dateutil.tz import tzlocal


def fail(msg: str, code: int = 1):
    print(json.dumps({"matched": False, "error": msg}, ensure_ascii=False), file=sys.stdout)
    sys.exit(code)


def fetch_ics(url: str) -> str:
    user = os.environ.get("CALDAV_USERNAME")
    pwd = os.environ.get("CALDAV_PASSWORD")
    auth = (user, pwd) if user and pwd else None
    try:
        with httpx.Client(follow_redirects=True, timeout=30.0) as client:
            r = client.get(url, auth=auth, headers={"Accept": "text/calendar"})
            r.raise_for_status()
            return r.text
    except Exception as e:
        fail(f"Failed to fetch ICS: {e}")


def serialize_dt(d) -> str:
    if hasattr(d, "isoformat"):
        return d.isoformat()
    return str(d)


def extract_attendees(component) -> list:
    out = []
    raw = component.get("attendee")
    if raw is None:
        return out
    items = raw if isinstance(raw, list) else [raw]
    for x in items:
        s = str(x)
        if s.lower().startswith("mailto:"):
            out.append(s[7:])
        else:
            out.append(s)
    return out


def main():
    ap = argparse.ArgumentParser(description="Lookup an event by datetime in an iCal feed (read-only).")
    ap.add_argument("--datetime", required=True, help="ISO datetime to match")
    ap.add_argument("--window", type=int, default=15, help="Match window in minutes (default 15)")
    args = ap.parse_args()

    url = os.environ.get("CALDAV_ICS_URL")
    if not url:
        fail("Missing CALDAV_ICS_URL env var")

    try:
        target = dtparser.isoparse(args.datetime)
    except Exception as e:
        fail(f"Invalid --datetime: {e}")

    if target.tzinfo is None:
        target = target.replace(tzinfo=tzlocal())

    window = timedelta(minutes=args.window)
    start_search = target - window
    end_search = target + window

    try:
        from icalendar import Calendar
        import recurring_ical_events
    except ImportError as e:
        fail(f"Missing dep: {e}")

    ics_text = fetch_ics(url)

    try:
        cal = Calendar.from_ical(ics_text)
    except Exception as e:
        fail(f"Invalid ICS content: {e}")

    try:
        events = recurring_ical_events.of(cal).between(start_search, end_search)
    except Exception as e:
        fail(f"Failed to expand recurring events: {e}")

    candidates = []
    for ev in events:
        try:
            ev_start = ev.get("dtstart").dt
            ev_end = ev.get("dtend").dt if ev.get("dtend") else ev_start
            summary = str(ev.get("summary", "")).strip()
            uid = str(ev.get("uid", ""))
            attendees = extract_attendees(ev)
            rrule = ""
            if ev.get("rrule"):
                rrule = ev["rrule"].to_ical().decode() if hasattr(ev["rrule"], "to_ical") else str(ev["rrule"])
        except Exception:
            continue

        if hasattr(ev_start, "tzinfo") and ev_start.tzinfo is None:
            ev_start = ev_start.replace(tzinfo=tzlocal())
        if hasattr(ev_end, "tzinfo") and ev_end.tzinfo is None:
            ev_end = ev_end.replace(tzinfo=tzlocal())

        try:
            delta = abs((ev_start - target).total_seconds())
        except TypeError:
            continue

        candidates.append({
            "summary": summary,
            "start": serialize_dt(ev_start),
            "end":   serialize_dt(ev_end),
            "uid": uid,
            "attendees": attendees,
            "rrule": rrule,
            "delta_seconds": delta,
        })

    candidates.sort(key=lambda c: c["delta_seconds"])

    if not candidates:
        print(json.dumps({"matched": False, "candidates": []}, ensure_ascii=False))
        return

    best = candidates[0]
    others = candidates[1:4]
    out = {
        "matched": True,
        **best,
        "candidates": others,
    }
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
