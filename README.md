# Sava 🦉

An [MCP server](https://modelcontextprotocol.io/) that gives agentic coding tools like [Claude Code](https://claude.ai/claude-code) hands-on access to your Google Workspace — and eventually, your calendar, email, GCP, GitHub, and whatever else you trust it with.

Named after a Eurasian eagle-owl. Quietly watches over your documents, drops suggestions where they matter, and even knows how to use Google Docs' "Suggesting" mode — something Google's own API [still can't do](https://issuetracker.google.com/issues/36763384) after a decade of polite requests.

## What it does

### Reading files

`read_doc` reads any file on Google Drive:

| Format | Method |
|---|---|
| Google Docs | Docs API (with inline suggestions) |
| Google Sheets | Sheets API (formatted as markdown tables) |
| Word (.docx) | Download + lxml XML extraction |
| Excel (.xlsx) | Download + openpyxl |
| PDF | Download + pymupdf |

`list_files` lists everything Sava has access to — docs, sheets, PDFs, folders.

### Editing documents

`suggest_edit` creates real tracked suggestions in Google Docs' Suggesting mode via headless Playwright. This is the preferred way to propose changes — it works on both native Google Docs and `.docx` files in compatibility mode.

`anchor_comment` posts a comment highlighted on specific text, also via Playwright. Use this only when you need to explain something or provide a reference that doesn't fit as a text replacement.

`write_sheet` writes to Google Sheets via the Sheets API.

### Comments

`list_comments` / `reply_to_comment` / `resolve_comment` manage comment threads via the Drive API.

> **Note on `.docx` files:** The Drive API can create comments on `.docx` files hosted in Google Drive, but they are invisible in the Google Docs compatibility mode UI. Sava automatically routes quoted comments through Playwright (`anchor_comment`) to ensure they're always visible.

## Known limitations

- **Google Docs API cannot create suggestions.** This is a [known limitation since 2016](https://issuetracker.google.com/issues/36763384). Sava works around this with Playwright browser automation.
- **Google Docs API cannot anchor comments on Google Docs.** The internal `kix.*` paragraph IDs [aren't exposed](https://issuetracker.google.com/issues/36763384) by any public API. Sava uses Playwright to create anchored comments through the UI.
- **Drive API comments are invisible on `.docx` files.** The API accepts them and returns success, but they don't render in Google Docs compatibility mode. Sava detects this and uses Playwright instead.
- **Google's tutorial popups** ("Welcome to Office editing", "Editors can see your view history", etc.) can block Playwright actions. Sava aggressively dismisses these on page load, but new popup types may require updates.
- **Playwright-based tools are slower** (~15-30 seconds) than API-based tools since they launch a headless browser.

## Where it's going

```
capabilities/
  gdocs.py       # ✅ docs, sheets, PDFs, comments, suggestions
  calendar.py    # 🔜
  gmail.py       # 🔜
  gcp.py         # 🔜
  github.py      # 🔜
```

One assistant, one identity (`sava@yourdomain.com`), incrementally trusted with more capabilities.

## Setup

### 1. Google Cloud

Create a GCP project and enable the required APIs:

```bash
gcloud projects create sava-the-owl
gcloud services enable docs.googleapis.com drive.googleapis.com sheets.googleapis.com --project=sava-the-owl
```

Create a service account:

```bash
gcloud iam service-accounts create sava-agent \
  --display-name="Sava" \
  --project=sava-the-owl

gcloud iam service-accounts keys create ~/.config/gcloud/sava-agent.json \
  --iam-account=sava-agent@sava-the-owl.iam.gserviceaccount.com \
  --project=sava-the-owl

chmod 600 ~/.config/gcloud/sava-agent.json
```

Enable domain-wide delegation on the service account in [Google Cloud Console](https://console.cloud.google.com) → IAM & Admin → Service Accounts → Advanced settings.

### 2. Google Workspace

Create a Workspace user for Sava (e.g. `sava@yourdomain.com`) in [admin.google.com](https://admin.google.com). This gives Sava a real identity — suggestions and comments show up as "Sava" in Google Docs.

Set up domain-wide delegation so the service account can act as this user:

1. Go to [admin.google.com/ac/owl/domainwidedelegation](https://admin.google.com/ac/owl/domainwidedelegation)
2. Add the service account's **Client ID** (find it with `gcloud iam service-accounts describe sava-agent@sava-the-owl.iam.gserviceaccount.com --format="value(uniqueId)"`)
3. Set OAuth scopes:
   ```
   https://www.googleapis.com/auth/documents,https://www.googleapis.com/auth/drive,https://www.googleapis.com/auth/spreadsheets
   ```

Share any documents you want Sava to access with `sava@yourdomain.com` as Editor (not the service account email).

### 3. Install

```bash
git clone https://github.com/gszep/sava.git
cd sava && uv sync
uv run playwright install chromium
```

### 4. Browser login (one-time)

The Playwright-based tools need a saved browser session. Run the login script, sign in as your Sava user in the browser window that opens, then close it:

```bash
uv run python -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto('https://accounts.google.com/')
    page.wait_for_event('close', timeout=300000)
    context.storage_state(path='$HOME/.config/gcloud/sava-playwright-state.json')
    browser.close()
"
```

### 5. Register with Claude Code

```bash
claude mcp add -s user \
  -e GOOGLE_SERVICE_ACCOUNT_FILE=$HOME/.config/gcloud/sava-agent.json \
  -e GOOGLE_IMPERSONATE_USER=sava@yourdomain.com \
  -- sava uv run --directory /path/to/sava sava
```

### 6. Create the slash command

Create `~/.claude/commands/sava.md`:

```markdown
You are Sava — a personal AI assistant with access to Google Workspace.

When making changes to documents, always prefer `suggest_edit` (suggesting mode) over comments. Only use `anchor_comment` when you need to explain something or provide a reference that doesn't fit as a text replacement. Never post unanchored comments.

Available tools: read_doc, list_files, list_comments, suggest_edit, anchor_comment, reply_to_comment, resolve_comment, write_sheet.

$ARGUMENTS
```

Restart Claude Code. Then use `/sava <request>` to invoke Sava from any project.

## Usage

```
/sava read the research plan summary
/sava review the English consent form and suggest corrections
/sava list comments on the ethics application
/sava update cell A1 in the feedback spreadsheet
```

The `/sava` prefix creates a clear boundary between normal Claude Code sessions (coding, file editing, git) and Sava's capability layer (Google Workspace). Without `/sava`, the MCP tools won't be invoked.

## Security

- **Service account key** (`~/.config/gcloud/sava-agent.json`) — the crown jewel. `chmod 600`, never commit it.
- **Playwright session** (`~/.config/gcloud/sava-playwright-state.json`) — treat like a cookie jar. Contains the browser session for `sava@yourdomain.com`.
- **Domain-wide delegation** — scoped to Docs, Drive, and Sheets only. The service account can only impersonate the Sava user, and Sava can only access files explicitly shared with it.
- **No admin role** — the Sava Workspace user should have no admin privileges. Just a regular user.
