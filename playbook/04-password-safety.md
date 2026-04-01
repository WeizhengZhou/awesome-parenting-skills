# Playbook 4 — Password Safety

**What you get:** A safe way to store your library PIN, school portal password, and API keys — so automation can use them without you storing them in plain text.

**Time:** 20 minutes
**Prerequisites:** None. Do this **before** Playbook 1 or 2.

---

## At a glance — what you do vs. what the agent does

| Section | You need to... | Agent does |
|---------|---------------|-----------|
| Core rule | Read it — it's one paragraph | — |
| Change library PIN | Log in to library website, change PIN to something unique | — |
| Store credentials in Keychain | Run `security add-generic-password` for each credential | — |
| Set up `.env` file | Copy template, paste in values, run `chmod 600` | — |
| Security checklist | Run through once (3 commands) | — |
| Privacy audit before commits | Type `/privacy-audit` | ✅ Scans all files for leaked credentials, API keys, personal emails |
| Ongoing credential safety | Nothing — just don't reuse passwords | ✅ Privacy audit skill flags any new issues automatically |

**TL;DR:** This playbook is almost entirely things only you can do — setting passwords and storing them. The agent's only role is the `/privacy-audit` scan. Budget 20 minutes and do it once before anything else.

---

## The one rule that matters most

**Use a password for your library that you use nowhere else.**

Library PINs are often just 4 digits — the same kind of number people use for ATM PINs, phone lock screens, and other things. If your library PIN is the same as something more important, change it now before you store it anywhere.

The same goes for school portals. These systems often have low security requirements (short passwords, no two-factor). Use something unique to each service.

> **Good:** A random password like `blue-mango-47` that you've never used before.
> **Bad:** Your Gmail password, your bank PIN, your child's birthday, "1234".

You won't be typing these passwords — the automation types them. So it doesn't matter if they're hard to remember.

---

## Where to store credentials

### Option A: macOS Keychain (most secure)

Keychain is built into every Mac. It's the same encrypted vault that Safari uses to save website passwords. Credentials stored here are:
- Encrypted (can't be read without your Mac login)
- Never visible in command history
- Safe from accidental git commits (they're not in any file)

**Store a password in Keychain:**

```bash
# The -w flag means "ask me for the password" — it won't show on screen
security add-generic-password -s "smcl-library" -a "your-library-username" -w
```

After running this, you'll see a prompt: `password data for new item:` — type your library PIN and press Enter. Nothing will appear on screen as you type (this is normal).

The `-s` part is a name you make up — use something descriptive like:
- `smcl-library` for your library
- `sacred-heart-portal` for your school portal
- `agentmail-key` for your AgentMail API key

**Check it saved correctly:**
```bash
security find-generic-password -s "smcl-library" -w
# Should print your PIN
```

**Update a stored password:**
```bash
# Delete the old one, then add again
security delete-generic-password -s "smcl-library" -a "your-library-username"
security add-generic-password -s "smcl-library" -a "your-library-username" -w
```

---

### Option B: `.env` file (acceptable for low-stakes services)

The `.env` file in this project is excluded from git — it will never be uploaded to GitHub. It's a plain text file readable by anyone with access to your Mac account, but it's protected from the most common mistake (accidentally publishing credentials to the internet).

**When `.env` is fine:**
- Library PIN (low stakes — see below)
- AgentMail API key (only controls an email inbox you created)

**When to use Keychain instead:**
- School portal passwords (protects your child's records and grades)
- Anything you'd feel uncomfortable about if exposed

**Set up your `.env`:**
```bash
cp .env_template .env        # create it from the template
chmod 600 .env               # make it readable only by you
```

Open `.env` in a text editor and fill in your values:
```
AGENTMAIL_API_KEY=am_us_your_key_here
SMCL_USERNAME=your-library-card-number
SMCL_PASSWORD=your-library-pin
```

**Verify only you can read it:**
```bash
ls -la .env
# Should show: -rw------- 1 yourname ...
# The "rw-------" means only you can read or write it
```

---

## Why library PINs are lower risk

Most US library systems use 4-digit PINs. This is a known low-security design — it's built for convenience at a self-checkout kiosk, not to protect sensitive data.

The realistic worst case if your library account is compromised:
- Someone checks out books under your name
- You get a fine for items not returned
- You'd see this immediately in your account

This is why storing the library PIN in `.env` is reasonable — as long as the PIN is **unique to your library** and not reused elsewhere.

**How to change your library PIN** (recommended before storing it):
- Log in to your library's website
- Go to Account → Settings or My Account → Change PIN
- Set something new that you don't use anywhere else

---

## Credential summary: what goes where

| Credential | Recommended storage | Why |
|-----------|--------------------|----|
| Library card PIN | `.env` (use a unique PIN) | Low stakes — only controls library account |
| AgentMail API key | `.env` | Low stakes — only controls an email inbox you created |
| School portal password | Keychain | Protects child's grades and records |
| Google / Apple password | **Not in this project** | Too high-stakes — don't automate these |
| Bank / financial passwords | **Not in this project** | Never |

---

## Quick security checklist

Run through this before connecting any accounts:

```bash
# 1. Check .env exists and has correct permissions
ls -la .env
# Should show: -rw------- (if not, run: chmod 600 .env)

# 2. Check .env is not tracked by git
git status
# .env should NOT appear in the output

# 3. See what credentials are in .env right now
grep -v "^#" .env | grep -v "^$"
```

For each credential you see, confirm:
- [ ] Is this password unique — not used for anything else?
- [ ] Is this the right level of risk for `.env` storage (see table above)?

---

## If you accidentally commit your credentials

If you run `git commit` and realize `.env` was included:

1. **Change the exposed credential immediately** at the service (library website, AgentMail settings, etc.)
2. Remove it from `.env` and store it in Keychain instead
3. The leaked credential is no longer valid — the rotation is the important step, not the git cleanup

If this happened on a public GitHub repo, also:
```bash
# Remove .env from git history (requires git-filter-repo — install with: brew install git-filter-repo)
git filter-repo --path .env --invert-paths
git push --force
```

**Prevention is easier than cleanup.** The `/privacy-audit` skill scans for credentials before you commit. Run it as a habit:
```
/privacy-audit --path . --mode scan --strict
```
