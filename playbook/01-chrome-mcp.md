# Playbook 1 — Chrome Browser Setup

**What you get:** Claude Code can open a browser, navigate to websites you're already logged into (YouTube, your library, school portal), read the content, and save it to files — automatically.

**Time:** 30–45 minutes
**Prerequisites:** Playbook 0 done. Playbook 4 (password safety) done.
**Platform:** macOS. Windows steps noted at the bottom.

---

## At a glance — what you do vs. what the agent does

| Section | You need to... | Agent does |
|---------|---------------|-----------|
| How it works | Read once | — |
| Install Chrome MCP server | Run one command (one-time) | — |
| Register MCP with Claude Code | Run one command (one-time) | — |
| Set up browser profile & alias | Edit one config file (one-time) | — |
| Log in to YouTube / library | Log in yourself in the browser (once per service) | — |
| Safety tips | Read once | — |
| Test the connection | Type "List open pages in Chrome" | ✅ Connects and lists tabs |
| YouTube audit | Open browser, type command (or let cron run it) | ✅ Scrolls history, classifies channels, saves report |
| Library sync | Ensure browser is open (or let cron run it) | ✅ Logs in with saved credentials, fetches all borrows |
| Re-login after session expiry | Log in again in the browser window (rare) | — |

**TL;DR for setup:** Steps 1–4 are one-time (30 min). Log in once per service in Step 4. After that the agent handles all browsing.

---

## How this works (plain English)

Chrome has a built-in "developer mode" that lets other programs on your computer read what's on the screen and click buttons — exactly like you would. The program that bridges Claude Code and Chrome is called an **MCP server** (a small background helper program).

Here's the flow:
1. You open a special Chrome window (separate from your regular browser)
2. You log in to YouTube / library / school portal yourself in that window
3. Claude Code connects to that window and reads the pages
4. It saves the data to files in your `user_docs/` folder

**Your passwords are never seen by Claude.** You type them yourself. Claude reads the result after you're logged in.

---

## Step 1: Install the Chrome MCP server

The MCP server is installed via npm, the same way Claude Code was installed.

> **Note:** Check the project's `README.md` or `.mcp.json` file for the exact current install command — the package name may be updated. The command below reflects the current setup in this repo.

```bash
# Check what MCP is already configured in this project
cat .mcp.json
```

If `.mcp.json` already exists and lists `chrome-devtools-cron`, the server is configured. You may still need to install it:

```bash
npm install -g @anthropic/mcp-server-chrome-devtools
```

If that fails, check the project's README or open an issue — the exact npm package name is subject to change as the tool evolves.

---

## Step 2: Verify Claude Code sees the MCP server

Start Claude Code from the project folder:
```bash
claude
```

Then type:
```
/mcp
```

You should see `chrome-devtools-cron` in the list of available servers. If it's missing, run:
```bash
claude mcp add chrome-devtools-cron -- npx @anthropic/mcp-server-chrome-devtools
```

Then restart Claude Code.

---

## Step 3: Set up a persistent browser profile

You'll open a special Chrome window for automation. Set it up once, log in to your services once, and it remembers your sessions indefinitely.

**First, create a stable profile folder** (this persists across reboots):

```bash
mkdir -p ~/.chrome-parenting-profile
```

**Add a shortcut command** so you can open it easily. Add this line to your shell config file:

```bash
# Find out which shell you're using:
echo $SHELL
# If it says /bin/zsh → edit ~/.zshrc
# If it says /bin/bash → edit ~/.bash_profile
```

Open that file in TextEdit:
```bash
open -e ~/.zshrc      # for zsh (most Macs since 2019)
# OR
open -e ~/.bash_profile   # for bash
```

Add this line at the bottom (copy exactly, including the backslashes):
```bash
alias chrome-parenting='/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --no-first-run --no-default-browser-check --user-data-dir="$HOME/.chrome-parenting-profile" --start-maximized'
```

Save the file, then reload it:
```bash
source ~/.zshrc    # or source ~/.bash_profile
```

Now you can open the automation browser any time with:
```bash
chrome-parenting "https://www.youtube.com/feed/history"
```

---

## Step 4: Log in to each service (once)

Open the automation browser and log in to the services you want Claude to access:

```bash
# Open YouTube
chrome-parenting "https://www.youtube.com/feed/history"
```

In the Chrome window that opens, sign in to your Google account. **You do this just once** — the profile saves your session, so you won't need to log in again on future runs (unless your session expires or you clear the profile).

Repeat for your library:
```bash
chrome-parenting "https://smcl.bibliocommons.com/user/login"
# (replace smcl with your library's BiblioCommons URL)
```

Log in with your library card number and PIN.

> **Session expiry:** Library and YouTube sessions typically last weeks to months. If a skill reports "login page found" or "not signed in," just open the automation browser, log in again, and re-run the skill.

---

## Safety tips — read this section

### 1. Keep the automation browser separate from your personal browser

The `--user-data-dir` flag means this Chrome window has its own bookmarks, history, and saved passwords — completely separate from your regular Chrome. If you delete `~/.chrome-parenting-profile`, you lose the saved sessions but nothing else.

**Never run automation using your default Chrome profile** (without the `--user-data-dir` flag). That would give automation access to your regular browser's saved passwords.

### 2. Close the automation browser when you're not using it

The debug port (9222) is open to any program on your computer while Chrome is running. This is fine on a personal machine, but there's no need to leave it open all day.

**Check if it's open:**
```bash
curl -s http://localhost:9222/json/version 2>/dev/null | python3 -c "import json,sys; print(json.load(sys.stdin).get('Browser',''))" || echo "Not running"
```

### 3. The Chrome window is always visible

This is intentional. You can watch everything Claude does — every page it visits, every button it clicks. If something looks wrong, just close the window. The automation stops immediately.

### 4. Claude types credentials from `.env` — not from your password manager

When a skill logs in (like the library skill), it reads the username and PIN from your `.env` file and types them into the login form. The values are never written to any output file. See [Playbook 4](04-password-safety.md) for how to store these safely.

### 5. Don't use your primary Google account if you can avoid it

For YouTube history scraping, the best setup is a supervised Google account that's specifically for your child's viewing. If your child watches YouTube on your main Google account, that account will be logged in to the automation browser. This is fine — just be aware of it.

---

## Step 5: Test the connection

With the automation browser open and logged into YouTube:

```bash
claude
```

In Claude Code, type:
```
List the pages currently open in Chrome.
```

You should see a list of open tabs. If you see a connection error, the automation browser isn't running. Open it with `chrome-parenting` and try again.

---

## Step 6: Run your first automated skill

```
/youtube-kids-audit --days 30
```

Claude will scroll through your YouTube history, extract video titles and channels, save them to `user_docs/YYYYMMDD_watch_history.json`, and print a summary.

Then analyze the content:
```
/youtube-kids-audit analyze-kids-content --profile emma
```

This classifies each channel by educational value and age-appropriateness, and saves a report to `user_docs/kid_profile/YYYYMMDD_emma_analysis.md`.

---

## Skills that use the browser

| Skill | What it logs into |
|-------|-----------------|
| `/youtube-kids-audit` | YouTube (google.com) |
| `/library-history` | Your library's BiblioCommons site |
| `/check-grades` | Your school's grade portal |
| `/find-school-calendar` | School website |

---

## Windows setup

The same approach works on Windows. The Chrome path and alias syntax are different:

**Chrome path:** `"C:\Program Files\Google\Chrome\Application\chrome.exe"`

**Profile folder:** `C:\Users\YourName\.chrome-parenting-profile`

**Command (run in Command Prompt or save as a .bat file):**
```
"C:\Program Files\Google\Chrome\Application\chrome.exe" ^
  --remote-debugging-port=9222 ^
  --no-first-run ^
  --no-default-browser-check ^
  --user-data-dir="C:\Users\YourName\.chrome-parenting-profile"
```

Everything else in this playbook is the same.

---

## Troubleshooting

| Problem | What to do |
|---------|-----------|
| "Connection refused" or "Not running" | Run `chrome-parenting` to open the automation browser |
| "Login page found, not signed in" | Log in manually in the automation browser window, then re-run the skill |
| `chrome-parenting` command not found | Close Terminal, reopen it, try again — the alias may not have loaded yet |
| Chrome window opens but immediately closes | Profile folder may be corrupted — delete `~/.chrome-parenting-profile` and start fresh |
| `/mcp` doesn't show chrome-devtools-cron | Re-run `claude mcp add ...` from Step 2 and restart Claude Code |
| Skill finishes but output file is empty | YouTube or library may have changed their page layout — open a GitHub issue |
