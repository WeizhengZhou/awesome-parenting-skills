# Playbook 0 — Basic Setup

**What you get:** Book and media recommendations, discussion questions for any book, reading plans — all saved as files on your computer. No accounts, no internet connections needed beyond the initial install.

**Time:** 20–30 minutes
**Tech level:** Beginner — if you can copy and paste commands, you can do this.

---

## At a glance — what you do vs. what the agent does

| Section | You need to... | Agent does |
|---------|---------------|-----------|
| Open Terminal | Read this section once | — |
| Install Node.js | Install it (one-time, ~5 min) | — |
| Install Claude Code | Run one command | — |
| Download project | Download or clone once | — |
| Create `user_docs/` folder | Run one command | — |
| Link skills | Run one command | — |
| Fill in child profile | Write it; add more over time | Reads it to personalize all output |
| Run a skill | Type the command or ask in plain English | ✅ Generates everything — questions, plans, recommendations |
| Get book/media recommendations | Just ask | ✅ Reads your files, builds the plan |
| Extract info from school emails | Paste the email text | ✅ Pulls out dates, action items, reminders |

**TL;DR for setup:** Steps 1–6 are one-time installs (30 min total). After that, everything is just asking questions.

---

## Before you start: open Terminal

Terminal is a text-based window where you type commands. It comes with every Mac.

**To open Terminal:**
- Press **Command + Space**, type `Terminal`, press Enter
- Or: open Finder → Applications → Utilities → Terminal

A window with a `$` prompt appears. You type commands after the `$`. You don't type the `$` itself.

> **On Windows:** Use "Command Prompt" or "Windows Terminal" (search for either in the Start menu). Most commands in this guide work the same way.

---

## Step 1: Install Node.js

Node.js is a runtime that Claude Code needs. Check if it's already installed:

```bash
node --version
```

If you see something like `v20.11.0` — you already have it. Skip to Step 2.

If you see "command not found":
1. Go to **nodejs.org**
2. Click the big green **"LTS"** download button (LTS = Long Term Support, the stable version)
3. Run the installer, follow the prompts
4. Close and reopen Terminal, then run `node --version` again to confirm

---

## Step 2: Install Claude Code

```bash
npm install -g @anthropic-ai/claude-code
```

This installs Claude Code globally on your machine. It takes about 1 minute.

Verify it worked:
```bash
claude --version
```

You should see a version number. If you see "command not found", try closing and reopening Terminal, then try again.

**First-time login:** Run `claude` once and follow the prompts to log in with your Anthropic account. If you don't have an account, it will walk you through creating one.

---

## Step 3: Download this project

**Option A: Using git (if you have it)**
```bash
git clone https://github.com/YOUR-REPO-URL/awesome-parenting-skills.git
cd awesome-parenting-skills
```

Check if git is installed: `git --version`. If not installed, use Option B.

**Option B: Download as ZIP**
1. Go to the GitHub page for this project
2. Click the green **Code** button → **Download ZIP**
3. Unzip it somewhere easy to find (like your home folder or Desktop)
4. In Terminal, navigate to it:
```bash
cd ~/Desktop/awesome-parenting-skills  # adjust path to where you unzipped it
```

Confirm you're in the right place:
```bash
ls
# You should see: skills/  user_docs_template/  playbook/  README.md  etc.
```

---

## Step 4: Create your personal config folder

```bash
cp -r user_docs_template/ user_docs/
```

This copies a set of template files into a new `user_docs/` folder. This folder is where all your personal data lives — your child's profile, reading history, school info. It is **never uploaded to GitHub** (it's excluded from version control automatically).

---

## Step 5: Link the skills

Skills are the AI instructions that power each command. They need to be linked to a folder where Claude Code looks for them. Run this once:

```bash
mkdir -p ~/.claude/skills
for dir in skills/*/*; do
  [ -f "$dir/SKILL.md" ] || continue
  name=$(basename "$dir")
  ln -sf "$PWD/$dir" ~/.claude/skills/"$name"
  echo "✓ $name"
done
```

You should see a list of skill names printed with checkmarks. If you see nothing, check that you're in the project folder (`ls` should show a `skills/` directory).

> **What does this do?** It creates shortcuts (called "symlinks") from the `skills/` folder in this project to `~/.claude/skills/`. Claude Code looks in that folder for available commands. When you update skills in this project, the changes take effect immediately — no re-running this step.

---

## Step 6: Fill in your child's profile

Open the template file in a text editor (TextEdit on Mac, Notepad on Windows):

```bash
# Create a profile for your child
cp user_docs/kid_profile/_template.md user_docs/kid_profile/emma_profile.md
# Replace "emma" with your child's name
```

Open that file and fill in what you know:
- Child's name, age, current grade
- School name and location
- Books they've liked and disliked
- Favorite topics, movies, shows
- Activities and hobbies

**You don't need to fill in everything.** Even just name, age, and 2–3 favorite books gives Claude enough to make good recommendations. You can add more details over time.

---

## Step 7: Start Claude Code

Navigate to the project folder in Terminal and start Claude Code:

```bash
cd ~/Desktop/awesome-parenting-skills   # or wherever you put the project
claude
```

A `>` prompt appears. You're now talking to Claude Code. You can type commands (starting with `/`) or just ask questions in plain English.

---

## Step 8: Try your first skill

Type this and press Enter:

```
/co-read-prepare "Charlotte's Web"
```

Claude will:
1. Read your child's profile to tailor the output
2. Generate a **parent briefing** (so you can discuss the book without having read it)
3. Generate **4 levels of discussion questions** from basic to creative
4. Save everything to `user_docs/school/co-read/YYYYMMDD_charlottes-web.md`

**How to read the output file:**
- Open the file in VS Code (free download at code.visualstudio.com) — it renders markdown nicely
- Or drag the `.md` file into a browser — Chrome and Firefox both display it readably
- Or open it in any text editor — it's plain text with some formatting marks

---

## What else you can do right now (no extra setup)

**Ask anything in plain English:**
```
What books should my child read next based on their profile?
```
```
My child loved The Wild Robot. What similar books would they enjoy?
```
```
Paste school newsletter text here and ask: "What are the action items from this newsletter?"
```

**Paste content directly:** You don't have to save things to files first. Just paste a list of books, a school email, or a curriculum document into Claude and ask questions about it.

**Skills available with no extra setup:**

| Command | What it does |
|---------|-------------|
| `/co-read-prepare "Book Title"` | Parent briefing + 4-level discussion questions |
| Ask in plain English | Book/video/audio recommendations from reading log |
| Paste + ask | Extract key dates and action items from school emails |
| Paste + ask | Build a media plan from a list of watched/read items |

---

## Tips for getting better results

- **The more detail in the child profile, the better.** "Loves Dragon Masters, 5 stars; dropped Charlotte's Web, too slow" gives far better recommendations than just "age 7."
- **Rate books as you go.** Open `user_docs/kid_profile/emma_profile.md` and add ratings as your child finishes books. Claude uses this history to spot patterns.
- **You don't need to use slash commands.** Just typing in plain English works. The slash commands are shortcuts.
- **Saved files are in `user_docs/`.** Everything Claude generates is saved there. You can open, share, or print any of those files.

---

## Expected output after setup

After completing this playbook, your `user_docs/` folder will look like:

```
user_docs/
├── kid_profile/
│   └── emma_profile.md          ← your child's profile
├── school/
│   └── co-read/                 ← discussion question files go here
└── agentmail_config.md          ← (fill in later — Playbook 2)
```

---

## Next steps

Once you're comfortable with basic usage:
- **[Playbook 4](04-password-safety.md)** — set up safe password storage before connecting any accounts (do this before 1 or 2)
- **[Playbook 1](01-chrome-mcp.md)** — automate YouTube history and library record fetching
- **[Playbook 2](02-agentmail.md)** — have school emails automatically forwarded and processed
