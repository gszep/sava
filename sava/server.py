"""Sava MCP server — personal AI assistant capabilities."""

from mcp.server.fastmcp import FastMCP

from .capabilities import gdocs

mcp = FastMCP("sava")


# ---------------------------------------------------------------------------
# Google Drive
# ---------------------------------------------------------------------------

@mcp.tool()
def list_files() -> str:
    """List all files accessible to Sava on Google Drive (docs, spreadsheets, PDFs, etc.)."""
    return gdocs.list_docs()


@mcp.tool()
def read_doc(doc_id: str) -> str:
    """Read any file on Google Drive. Supports Google Docs, Google Sheets,
    Word (.docx), Excel (.xlsx), and PDF. The doc_id is the long string
    in the URL: docs.google.com/document/d/<doc_id>/edit"""
    return gdocs.read_doc(doc_id)


# ---------------------------------------------------------------------------
# Google Sheets
# ---------------------------------------------------------------------------

@mcp.tool()
def write_sheet(spreadsheet_id: str, range: str, values: list[list[str]]) -> str:
    """Write values to a Google Sheet. The range uses A1 notation
    e.g. 'Sheet1!A1:C3'. Values is a 2D array of strings."""
    return gdocs.write_sheet(spreadsheet_id, range, values)


# ---------------------------------------------------------------------------
# Comments (works on any Google Drive file)
# ---------------------------------------------------------------------------

@mcp.tool()
def list_comments(doc_id: str) -> str:
    """List all comments and replies on a file."""
    return gdocs.list_comments(doc_id)


@mcp.tool()
def add_comment(doc_id: str, message: str, quote: str = "") -> str:
    """Post a comment on a file. If quote is provided, the comment will be
    anchored to that text via browser automation (required for .docx files).
    Without quote, posts an unanchored comment via the API."""
    if quote:
        return gdocs.anchor_comment(doc_id, quote, message)
    return gdocs.add_comment(doc_id, message)


@mcp.tool()
def reply_to_comment(doc_id: str, comment_id: str, message: str) -> str:
    """Reply to an existing comment."""
    return gdocs.reply_to_comment(doc_id, comment_id, message)


@mcp.tool()
def resolve_comment(doc_id: str, comment_id: str, message: str = "Resolved.") -> str:
    """Resolve a comment thread."""
    return gdocs.resolve_comment(doc_id, comment_id, message)


# ---------------------------------------------------------------------------
# Browser-based (Playwright) — anchored comments + suggesting mode
# ---------------------------------------------------------------------------

@mcp.tool()
def anchor_comment(doc_id: str, quote: str, message: str) -> str:
    """Post a comment anchored/highlighted to specific text.
    Uses browser automation. Requires a saved browser session."""
    return gdocs.anchor_comment(doc_id, quote, message)


@mcp.tool()
def suggest_edit(doc_id: str, quote: str, replacement: str) -> str:
    """Create a tracked suggestion (suggesting mode).
    Finds the quoted text and suggests replacing it with the replacement.
    Uses browser automation. Requires a saved browser session."""
    return gdocs.suggest_edit(doc_id, quote, replacement)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
