"""Playwright worker — runs in its own process to avoid asyncio conflicts.

Reads a JSON payload from stdin, performs the requested action, prints the result to stdout.
"""

import json
import sys

from playwright.sync_api import sync_playwright


def dismiss_popups(page):
    """Aggressively dismiss any modal/dialog/toast that blocks the editor.
    Rather than matching specific text, click any small button inside a
    dialog-like container — these are almost always dismissal buttons."""
    page.evaluate("""() => {
        // Strategy 1: Click buttons inside dialogs/overlays
        const dialogs = document.querySelectorAll(
            '[role="dialog"], [role="alertdialog"], .modal, [class*="Dialog"], [class*="dialog"]'
        );
        for (const dialog of dialogs) {
            const buttons = dialog.querySelectorAll('button, [role="button"]');
            for (const btn of buttons) {
                const text = btn.textContent.trim().toLowerCase();
                // Click anything that looks like an acknowledgement
                if (['got it', 'ok', 'okay', 'dismiss', 'close', 'no thanks',
                     'i understand', 'not now', 'skip', 'next time', 'maybe later',
                     'continue'].includes(text)) {
                    btn.click();
                    return;
                }
            }
            // If there's only one button in the dialog, just click it
            if (buttons.length === 1) {
                buttons[0].click();
                return;
            }
        }

        // Strategy 2: Catch Google's custom Material Design dialogs
        const gmDialogs = document.querySelectorAll(
            '[class*="WizDialog"], [class*="material"], [data-disable-esc-to-close]'
        );
        for (const dialog of gmDialogs) {
            const buttons = dialog.querySelectorAll('button, [role="button"], [jsname]');
            for (const btn of buttons) {
                const text = btn.textContent.trim().toLowerCase();
                if (text.length > 0 && text.length < 30) {
                    btn.click();
                    return;
                }
            }
        }
    }""")


def open_doc(pw, cookies_file, doc_id):
    browser = pw.chromium.launch(headless=True)
    context = browser.new_context(storage_state=cookies_file)
    page = context.new_page()
    page.goto(
        f"https://docs.google.com/document/d/{doc_id}/edit",
        wait_until="domcontentloaded",
    )
    page.wait_for_selector(".kix-appview-editor", timeout=30000)

    # Dismiss popups repeatedly — some appear with a delay
    for _ in range(3):
        page.wait_for_timeout(2000)
        dismiss_popups(page)

    return browser, context, page


def save_and_close(browser, context, cookies_file):
    context.storage_state(path=cookies_file)
    browser.close()


def do_anchor_comment(pw, cookies_file, doc_id, quote, message):
    browser, context, page = open_doc(pw, cookies_file, doc_id)

    page.locator(".kix-appview-editor").click()
    page.wait_for_timeout(1000)

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
        save_and_close(browser, context, cookies_file)
        return "Error: could not find the search input."

    find_input.click()
    page.keyboard.type(quote, delay=20)
    page.wait_for_timeout(500)
    page.keyboard.press("Enter")
    page.wait_for_timeout(1000)
    page.keyboard.press("Escape")
    page.wait_for_timeout(500)

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
        save_and_close(browser, context, cookies_file)
        return "Error: could not find the comment box."

    comment_box.click()
    page.keyboard.type(message, delay=10)
    page.wait_for_timeout(300)
    page.keyboard.press("Control+Enter")
    page.wait_for_timeout(2000)

    save_and_close(browser, context, cookies_file)
    return f'Anchored comment posted on: "{quote}"'


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

    # Open Find & Replace
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

    # Click Next then Replace
    page.evaluate("""() => {
        const els = document.querySelectorAll('[role="dialog"] [role="button"], [role="dialog"] button');
        for (const el of els) {
            if (el.textContent.trim() === 'Next') { el.click(); return; }
        }
    }""")
    page.wait_for_timeout(1000)

    page.evaluate("""() => {
        const els = document.querySelectorAll('[role="dialog"] [role="button"], [role="dialog"] button');
        for (const el of els) {
            if (el.textContent.trim() === 'Replace') { el.click(); return; }
        }
    }""")
    page.wait_for_timeout(2000)

    page.keyboard.press("Escape")
    page.wait_for_timeout(500)

    save_and_close(browser, context, cookies_file)
    return f'Suggested edit: "{quote}" -> "{replacement}"'


def main():
    payload = json.loads(sys.stdin.read())
    action = payload["action"]
    cookies_file = payload["cookies_file"]

    with sync_playwright() as pw:
        if action == "anchor_comment":
            result = do_anchor_comment(
                pw, cookies_file, payload["doc_id"], payload["quote"], payload["message"]
            )
        elif action == "suggest_edit":
            result = do_suggest_edit(
                pw, cookies_file, payload["doc_id"], payload["quote"], payload["replacement"]
            )
        else:
            result = f"Unknown action: {action}"

    print(result)


if __name__ == "__main__":
    main()
