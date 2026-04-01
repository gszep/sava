"""Playwright worker — runs in a subprocess to avoid asyncio conflicts with the MCP server.

Reads a JSON payload from stdin, performs the requested action, prints the result to stdout.
"""

import json
import sys

from playwright.sync_api import sync_playwright

DISMISS_LABELS = [
    "got it", "ok", "okay", "dismiss", "close", "no thanks",
    "i understand", "not now", "skip", "next time", "maybe later", "continue",
]


def dismiss_popups(page):
    page.evaluate("""(labels) => {
        for (const sel of ['[role="dialog"]', '[role="alertdialog"]', '[class*="Dialog"]', '[class*="WizDialog"]', '[data-disable-esc-to-close]']) {
            for (const dialog of document.querySelectorAll(sel)) {
                const buttons = dialog.querySelectorAll('button, [role="button"], [jsname]');
                for (const btn of buttons) {
                    if (labels.includes(btn.textContent.trim().toLowerCase())) { btn.click(); return; }
                }
                if (buttons.length === 1) { buttons[0].click(); return; }
            }
        }
    }""", DISMISS_LABELS)


def open_doc(pw, cookies_file, doc_id):
    browser = pw.chromium.launch(headless=True)
    context = browser.new_context(storage_state=cookies_file)
    page = context.new_page()
    page.goto(f"https://docs.google.com/document/d/{doc_id}/edit", wait_until="domcontentloaded")
    page.wait_for_selector(".kix-appview-editor", timeout=30000)
    for _ in range(3):
        page.wait_for_timeout(2000)
        dismiss_popups(page)
    return browser, context, page


def save_and_close(browser, context, cookies_file):
    context.storage_state(path=cookies_file)
    browser.close()


def find_text(page, quote):
    page.keyboard.press("Control+f")
    page.wait_for_timeout(1500)
    for selector in ["input[aria-label='Find in document']", "input[name='findInput']", "input[type='text']"]:
        loc = page.locator(selector).first
        if loc.is_visible(timeout=1000):
            loc.click()
            page.keyboard.type(quote, delay=20)
            page.wait_for_timeout(500)
            page.keyboard.press("Enter")
            page.wait_for_timeout(1000)
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
            return True
    return False


def click_dialog_button(page, text):
    page.evaluate("""(text) => {
        for (const sel of ['[role="dialog"]', '[role="alertdialog"]', '[class*="Dialog"]']) {
            for (const dialog of document.querySelectorAll(sel)) {
                for (const btn of dialog.querySelectorAll('button, [role="button"]')) {
                    if (btn.textContent.trim() === text) { btn.click(); return; }
                }
            }
        }
    }""", text)


def do_anchor_comment(pw, cookies_file, doc_id, quote, message):
    browser, context, page = open_doc(pw, cookies_file, doc_id)
    page.locator(".kix-appview-editor").click()
    page.wait_for_timeout(1000)

    if not find_text(page, quote):
        save_and_close(browser, context, cookies_file)
        return "Error: could not find the search input."

    page.keyboard.press("Control+Alt+m")
    page.wait_for_timeout(1500)

    for selector in ["[aria-label='Add a comment']", "textarea", "[contenteditable='true'][role='textbox']"]:
        loc = page.locator(selector).first
        if loc.is_visible(timeout=1000):
            loc.click()
            page.keyboard.type(message, delay=10)
            page.wait_for_timeout(300)
            page.keyboard.press("Control+Enter")
            page.wait_for_timeout(2000)
            save_and_close(browser, context, cookies_file)
            return f'Anchored comment posted on: "{quote}"'

    save_and_close(browser, context, cookies_file)
    return "Error: could not find the comment box."


def do_suggest_edit(pw, cookies_file, doc_id, quote, replacement):
    browser, context, page = open_doc(pw, cookies_file, doc_id)
    page.locator(".kix-appview-editor").click()
    page.wait_for_timeout(500)

    # Switch to suggesting mode
    mode_btn = page.locator("#docs-toolbar-mode-switcher").first
    if not mode_btn.is_visible(timeout=3000):
        mode_btn = page.locator("[aria-label='Editing mode']").first
    mode_btn.click()
    page.wait_for_timeout(500)
    page.get_by_text("Suggesting", exact=True).click()
    page.wait_for_timeout(500)

    # Find & Replace
    page.keyboard.press("Control+h")
    page.wait_for_timeout(2000)

    page.evaluate("""() => {
        const inputs = document.querySelectorAll('[role="dialog"] input');
        if (inputs[0]) inputs[0].focus();
    }""")
    page.wait_for_timeout(300)
    page.keyboard.type(quote, delay=10)
    page.wait_for_timeout(500)
    page.keyboard.press("Tab")
    page.wait_for_timeout(300)
    page.keyboard.type(replacement, delay=10)
    page.wait_for_timeout(500)

    click_dialog_button(page, "Next")
    page.wait_for_timeout(1000)
    click_dialog_button(page, "Replace")
    page.wait_for_timeout(2000)

    page.keyboard.press("Escape")
    page.wait_for_timeout(500)

    save_and_close(browser, context, cookies_file)
    return f'Suggested edit: "{quote}" -> "{replacement}"'


def do_list_comments(pw, cookies_file, doc_id):
    """List all comments and suggestions visible in the Google Docs UI."""
    browser, context, page = open_doc(pw, cookies_file, doc_id)
    page.locator(".kix-appview-editor").click()
    page.wait_for_timeout(1000)

    # Open the comments panel
    btn = page.locator("#docs-docos-commentsbutton")
    if btn.is_visible(timeout=3000):
        btn.click()
        page.wait_for_timeout(2000)

    # Read from the stream view only (not anchored view) to avoid duplicates
    comments = page.evaluate("""() => {
        const results = [];
        const seen = new Set();
        for (const el of document.querySelectorAll('.docos-streamrootreplyview')) {
            const author = el.querySelector('.docos-author');
            const body = el.querySelector('.docos-replyview-body');
            const timestamp = el.querySelector('.docos-replyview-timestamp');
            const isSuggestion = el.querySelector('.docos-replyview-suggest') !== null;
            const text = body ? body.textContent.trim() : '';
            const key = (author ? author.textContent.trim() : '') + text;
            if (seen.has(key)) continue;
            seen.add(key);
            results.push({
                author: author ? author.textContent.trim() : '?',
                body: text,
                time: timestamp ? timestamp.textContent.trim() : '',
                type: isSuggestion ? 'suggestion' : 'comment',
            });
        }
        return results;
    }""")

    save_and_close(browser, context, cookies_file)

    if not comments:
        return "No comments or suggestions found."

    lines = []
    for c in comments:
        tag = "[SUGGESTION]" if c["type"] == "suggestion" else "[COMMENT]"
        lines.append(f'{tag}  {c["author"]}  {c["time"]}')
        lines.append(f'  {c["body"]}')
        lines.append("")

    return "\n".join(lines)


def do_delete_all_comments(pw, cookies_file, doc_id):
    """Delete all comment threads authored by Sava the Owl."""
    browser, context, page = open_doc(pw, cookies_file, doc_id)
    page.locator(".kix-appview-editor").click()
    page.wait_for_timeout(1000)

    # Open the comments panel
    btn = page.locator("#docs-docos-commentsbutton")
    if btn.is_visible(timeout=3000):
        btn.click()
        page.wait_for_timeout(2000)

    deleted = 0
    for _ in range(50):
        # Find Sava's comment, select it, get "..." button position
        pos = page.evaluate("""() => {
            for (const el of document.querySelectorAll('.docos-streamrootreplyview, .docos-docoview-rootreply')) {
                if (!el.querySelector('[data-name="Sava the Owl"]')) continue;
                el.scrollIntoView({block: 'center'});
                el.click();
                const menu = el.querySelector('.docos-docomenu-dropdown');
                if (!menu) continue;
                const r = menu.getBoundingClientRect();
                if (r.width > 0) return {x: r.x + r.width / 2, y: r.y + r.height / 2};
            }
            return null;
        }""")
        if not pos:
            break

        page.wait_for_timeout(1000)
        page.mouse.click(pos["x"], pos["y"])
        page.wait_for_timeout(800)

        # Navigate dropdown with keyboard to avoid fragile hover
        page.keyboard.press("ArrowDown")
        page.wait_for_timeout(200)
        page.keyboard.press("ArrowDown")
        page.wait_for_timeout(200)
        page.keyboard.press("Enter")
        page.wait_for_timeout(1000)

        # Confirm deletion dialog
        try:
            page.get_by_role("button", name="Delete").click(timeout=3000)
        except Exception:
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
            break

        page.wait_for_timeout(2000)
        deleted += 1

    save_and_close(browser, context, cookies_file)
    return f"Deleted {deleted} Sava comment threads"


def main():
    payload = json.loads(sys.stdin.read())
    action = payload["action"]
    cookies_file = payload["cookies_file"]

    with sync_playwright() as pw:
        if action == "anchor_comment":
            result = do_anchor_comment(pw, cookies_file, payload["doc_id"], payload["quote"], payload["message"])
        elif action == "suggest_edit":
            result = do_suggest_edit(pw, cookies_file, payload["doc_id"], payload["quote"], payload["replacement"])
        elif action == "list_comments":
            result = do_list_comments(pw, cookies_file, payload["doc_id"])
        elif action == "delete_all_comments":
            result = do_delete_all_comments(pw, cookies_file, payload["doc_id"])
        else:
            result = f"Unknown action: {action}"

    print(result)


if __name__ == "__main__":
    main()
