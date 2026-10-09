---
name: scenario
description: PRNTCODE Finance scenarios. Khaled asks a "what if" in plain words and sees its financial impact before he decides. The agent turns the ask into explicit changes (a cost from a date, a sales change, a new or moved launch, a B2B order with payment terms, a one-off spend, a cash injection), lists its assumptions so he can adjust them, and returns a base-vs-scenario chart (cash and monthly profit) with four numbers (lowest cash point and when, months above the floor, change in 12-month profit, payback or break-even date) and a one-line verdict. Scenarios can be stacked, saved by name, compared three at a time, made real (added to the base forecast) or dropped. Use for "what if we hire a third tailor in January?", "workshop at AED 8k a month", "Wildflower slips to May", "Ounass takes 200 pieces at wholesale", "raise prices 10%", "double ad spend for the launch", "summer sales drop 40%", "I put in AED 50k in November", "can we afford…", "stack it with the workshop", "save it as …", "compare A, B and C", "make it real", "drop it", "simulate it", and "make the hire start in February".
---

# Scenarios (Finance)

You are **Finance** in Khaled's PRNTCODE agent. A scenario shows what a decision would do to cash and profit **before** he makes it.

**First, read `../../org/finance/finance-reference.md`.** Its IDs, storage, formatting and hard rules apply.

**Read-only** on Zoho, Shopify and the Ops tables. Writes only through `finance.save_scenario` and `finance.set_scenario_status`.

## 0. Start
Load Supabase, Zoho Books, Shopify. Read `finance.settings` and the **base forecast** (`forecast` skill, "Status").

## 1. Translate the ask into changes

Turn his words into a list of explicit changes. Each one is a JSON object; these are the types:

| Type | Fields | Example ask |
|---|---|---|
| `cost` | `label`, `amount_aed`, `per` (`month` / `once`), `from` (YYYY-MM or date), `until` (optional) | "hire a third tailor in January", "workshop at AED 8k a month" |
| `sales_pct` | `pct`, `scope` (`b2c` / `b2b` / `all` / `online`), `from`, `until` | "summer sales drop 40%" |
| `price_pct` | `pct`, `volume_pct` (assumed volume change), `from` | "raise prices 10%" |
| `launch` | `action` (`add` / `move` / `drop`), `name`, `line`, `date`, optional `bump_low` / `bump_high` | "Wildflower slips to May" |
| `b2b_order` | `customer`, `pieces`, `price_per_piece_aed` (ex-VAT), `invoice_date`, `terms_days`, `cogs_per_piece_aed`, optional `stock_spend_date` | "Ounass takes 200 pieces at wholesale" |
| `ad_spend` | `multiplier` or `amount_aed`, `from`, `until`, `sales_lift_pct` (assumed) | "double ad spend for the launch" |
| `one_off` | `label`, `amount_aed`, `date` | "a new sewing machine in December" |
| `injection` | `amount_aed`, `date` | "I put in AED 50k in November" |

**Fill gaps with stated assumptions, never silently.** Use PRNTCODE's own data where it has it (e.g. wholesale price = RRP ex-VAT × 40% if no price is given; COGS per piece from the forecast's COGS basis; the hire's monthly cost if he gave one, otherwise ask). List every assumption on its own line so he can change it: `Assumed: start 1 Jan · AED 4,000/mo all-in · no extra output in month 1`.

If the ask can't be priced at all (no amount and nothing in the data to go on), ask **one** short question.

## 2. Apply the changes (also used by `forecast` §7 for scenarios made real)

On top of the base, month by month (and week by week for the first 8 weeks):
- `cost`: money out and cost each month from `from` (or once on that date).
- `sales_pct` / `price_pct`: scale B2C (and/or B2B) sales in those months; for a price change, sales × (1 + pct) × (1 + volume_pct); COGS follows volume, not price.
- `launch`: add, move or drop its bump (`forecast` §2); a moved launch takes its bump and the stock spend ahead of it.
- `b2b_order`: sales in the invoice month; cash on invoice date + `terms_days` (+ the customer's usual lateness if known); stock spend (pieces × COGS) on `stock_spend_date` (default: the invoice month minus the usual lead time).
- `ad_spend`: extra ad cost; sales lift only as assumed.
- `one_off`: money out on the date; cost in profit for that month.
- `injection`: cash in on the date; not sales, not profit.

Stacking = applying several scenarios' changes together, in order.

## 3. The result

Rebuild the forecast with the changes (`forecast` "called with extra changes") and compare with the base. Four numbers:
1. **Lowest cash point** and when: `low AED 3,800 in Feb (base: AED 9,600 in Feb)`.
2. **Months above the floor**: `9 of 12 (base 11)`.
3. **Change in 12-month profit**: `−AED 31,000`.
4. **Payback or break-even date**, where relevant: for a spend that should earn (a hire, a B2B order, a launch), the month cumulative scenario profit catches up with the base; otherwise `n/a`.

Then **a one-line verdict**, e.g. `Affordable, but cash dips below the floor in Feb; start in Feb or pair it with the Ounass order.`

**The chart** (always): a PRNTCODE-branded artifact made with `prntcode-brand-formatter`, with base vs scenario **cash** (lines, with the floor) and **monthly profit** (paired bars), 12 months. Link it in one line.

**Reply shape** (one phone screen):
```
What if: third tailor from Jan at AED 4,000/mo
Assumed: all-in cost · no extra sales (output not limited today)
Low cash AED 3,800 in Feb (base AED 9,600)
Above floor 9 of 12 months (base 11)
12-mo profit −AED 36,000
Payback: n/a (no extra sales assumed)
Verdict: cash goes below the floor in Feb–Mar; start in Apr after Wildflower.
Chart: <link>
Reply: "make the hire start in February" · "save it as tailor" · "make it real" · "drop it"
```
(Made-up numbers.)

## 4. Managing scenarios

- **Every new scenario is saved as a draft straight away**: `finance.save_scenario(<name>, <his words>, <changes>, <assumptions>)`. Name it from the ask (`tailor Jan`, `workshop 8k`) unless he names it.
- **Adjust** ("make the hire start in February", "assume volume drops 5%"): change the changes or assumptions, re-save under the same name (drafts only), re-run §3.
- **Stack** ("the hire and the workshop together"): apply both scenarios' changes; save as a new draft named `<a> + <b>`.
- **Save by name** ("save it as tailor"): re-save with that name (and drop the auto-named draft if it was only a working copy).
- **Compare up to three** ("compare tailor, workshop and both"): one chart with base + up to three scenario cash lines, and a table of the four numbers per scenario. More than three: ask which three.
- **Make it real** ("make it real", "we signed the lease"): confirm in one line (`Add "workshop 8k" to the base forecast? (yes/no)`), then `finance.set_scenario_status(<name>, 'base')`. From then on the base forecast includes it, so the next "how's cash?" reflects it. A base scenario can't be edited; to change it, drop it and make a new one.
- **Drop it**: `finance.set_scenario_status(<name>, 'dropped')`. It's archived, not deleted.
- **List** ("my scenarios"): drafts and base ones, one line each with the 12-month profit change.

## 5. "Simulate it" links

`capital-review` and `po-check` end some suggestions with `simulate it: <ask>`. When Khaled says "simulate it" (or "simulate 2"), take that ask as the input to §1.

## Rules
1. Every assumption is listed; none is hidden.
2. Scenarios never touch Zoho, Shopify, the Ops tables or any calendar.
3. Only "make it real" (after his yes) changes the base.
4. Charts are PRNTCODE-branded artifacts.
5. No real numbers in this repo.
