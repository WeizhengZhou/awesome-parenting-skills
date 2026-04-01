# Skill: youtube-kids-audit

Browse a child's YouTube / YouTube Kids watch history, analyze content patterns, and recommend channels/videos to add, keep, remove, or block.

## Sub-skills

| Sub-skill | Command | Description |
|-----------|---------|-------------|
| Scrape history | `/youtube-kids-audit` | CDP WebSocket scrape of `youtube.com/feed/history` (this file) |
| Analyze content | `/youtube-kids-audit analyze-kids-content` | Filter kid vs adult, classify, safety check, recommend |

See `analyze-kids-content/SKILL.md` for the full analysis pipeline.

## Usage

```
# Step 1 — scrape watch history from signed-in Chrome
/youtube-kids-audit [--days 30]

# Step 2 — analyze and generate educational report (uses claude-opus-4-6)
/youtube-kids-audit analyze-kids-content [--profile <child-name>]
```

## Capabilities

- Scrape watch history via Chrome DevTools Protocol (no YouTube API key required)
- Filter mixed adult/kid accounts using a kid profile noise filter
- Classify each video: Fantasy/Lore, Science, Math, Language Arts, Junk Food, Adult/Irrelevant
- Flag age-inappropriate or concerning content
- Recommend YouTube channels and books tailored to the child's learning style
- Gap analysis: identify missing "nutrients" in the content diet
- First-run intake: if no kid profile exists, interview the parent and write `user_docs/kid_profile/<name>.md`

## Arguments (planned)

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--profile` | no | all kids | Which child's account to audit |
| `--days` | no | 30 | Look-back window for watch history |
| `--min-watch-minutes` | no | 5 | Ignore videos watched less than N minutes |
| `--output` | no | report | `report` = markdown summary; `actions` = execute approved changes |
| `--dry-run` | no | false | Show recommended actions without executing |

## Design notes

### Data sources
- **YouTube Kids app** (iOS/Android): No API — parental controls live in Google Family Link
- **Google Family Link API**: Activity reports available; no public API for watch history extraction
- **Supervised Google account** (ages 13+): YouTube History at `myactivity.google.com` — accessible via browser automation
- **YouTube Data API v3**: Can fetch channel metadata, video details, category, age restriction once video IDs are known

### Content classification approach
1. Extract video/channel list from watch history (browser automation on `myactivity.google.com` or Family Link activity export)
2. For each unique channel: fetch metadata via YouTube Data API (category, subscriber count, description)
3. Pass channel name + recent video titles to Claude for age-appropriateness and educational value scoring
4. Flag channels with: `made for kids=false`, explicit language in titles, low subscriber count + high engagement anomaly (potential predatory content)
5. Aggregate by watch-time to surface top 10 channels

### Classification dimensions

| Dimension | Scale | Description |
|-----------|-------|-------------|
| Age fit | 1–5 | Appropriate for child's age (from `family-state.json`) |
| Educational value | 1–5 | Learning content vs pure entertainment |
| Watch time share | % | What % of total watch time this channel represents |
| Concern flags | list | `language`, `violence`, `ads_heavy`, `misleading_thumbnails`, `predatory_comments` |
| Recommendation | keep/add/remove/block | Parent action |

### Actions (when `--output actions` and parent approves)
- **Subscribe**: Add channel to YouTube Kids approved list (via Family Link browser automation)
- **Remove from history**: Delete specific videos from activity
- **Block channel**: Add to blocked list in Family Link parental controls
- **Set timer**: Update YouTube Kids daily time limit for child

### `family-state.json` schema (planned additions)
```json
{
  "kids": {
    "emma": {
      "age": 7,
      "youtube": {
        "account_type": "youtube_kids",
        "family_link_supervised": true,
        "approved_channels": ["SciShow Kids", "National Geographic Kids"],
        "blocked_channels": [],
        "daily_limit_minutes": 60
      }
    }
  }
}
```

## Step-by-step: scrape watch history

### Step 0: Detect and launch headed Chrome on debug port 9222

Before doing anything else, check if a headed Chrome with remote debugging is already running:

```bash
curl -s http://localhost:9222/json/version 2>/dev/null | python3 -c \
  "import json,sys; d=json.load(sys.stdin); print(d.get('Browser',''))"
```

**If port 9222 is not responding**, tell the user:

> Chrome isn't running in debug mode yet. I need to open a special Chrome window so I can read your YouTube history.
>
> Here's what the command does:
> - Opens a **visible** (headed) Chrome window — you'll be able to see and interact with it
> - Enables a debug port (`9222`) so I can read page content without controlling your regular browser
> - Uses a separate profile (`/tmp/chrome-parenting-profile`) so it won't affect your regular Chrome bookmarks or settings
>
> Command:
> ```bash
> /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
>   --remote-debugging-port=9222 \
>   --no-first-run \
>   --no-default-browser-check \
>   --user-data-dir=/tmp/chrome-parenting-profile \
>   --start-maximized \
>   "https://www.youtube.com/feed/history"
> ```
>
> Want me to run this for you, or would you prefer to run it yourself?

If the user asks you to run it, execute:
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --no-first-run \
  --no-default-browser-check \
  --user-data-dir=/tmp/chrome-parenting-profile \
  --start-maximized \
  "https://www.youtube.com/feed/history" \
  > /tmp/chrome-debug.log 2>&1 &
sleep 2
curl -s http://localhost:9222/json/version | python3 -c "import json,sys; print('Chrome ready:', json.load(sys.stdin).get('Browser',''))"
```

**After launching**, tell the user:

> Chrome is open and showing YouTube. Please **sign in to your Google account** in that window — the one with your child's watch history. Come back here once you're signed in.

**Detect sign-in**: Poll every 3 seconds (up to 60 seconds) until the history page shows videos:

```bash
for i in $(seq 1 20); do
  STATUS=$(curl -s http://localhost:9222/json | python3 -c "
import json, sys, urllib.request
tabs = json.load(sys.stdin)
yt_tab = next((t for t in tabs if 'youtube.com' in t.get('url','')), None)
print(yt_tab.get('url','') if yt_tab else 'no_tab')
" 2>/dev/null)
  echo "[$i] $STATUS"
  # Check if signed in by reading page title via CDP
  SIGNED_IN=$(curl -s "http://localhost:9222/json" | python3 -c "
import json, sys
tabs = json.load(sys.stdin)
yt = next((t for t in tabs if 'youtube.com/feed/history' in t.get('url','')), None)
print('yes' if yt and 'Watch history' in yt.get('title','') else 'no')
" 2>/dev/null)
  if [ "$SIGNED_IN" = "yes" ]; then
    echo "Signed in — continuing."
    break
  fi
  sleep 3
done
```

Alternatively, use the Chrome DevTools MCP to check:
```
navigate to https://www.youtube.com/feed/history
evaluate_script: () => document.title
```
If the title contains the user's channel name or "Watch history" with videos present (not "Sign in"), proceed. If still showing "Sign in" after 60 seconds, prompt:
> I don't see you're signed in yet. Please sign in to YouTube in the Chrome window, then let me know.

### Step 1: Find the YouTube history tab

Get the Chrome tab ID for the history page via CDP:

```bash
HISTORY_TAB_ID=$(curl -s http://localhost:9222/json | python3 -c "
import json, sys
tabs = json.load(sys.stdin)
yt = next((t for t in tabs if 'youtube.com/feed/history' in t.get('url','')), None)
if not yt:
    print('ERROR: no history tab found')
else:
    print(yt['id'])
")
echo "History tab: $HISTORY_TAB_ID"
```

If no history tab is found, navigate there using the MCP tool or:
```bash
# Navigate existing tab via CDP (replace TAB_ID)
curl -s -X POST http://localhost:9222/json/activate/$HISTORY_TAB_ID
```

Then open `https://www.youtube.com/feed/history` in the Chrome window manually.

### Step 2: Scroll to load all history items

YouTube history uses infinite scroll. Scroll down until no new items load:

```python
import asyncio, json, websockets

WS_URL = f"ws://localhost:9222/devtools/page/{TAB_ID}"

SCROLL_JS = """
(async () => {
  let lastCount = 0;
  for (let i = 0; i < 30; i++) {
    window.scrollTo(0, document.body.scrollHeight);
    await new Promise(r => setTimeout(r, 1500));
    const count = document.querySelectorAll('div[class*="content-id-"]').length;
    if (count === lastCount) break;
    lastCount = count;
  }
  return lastCount;
})()
"""

async with websockets.connect(WS_URL) as ws:
    await ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
    await ws.recv()
    await ws.send(json.dumps({
        "id": 2, "method": "Runtime.evaluate",
        "params": {"expression": SCROLL_JS, "returnByValue": True, "awaitPromise": True}
    }))
    while True:
        msg = json.loads(await ws.recv())
        if msg.get("id") == 2: break
    count = msg["result"]["result"].get("value", 0)
    print(f"Loaded {count} history items")
```

### Step 3: Extract history items via CDP

YouTube's history page renders each video as `div[class*="content-id-{videoId}"]`. Confirmed working selectors:

| Field | Selector |
|-------|----------|
| Container | `div[class*="content-id-"]` |
| Video ID | `content-id-{11chars}` in class name |
| Duration | `.yt-badge-shape__text` |
| Title | `span.yt-core-attributed-string:not(.yt-content-metadata-view-model__metadata-text)` |
| Channel | `span.yt-content-metadata-view-model__metadata-text` (first) |
| Views | `span.yt-content-metadata-view-model__metadata-text` (second) |
| Thumbnail | `img` (first inside container) |

```python
EXTRACT_JS = """
(() => {
  const results = [];
  document.querySelectorAll('div[class*="content-id-"]').forEach(item => {
    const m = item.className.match(/content-id-([A-Za-z0-9_-]{11})/);
    if (!m) return;
    const videoId = m[1];

    const durationEl = item.querySelector('.yt-badge-shape__text');
    const titleEl    = item.querySelector(
      'span.yt-core-attributed-string:not(.yt-content-metadata-view-model__metadata-text)'
    );
    const metaSpans  = item.querySelectorAll('span.yt-content-metadata-view-model__metadata-text');
    const img        = item.querySelector('img');

    results.push({
      videoId,
      title:       titleEl?.textContent?.trim() || '',
      channel:     metaSpans[0]?.textContent?.trim() || '',
      views:       metaSpans[1]?.textContent?.trim() || '',
      durationRaw: durationEl?.textContent?.trim() || '',
      thumbnail:   img?.src || '',
    });
  });
  return results;
})()
"""
```

### Step 4: Parse duration and classify video type

```python
import re, datetime

def parse_duration_secs(raw: str) -> int:
    parts = raw.strip().split(":")
    try:
        if len(parts) == 2:   return int(parts[0]) * 60 + int(parts[1])
        if len(parts) == 3:   return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    except Exception:
        pass
    return 0

enriched = []
for v in videos_raw:
    secs = parse_duration_secs(v["durationRaw"])
    mins = round(secs / 60, 1)
    enriched.append({
        "videoId":     v["videoId"],
        "title":       v["title"],
        "url":         f"https://www.youtube.com/watch?v={v['videoId']}",
        "channel":     v["channel"],
        "views":       v["views"],
        "durationRaw": v["durationRaw"],
        "durationMins": mins,
        "videoType":   "short" if 0 < secs <= 60 else "long",
        "thumbnail":   v["thumbnail"],
        "scrapedAt":   datetime.datetime.now().isoformat(),
    })
```

### Step 5: Write JSON output

```python
import json, os

today = datetime.date.today().isoformat()
out_dir = "user_docs"
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, f"watch_history_{today}.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(enriched, f, indent=2, ensure_ascii=False)
print(f"Saved {len(enriched)} videos → {out_path}")
```

### Output JSON schema

```json
[
  {
    "videoId": "3ryID_SwU5E",
    "title": "$1 vs $100,000,000 House!",
    "url": "https://www.youtube.com/watch?v=3ryID_SwU5E",
    "channel": "MrBeast",
    "views": "416M views",
    "durationRaw": "17:03",
    "durationMins": 17.1,
    "videoType": "long",
    "thumbnail": "https://i.ytimg.com/vi/3ryID_SwU5E/hqdefault.jpg",
    "scrapedAt": "2026-03-31T09:00:00"
  }
]
```

### Step 6: Summary printout

After saving, print a quick summary:

```
Watch history scraped: 112 videos

By type:
  Long videos : 112 (100%)
  Shorts      :   0   (0%)

Top channels:
  1. Inglês Essencial    — 23 videos
  2. Peekaboo Kidz       — 21 videos
  3. Jordan Matter       —  6 videos

Output: user_docs/watch_history_2026-03-31.json

Next: run '/youtube-kids-audit --output report' to analyze content.
```

---

## Implementation checklist

**Scrape watch history (CDP approach — no API key required)**
- [x] Detect Chrome on port 9222; offer to launch if missing (Step 0)
- [x] Poll for sign-in via tab title check
- [x] Navigate to `youtube.com/feed/history` in headed Chrome
- [x] Infinite-scroll to load all history items
- [x] Extract via CDP: `div[class*="content-id-"]` → title, channel, duration, thumbnail
- [x] Parse `MM:SS` / `H:MM:SS` duration → decimal minutes; classify short (≤60s) vs long
- [x] Write `user_docs/watch_history_<date>.json`
- [x] Print summary: total videos, type breakdown, top channels

**Analysis (next phase)**
- [ ] Deduplicate by channel; compute per-channel total watch minutes
- [ ] Classify each channel with Claude (batch prompt, 20 channels per call)
- [ ] Generate markdown report: top channels table, concern flags, recommendations
- [ ] Parent approval gate for `--output actions`
- [ ] Execute approved Family Link actions via browser automation
- [ ] Update `family-state.json > youtube.approved_channels / blocked_channels`

## Privacy notes

- Watch history data stays local — never sent to third-party APIs beyond YouTube Data API (channel metadata only)
- Do not log individual video titles in output files — use channel-level aggregation
- Family Link credentials: Tier 1 only (attach to existing Chrome) — never store in plaintext
