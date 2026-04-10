"""Gmail capabilities (read-only access to primary user's inbox)."""

import base64

from googleapiclient.discovery import build

from ..auth import get_primary_credentials


def _service():
    return build("gmail", "v1", credentials=get_primary_credentials())


def list_emails(query: str = "", max_results: int = 20) -> str:
    service = _service()
    result = (
        service.users()
        .messages()
        .list(userId="me", q=query, maxResults=max_results)
        .execute()
    )
    messages = result.get("messages", [])
    if not messages:
        return "No emails found."

    lines = []
    for msg_stub in messages:
        msg = (
            service.users()
            .messages()
            .get(userId="me", id=msg_stub["id"], format="metadata", metadataHeaders=["From", "Subject", "Date"])
            .execute()
        )
        headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
        subject = headers.get("Subject", "(no subject)")
        sender = headers.get("From", "unknown")
        date = headers.get("Date", "")
        snippet = msg.get("snippet", "")
        labels = msg.get("labelIds", [])
        unread = "UNREAD" in labels

        marker = "\u2b24 " if unread else "  "
        lines.append(f"{marker}**{subject}**\n  From: {sender}  |  {date}\n  {snippet}\n  ID: `{msg_stub['id']}`")

    return "\n".join(lines)


def read_email(message_id: str) -> str:
    service = _service()
    msg = service.users().messages().get(userId="me", id=message_id, format="full").execute()

    headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
    subject = headers.get("Subject", "(no subject)")
    sender = headers.get("From", "unknown")
    to = headers.get("To", "")
    cc = headers.get("Cc", "")
    date = headers.get("Date", "")

    body = _extract_body(msg.get("payload", {}))

    parts = [
        f"# {subject}",
        f"**From:** {sender}",
        f"**To:** {to}",
    ]
    if cc:
        parts.append(f"**Cc:** {cc}")
    parts.append(f"**Date:** {date}")
    parts.append("")
    parts.append(body)

    attachments = _list_attachments(msg.get("payload", {}))
    if attachments:
        parts.append("\n**Attachments:**")
        for name in attachments:
            parts.append(f"- {name}")

    return "\n".join(parts)


def _extract_body(payload: dict) -> str:
    """Recursively extract plain text body from a Gmail message payload."""
    if payload.get("mimeType") == "text/plain" and payload.get("body", {}).get("data"):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")

    for part in payload.get("parts", []):
        if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
            return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")

    # Fallback: try nested parts
    for part in payload.get("parts", []):
        result = _extract_body(part)
        if result:
            return result

    return "(no text body)"


def _list_attachments(payload: dict) -> list[str]:
    """Return list of attachment filenames."""
    names = []
    for part in payload.get("parts", []):
        if part.get("filename"):
            names.append(part["filename"])
        names.extend(_list_attachments(part))
    return names
