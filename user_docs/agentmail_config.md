---
config_type: agentmail
description: AgentMail inbox configuration and human owner email whitelist
last_updated: 2026-03-31
---

# AgentMail Configuration

This file is read by the `/agentmail-skill`, `/send-email`, and related email skills.
Edit it to add your own email addresses and inbox settings.

> **Security note:** This file defines the allowlist of addresses that agent skills
> are permitted to send email to. Skills enforce this list before every send.
> See `skills/email/agentmail-skill/email_safety_guidelines.md` for the full policy.

---

## Human owner email addresses (allowlist)

Only these addresses may receive email from agent skills.
Add your own email(s) here. Remove the examples.

```yaml
human_owners:
  - email: your-email@example.com
    name: Your Name
    role: primary              # primary | secondary | test
    notes: "Main inbox — receives all agent updates"

  - email: your-test-inbox@example.com
    name: Your Name (test)
    role: test
    notes: "Use for dry runs before sending to primary"
```

**To customize:** Replace the examples above with your real addresses.
The agent will ask for these on first run and write them here automatically.

---

## AgentMail inboxes

Inboxes your agent can send FROM. Add your own inbox IDs from agentmail.to.

```yaml
inboxes:
  - inbox_id: your-agent@agentmail.to
    display_name: "Parenting Assistant"
    default: true
    use_for:
      - status_updates
      - weekly_digest
      - grade_alerts
      - registration_alerts

  - inbox_id: your-inbox@agentmail.to
    display_name: "KidPlanr"
    default: false
    use_for:
      - marketing           # disabled by default in parenting project
```

---

## Default send settings

```yaml
send_defaults:
  default_inbox: your-agent@agentmail.to
  require_confirmation_before_send: false   # set true to always prompt before sending
  dry_run_recipient: your-test-inbox@example.com   # used for dry runs
  mobile_friendly: true                    # apply mobile formatting rules
```

---

## Reply monitoring settings

```yaml
monitor_human_reply:
  enabled: true
  poll_interval_minutes: 60
  active_hours:                  # only poll during these hours (local time)
    start: "08:00"
    end:   "20:00"
  state_file: user_docs/agentmail_reply_state.json
  log_replies_to: user_docs/reply_log.md
```

---

## Scan settings

```yaml
scan_emails:
  default_limit: 20
  default_lookback_hours: 24
  save_summaries_to: user_docs/email_summaries/
```
