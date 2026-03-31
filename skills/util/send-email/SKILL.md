# Skill: send-email

Send an email from an AgentMail inbox.

## Usage

```
/send-email --to <recipient> --from <inbox_email> --subject "<subject>" --body "<body>"
```

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--to` | yes | — | Recipient email address |
| `--from` | yes | — | AgentMail inbox email (e.g. `pgm@agentmail.to`) |
| `--subject` | yes | — | Email subject line |
| `--body` | yes | — | Plain-text email body |
| `--html` | no | — | HTML email body (overrides `--body` for HTML clients) |
| `--cc` | no | — | CC recipients (comma-separated) |
| `--reply-to` | no | — | Reply-to address |

## How it works

1. Look up `AGENTMAIL_API_KEY` — check in order:
   - Environment variable `AGENTMAIL_API_KEY`
   - `/Users/weizheng/projects/claude/kid_camp2/backend/.env`
   - macOS Keychain: `security find-generic-password -s agentmail -w`

2. URL-encode the `--from` address for use as `{inbox_id}` in the path.

3. POST to the AgentMail API:

```bash
INBOX_ID=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$FROM_EMAIL'))")
curl -s -X POST "https://api.agentmail.to/v0/inboxes/${INBOX_ID}/messages/send" \
  -H "Authorization: Bearer $AGENTMAIL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "to": ["$TO"],
    "subject": "$SUBJECT",
    "text": "$BODY"
  }'
```

4. On success, the API returns `{"message_id": "...", "thread_id": "..."}`. Report both to the user.

5. On error, report the `name` and `message` fields from the response.

## Available inboxes

| Email | Display Name | Use for |
|-------|-------------|---------|
| `pgm@agentmail.to` | KidPlanr PgM | Status updates, project comms |
| `kidplanr@agentmail.to` | KidPlanr | Marketing, lead outreach |

## API reference

- List inboxes: `GET https://api.agentmail.to/v0/inboxes`
- Send message: `POST https://api.agentmail.to/v0/inboxes/{inbox_id}/messages/send`
- List messages: `GET https://api.agentmail.to/v0/inboxes/{inbox_id}/messages`

## Notes

- `inbox_id` in the URL must be the full email address, URL-encoded (`%40` for `@`)
- The API key from `kid_camp2/backend/.env` works for both inboxes (same organization)
- Never log or expose the API key in output
