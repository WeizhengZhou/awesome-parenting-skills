#!/usr/bin/env python3
"""
AgentMail CLI — send, read, list, and reply via the AgentMail API.

Usage:
    python3 scripts/email/agentmail.py send   --from INBOX --to ADDR --subject S --body B
    python3 scripts/email/agentmail.py read   --inbox INBOX --id MSG_ID
    python3 scripts/email/agentmail.py list   --inbox INBOX [--limit 20] [--since 24h]
    python3 scripts/email/agentmail.py reply  --inbox INBOX --thread-id T --to ADDR --body B
    python3 scripts/email/agentmail.py list-inboxes

Credential loading (first match wins):
    1. AGENTMAIL_API_KEY env var
    2. .env file in the project root
    3. macOS Keychain: security find-generic-password -s agentmail -w
"""

import argparse
import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path



BASE_URL = "https://api.agentmail.to"
PROJECT_ROOT = Path(__file__).parent.parent


# ---------------------------------------------------------------------------
# Credential loading
# ---------------------------------------------------------------------------

def load_api_key() -> str:
    # 1. Environment variable
    key = os.environ.get("AGENTMAIL_API_KEY", "")
    if key and not key.startswith("your_"):
        return key

    # 2. .env file
    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("AGENTMAIL_API_KEY="):
                key = line.split("=", 1)[1].strip()
                if key and not key.startswith("your_"):
                    return key

    # 3. macOS Keychain
    try:
        result = subprocess.run(
            ["security", "find-generic-password", "-s", "agentmail", "-w"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            key = result.stdout.strip()
            if key:
                return key
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    sys.exit(
        "Error: AGENTMAIL_API_KEY not found.\n"
        "Copy .env_template to .env and add your key, or set the env var."
    )


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _encode_inbox(inbox_id: str) -> str:
    return urllib.parse.quote(inbox_id, safe="")


def _request(method: str, path: str, api_key: str, body: dict | None = None) -> dict:
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode() if body is not None else None
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode(errors="replace")
        try:
            err = json.loads(error_body)
            msg = err.get("message") or err.get("error") or error_body
        except json.JSONDecodeError:
            msg = error_body
        sys.exit(f"API error {e.code}: {msg}")


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------

def cmd_send(args, api_key: str):
    inbox_enc = _encode_inbox(args.from_inbox)
    payload = {
        "to": [args.to],
        "subject": args.subject,
        "text": args.body,
    }
    if args.html:
        payload["html"] = Path(args.html).read_text() if Path(args.html).exists() else args.html
    result = _request("POST", f"/v0/inboxes/{inbox_enc}/messages/send", api_key, payload)
    print(json.dumps(result, indent=2))


def cmd_read(args, api_key: str):
    inbox_enc = _encode_inbox(args.inbox)
    msg_enc = urllib.parse.quote(args.id, safe="")
    result = _request("GET", f"/v0/inboxes/{inbox_enc}/messages/{msg_enc}", api_key)
    print(json.dumps(result, indent=2))


def cmd_list(args, api_key: str):
    inbox_enc = _encode_inbox(args.inbox)
    params = f"?limit={args.limit}"
    result = _request("GET", f"/v0/inboxes/{inbox_enc}/messages{params}", api_key)
    messages = result.get("messages", result) if isinstance(result, dict) else result

    # --since filter
    if args.since:
        cutoff = _parse_since(args.since)
        messages = [
            m for m in messages
            if _parse_ts(m.get("created_at", "")) >= cutoff
        ]

    if args.output == "json":
        print(json.dumps(messages, indent=2))
    else:
        print(f"{'#':<4} {'Date':<18} {'From':<32} {'Subject'}")
        print("-" * 80)
        for i, m in enumerate(messages, 1):
            ts = m.get("created_at", "")[:16].replace("T", " ")
            frm = (m.get("from") or "")[:30]
            subj = (m.get("subject") or "")[:40]
            print(f"{i:<4} {ts:<18} {frm:<32} {subj}")


def cmd_reply(args, api_key: str):
    inbox_enc = _encode_inbox(args.inbox)
    payload = {
        "to": [args.to],
        "subject": f"Re: {args.subject}" if args.subject else "",
        "text": args.body,
    }
    if args.thread_id:
        payload["thread_id"] = args.thread_id
    result = _request("POST", f"/v0/inboxes/{inbox_enc}/messages/send", api_key, payload)
    print(json.dumps(result, indent=2))


def cmd_get_attachment(args, api_key: str):
    inbox_enc = _encode_inbox(args.inbox)
    msg_enc = urllib.parse.quote(args.id, safe="")
    att_enc = urllib.parse.quote(args.attachment_id, safe="")
    meta = _request("GET", f"/v0/inboxes/{inbox_enc}/messages/{msg_enc}/attachments/{att_enc}", api_key)

    download_url = meta.get("download_url")
    if not download_url:
        sys.exit(f"No download_url in response: {meta}")

    req = urllib.request.Request(download_url, headers={"Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()

    out_path = Path(args.out) if args.out else Path(meta.get("filename", "attachment"))
    out_path.write_bytes(data)
    print(f"Saved {len(data)} bytes → {out_path}")


def cmd_list_inboxes(args, api_key: str):
    result = _request("GET", "/v0/inboxes", api_key)
    if args.output == "json":
        print(json.dumps(result, indent=2))
    else:
        inboxes = result if isinstance(result, list) else result.get("inboxes", [result])
        for inbox in inboxes:
            inbox_id = inbox.get("address") or inbox.get("inbox_id") or inbox.get("id", "")
            name = inbox.get("display_name") or inbox.get("name", "")
            created = (inbox.get("created_at") or "")[:10]
            print(f"{inbox_id}  {name}  (created {created})")


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _parse_since(since: str) -> datetime:
    since = since.strip()
    now = datetime.now(timezone.utc)
    if since.endswith("h"):
        return now - timedelta(hours=int(since[:-1]))
    if since.endswith("d"):
        return now - timedelta(days=int(since[:-1]))
    # ISO date
    return datetime.fromisoformat(since).replace(tzinfo=timezone.utc)


def _parse_ts(ts: str) -> datetime:
    if not ts:
        return datetime.min.replace(tzinfo=timezone.utc)
    ts = ts.rstrip("Z")
    try:
        return datetime.fromisoformat(ts).replace(tzinfo=timezone.utc)
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        prog="agentmail.py",
        description="AgentMail CLI — send, read, list, reply",
    )
    parser.add_argument("--output", choices=["json", "text"], default="text",
                        help="Output format (default: text)")
    sub = parser.add_subparsers(dest="action", required=True)

    # send
    p_send = sub.add_parser("send", help="Send a new message")
    p_send.add_argument("--from", dest="from_inbox", required=True,
                        help="Sending inbox (e.g. yourname@agentmail.to)")
    p_send.add_argument("--to", required=True, help="Recipient email address")
    p_send.add_argument("--subject", required=True)
    p_send.add_argument("--body", required=True)
    p_send.add_argument("--html", default=None,
                        help="HTML body: file path or raw HTML string (optional)")

    # read
    p_read = sub.add_parser("read", help="Read a single message by ID")
    p_read.add_argument("--inbox", required=True)
    p_read.add_argument("--id", required=True, help="Message ID")

    # list
    p_list = sub.add_parser("list", help="List recent messages")
    p_list.add_argument("--inbox", required=True)
    p_list.add_argument("--limit", type=int, default=20)
    p_list.add_argument("--since", default=None,
                        help="e.g. 24h, 7d, or 2026-03-28")

    # reply
    p_reply = sub.add_parser("reply", help="Reply to a thread")
    p_reply.add_argument("--inbox", required=True)
    p_reply.add_argument("--to", required=True, help="Recipient email address")
    p_reply.add_argument("--body", required=True)
    p_reply.add_argument("--thread-id", dest="thread_id", default=None)
    p_reply.add_argument("--subject", default="", help="Original subject (Re: prepended)")

    # get-attachment
    p_att = sub.add_parser("get-attachment", help="Download a message attachment by ID")
    p_att.add_argument("--inbox", required=True)
    p_att.add_argument("--id", required=True, help="Message ID")
    p_att.add_argument("--attachment-id", dest="attachment_id", required=True)
    p_att.add_argument("--out", default=None, help="Output file path (default: original filename)")

    # list-inboxes
    sub.add_parser("list-inboxes", help="List all configured inboxes")

    args = parser.parse_args()
    api_key = load_api_key()

    dispatch = {
        "send": cmd_send,
        "read": cmd_read,
        "list": cmd_list,
        "reply": cmd_reply,
        "get-attachment": cmd_get_attachment,
        "list-inboxes": cmd_list_inboxes,
    }
    dispatch[args.action](args, api_key)


if __name__ == "__main__":
    main()
