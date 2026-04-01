---
status: draft
last_verified: 2026-04-01
verified_by: weizheng
eval_path:
known_issues: []
---

# Skill: meal-planner

Generate a kid-friendly weekly meal plan using the child's food preferences file, with a matching grocery list. Addresses nutrition gaps flagged in the preference file (iron, omega-3, etc.).

---

## Usage

```
/meal-planner
/meal-planner --days 5
/meal-planner --days 7 --focus iron
/meal-planner --child lexi --days 7 --save
```

### Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--child` | auto-detect from `user_docs/kid_profile/` | Child name (matches `<name>_profile.md`) |
| `--days` | `7` | Number of days to plan (5 = weekdays only, 7 = full week) |
| `--focus` | (none) | Nutrition focus: `iron`, `omega3`, `calcium`, `vitamin-d` — prioritizes foods that address this gap |
| `--save` | off | Save output to `user_docs/food/YYYYMMDD_meal_plan.md` |

---

## What this skill does

1. **Read food preferences** — loads `user_docs/food/<child>_food_preference.md`
   - Likes / dislikes / OK / unknown
   - Nutrition TODOs (iron, vitamin D, omega-3, calcium targets)
   - Snack ideas already listed

2. **Read child profile** — loads `user_docs/kid_profile/<child>_profile.md`
   - Age, activity schedule (swim, lacrosse, etc.) — use to adjust portion guidance for active days

3. **Generate meal plan** — produce a markdown table with:
   - Breakfast, lunch, dinner for each day
   - One snack per day (rotate from snack list)
   - Active-day meals (swim days = higher carb/protein)
   - If `--focus iron`: at least 1 iron-rich item per day
   - If `--focus omega3`: fish appears at least once

4. **Generate grocery list** — grouped by category:
   - Produce, Protein, Dairy, Pantry, Snacks
   - Quantities estimated for the plan (e.g., "salmon fillets × 2")
   - Flags any "to try" items included in the plan

5. **Output format**:

```markdown
# Lexi's Meal Plan — Week of [date]

## Schedule context
- Swim: Tue, Thu 5:00–5:30pm → higher carb/protein dinner those nights
- [other activity days if applicable]

## Meal Plan

| Day | Breakfast | Lunch | Dinner | Snack |
|-----|-----------|-------|--------|-------|
| Mon | ... | ... | ... | ... |
...

## Nutrition check
- Iron: ✅ [list days/meals]
- Omega-3: ✅ [day + meal]
- Calcium: ✅ milk target met [X]/7 days

## Grocery List

### Produce
- Broccoli (1 head or bag)
- ...

### Protein
- Salmon fillets × 2
- ...

### Dairy
- Milk (2 gallons for week target)
- ...

### Pantry
- ...

### Snacks (pre-pack)
- ...
```

---

## Rules

- **Never include disliked foods**: no tomatoes, pickles, onions, spicy items, eggs
- **Variety**: no meal repeated more than twice in the week
- **Age-appropriate**: all meals suit a ~7-year-old in terms of complexity and portion
- **Practical**: meals are things a parent can make on a weeknight (≤30 min); mark any longer prep meals for weekends
- **"To try" items**: flag clearly with 🆕 in the meal plan — never presented as an established like
- **Nutrition over novelty**: if iron/omega-3 targets aren't met by preferred foods, suggest the most accepted bridge (e.g., fish sticks before sashimi)

---

## Files read

| File | Purpose |
|------|---------|
| `user_docs/food/<child>_food_preference.md` | Likes, dislikes, nutrition gaps, snack list |
| `user_docs/kid_profile/<child>_profile.md` | Age, activity schedule for calorie/macro adjustment |

## Files written

| File | When |
|------|------|
| `user_docs/food/YYYYMMDD_meal_plan.md` | Only when `--save` is passed |

---

## Example run

```
/meal-planner --days 7 --focus iron --save
```

Reads Lexi's food preferences and profile, generates a 7-day plan with iron-rich meals every day, and saves to `user_docs/food/20260401_meal_plan.md`.
