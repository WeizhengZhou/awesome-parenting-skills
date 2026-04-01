---
name: library-history
description: "Fetch San Mateo County Library borrowing history and currently checked-out items via Chrome CDP. Saves to user_docs/library/ for use in reading insights and weekly digest. Usage: /library-history [--child Lexi] [--mode history|checkedout|both]"
tools: Read, Write, Glob, Bash
model: sonnet
metadata:
  requires:
    env: [SMCL_USERNAME, SMCL_PASSWORD]
    mcp: [chrome-devtools-cron]
    os: [macos]
---

You are a library assistant. Log in to San Mateo County Library (BiblioCommons) using
Chrome CDP and retrieve the family's borrowing history and current checkouts. Save results
to `user_docs/library/` for use by other skills (weekly digest, media analysis, etc.).

---

## Step 1: Load credentials

Read from `.env` (or env vars):
```
SMCL_USERNAME   ← library card number
SMCL_PASSWORD   ← PIN
```

Read `user_docs/family_profile.md` for library config:
- `library.url` — base URL (`https://smcl.bibliocommons.com`)
- `library.children` — which card holder(s) to fetch for

---

## Step 2: Open the library catalog

```
mcp: navigate_page → https://smcl.bibliocommons.com/user/login
mcp: wait_for → selector: input[name="user[username]" or similar login field]
```

If a Chrome page is already open and logged in to smcl.bibliocommons.com, reuse it
(check `list_pages` first).

---

## Step 3: Log in

```
mcp: fill → username field → SMCL_USERNAME
mcp: fill → password field → SMCL_PASSWORD
mcp: click → submit / "Sign In" button
mcp: wait_for → URL contains "/user/dashboard" or patron name appears in nav
```

If login fails (error message appears), stop and report the error to the user — do not
retry with wrong credentials.

---

## Step 4: Fetch checked-out items (if --mode checkedout or both)

```
mcp: navigate_page → https://smcl.bibliocommons.com/checkedout
mcp: wait_for → selector: .checked-out-item, or similar list container
mcp: evaluate_script → extract item list
```

Extract per item:
- Title
- Author
- Format (book, ebook, audiobook, DVD, etc.)
- Due date
- Renewals remaining (if shown)

---

## Step 5: Fetch borrowing history (if --mode history or both)

```
mcp: navigate_page → https://smcl.bibliocommons.com/v2/recentlyreturned
mcp: wait_for → "Borrowing History", "items"
```

The page shows a preview with 1 item + "View all Borrowing History (N items)" button.
Click that button to expand, then use the print view to get structured data:

```
mcp: navigate_page → https://smcl.bibliocommons.com/v2/print/recentlyreturned
```

**Important:** The print view opens 50 items at a time with a "Load next 50" button.
Use evaluate_script to load ALL pages AND extract data in one call — do NOT click
"Print these 50" as it opens a print dialog that navigates away.

```javascript
// Load all pages then extract
async () => {
  const delay = ms => new Promise(r => setTimeout(r, ms));
  while (true) {
    const btn = Array.from(document.querySelectorAll('button'))
      .find(b => b.textContent.includes('Load next'));
    if (!btn) break;
    btn.click();
    await delay(2000);
  }
  return document.body.innerText;
}
```

Extract per item from the tab-separated text: Title, Author, Format, Checked Out date.

---

## Step 6: Save output

### Checked-out items
```
user_docs/library/YYYYMMDD_checkedout.md
```

```markdown
---
date: YYYY-MM-DD
library: San Mateo County Library
account: SMCL_USERNAME (redacted — show last 4 only)
---

# Currently Checked Out — [Date]

| Title | Author | Format | Due Date | Renewals |
|-------|--------|--------|----------|---------|
| ...   | ...    | ...    | ...      | ...     |
```

### Borrowing history
```
user_docs/library/YYYYMMDD_borrow_history.md
```

```markdown
---
date: YYYY-MM-DD
library: San Mateo County Library
items_fetched: N
---

# Borrowing History — fetched [Date]

| Title | Author | Format | Returned |
|-------|--------|--------|---------|
| ...   | ...    | ...    | ...     |
```

---

## Step 7: Summarize for the user

After saving, print a brief summary:
```
✅ Checked out: N items (next due: [soonest due date])
✅ Borrowing history: N items saved → user_docs/library/YYYYMMDD_borrow_history.md

Top genres this month: [inferred from titles]
Suggested next: [1–2 book suggestions based on recent reads + kid profile interests]
```

---

## Usage

```
/library-history                    # fetch both checkedout + history
/library-history --mode checkedout  # only what's currently borrowed
/library-history --mode history     # only past borrows
```

---

## File naming convention

```
user_docs/library/
├── YYYYMMDD_checkedout.md       ← currently borrowed items (point-in-time snapshot)
└── YYYYMMDD_borrow_history.md   ← full history up to 100 items
```

Config/credentials: `.env` (gitignored). Never write credentials to any markdown file.

---

## Failure handling

| Problem | Action |
|---------|--------|
| Login fails | Report error; check SMCL_USERNAME / SMCL_PASSWORD in .env |
| History page empty | Library history may be disabled — check smcl.bibliocommons.com settings → Privacy → "Save my borrowing history" |
| Chrome not open | Launch Chrome or use an existing session; BiblioCommons requires JS |
| Pagination issues | Extract whatever is visible on first page; note truncation in frontmatter |
