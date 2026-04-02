# awesome-parenting-skills

Claude Code skills and agents for automating the tedious parts of parenting — school portals, lunch accounts, event finding, registration watching, and more. Everything runs locally on your machine.

> **Status:** Early-stage, single-author project. 14 working skills, Bay Area community data. Contributions welcome — see [Contributing](#contributing).

---

## Why this exists

Between school portals, homework check-ins, camp registrations, lunch account top-ups, activity signups, and the weekly flood of school newsletters, a real chunk of parenting time goes to logistics. Not quality time with your kids — just chores.

Claude Code can automate most of it. This repo is a shared collection of skills that make that practical.

**What makes this different from yet another parenting app:**

- **Agent skills, not apps** — these aren't web dashboards or browser extensions. They're Claude Code skills: composable, scriptable, and able to reason and chain together. You describe what you need; the agent figures out how.
- **Actually does the work** — skills submit forms, send emails, monitor pages, and book appointments. They escalate to you when a human decision is needed, not for every step.
- **Your data stays local** — children's data never leaves your machine. Skills run inside Claude Code locally. `user_docs/` and `.env` are gitignored. The repo is public; your family details are not.
- **Safety-gated** — agents acting on your behalf need guardrails. Confirmation prompts before financial transactions or outbound messages. Privacy audit on every commit. Factuality checker for critical decisions.
- **Community-contributed** — school portal configs, local event sources, and district setups are shared by parents in the same cities and districts. You don't have to figure out where your city posts rec league signups — someone already did.

---

## Skills

Skills are slash commands you run inside Claude Code. You can also just describe what you need in plain English and Claude Code picks the right skill.

### Working (`implemented`)

| Category | Command | What it does |
|----------|---------|--------------|
| Academics | `/check-grades` | Pull grades, attendance, assignments from school portals |
| Academics | `/weekly-digest` | Monday morning family summary — grades, events, lunch balances, action items |
| Academics | `/co-read-prepare` | Parent briefing + discussion questions for a book or movie |
| Academics | `/find-school-calendar` | Find and save a school's academic calendar |
| Afterschools | `/weekend-fun-events` | Find weekend events by child age, interests, and location |
| Afterschools | `/monitor-registration` | Watch a registration page, alert when it opens |
| Media | `/youtube-kids-audit` | Audit a child's YouTube history, classify channels, suggest actions |
| Meals | `/meal-planner` | Weekly meal plan + grocery list tailored to kids |
| Shopping | `/top-up-lunch` | Check school lunch balance, top up if below threshold |
| Email | `/draft-teacher-email` | Draft a polished email to a teacher |
| Email | `/send-email` | Send email from an AgentMail inbox |
| Util | `/info-gather` | Pull info from RSS, APIs, and web sources using a `sources.yaml` config |
| Util | `/browser-automate` | Automate Chrome — school portals, registration forms, appointments |
| Util | `/mac-cron-job` | Create and manage scheduled tasks via macOS launchd |

### Draft (written, not yet tested)

| Command | What it does |
|---------|--------------|
| `/analyze-report-card` | Extract grades from a PDF/photo report card, generate action plan |
| `/order-food` | Automate food orders with allergen checks and parent confirmation |
| `/privacy-audit` | Scan files for PII and API keys before committing |
| `/agentmail-skill` | AgentMail inbox management — send, read, reply, scan |

### Agents

Agents handle multi-step tasks that go beyond a single skill.

| Agent | What it does |
|-------|--------------|
| `summer-camp-planner` | Research, compare, and schedule summer camps for a given city and child |
| `kids-events-finder` | Search for local family events by city, age range, and time window |
| `factuality-checker` | Verify claims (prices, dates, policies) before you act on them |

---

## Quick start

```bash
# 1. Clone
git clone https://github.com/anthropics/awesome-parenting-skills
cd awesome-parenting-skills

# 2. Symlink skills into Claude Code
for skill in skills/**/*; do
  name=$(basename $skill)
  ln -sf "$PWD/$skill" ~/.claude/skills/$name
done

# 3. Copy templates for personal config (gitignored — stays on your machine)
cp -r user_docs_template/ user_docs/
cp .env_template .env
# Edit .env with your API keys (AgentMail, etc.)
# Edit user_docs/ with your family details

# 4. Open Claude Code
claude
```

Then just talk to it:

> "Check my daughter's grades and send me a summary."
>
> "Find something fun to do with a 7-year-old this weekend in San Carlos."
>
> "Set up a Monday morning reminder to top up the lunch account if it drops below $15."

---

## How it works

**Skills are markdown files.** Each skill is a `SKILL.md` that Claude Code reads and follows. No compiled code, no build step — edit a skill and the change is live immediately.

**Personal data stays local.** Your family details live in `user_docs/` (gitignored) and `.env` (gitignored). Skills run inside Claude Code on your machine. Nothing is uploaded unless you explicitly choose to (e.g., sending an email).

**Community data is shared.** School portal configs, event source lists, and region guides live in `community/` and are safe to commit — they contain no personal data, just URLs and structure.

**Scheduling.** Skills become most useful on autopilot. The `/mac-cron-job` skill sets up macOS `launchd` jobs to run skills on a schedule (e.g., Monday 7am grade summary, daily lunch balance check).

---

## Community data

Shared configs that make setup faster for parents in the same area. Currently:

| Region / District | Status |
|-------------------|--------|
| Bay Area (general) | Event sources mapped |
| San Carlos, CA | Local sources + presets (`events_this_weekend`, `summer_camps`, `sports_registration`, etc.) |
| San Carlos School District (SCSD) | Portal config (PowerSchool, Google Classroom) |
| Carlmont High School (SUHSD) | Portal config (Infinite Campus, Canvas) |
| Everything else | Not started |

Adding your city or school district takes ~20 minutes and helps every parent who comes after you. See [playbook.md](playbook.md) for how.

---

## Project structure

```
skills/<category>/<name>/SKILL.md   # skill source (symlinked to ~/.claude/skills/)
agents/<name>.md                    # agent definitions
community/regions/                  # event sources and local guides by city
community/schools/                  # school portal configs by district
scripts/                            # shared Python utilities (calendar, email, cron)
user_docs_template/                 # templates — copy to user_docs/ on setup
user_docs/                          # your personal config (gitignored)
.env_template                       # copy to .env for API keys (gitignored)
```

See [playbook.md](playbook.md) for the full reference and [design_doc.md](design_doc.md) for architecture decisions.

---

## Vision

This started as one parent's automation setup. The goal is to grow it into a shared collection that any parent using Claude Code can benefit from — especially the community data layer, where mapping one school district or city saves every other parent in that area from doing the same work.

Principles guiding that direction:

- **Local-first.** Children's data never leaves your machine unless you explicitly send it somewhere. No accounts, no vendor servers, no data harvesting.
- **Actually useful automation.** Skills that submit forms, send emails, and monitor pages — not just dashboards. Escalate to the parent only when a human decision is needed.
- **Safety-gated.** Confirmation prompts before financial transactions or outbound messages. Privacy audit on every commit. Factuality checker for critical decisions.
- **Low barrier to contribute.** Adding a school district is a YAML file. Adding a skill is a markdown file. No build system, no framework.

---

## Contributing

### Add a skill

1. Create `skills/<category>/<name>/SKILL.md`
2. Run `/privacy-audit` — fix all Tier 1 issues (API keys, PII)
3. Replace personal data with placeholders
4. Open a PR

### Add a city or school district

1. Copy `community/regions/bay-area/san-carlos/` as a template
2. Update `sources.yaml` with local event sources
3. Add school districts under `community/schools/<district>/` with a `portals.yaml`
4. Open a PR

See [playbook.md](playbook.md) for details.

---

## License

MIT
