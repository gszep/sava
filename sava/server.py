"""Sava MCP server — personal AI assistant capabilities."""

from mcp.server.fastmcp import FastMCP

from .capabilities import calendar, gdocs, gmail, tasks

mcp = FastMCP("sava")


# ---------------------------------------------------------------------------
# Google Drive (API-based — fast and reliable)
# ---------------------------------------------------------------------------

@mcp.tool()
def list_files() -> str:
    """List all files accessible to Sava on Google Drive."""
    return gdocs.list_docs()


@mcp.tool()
def read_doc(doc_id: str) -> str:
    """Read any file on Google Drive. Supports Google Docs, Google Sheets,
    Word (.docx), Excel (.xlsx), and PDF. The doc_id is the long string
    in the URL: docs.google.com/document/d/<doc_id>/edit"""
    return gdocs.read_doc(doc_id)


@mcp.tool()
def list_comments(doc_id: str) -> str:
    """List all comments and replies on a file."""
    return gdocs.list_comments(doc_id)


@mcp.tool()
def write_sheet(spreadsheet_id: str, range: str, values: list[list[str]]) -> str:
    """Write values to a Google Sheet. The range uses A1 notation
    e.g. 'Sheet1!A1:C3'. Values is a 2D array of strings."""
    return gdocs.write_sheet(spreadsheet_id, range, values)


# ---------------------------------------------------------------------------
# Document editing (Playwright-based — works on both native Docs and .docx)
# ---------------------------------------------------------------------------

@mcp.tool()
def suggest_edit(doc_id: str, quote: str, replacement: str) -> str:
    """Create a tracked suggestion (Suggesting mode) in a document.
    Finds the quoted text and suggests replacing it with the replacement.
    Creates inline diffs: green for additions, red strikethrough for deletions."""
    return gdocs.suggest_edit(doc_id, quote, replacement)


@mcp.tool()
def anchor_comment(doc_id: str, quote: str, message: str) -> str:
    """Post a comment anchored/highlighted to specific text in a document.
    Use only for notes, questions, or explanations — prefer suggest_edit for changes."""
    return gdocs.anchor_comment(doc_id, quote, message)


@mcp.tool()
def delete_all_comments(doc_id: str) -> str:
    """Delete all comment threads in a document. This permanently removes
    them — use with care."""
    return gdocs.delete_all_comments(doc_id)


# ---------------------------------------------------------------------------
# Google Calendar
# ---------------------------------------------------------------------------

@mcp.tool()
def list_calendars() -> str:
    """List all calendars visible to the primary user."""
    return calendar.list_calendars()


@mcp.tool()
def list_events(
    calendar_id: str = "primary",
    time_min: str | None = None,
    time_max: str | None = None,
    max_results: int = 25,
) -> str:
    """List upcoming calendar events. Defaults to the next 7 days.
    time_min/time_max are ISO 8601 strings (e.g. '2026-04-04T00:00:00Z')."""
    return calendar.list_events(calendar_id, time_min, time_max, max_results)


@mcp.tool()
def create_event(
    summary: str,
    start: str,
    end: str,
    calendar_id: str = "primary",
    description: str | None = None,
    location: str | None = None,
    time_zone: str | None = None,
) -> str:
    """Create a calendar event. For timed events use ISO 8601 datetime
    (e.g. '2026-04-13T18:15:00+09:00'). For all-day events use date
    (e.g. '2026-04-13'). time_zone is an IANA name like 'Asia/Tokyo'."""
    return calendar.create_event(summary, start, end, calendar_id, description, location, time_zone)


@mcp.tool()
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
    """Update an existing calendar event. Only provided fields are changed.
    Get event_id from list_events."""
    return calendar.update_event(event_id, calendar_id, summary, start, end, description, location, time_zone)


@mcp.tool()
def delete_event(event_id: str, calendar_id: str = "primary") -> str:
    """Delete a calendar event by its ID."""
    return calendar.delete_event(event_id, calendar_id)


# ---------------------------------------------------------------------------
# Gmail (read-only on primary user's account)
# ---------------------------------------------------------------------------

@mcp.tool()
def list_emails(query: str = "", max_results: int = 20) -> str:
    """Search and list emails. Use Gmail search syntax for the query,
    e.g. 'from:alice subject:meeting is:unread', 'after:2026/04/01'."""
    return gmail.list_emails(query, max_results)


@mcp.tool()
def read_email(message_id: str) -> str:
    """Read the full content of an email by its message ID."""
    return gmail.read_email(message_id)


# ---------------------------------------------------------------------------
# Google Tasks (read-only on primary user's account)
# ---------------------------------------------------------------------------

@mcp.tool()
def list_task_lists() -> str:
    """List all task lists."""
    return tasks.list_task_lists()


@mcp.tool()
def list_tasks(tasklist_id: str = "@default", show_completed: bool = False) -> str:
    """List tasks in a task list. Defaults to the primary list."""
    return tasks.list_tasks(tasklist_id, show_completed)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
