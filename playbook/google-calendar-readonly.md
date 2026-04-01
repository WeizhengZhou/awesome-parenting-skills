# Playbook — Google Calendar (Read-Only via ICS)

**What you get:** The agent can read your Google Calendar events — upcoming activities, school events, camp dates — and use them in weekly digests, family planning, and reminders. No API key or Google Cloud setup required.

**Time:** 5 minutes
**Prerequisites:** Playbook 0 done. A Google Calendar you want to share.

---

## At a glance — what you do vs. what the agent does

| Section | You need to... | Agent does |
|---------|---------------|-----------|
| Get ICS URL | Find it in Google Calendar settings (one-time, 2 min) | — |
| Add URL to `.env` | Paste one line | — |
| Add multiple calendars | Repeat for each calendar | — |
| Read events | Nothing | ✅ Fetches URL, parses events, filters by date |
| Use in weekly digest | Nothing | ✅ Pulls upcoming events into digest automatically |
| Refresh | Nothing | ✅ Fetches live URL each time — always current |

**TL;DR:** Copy one URL from Google Calendar, paste it in `.env`. That's it.

---

## Step 1: Get your calendar's private ICS URL

1. Open **calendar.google.com** in a browser
2. In the left sidebar, hover over the calendar you want to share → click **⋮ (three dots)**
3. Click **"Settings and sharing"**
4. Scroll down to the **"Integrate calendar"** section
5. Find **"Secret address in iCal format"** → click the copy icon

The URL looks like:
```
https://calendar.google.com/calendar/ical/yourname%40gmail.com/private-abc123.../basic.ics
```

> **Can't find "Integrate calendar"?** You may be on a Google Workspace (work/school) account where the admin disabled external sharing. See the alternatives section at the bottom.

---

## Step 2: Add the URL to `.env`

Open `.env` in a text editor and add a line:

```bash
# Google Calendars (ICS format — treat these URLs as secrets)
FAMILY_CALENDAR_ICS=https://calendar.google.com/calendar/ical/...your-url.../basic.ics
```

For multiple calendars, add one line per calendar:

```bash
FAMILY_CALENDAR_ICS=https://...your-family-calendar.../basic.ics
LEXI_CALENDAR_ICS=https://...lexi-activities-calendar.../basic.ics
SCHOOL_CALENDAR_ICS=https://...school-calendar.../basic.ics
```

Use descriptive names — the agent reads them by name to know which calendar is which.

---

## Step 3: Tell the agent to read your calendar

In Claude Code, just ask:

```
What's on the family calendar for the next 2 weeks?
```

Or more specifically:
```
Pull the family calendar and show me everything in April.
```

The agent will fetch the URL live, parse the events, and display them. No skill needed — it works from the `.env` file directly.

---

## What the agent can do with your calendar

| Ask | What happens |
|-----|-------------|
| "What's on the calendar this week?" | Lists events with dates and times |
| "Are there any conflicts next week?" | Checks for overlapping events |
| "Add calendar events to the weekly digest" | Digest includes upcoming events section |
| "What activities does Lexi have in April?" | Filters events by name/keyword |
| "When is the next school break?" | Finds multi-day events or gaps |
| "What's coming up in the next 30 days?" | Full lookahead |

---

## Adding more calendars

Each person or category can have their own calendar:

```bash
# Suggested setup for a family with one school-age child
FAMILY_CALENDAR_ICS=...     # shared family events
LEXI_CALENDAR_ICS=...       # Lexi's activities, camps, playdates
SCHOOL_CALENDAR_ICS=...     # school events (if school publishes a public ICS)
SPORTS_CALENDAR_ICS=...     # lacrosse, swim, RSM schedule
```

Many schools and sports leagues publish public ICS feeds — check their website for a "Subscribe to calendar" or "Add to Google Calendar" link. Those URLs work the same way.

---

## Security note — treat the ICS URL as a secret

The private ICS URL gives read-only access to your calendar to anyone who has it. It's not tied to your Google account login, so you can't protect it with 2FA.

- Store it in `.env` only (gitignored, never committed)
- Don't paste it in Slack, email, or any public place
- If you think it's been exposed: Google Calendar → Settings → "Reset private URLs" to revoke and generate a new one

The agent uses it read-only — it cannot create, edit, or delete calendar events via ICS.

---

## Alternatives if ICS is not available

### Google Workspace accounts

If you're on a school or work Google account and can't find the ICS option, try:

1. **Create a separate personal Gmail calendar** — add your family events there, get ICS from that
2. **Use a public school calendar** — many schools publish a public `.ics` or "Subscribe" link on their website. Search: `site:yourschool.org ical` or look for a "Subscribe to calendar" button on the school events page
3. **Apple Calendar / iCal** — if you use Apple Calendar, each calendar also has an exportable ICS URL under Calendar → Get Info → Share Calendar (public read-only link)

### If you want write access (agent creates events)

That requires the Google Calendar API with OAuth. It's more setup (~30 min) but lets the agent add library due dates, permission slip deadlines, and activity reminders directly to your calendar. Ask for "Playbook: Google Calendar API setup" if you want to go this route.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Empty calendar / no events | The ICS URL may be for a calendar with no future events — check Google Calendar directly |
| "403 Forbidden" error | The URL may have expired or been reset — get a fresh URL from Google Calendar settings |
| Very old events showing up | Agent is filtering from today — ask specifically "upcoming events" |
| Can't find the ICS URL | You may be on Workspace — see alternatives above |
| Want to stop sharing | Google Calendar → Settings → "Reset private URLs" |
