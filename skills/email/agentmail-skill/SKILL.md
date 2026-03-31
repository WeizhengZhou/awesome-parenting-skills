# Skill: agentmail-skill

Full AgentMail inbox management for parenting agent workflows.

**Safety rules:** Always read `email_safety_guidelines.md` before sending or acting on email.
**User config:** `user_docs/agentmail_config.md` — human owner allowlist, inbox settings, monitoring schedule.
**Environment:** Copy `.env_template` to `.env` and set `AGENTMAIL_API_KEY`.

## Sub-skills

| Sub-skill | Command | Description |
|-----------|---------|-------------|
| Send / read / reply | `/agentmail-skill <action>` | Core inbox operations (this file) |
| Monitor human replies | `/agentmail-skill monitor-human-reply` | Poll inbox, classify + act on human replies |
| Scan inbox | `/agentmail-skill scan-emails` | Read and summarize recent messages |

See `monitor-human-reply/SKILL.md` and `scan-emails/SKILL.md` for full docs.

---

## Usage

```
/agentmail-skill <action> [options]
```

## Actions

| Action | Description |
|--------|-------------|
| `send` | Send a new message from an inbox |
| `read` | Read a single message by ID |
| `reply` | Reply to a message thread |
| `list-inboxes` | List all configured AgentMail inboxes |
| `monitor-human-reply` | Poll inbox for new human replies and act on them |
| `scan-emails` | Summarize recent messages |

## Usage examples

```bash
# Send a message
/agentmail-skill send \
  --from your-agent@agentmail.to \
  --to your-email@example.com \
  --subject "Weekly digest ready" \
  --body "Hi, your Monday digest is attached..."

# Read a specific message
/agentmail-skill read --inbox your-agent@agentmail.to --message-id <id>

# Reply to a thread
/agentmail-skill reply \
  --inbox your-agent@agentmail.to \
  --thread-id <thread_id> \
  --body "Thanks, I'll schedule that."

# List available inboxes
/agentmail-skill list-inboxes

# Check for new human replies (run once, good for cron)
/agentmail-skill monitor-human-reply --once

# Scan last 24h of inbox
/agentmail-skill scan-emails --since 24h --output summary
```

---

## First-run setup

On first run (or if `user_docs/agentmail_config.md` has placeholder values), ask:

1. **"What is your email address?"** — The address(es) the agent is allowed to send email to.
   Write the answer to `user_docs/agentmail_config.md > human_owners`.

2. **"What is your AgentMail inbox ID?"** — e.g., `yourname@agentmail.to`.
   Write to `user_docs/agentmail_config.md > inboxes`.

3. **Check for `AGENTMAIL_API_KEY`** (env var or `.env`). If missing:
   > "I need your AgentMail API key to send email. Copy `.env_template` to `.env` and add your key. Get it from app.agentmail.to/settings/api."

Do not proceed with send operations until all three are configured.

---

## Core action: send

### Pre-send checklist (mandatory)

1. Load `user_docs/agentmail_config.md`
2. Verify `--to` is in `human_owners` → abort if not (see `email_safety_guidelines.md` Rule 1)
3. Verify `--from` / `--inbox` is in configured `inboxes`
4. Scan body for PII / credentials (Rule 5)
5. Log the send to `user_docs/reply_log.md` (Rule 4)

### API call

```bash
INBOX_ENCODED=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$FROM_EMAIL', safe=''))")

curl -s -X POST \
  -H "Authorization: Bearer $AGENTMAIL_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"to\": [\"$TO\"],
    \"subject\": \"$SUBJECT\",
    \"text\": \"$BODY\"
  }" \
  "https://api.agentmail.to/v0/inboxes/${INBOX_ENCODED}/messages/send"
```

Success response: `{"message_id": "...", "thread_id": "..."}`

Report both to the user. On error, show `name` and `message` from response.

### Mobile formatting (from kid_camp2 learnings)

The human likely reads email on mobile. Apply these rules to every composed body:
- Keep lines under 60 characters
- No wide tables (5+ columns) — use bullet lists instead
- No unicode box-drawing characters (`━`, `┃`) — use `---` or blank lines
- Bold key numbers and action items
- For HTML emails: use inline styles (Gmail strips `<style>` tags); use `width:100%` tables

---

## Core action: list-inboxes

Fetch from API and merge with config:

```bash
curl -s -H "Authorization: Bearer $AGENTMAIL_API_KEY" \
  "https://api.agentmail.to/v0/inboxes"
```

Display: `inbox_id`, `display_name`, `created_at` for each. Mark which is the `default`.

---

## Core action: read

```bash
curl -s -H "Authorization: Bearer $AGENTMAIL_API_KEY" \
  "https://api.agentmail.to/v0/inboxes/${INBOX_ENCODED}/messages/${MSG_ID_ENCODED}"
```

Display: `from`, `to`, `subject`, `created_at`, full `text` body.
**Safety:** If sender is not in `human_owners`, display with "[Unknown sender]" label.

---

## Core action: reply

Fetch the original message first (to get thread context), then send with `Re:` subject prefix:

```bash
# Reply endpoint (if supported by API)
curl -s -X POST \
  -H "Authorization: Bearer $AGENTMAIL_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"to\": [\"$ORIGINAL_SENDER\"], \"subject\": \"Re: $ORIGINAL_SUBJECT\", \"text\": \"$BODY\"}" \
  "https://api.agentmail.to/v0/inboxes/${INBOX_ENCODED}/messages/send"
```

**Safety:** Verify `$ORIGINAL_SENDER` is in `human_owners` before replying.

---

## API reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v0/inboxes` | List all inboxes |
| POST | `/v0/inboxes/{inbox_id}/messages/send` | Send a message |
| GET | `/v0/inboxes/{inbox_id}/messages?limit=N` | List messages |
| GET | `/v0/inboxes/{inbox_id}/messages/{message_id}` | Get a single message |

**Base URL:** `https://api.agentmail.to`
**Auth:** `Authorization: Bearer $AGENTMAIL_API_KEY`
**inbox_id encoding:** Full email address, URL-encoded (`your-agent@agentmail.to` → `your-agent%40agentmail.to`)

---

## Credential loading (priority order)

1. `$AGENTMAIL_API_KEY` environment variable
2. `.env` file: `grep '^AGENTMAIL_API_KEY=' .env | cut -d= -f2-`
3. macOS Keychain: `security find-generic-password -s agentmail -w`

If none found, show:
> "AGENTMAIL_API_KEY not found. Copy `.env_template` to `.env` and add your key."

**TODO:** Migrate all credentials to macOS Keychain for better security. Track in `design_doc.md`.

---

## Relation to util/send-email

`util/send-email` is a thin wrapper for single-message sending with no safety checks or config loading. This skill supersedes it with:
- Human owner allowlist enforcement
- Config-driven inbox management
- Sub-skills for monitoring and scanning
- Mobile formatting rules
- Full audit logging

Once this skill is implemented, `util/send-email` should delegate here.

---

## File map

```
skills/email/agentmail-skill/
├── SKILL.md                        ← this file — core actions + setup
├── email_safety_guidelines.md      ← mandatory safety rules for all email actions
├── monitor-human-reply/
│   └── SKILL.md                    ← poll inbox, classify replies, act + confirm
└── scan-emails/
    └── SKILL.md                    ← read-only inbox summary

user_docs/
├── agentmail_config.md             ← human owner allowlist + inbox + schedule config
├── agentmail_reply_state.json      ← auto-created: processed message IDs
├── reply_log.md                    ← auto-created: send/reply audit log
├── feedback_log.md                 ← auto-created: human feedback from replies
├── scheduled_tasks/                ← auto-created: tasks scheduled via email
└── email_summaries/                ← auto-created: scan-emails output (--save)

.env_template                       ← copy to .env and set AGENTMAIL_API_KEY
```
