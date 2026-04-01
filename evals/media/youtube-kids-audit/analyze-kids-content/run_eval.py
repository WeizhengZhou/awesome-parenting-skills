#!/usr/bin/env python3
"""
Eval runner for analyze-kids-content skill.

Usage (from repo root):
    python3 evals/media/youtube-kids-audit/analyze-kids-content/run_eval.py
    python3 evals/media/youtube-kids-audit/analyze-kids-content/run_eval.py --tc tc001
    python3 evals/media/youtube-kids-audit/analyze-kids-content/run_eval.py --dry-run
    python3 evals/media/youtube-kids-audit/analyze-kids-content/run_eval.py --output results.json
"""

import argparse
import json
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

EVAL_DIR = Path(__file__).parent
FIXTURES_DIR = EVAL_DIR / "fixtures"
PROFILES_DIR = FIXTURES_DIR / "profiles"
HISTORIES_DIR = FIXTURES_DIR / "histories"

# ---------------------------------------------------------------------------
# Test case definitions
# ---------------------------------------------------------------------------

@dataclass
class TestCase:
    id: str
    label: str
    profile_file: str
    history_file: str
    # Rubric dimensions that apply to this TC (not all apply to all TCs)
    applicable_rubrics: list[str] = field(default_factory=list)


TEST_CASES = [
    TestCase(
        id="tc001",
        label="Advanced 7yo, mixed account",
        profile_file="tc001_advanced_7yo_mixed.md",
        history_file="tc001_history.json",
        applicable_rubrics=["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8"],
    ),
    TestCase(
        id="tc002",
        label="Average 5yo, dedicated account",
        profile_file="tc002_average_5yo_dedicated.md",
        history_file="tc002_history.json",
        # R1 not applicable — dedicated account with no adult content
        applicable_rubrics=["R2", "R3", "R4", "R5", "R6", "R7", "R8"],
    ),
    TestCase(
        id="tc003",
        label="Struggling 9yo, mixed account",
        profile_file="tc003_struggling_9yo_mixed.md",
        history_file="tc003_history.json",
        # R7 requires cross-TC comparison (handled separately)
        applicable_rubrics=["R1", "R2", "R3", "R4", "R5", "R6", "R8"],
    ),
]

# ---------------------------------------------------------------------------
# Rubric definitions
# ---------------------------------------------------------------------------

@dataclass
class RubricDim:
    id: str
    name: str
    weight: int
    scoring_method: str  # "structural" or "llm_judge"
    description: str
    pass_criteria: str
    fail_criteria: str


RUBRIC = [
    RubricDim(
        id="R1",
        name="Adult Content Filtering",
        weight=3,
        scoring_method="llm_judge",
        description="Adult content matching ignore_patterns must not appear in KEEP, ADD, or curriculum table.",
        pass_criteria=(
            "Zero channels matching ignore_patterns appear in KEEP or ADD recommendations. "
            "Finance, tech news, adult drama, crypto, sports analysis, and news channels "
            "do not appear as recommendations for the child."
        ),
        fail_criteria=(
            "Any finance, tech news, drama, crypto, sports, or news channel appears "
            "as a child recommendation in KEEP or ADD sections."
        ),
    ),
    RubricDim(
        id="R2",
        name="Educational Junk Food Detection",
        weight=3,
        scoring_method="llm_judge",
        description=(
            "Content >2 academic years below child's level is labeled 'Educational Junk Food' "
            "in REMOVE with explicit level-mismatch explanation. Age-appropriate content is "
            "NOT incorrectly flagged (contrast test)."
        ),
        pass_criteria=(
            "For advanced learners: below-level content (Cocomelon, basic Numberblocks, Blippi phonics) "
            "appears in REMOVE labeled as Educational Junk Food with specific level mismatch cited. "
            "For typical/below-level learners: age-appropriate content is NOT flagged as junk food."
        ),
        fail_criteria=(
            "Below-level content kept without flagging for advanced learner, OR "
            "age-appropriate content incorrectly flagged as junk food for typical/below-level learner."
        ),
    ),
    RubricDim(
        id="R3",
        name="Math Level Calibration",
        weight=3,
        scoring_method="llm_judge",
        description=(
            "All math ADD recommendations match or exceed child's stated math level. "
            "No basic counting for advanced learners; no grade-5 math for grade-2 learners."
        ),
        pass_criteria=(
            "ADD section names at least one math channel at or above child's level. "
            "No basic counting/Numberblocks for Beast Academy learner. "
            "No abstract algebra for grade-2 math learner. "
            "Recommendations reflect child's learning style (logic/puzzles for TC-001, "
            "visual/spatial for TC-003, story-based for TC-002)."
        ),
        fail_criteria=(
            "Basic counting recommended for advanced learner, OR "
            "grade-5+ math recommended for grade-2 learner, OR "
            "no specific math channel named."
        ),
    ),
    RubricDim(
        id="R4",
        name="Five-Goal Coverage",
        weight=2,
        scoring_method="llm_judge",
        description=(
            "ADD section addresses at least 4 of 5 goals: Knowledge, English, Math, Science, SEL."
        ),
        pass_criteria=(
            "ADD recommendations collectively address at least 4 of 5 goals. "
            "At least one English Skills recommendation. "
            "At least one SEL or growth mindset recommendation. "
            "Goal labels appear in curriculum table."
        ),
        fail_criteria=(
            "Fewer than 3 goals in ADD, OR missing English recommendation, "
            "OR missing SEL recommendation, OR no goal labels in curriculum table."
        ),
    ),
    RubricDim(
        id="R5",
        name="Output Structure Completeness",
        weight=2,
        scoring_method="structural",
        description="All 5 required output parts present: Audit, KEEP/REMOVE/ADD, Channel Table, Schedule, Next Steps.",
        pass_criteria=(
            "Output contains all 5 parts: (1) Content Audit, (2) Three-Way Classification "
            "with explicit KEEP/REMOVE/ADD, (3) Curriculum Channel Table (Markdown), "
            "(4) Implementation Schedule table, (5) Next Steps checklist with [ ] items."
        ),
        fail_criteria=(
            "Any of the 5 parts missing, KEEP/REMOVE/ADD merged without labeling, "
            "table replaced with list, or Next Steps has fewer than 3 [ ] items."
        ),
    ),
    RubricDim(
        id="R6",
        name="Recommendation Specificity",
        weight=2,
        scoring_method="structural",
        description="ADD section names at least 5 specific YouTube channels by exact name.",
        pass_criteria=(
            "ADD section contains at least 5 named YouTube channels (real channel names, "
            "not generic descriptions). Each has a rationale connecting it to this child's profile."
        ),
        fail_criteria=(
            "Fewer than 3 named specific channels, OR recommendations are generic descriptions, "
            "OR channels listed without rationale."
        ),
    ),
    RubricDim(
        id="R7",
        name="Age Calibration Contrast",
        weight=2,
        scoring_method="cross_tc",
        description=(
            "Cocomelon flagged as junk food for TC-001 (advanced 7yo) but NOT for TC-002 (typical 5yo). "
            "Same content, different verdict based on profile."
        ),
        pass_criteria=(
            "TC-001: Cocomelon in REMOVE labeled Educational Junk Food with level explanation. "
            "TC-002: Cocomelon NOT in REMOVE and NOT labeled junk food."
        ),
        fail_criteria=(
            "Same verdict for both TCs, OR TC-002 flags Cocomelon as junk food, "
            "OR TC-001 keeps Cocomelon without flagging."
        ),
    ),
    RubricDim(
        id="R8",
        name="Trojan Horse Recommendation",
        weight=1,
        scoring_method="llm_judge",
        description=(
            "At least one ADD recommendation uses child's known interest to teach a gap subject, "
            "with the cross-domain bridge explicitly stated."
        ),
        pass_criteria=(
            "At least one ADD recommendation explicitly connects child's stated interest domain "
            "to a gap subject (e.g. Lego/Minecraft to teach math concepts; dinosaurs to teach "
            "geology or timelines; Harry Potter lore to teach medieval history)."
        ),
        fail_criteria=(
            "All recommendations are direct subject-to-subject with no cross-domain bridge, "
            "OR bridge exists but is not connected to child's specific stated interests."
        ),
    ),
]

RUBRIC_BY_ID = {r.id: r for r in RUBRIC}

# ---------------------------------------------------------------------------
# Prompt building
# ---------------------------------------------------------------------------

def load_profile(tc: TestCase) -> str:
    path = PROFILES_DIR / tc.profile_file
    return path.read_text(encoding="utf-8")


def load_history(tc: TestCase) -> list[dict]:
    path = HISTORIES_DIR / tc.history_file
    return json.loads(path.read_text(encoding="utf-8"))


def format_history_table(videos: list[dict]) -> str:
    lines = [
        "| # | Title | Channel | Duration |",
        "|---|-------|---------|----------|",
    ]
    for i, v in enumerate(videos, 1):
        title = v.get("title", "")[:70]
        channel = v.get("channel", "")[:40]
        duration = v.get("durationRaw", "")
        lines.append(f"| {i} | {title} | {channel} | {duration} |")
    return "\n".join(lines)


def parse_profile_fields(profile_text: str) -> dict:
    """Extract key fields from the profile markdown for prompt construction."""
    fields = {}

    # Name
    m = re.search(r'^name:\s*"?([^"\n]+)"?', profile_text, re.MULTILINE)
    fields["name"] = m.group(1).strip() if m else "Child"

    # Age
    m = re.search(r'^age:\s*(\d+)', profile_text, re.MULTILINE)
    fields["age"] = int(m.group(1)) if m else 0

    # Account type
    if "`dedicated`" in profile_text or "dedicated child account" in profile_text.lower():
        fields["account_type"] = "dedicated"
    else:
        fields["account_type"] = "mixed"

    # ignore_patterns block
    m = re.search(r'ignore_patterns:\s*\n((?:\s*-[^\n]+\n?)+)', profile_text)
    if m:
        raw = m.group(1)
        fields["ignore_patterns"] = [
            line.strip().lstrip("- ").strip()
            for line in raw.splitlines()
            if line.strip().startswith("-")
        ]
    else:
        fields["ignore_patterns"] = []

    # Math level
    m = re.search(r'\|\s*Math\s*\|\s*([^|]+)\|', profile_text)
    fields["math_level"] = m.group(1).strip() if m else "grade-appropriate"

    # Reading level
    m = re.search(r'\|\s*Reading\s*\|\s*([^|]+)\|', profile_text)
    fields["reading_level"] = m.group(1).strip() if m else ""

    # Interests
    m = re.search(r'## Interests.*?\n((?:- [^\n]+\n?)+)', profile_text, re.DOTALL)
    if m:
        fields["interests"] = [
            line.strip().lstrip("- ").strip()
            for line in m.group(1).splitlines()
            if line.strip().startswith("-")
        ]
    else:
        fields["interests"] = []

    # Dislikes
    m = re.search(r'## Dislikes.*?\n((?:- [^\n]+\n?)+)', profile_text, re.DOTALL)
    if m:
        fields["dislikes"] = [
            line.strip().lstrip("- ").strip()
            for line in m.group(1).splitlines()
            if line.strip().startswith("-")
        ]
    else:
        fields["dislikes"] = []

    # Current books/shows
    m = re.search(r'## Current books.*?\n(.*?)(?=\n##|\Z)', profile_text, re.DOTALL)
    fields["current_media"] = m.group(1).strip() if m else ""

    # Parent notes
    m = re.search(r'## Parent notes.*?>\s*(.*?)(?=\n##|\Z)', profile_text, re.DOTALL)
    fields["parent_notes"] = m.group(1).strip() if m else ""

    return fields


def build_analysis_prompt(profile_text: str, history_table: str) -> str:
    """Build the prompt as specified in the skill's Step 3."""
    p = parse_profile_fields(profile_text)
    name = p["name"]
    age = p["age"]
    math_level = p["math_level"]
    reading_level = p["reading_level"]
    interests = "\n".join(f"- {i}" for i in p["interests"])
    dislikes = "\n".join(f"- {d}" for d in p["dislikes"])
    ignore = "\n".join(f"- {pat}" for pat in p["ignore_patterns"])
    current_media = p["current_media"]
    notes = p["parent_notes"]
    shared = bool(p["ignore_patterns"])

    account_section = (
        f"This account is SHARED with an adult. You MUST IGNORE content matching these patterns:\n{ignore}"
        if shared
        else "This is a dedicated child account."
    )

    return f"""
You are an expert Educational Consultant specializing in Gifted & Talented Elementary
Education and personalized digital learning curricula.

## Child Profile

- Name: {name}, Age: {age}
- Math level: {math_level}
- Reading level: {reading_level}
- Interests (HIGH value):
{interests}
- Dislikes / avoid:
{dislikes}
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
   resilience, and growth mindset.

## Account Context

{account_section}

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
they have likely "graduated from" even though it may still appear in history. Examples:
basic phonics channels for a fluent reader, simple counting for an advanced math learner.
Label these **"Educational Junk Food"** — they feel productive but provide no new
challenge.

---

### Part 2: Three-Way Content Classification

Classify ALL relevant (non-adult) videos into one of these buckets:

**KEEP — The Foundation (already working)**
Content aligned with the 5 goals that should remain core to their curriculum.
For each item: channel name, why it fits, which goal(s) it serves.

**REMOVE / GRADUATE FROM — Outdated or Misaligned**
Content to deprecate. Two types:
- *Too Easy / Mastered*: they have outgrown this (flag with "Educational Junk Food")
- *Misaligned*: passive entertainment with low vocabulary/complexity for their level

**ADD — The Growth Areas (gaps to fill)**
This is the most important section. Recommend specific named YouTube channels or
content types to fill gaps identified in the audit. Use these strategies:

- **Elevate Math**: Logic puzzles, proof-based thinking, conceptual geometry —
  no drills. Must match their actual level.
- **The "Trojan Horse"**: History / biography content framed as engineering,
  science, or systems — bypasses any dislike of "dates and names" history.
- **Deepen English**: Fiction featuring competence, survival, and logic.
  Audiobooks at native speed beat ESL-simplified videos for vocabulary growth.
- **Science Breadth**: Inquiry-first channels (How? Why? What if?) over
  fact-listing channels.
- **SEL for Learners**: Growth mindset content.

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


# ---------------------------------------------------------------------------
# Claude CLI runner
# ---------------------------------------------------------------------------

def run_claude(prompt: str, timeout: int = 300) -> tuple[str, bool]:
    """
    Call `claude -p "<prompt>"` via subprocess.
    Returns (output_text, success).
    """
    try:
        result = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            err = result.stderr.strip() or "(no stderr)"
            return f"ERROR: claude exited {result.returncode}: {err}", False
        return result.stdout.strip(), True
    except subprocess.TimeoutExpired:
        return f"ERROR: claude timed out after {timeout}s", False
    except FileNotFoundError:
        return "ERROR: 'claude' CLI not found. Install with: npm install -g @anthropic-ai/claude-code", False


# ---------------------------------------------------------------------------
# Structural scoring (no LLM needed)
# ---------------------------------------------------------------------------

SECTION_PATTERNS = {
    "Part 1": [r"Part 1", r"Content Audit", r"Currently Exploring"],
    "Part 2 KEEP": [r"KEEP", r"✅", r"Foundation"],
    "Part 2 REMOVE": [r"REMOVE", r"🛑", r"GRADUATE"],
    "Part 2 ADD": [r"ADD", r"🟢", r"Growth Areas"],
    "Part 3": [r"Part 3", r"Curriculum Channel Table", r"Channel / Playlist"],
    "Part 4": [r"Part 4", r"Implementation Schedule", r"Time / Context"],
    "Part 5": [r"Part 5", r"Next Steps", r"\[ \]", r"- \["],
}


def check_structure(output: str) -> tuple[bool, str]:
    """R5: Check all 5 output parts are present."""
    missing = []

    required_groups = [
        ("Content Audit (Part 1)", SECTION_PATTERNS["Part 1"]),
        ("KEEP classification (Part 2)", SECTION_PATTERNS["Part 2 KEEP"]),
        ("REMOVE classification (Part 2)", SECTION_PATTERNS["Part 2 REMOVE"]),
        ("ADD classification (Part 2)", SECTION_PATTERNS["Part 2 ADD"]),
        ("Curriculum Channel Table (Part 3)", SECTION_PATTERNS["Part 3"]),
        ("Implementation Schedule (Part 4)", SECTION_PATTERNS["Part 4"]),
        ("Next Steps checklist (Part 5)", SECTION_PATTERNS["Part 5"]),
    ]

    for label, patterns in required_groups:
        found = any(re.search(p, output, re.IGNORECASE) for p in patterns)
        if not found:
            missing.append(label)

    # Check [ ] checklist items exist
    checklist_items = re.findall(r'- \[[ x]\]', output, re.IGNORECASE)
    if len(checklist_items) < 3:
        missing.append(f"Fewer than 3 Next Steps checklist items (found {len(checklist_items)})")

    if missing:
        return False, f"Missing sections: {'; '.join(missing)}"
    return True, "All 5 sections present"


def check_specificity(output: str) -> tuple[bool, str]:
    """R6: Count named YouTube channels in ADD section."""
    # Extract the ADD section
    add_match = re.search(
        r'(?:ADD|🟢|Growth Areas?)(.*?)(?:Part 3|Curriculum Channel Table|\Z)',
        output,
        re.DOTALL | re.IGNORECASE,
    )
    add_text = add_match.group(1) if add_match else output

    # Known real channels to look for (case-insensitive)
    known_channels = [
        "TED-Ed", "Kurzgesagt", "Mathologer", "Numberphile", "SciShow Kids",
        "SciShow", "Crash Course", "Khan Academy", "Wild Kratts", "Odd Squad",
        "PBS Kids", "Teaching Without Frills", "Homeschool Pop", "Veritasium",
        "Vsauce", "MinutePhysics", "MinuteEarth", "3Blue1Brown", "Dino Dana",
        "Alma's Way", "Elinor Wonders Why", "Bluey", "Daniel Tiger",
        "Numberblocks", "Alphablocks", "ReadingIQ", "Epic", "Audible",
        "Bedtime Stories", "Mythology with Milo", "Overly Sarcastic",
        "History Buffs", "Real Engineering", "Practical Engineering",
        "Engineerguy", "Mark Rober", "Destin Sandlin", "Smarter Every Day",
        "It's Okay to Be Smart", "PBS Space Time", "Cosmos", "NASA",
        "CrashCourse Kids", "Sesame Street", "Brainpop",
    ]

    # Also look for channel-like patterns (Capitalized Name Channel patterns)
    generic_channel_pattern = re.findall(
        r'\*\*([A-Z][A-Za-z0-9\s&!\':\-]{3,40})\*\*', add_text
    )

    named_count = 0
    found_names = []
    for ch in known_channels:
        if re.search(re.escape(ch), add_text, re.IGNORECASE):
            named_count += 1
            found_names.append(ch)

    # Also count bold-formatted channel names not in our list
    for g in generic_channel_pattern:
        g = g.strip()
        if g not in found_names and len(g) > 3:
            named_count += 1
            found_names.append(g)

    if named_count >= 5:
        return True, f"{named_count} named channels found: {', '.join(found_names[:8])}"
    elif named_count >= 3:
        return False, f"Only {named_count} named channels (need 5): {', '.join(found_names)}"
    else:
        return False, f"Only {named_count} named channels found (need 5). Recommendations may be generic."


# ---------------------------------------------------------------------------
# LLM judge scoring — single batched call per TC
# ---------------------------------------------------------------------------

def build_batch_judge_prompt(
    tc: TestCase,
    profile_text: str,
    history_summary: str,
    skill_output: str,
    dims: list[RubricDim],
) -> str:
    dims_block = "\n\n".join(
        f"### {d.id} — {d.name} (weight {d.weight})\n"
        f"Description: {d.description}\n"
        f"PASS if: {d.pass_criteria}\n"
        f"FAIL if: {d.fail_criteria}"
        for d in dims
    )
    ids = [d.id for d in dims]
    return f"""You are evaluating the output of an AI skill called "analyze-kids-content".
The skill analyzes a child's YouTube watch history and produces a personalized educational report.

## Test Case: {tc.id} — {tc.label}

## Child Profile (abbreviated)
{profile_text[:1500]}

## Watch History Summary (first 20 entries)
{history_summary}

## Skill Output
{skill_output[:6000]}

## Rubric Dimensions to Score

Score EACH of the following dimensions PASS or FAIL based on the skill output above.

{dims_block}

## Response Format

Return a JSON object — nothing else, no markdown fences. Example:
{{"R1": {{"verdict": "PASS", "reason": "one sentence"}}, "R2": {{"verdict": "FAIL", "reason": "one sentence"}}}}

Score all {len(ids)} dimensions: {', '.join(ids)}
"""


def score_all_llm_dims(
    tc: TestCase,
    profile_text: str,
    videos: list[dict],
    skill_output: str,
    dims: list[RubricDim],
    verbose: bool = False,
) -> dict[str, tuple[Optional[bool], str]]:
    """Single claude call scoring all LLM-judge dimensions. Returns {rid: (verdict, reason)}."""
    if not dims:
        return {}
    history_summary = format_history_table(videos[:20])
    prompt = build_batch_judge_prompt(tc, profile_text, history_summary, skill_output, dims)
    if verbose:
        print(f"    [judge] Scoring {[d.id for d in dims]} in one call...")
    response, ok = run_claude(prompt, timeout=180)
    if not ok:
        return {d.id: (None, f"Judge call failed: {response[:100]}") for d in dims}

    # Strip markdown fences if present
    cleaned = re.sub(r'^```(?:json)?\s*|\s*```$', '', response.strip(), flags=re.MULTILINE)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        # Fallback: try to extract individual verdicts
        results = {}
        for d in dims:
            m = re.search(rf'"{d.id}".*?"verdict":\s*"(PASS|FAIL)".*?"reason":\s*"([^"]+)"',
                          response, re.IGNORECASE | re.DOTALL)
            if m:
                results[d.id] = (m.group(1).upper() == "PASS", m.group(2)[:200])
            else:
                results[d.id] = (None, f"Parse error in batch response: {response[:100]}")
        return results

    results = {}
    for d in dims:
        entry = data.get(d.id, {})
        verdict_str = entry.get("verdict", "").upper()
        reason = entry.get("reason", "(no reason)")[:200]
        verdict = True if verdict_str == "PASS" else (False if verdict_str == "FAIL" else None)
        results[d.id] = (verdict, reason)
    return results


# ---------------------------------------------------------------------------
# Cross-TC scoring (R7)
# ---------------------------------------------------------------------------

def score_r7_contrast(outputs: dict[str, str]) -> tuple[Optional[bool], str]:
    """
    R7: Cocomelon flagged as junk food for TC-001 but NOT for TC-002.
    Requires both outputs to be available.
    """
    if "tc001" not in outputs or "tc002" not in outputs:
        return None, "N/A — requires both TC-001 and TC-002 outputs"

    out001 = outputs["tc001"]
    out002 = outputs["tc002"]

    # TC-001: Cocomelon should be in REMOVE section labeled junk food
    remove_section_001 = ""
    m = re.search(
        r'(?:REMOVE|🛑|GRADUATE)(.*?)(?:ADD|🟢|\Z)',
        out001,
        re.DOTALL | re.IGNORECASE,
    )
    if m:
        remove_section_001 = m.group(1)

    cocomelon_removed_001 = bool(
        re.search(r'cocomelon', remove_section_001, re.IGNORECASE)
    )
    junk_food_001 = bool(
        re.search(r'educational junk food', out001[:out001.lower().find("add") if "add" in out001.lower() else len(out001)], re.IGNORECASE)
        and re.search(r'cocomelon', out001[:out001.lower().find("add") if "add" in out001.lower() else len(out001)], re.IGNORECASE)
    )

    # TC-002: Cocomelon should NOT be in REMOVE as junk food
    remove_section_002 = ""
    m2 = re.search(
        r'(?:REMOVE|🛑|GRADUATE)(.*?)(?:ADD|🟢|\Z)',
        out002,
        re.DOTALL | re.IGNORECASE,
    )
    if m2:
        remove_section_002 = m2.group(1)

    cocomelon_junk_002 = bool(
        re.search(r'cocomelon', remove_section_002, re.IGNORECASE)
        and re.search(r'(?:junk food|junk|below.level|too easy)', remove_section_002, re.IGNORECASE)
    )

    if cocomelon_removed_001 and not cocomelon_junk_002:
        return True, (
            "TC-001: Cocomelon in REMOVE section. "
            "TC-002: Cocomelon not flagged as junk food. Contrast correct."
        )

    reasons = []
    if not cocomelon_removed_001:
        reasons.append("TC-001: Cocomelon not found in REMOVE section")
    if cocomelon_junk_002:
        reasons.append("TC-002: Cocomelon incorrectly flagged as junk food")

    return False, "; ".join(reasons) if reasons else "R7 contrast check failed"


# ---------------------------------------------------------------------------
# Result data structures
# ---------------------------------------------------------------------------

@dataclass
class DimResult:
    rubric_id: str
    name: str
    weight: int
    verdict: Optional[bool]  # True=PASS, False=FAIL, None=N/A or ERROR
    points_earned: int
    points_possible: int
    reason: str


@dataclass
class TCResult:
    tc_id: str
    tc_label: str
    dim_results: list[DimResult]
    skill_output: str
    prompt_used: str

    def total_points(self) -> int:
        return sum(d.points_earned for d in self.dim_results)

    def max_points(self) -> int:
        return sum(d.points_possible for d in self.dim_results)

    def pass_rate(self) -> float:
        if self.max_points() == 0:
            return 0.0
        return self.total_points() / self.max_points()

    def overall_pass(self) -> bool:
        return self.pass_rate() >= 0.75


# ---------------------------------------------------------------------------
# Printing results
# ---------------------------------------------------------------------------

def print_tc_result(result: TCResult) -> None:
    width = 68
    print(f"\n{'=' * width}")
    print(f"  {result.tc_id.upper()}: {result.tc_label}")
    print(f"{'=' * width}")

    for dim in result.dim_results:
        if dim.verdict is None:
            badge = "[N/A ]"
            color = ""
        elif dim.verdict:
            badge = "[PASS]"
        else:
            badge = "[FAIL]"

        wt = f"(w{dim.weight})"
        label = f"  {dim.rubric_id} {dim.name:<28} {badge} {wt}"
        print(label)
        # Truncate reason to fit terminal
        reason = dim.reason
        if len(reason) > 70:
            reason = reason[:67] + "..."
        print(f"       {reason}")

    total = result.total_points()
    maximum = result.max_points()
    pct = result.pass_rate() * 100
    status = "PASS" if result.overall_pass() else "FAIL"
    print(f"\n  Score: {total}/{maximum} ({pct:.0f}%)  [{status}]")


def print_summary(results: list[TCResult]) -> None:
    width = 68
    print(f"\n{'=' * width}")
    print("  OVERALL SUMMARY")
    print(f"{'=' * width}")

    grand_total = 0
    grand_max = 0
    for r in results:
        t = r.total_points()
        m = r.max_points()
        grand_total += t
        grand_max += m
        pct = (t / m * 100) if m > 0 else 0
        status = "PASS" if r.overall_pass() else "FAIL"
        print(f"  {r.tc_id.upper()}: {r.tc_label}")
        print(f"         {t}/{m} ({pct:.0f}%)  [{status}]")

    if grand_max > 0:
        overall_pct = grand_total / grand_max * 100
        print(f"\n  TOTAL: {grand_total}/{grand_max} ({overall_pct:.0f}%)")
        if overall_pct >= 85:
            print("  STATUS: PRODUCTION READY")
        elif overall_pct >= 70:
            print("  STATUS: NEEDS IMPROVEMENT")
        else:
            print("  STATUS: FAILING — REVIEW SKILL PROMPT AND MODEL CHOICE")
    print()


# ---------------------------------------------------------------------------
# Main eval logic
# ---------------------------------------------------------------------------

def run_single_tc(
    tc: TestCase,
    dry_run: bool = False,
    verbose: bool = False,
    skill_output_override: Optional[str] = None,
) -> TCResult:
    profile_text = load_profile(tc)
    videos = load_history(tc)
    history_table = format_history_table(videos)
    prompt = build_analysis_prompt(profile_text, history_table)

    if dry_run:
        print(f"\n[DRY RUN] Prompt for {tc.id}:")
        print(prompt[:2000])
        print("... (truncated)")
        skill_output = "[DRY RUN — no output]"
    elif skill_output_override is not None:
        skill_output = skill_output_override
    else:
        if verbose:
            print(f"  Calling claude for skill output ({tc.id})...")
        skill_output, ok = run_claude(prompt, timeout=300)
        if not ok:
            print(f"  ERROR running skill for {tc.id}: {skill_output}")
            # Return empty result with errors
            dim_results = []
            for rid in tc.applicable_rubrics:
                rd = RUBRIC_BY_ID[rid]
                dim_results.append(DimResult(
                    rubric_id=rid,
                    name=rd.name,
                    weight=rd.weight,
                    verdict=None,
                    points_earned=0,
                    points_possible=rd.weight,
                    reason=f"Skill call failed: {skill_output[:100]}",
                ))
            return TCResult(
                tc_id=tc.id,
                tc_label=tc.label,
                dim_results=dim_results,
                skill_output="",
                prompt_used=prompt,
            )

    dim_results = []

    for rid in tc.applicable_rubrics:
        rd = RUBRIC_BY_ID[rid]

        if dry_run:
            dim_results.append(DimResult(
                rubric_id=rid,
                name=rd.name,
                weight=rd.weight,
                verdict=None,
                points_earned=0,
                points_possible=rd.weight,
                reason="[DRY RUN]",
            ))
            continue

        if rd.scoring_method == "structural":
            if rid == "R5":
                verdict, reason = check_structure(skill_output)
            elif rid == "R6":
                verdict, reason = check_specificity(skill_output)
            else:
                verdict, reason = None, f"Unknown structural check for {rid}"

        elif rd.scoring_method == "cross_tc":
            # R7 needs outputs from both TCs — handled after all TCs run
            dim_results.append(DimResult(
                rubric_id=rid,
                name=rd.name,
                weight=rd.weight,
                verdict=None,
                points_earned=0,
                points_possible=rd.weight,
                reason="Pending cross-TC comparison",
            ))
            continue

        elif rd.scoring_method == "llm_judge":
            # Resolved below via batch call — placeholder until then
            dim_results.append(DimResult(
                rubric_id=rid, name=rd.name, weight=rd.weight,
                verdict=None, points_earned=0, points_possible=rd.weight,
                reason="Pending batch judge",
            ))
            continue

        else:
            verdict, reason = None, f"Unknown scoring method: {rd.scoring_method}"

        points = rd.weight if verdict is True else 0
        dim_results.append(DimResult(
            rubric_id=rid,
            name=rd.name,
            weight=rd.weight,
            verdict=verdict,
            points_earned=points,
            points_possible=rd.weight,
            reason=reason,
        ))

    # --- Single batched LLM judge call for all llm_judge dims ---
    if not dry_run:
        llm_dims = [RUBRIC_BY_ID[rid] for rid in tc.applicable_rubrics
                    if RUBRIC_BY_ID[rid].scoring_method == "llm_judge"]
        if llm_dims:
            if verbose:
                print(f"  [judge] Batch scoring {[d.id for d in llm_dims]}...")
            batch_results = score_all_llm_dims(
                tc, profile_text, videos, skill_output, llm_dims, verbose=verbose
            )
            for i, dim in enumerate(dim_results):
                if dim.reason == "Pending batch judge" and dim.rubric_id in batch_results:
                    verdict, reason = batch_results[dim.rubric_id]
                    points = RUBRIC_BY_ID[dim.rubric_id].weight if verdict is True else 0
                    dim_results[i] = DimResult(
                        rubric_id=dim.rubric_id, name=dim.name, weight=dim.weight,
                        verdict=verdict, points_earned=points,
                        points_possible=dim.weight, reason=reason,
                    )

    return TCResult(
        tc_id=tc.id,
        tc_label=tc.label,
        dim_results=dim_results,
        skill_output=skill_output,
        prompt_used=prompt,
    )


def apply_cross_tc_scoring(results: list[TCResult]) -> None:
    """
    R7 requires outputs from both TC-001 and TC-002.
    Update pending R7 entries in-place.
    """
    outputs = {r.tc_id: r.skill_output for r in results}
    verdict, reason = score_r7_contrast(outputs)
    rd = RUBRIC_BY_ID["R7"]

    for result in results:
        tc = next((t for t in TEST_CASES if t.id == result.tc_id), None)
        if tc is None:
            continue
        if "R7" not in tc.applicable_rubrics:
            continue
        # Find and update the pending R7 entry
        for i, dim in enumerate(result.dim_results):
            if dim.rubric_id == "R7" and dim.reason == "Pending cross-TC comparison":
                points = rd.weight if verdict is True else 0
                result.dim_results[i] = DimResult(
                    rubric_id="R7",
                    name=rd.name,
                    weight=rd.weight,
                    verdict=verdict,
                    points_earned=points,
                    points_possible=rd.weight,
                    reason=reason or "N/A",
                )
                break


# ---------------------------------------------------------------------------
# Markdown report writer
# ---------------------------------------------------------------------------

def write_markdown_report(results: list[TCResult], report_path: Path) -> None:
    import datetime
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        f"# Eval Report — analyze-kids-content",
        f"",
        f"**Run date:** {now}  ",
        f"**Test cases:** {len(results)}  ",
        f"**Rubric:** `rubric.md`",
        f"",
        f"---",
        f"",
        f"## Summary",
        f"",
        f"| Test Case | Score | Pass Rate | Status |",
        f"|-----------|-------|-----------|--------|",
    ]
    grand_total = grand_max = 0
    for r in results:
        t, m = r.total_points(), r.max_points()
        grand_total += t
        grand_max += m
        pct = f"{t/m*100:.0f}%" if m else "N/A"
        status = "✅ PASS" if r.overall_pass() else "❌ FAIL"
        lines.append(f"| **{r.tc_id}**: {r.tc_label} | {t}/{m} | {pct} | {status} |")

    overall_pct = grand_total / grand_max * 100 if grand_max else 0
    overall_status = (
        "✅ PRODUCTION READY" if overall_pct >= 85
        else "⚠️ NEEDS IMPROVEMENT" if overall_pct >= 70
        else "❌ FAILING"
    )
    lines += [
        f"",
        f"**Overall: {grand_total}/{grand_max} ({overall_pct:.0f}%) — {overall_status}**",
        f"",
        f"---",
        f"",
    ]

    for r in results:
        lines += [
            f"## {r.tc_id.upper()}: {r.tc_label}",
            f"",
            f"**Score: {r.total_points()}/{r.max_points()} ({r.pass_rate()*100:.0f}%)**",
            f"",
            f"| Rubric | Dimension | Weight | Verdict | Reason |",
            f"|--------|-----------|--------|---------|--------|",
        ]
        for d in r.dim_results:
            if d.verdict is None:
                badge = "⏭ N/A"
            elif d.verdict:
                badge = "✅ PASS"
            else:
                badge = "❌ FAIL"
            reason = d.reason.replace("|", "\\|").replace("\n", " ")[:120]
            lines.append(f"| {d.rubric_id} | {d.name} | {d.weight} | {badge} | {reason} |")

        lines += ["", "### Skill Output (excerpt)", "", "```"]
        lines += r.skill_output[:3000].splitlines()
        if len(r.skill_output) > 3000:
            lines.append("... [truncated — full output in JSON results file]")
        lines += ["```", "", "---", ""]

    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Markdown report saved → {report_path}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Eval runner for analyze-kids-content skill"
    )
    parser.add_argument(
        "--tc",
        choices=["tc001", "tc002", "tc003"],
        help="Run a single test case (default: all)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build and print prompts without calling claude",
    )
    parser.add_argument(
        "--output",
        metavar="FILE",
        help="Save full results to JSON file (also auto-generates a .md report alongside it)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print progress messages during scoring",
    )
    args = parser.parse_args()

    # Select test cases
    if args.tc:
        tcs = [t for t in TEST_CASES if t.id == args.tc]
    else:
        tcs = TEST_CASES

    print(f"\nanalyze-kids-content eval — {len(tcs)} test case(s)")
    if args.dry_run:
        print("(DRY RUN — no API calls)")

    results = []
    for tc in tcs:
        print(f"\nRunning {tc.id}: {tc.label}...")
        result = run_single_tc(tc, dry_run=args.dry_run, verbose=args.verbose)
        results.append(result)
        print(f"  Done. Raw score: {result.total_points()}/{result.max_points()}")

    if not args.dry_run and len(results) > 1:
        # Apply cross-TC R7 scoring now that all outputs are available
        apply_cross_tc_scoring(results)

    # Print detailed results
    for result in results:
        print_tc_result(result)

    # Print summary
    print_summary(results)

    # Optionally save to JSON
    if args.output:
        out = []
        for r in results:
            out.append({
                "tc_id": r.tc_id,
                "tc_label": r.tc_label,
                "total_points": r.total_points(),
                "max_points": r.max_points(),
                "pass_rate": r.pass_rate(),
                "overall_pass": r.overall_pass(),
                "dimensions": [
                    {
                        "rubric_id": d.rubric_id,
                        "name": d.name,
                        "weight": d.weight,
                        "verdict": d.verdict,
                        "points_earned": d.points_earned,
                        "points_possible": d.points_possible,
                        "reason": d.reason,
                    }
                    for d in r.dim_results
                ],
            })
        output_path = Path(args.output)
        output_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
        print(f"Results saved to {output_path}")
        # Auto-generate markdown report alongside the JSON
        md_path = output_path.with_suffix(".md")
        write_markdown_report(results, md_path)


if __name__ == "__main__":
    main()
