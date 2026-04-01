# Skill: youtube-kids-audit

> **Status: PLACEHOLDER** — Not yet implemented. Contributions welcome.

Browse a child's YouTube / YouTube Kids watch history, analyze content patterns, and recommend channels/videos to add, keep, remove, or block.

## Usage

```
/youtube-kids-audit [--profile <child-name>] [--days 30] [--output report|actions]
```

## Planned capabilities

- Pull watch history from YouTube Kids app or supervised Google account
- Classify each channel/video by: topic, age-appropriateness, educational value, screen-time pattern
- Identify channels the child watches frequently → prompt parent to subscribe or block
- Flag concerning content (excessive violence, inappropriate language, predatory comment patterns, misleading thumbnails)
- Generate a parent-readable report with approve / remove / block recommendations
- Execute approved actions: subscribe to channel, remove from history, add to blocked list in Family Link

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

### Step 0: Choose browser mode

On first run, ask the user:

```
YouTube history requires a Google login. How would you like to open the browser?

  1. Headed Chrome (recommended) — opens a visible browser window you can log in to
  2. Headless Chrome — runs invisibly in the background (requires existing saved session)

Enter 1 or 2 [default: 1]:
```

- **First-time use → always default to headed (option 1).** The user needs to see the browser to complete Google login.
- **Subsequent runs** → if a saved Playwright profile exists at `~/.parenting/profiles/youtube/`, offer headless as the default.
- Save the user's choice to `user_docs/youtube_audit_config.md` so it persists across runs.

### Step 1: Launch browser

**Headed Chrome (option 1):**
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch_persistent_context(
        user_data_dir="~/.parenting/profiles/youtube/",
        headless=False,
        args=["--start-maximized"],
        no_viewport=True,
    )
    page = browser.new_page()
```

**Headless Chrome (option 2):**
```python
    browser = p.chromium.launch_persistent_context(
        user_data_dir="~/.parenting/profiles/youtube/",
        headless=True,
    )
    page = browser.new_page()
```

Using a **persistent context** (`user_data_dir`) means Google login is saved between runs — the user only logs in once.

### Step 2: Navigate and verify login

```python
page.goto("https://myactivity.google.com/product/youtube")
page.wait_for_load_state("networkidle", timeout=15000)

# Check if login is required
if "accounts.google.com" in page.url or page.locator("text=Sign in").count() > 0:
    if headless:
        raise RuntimeError(
            "Not logged in and running headless. Re-run with headed Chrome to log in first."
        )
    print("Please log in to your Google account in the browser window.")
    print("Press Enter here once you are signed in and can see your activity...")
    input()
    page.wait_for_url("*myactivity.google.com*", timeout=60000)
```

### Step 3: Filter by date range

Navigate to YouTube history with the correct date filter:

```python
from datetime import datetime, timedelta

cutoff = datetime.now() - timedelta(days=N_DAYS)
cutoff_str = cutoff.strftime("%Y%m%d")  # e.g. 20260101

# myactivity.google.com supports date range via URL params
url = (
    f"https://myactivity.google.com/product/youtube"
    f"?hl=en&startTime={cutoff_str}&endTime={datetime.now().strftime('%Y%m%d')}"
)
page.goto(url)
page.wait_for_load_state("networkidle", timeout=15000)
```

### Step 4: Scroll and extract history items

YouTube activity is rendered in an infinite-scroll list. Scroll until no new items load or the oldest visible date is before the cutoff:

```python
import json, re
from datetime import datetime

videos = []
seen_urls = set()
last_height = 0

while True:
    # Extract all visible history items
    items = page.query_selector_all("div[data-ved] a[href*='youtube.com/watch']")
    for item in items:
        href = item.get_attribute("href") or ""
        if not href or href in seen_urls:
            continue
        seen_urls.add(href)

        # Extract video ID
        vid_match = re.search(r"v=([A-Za-z0-9_-]{11})", href)
        if not vid_match:
            continue
        video_id = vid_match.group(1)

        # Title is usually the link text or nearby heading
        title = item.inner_text().strip() or "Unknown"

        # Timestamp — look for adjacent time element
        parent = item.evaluate_handle("el => el.closest('div[data-ved]')")
        time_el = parent.query_selector("span[class*='time'], div[class*='time']")
        watched_at = time_el.inner_text().strip() if time_el else ""

        videos.append({
            "video_id": video_id,
            "title": title,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "watched_at_raw": watched_at,
        })

    # Scroll down
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(1500)

    new_height = page.evaluate("document.body.scrollHeight")
    if new_height == last_height:
        break  # no more content loaded
    last_height = new_height
```

### Step 5: Enrich with YouTube Data API v3

For each unique `video_id`, fetch metadata in batches of 50 (API limit):

```python
import requests, math

API_KEY = load_env("YOUTUBE_API_KEY")  # from .env
BASE = "https://www.googleapis.com/youtube/v3/videos"

def fetch_video_metadata(video_ids: list[str]) -> dict:
    results = {}
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i+50]
        resp = requests.get(BASE, params={
            "key": API_KEY,
            "id": ",".join(batch),
            "part": "snippet,contentDetails,statistics,status",
        })
        for item in resp.json().get("items", []):
            vid_id = item["id"]
            snippet = item.get("snippet", {})
            content = item.get("contentDetails", {})
            stats   = item.get("statistics", {})
            status  = item.get("status", {})

            # Parse ISO 8601 duration → minutes
            duration_iso = content.get("duration", "PT0S")
            duration_mins = parse_iso_duration_to_mins(duration_iso)

            # Classify: Shorts ≤ 1 min, Long > 1 min
            video_type = "short" if duration_mins <= 1 else "long"

            results[vid_id] = {
                "title":          snippet.get("title", ""),
                "description":    snippet.get("description", "")[:500],  # truncate
                "channel_name":   snippet.get("channelTitle", ""),
                "channel_id":     snippet.get("channelId", ""),
                "published_at":   snippet.get("publishedAt", ""),
                "tags":           snippet.get("tags", []),
                "category_id":    snippet.get("categoryId", ""),
                "made_for_kids":  status.get("madeForKids", None),
                "duration_mins":  round(duration_mins, 1),
                "video_type":     video_type,   # "short" | "long"
                "view_count":     int(stats.get("viewCount", 0)),
                "like_count":     int(stats.get("likeCount", 0)),
                "thumbnail_url":  snippet.get("thumbnails", {}).get("medium", {}).get("url", ""),
                "url":            f"https://www.youtube.com/watch?v={vid_id}",
            }
    return results

def parse_iso_duration_to_mins(iso: str) -> float:
    """Convert PT4M13S → 4.22 minutes."""
    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso)
    if not match:
        return 0
    h, m, s = (int(x or 0) for x in match.groups())
    return h * 60 + m + s / 60
```

### Step 6: Merge and write JSON output

```python
# Merge browser-scraped history with API metadata
enriched = []
for v in videos:
    meta = api_results.get(v["video_id"], {})
    enriched.append({
        # Watch event fields (from browser)
        "watched_at": v["watched_at_raw"],
        # Video identity
        "video_id":    v["video_id"],
        "url":         v["url"],
        "title":       meta.get("title") or v["title"],
        # Video metadata (from API)
        "description":    meta.get("description", ""),
        "channel_name":   meta.get("channel_name", ""),
        "channel_id":     meta.get("channel_id", ""),
        "published_at":   meta.get("published_at", ""),
        "tags":           meta.get("tags", []),
        "category_id":    meta.get("category_id", ""),
        "made_for_kids":  meta.get("made_for_kids"),
        "duration_mins":  meta.get("duration_mins", 0),
        "video_type":     meta.get("video_type", "unknown"),  # "short" | "long"
        "view_count":     meta.get("view_count", 0),
        "like_count":     meta.get("like_count", 0),
        "thumbnail_url":  meta.get("thumbnail_url", ""),
    })

# Sort by watched_at descending
enriched.sort(key=lambda x: x["watched_at"], reverse=True)

# Write output
from pathlib import Path
import json
out_path = Path(f"user_docs/watch_history_{child_name}_{datetime.now().strftime('%Y%m%d')}.json")
out_path.parent.mkdir(exist_ok=True)
out_path.write_text(json.dumps({"scraped_at": datetime.now().isoformat(),
                                 "child": child_name,
                                 "days": N_DAYS,
                                 "total_videos": len(enriched),
                                 "videos": enriched}, indent=2))
print(f"Saved {len(enriched)} videos → {out_path}")
```

### Output JSON schema

```json
{
  "scraped_at": "2026-03-31T09:00:00",
  "child": "emma",
  "days": 30,
  "total_videos": 142,
  "videos": [
    {
      "watched_at": "Mar 30, 2026, 4:12 PM",
      "video_id": "dQw4w9WgXcQ",
      "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
      "title": "Example Kids Video",
      "description": "A fun learning video for kids...",
      "channel_name": "SciShow Kids",
      "channel_id": "UCZVhFRrFcSYkMkh5LA9RD2Q",
      "published_at": "2025-06-15T14:00:00Z",
      "tags": ["science", "kids", "learning"],
      "category_id": "27",
      "made_for_kids": true,
      "duration_mins": 5.2,
      "video_type": "long",
      "view_count": 1423000,
      "like_count": 18400,
      "thumbnail_url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/mqdefault.jpg"
    }
  ]
}
```

### Step 7: Summary printout

After saving, print a quick summary:

```
Watch history scraped: 142 videos over last 30 days

By type:
  Long videos : 98 (69%)
  Shorts      : 44 (31%)

Top channels:
  1. SciShow Kids        — 23 videos, avg 6.1 min
  2. Cocomelon           — 18 videos, avg 3.2 min
  3. Blippi               — 14 videos, avg 8.7 min

Output: user_docs/watch_history_emma_20260331.json

Next: run '/youtube-kids-audit --profile emma --output report' to analyze content.
```

---

## Implementation checklist

**Scrape watch history**
- [ ] Prompt user to choose headed vs headless Chrome; save preference to `user_docs/youtube_audit_config.md`
- [ ] Launch Playwright persistent context (`~/.parenting/profiles/youtube/`)
- [ ] Detect login wall; pause for manual login if headed; raise error if headless + not logged in
- [ ] Navigate to `myactivity.google.com/product/youtube` with date filter
- [ ] Infinite-scroll and extract video IDs + titles + timestamps
- [ ] Batch-enrich with YouTube Data API v3 (snippet, contentDetails, statistics, status)
- [ ] Parse ISO 8601 duration → decimal minutes; classify as `short` (≤1 min) or `long`
- [ ] Write `user_docs/watch_history_<child>_<date>.json` with full schema
- [ ] Print summary: total videos, type breakdown, top channels

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
