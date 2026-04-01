# Playbook 2 — Email Setup (AgentMail)

**What you get:** Your assistant gets its own email address. You forward school newsletters to it. It reads them, pulls out key dates and reminders, and emails you a weekly summary.

**Time:** 20–30 minutes
**Prerequisites:** Playbook 0 done.
**What you need:** A Gmail account (or similar) that receives school emails.

---

## At a glance — what you do vs. what the agent does

| Section | You need to... | Agent does |
|---------|---------------|-----------|
| How it works | Read once | — |
| Create AgentMail account | Sign up on agentmail.to (~5 min, one-time) | — |
| Add API key to `.env` | Paste one line into a file | — |
| Update config file | Edit two fields (your email + inbox address) | — |
| Set up Gmail forwarding | Add filter in Gmail settings (one-time per sender) | — |
| Add newsletter sources to kid profile | Add school email addresses to profile file | — |
| Test the inbox | Type "check my AgentMail inbox" | ✅ Reads inbox, summarizes what arrived |
| Weekly digest | Type `/weekly-digest --refresh` (or let cron run it) | ✅ Reads emails, extracts dates/action items, sends digest to you |
| Email safety | Read the safety section | ✅ Enforces allowlist — refuses to email unapproved addresses |

**TL;DR for setup:** Sign up for AgentMail (~5 min), add a Gmail filter (~5 min), edit two config files (~5 min). Agent handles everything after that.

---

## How this works (plain English)

1. You create a free inbox at AgentMail (like `your-name@agentmail.to`)
2. In your Gmail, you set up a filter: "any email from school → also send a copy to my AgentMail inbox"
3. Your assistant reads that inbox, extracts what matters, and emails you a digest
4. The school never knows about any of this — you just added a forwarding rule in your own Gmail

The assistant can only **send** email to addresses you approve in a config file. It can never email your child's school, teacher, or anyone else without you explicitly adding them to an allowlist.

---

## Step 1: Create an AgentMail account

1. Go to **https://agentmail.to** and sign up (free tier available)
2. Create an inbox — pick a name like `your-first-name-parenting` or `yourname-assistant`
3. Note down your **inbox address** (e.g., `yourname@agentmail.to`)
4. Go to **Settings → API** and copy your API key (it looks like `am_us_XXXXXXXXXXXXXXXX`)

---

## Step 2: Set up your `.env` file

In your project folder, copy the template if you haven't already:

```bash
cp .env_template .env
```

Open `.env` in a text editor and add your AgentMail API key:

```
AGENTMAIL_API_KEY=am_us_XXXXXXXXXXXXXXXX
```

Save the file.

**Confirm it's not tracked by git** (important — this file contains your key):
```bash
git status
```
The `.env` file should **not** appear in the output. If it does, something is wrong — do not commit it.

---

## Step 3: Update your config file

Open `user_docs/agentmail_config.md` in a text editor. Update the two sections highlighted:

```yaml
human_owners:
  - email: your-email@example.com    # ← YOUR personal email here
    name: Your Name                      # ← your name
    role: primary

inboxes:
  - inbox_id: yourname@agentmail.to     # ← your AgentMail address
    display_name: "Parenting Assistant"
    default: true
```

**Why this matters:** The `human_owners` list is your safety allowlist. The assistant will only ever send email to addresses on this list. It cannot email your child's teacher, school, or anyone else unless you add them here.

---

## Step 4: Set up email forwarding in Gmail

You're going to add a rule in Gmail that sends a copy of school emails to your AgentMail inbox. The school never knows about this — you're just routing your own email.

### Part A: Add AgentMail as a forwarding address (do this once)

1. Open Gmail → click the gear icon (⚙️) → **See all settings**
2. Click the **Forwarding and POP/IMAP** tab
3. Click **Add a forwarding address**
4. Enter your AgentMail address: `yourname@agentmail.to`
5. Click **Next** → **Proceed** → **OK**

**Now check your AgentMail inbox for a confirmation email from Gmail:**
- Log in to https://agentmail.to → your inbox
- Find the email from Google with subject "Gmail Forwarding Confirmation"
- It contains a long confirmation link — click it (or copy the code into Gmail)
- Back in Gmail, you'll see your AgentMail address listed as confirmed

### Part B: Create a filter for school emails

1. Go to Gmail → Settings → **See all settings** → **Filters and Blocked Addresses**
2. Click **Create a new filter**
3. In the **From** field, enter the school's email domain or address:
   - For all emails from a domain: `@school-domain.com`
   - For one specific teacher: `teacher@school.org`
4. Click **Create filter with this search** (blue link at bottom)
5. Check the box **Forward it to:** and select your AgentMail address from the dropdown
6. Click **Create filter**

Repeat Part B for each school sender you want to forward (school-wide emails, classroom teacher, after-school programs, etc.).

> **What gets forwarded:** Only emails that match your filter rule. Your bank, friends, shopping, and everything else is never forwarded.

---

## Step 5: Tell the assistant which emails are school-related

Open `user_docs/kid_profile/your_child_profile.md` and add a `newsletter_sources` section:

```yaml
newsletter_sources:
  - name: "School-wide"
    from_domain: school-domain.com       # matches any email from this domain
  - name: "Classroom teacher"
    from_email: teacher@school.org       # matches this exact address only
```

The weekly digest skill reads this list to know which emails in the AgentMail inbox are relevant.

---

## Step 6: Test it

Wait for the next school email to arrive (or ask someone to send a test email), then in Claude Code:

```
Check for new emails in my AgentMail inbox and summarize what arrived.
```

Or test directly from the terminal:
```bash
python3 scripts/email/agentmail.py list --inbox yourname@agentmail.to --limit 5
```

You should see recent forwarded emails listed. If the inbox is empty, check that:
- The Gmail forwarding address is confirmed (Step 4A)
- The Gmail filter is saved and active (Step 4B)
- A qualifying email has actually arrived since you set up the filter

---

## Step 7: Run the weekly digest

```
/weekly-digest --refresh
```

This scans your AgentMail inbox for emails matching your newsletter sources, extracts the key information, and sends you a digest to your personal email.

On first run, Claude will tell you what it found and what it sent. After this, the digest will be saved to `user_docs/digest/YYYYMMDD_weekly_digest.md` — you can also just read it there.

---

## What the agent will and won't do with email

**It will:**
- Read emails in your AgentMail inbox
- Send summaries and digests to your personal email (from the `human_owners` list)
- Download PDF attachments locally for reading

**It will never:**
- Reply to school emails or send anything to the school
- Send email to anyone not on your `human_owners` allowlist
- Store email content anywhere other than your local `user_docs/` folder and the AgentMail servers

**If the agent tries to email an unapproved address:** It will stop and tell you. To allow it, add the address to `human_owners` in `user_docs/agentmail_config.md`.

---

## Privacy notes

- **What's stored on AgentMail's servers:** The forwarded emails, until you delete them
- **What leaves your computer:** Only emails you chose to forward — not grades, portal data, or anything from Chrome automation
- **To delete your email history:** Log in to agentmail.to and delete messages from the web interface
- **To stop forwarding:** Delete the Gmail filter — forwarding stops immediately, existing emails in AgentMail are unaffected

---

## Troubleshooting

| Problem | What to do |
|---------|-----------|
| AgentMail inbox is empty | Check the Gmail filter is active; check that a qualifying email arrived after setup |
| "Forwarding confirmation" email never arrived | Check your AgentMail inbox (log in to agentmail.to directly) — the code is in the inbox, not sent to Gmail |
| API error when running skills | Open `.env` and check that `AGENTMAIL_API_KEY` is set correctly — no extra spaces or quotes |
| Digest email not arriving | Check that your personal email is correctly set in `human_owners` in `user_docs/agentmail_config.md` |
| Don't want forwarding anymore | Gmail → Settings → Filters → find your school filter → Delete |

---

## Next steps

- **[Playbook 3](03-cron-jobs.md)** — schedule the weekly digest to run automatically without you triggering it
- **[Playbook 4](04-password-safety.md)** — store your API key more securely using macOS Keychain
