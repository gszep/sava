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

### 1. Google Cloud

Create a GCP project and enable the **Google Docs API** and **Google Drive API**.

```bash
gcloud projects create sava-the-owl
gcloud services enable docs.googleapis.com drive.googleapis.com --project=sava-the-owl
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

### 2. Google Workspace

Create a Workspace user for Sava (e.g. `sava@yourdomain.com`) in [admin.google.com](https://admin.google.com). This gives Sava a real identity — comments show up as "Sava" in Google Docs.

Then set up domain-wide delegation so the service account can act as this user:

1. Go to [admin.google.com/ac/owl/domainwidedelegation](https://admin.google.com/ac/owl/domainwidedelegation)
2. Add the service account's **Client ID** (find it with `gcloud iam service-accounts describe sava-agent@sava-the-owl.iam.gserviceaccount.com --format="value(uniqueId)"`)
3. Set OAuth scopes: `https://www.googleapis.com/auth/documents,https://www.googleapis.com/auth/drive`

Also enable domain-wide delegation on the service account itself in [Google Cloud Console](https://console.cloud.google.com) → IAM & Admin → Service Accounts → Advanced settings.

Share any Google Docs you want Sava to access with `sava@yourdomain.com` as Editor.

### 3. Install

```bash
git clone https://github.com/gszep/sava.git
cd sava && uv sync
uv run playwright install chromium
```

### 4. Browser login (one-time)

The Playwright-based tools (`anchor_comment`, `suggest_edit`) need a saved browser session. Run the login command, sign in as your Sava user in the browser window that opens, then close it:

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
You are Sava — a personal AI assistant with access to Google Workspace. Use your MCP tools (read_doc, list_docs, list_comments, add_comment, reply_to_comment, resolve_comment, anchor_comment, suggest_edit) to carry out the request below.

$ARGUMENTS
```

Restart Claude Code. Then use `/sava <request>` to invoke Sava from any project.

## Usage

```
/sava read the PROTOCOL doc
/sava list all comments on 1gmF8BJBpGsH...
/sava suggest replacing "old text" with "new text" in the PROTOCOL doc
/sava review the doc and post comments on anything unclear
```

The `/sava` prefix is intentional — it creates a clear boundary between normal Claude Code sessions (coding, file editing, git) and Sava's capability layer (Google Workspace). Without `/sava`, the MCP tools won't be invoked.

## Security

- **Service account key** (`~/.config/gcloud/sava-agent.json`) — the crown jewel. `chmod 600`, never commit it.
- **Playwright session** (`~/.config/gcloud/sava-playwright-state.json`) — treat like a cookie jar. Contains the browser session for `sava@yourdomain.com`.
- **Domain-wide delegation** — scoped to Docs + Drive only. The service account can only impersonate the Sava user, and Sava can only access docs explicitly shared with it.
- **No admin role** — the Sava Workspace user should have no admin privileges. Just a regular user.
