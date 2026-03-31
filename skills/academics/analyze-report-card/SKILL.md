# Skill: analyze-report-card

> **Status: PLACEHOLDER** — Not yet implemented. Contributions welcome.

Analyze a child's school year-end report card or progress report and generate actionable insights for parents: strengths, growth areas, summer prep plan, and talking points for back-to-school.

## Usage

```
/analyze-report-card [--file <path-to-pdf-or-image>] [--child <name>] [--grade <grade>]
```

## Planned capabilities

- Ingest report card as PDF, image scan, or structured text
- Extract grades, attendance, teacher comments, and standardized test scores
- Identify patterns: consistent strengths, persistent struggles, social/behavioral notes
- Compare against prior report cards if available (trend analysis)
- Generate a parent action plan: summer tutoring targets, enrichment opportunities, conversation starters with the child
- Map weaknesses to specific local resources (tutors, enrichment programs, library programs)
- Output a family-facing summary + a child-facing version (age-appropriate language)

## Arguments (planned)

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--file` | yes* | — | Path to report card PDF or image file |
| `--child` | no | — | Child name (loads profile from `family-state.json`) |
| `--grade` | no | — | Grade level (inferred from report if not given) |
| `--prior` | no | — | Path to prior year report card for trend comparison |
| `--output` | no | full | `full` = complete report; `summary` = 1-page; `action-plan` = next steps only |
| `--local-resources` | no | — | Path to `sources.yaml` for mapping gaps to local programs |

*If `--file` is omitted, skill will prompt for upload or check clipboard for a screenshot.

## Design notes

### Ingestion pipeline
1. **PDF**: Read with Claude's file reading capability (up to 20 pages). Extract text via pdf-to-text, fall back to vision if text layer is absent (scanned report cards).
2. **Image/photo**: Use Claude vision to extract grades, scores, and comments from a photo of a paper report card.
3. **Structured text**: Accept pasted text directly.

### Extraction schema
```json
{
  "child": "Emma",
  "grade": "3rd",
  "school_year": "2025-2026",
  "school": "Arundel Elementary",
  "subjects": [
    {
      "name": "Mathematics",
      "grade": "3",
      "grade_label": "Approaching Standard",
      "teacher_comment": "Emma struggles with word problems but shows strong number sense.",
      "standards": [
        {"code": "3.OA.1", "label": "Multiplication concepts", "score": "2/4"}
      ]
    }
  ],
  "attendance": {"days_present": 174, "days_absent": 6, "tardies": 2},
  "social_emotional": {"grade": "3", "notes": "Works well in groups, sometimes needs reminders to stay on task"},
  "teacher_overall_comment": "...",
  "standardized_tests": [{"name": "CAASPP ELA", "score": "Standard Met", "percentile": 68}]
}
```

### Analysis dimensions

| Dimension | What to surface |
|-----------|----------------|
| Academic strengths | Subjects/standards consistently at or above grade level |
| Growth areas | Subjects/standards below grade level or declining trend |
| Attendance pattern | Chronic absenteeism flag (>10% = 18+ days), tardy pattern |
| Social/emotional | Behavioral notes, collaboration, self-regulation |
| Teacher signal words | Flag: "concerns", "struggles", "inconsistent", "significant progress" |
| Trend vs prior year | Improving / stable / declining per subject |

### Action plan output structure

```markdown
## Summer Action Plan — Emma (Grade 3 → 4)

### Focus areas
1. **Math word problems** (3.OA) — 2 weeks of targeted practice
   - Resource: Khan Academy Kids (free) — "3rd Grade Word Problems" unit
   - Local: Arundel Summer Math Packets (check school website Aug 1)
   - Consider: Mathnasium San Carlos (anc.apm.activecommunities.com/sancarlos)

### Keep building
- Reading fluency — continue chapter books at current level
- Art / Creative projects — strong scores, enroll in SCCT summer session

### Conversation starters (for Emma)
- "What was your favorite project this year?"
- "Which part of math felt tricky? Let's try it together this summer."

### Back-to-school prep
- Email new teacher in August: flag math word problems, ask about reading groups
- Schedule PAMF annual checkup before school starts (vision check especially)
```

### Local resource mapping
When `--local-resources` points to a `sources.yaml`, map identified gaps to specific local programs:
- Math/reading tutoring → enrichment vendors in SCSD after-school list
- STEM gap → ActiveNet summer classes, ChatterBlock enrichment listings
- Social skills → SCCT theater programs, team sports (AYSO)

## Implementation checklist

- [ ] PDF/image ingestion with Claude vision fallback
- [ ] Structured extraction with subject-level grades and teacher comments
- [ ] CAASPP / standardized test score parsing (California-specific)
- [ ] Prior year comparison (if `--prior` provided)
- [ ] Action plan generation with local resource mapping
- [ ] Child-facing summary in age-appropriate language
- [ ] Save extracted data to `family-state.json > report_cards[year]`
- [ ] Optional: email action plan to parent via `/send-email`

## Privacy notes

- Report card files contain sensitive FERPA-protected student data — never upload to external services
- All analysis runs locally via Claude API; no data is stored by the API beyond the session
- Extracted JSON saved to `family-state.json` is stored locally only
- Redact student ID numbers and teacher full names from any output shared externally
