#!/usr/bin/env python3
"""
Convert a weekly digest markdown file to a Gmail-friendly HTML email.

Usage:
    python3 scripts/email/digest_to_html.py user_docs/digest/weekly_digest_YYYYMMDD.md

Returns the HTML string on stdout, or writes to --out FILE.
"""

import re
import sys
import argparse
from pathlib import Path

try:
    import markdown
except ImportError:
    sys.exit("Missing dependency: pip install markdown")


# ---------------------------------------------------------------------------
# Inline style helpers
# ---------------------------------------------------------------------------

FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif"

# Brand colors
GREEN       = "#16a34a"   # header bar, primary accent
GREEN_DARK  = "#15803d"   # section headings
GREEN_LIGHT = "#f0fdf4"   # table alt rows, tag bg
RED         = "#dc2626"   # urgent badge
AMBER       = "#d97706"   # upcoming badge
GRAY_BG     = "#f9fafb"   # page + footer bg
GRAY_BORDER = "#e5e7eb"
GRAY_TEXT   = "#6b7280"
DARK_TEXT   = "#111827"


def badge(label: str, color: str, bg: str) -> str:
    return (
        f'<span style="display:inline-block;padding:2px 8px;border-radius:4px;'
        f'font-size:11px;font-weight:700;letter-spacing:.5px;'
        f'background:{bg};color:{color};text-transform:uppercase">{label}</span>'
    )


def urgency_badge(deadline: str) -> str:
    """Return a colored badge based on deadline text."""
    d = deadline.lower()
    if "today" in d:
        return badge("TODAY", "#fff", RED)
    if "tomorrow" in d:
        return badge("TOMORROW", "#fff", AMBER)
    return badge(deadline, GREEN_DARK, GREEN_LIGHT)


def apply_inline_styles(html: str) -> str:
    """Walk the HTML and inject inline styles Gmail will respect."""

    # ── headings ──────────────────────────────────────────────────────────
    html = html.replace(
        "<h2>",
        f'<h2 style="color:{GREEN_DARK};font-size:15px;font-weight:700;'
        f'margin:28px 0 8px;text-transform:uppercase;letter-spacing:.5px;'
        f'border-bottom:2px solid {GREEN_LIGHT};padding-bottom:6px">',
    )
    html = html.replace(
        "<h3>",
        f'<h3 style="font-size:14px;color:{DARK_TEXT};font-weight:600;margin:16px 0 6px">',
    )

    # ── paragraphs ────────────────────────────────────────────────────────
    html = html.replace(
        "<p>",
        f'<p style="margin:6px 0;font-size:14px;line-height:1.6;color:{DARK_TEXT}">',
    )

    # ── horizontal rules ──────────────────────────────────────────────────
    html = re.sub(
        r"<hr\s*/?>",
        f'<hr style="border:none;border-top:1px solid {GRAY_BORDER};margin:20px 0">',
        html,
    )

    # ── tables ────────────────────────────────────────────────────────────
    html = html.replace(
        "<table>",
        '<table style="border-collapse:collapse;width:100%;font-size:13px;margin:10px 0">',
    )
    html = html.replace(
        "<thead>",
        f'<thead style="background:{GREEN_LIGHT}">',
    )
    html = html.replace(
        "<th>",
        f'<th style="text-align:left;padding:8px 10px;font-weight:600;'
        f'color:{GREEN_DARK};border-bottom:2px solid {GRAY_BORDER}">',
    )
    # Zebra-stripe <tr> in tbody via regex (alternating)
    def stripe_rows(m):
        rows = re.findall(r"<tr>(.*?)</tr>", m.group(1), re.DOTALL)
        out = []
        for i, row in enumerate(rows):
            bg = GREEN_LIGHT if i % 2 == 0 else "#ffffff"
            row_styled = row.replace(
                "<td>",
                f'<td style="padding:7px 10px;border-bottom:1px solid {GRAY_BORDER};'
                f'font-size:13px;color:{DARK_TEXT};background:{bg}">',
            )
            out.append(f"<tr>{row_styled}</tr>")
        return "<tbody>" + "".join(out) + "</tbody>"

    html = re.sub(r"<tbody>(.*?)</tbody>", stripe_rows, html, flags=re.DOTALL)

    # ── lists ─────────────────────────────────────────────────────────────
    html = html.replace("<ul>", f'<ul style="padding-left:18px;margin:6px 0">')
    html = html.replace("<ol>", f'<ol style="padding-left:18px;margin:6px 0">')
    html = html.replace(
        "<li>",
        f'<li style="margin-bottom:5px;font-size:14px;line-height:1.5;color:{DARK_TEXT}">',
    )

    # ── bold ──────────────────────────────────────────────────────────────
    html = html.replace("<strong>", f'<strong style="color:{DARK_TEXT};font-weight:700">')

    # ── links ─────────────────────────────────────────────────────────────
    html = re.sub(
        r'<a href="([^"]+)">',
        lambda m: f'<a href="{m.group(1)}" style="color:{GREEN};text-decoration:none">',
        html,
    )

    return html


# ---------------------------------------------------------------------------
# Action-item badge injection
# ---------------------------------------------------------------------------

def inject_action_badges(html: str) -> str:
    """
    Find list items that start with **DEADLINE** — **action**
    and wrap the deadline in a colored badge.
    Pattern: <li ...><strong>...deadline text...</strong>
    """
    def replace_action(m):
        full_li = m.group(0)
        deadline = m.group(1).strip()
        badge_html = urgency_badge(deadline)
        return full_li.replace(
            f"<strong>{deadline}</strong>",
            badge_html,
            1,
        )

    # Match <li ...><strong>DEADLINE TEXT</strong>
    return re.sub(
        r'(<li[^>]*>)\s*<strong[^>]*>(.*?)</strong>',
        replace_action,
        html,
    )


# ---------------------------------------------------------------------------
# Full email wrapper
# ---------------------------------------------------------------------------

def wrap_email(body_html: str, week_label: str, child_names: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:24px 16px;background:{GRAY_BG};font-family:{FONT}">

  <div style="max-width:600px;margin:0 auto;background:#ffffff;
              border-radius:10px;border:1px solid {GRAY_BORDER};overflow:hidden;
              box-shadow:0 1px 4px rgba(0,0,0,.06)">

    <!-- Header -->
    <div style="background:{GREEN};padding:22px 28px">
      <p style="color:rgba(255,255,255,.85);margin:0 0 2px;
                font-size:11px;font-weight:600;letter-spacing:.8px;
                text-transform:uppercase">Family Weekly Digest</p>
      <h1 style="color:#fff;margin:0;font-size:20px;font-weight:700;line-height:1.3">
        {week_label}
      </h1>
      <p style="color:rgba(255,255,255,.8);margin:6px 0 0;font-size:13px">
        {child_names}
      </p>
    </div>

    <!-- Body -->
    <div style="padding:24px 28px">
      {body_html}
    </div>

    <!-- Footer -->
    <div style="padding:14px 28px;background:{GRAY_BG};
                border-top:1px solid {GRAY_BORDER};
                font-size:11px;color:{GRAY_TEXT};text-align:center">
      Sent by your parenting agent &nbsp;·&nbsp;
      <a href="https://github.com/awesome-parenting-skills"
         style="color:{GREEN};text-decoration:none">awesome-parenting-skills</a>
    </div>

  </div>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def convert(md_path: Path) -> tuple[str, str]:
    """Return (plain_text, html_email) from a digest markdown file."""
    raw = md_path.read_text()

    # Strip YAML frontmatter
    if raw.startswith("---"):
        end = raw.find("---", 3)
        frontmatter = raw[3:end]
        body_md = raw[end + 3:].strip()
    else:
        frontmatter = ""
        body_md = raw.strip()

    # Parse frontmatter for metadata
    week_of = ""
    children = ""
    for line in frontmatter.splitlines():
        if line.startswith("week_of:"):
            week_of = line.split(":", 1)[1].strip()
        if line.startswith("children:"):
            children = line.split(":", 1)[1].strip().strip("[]")

    # Format header label
    if week_of:
        from datetime import datetime
        try:
            dt = datetime.strptime(week_of, "%Y-%m-%d")
            week_label = "Week of " + dt.strftime("%B %-d, %Y")
        except ValueError:
            week_label = "Week of " + week_of
    else:
        week_label = "Weekly Digest"

    child_label = children if children else "Family"

    # Convert markdown → HTML
    body_html = markdown.markdown(body_md, extensions=["tables", "smarty"])

    # Apply styles
    body_html = apply_inline_styles(body_html)
    body_html = inject_action_badges(body_html)

    # Wrap in full email template
    html_email = wrap_email(body_html, week_label, child_label)
    plain_text = body_md  # plain fallback

    return plain_text, html_email


def main():
    parser = argparse.ArgumentParser(description="Convert digest markdown to HTML email")
    parser.add_argument("file", help="Path to weekly_digest_YYYYMMDD.md")
    parser.add_argument("--out", help="Write HTML to this file instead of stdout")
    args = parser.parse_args()

    plain, html = convert(Path(args.file))

    if args.out:
        Path(args.out).write_text(html)
        print(f"Written to {args.out}")
    else:
        print(html)


if __name__ == "__main__":
    main()
