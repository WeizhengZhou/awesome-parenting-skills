---
status: draft
last_verified: 2026-04-01
verified_by: [your-username]
eval_path:
known_issues: []
---

# Skill: draft-teacher-email

Draft a polished, concise email to your child's teacher from a plain-English situation description. Adapts tone to the situation (concerned but not alarmed, positive but not sycophantic). Reads child and school info from existing profile files so you don't have to repeat context each time.

---

## Usage

```
/draft-teacher-email "[child_name] has been struggling with reading comprehension lately — ask for tips we can practice at home"
/draft-teacher-email "[child_name] is going to miss Friday for a doctor appointment — let the teacher know"
/draft-teacher-email --child [child_name] --situation "[child_name] mentioned she's been having trouble with a classmate at recess. We want to flag it without making a big deal." --tone sensitive
/draft-teacher-email --send
```

### Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--child` | auto-detect from `user_docs/kid_profile/` | Child name |
| `--situation` | (required) | Plain-English description of what you want to communicate |
| `--tone` | `neutral` | `neutral`, `concerned`, `positive`, `sensitive`, `urgent` |
| `--to` | teacher email from child's profile | Override recipient |
| `--send` | off | Send via AgentMail after user confirms. **Always shows draft first.** |
| `--save` | off | Save draft to `user_docs/school/emails/YYYYMMDD_teacher_email.md` |

---

## What this skill does

1. **Read child profile** — loads `user_docs/kid_profile/<child>_profile.md`
   - Child name, grade, school
   - Teacher name and email from `newsletter_sources`

2. **Read AgentMail config** — loads `user_docs/agentmail_config.md`
   - Sender email (agent's AgentMail address)
   - Human owner email (for CC or as reply-to)

3. **Draft the email** — produce a complete email:
   - Subject line (clear, not clickbait)
   - Body: 2–4 sentences max — teachers receive many emails
   - Warm but professional tone
   - Signed with the parent's name (from `human_owners` config)

4. **Show the draft** — always display the full draft before any action

5. **Send (optional)** — if `--send` passed:
   - Confirm with user: "Send this email? (yes/no)"
   - On yes: send via AgentMail to teacher's address
   - CC human owner if `--send` is used (so you have a copy in your inbox)

---

## Email tone guide

| Tone | Use for | Style |
|------|---------|-------|
| `neutral` | General updates, info sharing | Matter-of-fact, polite |
| `concerned` | Academic struggles, behavior changes | Empathetic, collaborative ("we'd like to work together...") |
| `positive` | Thank-you, sharing good news | Warm, brief |
| `sensitive` | Social issues, peer conflict, mental health | Careful, non-accusatory, focused on child's wellbeing |
| `urgent` | Same-day absence, pickup change, safety | Direct, all key info in first sentence |

---

## Rules

- **Always show draft before sending** — never silently send
- **Short emails only** — 2–4 sentences unless the situation requires more (flag if longer)
- **No assumptions about the teacher's knowledge** — include enough context for someone who doesn't know the situation
- **Non-native speaker mode** — default to clear, simple English; avoid idioms (parent may not be a native speaker)
- **Child's name not in subject line** (privacy — school email systems are often not encrypted)
- **Never send to anyone not in the teacher's configured email OR explicitly provided via `--to`**
- **Save only when `--save` passed** — don't write files without being asked

---

## Output format

```
📧 Draft email

To: Ms. Rodriguez <mrodriguez@school.org>
From: Your Name <yourname@agentmail.to>
Subject: [child_name] — homework support question

---

Hi Ms. Rodriguez,

I wanted to reach out about [child_name]'s reading comprehension. She's been finding the longer passages a bit overwhelming at home, and we'd love any tips you can share for how to practice this together. Happy to jump on a quick call if that's easier.

Thank you,
[Parent Name]

---

Send this email? (reply 'yes' to send, or paste edits to revise)
```

---

## Files read

| File | Purpose |
|------|---------|
| `user_docs/kid_profile/<child>_profile.md` | Child name, grade, teacher name/email |
| `user_docs/agentmail_config.md` | Sender inbox, parent name for sign-off |

## Files written

| File | When |
|------|------|
| `user_docs/school/emails/YYYYMMDD_teacher_email.md` | Only when `--save` is passed |

---

## Example runs

```
/draft-teacher-email "[child_name] is going to miss Thursday for a dentist appointment — please let us know if she'll miss anything important"
```

```
/draft-teacher-email --tone sensitive "[child_name] mentioned that a classmate said something mean to her at lunch. We don't know the full story but wanted to give you a heads-up in case you noticed anything."
```

```
/draft-teacher-email --send --save "Can we schedule a quick parent-teacher check-in in the next few weeks? We have some questions about reading comprehension."
```
