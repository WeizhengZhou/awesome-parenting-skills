# user_docs_template/

Template directory for personal configuration. **This is the only part of user_docs that is committed.**

## Setup (first time)

```bash
cp -r user_docs_template/ user_docs/
```

Then edit `user_docs/agentmail_config.md` and `user_docs/kid_profile/` with your real info.
`user_docs/` is gitignored — your personal data never leaves your machine.

## Structure

```
user_docs_template/
├── agentmail_config.md          ← AgentMail inbox + human owner allowlist
├── kid_profile/
│   ├── README.md
│   └── _template.md             ← copy to <child>_profile.md and fill in
├── school/
│   └── README.md                ← calendar/ and newsletter/ auto-created by skills
└── activities/
    └── README.md                ← weekend_activities_*.md auto-created by skills
```
