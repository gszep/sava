"""Sava MCP server — personal AI assistant capabilities."""

from mcp.server.fastmcp import FastMCP

from .capabilities import gdocs

mcp = FastMCP("sava")


# ---------------------------------------------------------------------------
# Reading (API-based — fast and reliable)
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
def resolve_all_comments(doc_id: str) -> str:
    """Resolve all open comments in a document."""
    return gdocs.resolve_all_comments(doc_id)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
