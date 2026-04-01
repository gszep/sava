"""Shared Playwright browser helpers for Google Docs UI automation.

Playwright operations run in a subprocess to avoid conflicts with
the MCP server's asyncio event loop.
"""

import json
import os
import subprocess
import sys

COOKIES_FILE = os.environ.get(
    "GOOGLE_DOCS_COOKIES_FILE",
    os.path.expanduser("~/.config/gcloud/sava-playwright-state.json"),
)

# Path to the worker script that runs Playwright in its own process
_WORKER = os.path.join(os.path.dirname(__file__), "_pw_worker.py")


def run_playwright_action(action: str, **kwargs) -> str:
    """Run a Playwright action in a subprocess, returning the result string."""
    if not os.path.exists(COOKIES_FILE):
        raise RuntimeError("No saved browser session. Run sava-login first.")

    payload = json.dumps({"action": action, "cookies_file": COOKIES_FILE, **kwargs})
    result = subprocess.run(
        [sys.executable, _WORKER],
        input=payload,
        capture_output=True,
        text=True,
        timeout=300,
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Playwright worker failed")

    return result.stdout.strip()
