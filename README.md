# awesome-parenting-skills

Reusable Claude Code skills, agents, and community data for automating family and parenting workflows.

## Quick start

Skills are installed globally via symlinks — run any `/command` from any Claude Code session:

```bash
# Link all skills to ~/.claude/skills/
for skill in skills/**/*; do
  name=$(basename $skill)
  ln -sf "$PWD/$skill" ~/.claude/skills/$name
done
```

---

## Skills

Skills live in `skills/<category>/<name>/SKILL.md` and are symlinked to `~/.claude/skills/<name>`.

### academics

| Command | Description | Status |
|---------|-------------|--------|
| `/check-grades` | Pull grades, attendance, and assignments from school portals (PowerSchool, Infinite Campus, Canvas, Google Classroom) | Implemented |
| `/analyze-report-card` | Ingest a PDF/photo report card, extract grades and teacher comments, generate a summer action plan | Placeholder |
| `/weekly-digest` | Monday morning family summary: grades, upcoming assignments, events, lunch balances, action items | Implemented |

### afterschools

| Command | Description | Status |
|---------|-------------|--------|
| `/find-events` | Find local kids events by city, age, and time window. Delegates to `kids-events-finder` agent | Implemented |
| `/monitor-registration` | Watch a registration page (camp, class, sports) and send an alert when it opens | Implemented |

### shopping

| Command | Description | Status |
|---------|-------------|--------|
| `/order-food` | Automate kid-friendly food orders from saved restaurant presets, with allergen check and parent confirmation gate | Placeholder |
| `/top-up-lunch` | Check school lunch balances and top up via MySchoolBucks when below threshold | Implemented |

### email

| Command | Description | Status |
|---------|-------------|--------|
| `/agentmail-skill` | Core AgentMail actions: send, read, reply, list-inboxes. Safety-gated — only sends to human owner allowlist | Placeholder |
| `/agentmail-skill monitor-human-reply` | Poll inbox for replies from human owner, classify (approval/feedback/instruction/question), act and confirm | Placeholder |
| `/agentmail-skill scan-emails` | Read-only inbox scan — summarize recent messages, filter by sender/keyword, optionally save to `user_docs/` | Placeholder |

### media

| Command | Description | Status |
|---------|-------------|--------|
| `/youtube-kids-audit` | Analyze a child's YouTube watch history, classify channels by age-fit and educational value, and apply approved Family Link actions | Placeholder |

### util

| Command | Description | Status |
|---------|-------------|--------|
| `/info-gather` | Pull and deduplicate information from RSS, JSON APIs, and browser sources using a `sources.yaml` config | Implemented |
| `/browser-automate` | Automate a Chrome task — school portals, registration forms, appointment booking, page monitoring | Implemented |
| `/mac-cron-job` | Create, list, and debug scheduled automation tasks via launchd or crontab | Implemented |
| `/send-email` | Send email from an AgentMail inbox (`your-agent@agentmail.to`, `your-inbox@agentmail.to`) | Implemented |
| `/privacy-audit` | Scan skill files for PII, API keys, and child-identifiable data before submitting a PR | Placeholder |

---

## Agents

Agents live in `agents/` and are invoked by skills or directly via Claude Code's agent system.

| Agent | Description |
|-------|-------------|
| `kids-events-finder` | Searches for local kids events given city, age range, and time window |
| `summer-camp-planner` | Researches, filters, and schedules summer camps for a given city and child profile |
| `factuality-checker` | Verifies parenting information at L1–L5 factuality levels (L1 = web search, L5 = primary source) |

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

---

## Related

- [`design_doc.md`](design_doc.md) — Full architecture, Chrome automation guide, safety model, roadmap
