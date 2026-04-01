# Playbook

Detailed reference for skills, scheduling, community data, project structure, and contributing.

---

## Skills

Skills live in `skills/<category>/<name>/SKILL.md` and are symlinked to `~/.claude/skills/<name>`.

Status legend: `idea` → `draft` → `implemented` → `verified` · also `deprecated` / `retired`. See [skills_roadmap.md](skills_roadmap.md) for full definitions and quality checklist.

### academics

| Command | Description | Status |
|---------|-------------|--------|
| `/check-grades` | Pull grades, attendance, and assignments from school portals (PowerSchool, Infinite Campus, Canvas, Google Classroom) | `implemented` |
| `/analyze-report-card` | Ingest a PDF/photo report card, extract grades and teacher comments, generate a summer action plan | `draft` |
| `/weekly-digest` | Monday morning family summary: grades, upcoming assignments, events, lunch balances, action items | `implemented` |

### afterschools

| Command | Description | Status |
|---------|-------------|--------|
| `/find-events` | Find local kids events by city, age, and time window. Delegates to `kids-events-finder` agent | `implemented` |
| `/monitor-registration` | Watch a registration page (camp, class, sports) and send an alert when it opens | `implemented` |

### email

| Command | Description | Status |
|---------|-------------|--------|
| `/agentmail-skill` | Core AgentMail actions: send, read, reply, list-inboxes. Safety-gated — only sends to human owner allowlist | `draft` |
| `/agentmail-skill monitor-human-reply` | Poll inbox for replies from human owner, classify (approval/feedback/instruction/question), act and confirm | `draft` |
| `/agentmail-skill scan-emails` | Read-only inbox scan — summarize recent messages, filter by sender/keyword, optionally save to `user_docs/` | `draft` |

### media

| Command | Description | Status |
|---------|-------------|--------|
| `/youtube-kids-audit` | Analyze a child's YouTube watch history, classify channels by age-fit and educational value, and apply approved Family Link actions | `implemented` |

### shopping

| Command | Description | Status |
|---------|-------------|--------|
| `/order-food` | Automate kid-friendly food orders from saved restaurant presets, with allergen check and parent confirmation gate | `draft` |
| `/top-up-lunch` | Check school lunch balances and top up via MySchoolBucks when below threshold | `implemented` |

### util

| Command | Description | Status |
|---------|-------------|--------|
| `/info-gather` | Pull and deduplicate information from RSS, JSON APIs, and browser sources using a `sources.yaml` config | `implemented` |
| `/browser-automate` | Automate a Chrome task — school portals, registration forms, appointment booking, page monitoring | `implemented` |
| `/mac-cron-job` | Create, list, and debug scheduled automation tasks via launchd or crontab | `implemented` |
| `/send-email` | Send email from an AgentMail inbox (`your-agent@agentmail.to`, `your-inbox@agentmail.to`) | `implemented` |
| `/privacy-audit` | Scan skill files for PII, API keys, and child-identifiable data before submitting a PR | `draft` |

---

## Agents

Agents live in `agents/` and are invoked by skills or directly via Claude Code's agent system.

| Agent | Description |
|-------|-------------|
| `kids-events-finder` | Searches for local kids events given city, age range, and time window |
| `summer-camp-planner` | Researches, filters, and schedules summer camps for a given city and child profile |
| `factuality-checker` | Verifies parenting information at L1–L5 factuality levels (L1 = web search, L5 = primary source) |

---

## Scheduling with cron (macOS)

Skills are most powerful when they run automatically — Monday morning grade summaries, weekly YouTube audits, lunch balance checks before they hit zero. On a personal MacBook or Mac mini, `launchd` is the right tool.

### Why launchd over crontab

`launchd` is macOS-native. Unlike `crontab`, it survives reboots, logs cleanly to `/tmp/`, and doesn't require a running terminal session. Use `crontab` only for quick experiments; use `launchd` for anything you want to rely on.

### Quick setup

The `/mac-cron-job` skill handles plist creation for you:

```
/mac-cron-job create --schedule "Mon 7:00am" --command "claude -p '/weekly-digest'"
```

Or write a plist manually:

```bash
cat > ~/Library/LaunchAgents/com.parenting.weekly-digest.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.parenting.weekly-digest</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>-c</string>
    <string>cd /path/to/your/parenting && claude -p '/weekly-digest' --output-format text</string>
  </array>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Weekday</key><integer>1</integer>
    <key>Hour</key><integer>7</integer>
    <key>Minute</key><integer>0</integer>
  </dict>
  <key>StandardOutPath</key>
  <string>/tmp/weekly-digest.log</string>
  <key>StandardErrorPath</key>
  <string>/tmp/weekly-digest.err</string>
</dict>
</plist>
EOF

# Load it
launchctl load ~/Library/LaunchAgents/com.parenting.weekly-digest.plist

# Test it immediately
launchctl start com.parenting.weekly-digest

# Check logs
tail -f /tmp/weekly-digest.log
```

### Useful launchd commands

```bash
# List all loaded parenting jobs
launchctl list | grep parenting

# Unload (disable) a job
launchctl unload ~/Library/LaunchAgents/com.parenting.weekly-digest.plist

# Reload after editing a plist
launchctl unload ~/Library/LaunchAgents/com.parenting.weekly-digest.plist
launchctl load ~/Library/LaunchAgents/com.parenting.weekly-digest.plist
```

### Sending a briefing email from a cron job

Combine any skill output with `/send-email` to push results to your inbox instead of waiting to check:

```bash
# In your plist ProgramArguments:
claude -p '/weekly-digest | /send-email --to your-email@example.com --subject "Weekly family briefing"'
```

> **TODO:** Add sample plist files for common schedules (weekly digest, daily lunch balance check, YouTube audit)

> **TODO:** Add sample briefing email templates — concise HTML summaries with action items highlighted, sent from an AgentMail inbox to the parent's personal email

---

## Community data

Curated source configs and school portal configs. No code — data only.

```
community/
├── regions/
│   └── bay-area/
│       ├── sources.yaml                  # Bay Area-wide event and activity sources
│       └── san-carlos/
│           ├── README.md                 # Quick reference: key URLs, storytime schedule
│           └── sources.yaml             # 25+ San Carlos sources with topic presets
└── schools/
    ├── scsd/                             # San Carlos School District (TK–8)
    │   ├── README.md
    │   └── portals.yaml                  # PowerSchool + Google Classroom config
    └── suhsd-carlmont/                   # Carlmont High School (9–12)
        ├── README.md
        └── portals.yaml                  # Infinite Campus + Canvas Observer config
```

### Topic presets (`/info-gather [preset]`)

Defined in each `sources.yaml`. San Carlos presets:

| Preset | What it pulls |
|--------|--------------|
| `events_this_weekend` | Library, San Carlos Life, ChatterBlock, Eventbrite, Parks & Rec, SCCT |
| `summer_camps` | KidsOutAndAbout, CampPage, ChatterBlock, ActiveNet, SCCT, King's Swim |
| `school_news` | SCSD RSS + individual school feeds |
| `sports_registration` | AYSO, Little League, ActiveNet, Youth Sports, San Carlos United |
| `enrichment_classes` | ChatterBlock, SCCT, King's Swim, ActiveNet |
| `community_news` | San Carlos Life, Patch, Reddit r/SanCarlos, SM Daily Journal |

---

## Project structure

```
parenting/
├── README.md
├── playbook.md
├── design_doc.md
├── agents/
│   ├── factuality-checker-agent.md
│   ├── kids-events-finder.md
│   └── summer-camp-planner.md
├── skills/
│   ├── academics/
│   │   ├── analyze-report-card/SKILL.md
│   │   ├── check-grades/SKILL.md
│   │   └── weekly-digest/SKILL.md
│   ├── afterschools/
│   │   ├── find-events/SKILL.md
│   │   └── monitor-registration/SKILL.md
│   ├── email/
│   │   └── agentmail-skill/
│   │       ├── SKILL.md
│   │       ├── email_safety_guidelines.md
│   │       ├── monitor-human-reply/SKILL.md
│   │       └── scan-emails/SKILL.md
│   ├── media/
│   │   └── youtube-kids-audit/SKILL.md
│   ├── shopping/
│   │   ├── order-food/SKILL.md
│   │   └── top-up-lunch/SKILL.md
│   └── util/
│       ├── browser-automate/SKILL.md
│       ├── info-gather/SKILL.md
│       ├── mac-cron-job/SKILL.md
│       ├── privacy-audit/SKILL.md
│       └── send-email/SKILL.md
├── user_docs/                       ← per-user config and state (not committed)
│   └── agentmail_config.md          ← human owner allowlist + inbox settings
├── .env_template                    ← copy to .env, add API keys
└── community/
    ├── regions/
    │   └── bay-area/
    │       ├── sources.yaml
    │       └── san-carlos/
    │           ├── README.md
    │           └── sources.yaml
    └── schools/
        ├── scsd/
        │   ├── README.md
        │   └── portals.yaml
        └── suhsd-carlmont/
            ├── README.md
            └── portals.yaml
```

---

## Contributing

1. Create your skill under `skills/<category>/<name>/SKILL.md`
2. Run `/privacy-audit --path skills/<category>/<name>/ --mode report` before submitting
3. All Tier 1 issues (API keys, tokens, passwords) must be resolved
4. Replace any personal data (child names, real addresses, school portal IDs) with placeholders
5. Open a PR — the description should note any Tier 2 items left intentionally

### Adding a new city

1. Copy `community/regions/bay-area/san-carlos/` as a template
2. Update `sources.yaml` with local sources and presets
3. Add school districts under `community/schools/<district>/`
