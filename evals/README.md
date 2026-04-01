# Evals

Automated evaluation suites for Claude Code skills in this repository.

## Structure

```
evals/
├── README.md                  ← this file
└── media/
    └── youtube-kids-audit/
        └── analyze-kids-content/
            ├── README.md      ← eval spec and how to run
            ├── rubric.md      ← scoring rubric (R1–R8)
            ├── run_eval.py    ← eval runner script
            └── fixtures/
                ├── profiles/  ← synthetic child profiles (.md)
                └── histories/ ← synthetic watch histories (.json)
```

## Running evals

From the repo root:

```bash
# Run the full analyze-kids-content eval suite
python3 evals/media/youtube-kids-audit/analyze-kids-content/run_eval.py

# Run a single test case
python3 evals/media/youtube-kids-audit/analyze-kids-content/run_eval.py --tc tc001

# Dry run (show prompt, skip API call)
python3 evals/media/youtube-kids-audit/analyze-kids-content/run_eval.py --dry-run
```

## Privacy

All fixture data is synthetic. No real child names, emails, API keys, or personal
information appear anywhere in this directory. Channel names are real (public YouTube
channels) but no personal accounts are referenced.
