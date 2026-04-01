# awesome-parenting-skills

Reusable Claude Code skills, agents, and community data for automating family and parenting workflows.

## Why this exists

Parenting is a full-time job — on top of the actual full-time job.

Between school pickups, homework check-ins, camp registrations, lunch account top-ups, activity signups, and the endless inbox of school newsletters, a meaningful chunk of every week goes to logistics. Not quality time. Not deep connection. Just chores.

We're AI-native parents. We've seen what AI agents can do in software and business workflows — and we believe the same leverage belongs at home. Not to replace parenting, but to replace the parts we're bored of: the repetitive, the administrative, the "I have to remember to do this again" tasks that quietly drain the hours we'd rather spend with our kids.

**The vision:** a shared library of Claude Code skills that any parent can install, run, and contribute to — purpose-built for the workflows that come up every week. Check grades. Find weekend events. Monitor a registration page until it opens. Audit what your kid is watching. Top up the lunch account before it hits zero. Schedule it all to run without you.

**What makes this different:**

- **AI-native from the start** — these aren't web apps or browser extensions. They're agent skills: composable, scriptable, and built to run inside Claude Code, which means they can reason, adapt, and chain together.
- **Serious about delegation** — we want AI to do real work, not just answer questions. That means skills that actually submit forms, send emails, book appointments, and escalate to you only when a human decision is needed.
- **Responsible by design** — your kids' data stays local. Skills are privacy-audited before merging. The repo is public; your `.env` and `user_docs/` are not.
- **Safe and trustable** — AI agents acting on your behalf need guardrails, not just good intentions. We have a factuality checker to reduce hallucination, a privacy auditor to catch PII before it leaks, browser automation with explicit confirmation gates so nothing submits without your approval, and all files stay on your local machine. You stay in control; the agent does the legwork.
- **Shared, not siloed** — the community data (school portals, local event sources, district configs) is curated and contributed by parents in the same cities, the same districts. You don't have to figure out where your city posts rec league signups. Someone already did.
- **Community as a knowledge base** — parenting expertise shouldn't live in one parent's head or a sprawling Google Doc. When a friend asks how to navigate private school applications, the answer shouldn't be a wall of text in iMessage — it should be a skill: structured, reusable, shareable. This repo is a place for parents to encode what they know, so others don't have to start from scratch.

The goal isn't to be less present as a parent. It's to be more present — by spending less time on the things that don't require you.

---

## You don't need to know the commands

You don't need to memorize skill names or flags. Just open Claude Code and say what you need:

> *"Check my daughter's grades and send me a summary."*

> *"Find something fun to do with a 7-year-old this weekend in San Carlos."*

> *"Set up a Monday morning reminder to top up the lunch account if it drops below $15."*

> *"Audit what my kid has been watching on YouTube this week."*

Claude Code will pick the right skill, ask for any missing info, and handle the rest. The slash commands exist for power users and automation — you never have to use them directly.

---

## Quick start

```bash
# 1. Clone the repo
git clone https://github.com/your-org/awesome-parenting-skills
cd awesome-parenting-skills

# 2. Link all skills to ~/.claude/skills/
for skill in skills/**/*; do
  name=$(basename $skill)
  ln -sf "$PWD/$skill" ~/.claude/skills/$name
done

# 3. Copy the env template and add your API keys
cp .env_template .env

# 4. Open Claude Code and start talking
claude
```

That's it. Skills are live immediately — no restart needed.

---

## Learn more

- [`playbook.md`](playbook.md) — Full skill reference, scheduling with launchd, contributing guide, community data, project structure
- [`design_doc.md`](design_doc.md) — Architecture, Chrome automation guide, safety model, roadmap
