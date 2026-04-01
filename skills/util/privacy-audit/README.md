# privacy-audit

Scans skill files, configs, and docs for PII and sensitive data before they reach the public repo.

## Pre-commit hook (installed automatically)

This repo ships with a git pre-commit hook that runs a privacy scan on every `git commit`. It blocks commits containing:

| Pattern | Example | Action |
|---------|---------|--------|
| API keys / tokens | `am_us_...`, `sk-ant-...` | Blocked |
| Personal email addresses | `name[at]gmail.com` (real address) | Blocked |
| Real AgentMail addresses | `yourname@agentmail.to` | Blocked |
| Absolute user paths | `/Users/yourname/...` | Blocked |

### Install the hook (one-time, after cloning)

```bash
cat > "$PWD/.git/hooks/pre-commit" << 'EOF'
#!/bin/bash
STAGED=$(git diff --cached --name-only 2>/dev/null)
if [ -z "$STAGED" ]; then exit 0; fi
echo "[pre-commit] Running privacy audit..."
FAIL=0
while IFS= read -r file; do
  [ -f "$file" ] || continue
  grep -qE '(am_us_|sk-ant-)[A-Za-z0-9_\-]{20,}' "$file" && echo "[BLOCKED] $file — API key" && FAIL=1
  grep -qP '(?<!your-)\b[a-z]{2,12}@agentmail\.to\b' "$file" && echo "[BLOCKED] $file — agentmail address" && FAIL=1
  [[ "$file" != "CLAUDE.md" ]] && grep -qP '/Users/(?!<)[a-zA-Z][a-zA-Z0-9_-]+/' "$file" && echo "[BLOCKED] $file — user path" && FAIL=1
done <<< "$STAGED"
[ "$FAIL" -eq 1 ] && echo "Fix issues above before committing." && exit 1
echo "[pre-commit] Passed." && exit 0
EOF
chmod +x "$PWD/.git/hooks/pre-commit"
```

### Manual scan

```bash
# Scan everything
claude -p "/privacy-audit --path . --mode scan"

# Auto-redact PII with placeholders
claude -p "/privacy-audit --path . --mode redact"

# Scan a specific skill before submitting a PR
claude -p "/privacy-audit --path skills/your-category/your-skill/ --mode report"
```

## Placeholders to use

| PII type | Use this instead |
|----------|-----------------|
| AgentMail inbox | `your-agent@agentmail.to` |
| Personal email | `your-email@example.com` |
| API key | `[YOUR_API_KEY]` |
| File path | `/path/to/your/project/` |
| Child name | `[CHILD_NAME]` |
| School name | `[YOUR_SCHOOL]` |

## Full skill docs

See `SKILL.md` for the complete implementation spec (Tier 1/2/3 detection, `--redact` mode, CI integration).
