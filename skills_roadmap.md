# Skills Roadmap

Proposed skills not yet implemented, plus the quality framework that applies to all skills across this repo.

---

## Skill status lifecycle

Every skill — existing or proposed — carries one of these statuses:

| Status | Meaning |
|--------|---------|
| `idea` | Proposed in this roadmap; no SKILL.md yet |
| `draft` | SKILL.md written; not yet tested in practice |
| `implemented` | Works for at least one parent in real use; no formal evals yet |
| `verified` | Passes evals, privacy audit clean, confirmed reliable by multiple parents |
| `deprecated` | Superseded by a better skill; do not use for new setups |
| `retired` | Broken or unsupported (upstream portal changed, API removed, etc.) |

The normal progression is `idea → draft → implemented → verified`. A skill can move backward (e.g., `verified → retired`) if the underlying service breaks.

---

## Quality checklist — requirements to reach `verified`

A skill earns `verified` status when all of the following are true:

- [ ] **Privacy audit passed** — `/privacy-audit` finds no Tier 1 issues (no API keys, PII, child-identifiable data in committed files)
- [ ] **Smoke test documented** — at least one end-to-end test case written and passing, in `evals/<category>/<name>/`
- [ ] **Happy path eval** — automated eval covers the primary use case with expected output assertions
- [ ] **Error handling** — skill gracefully handles at least: missing config, portal login failure, empty results
- [ ] **Confirmed by 2+ parents** — at least two people have run it successfully in their own setup (note in PR or SKILL.md)
- [ ] **Known limitations documented** — edge cases, unsupported portals, or platform quirks noted in SKILL.md

Skills that are `implemented` but not yet `verified` are usable — they just haven't been formally validated. Treat their output with a bit more skepticism and run `/factuality-checker` on any critical output before acting on it.

---

## Tracking quality per skill

Each `SKILL.md` should include a frontmatter block:

```yaml
---
status: draft | implemented | verified | deprecated | retired
last_verified: 2026-03-31        # date verified or last confirmed working
verified_by: github-username     # who verified it
eval_path: evals/media/youtube-kids-audit/   # path to eval suite, if any
known_issues:
  - MySchoolBucks login breaks if 2FA is enabled
---
```

This makes status machine-readable and lets the community see at a glance what's reliable.

---

## Proposed skills

### Health & Medical

| Command | Description | Priority | Status |
|---------|-------------|----------|--------|
| `/track-vaccines` | Track immunization records, flag upcoming boosters, generate school-required health forms | High | `idea` |
| `/book-appointment` | Book pediatrician / dentist appointments via browser automation, with preferred time slots | High | `idea` |
| `/health-insurance-claim` | Parse EOB emails, flag unpaid claims, draft dispute letters | Medium | `idea` |

---

### School & Communication

| Command | Description | Priority | Status |
|---------|-------------|----------|--------|
| `/draft-teacher-email` | Draft emails to teachers given a plain-English situation ("Emma struggled with the last math test, ask for extra help") | High | `idea` |
| `/permission-slip-tracker` | Monitor school emails for permission slips, flag unsigned ones, send reminders before due date | High | `idea` |
| `/college-app-tracker` | Track deadlines, requirements, essay prompts, and status across schools — for high schoolers | Medium | `idea` |
| `/iep-meeting-prep` | Summarize recent progress notes and draft questions before an IEP/504 meeting | Medium | `idea` |

---

### Scheduling & Coordination

| Command | Description | Priority | Status |
|---------|-------------|----------|--------|
| `/family-calendar` | Aggregate school calendars, sports schedules, and activity rosters into one unified weekly view | High | `idea` |
| `/carpool-coordinator` | Manage a recurring carpool rotation with other families, send day-of reminders | Medium | `idea` |
| `/playdate-scheduler` | Draft playdate proposals, track RSVPs, suggest activities based on kids' ages | Low | `idea` |

---

### Meals & Nutrition

| Command | Description | Priority | Status |
|---------|-------------|----------|--------|
| `/meal-planner` | Generate a weekly kid-friendly meal plan given dietary restrictions, output a grocery list | High | `idea` |
| `/check-school-menu` | Scrape this week's cafeteria menu, flag days with known allergens or disliked items | Medium | `idea` |

---

### Finance & Allowance

| Command | Description | Priority | Status |
|---------|-------------|----------|--------|
| `/allowance-tracker` | Track chore completion, calculate allowance owed, log payments | Medium | `idea` |
| `/college-savings-check` | Pull 529 balance, project growth vs. target, suggest monthly contribution adjustment | Low | `idea` |

---

### Safety & Digital Wellbeing

| Command | Description | Priority | Status |
|---------|-------------|----------|--------|
| `/screen-time-report` | Aggregate device usage across platforms (iOS Screen Time, Android Digital Wellbeing), weekly summary | High | `idea` |
| `/social-media-audit` | Like `/youtube-kids-audit` but for Instagram/TikTok — flag follows, content themes, time spent | Medium | `idea` |
| `/online-safety-check` | Scan for publicly visible personal info about your child (school, location, photos indexed online) | Medium | `idea` |

---

### Community & Volunteering

| Command | Description | Priority | Status |
|---------|-------------|----------|--------|
| `/volunteer-signup` | Monitor school/PTA volunteer slots, sign up for preferred ones when they open | Medium | `idea` |
| `/pta-digest` | Summarize PTA meeting notes and newsletters into 5 bullet points with action items | Medium | `idea` |
| `/fundraiser-tracker` | Track active school fundraisers, deadlines, and amounts raised vs. goal | Low | `idea` |

---

### Sports

| Command | Description | Priority | Status |
|---------|-------------|----------|--------|
| `/sports-registration` | Monitor league registration windows (AYSO, Little League, rec basketball) and auto-register when they open | High | `idea` |
| `/game-schedule` | Aggregate game and practice schedules across multiple kids and sports into one calendar view | High | `idea` |
| `/snack-duty` | Track team snack rotation, send reminders to the assigned family, suggest age-appropriate snack ideas | High | `idea` |
| `/tryout-tracker` | Track tryout dates, requirements, what to bring, and follow-up status across competitive teams | Medium | `idea` |
| `/sports-budget` | Track per-sport costs (registration fees, gear, travel, camps) across the season, flag overruns | Medium | `idea` |
| `/gear-checklist` | Maintain a per-sport gear checklist, flag missing or outgrown items before the season starts | Medium | `idea` |
| `/athletic-eligibility` | Track GPA and attendance thresholds required for school sports eligibility, alert if at risk | Medium | `idea` |
| `/league-standings` | Pull current standings and upcoming schedules from league sites (AYSO, MaxPreps, local rec portals) | Low | `idea` |
| `/sports-photos` | Find and download team/game photos from league sites, school athletics pages, or shared parent albums | Low | `idea` |
| `/carpool-to-game` | Coordinate ride-sharing to games and practices among team families, send day-of reminders | Low | `idea` |

---

### Knowledge Base (community-contributed)

These aren't automation skills — they're structured parent expertise, encoded as reusable guides that other parents can read, run, or extend.

| Command | Description | Priority | Status |
|---------|-------------|----------|--------|
| `/private-school-guide` | Playbook for private school research, applications, and financial aid — contributed by parents who've done it | High | `idea` |
| `/iep-guide` | Parent-written guide to navigating IEP evaluations, annual meetings, and appeals | High | `idea` |
| `/new-parent-checklist` | Onboarding checklist for parents new to a school district — portals, key contacts, calendar deadlines | Medium | `idea` |

---

## Contributing a skill from this roadmap

1. Pick a skill and create `skills/<category>/<name>/SKILL.md` with the status frontmatter block above
2. Set `status: draft` initially
3. Run `/privacy-audit --path skills/<category>/<name>/ --mode report`
4. Open a PR and reference this roadmap item in the description
5. Once merged, move the row out of this file and into the skill tables in `playbook.md`
6. Work toward `verified` by adding evals under `evals/<category>/<name>/` and getting a second parent to confirm it works
