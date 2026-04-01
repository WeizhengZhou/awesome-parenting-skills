# Sub-skill: analyze-kids-content

Part of `/youtube-kids-audit`. Reads a scraped watch history, filters adult noise,
and generates a personalized educational curriculum analysis for a specific child.

**Model requirement:** Use `claude-opus-4-6` (Pro/Opus). This analysis requires
expert-level educational judgment — do NOT use Haiku or any flash model.

## Usage

```
/youtube-kids-audit analyze-kids-content [--profile <child-name>] [--history <path>]
```

| Argument | Default | Description |
|----------|---------|-------------|
| `--profile` | prompts to choose | Child profile in `user_docs/kid_profile/<name>.md` |
| `--history` | latest `watch_history_*.json` | Scraped history from `/youtube-kids-audit` |
| `--output` | `report` | `report` = markdown table + sections |

---

## Step 0: Load or create kid profile

Check for existing profiles:

```bash
ls user_docs/kid_profile/*.md 2>/dev/null | grep -v '_template\|README'
```

**If none exist**, run the intake interview — ask these one at a time:

1. **"What is your child's name and age?"**
2. **"Is this a dedicated YouTube account, or shared with an adult?"**
   - If shared: "Describe the adult content I should ignore (e.g. finance podcasts, political commentary, foreign-language drama)"
3. **"What's their current math level?"** (e.g. grade, curriculum name, specific topics)
4. **"What's their reading level?"** (e.g. reads independently vs with help, example books)
5. **"What are their top 3 interests?"**
6. **"What do they dislike or find boring?"**
7. **"What do they currently watch or listen to most?"**
8. **"Any context I should know — learning style, emotional sensitivities, goals?"**

Write answers to `user_docs/kid_profile/<name>.md` using `_template.md` schema.

---

## Step 1: Load watch history

```python
import glob, json

history_files = sorted(glob.glob("user_docs/watch_history_*.json"), reverse=True)
if not history_files:
    raise FileNotFoundError(
        "No watch_history_*.json found. Run '/youtube-kids-audit' first to scrape."
    )
videos = json.load(open(history_files[0], encoding="utf-8"))
print(f"Loaded {len(videos)} videos from {history_files[0]}")
```

---

## Step 2: Format history as plain-text table (no URLs)

```python
def format_history_table(videos: list[dict]) -> str:
    lines = ["| # | Title | Channel | Duration |",
             "|---|-------|---------|----------|"]
    for i, v in enumerate(videos, 1):
        lines.append(
            f"| {i} | {v.get('title','')[:70]} | {v.get('channel','')[:40]} | {v.get('durationRaw','')} |"
        )
    return "\n".join(lines)
```

Do not include URLs or thumbnails — the model doesn't need them and it reduces token cost.

---

## Step 3: Build the analysis prompt

Construct from the kid's profile. The prompt follows the structure of an Educational
Consultant analyzing a personalized digital learning curriculum.

```python
def build_prompt(profile: dict, history_table: str) -> str:
    name          = profile["name"]
    age           = profile["age"]
    math_level    = profile.get("math_level", "grade-appropriate")
    reading_level = profile.get("reading_level", "")
    interests     = "\n".join(f"- {i}" for i in profile.get("interests", []))
    dislikes      = "\n".join(f"- {d}" for d in profile.get("dislikes", []))
    ignore        = "\n".join(f"- {p}" for p in profile.get("ignore_patterns", []))
    current_media = profile.get("current_books_shows", "")
    notes         = profile.get("parent_notes", "")
    shared        = bool(profile.get("ignore_patterns"))

    return f"""
You are an expert Educational Consultant specializing in Gifted & Talented Elementary
Education and personalized digital learning curricula.

## Child Profile

- Name: {name}, Age: {age}
- Math level: {math_level}
- Reading level: {reading_level}
- Interests (HIGH value): {interests}
- Dislikes / avoid: {dislikes}
- Currently consuming: {current_media}
- Parent notes: {notes}

## Five Core Educational Goals

When classifying and recommending content, evaluate it against these five goals:

1. **Expand Knowledge Breadth & Depth** — Move beyond surface facts into history,
   biography, global concepts, and cultural literacy.
2. **Improve English Holistic Skills** — Advance listening comprehension, complex
   narrative exposure, writing structure, and articulate speaking. Not phonics drills.
3. **Elevate Math Content** — CRITICAL: DO NOT recommend basic counting, arithmetic
   drills, or phonics-adjacent content. Content must match {name}'s actual level
   ({math_level}), focusing on logic, puzzles, and conceptual thinking.
4. **Broaden Science Horizons** — Spark curiosity across biology, physics, astronomy,
   engineering. Prefer inquiry-based ("How? Why?") over fact-listing.
5. **Reinforce Social-Emotional Learning (SEL)** — Support understanding of emotions,
   resilience, and growth mindset (especially important for advanced learners who
   rarely face challenge and may struggle when they finally do).

## Account Context

{"This account is SHARED with an adult. You MUST IGNORE content matching these patterns:" if shared else "This is a dedicated child account."}
{ignore}

Focus your analysis on: children's educational content, audiobooks, cartoons,
science/math enrichment, English language content, and fantasy/adventure stories.

## Watch History

{history_table}

---

## Your Task

Analyze the watch history above and produce a Strategic Educational Report in this
exact structure:

---

### Part 1: Content Audit — What Is {name} Currently Exploring?

Identify the dominant themes and "systems" {name} is consuming.
For each theme, list 2-3 example titles and rate engagement (High/Medium/Low based on
frequency, repeat views, or channel volume).

**Level check:** Flag any content that appears to be *below* {name}'s level — content
she has likely "graduated from" even though it may still appear in history. Examples:
basic phonics channels for a fluent reader, simple counting for an advanced math learner.
Label these **"Educational Junk Food"** — they feel productive but provide no new
challenge.

---

### Part 2: Three-Way Content Classification

Classify ALL relevant (non-adult) videos into one of these buckets:

**✅ KEEP — The Foundation (already working)**
Content aligned with the 5 goals that should remain core to her curriculum.
For each item: channel name, why it fits, which goal(s) it serves.

**🛑 REMOVE / GRADUATE FROM — Outdated or Misaligned**
Content to deprecate. Two types:
- *Too Easy / Mastered*: she has outgrown this (flag with "Educational Junk Food")
- *Misaligned*: passive entertainment with low vocabulary/complexity for her level

**🟢 ADD — The Growth Areas (gaps to fill)**
This is the most important section. Recommend specific named YouTube channels or
content types to fill gaps identified in the audit. Use these strategies:

- **Elevate Math**: Logic puzzles, proof-based thinking, conceptual geometry —
  no drills. Must match her actual level.
- **The "Trojan Horse"**: History / biography content framed as engineering,
  science, or systems — bypasses any dislike of "dates and names" history.
- **Deepen English**: Fiction featuring competence, survival, and logic.
  Avoid whimsical/nonsense if she dislikes it. Audiobooks at native speed
  beat ESL-simplified videos for vocabulary growth.
- **Science Breadth**: Inquiry-first channels (How? Why? What if?) over
  fact-listing channels.
- **SEL for Gifted Learners**: Growth mindset content specifically addressing
  the "panic when things get hard" pattern common in advanced learners.

---

### Part 3: Curriculum Channel Table

Produce a Markdown table of the recommended final channel lineup:

| Channel / Playlist | Short Description | Why {name} Needs This | Goal Alignment |
|-------------------|-------------------|-----------------------|----------------|
| (keep + add items only, sorted by goal) | | | |

Use these Goal labels: `Knowledge Breadth` | `English Skills` | `Math` | `Science` | `SEL`

---

### Part 4: Implementation Schedule

Suggest a simple weekly rhythm (not a rigid schedule — just framing):

| Time / Context | Content Type | Example |
|----------------|-------------|---------|
| Morning (fresh brain) | Active learning | Math puzzles, writing structure |
| Relaxed / meal time | High-quality entertainment | Engineering shows, narrative history |
| Car / bedtime | Audio-first | Audiobooks, mythology podcasts |

---

### Part 5: 3-5 Immediate Next Steps

A specific, actionable parent checklist:

- [ ] **Subscribe to:** [channel] — [one-line reason]
- [ ] **Remove or stop:** [channel] — [one-line reason]
- [ ] **Buy / borrow:** [book or audiobook] — start with [specific entry point]
- [ ] **Ask {name}:** "[A question that opens a conversation about a gap topic]"
""".strip()
```

---

## Step 4: Call Claude Opus for analysis

```python
import anthropic

def run_analysis(prompt: str) -> str:
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model="claude-opus-4-6",   # Pro model required — not haiku/flash
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )
    return msg.content[0].text
```

**Why Opus and not Haiku:** This task requires the model to:
- Detect *level mismatches* between a child's academic profile and what they're watching
- Identify "educational junk food" vs genuinely enriching content
- Generate curriculum-quality recommendations tailored to a specific learner profile
- Cross-reference five goal dimensions simultaneously

Haiku will produce generic results. Opus produces recommendations that feel like a
real educational consultant reviewed the data.

---

## Step 5: Save and display report

```python
import datetime, os

today = datetime.date.today().isoformat()
safe_name = profile["name"].lower().replace(" ", "_")
out_path = f"user_docs/kid_profile/{safe_name}_analysis_{today}.md"

header = f"""# YouTube Watch History Analysis — {profile['name']}

**Date:** {today}
**Videos analyzed:** {len(videos)}
**Model:** claude-opus-4-6

---

"""

with open(out_path, "w", encoding="utf-8") as f:
    f.write(header + analysis_text)

print(f"Report saved → {out_path}")
print("\n" + analysis_text[:3000])
if len(analysis_text) > 3000:
    print(f"\n... [full report in {out_path}]")
```

---

## Key concepts baked into the prompt

### "Educational Junk Food"
Content that *feels* productive (it's about numbers! it's educational!) but provides
no new challenge because the child has already mastered it. Common examples:
- Basic phonics channels for a child who reads chapter books independently
- Simple counting/number cartoons for a child doing advanced math curriculum
- Letter-recognition apps for a fluent reader

These are more harmful than pure entertainment because they consume curriculum time
without developmental return, and may actually *bore* advanced learners into disliking
"educational" content.

### "Consumer → Creator" gap
Advanced readers often have a large intake-output gap: they consume complex content
but haven't been guided to produce at a matching level. The analysis flags this and
recommends writing-structure content (not just "write a story") to close it.

### The "Trojan Horse" recommendation
For children who dislike a specific subject (e.g. traditional history), recommend
content in their *preferred* domain that secretly teaches the gap subject:
- History of medicine → satisfies anatomy interest + teaches history
- Engineering history (bridges, rockets) → satisfies STEM interest + teaches history
- Biography of a scientist → satisfies science interest + teaches biography genre

### Level-matching (critical for gifted learners)
The prompt explicitly tells the model the child's actual academic level and instructs
it NOT to recommend content below that level. A child doing 3rd-grade-level math
should never see a recommendation for basic counting videos, regardless of how many
counting videos appear in the history.

---

## Output files

| File | Contents | Committed? |
|------|----------|------------|
| `user_docs/kid_profile/<name>.md` | Kid profile | Parent's choice |
| `user_docs/kid_profile/<name>_analysis_<date>.md` | Full report | No (gitignored) |

---

## File map

```
skills/media/youtube-kids-audit/
├── SKILL.md                              ← Step 1: scrape watch history via CDP
└── analyze-kids-content/
    └── SKILL.md                          ← Step 2: this file — analyze + report

user_docs/
├── watch_history_<date>.json             ← scraped history (gitignored)
└── kid_profile/
    ├── README.md                         ← index
    ├── _template.md                      ← blank profile schema
    ├── <child-name>.md                   ← filled-in kid profile
    └── <child-name>_analysis_<date>.md   ← generated report (gitignored)
```
