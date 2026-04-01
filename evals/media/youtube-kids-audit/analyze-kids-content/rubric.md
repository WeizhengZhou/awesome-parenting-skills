# Rubric: analyze-kids-content

Eight scored dimensions used to evaluate skill output quality.
Each dimension has a weight (1–3); higher weight = more critical.

Scoring per dimension: PASS = full weight points, FAIL = 0 points.
Maximum per test case = 18 points (sum of all weights).

---

## R1 — Adult Content Filtering

**Weight:** 3
**Applies to:** TC-001, TC-003 (mixed accounts with ignore_patterns)
**Not scored for:** TC-002 (dedicated child account, no adult content in history)

### Description

When a watch history contains adult content matching the profile's `ignore_patterns`,
the skill must completely exclude those channels from analysis. Adult channels must not
appear in the KEEP section, the ADD recommendations, or the curriculum channel table.
They may be mentioned once in the audit to acknowledge filtering, but must not be
treated as content for the child.

### PASS criteria (all must be true)

1. Zero channels matching the profile's `ignore_patterns` appear in the KEEP section
2. Zero channels matching the profile's `ignore_patterns` appear in the ADD section
3. Zero channels matching the profile's `ignore_patterns` appear in the curriculum table
4. The output either silently skips adult content or explicitly states it was filtered

### FAIL criteria (any one triggers FAIL)

- Any finance, tech news, adult drama, crypto, sports analysis, or news channel
  appears as a recommendation for the child
- Adult content is misclassified as educational content for the child
- The output includes adult channels in the KEEP or ADD sections

### Test case specifics

**TC-001:** Must filter: CNBC finance news, Chinese drama ENG sub, tech startup podcast,
crypto investing channels.

**TC-003:** Must filter: ESPN sports analysis, adult tech product review channels,
political news commentary.

---

## R2 — Educational Junk Food Detection

**Weight:** 3
**Applies to:** All TCs (calibration varies by profile)

### Description

"Educational Junk Food" is content that appears educational but is so far below the
child's current academic level that it provides no developmental value. The skill must
correctly identify such content for advanced learners — AND must correctly NOT flag
age-appropriate content as junk food for typical or below-level learners.

This dimension tests both directions: false negatives (missing junk food) AND false
positives (incorrectly flagging appropriate content).

### PASS criteria (all must be true)

1. Content more than 2 academic years below the child's stated level is labeled
   "Educational Junk Food" in the REMOVE section with an explicit explanation citing
   the specific level mismatch (e.g., "below Beast Academy 3B level")
2. The explanation names the specific curriculum or level of the child and compares
   it to the content level
3. Age-appropriate content is NOT incorrectly flagged as junk food (contrast test):
   - TC-002: Cocomelon and Super Simple Songs must NOT be labeled junk food
   - TC-003: Numberblocks visual patterns must NOT be labeled junk food (appropriate
     for a 9yo at grade-2 math level)

### FAIL criteria (any one triggers FAIL)

- Cocomelon, Numberblocks basic, or Blippi letter content kept in KEEP or ignored
  without flagging for TC-001 (advanced 7yo at Beast Academy 3B)
- Cocomelon or Super Simple Songs flagged as junk food for TC-002 (typical 5yo)
- Numberblocks flagged as junk food for TC-003 (9yo at grade-2 math level)
- Junk food flagged without explanation of the specific level mismatch
- Junk food content recommended in the ADD section for any TC

### Test case specifics

**TC-001 (flag as junk food):** Cocomelon nursery rhymes, Numberblocks basic counting,
Blippi letter/phonics videos. Explanation must reference Beast Academy 3B specifically.

**TC-002 (do NOT flag):** Cocomelon, Super Simple Songs are age-appropriate for a
typical kindergartener learning to count and read sight words.

**TC-003 (do NOT flag):** Numberblocks visual pattern content is appropriate for a
9yo whose math is at grade-2 level. Age alone does not determine junk food status;
academic level does.

---

## R3 — Math Level Calibration

**Weight:** 3
**Applies to:** All TCs

### Description

All math content recommendations in the ADD section must match or appropriately exceed
the child's stated math curriculum. The skill must not recommend content that is below
the child's math level (no basic counting for advanced learners) or far above it (no
algebra for a grade-2 math learner). Recommendations should extend the child's current
level toward the next challenge, not regress.

### PASS criteria (all must be true)

1. ADD section contains at least one named math channel or content type
2. All math ADD recommendations are at or above the child's stated math level
3. No basic counting, one-digit arithmetic, or phonics-adjacent math content is
   recommended for a child doing advanced math (TC-001)
4. No grade-5+ math content is recommended for a child at grade-2 math level (TC-003)
5. Math recommendations reflect the child's learning style:
   - TC-001: logic puzzles, proof-based thinking, conceptual math (e.g., TED-Ed
     Riddles, Mathologer, Numberphile Jr.)
   - TC-002: age-appropriate counting/addition enrichment (e.g., Numberblocks,
     ScratchJr math games description)
   - TC-003: visual/spatial math approaches (e.g., Khan Academy at grade-2 level,
     visual multiplication, geometry via Lego)

### FAIL criteria (any one triggers FAIL)

- Basic counting or Numberblocks recommended for TC-001 (Beast Academy 3B learner)
- Beast Academy or proof-based math recommended for TC-002 (kindergarten learner)
- Grade-5+ abstract math recommended for TC-003 (grade-2 math level)
- No specific math channel or content named in ADD section
- Math recommendations ignore the child's stated curriculum entirely

---

## R4 — Five-Goal Coverage

**Weight:** 2
**Applies to:** All TCs

### Description

The skill's ADD section must address the five core educational goals defined in the
skill prompt: Knowledge Breadth, English Skills, Math, Science, and SEL (Social-
Emotional Learning). Recommendations should be distributed across goals rather than
clustering in one area.

### PASS criteria

1. The ADD section contains recommendations that collectively address at least 4 of
   the 5 goals
2. At least one recommendation explicitly serves English Skills (not just reading
   level — vocabulary, comprehension, or narrative exposure)
3. At least one recommendation explicitly serves SEL or growth mindset
4. Goal labels appear in the curriculum channel table (Part 3)

### FAIL criteria (any one triggers FAIL)

- Fewer than 3 distinct goals represented in ADD recommendations
- No English Skills recommendation in ADD
- No SEL or growth mindset recommendation anywhere in the output
- Curriculum table is missing goal alignment column

---

## R5 — Output Structure Completeness

**Weight:** 2
**Applies to:** All TCs

### Description

The skill specifies an exact five-part output structure. All five parts must be present
and substantially complete. Missing sections indicate the model did not follow the
skill's instruction template.

### PASS criteria (all five must be present)

1. **Part 1: Content Audit** — narrative section identifying dominant content themes
   with engagement ratings and Educational Junk Food flags
2. **Part 2: Three-Way Classification** — explicit KEEP / REMOVE / ADD sections with
   labeled items and goal alignment rationale
3. **Part 3: Curriculum Channel Table** — Markdown table with columns: Channel/Playlist,
   Short Description, Why [Child] Needs This, Goal Alignment
4. **Part 4: Implementation Schedule** — table with morning / relaxed / car+bedtime
   time slots and example content for each
5. **Part 5: Next Steps Checklist** — 3-5 actionable checklist items using [ ] format,
   covering Subscribe, Remove, Buy/Borrow, and Ask [child] actions

### FAIL criteria

- Any of the 5 parts is entirely absent from the output
- KEEP / REMOVE / ADD classification is present but merged into a single list without
  clear labeling
- Curriculum table is a list instead of a Markdown table
- Next Steps has fewer than 3 items or uses paragraph format instead of checklist

---

## R6 — Recommendation Specificity

**Weight:** 2
**Applies to:** All TCs

### Description

ADD recommendations must name specific YouTube channels, playlists, or content series —
not generic descriptions. Vague recommendations like "find a good math puzzle channel"
or "look for educational science content" do not count. Real channel names that a parent
can search on YouTube immediately are required.

### PASS criteria

1. The ADD section names at least 5 specific YouTube channels by their exact channel
   name (e.g., "TED-Ed", "Kurzgesagt", "Mathologer", "Wild Kratts", "SciShow Kids")
2. Each named channel includes a one-sentence rationale for why it fits this specific
   child profile
3. Named channels are appropriate for the child's age range (not adult channels
   recommended for a 5-year-old)

### FAIL criteria (any one triggers FAIL)

- Fewer than 3 named specific channels in the ADD section
- Recommendations are purely generic ("educational math channel", "science videos")
- Channels are named but have no rationale connecting them to the child's profile
- Adult channels recommended for a young child

---

## R7 — Age Calibration Contrast

**Weight:** 2
**Applies to:** TC-001 and TC-002 (cross-case comparison)

### Description

This dimension specifically tests whether the skill applies consistent logic across
different child profiles rather than applying a fixed template. The same channel
(Cocomelon) should receive opposite verdicts for TC-001 and TC-002 because the profiles
are different. This confirms the skill is profile-driven, not channel-label-driven.

### PASS criteria (both must be true)

1. In TC-001 output: Cocomelon is classified in REMOVE and explicitly labeled as
   "Educational Junk Food" with an explanation citing the child's advanced level
   (Beast Academy 3B, chapter book reading)
2. In TC-002 output: Cocomelon is NOT in the REMOVE section AND is NOT labeled as
   junk food — it should be in KEEP or acknowledged as age-appropriate

Note: This dimension requires outputs from both TC-001 and TC-002 to evaluate.
When running a single TC, mark R7 as "N/A (requires both TC-001 and TC-002)".

### FAIL criteria

- Cocomelon receives identical treatment (both flagged OR both kept) regardless of
  the very different child profiles
- TC-002 flags Cocomelon as junk food despite the child being a typical 5yo
- TC-001 keeps Cocomelon without flagging despite Beast Academy 3B math level

---

## R8 — Trojan Horse Recommendation

**Weight:** 1
**Applies to:** All TCs

### Description

The "Trojan Horse" strategy is a core concept in this skill: use the child's known
interest domain as a vehicle to teach a gap subject. At least one ADD recommendation
must explicitly connect the child's stated interest to a subject they need to develop,
creating a bridge that makes the unfamiliar subject approachable through familiar
territory.

### PASS criteria

1. At least one ADD recommendation explicitly frames a gap subject through the
   child's interest domain
2. The connection is stated — not just implied (e.g., "Because Alex loves Lego, this
   channel uses spatial building to teach multiplication concepts")
3. Examples of valid Trojan Horse recommendations by TC:
   - TC-001: Harry Potter lore → history of medieval Europe; animals → biology + taxonomy
   - TC-002: Dinosaurs → geology + timeline concepts; trains → physics of motion
   - TC-003: Lego → geometry + multiplication; Minecraft → coordinate geometry + area

### FAIL criteria

- All ADD recommendations are direct (math channel for math gap, reading for reading gap)
  with no cross-domain bridge
- A cross-domain bridge is present in the output but never explicitly connected to
  the child's stated interests
- The recommendation uses generic interest framing ("since your child likes building")
  rather than referencing the specific interest named in the profile
