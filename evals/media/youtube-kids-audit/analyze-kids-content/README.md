# Eval: analyze-kids-content

Evaluation suite for the `analyze-kids-content` sub-skill of `/youtube-kids-audit`.

## What this skill does

Given a child profile (age, academic level, interests, account type) and a scraped
YouTube watch history, the skill produces a Strategic Educational Report that:

1. Audits existing content and flags "Educational Junk Food"
2. Classifies all content as KEEP / REMOVE / ADD
3. Produces a curriculum channel table aligned to 5 educational goals
4. Suggests a weekly implementation schedule
5. Lists 3-5 immediate parent action items

## Test cases

| ID     | Description                          | Key challenges                                   |
|--------|--------------------------------------|--------------------------------------------------|
| TC-001 | Advanced 7yo, mixed account          | Adult filtering, junk food for advanced learner  |
| TC-002 | Average 5yo, dedicated account       | Age-appropriate calibration (no false junk food) |
| TC-003 | Struggling 9yo, mixed account        | Scaffolded recs, adult filtering, visual learner |

## Rubric dimensions

| ID | Name                        | Weight |
|----|-----------------------------|--------|
| R1 | Adult Content Filtering     | 3      |
| R2 | Junk Food Detection         | 3      |
| R3 | Math Level Calibration      | 3      |
| R4 | Five-Goal Coverage          | 2      |
| R5 | Output Structure            | 2      |
| R6 | Recommendation Specificity  | 2      |
| R7 | Age Calibration Contrast    | 2      |
| R8 | Trojan Horse Recommendation | 1      |

Maximum raw score per TC: 18 points (sum of weights).
See `rubric.md` for full pass/fail criteria.

## How to run

Prerequisites:
- `claude` CLI installed and authenticated (`claude --version`)
- Python 3.9+
- Run from repo root

```bash
# Full suite
python3 evals/media/youtube-kids-audit/analyze-kids-content/run_eval.py

# Single test case
python3 evals/media/youtube-kids-audit/analyze-kids-content/run_eval.py --tc tc001

# Save outputs to file
python3 evals/media/youtube-kids-audit/analyze-kids-content/run_eval.py --output results.json

# Dry run (build and print prompt only, skip claude calls)
python3 evals/media/youtube-kids-audit/analyze-kids-content/run_eval.py --dry-run
```

## Scoring interpretation

| Score | Interpretation                                         |
|-------|--------------------------------------------------------|
| 100%  | All rubric dimensions pass across all TCs              |
| 85%+  | Production-ready; minor gaps in low-weight dimensions  |
| 70-84% | Needs improvement; likely R2 or R3 calibration issues |
| <70%  | Skill is miscalibrated; review prompt or model choice  |

## Fixture files

All fixtures are synthetic. Profile names are placeholder names (Alex, Sam, Jordan).
Channel names are real public YouTube channels — no personal data.

```
fixtures/
├── profiles/
│   ├── tc001_advanced_7yo_mixed.md
│   ├── tc002_average_5yo_dedicated.md
│   └── tc003_struggling_9yo_mixed.md
└── histories/
    ├── tc001_history.json   (30 videos)
    ├── tc002_history.json   (32 videos)
    └── tc003_history.json   (30 videos)
```
