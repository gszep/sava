"""Shared Playwright browser helpers for Google Docs UI automation."""

import os
import sys

COOKIES_FILE = os.environ.get(
    "GOOGLE_DOCS_COOKIES_FILE",
    os.path.expanduser("~/.config/gcloud/sava-playwright-state.json"),
)


def open_doc_page(pw, doc_id):
    """Open a Google Doc in Playwright, dismiss popups, return (browser, context, page)."""
    if not os.path.exists(COOKIES_FILE):
        raise RuntimeError("No saved browser session. Run: sava-login")

    browser = pw.chromium.launch(headless=True)
    context = browser.new_context(storage_state=COOKIES_FILE)
    page = context.new_page()
    page.goto(
        f"https://docs.google.com/document/d/{doc_id}/edit",
        wait_until="domcontentloaded",
    )
    page.wait_for_selector(".kix-appview-editor", timeout=30000)

    # Dismiss popups (e.g. "Editors can see your view history")
    page.wait_for_timeout(3000)
    page.evaluate("""() => {
        const labels = ['I understand', 'Got it', 'OK', 'Dismiss', 'No thanks'];
        const all = document.querySelectorAll('button, [role="button"], [jsname]');
        for (const el of all) {
            const text = el.textContent.trim();
            if (labels.some(l => text === l)) { el.click(); return; }
        }
    }""")
    page.wait_for_timeout(1000)

    return browser, context, page


def switch_to_suggesting(page):
    """Switch the editor to Suggesting mode via the mode dropdown."""
    mode_btn = page.locator("#docs-toolbar-mode-switcher").first
    if not mode_btn.is_visible(timeout=3000):
        mode_btn = page.locator("[aria-label='Editing mode']").first
    mode_btn.click()
    page.wait_for_timeout(500)

    page.get_by_text("Suggesting", exact=True).click()
    page.wait_for_timeout(500)


def save_and_close(browser, context):
    """Save browser state and close."""
    context.storage_state(path=COOKIES_FILE)
    browser.close()
