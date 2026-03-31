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

## Implementation checklist

- [ ] Browser automation: sign into `myactivity.google.com` (Tier 1 — attach to existing Chrome)
- [ ] Extract watch history (video IDs, watch duration, timestamps) for `--days` window
- [ ] Deduplicate by channel; compute per-channel total watch minutes
- [ ] Fetch channel metadata via YouTube Data API v3 (needs `YOUTUBE_API_KEY`)
- [ ] Classify each channel with Claude (batch prompt, 20 channels per call)
- [ ] Generate markdown report: top channels table, concern flags, recommendations
- [ ] Parent approval gate for `--output actions`
- [ ] Execute approved Family Link actions via browser automation
- [ ] Update `family-state.json > youtube.approved_channels / blocked_channels`

## Privacy notes

- Watch history data stays local — never sent to third-party APIs beyond YouTube Data API (channel metadata only)
- Do not log individual video titles in output files — use channel-level aggregation
- Family Link credentials: Tier 1 only (attach to existing Chrome) — never store in plaintext
