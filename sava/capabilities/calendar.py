"""Google Calendar capabilities for the primary user's calendar."""

from datetime import datetime, timedelta, timezone

from googleapiclient.discovery import build

from ..auth import get_primary_credentials


def _service():
    return build("calendar", "v3", credentials=get_primary_credentials())


def list_calendars() -> str:
    service = _service()
    result = service.calendarList().list().execute()
    calendars = result.get("items", [])
    if not calendars:
        return "No calendars found."

    lines = []
    for cal in calendars:
        primary = " (primary)" if cal.get("primary") else ""
        lines.append(f"- **{cal['summary']}**{primary}  \n  ID: `{cal['id']}`")
    return "\n".join(lines)


def _format_event(ev: dict) -> str:
    start = ev["start"].get("dateTime", ev["start"].get("date", ""))
    end = ev["end"].get("dateTime", ev["end"].get("date", ""))
    summary = ev.get("summary", "(no title)")
    event_id = ev["id"]

    parts = [f"- **{summary}**", f"  {start} \u2192 {end}"]
    if ev.get("location"):
        parts.append(f"  Location: {ev['location']}")
    if ev.get("description"):
        desc = ev["description"][:200]
        parts.append(f"  Description: {desc}")
    attendees = ev.get("attendees", [])
    if attendees:
        names = [a.get("displayName", a["email"]) for a in attendees[:10]]
        parts.append(f"  Attendees: {', '.join(names)}")
    parts.append(f"  ID: `{event_id}`")
    return "\n".join(parts)


def list_events(
    calendar_id: str = "primary",
    time_min: str | None = None,
    time_max: str | None = None,
    max_results: int = 25,
) -> str:
    service = _service()

    now = datetime.now(timezone.utc)
    if not time_min:
        time_min = now.isoformat()
    if not time_max:
        time_max = (now + timedelta(days=7)).isoformat()

    result = (
        service.events()
        .list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = result.get("items", [])
    if not events:
        return "No events found in that time range."

    lines = []
    for ev in events:
        lines.append(_format_event(ev))

    return "\n".join(lines)


def _time_field(dt_str: str, tz: str | None = None) -> dict:
    """Build a Calendar API start/end object from a date or datetime string."""
    key = "date" if "T" not in dt_str else "dateTime"
    field: dict = {key: dt_str}
    if tz:
        field["timeZone"] = tz
    return field


def create_event(
    summary: str,
    start: str,
    end: str,
    calendar_id: str = "primary",
    description: str | None = None,
    location: str | None = None,
    time_zone: str | None = None,
) -> str:
    service = _service()

    body: dict = {
        "summary": summary,
        "start": _time_field(start, time_zone),
        "end": _time_field(end, time_zone),
    }
    if description:
        body["description"] = description
    if location:
        body["location"] = location

    ev = service.events().insert(calendarId=calendar_id, body=body).execute()
    return f"Created event.\n{_format_event(ev)}"


def update_event(
    event_id: str,
    calendar_id: str = "primary",
    summary: str | None = None,
    start: str | None = None,
    end: str | None = None,
    description: str | None = None,
    location: str | None = None,
    time_zone: str | None = None,
) -> str:
    service = _service()

    body: dict = {}
    if summary is not None:
        body["summary"] = summary
    if description is not None:
        body["description"] = description
    if location is not None:
        body["location"] = location
    if start is not None:
        body["start"] = _time_field(start, time_zone)
    if end is not None:
        body["end"] = _time_field(end, time_zone)

    updated = service.events().patch(calendarId=calendar_id, eventId=event_id, body=body).execute()
    return f"Updated event.\n{_format_event(updated)}"


def delete_event(event_id: str, calendar_id: str = "primary") -> str:
    service = _service()
    service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
    return f"Deleted event `{event_id}`."
