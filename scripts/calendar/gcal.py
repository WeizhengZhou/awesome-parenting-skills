#!/usr/bin/env python3
"""
gcal.py — Pull Google Calendar ICS feeds and render a markdown or HTML calendar view.

Usage:
    python3 scripts/calendar/gcal.py                          # next 7 days, markdown
    python3 scripts/calendar/gcal.py --days 14               # next 14 days
    python3 scripts/calendar/gcal.py --start 2026-04-07      # specific start date
    python3 scripts/calendar/gcal.py --view day              # day agenda only
    python3 scripts/calendar/gcal.py --view week             # week grid only
    python3 scripts/calendar/gcal.py --format html           # HTML output for email embedding
    python3 scripts/calendar/gcal.py --days 7 --save         # save to user_docs/calendar/

Reads all *_CALENDAR_ICS keys from .env automatically.
Multiple calendars are merged and icon-tagged by source.
"""

import argparse
import os
import re
import sys
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path

# ── Project root & .env ────────────────────────────────────────────────────────

ROOT = Path(__file__).parent.parent.parent


def load_env() -> dict:
    env = {}
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    env.update({k: v for k, v in os.environ.items() if k not in env})
    return env


# ── ICS fetching ───────────────────────────────────────────────────────────────

def fetch_ics(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "CalendarScript/1.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read().decode("utf-8", errors="replace")


# ── ICS parsing ────────────────────────────────────────────────────────────────

def _unfold(ics: str) -> str:
    """Unfold RFC 5545 line continuations."""
    return re.sub(r"\r?\n[ \t]", "", ics)


def _field(block: str, name: str) -> str:
    m = re.search(r"^" + name + r"(?:;[^\r\n:]+)?:([^\r\n]+)", block, re.MULTILINE)
    return m.group(1).strip() if m else ""


def _strip_html_tags(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    return re.sub(r"\s+", " ", text).strip()


def clean_description(raw: str) -> str:
    """Strip HTML tags, Google Meet boilerplate, dial-in numbers, and bare meet URLs.
    Returns a short plain-text note, or empty string if nothing meaningful remains."""
    text = _strip_html_tags(raw.replace("\\n", " "))
    # Remove full https:// URLs
    text = re.sub(r"https?://\S+", "", text)
    # Remove bare google.com paths (meet codes, support links, etc.)
    text = re.sub(r"\b(meet|support|calendar)\.google\.com\S*", "", text)
    text = re.sub(r"google\.com/\S+", "", text)
    # Remove Meet/conferencing sentences
    text = re.sub(r"Join with Google Meet.*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"Learn more about Meet.*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"Or dial:.*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\+\d[\d\s\-()]+PIN:[\d#]+", "", text)
    text = re.sub(r"More phone numbers?\S*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"meet/[a-z]{3}-[a-z]{4}-[a-z]{3}\S*", "", text, flags=re.IGNORECASE)
    # Unescape ICS escapes
    text = re.sub(r"\\,", ",", text)
    text = re.sub(r"\\;", ";", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text[:120] + "…" if len(text) > 120 else text


def parse_dt(raw: str):
    """Return (datetime, is_all_day). Returns (None, False) on failure."""
    raw = re.sub(r"^TZID=[^:]+:", "", raw)
    raw = raw.replace("Z", "").replace("-", "").replace(":", "")
    try:
        if len(raw) == 8:
            return datetime.strptime(raw, "%Y%m%d"), True
        return datetime.strptime(raw[:15], "%Y%m%dT%H%M%S"), False
    except ValueError:
        return None, False


WEEKDAY_IDX = {"MO": 0, "TU": 1, "WE": 2, "TH": 3, "FR": 4, "SA": 5, "SU": 6}


def expand_rrule(dt_start: datetime, rrule: str, window_start: datetime, window_end: datetime):
    """Yield occurrence datetimes within [window_start, window_end]."""
    freq_m   = re.search(r"FREQ=(\w+)",     rrule)
    int_m    = re.search(r"INTERVAL=(\d+)", rrule)
    until_m  = re.search(r"UNTIL=(\w+)",   rrule)
    count_m  = re.search(r"COUNT=(\d+)",   rrule)
    byday_m  = re.search(r"BYDAY=([^;]+)", rrule)

    freq      = freq_m.group(1)             if freq_m   else "WEEKLY"
    interval  = int(int_m.group(1))         if int_m    else 1
    until     = parse_dt(until_m.group(1))[0] if until_m else None
    max_count = int(count_m.group(1))       if count_m  else 500

    byday_days = set()
    if byday_m:
        for token in byday_m.group(1).split(","):
            token = token.strip()[-2:]
            if token in WEEKDAY_IDX:
                byday_days.add(WEEKDAY_IDX[token])

    ceil  = min(until, window_end) if until else window_end
    cur   = dt_start
    count = 0

    if freq == "DAILY":
        step = timedelta(days=interval)
        while cur <= ceil and count < max_count:
            if cur >= window_start:
                yield cur
            cur += step
            count += 1

    elif freq == "WEEKLY":
        if byday_days:
            week_start = cur - timedelta(days=cur.weekday())
            while week_start <= ceil and count < max_count:
                for wd in sorted(byday_days):
                    occ = week_start + timedelta(days=wd)
                    occ = occ.replace(hour=cur.hour, minute=cur.minute, second=cur.second)
                    if window_start <= occ <= ceil:
                        yield occ
                        count += 1
                week_start += timedelta(weeks=interval)
        else:
            step = timedelta(weeks=interval)
            while cur <= ceil and count < max_count:
                if cur >= window_start:
                    yield cur
                cur += step
                count += 1

    elif freq == "MONTHLY":
        while cur <= ceil and count < max_count:
            if cur >= window_start:
                yield cur
            month = cur.month - 1 + interval
            year  = cur.year + month // 12
            month = month % 12 + 1
            try:
                cur = cur.replace(year=year, month=month)
            except ValueError:
                break
            count += 1

    elif freq == "YEARLY":
        while cur <= ceil and count < max_count:
            if cur >= window_start:
                yield cur
            try:
                cur = cur.replace(year=cur.year + interval)
            except ValueError:
                break
            count += 1


def parse_ics(ics_text: str, calendar_name: str, window_start: datetime, window_end: datetime):
    """Return list of event dicts within the window."""
    ics_text = _unfold(ics_text)
    events   = []

    for block in re.findall(r"BEGIN:VEVENT(.*?)END:VEVENT", ics_text, re.DOTALL):
        summary     = _field(block, "SUMMARY")
        dtstart_raw = _field(block, "DTSTART")
        dtend_raw   = _field(block, "DTEND")
        location    = _field(block, "LOCATION").replace("\\,", ",").replace("\\n", ", ")
        description = _field(block, "DESCRIPTION")
        rrule       = _field(block, "RRULE")
        status      = _field(block, "STATUS")

        if status == "CANCELLED" or not summary or not dtstart_raw:
            continue

        dt_start, all_day = parse_dt(dtstart_raw)
        dt_end,   _       = parse_dt(dtend_raw)
        if not dt_start:
            continue

        desc = clean_description(description)

        def make_event(occ):
            return {
                "dt":       occ,
                "dt_end":   dt_end,
                "summary":  summary,
                "location": location,
                "desc":     desc,
                "all_day":  all_day,
                "calendar": calendar_name,
            }

        if rrule:
            for occ in expand_rrule(dt_start, rrule, window_start, window_end):
                events.append(make_event(occ))
        elif window_start <= dt_start <= window_end:
            events.append(make_event(dt_start))

    return events


# ── Calendar icons ─────────────────────────────────────────────────────────────

CALENDAR_ICONS = {
    "family":  "🏠",
    "lexi":    "👧",
    "school":  "🏫",
    "sports":  "⚽",
    "work":    "💼",
    "default": "📅",
}

def cal_icon(name: str) -> str:
    name_lower = name.lower()
    for key, icon in CALENDAR_ICONS.items():
        if key in name_lower:
            return icon
    return CALENDAR_ICONS["default"]


# ── Shared helpers ─────────────────────────────────────────────────────────────

def fmt_time(dt: datetime, dt_end=None, all_day=False) -> str:
    if all_day:
        return "All day"
    start = dt.strftime("%-I:%M %p")
    if dt_end and not all_day:
        return f"{start} – {dt_end.strftime('%-I:%M %p')}"
    return start


MAX_PER_CELL = 3  # week grid: max events shown per cell before "+N more"


def _cell_items(items: list) -> list:
    """Return display items for a grid cell, with overflow note appended."""
    shown    = items[:MAX_PER_CELL]
    overflow = len(items) - MAX_PER_CELL
    if overflow > 0:
        shown = shown + [f"+{overflow} more"]
    return shown


# ── Markdown rendering ─────────────────────────────────────────────────────────

def render_week_grid_md(events: list, start: datetime) -> str:
    lines    = []
    week_end = start + timedelta(days=6)
    lines.append(f"## Week of {start.strftime('%b %-d')} – {week_end.strftime('%b %-d, %Y')}\n")

    days = [start + timedelta(days=i) for i in range(7)]

    header = "| Time    | " + " | ".join(d.strftime("**%a %-d**") for d in days) + " |"
    sep    = "|---------|" + "|".join(["-----------"] * 7) + "|"
    lines.append(header)
    lines.append(sep)

    slots:       dict = {d.date(): {} for d in days}
    all_day_row: dict = {d.date(): [] for d in days}

    for ev in events:
        d = ev["dt"].date()
        if d not in slots:
            continue
        if ev["all_day"]:
            all_day_row[d].append(ev["summary"][:18])
        else:
            slots[d].setdefault(ev["dt"].hour, []).append(ev["summary"][:18])

    def md_cell(items):
        return "<br>".join(_cell_items(items)) if items else ""

    lines.append("| *All day* | " + " | ".join(md_cell(all_day_row[d.date()]) for d in days) + " |")

    for hour in range(7, 23):
        cells       = [_cell_items(slots[d.date()].get(hour, [])) for d in days]
        has_content = any(cells)
        if not has_content:
            continue
        label = datetime(2000, 1, 1, hour).strftime("%-I %p")
        lines.append(f"| {label:<7} | " + " | ".join("<br>".join(c) for c in cells) + " |")

    lines.append("")
    return "\n".join(lines)


def render_day_view_md(events: list, start: datetime, end: datetime, multi_cal: bool) -> str:
    lines = []
    days  = (end - start).days + 1

    title_end = (start + timedelta(days=days - 1)).strftime("%b %-d")
    lines.append(f"# 📅 {start.strftime('%b %-d')} – {title_end}, {start.year}")
    lines.append(f"> {len(events)} event{'s' if len(events) != 1 else ''} · {days}-day view\n")

    by_day: dict = {}
    for d in range(days):
        by_day[(start + timedelta(days=d)).date()] = []
    for ev in events:
        by_day.setdefault(ev["dt"].date(), []).append(ev)

    for day, day_events in sorted(by_day.items()):
        today_tag = "  ← today" if day == date.today() else ""
        lines.append("---\n")
        lines.append(f"## {day.strftime('%A, %B %-d')}{today_tag}\n")

        if not day_events:
            lines.append("*No events*\n")
            continue

        day_events.sort(key=lambda e: (not e["all_day"], e["dt"]))

        rows = []
        for ev in day_events:
            time_col = fmt_time(ev["dt"], ev["dt_end"], ev["all_day"])
            icon     = cal_icon(ev["calendar"]) if multi_cal else ""
            name     = f"{icon} {ev['summary']}" if icon else ev["summary"]
            loc      = f"📍 {ev['location']}" if ev["location"] else ""
            detail   = " · ".join(filter(None, [loc, ev["desc"]]))
            rows.append((time_col, name, detail))

        w_time = max(len(r[0]) for r in rows)
        w_name = max(len(r[1]) for r in rows)
        any_detail = any(r[2] for r in rows)

        header = f"| {'Time':<{w_time}} | {'Event':<{w_name}} |"
        sep    = f"|{'-'*(w_time+2)}|{'-'*(w_name+2)}|"
        if any_detail:
            w_detail = max(len(r[2]) for r in rows)
            header  += f" {'Notes':<{w_detail}} |"
            sep     += f"{'-'*(w_detail+2)}|"

        lines.append(header)
        lines.append(sep)
        for time_col, name, detail in rows:
            row = f"| {time_col:<{w_time}} | {name:<{w_name}} |"
            if any_detail:
                lines.append(row + f" {detail:<{w_detail}} |")
            else:
                lines.append(row)
        lines.append("")

    return "\n".join(lines)


# ── HTML rendering ─────────────────────────────────────────────────────────────

_HTML_STYLE = """
<style>
  .gcal { font-family: -apple-system, Arial, sans-serif; font-size: 14px; color: #1a1a1a; }
  .gcal h2 { font-size: 15px; font-weight: 600; color: #2d5a3d; margin: 20px 0 6px; border-bottom: 1px solid #d0e8d8; padding-bottom: 4px; }
  .gcal table { border-collapse: collapse; width: 100%; margin-bottom: 16px; }
  .gcal th { background: #2d5a3d; color: #fff; padding: 6px 10px; font-size: 12px; text-align: left; }
  .gcal td { padding: 5px 10px; border-bottom: 1px solid #eee; vertical-align: top; }
  .gcal tr:hover td { background: #f5faf6; }
  .gcal .time { white-space: nowrap; color: #555; font-size: 13px; width: 140px; }
  .gcal .allday { color: #888; font-style: italic; font-size: 12px; }
  .gcal .note { color: #666; font-size: 12px; }
  .gcal .loc { color: #888; font-size: 12px; }
  /* week grid */
  .gcal .grid th { text-align: center; font-size: 12px; padding: 4px 6px; }
  .gcal .grid td { text-align: left; font-size: 12px; padding: 4px 6px; min-width: 80px; vertical-align: top; }
  .gcal .grid .slot { font-size: 11px; }
  .gcal .grid .overflow { color: #999; font-size: 11px; }
  .gcal .grid .hour { color: #666; font-size: 11px; white-space: nowrap; }
</style>
"""


def _esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def render_week_grid_html(events: list, start: datetime) -> str:
    week_end = start + timedelta(days=6)
    days     = [start + timedelta(days=i) for i in range(7)]

    slots:       dict = {d.date(): {} for d in days}
    all_day_row: dict = {d.date(): [] for d in days}

    for ev in events:
        d = ev["dt"].date()
        if d not in slots:
            continue
        if ev["all_day"]:
            all_day_row[d].append(ev["summary"][:22])
        else:
            slots[d].setdefault(ev["dt"].hour, []).append(ev["summary"][:22])

    def html_cell(items):
        if not items:
            return "&nbsp;"
        shown = _cell_items(items)
        parts = []
        for i, item in enumerate(shown):
            cls = "overflow" if item.startswith("+") else "slot"
            parts.append(f'<span class="{cls}">{_esc(item)}</span>')
        return "<br>".join(parts)

    cols = "".join(f'<th>{_esc(d.strftime("%a %-d"))}</th>' for d in days)
    header = f'<tr><th>Time</th>{cols}</tr>'

    all_day_cells = "".join(f"<td>{html_cell(all_day_row[d.date()])}</td>" for d in days)
    all_day_row_html = f'<tr><td class="hour allday">All day</td>{all_day_cells}</tr>'

    hour_rows = []
    for hour in range(7, 23):
        cells       = [slots[d.date()].get(hour, []) for d in days]
        has_content = any(cells)
        if not has_content:
            continue
        label      = datetime(2000, 1, 1, hour).strftime("%-I %p")
        cell_html  = "".join(f"<td>{html_cell(c)}</td>" for c in cells)
        hour_rows.append(f'<tr><td class="hour">{_esc(label)}</td>{cell_html}</tr>')

    title = f"Week of {start.strftime('%b %-d')} – {week_end.strftime('%b %-d, %Y')}"
    return (
        f'<h2>{_esc(title)}</h2>\n'
        f'<table class="grid">\n{header}\n{all_day_row_html}\n'
        + "\n".join(hour_rows)
        + "\n</table>\n"
    )


def render_day_view_html(events: list, start: datetime, end: datetime, multi_cal: bool) -> str:
    parts = []
    days  = (end - start).days + 1

    title_end = (start + timedelta(days=days - 1)).strftime("%b %-d")
    parts.append(f'<h2>📅 {_esc(start.strftime("%b %-d"))} – {_esc(title_end)}, {start.year}</h2>\n')

    by_day: dict = {}
    for d in range(days):
        by_day[(start + timedelta(days=d)).date()] = []
    for ev in events:
        by_day.setdefault(ev["dt"].date(), []).append(ev)

    for day, day_events in sorted(by_day.items()):
        today_tag = " <small style='color:#888'>← today</small>" if day == date.today() else ""
        parts.append(f'<h2>{_esc(day.strftime("%A, %B %-d"))}{today_tag}</h2>\n')

        if not day_events:
            parts.append('<p style="color:#999;font-style:italic">No events</p>\n')
            continue

        day_events.sort(key=lambda e: (not e["all_day"], e["dt"]))

        rows_html = []
        for ev in day_events:
            time_str = fmt_time(ev["dt"], ev["dt_end"], ev["all_day"])
            time_cls = "allday" if ev["all_day"] else ""
            icon     = (cal_icon(ev["calendar"]) + " ") if multi_cal else ""
            loc_html = f'<br><span class="loc">📍 {_esc(ev["location"])}</span>' if ev["location"] else ""
            note_html = f'<br><span class="note">{_esc(ev["desc"])}</span>' if ev["desc"] else ""
            rows_html.append(
                f'<tr>'
                f'<td class="time {time_cls}">{_esc(time_str)}</td>'
                f'<td>{_esc(icon + ev["summary"])}{loc_html}{note_html}</td>'
                f'</tr>'
            )

        parts.append(
            '<table>\n'
            '<tr><th>Time</th><th>Event</th></tr>\n'
            + "\n".join(rows_html)
            + "\n</table>\n"
        )

    return "\n".join(parts)


def render_html(events, start, end, view, multi_cal):
    """Full standalone HTML document for calendar output."""
    days    = (end - start).days + 1
    content = []

    if view in ("week", "both") and days <= 14:
        week_start = start
        while week_start <= end:
            week_evs = [e for e in events if week_start.date() <= e["dt"].date() <= (week_start + timedelta(days=6)).date()]
            content.append(render_week_grid_html(week_evs, week_start))
            week_start += timedelta(days=7)

    if view in ("day", "both"):
        content.append(render_day_view_html(events, start, end, multi_cal))

    body = "\n".join(content)
    return f'<!DOCTYPE html><html><head><meta charset="utf-8">{_HTML_STYLE}</head><body><div class="gcal">{body}</div></body></html>'


def render_markdown(events, start, end, view, multi_cal):
    parts = []
    days  = (end - start).days + 1

    if view in ("week", "both") and days <= 14:
        week_start = start
        while week_start <= end:
            week_evs = [e for e in events if week_start.date() <= e["dt"].date() <= (week_start + timedelta(days=6)).date()]
            parts.append(render_week_grid_md(week_evs, week_start))
            week_start += timedelta(days=7)
        parts.append("---\n")

    if view in ("day", "both"):
        parts.append(render_day_view_md(events, start, end, multi_cal))

    return "\n".join(parts)


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Pull and render Google Calendar ICS feeds.")
    parser.add_argument("--start",     help="Start date YYYY-MM-DD (default: today)")
    parser.add_argument("--end",       help="End date YYYY-MM-DD")
    parser.add_argument("--days",      type=int, default=7, help="Number of days (default: 7)")
    parser.add_argument("--view",      choices=["day", "week", "both"], default="both",
                        help="Output view: day (agenda), week (grid), both (default)")
    parser.add_argument("--format",    choices=["markdown", "html"], default="markdown",
                        help="Output format: markdown (default) or html (for email embedding)")
    parser.add_argument("--save",      action="store_true", help="Save output to user_docs/calendar/")
    parser.add_argument("--calendars", help="Comma-separated env var names to use (default: all *_CALENDAR_ICS)")
    args = parser.parse_args()

    env = load_env()

    # Date range
    if args.start:
        start = datetime.strptime(args.start, "%Y-%m-%d")
    else:
        start = datetime.combine(date.today(), datetime.min.time())

    if args.end:
        end = datetime.strptime(args.end, "%Y-%m-%d").replace(hour=23, minute=59)
    else:
        end = (start + timedelta(days=args.days - 1)).replace(hour=23, minute=59)

    # Calendar keys
    if args.calendars:
        cal_keys = [k.strip() for k in args.calendars.split(",")]
    else:
        cal_keys = [k for k in env if k.endswith("_CALENDAR_ICS")]

    if not cal_keys:
        print("No calendar ICS URLs found. Add *_CALENDAR_ICS entries to your .env file.", file=sys.stderr)
        sys.exit(1)

    multi_cal = len(cal_keys) > 1

    # Fetch & parse
    all_events = []
    for key in cal_keys:
        url = env.get(key, "")
        if not url or url.startswith("https://..."):
            continue
        cal_name = key.replace("_CALENDAR_ICS", "").replace("_", " ").title()
        try:
            print(f"Fetching {cal_name}…", file=sys.stderr)
            ics_text = fetch_ics(url)
            evs      = parse_ics(ics_text, cal_name, start, end)
            all_events.extend(evs)
            print(f"  → {len(evs)} events in range", file=sys.stderr)
        except Exception as e:
            print(f"  ✗ Failed to fetch {cal_name}: {e}", file=sys.stderr)

    all_events.sort(key=lambda e: (e["dt"].date(), not e["all_day"], e["dt"]))

    # Render
    if args.format == "html":
        output = render_html(all_events, start, end, args.view, multi_cal)
        ext    = "html"
    else:
        output = render_markdown(all_events, start, end, args.view, multi_cal)
        ext    = "md"

    print(output)

    if args.save:
        out_dir = ROOT / "user_docs" / "calendar"
        out_dir.mkdir(parents=True, exist_ok=True)
        slug     = f"{start.strftime('%Y%m%d')}_{end.strftime('%Y%m%d')}_calendar.{ext}"
        out_path = out_dir / slug
        out_path.write_text(output)
        print(f"\nSaved → {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
