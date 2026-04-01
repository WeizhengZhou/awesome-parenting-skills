# Playbook 3 — Scheduled Jobs

**What you get:** Your weekly routines (YouTube audit, library sync, email digest) run automatically every Sunday morning without you having to do anything.

**Time:** 45–60 minutes
**Prerequisites:** Playbooks 0, 1, and 2 complete.
**Platform:** macOS. (Windows users: see the simple alternative at the end.)

---

## At a glance — what you do vs. what the agent does

| Section | You need to... | Agent does |
|---------|---------------|-----------|
| Understanding cron jobs | Read once | — |
| Create the 3 weekly jobs | Ask in plain English: "Set up the three standard weekly media tracking jobs" | ✅ Creates and schedules all three jobs |
| launchd setup (auto wake) | Run 3 terminal commands (one-time, ~10 min) | — |
| Enable wake from sleep | Toggle one setting in System Settings | — |
| Monitor: did jobs run? | Check your Sunday email | ✅ Sends you confirmation via the digest email |
| Cancel or change a job | Ask in plain English: "Cancel cron job [ID]" | ✅ Cancels it |
| Re-register expired jobs | Ask: "Set up the weekly jobs again" (if jobs expired after 7 days) | ✅ Recreates them |
| Simple alternative (no launchd) | Open Claude Code on Sunday, ask to run the jobs | ✅ Runs all three in sequence |

**TL;DR for setup:**
- **Cron jobs** (the tasks): just ask Claude to set them up — takes 30 seconds.
- **launchd** (the wake-up alarm): copy-paste 3 terminal commands — takes 10 minutes.
- If you skip launchd, just run Claude manually on Sunday. Both approaches work.

---

## The big picture

Fully automatic weekly automation needs two things working together:

```
macOS launchd          →  wakes your Mac on Sunday morning, starts Claude Code
Claude Code cron jobs  →  runs the YouTube / library / newsletter tasks in order
```

Think of it as: **launchd is the alarm clock** that wakes everything up. **Claude Code cron jobs are the to-do list** that run once the machine is awake.

If this feels like too much setup, skip to **"Simple alternative"** at the bottom — you can get 80% of the value by just running Claude Code manually once a week.

---

## Part A — Claude Code Cron Jobs

### What is a cron job?

A cron job is a task that runs on a schedule — like "every Sunday at 9am, do this." In Claude Code, the "task" is a plain English prompt. When the scheduled time arrives, Claude Code runs the prompt automatically, as if you typed it yourself.

### Creating jobs in plain English

Just tell Claude Code what you want:

```
Schedule a job every Sunday at 9am to run the library history skill.
```

Claude creates the job and gives you an ID like `538228fd`. Write it down — you'll need it if you want to cancel the job.

### The three standard jobs for this repo

Set these up by telling Claude Code in plain English, or have Claude set them up for you by asking:

```
Set up the three standard weekly media tracking jobs for my child.
```

| Job | Time | What it does |
|-----|------|-------------|
| YouTube audit | Sunday 8:47am | Reads watch history, classifies channels, saves report |
| Library sync | Sunday 9:13am | Logs into library, fetches borrowed books, saves list |
| Media newsletter | Sunday 10:07am | Combines both reports, writes HTML email, sends it to you |

> Jobs are intentionally scheduled at odd minutes (8:47, not 9:00) so they don't all hit the same server at the same moment as other users.

### Check what jobs are scheduled

Inside Claude Code:
```
List my scheduled cron jobs.
```

### Important: jobs expire after 7 days

Claude Code cron jobs automatically stop after 7 days. This is a built-in safety limit.

**How to handle this:**
- Ask for "durable" jobs (they reload when Claude Code starts): `Schedule a durable job every Sunday at 9am...`
- Even durable jobs expire after 7 days, so Claude Code must be **running at least once a week** to re-register them
- The launchd setup in Part B handles this by starting Claude Code automatically

### Cancel a job

```
Cancel cron job 538228fd.
```
(Use the actual job ID shown when you created it.)

---

## Part B — macOS launchd (Wake Your Mac Automatically)

launchd is macOS's built-in scheduler. It can wake your Mac from sleep and run a command at a set time every week — even if you forgot to leave it on.

### Step 1: Find your project path

```bash
cd /path/to/awesome-parenting-skills
echo $PWD
```

Copy the output. You'll paste it into the config file below.

### Step 2: Create the launchd config file

Run this command (paste your actual project path where it says `REPLACE_THIS`):

```bash
PROJECT_PATH="REPLACE_THIS"   # ← paste your project path here, e.g. /Users/yourname/awesome-parenting-skills

cat > ~/Library/LaunchAgents/com.parenting.claude-cron.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.parenting.claude-cron</string>

  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>-c</string>
    <string>cd ${PROJECT_PATH} && claude --print "The scheduled weekly jobs should now be running. Check and run any pending cron tasks for the parenting assistant." >> /tmp/claude-parenting.log 2>&1</string>
  </array>

  <key>StartCalendarInterval</key>
  <dict>
    <key>Weekday</key>  <integer>0</integer>
    <key>Hour</key>     <integer>8</integer>
    <key>Minute</key>   <integer>30</integer>
  </dict>

  <key>WakeForJob</key>
  <true/>

  <key>StandardOutPath</key>
  <string>/tmp/claude-parenting.log</string>
  <key>StandardErrorPath</key>
  <string>/tmp/claude-parenting-error.log</string>
</dict>
</plist>
EOF
```

**What the fields mean:**
- `StartCalendarInterval` — when to run: Weekday 0 = Sunday, Hour 8, Minute 30 = 8:30am
- `WakeForJob` — wake the Mac from sleep to run this
- `StandardOutPath` / `StandardErrorPath` — where to save log output so you can check if it ran

### Step 3: Activate it

```bash
launchctl load ~/Library/LaunchAgents/com.parenting.claude-cron.plist
```

Confirm it's registered:
```bash
launchctl list | grep parenting
# Should print a line with: com.parenting.claude-cron
```

### Step 4: Test it right now (don't wait until Sunday)

```bash
launchctl start com.parenting.claude-cron
```

Wait 10 seconds, then check the log:
```bash
tail -30 /tmp/claude-parenting.log
```

You should see Claude Code starting up and acknowledging the request. If the file is empty, the project path in the config may be wrong — re-run Step 2 with the correct path.

### Step 5: Allow your Mac to wake up from sleep

1. Open **System Settings** → **Battery** (or **Energy Saver** on older macOS)
2. Enable **"Wake for network access"**

> **MacBook note:** When running on battery, Macs sometimes skip scheduled wake events. If you want reliable Sunday automation, leave the MacBook plugged in Saturday night. Alternatively, just check the log on Monday morning — if it ran, great; if not, trigger manually.

### Updating the schedule

To change the run time, edit the plist file and reload:
```bash
# Edit the file
open -e ~/Library/LaunchAgents/com.parenting.claude-cron.plist

# After saving, reload:
launchctl unload ~/Library/LaunchAgents/com.parenting.claude-cron.plist
launchctl load  ~/Library/LaunchAgents/com.parenting.claude-cron.plist
```

### Stop the automation

```bash
launchctl unload ~/Library/LaunchAgents/com.parenting.claude-cron.plist
```

To start again:
```bash
launchctl load ~/Library/LaunchAgents/com.parenting.claude-cron.plist
```

---

## How to check if everything ran

### Best check: did the digest email arrive?

The newsletter job sends you an email every Sunday. If it's in your inbox — all three jobs ran.

### Check the log file

```bash
tail -50 /tmp/claude-parenting.log
```

Look for timestamps and task names. If the log ends at 8:30am with no further activity, the cron jobs didn't fire — check that they're registered (ask Claude Code to list them).

### Check output files exist

```bash
# Look for today's date in filenames
ls user_docs/kid_profile/ | grep $(date +%Y%m%d)    # YouTube analysis
ls user_docs/library/      | grep $(date +%Y%m%d)    # Library sync
ls user_docs/digest/       | grep $(date +%Y%m%d)    # Newsletter
```

If today's date appears in the filenames, those jobs ran successfully.

### Ask Claude Code

```
Did the weekly jobs run this week? Check user_docs/ for this week's files.
```

---

## Simple alternative (no launchd required)

If launchd feels like too much, here's a simpler approach that still saves you most of the effort:

**Keep a Terminal window open on Sunday mornings.** Start Claude Code and ask:

```
Run the weekly media tracking jobs: YouTube audit, library sync, and media newsletter.
```

Claude will run all three in sequence and email you the results. The only difference from full automation is that you have to remember to do it — but you only need to be present for 30 seconds.

This is a perfectly valid setup. Most parents who try full automation end up using this anyway because Sunday mornings are unpredictable.

---

## Full weekly flow (when everything is set up)

```
Saturday night  →  plug in MacBook (optional but recommended)
Sunday 8:30am   →  Mac wakes from sleep, Claude Code starts
Sunday 8:47am   →  YouTube audit runs automatically
Sunday 9:13am   →  Library sync runs automatically
Sunday 10:07am  →  Newsletter is generated and emailed to you
Sunday morning  →  email arrives in your inbox 📧
```

---

## Troubleshooting

| Problem | What to do |
|---------|-----------|
| Jobs didn't run on Sunday | Check if Mac was asleep — plug in next week; also check `/tmp/claude-parenting-error.log` |
| `launchctl load` gives "already loaded" error | Run `unload` first, then `load` again |
| `launchctl load` gives permission error | Run: `chown $USER ~/Library/LaunchAgents/com.parenting.claude-cron.plist` |
| Log file is empty after `launchctl start` | The project path in the plist is wrong — redo Step 2 with the correct path |
| YouTube audit fails | Debug Chrome needs to be open and logged in; this job can't open Chrome by itself on a sleeping Mac |
| Library sync fails | Library session may have expired — open `chrome-parenting`, log in to the library, try again |
| Cron jobs aren't listed in Claude Code | They may have expired (7-day limit) — recreate them |
