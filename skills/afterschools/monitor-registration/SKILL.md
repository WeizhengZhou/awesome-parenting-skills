---
name: monitor-registration
description: "Set up monitoring for a registration page — camp signups, class registrations, doctor appointments, rec department openings. Alerts you via ntfy when the status changes from 'waitlist' or 'full' to 'open'. Usage: /monitor-registration [url] [--selector CSS_SELECTOR] [--label 'Camp Name']"
tools: Read, Write, Bash, WebFetch
model: sonnet
---

You help parents never miss a registration opening by setting up automated page monitoring with instant alerts.

## Step 1: Collect parameters

Parse from the user's command or ask:
- **URL** — the registration page to monitor (required)
- **Label** — friendly name for the alert, e.g., "Galileo Camp Week 3" (optional, defaults to page title)
- **CSS selector** — element to watch, e.g., `.registration-status`, `#enroll-button` (optional — auto-detect if not provided)
- **Check interval** — how often to poll (default: every 30 minutes during business hours)
- **Alert condition** — what text change to watch for (default: "Register" or "Enroll" appearing, or "Waitlist" disappearing)

## Step 2: Inspect the page

Fetch the URL and analyze the current state:

```python
import requests
from bs4 import BeautifulSoup

resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
soup = BeautifulSoup(resp.text, 'html.parser')

# Try to auto-detect the registration status element
candidates = soup.find_all(text=lambda t: any(word in t.lower() for word in
    ['register', 'enroll', 'waitlist', 'full', 'open', 'closed', 'sold out', 'available']))

print("Current status candidates:")
for c in candidates[:5]:
    print(f"  [{c.parent.name}#{c.parent.get('id','')}.{' '.join(c.parent.get('class',[]))}]: {c.strip()[:100]}")
```

Report to user: "The page currently shows: **[current status]**. I'll alert you when this changes."

## Step 3: Choose monitoring method

### Option A: changedetection.io (recommended for most pages)

Requires changedetection.io running locally (see `mcp/chrome-automation.md` for Docker setup).

```bash
# Add a new watch via changedetection.io API
curl -s -X POST "http://localhost:5000/api/v1/watch" \
  -H "x-api-key: YOUR_CDI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "'$URL'",
    "title": "'$LABEL'",
    "time_between_check": {"minutes": 30},
    "css_filter": "'$SELECTOR'",
    "notification_urls": ["ntfy://ntfy.sh/YOUR_FAMILY_TOPIC"],
    "notification_title": "Registration Alert: '$LABEL'",
    "notification_body": "Status changed on '$URL'"
  }'
echo "Watch created in changedetection.io"
echo "Dashboard: http://localhost:5000"
```

### Option B: Standalone monitoring script + launchd

For pages that don't work with changedetection.io (login-required, JS-heavy):

```javascript
// monitor-registration.js
const { chromium } = require('playwright');
const crypto = require('crypto');
const fs = require('fs');

const CONFIG = {
  url: process.env.MONITOR_URL,
  label: process.env.MONITOR_LABEL || 'Registration',
  selector: process.env.MONITOR_SELECTOR || 'body',
  ntfyTopic: process.env.NTFY_TOPIC,
  stateFile: `${process.env.HOME}/.family-monitor-state.json`
};

async function check() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  try {
    await page.goto(CONFIG.url, { waitUntil: 'networkidle', timeout: 30000 });
    const content = await page.$eval(CONFIG.selector, el => el.textContent.trim())
      .catch(() => page.content());

    const hash = crypto.createHash('md5').update(content).digest('hex');
    const state = fs.existsSync(CONFIG.stateFile)
      ? JSON.parse(fs.readFileSync(CONFIG.stateFile)) : {};

    if (state[CONFIG.url] && state[CONFIG.url].hash !== hash) {
      // Content changed — check if it's a positive signal
      const isOpen = /register now|enroll now|sign up|available|open/i.test(content);
      const wasWaitlist = /waitlist|full|sold out|closed/i.test(state[CONFIG.url].content || '');

      const priority = (isOpen && wasWaitlist) ? 'high' : 'default';
      const title = isOpen ? `OPEN: ${CONFIG.label}` : `Changed: ${CONFIG.label}`;
      const body = isOpen
        ? `Registration is now OPEN! Act fast: ${CONFIG.url}`
        : `Page content changed: ${CONFIG.url}`;

      // Send ntfy notification
      await fetch(`https://ntfy.sh/${CONFIG.ntfyTopic}`, {
        method: 'POST',
        headers: { 'Title': title, 'Priority': priority, 'Click': CONFIG.url },
        body
      });

      console.log(`[${new Date().toISOString()}] ALERT sent: ${title}`);
    } else {
      console.log(`[${new Date().toISOString()}] No change: ${CONFIG.label}`);
    }

    state[CONFIG.url] = { hash, content: content.slice(0, 500), checked: new Date().toISOString() };
    fs.writeFileSync(CONFIG.stateFile, JSON.stringify(state, null, 2));

  } finally {
    await browser.close();
  }
}

check().catch(console.error);
```

Save to `~/projects/parenting/automation/monitor-registration.js`, then use `/mac-cron-job create` to schedule it:

```
# Every 30 minutes, 7 AM – 9 PM
*/30 7-21 * * * MONITOR_URL="[url]" MONITOR_LABEL="[label]" NTFY_TOPIC="your-topic" node ~/projects/parenting/automation/monitor-registration.js >> ~/Library/Logs/family-automation/monitor.log 2>&1
```

## Step 4: Confirm setup

Tell the user:
```
✓ Monitoring set up for: [Label]
  URL: [url]
  Watching: [selector or "full page"]
  Check interval: every 30 minutes
  Alert: ntfy.sh/[topic] when status changes
  Current status: [status text]

You'll get a HIGH priority alert the moment registration opens.
Dashboard (changedetection.io): http://localhost:5000
```

## Common registration patterns to watch for

| Platform | What to monitor | Selector hint |
|----------|----------------|---------------|
| ActiveNet (city rec) | "Register" button | `#btnRegister`, `.register-btn` |
| Xplor/PerfectMind | Status badge | `.status-badge`, `.availability` |
| Camp websites | "Enroll" or "Full" text | `.enrollment-status` |
| ZocDoc (appointments) | Available time slots | `.time-slot-available` |
| MyChart | Appointment availability | `.schedule-appt` |
| Eventbrite | Ticket availability | `.ticket-status` |

## Tips

- For pages requiring login, use Tier 1 (existing Chrome) or Tier 2 (saved session) from `/browser-automate`
- Set interval to 5–10 minutes in the week before a popular program opens
- Most Bay Area city rec departments open registration at 7 AM or 9 AM — set interval to 5 min during those windows
- Always test the script manually before scheduling: `node monitor-registration.js`
