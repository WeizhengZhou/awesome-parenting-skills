# awesome-parenting-skills — Claude Code Instructions

## Privacy audit gate (MANDATORY)

**Before every `git commit` or `git push`, run the privacy audit on all staged/changed files.**

This is not optional. The repo is public. A single leaked API key or personal email address requires a force-push and git history rewrite to fix.

### How to run

```bash
# Audit all staged files before committing
/privacy-audit --path . --mode scan --strict

# If any Tier 1 issues are found (API keys, tokens, passwords, personal emails):
# → Fix them first, then re-stage and retry the commit
# → Do NOT use --no-verify or bypass this check
```

### What it catches

| Tier | Examples | Action |
|------|---------|--------|
| Tier 1 — Block | API keys (`am_us_`, `sk-ant-`), passwords, personal email addresses, student IDs | Must fix before commit |
| Tier 2 — Review | Child names, street addresses, school portal URLs with IDs | Confirm intentional before commit |
| Tier 3 — Info | COPPA/FERPA considerations | Informational only |

### Common PII to watch for in this repo

- AgentMail addresses (e.g. `name@agentmail.to`) → use `your-agent@agentmail.to`
- Personal Gmail/email addresses → use `your-email@example.com`
- File paths containing usernames (e.g. `/Users/yourname/`) → use `/path/to/your/`
- API keys in any file other than `.env` (which is gitignored)
- Child names, school names tied to real children
- Student portal IDs or session tokens

### Hook setup (automate this check)

To enforce the audit automatically on every commit, add a pre-commit hook:

```bash
# Run once to install the hook
cat > "$PWD/.git/hooks/pre-commit" << 'EOF'
#!/bin/bash
echo "Running privacy audit on staged files..."
STAGED=$(git diff --cached --name-only)
if [ -z "$STAGED" ]; then exit 0; fi
claude -p "/privacy-audit --path . --mode scan --strict" || {
  echo "Privacy audit failed. Fix Tier 1 issues before committing."
  exit 1
}
EOF
chmod +x .git/hooks/pre-commit
```

---

## Project overview

This is a public repo of reusable Claude Code skills, agents, and community data for parenting workflows. All files here must be safe for public viewing.

## Structure

```
skills/<category>/<name>/SKILL.md   ← skill source (symlinked to ~/.claude/skills/)
agents/<name>.md                    ← agent definitions
community/                          ← curated data safe for public (no personal data)
scripts/                            ← shared Python utilities, organized by category
scripts/calendar/gcal.py            ← ICS calendar fetcher and markdown/HTML renderer
scripts/email/agentmail.py          ← AgentMail API wrapper (send, list, read, reply)
scripts/email/digest_to_html.py     ← convert weekly digest markdown to HTML email
scripts/cron/                       ← macOS launchd plist files
user_docs_template/                 ← committed templates — copy to user_docs/ on setup
user_docs/                          ← your personal config (gitignored — never committed)
.env_template                       ← copy to .env (gitignored) for API keys
```

## First-time setup

```bash
# 1. Copy personal config templates
cp -r user_docs_template/ user_docs/

# 2. Fill in your details
#    - user_docs/agentmail_config.md  → your email + AgentMail inbox
#    - user_docs/kid_profile/         → copy _template.md for each child

# 3. Copy env template and add API keys
cp .env_template .env
```

`user_docs/` is gitignored. Your personal data (email, child names, school info) never leaves your machine.

## Skills are symlinked, not copied

Skills in this repo are symlinked to `~/.claude/skills/`. Edits here take effect immediately — no re-install needed.

```bash
# If symlinks are missing (e.g. fresh clone), re-link:
for dir in skills/*/*; do
  name=$(basename "$dir")
  ln -sf "$PWD/$dir" ~/.claude/skills/"$name"
done
```

## `.env` setup

Copy `.env_template` to `.env` and fill in your API keys. `.env` is gitignored and must never be committed.

```bash
cp .env_template .env
# Edit .env with your AGENTMAIL_API_KEY, NTFY_TOPIC, etc.
```

## When the user says "remember" something

When the user says "remember X" or "remember that X":

1. **Save to memory** — write a memory file under `~/.claude/projects/.../memory/` and update `MEMORY.md` index (type: `user`, `project`, `feedback`, or `reference` as appropriate).

2. **Update `user_docs/`** — find the most relevant existing file and update it. Mapping:

   | What was remembered | Where to update in user_docs/ |
   |---------------------|-------------------------------|
   | Child info (school, grade, age, interests) | `user_docs/kid_profile/<child>_profile.md` — update frontmatter and/or profile body |
   | School info (name, location, email, portal) | `user_docs/kid_profile/<child>_profile.md` frontmatter + create/update `user_docs/school/` config if relevant |
   | Email / contact config | `user_docs/agentmail_config.md` |
   | Any other personal config | Create or update the appropriate file under `user_docs/` |

3. **Confirm both** — tell the user what was saved to memory and which `user_docs/` file was updated.

If no `user_docs/` file clearly applies, save to memory only and note that no file update was needed.

---

## Contributing a new skill

1. Create `skills/<category>/<name>/SKILL.md`
2. **Run `/privacy-audit --path skills/<category>/<name>/ --mode report`**
3. Fix all Tier 1 issues; document any Tier 2 items in your PR
4. Symlink: `ln -sf "$PWD/skills/<category>/<name>" ~/.claude/skills/<name>`
5. Open a PR
