# Skill: order-food

> **Status: PLACEHOLDER** — Not yet implemented. Contributions welcome.

Automate food ordering for kids from supported delivery and restaurant platforms.

## Usage

```
/order-food [--platform doordash|ubereats|instacart] [--profile <child-name>] [--preset <meal-name>] [--dry-run]
```

## Planned capabilities

- Load a saved "kid-approved" meal preset (e.g. "Emma's usual: plain cheese pizza, apple juice, no onions")
- Place orders from a saved restaurant list without requiring manual review of menus
- Apply stored dietary restrictions / allergen blocklist before ordering
- Confirm order summary with parent before submitting payment
- Track order status and send ntfy alert when delivered

## Arguments (planned)

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--platform` | no | doordash | Delivery platform |
| `--profile` | no | all kids | Which child's preferences to apply |
| `--preset` | no | — | Named meal preset from `family-state.json` |
| `--restaurant` | no | — | Specific restaurant (overrides preset) |
| `--budget` | no | $25 | Per-order cap; abort if exceeded |
| `--dry-run` | no | false | Show order summary but do not submit |

## Design notes

### Safety gates (required before implementation)
- **Always** show itemized order + total + estimated delivery time and require parent `y/n` confirmation before payment
- Never store raw card numbers — use saved payment method token in platform (Tier 1: attach to existing Chrome session with saved payment)
- Allergen check: cross-reference each item name against `family-state.json > dietary_restrictions` using fuzzy match; block if match found
- Budget cap: hard-abort if cart total exceeds `--budget`; do not prompt to override

### Automation approach
- **Tier 1** (preferred): Attach to existing logged-in Chrome session — avoids re-auth, uses saved addresses and payment
- **Tier 2**: Playwright persistent profile with stored cookies
- Platform SDKs / APIs (DoorDash Drive API, Instacart Connect) where available — preferred over browser automation

### `family-state.json` schema (planned additions)
```json
{
  "kids": {
    "emma": {
      "dietary_restrictions": ["no nuts", "no shellfish"],
      "food_presets": {
        "lunch": {"restaurant": "Pizza My Heart", "items": ["Cheese slice", "Lemonade"]},
        "dinner_quick": {"restaurant": "Chipotle", "items": ["Kids quesadilla", "Apple juice"]}
      }
    }
  },
  "food_ordering": {
    "default_platform": "doordash",
    "default_address": "123 Main St, San Carlos, CA 94070",
    "budget_per_order": 25,
    "blocked_restaurants": []
  }
}
```

## Supported platforms (planned)

| Platform | Method | Auth |
|----------|--------|------|
| DoorDash | Browser (Tier 1) | Existing Chrome session |
| Uber Eats | Browser (Tier 1) | Existing Chrome session |
| Instacart | Browser (Tier 1) + API | Existing Chrome session |
| Safeway delivery | Browser (Tier 1) | Existing Chrome session |

## Implementation checklist

- [ ] Read `family-state.json` for child profile + dietary restrictions
- [ ] Navigate to platform, select restaurant from saved list
- [ ] Apply meal preset or browse menu
- [ ] Allergen cross-check before adding items to cart
- [ ] Show parent confirmation gate (items, total, ETA)
- [ ] Submit order on approval
- [ ] Send ntfy delivery alert
- [ ] Log order to `family-state.json > order_history`
