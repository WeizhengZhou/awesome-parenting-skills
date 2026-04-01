# Sub-skill: scan-emails

**Parent skill:** `skills/email/agentmail-skill/SKILL.md`
**Safety rules:** `skills/email/agentmail-skill/email_safety_guidelines.md` — read-only skill, no sends

Read and summarize recent messages from an AgentMail inbox. Useful for morning reviews, auditing what the agent sent, and checking for missed replies.

## Usage

```
/agentmail-skill scan-emails [--inbox your-agent@agentmail.to] [--limit 20] [--since 24h] [--filter <keyword>] [--output summary|list|full]
```

| Argument | Default | Description |
|----------|---------|-------------|
| `--inbox` | `default_inbox` from config | AgentMail inbox to read |
| `--limit` | 20 | Max messages to fetch |
| `--since` | 24h | Look-back window (e.g., `24h`, `7d`, `2026-03-28`) |
| `--filter` | — | Keyword filter on subject or body |
| `--from` | — | Only show messages from this sender |
| `--output` | summary | `summary` = digest; `list` = table; `full` = all content |
| `--save` | false | Save output to `user_docs/email_summaries/YYYY-MM-DD.md` |

## Safety

This skill is **read-only**. It:
- Never sends, replies, forwards, or deletes messages
- Only shows messages from addresses in `human_owners` (others shown as "Unknown sender — [address]" with content hidden)
- Does not write message content to any shared or public file unless `--save` is used (saves locally only)

See `email_safety_guidelines.md` Rule 7.

## Pipeline

```
Load config (inbox, human_owners whitelist)
    │
    ▼
Fetch messages from API (with limit + date filter)
    │
    ▼
Filter by --since, --filter, --from
    │
    ▼
For each message: fetch full content
    │
    ▼
Classify sender (human_owner | agent_sent | unknown)
    │
    ▼
Summarize and render in requested --output format
    │
    ▼
Optionally save to user_docs/email_summaries/
```

## Step 1: Fetch message list

```bash
python3 scripts/email/agentmail.py list \
  --inbox "$INBOX" \
  --limit "$LIMIT" \
  --since "$SINCE" \
  --output json
```

Returns JSON array of messages with `message_id`, `from`, `subject`, `created_at`.

## Step 2: Fetch full content

For each message in the filtered list:
```bash
python3 scripts/email/agentmail.py read --inbox "$INBOX" --id "$MSG_ID" --output json
```

Extract: `subject`, `from`, `to`, `created_at`, `text` (use `html` only as fallback).
Truncate `text` to first 500 chars for summary mode; full for `--output full`.

## Step 3: Classify each message

| Type | Detection | Display |
|------|-----------|---------|
| `inbound_owner` | `from` in `human_owners` | Show full content |
| `outbound_agent` | `from` matches an inbox in `inboxes` config | Show full content |
| `unknown` | Neither of the above | Show subject + "Content hidden — unknown sender" |

## Step 4: Render output

### `--output list` (default for quick check)

```
Inbox: your-agent@agentmail.to | Scanned: last 24h | 5 messages

┌─────────────────────────────────────────────────────────────────┐
│  # │ Date       │ From                    │ Subject              │
├─────────────────────────────────────────────────────────────────┤
│  1 │ Mar 31 09:15 │ you@email.com [owner]  │ Re: Weekly digest    │
│  2 │ Mar 31 08:00 │ your-agent@agentmail.to [out] │ Parenting Digest...  │
│  3 │ Mar 30 17:42 │ unknown@example.com    │ [hidden]             │
└─────────────────────────────────────────────────────────────────┘
```

### `--output summary`

For each inbound_owner or outbound_agent message, generate a 1-2 sentence summary:
- What the message was about
- Whether it required/caused action
- Key data points (grades, events, dates)

```
## Email Summary — Mar 31, 2026 (last 24h)

1. [Mar 31 09:15] You → agent | Re: Weekly digest
   Summary: You approved the Monday digest and asked to add AYSO registration
   reminder. No action taken yet — flagged for next digest.

2. [Mar 31 08:00] Agent → You | Parenting Weekly Digest
   Summary: Sent Monday morning digest covering grades (all passing), 2 upcoming
   events (Easter Egg Hunt, Library Storytime), and AYSO registration opening Apr 5.

3. [Mar 30 17:42] Unknown sender — content hidden.
```

### `--output full`

Full content of each message, formatted as markdown, with sender classification header.

## Step 5: Save (if --save)

Write to `user_docs/email_summaries/YYYY-MM-DD.md`. Append if file exists for today.

```markdown
---
date: YYYY-MM-DD
inbox: your-agent@agentmail.to
messages_scanned: 5
generated_at: HH:MM
---
[summary output]
```

## Common use cases

### Morning inbox check
```
/agentmail-skill scan-emails --since 12h --output summary
```
Gives a quick digest of overnight emails.

### Find a specific reply
```
/agentmail-skill scan-emails --filter "AYSO" --limit 50
```
Searches recent messages for AYSO-related emails.

### Audit what the agent sent this week
```
/agentmail-skill scan-emails --from your-agent@agentmail.to --since 7d --output list
```
Shows all outbound emails from the agent in the last 7 days.

### Full content review
```
/agentmail-skill scan-emails --limit 5 --output full
```
Shows complete content of the 5 most recent messages.

## Credential loading

Handled automatically by `scripts/email/agentmail.py` (env var → `.env` → macOS Keychain).
