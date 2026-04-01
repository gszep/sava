"""Sava MCP server — personal AI assistant capabilities."""

from mcp.server.fastmcp import FastMCP

from .capabilities import gdocs

mcp = FastMCP("sava")


# ---------------------------------------------------------------------------
# Google Docs tools
# ---------------------------------------------------------------------------

@mcp.tool()
def read_doc(doc_id: str) -> str:
    """Read the full text content of a Google Doc. The doc_id is the long string
    in the URL: docs.google.com/document/d/<doc_id>/edit"""
    return gdocs.read_doc(doc_id)


@mcp.tool()
def list_docs() -> str:
    """List all Google Docs accessible to Sava."""
    return gdocs.list_docs()


@mcp.tool()
def list_comments(doc_id: str) -> str:
    """List all comments and replies on a Google Doc."""
    return gdocs.list_comments(doc_id)


@mcp.tool()
def add_comment(doc_id: str, message: str, quote: str = "") -> str:
    """Post a comment on a Google Doc. If quote is provided, the comment
    will reference that text passage."""
    return gdocs.add_comment(doc_id, message, quote)


@mcp.tool()
def reply_to_comment(doc_id: str, comment_id: str, message: str) -> str:
    """Reply to an existing comment on a Google Doc."""
    return gdocs.reply_to_comment(doc_id, comment_id, message)


@mcp.tool()
def resolve_comment(doc_id: str, comment_id: str, message: str = "Resolved.") -> str:
    """Resolve a comment thread on a Google Doc."""
    return gdocs.resolve_comment(doc_id, comment_id, message)


@mcp.tool()
def anchor_comment(doc_id: str, quote: str, message: str) -> str:
    """Post a comment anchored/highlighted to specific text in a Google Doc.
    Uses browser automation to create a properly anchored comment.
    Requires a saved browser session (run sava-login first)."""
    return gdocs.anchor_comment(doc_id, quote, message)


@mcp.tool()
def suggest_edit(doc_id: str, quote: str, replacement: str) -> str:
    """Create a tracked suggestion (suggesting mode) in a Google Doc.
    Finds the quoted text and suggests replacing it with the replacement.
    Uses browser automation. Requires a saved browser session (run sava-login first)."""
    return gdocs.suggest_edit(doc_id, quote, replacement)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
