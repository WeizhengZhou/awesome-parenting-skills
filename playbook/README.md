# Parenting Assistant — Setup Playbooks

Step-by-step guides for parents setting up this assistant. You don't need a technical background. Each playbook tells you exactly what to do, what to expect, and what can go wrong.

---

## What does this assistant actually do?

It helps you:
- Track what your child is reading and watching
- Get book and media recommendations matched to their interests and school curriculum
- Receive a weekly summary of what they borrowed from the library and watched on YouTube
- Get school newsletter updates automatically processed into action items

**All your personal data stays on your own computer.** Nothing is stored in the cloud unless you explicitly set up email (Playbook 2).

---

## Playbooks at a glance

| # | Playbook | What you unlock | Setup difficulty |
|---|----------|----------------|-----------------|
| **0** | [Basic Setup](00-basic-setup.md) | Book recommendations, discussion questions, reading plans — all from files on your computer | ⭐ Easy |
| **1** | [Chrome Browser Setup](01-chrome-mcp.md) | Automatic YouTube history scraping and library record fetching | ⭐⭐ Moderate |
| **2** | [Email Setup](02-agentmail.md) | School email forwarding + weekly digest sent to your inbox | ⭐⭐ Moderate |
| **3** | [Scheduled Jobs](03-cron-jobs.md) | Everything runs automatically on Sunday — no manual trigger needed | ⭐⭐⭐ Advanced |
| **4** | [Password Safety](04-password-safety.md) | Store library and school passwords safely before connecting anything | ⭐ Easy |

---

## Where to start

**If you just want to try it with no setup risk:**
→ Do **Playbook 0** only. You'll have useful tools in under 30 minutes.

**If you want the full weekly automation:**
→ Follow in order: **0 → 4 → 1 → 2 → 3**
(Do Playbook 4 before 1 and 2 so passwords are stored safely from the start)

---

## You don't have to do everything

Each playbook adds more automation but also more complexity. Most parents find Playbooks 0 + 2 (manual + email) are enough and skip the Chrome automation entirely.

```
Minimum useful setup:    Playbook 0
Add email digest:        Playbook 0 + 2
Full automation:         Playbooks 0 + 4 + 1 + 2 + 3
```
