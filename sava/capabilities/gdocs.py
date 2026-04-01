"""Google Docs capability — read documents, manage comments, suggest edits."""

from googleapiclient.discovery import build
from playwright.sync_api import sync_playwright

from ..auth import get_credentials
from ..browser import open_doc_page, switch_to_suggesting, save_and_close


def _docs_service():
    return build("docs", "v1", credentials=get_credentials())


def _drive_service():
    return build("drive", "v3", credentials=get_credentials())


def read_doc(doc_id: str) -> str:
    """Read the full text content of a Google Doc."""
    docs = _docs_service()
    doc = docs.documents().get(
        documentId=doc_id,
        suggestionsViewMode="SUGGESTIONS_INLINE",
    ).execute()

    title = doc.get("title", "(untitled)")
    parts = []
    for element in doc.get("body", {}).get("content", []):
        paragraph = element.get("paragraph")
        if not paragraph:
            continue
        for pe in paragraph.get("elements", []):
            text_run = pe.get("textRun")
            if text_run:
                parts.append(text_run["content"])

    return f"# {title}\n\n{''.join(parts)}"


def list_comments(doc_id: str) -> str:
    """List all comments and replies on a Google Doc."""
    drive = _drive_service()
    lines = []
    page_token = None

    while True:
        resp = drive.comments().list(
            fileId=doc_id,
            fields="comments(id,content,quotedFileContent,resolved,author,createdTime,"
                   "replies(id,content,author,createdTime,action)),nextPageToken",
            includeDeleted=False,
            pageSize=100,
            pageToken=page_token,
        ).execute()

        for c in resp.get("comments", []):
            status = "[RESOLVED]" if c.get("resolved") else "[OPEN]"
            author = c.get("author", {}).get("displayName", "?")
            quoted = c.get("quotedFileContent", {}).get("value", "")
            lines.append(f"\nComment {c['id']}  {status}  by {author}  {c.get('createdTime', '')}")
            if quoted:
                lines.append(f'  Quoted: "{quoted}"')
            lines.append(f"  {c['content']}")

            for r in c.get("replies", []):
                r_author = r.get("author", {}).get("displayName", "?")
                action = f" [{r['action']}]" if r.get("action") else ""
                lines.append(f"    -> {r_author}{action}: {r['content']}")

        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    return "\n".join(lines) if lines else "No comments found."


def add_comment(doc_id: str, message: str, quote: str = "") -> str:
    """Post a comment on a Google Doc. Optionally reference a text passage."""
    drive = _drive_service()
    content = f'Re: "{quote}"\n\n{message}' if quote else message

    comment = drive.comments().create(
        fileId=doc_id,
        fields="id",
        body={"content": content},
    ).execute()

    return f"Created comment {comment['id']}"


def reply_to_comment(doc_id: str, comment_id: str, message: str) -> str:
    """Reply to an existing comment."""
    drive = _drive_service()
    reply = drive.replies().create(
        fileId=doc_id,
        commentId=comment_id,
        fields="id",
        body={"content": message},
    ).execute()

    return f"Created reply {reply['id']} on comment {comment_id}"


def resolve_comment(doc_id: str, comment_id: str, message: str = "Resolved.") -> str:
    """Resolve a comment thread."""
    drive = _drive_service()
    drive.replies().create(
        fileId=doc_id,
        commentId=comment_id,
        fields="id",
        body={"content": message, "action": "resolve"},
    ).execute()

    return f"Resolved comment {comment_id}"


def anchor_comment(doc_id: str, quote: str, message: str) -> str:
    """Post a comment anchored to specific text using browser automation."""
    with sync_playwright() as pw:
        browser, context, page = open_doc_page(pw, doc_id)

        page.locator(".kix-appview-editor").click()
        page.wait_for_timeout(1000)

        # Find the text via Ctrl+F
        page.keyboard.press("Control+f")
        page.wait_for_timeout(1500)

        find_input = None
        for selector in [
            "input[aria-label='Find in document']",
            "input[name='findInput']",
            "input[type='text']",
        ]:
            loc = page.locator(selector).first
            if loc.is_visible(timeout=1000):
                find_input = loc
                break

        if not find_input:
            save_and_close(browser, context)
            return "Error: could not find the search input."

        find_input.click()
        page.keyboard.type(quote, delay=20)
        page.wait_for_timeout(500)
        page.keyboard.press("Enter")
        page.wait_for_timeout(1000)
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)

        # Open comment dialog on selected text
        page.keyboard.press("Control+Alt+m")
        page.wait_for_timeout(1500)

        comment_box = None
        for selector in [
            "[aria-label='Add a comment']",
            "[aria-label='Enter new comment']",
            "textarea",
            "[contenteditable='true'][role='textbox']",
        ]:
            loc = page.locator(selector).first
            if loc.is_visible(timeout=1000):
                comment_box = loc
                break

        if not comment_box:
            save_and_close(browser, context)
            return "Error: could not find the comment box."

        comment_box.click()
        page.keyboard.type(message, delay=10)
        page.wait_for_timeout(300)
        page.keyboard.press("Control+Enter")
        page.wait_for_timeout(2000)

        save_and_close(browser, context)
        return f'Anchored comment posted on: "{quote}"'


def suggest_edit(doc_id: str, quote: str, replacement: str) -> str:
    """Create a tracked suggestion using Find & Replace in Suggesting mode."""
    with sync_playwright() as pw:
        browser, context, page = open_doc_page(pw, doc_id)

        page.locator(".kix-appview-editor").click()
        page.wait_for_timeout(500)

        switch_to_suggesting(page)

        # Open Find & Replace
        page.keyboard.press("Control+h")
        page.wait_for_timeout(2000)

        # Focus the find input and type
        page.evaluate("""() => {
            const inputs = document.querySelectorAll('[role="dialog"] input');
            if (inputs[0]) inputs[0].focus();
        }""")
        page.wait_for_timeout(300)
        page.keyboard.type(quote, delay=10)
        page.wait_for_timeout(500)

        # Tab to replace field and type
        page.keyboard.press("Tab")
        page.wait_for_timeout(300)
        page.keyboard.type(replacement, delay=10)
        page.wait_for_timeout(500)

        # Click Next to find the match
        page.evaluate("""() => {
            const els = document.querySelectorAll('[role="dialog"] [role="button"], [role="dialog"] button');
            for (const el of els) {
                if (el.textContent.trim() === 'Next') { el.click(); return; }
            }
        }""")
        page.wait_for_timeout(1000)

        # Click Replace to apply as suggestion
        page.evaluate("""() => {
            const els = document.querySelectorAll('[role="dialog"] [role="button"], [role="dialog"] button');
            for (const el of els) {
                if (el.textContent.trim() === 'Replace') { el.click(); return; }
            }
        }""")
        page.wait_for_timeout(2000)

        page.keyboard.press("Escape")
        page.wait_for_timeout(500)

        save_and_close(browser, context)
        return f'Suggested edit: "{quote}" -> "{replacement}"'


def list_docs() -> str:
    """List all Google Docs accessible to Sava."""
    drive = _drive_service()
    results = drive.files().list(
        pageSize=50,
        fields="files(id,name,owners,webViewLink)",
        q="mimeType='application/vnd.google-apps.document'",
    ).execute()

    lines = []
    for f in results.get("files", []):
        owners = ", ".join(o.get("emailAddress", "?") for o in f.get("owners", []))
        lines.append(f"{f['name']}")
        lines.append(f"  ID: {f['id']}")
        lines.append(f"  Owner: {owners}")
        lines.append(f"  Link: {f.get('webViewLink', 'N/A')}")
        lines.append("")

    return "\n".join(lines) if lines else "No documents found."
