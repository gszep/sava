# Sava 🦉

An [MCP server](https://modelcontextprotocol.io/) that gives agentic coding tools like [Claude Code](https://claude.ai/claude-code) hands-on access to your Google Workspace — and eventually, your calendar, email, GCP, GitHub, and whatever else you trust it with.

Named after a Eurasian eagle-owl. Quietly watches over your documents, drops comments where they matter, and even knows how to use Google Docs' "Suggesting" mode — something Google's own API [still can't do](https://issuetracker.google.com/issues/36763384) after a decade of polite requests.

## What it does

**Google Docs** — read, comment, and suggest edits as a named Workspace user.

- `read_doc` / `list_docs` / `list_comments` — fast, API-based
- `add_comment` / `reply_to_comment` / `resolve_comment` — fast, API-based
- `anchor_comment` — highlighted comment on specific text (Playwright)
- `suggest_edit` — real tracked suggestion in Suggesting mode (Playwright)

The [Playwright](https://playwright.dev/)-based tools use headless browser automation to work around API limitations. Slower, but they produce real UI-native results.

## Where it's going

```
capabilities/
  gdocs.py       # ✅ today
  calendar.py    # 🔜
  gmail.py       # 🔜
  gcp.py         # 🔜
  github.py      # 🔜
```

One assistant, one identity (`sava@yourdomain.com`), incrementally trusted with more capabilities.

## Setup

1. Create a GCP project, enable Docs + Drive APIs, create a service account with [domain-wide delegation](https://support.google.com/a/answer/162106)
2. Create a Workspace user for Sava and share your docs with it
3. `git clone https://github.com/gszep/sava.git && cd sava && uv sync`
4. `uv run playwright install chromium` (for browser-based tools)
5. Add to `~/.claude/.mcp.json`:

```json
{
  "mcpServers": {
    "sava": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/sava", "sava"],
      "env": {
        "GOOGLE_SERVICE_ACCOUNT_FILE": "/path/to/key.json",
        "GOOGLE_IMPERSONATE_USER": "sava@yourdomain.com"
      }
    }
  }
}
```

Restart Claude Code. Sava is now available in every project.
