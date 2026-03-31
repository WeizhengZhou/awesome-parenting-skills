# Skill: privacy-audit

> **Status: PLACEHOLDER** — Not yet implemented. Contributions welcome.

Scan skill files, agent configs, source YAML, and related documents for personally identifiable information (PII) and sensitive trust data before a contributor submits them to the shared repository.

**Primary use case:** Pre-submission gate for the `awesome-parenting-skills` community repo. Run this before opening a PR to ensure no personal data leaks into public skills.

## Usage

```
/privacy-audit [--path <file-or-dir>] [--mode scan|redact|report] [--strict]
```

## Planned capabilities

- Scan skill files (SKILL.md, YAML configs, Python scripts, shell hooks) for PII patterns
- Detect: real names, email addresses, phone numbers, street addresses, school names tied to real children, API keys/tokens, passwords, account numbers, session cookies
- Detect: hardcoded URLs pointing to personal portals (PowerSchool, Infinite Campus, Canvas observer tokens)
- Offer `--redact` mode: auto-replace detected PII with safe placeholders (`[REDACTED_EMAIL]`, `[YOUR_CHILD_NAME]`, `[YOUR_SCHOOL_DISTRICT]`)
- Generate a pre-submission report: clean / needs review / blocked (has keys or child-identifiable data)
- COPPA check: flag any content that collects or references data about children under 13 without appropriate safeguards

## Arguments (planned)

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--path` | no | `.` (cwd) | File or directory to scan |
| `--mode` | no | scan | `scan` = report only; `redact` = auto-replace PII; `report` = generate PR-ready checklist |
| `--strict` | no | false | Fail on any PII hit (for CI gate use) |
| `--exclude` | no | — | Glob patterns to skip (e.g. `**/family-state.json`) |
| `--child-names` | no | — | Comma-separated known child names to flag (loaded from `family-state.json` if available) |

## PII detection categories

### Tier 1 — Block (must fix before submission)
| Category | Examples | Pattern |
|----------|----------|---------|
| API keys / tokens | `am_us_0c700c1f...`, `sk-ant-...`, `Bearer eyJ...` | Regex: `(am_us_|sk-ant-|Bearer\s)[A-Za-z0-9_\-]{20,}` |
| Passwords | `password: mysecret`, `PASSWORD=abc123` | Regex: `(?i)(password|passwd|secret|token)\s*[=:]\s*\S+` |
| OAuth tokens / cookies | `access_token=...`, `session=...` | Regex: common cookie/token patterns |
| Private keys | `-----BEGIN RSA PRIVATE KEY-----` | Regex: PEM headers |
| Canvas observer tokens | Student pairing codes | Regex: `pairing_code\s*[=:]\s*\w+` |

### Tier 2 — Review (flag for contributor decision)
| Category | Examples | Notes |
|----------|----------|-------|
| Email addresses | `user@example.com` | Allow `example@`, `your@`, placeholder patterns |
| Phone numbers | `(650) 555-1234` | Flag 10-digit US numbers |
| Street addresses | `301 Industrial Rd, San Carlos` | Flag real addresses (allow well-known public venues) |
| Child full names | `Emma Zhang`, `Liam Chen` | Cross-reference `--child-names` list |
| School portal URLs with IDs | `scsdk8.powerschool.com/guardian/home?studentid=12345` | Flag URLs with student IDs |
| Real school names tied to real kids | "My daughter at Arundel Elementary" | NLP heuristic: `[child name] at [school name]` |

### Tier 3 — COPPA / FERPA flags (informational)
| Issue | What to check |
|-------|---------------|
| Collecting children's data without consent notice | Any form-fill automation that submits child data to third-party services |
| FERPA: storing student records outside school systems | `family-state.json` fields containing grades or attendance |
| Screen time / behavioral data | YouTube watch history, app usage — flag if saved to a shared location |

## Redaction placeholders

When `--mode redact`, replace detected values with:

| PII type | Placeholder |
|----------|-------------|
| Email | `your-email@example.com` |
| Child name | `[CHILD_NAME]` |
| Phone | `(555) 555-5555` |
| Address | `[YOUR_ADDRESS]` |
| API key | `[YOUR_API_KEY]` |
| School name (personal) | `[YOUR_SCHOOL]` |
| Student ID | `[STUDENT_ID]` |
| Portal URL with ID | `[YOUR_PORTAL_URL]` |

## Output: PR-ready report

```markdown
## Privacy Audit Report
**Path:** skills/order_food_skill/SKILL.md
**Date:** 2026-03-31
**Result:** ✅ CLEAN — safe to submit

### Checks passed
- [x] No API keys or tokens detected
- [x] No email addresses (only example@... placeholders)
- [x] No child names detected
- [x] No hardcoded addresses
- [x] No student portal URLs with IDs

---

**Path:** my_custom_skill/SKILL.md
**Result:** 🚫 BLOCKED — fix before submitting

### Issues found
| Line | Category | Value | Action |
|------|----------|-------|--------|
| 12 | Tier 1 — API key | `am_us_0c700c1f...` | Remove or replace with `[YOUR_API_KEY]` |
| 34 | Tier 2 — Child name | `Emma` | Replace with `[CHILD_NAME]` |
| 67 | Tier 2 — Email | `user@example.com` | Replace with `your-email@example.com` |
```

## CI / pre-commit integration (planned)

Add to `.github/workflows/privacy-check.yml`:
```yaml
- name: Privacy audit
  run: claude -p "/privacy-audit --path . --mode scan --strict"
```

Or as a local pre-commit hook:
```bash
#!/bin/bash
# .git/hooks/pre-commit
claude -p "/privacy-audit --path $(git diff --cached --name-only | tr '\n' ' ') --mode scan --strict"
```

## Implementation checklist

- [ ] Regex-based scanner for Tier 1 patterns (API keys, passwords, tokens)
- [ ] NLP heuristic for Tier 2 (child names + institution patterns)
- [ ] Load child names from `family-state.json` if present (for personal installs)
- [ ] `--redact` mode: in-place file edit with placeholder substitution
- [ ] Per-file status: clean / review / blocked
- [ ] PR-ready markdown report generation
- [ ] `--strict` exit code 1 on any Tier 1 hit (CI gate)
- [ ] GitHub Actions workflow template
- [ ] Pre-commit hook template

## Notes for contributors

Before opening a PR to `awesome-parenting-skills`, run:
```
/privacy-audit --path your-skill-directory/ --mode report
```

All Tier 1 issues must be resolved. Tier 2 items require a brief explanation in your PR description if intentionally left as real values (e.g., a well-known public library URL is fine; your child's name is not).
