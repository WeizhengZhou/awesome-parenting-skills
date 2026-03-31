# awesome-parenting-skills — Design Document

> A community-curated collection of Claude Code agents, skills, and MCP configurations for automating family life.

---

## 1. Vision

Modern parents spend enormous time on coordination overhead: monitoring school portals, finding summer camps, booking appointments, managing kids' activities, and staying on top of school communications. Claude Code — running locally with access to a signed-in Chrome session and MCP servers — can automate most of this.

**awesome-parenting-skills** is a public GitHub repo that:
- Seeds reusable agents and skills for common parenting tasks
- Curates the best public MCP servers for family automation
- Provides Chrome automation patterns for portals that require real browser sessions
- Invites community contributions for school/region/family-specific needs
- Grows into the canonical resource for Claude Code × parenting automation

**Core design principle:** Everything runs locally. Children's data never leaves your machine unless you explicitly choose otherwise.

---

## 2. Repo Structure

```
awesome-parenting-skills/
│
├── README.md                        # Hub index, quick-start, install instructions
├── CONTRIBUTING.md                  # How to submit agents, skills, MCP configs
├── CLAUDE.md                        # Template: copy to your project, fill in family details
├── family-state.schema.json         # JSON schema for shared state across agents
│
├── agents/                          # Sub-agents → drop in ~/.claude/agents/
│   ├── README.md
│   ├── summer-camp-planner.md       # Find + schedule summer camps (any region)
│   ├── kids-events-finder.md        # Find local family events (parameterized by city)
│   ├── appointment-scheduler.md       # Book/monitor doctor, dentist, specialist slots
│   ├── school-portal-watcher.md      # Monitor grades, attendance, assignments
│   ├── homework-tracker.md           # Aggregate assignments across Canvas, Classroom, etc.
│   ├── youtube-channel-manager.md    # Manage kids' YouTube channel or content curation
│   └── factuality-checker-agent.md  # Verify claims before acting: camps, events, health
│
├── skills/                          # Slash-command skills → install via Claude Code
│   ├── README.md
│   ├── info_gather_skill/           # /info-gather [topic] — multi-source info gathering
│   │   └── SKILL.md
│   ├── browser_automation_skill/    # /browser-automate [task] — Chrome headed/headless
│   │   └── SKILL.md
│   ├── mac_cron_job_skill/          # /mac-cron-job [create|list|remove|debug|logs]
│   │   └── SKILL.md
│   ├── find-camps/                  # /find-camps → runs summer-camp-planner agent
│   ├── find-events/                 # /find-events → runs kids-events-finder agent
│   ├── check-grades/                # /check-grades → polls school portal
│   ├── top-up-lunch/                # /top-up-lunch → checks and tops up lunch account
│   ├── weekly-digest/               # /weekly-digest → compiles family weekly summary
│   └── monitor-registration/        # /monitor-registration [url] → watches for open spots
│
├── mcp/                             # MCP server setup guides + config snippets
│   ├── README.md
│   ├── google-workspace.md          # Gmail + Calendar + Drive (taylorwilsdon/google_workspace_mcp)
│   ├── youtube.md                   # YouTube channel management
│   ├── notion.md                    # Family wiki, homework tracker boards
│   ├── todoist.md                   # Family to-do lists (official Doist MCP)
│   ├── apple-calendar.md            # macOS Calendar via mcp-ical
│   ├── chrome-automation.md         # Headed/headless Chrome setup guide
│   └── notifications.md             # ntfy + Pushover setup for family alerts
│
├── automation/                      # Reusable scripts and patterns
│   ├── README.md
│   ├── chrome/
│   │   ├── connect-existing-session.js    # CDP attach to running Chrome
│   │   ├── save-school-session.js         # One-time headed login → storageState
│   │   ├── monitor-page-change.js         # Poll URL for content changes
│   │   └── fill-registration-form.js      # Generic form-fill pattern
│   ├── school-portals/
│   │   ├── infinite-campus.py       # Grades, attendance, assignments
│   │   ├── canvas-observer.py       # Canvas API via observer/parent role
│   │   ├── powerschool.py           # PowerSchool grades + schedule
│   │   └── google-classroom.py      # Classroom API for assignments
│   ├── scheduling/
│   │   ├── mychart-slots.py         # Monitor MyChart for earlier appointment slots
│   │   ├── lunch-balance.js         # Check + top up MySchoolBucks
│   │   └── rec-department.js        # Monitor city rec registration pages
│   └── notifications/
│       ├── ntfy.py                  # ntfy.sh push notification helper
│       └── notify.py                # Multi-channel notification dispatcher
│
├── memory/                          # CLAUDE.md templates for memory management
│   ├── family-template.md           # Top-level family context template
│   ├── child-template.md            # Per-child context template
│   └── README.md
│
├── examples/                        # End-to-end workflow walkthroughs
│   ├── summer-planning/             # Full summer camp research + scheduling
│   ├── weekly-family-digest/        # Automated weekly summary workflow
│   ├── appointment-monitoring/      # Doctor slot monitoring + booking
│   ├── school-portal-daily/         # Daily grade + homework pull
│   └── youtube-channel-mgmt/        # Managing a kids' YouTube channel
│
├── safety/                          # Privacy and security guidelines
│   ├── README.md                    # Overview and principles
│   ├── coppa-ferpa-guide.md         # What parents need to know
│   ├── credential-management.md     # Keychain, env vars, storageState safety
│   └── responsible-scraping.md      # Rate limits, robots.txt, ToS considerations
│
└── community/                       # Region/school-specific contributions
    ├── README.md
    ├── regions/
    │   ├── _template/               # Template for new regions
    │   ├── bay-area/
    │   ├── seattle/
    │   ├── nyc/
    │   └── socal/
    └── schools/
        ├── _template/               # Template for a school-district contribution
        ├── sfusd/                   # San Francisco Unified
        ├── pausd/                   # Palo Alto Unified
        └── cusd/                    # Cupertino Unified
```

---

## 3. Seed Content — Agents

### 3.1 `summer-camp-planner` (generalized from existing)

**Source:** `~/.claude/agents/bay-area-kids-summer-camp-planner.md`
**Changes for public release:**
- Remove Bay Area hardcoding; make `region` a required first-ask parameter
- Keep Bay Area as the worked example in documentation
- Add a `community/bay-area/` variant that has Bay Area-specific camp sources baked in

**What it does:** Takes a family's constraints (age, interests, dates, budget, location) → searches live web for real camps → returns ranked list or week-by-week calendar.

---

### 3.2 `kids-events-finder` (generalized from existing)

**Source:** `~/.claude/agents/kids-events-finder.md`
**Changes for public release:**
- Remove hardcoded "San Carlos, CA" and specific surrounding cities
- Make `city`, `age_range`, and `radius_miles` required intake parameters
- Community variants in `community/bay-area/` can re-add the specific Peninsula cities

**What it does:** Finds local family-friendly events (storytime, festivals, classes, playground meetups) for a given city and age range.

---

### 3.3 `appointment-scheduler` (new)

Monitors doctor, dentist, and specialist availability. Handles:
- MyChart (Epic) FHIR API for appointment slot queries
- ZocDoc availability monitoring via changedetection.io
- Practice-specific portals via Playwright
- Cancellation monitoring: notifies when an earlier slot opens than your current appointment
- Integrates with Google Calendar or Apple Calendar via MCP to auto-block confirmed slots

---

### 3.4 `school-portal-watcher` (new)

Daily or on-demand pull from school information systems:
- Grades (new grades posted, grade drops below threshold)
- Attendance (absences, tardies)
- Upcoming assignments and due dates
- School announcements

Supports: Infinite Campus, Canvas (observer role), PowerSchool, Schoology, Google Classroom.
Credential storage: macOS Keychain via `keyring` — no plaintext passwords.

---

### 3.5 `homework-tracker` (new)

Aggregates assignments across platforms into a unified weekly view:
- Queries Canvas API + Google Classroom API
- Parses assignment due dates and submission status
- Produces a per-child weekly homework summary
- Flags overdue or missing submissions
- Feeds data into `family-state.json` for cross-agent visibility

---

### 3.7 `factuality-checker-agent` (new, adapted from trending_topics)

Verifies claims before a parent acts on them. Adapted from the trending_topics fact-checker with a parenting-specific evidence framework.

**Two modes:**
- **Briefing Mode** — given a batch of items from `/info-gather` or `summer-camp-planner`, verifies the top claims (prices, dates, eligibility, location) and outputs a structured fact sheet with L1–L5 confidence levels
- **Single-Item Mode** — deeply verifies one specific claim: "Is this camp accredited?", "Is this pediatric guideline current?", "Is this event still happening?"

**Factuality levels (same L1–L5 system as trending_topics, adapted for parenting):**
- L1: Multi-source confirmed — act on it
- L2: Single official source — act, note the source
- L3: Community signal only (forum, neighbor) — verify before spending money
- L4: Unverifiable or outdated — find a better source
- L5: Confirmed wrong — discard, see correction

**Domain-specific sources baked in:** ACA camp accreditation, AAP/CDC for health claims, CDE for California schools, city gov for local events, insurance provider directories for appointments.

**Mechanism overreach check:** Flags common parenting misinformation patterns — single study extrapolated to universal truth, outdated data presented as current, marketing copy treated as fact.

---

### 3.6 `youtube-channel-manager` (new)

For families managing a kids' YouTube channel or curating content:
- Upload videos without YouTube Studio UI
- Manage playlists (add, reorder, remove)
- Pull channel analytics (views, watch time, subscriber count)
- Screen videos for content safety before adding to a child's playlist (YouTube Data API v3 content ratings)
- Schedule video publishing

Uses: `ZubeidHendricks/youtube-mcp-server` + YouTube Data API v3.

---

## 4. Seed Content — Skills (Slash Commands)

### General-purpose skills (reusable across all parenting tasks)

| Skill | Command | Description |
|-------|---------|-------------|
| info_gather_skill | `/info-gather [topic]` | Gather + deduplicate information from RSS feeds, APIs, browser, web search. Configurable via `sources.yaml`. Works for camps, events, school news, local activities. |
| browser_automation_skill | `/browser-automate [task]` | Automate any browser task: attach to existing Chrome (Tier 0/1 for SSO portals), Playwright persistent profile (Tier 2 for scheduled), or headless (Tier 3 for public pages). Includes safety blocklist, credential management, and form-fill confirmation flow. |
| mac_cron_job_skill | `/mac-cron-job [create\|list\|remove\|debug\|logs]` | Set up macOS launchd plists or crontab entries for scheduled automation. Includes log management, debugging guide, ntfy notification integration, and recommended family automation schedule. |

### Domain-specific skills

| Skill | Command | Description |
|-------|---------|-------------|
| find-camps | `/find-camps` | Launches summer-camp-planner agent with intake flow |
| find-events | `/find-events [city] [age]` | Finds local family events this week/weekend |
| check-grades | `/check-grades [child]` | Pulls latest grades and assignments from school portal |
| top-up-lunch | `/top-up-lunch [child]` | Checks lunch balance and tops up if below threshold |
| weekly-digest | `/weekly-digest` | Compiles grades, events, assignments, appointments into a weekly summary |
| monitor-registration | `/monitor-registration [url]` | Sets up changedetection.io watch on a registration page |

---

## 5. MCP Servers to Feature

### Essential stack for most families

| Need | Server | Repo | Stars |
|------|--------|------|-------|
| Google Calendar + Gmail + Drive | google_workspace_mcp | taylorwilsdon/google_workspace_mcp | 1,977 |
| YouTube channel management | youtube-mcp-server | ZubeidHendricks/youtube-mcp-server | 473 |
| Screen YouTube content | mcp-server-youtube-transcript | kimtaeyoon83/mcp-server-youtube-transcript | 507 |
| Family wiki / task boards | notion-mcp-server | makenotion/notion-mcp-server (official) | 4,137 |
| To-do lists | todoist-ai | Doist/todoist-ai (official) | 413 |
| Apple Calendar (macOS) | mcp-ical | Omar-v2/mcp-ical | — |
| School portals (logged-in Chrome) | mcp-chrome | hangwin/mcp-chrome | 11,035 |
| General browser automation | playwright-mcp | microsoft/playwright-mcp | 30,065 |
| Appointment booking links | calendly-mcp-server | meAmitPatil/calendly-mcp-server | — |
| 500+ apps via one install | Rube | ComposioHQ/Rube | — |

### Already in your environment

- `chrome-devtools-cron` — available as `mcp__chrome-devtools-cron__*` tools; handles click, fill, navigate, screenshot, evaluate_script, and more. Good for headed Chrome sessions you control.
- `bay-area-kids-summer-camp-planner` agent — installed at `~/.claude/agents/`
- `kids-events-finder` agent — installed at `~/.claude/agents/`

---

## 6. Chrome Automation Guide

This is a core differentiator of the project: most school and appointment portals require a real logged-in browser session. We document three tiers of browser automation.

### Tier 1: Attach to your existing Chrome (recommended for school portals)

Best for portals that use Google SSO, Microsoft SSO, or complex school authentication.

**Setup (macOS):**
```bash
# Launch Chrome with remote debugging enabled
open -a "Google Chrome" --args --remote-debugging-port=9222

# In your automation script, connect to it
const browser = await chromium.connectOverCDP('http://localhost:9222');
const context = browser.contexts()[0]; // reuses all your existing sessions
```

**Why this works:** You log in manually once. The automation reuses your existing cookies and sessions forever. No login automation needed — no CAPTCHA, no SSO bypass required.

**MCP option:** `hangwin/mcp-chrome` (Chrome extension) exposes your real Chrome tabs to Claude Code via MCP. Install the extension, and Claude can read, click, and fill forms in your existing browser tabs.

---

### Tier 2: Persistent Chrome profile (for headless re-runs)

Best for automation that runs overnight or on a schedule.

```javascript
const { chromium } = require('playwright');

// Step 1: One-time headed login (run this manually once)
const browser = await chromium.launchPersistentContext('./profiles/school', {
  headless: false,
  channel: 'chrome'         // use your real Chrome, not Chromium
});
const page = await browser.newPage();
await page.goto('https://parentvue.district.org');
// Complete login manually in the browser window that opens
// Wait until you're fully logged in, then:
await browser.storageState({ path: './profiles/school-auth.json' });
await browser.close();

// Step 2: Reuse the session in future runs (can be headless)
const ctx = await chromium.launchPersistentContext('./profiles/school', {
  headless: true,
  storageState: './profiles/school-auth.json'
});
```

**Session refresh:** Sessions expire. Build in a check: if the page redirects to a login URL, surface a notification to log in again and save a new `storageState`.

**Security:** Store `school-auth.json` with `chmod 600`. Add `profiles/` to `.gitignore`. These files contain session tokens equivalent to your password.

---

### Tier 3: Full headless automation (for public/unauthenticated pages)

Best for public school calendars, library events, Eventbrite, rec department pages.

```javascript
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();

// Set a realistic user agent
await page.setExtraHTTPHeaders({
  'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) ...'
});

// Add human-like delays
await page.waitForTimeout(Math.random() * 1000 + 500);
await page.goto('https://www.cityofsunnyvale.org/parks/register');
```

---

### Page Change Monitoring (for registration openings, appointment slots)

Run [changedetection.io](https://github.com/dgtlmoon/changedetection.io) locally via Docker:

```bash
docker run -d --restart unless-stopped \
  -p 5000:5000 \
  -v ~/.changedetection:/datastore \
  dgtlmoon/changedetection.io
```

Point it at the registration URL. Configure it to use Playwright rendering (for JavaScript-heavy pages). Set notification to ntfy, Pushover, or email. Watch for the text change from "Join Waitlist" to "Register Now."

---

## 7. School Portal Integration

### Portal coverage map

| Portal | API/Library | Notes |
|--------|-------------|-------|
| Infinite Campus | `gilesgc/Infinite-Campus-API` (Python), `tonyzimbinski/infinite-campus` (Node) | Common in Midwest/West; unofficial wrappers |
| PowerSchool | `dougpenny/PyPowerSchool`, `ouiliame/ps.py` | Wide national coverage; Dec 2024 breach — expect MFA |
| Canvas (K-12) | `ucfopen/canvasapi` (official Python) | Observer/parent role required from school |
| Google Classroom | `googleapis` (Python/Node, official) | Guardian invite from teacher required |
| Schoology | Official REST API + OAuth | Full developer docs available |
| Aeries (CA) | Browser automation only | Common in California; no parent API |
| ParentVUE (Synergy) | Browser automation only | Common in Pacific Northwest and CA |

### Authentication pattern for all portals

1. Check if the portal has an official parent API → use it with OAuth
2. If unofficial wrapper exists → use it with credentials from macOS Keychain
3. If neither → use Playwright Tier 1 or Tier 2 (attach to existing session or persistent profile)
4. Never store credentials in plaintext or in version-controlled files

---

## 8. Safety and Privacy Guidelines

### Guiding principles

1. **Local-first processing.** Children's school data, health records, and schedules should not leave your machine unless you explicitly choose to send them to an external service.
2. **Minimal data collection.** Automate only what you actually need. Don't cache grade data indefinitely — delete after it's served its purpose.
3. **Credentials in system keychain.** Use macOS Keychain (`keyring` Python package) or equivalent. No `.env` files with passwords committed to any repo.
4. **Respectful automation.** Rate-limit requests. Don't scrape during school business hours. Identify your automation with a descriptive User-Agent.

### COPPA / FERPA basics for parents

- **COPPA (2025 update, effective April 2026):** Covers collection of children's personal data by operators. As a parent using automation for your own child via your own credentials, you are not an "operator" — COPPA applies to the platforms, not to you.
- **Practical concern:** If you publish an automation tool that collects other families' children's data, COPPA applies to you as the tool operator.
- **FERPA:** Parents have the right to access their own child's education records. Automating that access via parent portal credentials is legally your right. Do not redistribute or share your child's FERPA-protected records.

### Credential storage

```python
# Store a credential (run once)
import keyring
keyring.set_password("school-portal", "parent@email.com", "your-password")

# Retrieve in automation (no plaintext)
password = keyring.get_password("school-portal", "parent@email.com")
```

For Playwright `storageState` files (session tokens):
```bash
chmod 600 ./profiles/school-auth.json
echo "profiles/" >> .gitignore
```

### Responsible scraping checklist

- [ ] Check `robots.txt` before automating any URL
- [ ] No more than 1 request per 2 seconds for informational scraping
- [ ] Run scheduled automation at off-peak hours (2–5 AM local)
- [ ] Set a descriptive `User-Agent` header
- [ ] Daily pulls are sufficient for grades/attendance; don't poll more frequently than needed
- [ ] Never build tools that collect other families' credentials

---

## 9. Memory Architecture

Claude Code agents in this project use a two-layer memory approach:

### Layer 1: CLAUDE.md (stable family context)

Copy `memory/family-template.md` to your project root and fill in your family details:

```markdown
# Family Context
## Children
- Child 1: [name], age [X], grade [Y], [School Name]
  - School portal: [Infinite Campus / Canvas / PowerSchool / etc.]
  - District: [District Name]
  - Activities: [Soccer Tues/Thurs, Piano Fridays]
  - Allergies: [list]
- Child 2: ...

## Key Contacts
- Pediatrician: [Name], portal: [MyChart / etc.]
- Dentist: [Name]
- School office: [phone], [email]

## Automation Preferences
- Notification channel: ntfy topic [your-topic]
- Lunch balance threshold: $[amount]
- Grade check time: daily at [time]

## Credentials
- All credentials stored in macOS Keychain
- Playwright profiles: ./profiles/ (gitignored)
```

### Layer 2: `family-state.json` (dynamic shared state)

Agents read and write this file to share state across runs:

```json
{
  "last_updated": "2026-03-31T18:00:00Z",
  "children": {
    "child1": {
      "name": "Alex",
      "lunch_balance": 23.50,
      "last_grade_check": "2026-03-31",
      "upcoming_assignments": [
        { "subject": "Math", "title": "Chapter 7 HW", "due": "2026-04-02" }
      ],
      "pending_alerts": []
    }
  },
  "appointments": [],
  "monitored_urls": []
}
```

### Layer 3: Agent memory files

Each agent can write to `~/.claude/projects/[project]/memory/` for cross-session recall of preferences, past searches, and learned context (e.g., "family prefers morning camp sessions, tried Galileo 2025 and loved it").

---

## 10. Notification Architecture

All agents use a shared notification pattern. Configure once in `CLAUDE.md`:

```
Primary channel: ntfy.sh topic [family-alerts]
Secondary channel: Pushover (for time-sensitive)
```

**ntfy setup (free, self-hostable):**
```bash
# Send a notification from any agent
curl -d "Alex's lunch balance is low: $8.50" ntfy.sh/your-family-topic
```

**Priority levels:**
- `low` — routine (grade posted, weekly digest ready)
- `normal` — action needed (lunch balance low, assignment due tomorrow)
- `high` — time-sensitive (camp registration opens, earlier doctor slot available)
- `urgent` — immediate action (appointment today, registration closes in 1 hour)

---

## 11. Community Contribution Model

### What the community can contribute

| Type | Location | Examples |
|------|----------|---------|
| Regional agents/skills | `community/regions/[region]/` | Bay Area camp agents, NYC after-school agents |
| School-district integrations | `community/schools/[district]/` | District portal scripts, calendar sources, specific portals |
| Platform skills | `skills/` | New slash commands for specific apps |
| Automation scripts | `automation/` | Lunch account scripts for new platforms |
| Example workflows | `examples/` | Complete end-to-end family automation stories |

### Community directory conventions

**Regions** (`community/regions/<region>/`): Anything specific to a geographic area — local rec department URLs, region-specific camp directories, local library systems, city event calendars.

```
community/regions/bay-area/
├── README.md                        # Bay Area context: useful URLs, portals, resources
├── agents/
│   ├── bay-area-camp-planner.md     # Pre-seeded with Bay Area camp sources
│   └── peninsula-events-finder.md   # San Carlos / Redwood City / Belmont events
├── portals/
│   └── aeries-ca.py                 # Aeries SIS (dominant in CA districts)
└── sources.yaml                     # Bay Area info sources (RSS, API, browser)
```

**Schools** (`community/schools/<district-slug>/`): Anything specific to a school district — portal type, calendar URL, lunch system, PTA newsletter format, specific automation scripts.

```
community/schools/pausd/
├── README.md                        # Portal type, useful URLs, known quirks
├── portal.md                        # How to authenticate and pull data (Aeries/Canvas/etc.)
├── calendar-sources.md              # iCal / RSS feeds for school calendars
└── lunch-account.md                 # Which lunch platform (MySchoolBucks / SchoolPay)
```

### Contribution principles

1. **No PII.** No hardcoded names, addresses, emails, school names specific to a contributor's family.
2. **No credentials.** All credentials via environment variables or system keychain.
3. **Region/school-specific content belongs in `community/`**, not in the root `agents/` or `skills/` directories.
4. **Each contribution needs a `README.md`** explaining what it does, what setup is required, and what portals/APIs it supports.
5. **Safety review required** for any automation that handles children's data or makes financial transactions.

### Community directory structure example

```
community/bay-area/
├── README.md                        # Bay Area-specific context and resources
├── agents/
│   ├── bay-area-camp-planner.md    # Pre-seeded with Bay Area camp sources
│   └── bay-area-events-finder.md   # Peninsula-specific event sources
├── portals/
│   ├── aeries-ca.py                # Aeries SIS (common in CA districts)
│   └── sfusd-portal.py             # San Francisco USD specific
└── resources.md                    # Curated list of Bay Area family resources
```

---

## 12. Marketing and Community Building

### Target communities (in priority order)

| Community | Platform | Size | Angle |
|-----------|----------|------|-------|
| r/ClaudeCode | Reddit | 96k | Technical: "I built reusable Claude Code agents for parenting" |
| r/ClaudeAI | Reddit | 612k | Broader Claude audience, demo focus |
| Anthropic Discord | Discord | 77k | `#skills-and-agents` channel |
| r/Parenting | Reddit | 12M | Non-technical: "I automated my family chores with AI" |
| r/daddit + r/Mommit | Reddit | 5M+ | Personal story angle |
| X / Twitter | X | — | Tag @claude_code, @AnthropicAI, demo video |
| Dev.to | Blog | — | "How I use Claude Code to manage family chores" |
| Hacker News | HN | — | "Show HN: awesome-parenting-skills" |
| SkillsMP | Marketplace | — | Submit individual skills |
| SkillHub | Marketplace | — | Submit to skillhub.club |

### Content strategy

**Launch post (r/ClaudeCode):** Demo video showing the summer-camp-planner agent in action. Show the intake flow, the web research, and the week-by-week calendar output. This is the most visually compelling demo.

**Personal story post (r/Parenting):** "I'm a parent in the Bay Area who built a tool that automatically finds summer camps, monitors school portals, and alerts me when a doctor appointment slot opens. Here's how to set it up." Non-technical, practical, relatable.

**Show HN:** Focus on the architecture — local-first, signed-in Chrome session reuse, COPPA/FERPA considerations. The technical safety angle is interesting to HN.

---

## 13. Name and Repo Decision

**Recommended name:** `awesome-parenting-skills`

- `awesome-parenting` — heavily taken (9+ existing repos)
- `awesome-parenting-skills` — **available**, clearly signals Claude Code skills collection
- Follows the `awesome-*` GitHub convention that signals a curated community list
- The word "skills" connects it to the Claude Code skills ecosystem

**GitHub org options:**
- Personal account: `github.com/[yourname]/awesome-parenting-skills`
- Dedicated org: `github.com/awesome-parenting-skills/awesome-parenting-skills` (allows multiple maintainers, cleaner URLs)

**Recommended:** Create a GitHub org `awesome-parenting-skills` to allow community co-maintainers and avoid tying the project to a personal account.

---

## 14. Roadmap

### v0.1 — Seed (launch)
- [ ] Repo structure and README
- [ ] CONTRIBUTING.md and safety guidelines
- [ ] Generalized `summer-camp-planner` agent
- [ ] Generalized `kids-events-finder` agent
- [ ] Chrome automation guide (`mcp/chrome-automation.md`)
- [ ] Family CLAUDE.md template
- [ ] Bay Area community directory as the first example

### v0.2 — Portal integration
- [ ] `school-portal-watcher` agent
- [ ] Infinite Campus + Canvas automation scripts
- [ ] `homework-tracker` agent
- [ ] Credential management guide

### v0.3 — Scheduling automation
- [ ] `appointment-scheduler` agent
- [ ] MyChart slot monitoring script
- [ ] Lunch balance monitoring + top-up script
- [ ] `monitor-registration` skill (changedetection.io integration)

### v0.4 — Media and content
- [ ] `youtube-channel-manager` agent
- [ ] Google Classroom homework tracker
- [ ] PTA newsletter email parser

### v0.5 — Community
- [ ] Second regional community directory (Seattle or NYC)
- [ ] Skill submissions to marketplaces (SkillsMP, SkillHub)
- [ ] Launch posts across communities

---

## 15. Key External Resources

| Resource | URL | Purpose |
|----------|-----|---------|
| Anthropic official skills | github.com/anthropics/skills | Official skill examples and standards |
| hesreallyhim/awesome-claude-code | github.com | Cross-reference: curated Claude skills list |
| changedetection.io | github.com/dgtlmoon/changedetection.io | Page monitoring for registration openings |
| ntfy.sh | ntfy.sh | Push notifications for parent alerts |
| Playwright MCP | github.com/microsoft/playwright-mcp | Browser automation MCP |
| mcp-chrome | github.com/hangwin/mcp-chrome | Real Chrome session exposure via MCP |
| google_workspace_mcp | github.com/taylorwilsdon/google_workspace_mcp | Gmail + Calendar + Drive |
| notion-mcp-server | github.com/makenotion/notion-mcp-server | Family wiki + task management |
| canvasapi | github.com/ucfopen/canvasapi | Canvas LMS parent/observer access |
| Infinite-Campus-API | github.com/gilesgc/Infinite-Campus-API | Infinite Campus grades + schedule |
| PyPowerSchool | github.com/dougpenny/PyPowerSchool | PowerSchool parent data |
| Eventbrite API | eventbrite.com/platform/api | Local family event discovery |
| SchoolDigger API | developer.schooldigger.com | Public school data and boundaries |
| Skyvern | github.com/Skyvern-AI/skyvern | LLM + vision browser automation |
