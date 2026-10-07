---
name: collection-review
description: PRNTCODE Strategy's collection review. Ends in the Track A line plan for one product line (RTW spring/summer, RTW fall/winter, an abaya drop or the Ramadan jalabiyas), each on its own calendar, as counts not designs (e.g. "8 tops, 4 of them long-sleeve"), with units, first run and restock, size split, last price, carry-over and new print slots, the reason for every line, and how far the history behind it can be trusted. Built from Shopify sales, planned for in-house production. Use when Khaled says "collection review", "line plan", "what does Track A need", "how many tops / abayas do we need", "plan spring summer", "plan the Ramadan drop", "starting point for the next collection", "stage 00 pack", "check Wildflower against past sales". Read-only. Never plans Track B. Not the catalogue (tag) review, which is Operations' prntcode-catalogue-review.
---

# PRNTCODE collection review (Strategy)

## The end goal

**The full Track A line plan for one line's next collection, and why.** Counts, not designs:

```
## How much to trust this: LOW
- Learned from The Jungle Edit (launched Jun 2026): 4 months of sales so far (Jun 8, Jul 88, Aug 17, Sep 8).
- Wildflower SS27 sells for 6 months, longer than the history. Months 5–6 are extrapolated.
- 73% of The Jungle Edit's units came in month 2. If that was a one-off, units to make fall from 182 to about 82.

## What Track A needs
- 8 tops (4 long sleeve tops, 3 smocked tops, 1 halter top) · 84 units
- 7 bottoms (3 long skirts, 3 pants, 1 midi skirt) · 73 units
- 2 dresses (2 long dresses) · 25 units
- Total: 17 styles, 182 units. First run 93 to make, 89 held back to restock what sells.
- Track B reserve: about 98 more units, planned by Hessa and the design seat without sales data.
```

Then one line per silhouette (styles, first run + restock, first-run sizes, last price, print slots, **why**), what's not in Track A and why, and month by month how the numbers were reached.

Everything else in this skill is the evidence for that plan.

## Lines run on their own calendars

PRNTCODE's lines don't share a season, so **a plan is always for one line, from that line's category only.** Never blend ready-to-wear, abayas and jalabiyas into one plan. The calendar comes from the PRNTCODE Collection Calendar (PC-OPS-CAL-01) and lives under `lines` in `references/catalogue-map.json`:

| Line | Launch | On sale until | Learns from |
|---|---|---|---|
| `rtw-ss` RTW Spring/Summer | April | the Fall/Winter launch (October) | past RTW collections, by months since launch |
| `rtw-fw` RTW Fall/Winter | October | the Spring/Summer launch (April) | past RTW collections, by months since launch |
| `abaya-initial` | September | the pre-Ramadan drop | the same months last year |
| `abaya-pre-ramadan` | a week before Ramadan | the summer drop (June) | the same months last year |
| `abaya-summer` | June | the initial drop (September) | the same months last year |
| `jalabiya` | a week before Ramadan | through Ramadan and Eid (2 months) | past Ramadan drops, by months since launch |
| `swimwear` | May | 5 months | nothing yet: plan it as Track B or a small test |

"Spring summer" means `rtw-ss`. If Khaled asks for a season without naming a line, plan the RTW line for that season and say the abaya and jalabiya drops are separate runs.

**Two ways to learn from the past:**
- **By collection** (RTW, jalabiyas): line the new collection up against past collections **by months since launch**, not by calendar month. Month 1 of the new collection is compared with month 1 of the last one. That's what makes a late launch comparable: the Jungle Edit launched in June 2026, so its first month was June.
- **By season** (abayas, which sell all year): each month of the window uses the same month last year.

Past collections are listed under `collections` in the catalogue map. **Add each new collection when it launches**, with its launch month, or the next plan can't line it up.

## How much to trust the history

Every plan states a confidence level, because a line with one short collection behind it can't carry the same weight as a line with years of sales.

| Confidence | When | What it changes |
|---|---|---|
| **Low** | one past collection with under 6 months of sales, or under 6 months of seasonal history | first run 50% (the rest held back to restock), units spread half by sales and half evenly, silhouettes with under 5 sales called *unproven*, not dropped |
| **Medium** | 6+ months of history | first run 60%, units spread a quarter evenly, thin silhouettes *unproven* |
| **High** | 2+ past collections with 6+ months, or 12+ months of seasonal history | first run 70%, units allocated by sales, thin silhouettes dropped |

In-house production makes this cheap: a smaller first run and a bigger restock reserve cost little when there's no minimum order.

**Two more checks the planner makes:**
- **Longer window than the history.** When the new collection sells for longer than the past one has been on sale (Wildflower's 6 months against the Jungle Edit's 4), the extra months are extrapolated at the last two months' rate. They're marked *extrapolated* in the month-by-month table.
- **One month carrying the history.** If one month holds over half a past collection's units (the Jungle Edit's July: 73%), the plan says so and gives the smaller number if that month was a one-off. Run again with `--drop-spike` to get that version's full line. Lines whose launch month is meant to peak (jalabiyas at Ramadan, `expect_launch_peak`) aren't flagged.

## Where this sits in the Collection Design Process

The process doc is **🧵 Collection Design Process** (PC-OPS-CDP-09) in Notion: `https://app.notion.com/p/3c5e351b3578817d97f6e7ba21561ad7`.

**Production and sampling are now in-house** (the tailors and embroiderers; see the Atelier brief). The process doc still describes Deepwear blocks, factory sampling, MOQs and freight. Until it's revised, this skill assumes:

- **Track A is built on proven silhouettes**: PRNTCODE's own patterns that have already sold.
- **No minimum orders.** So the buy is a **first run plus a restock reserve**, not one bulk order.
- **Capacity limits the first run.** The Atelier will know the team's output; until then capacity isn't checked unless Khaled gives a number.

| Stage | Use |
|---|---|
| **00 · Collection budget** (Khaled, GATE) | Track A units → materials and labour cost → the budget |
| 01 · Trend research and brand track | **Nothing.** Track B is designed without sales data. The plan only reserves its share |
| **02 · Silhouette selection and commercial core** | The line plan **is** the draft Track A style list |
| **11 · Buy commitment** | First run, restock reserve and size curve per silhouette |

Rules: **directional** (Khaled signs the budget, Hessa signs the range); **Track A only** (never plan Track B from sales, never average the tracks); **prints are Hessa's** (the plan names print *slots*; a carry-over holds only if she keeps that print). **Read-only**: never writes to Shopify, Notion, the ledger or a calendar.

## Step 1: Scope

| Setting | Default | Flag |
|---|---|---|
| Line | from the request ("spring summer" → `rtw-ss`) | `--line rtw-ss` (or an alias) |
| Year | the line's next launch | `--year 2027` |
| Collection name | "<line> <year>"; use the Game Plan name if known | `--collection "Wildflower SS27"` |
| Growth on last year | 0% (Khaled's call) | `--growth 0.1` |
| Team capacity before launch | not checked | `--capacity 300` |
| Focus (listings to count as already made) | the collection's name | `--focus Wildflower` |
| Sales period to learn from | the 12 complete months before this month | in the queries |

The launch month and window come from the line's calendar, not a flag. Other settings (target sell-through 80%, Track A 65% of the collection, units per style, carry-over cap 50%) live under `plan` in the catalogue map. Say in the report which were used.

## Step 2: Pull the data (five ShopifyQL queries)

Use the Shopify connector's `run-analytics-query` tool (load it with ToolSearch if it's deferred). Run the queries **one at a time, about 30 seconds apart**; if one returns "Rate limited", wait about 75 seconds and retry once.

Replace `<SINCE>` and `<UNTIL>` with the period (on 7 Oct 2026: `2025-10-01` and `2026-09-30`). Save each result **exactly as the tool returned it** to a working folder, e.g. `collection-review-data/`. The file names matter.

| # | File | Query | Needed for |
|---|---|---|---|
| 1 | `products.json` | `FROM sales SHOW orders, quantity_ordered, quantity_returned, net_items_sold, gross_sales, discounts, sales_reversals, net_sales GROUP BY product_title, product_type SINCE <SINCE> UNTIL <UNTIL> ORDER BY net_sales DESC LIMIT 1000` | everything (required) |
| 2 | `channels.json` | `FROM sales SHOW net_items_sold, gross_sales, discounts, net_sales GROUP BY product_title, sales_channel SINCE <SINCE> UNTIL <UNTIL> ORDER BY net_sales DESC LIMIT 1000` | evidence |
| 3 | `variants.json` | `FROM sales SHOW net_items_sold, net_sales GROUP BY product_title, product_type, product_variant_title SINCE <SINCE> UNTIL <UNTIL> ORDER BY net_items_sold DESC LIMIT 1000` | size split |
| 4 | `monthly.json` | `FROM sales SHOW net_items_sold, gross_sales, discounts GROUP BY product_title TIMESERIES month SINCE <SINCE> UNTIL <UNTIL> LIMIT 1000` | the line plan (required) |
| 5 | `inventory.json` | `FROM inventory SHOW ending_inventory_units, inventory_units_sold, sell_through_rate GROUP BY product_title SINCE <SINCE> UNTIL <UNTIL> ORDER BY inventory_units_sold DESC LIMIT 1000` | sell-through, stock already made |

If query 2, 3 or 5 keeps failing, carry on: the scripts skip what they can't build and say so. Without queries 1 and 4 there's no line plan.

## Step 3: Run the scripts

```
python3 <skill>/scripts/line_plan.py collection-review-data --line rtw-ss --year 2027 --collection "Wildflower SS27" --focus Wildflower
python3 <skill>/scripts/line_plan.py collection-review-data --line rtw-ss --year 2027 --collection "Wildflower SS27" --focus Wildflower --drop-spike   # only if the plan flags a peak month
python3 <skill>/scripts/collection_review.py collection-review-data --line rtw-ss --period "Oct 2025 – Sep 2026"
```

- **`line_plan.py`** writes the end goal: how much to trust it, what Track A needs, the line and why, what's not in Track A, and month by month how the numbers were reached.
- **`collection_review.py --line`** writes the evidence for that line's category only: sell-through by print, stock on hand, silhouette calls (confidence-aware), print pairings, price tiers, size run, channels, launch and pace.
- **`lines.py`** holds the calendars, the launch-aligned history and the confidence rules; both scripts use it.

**If you can't run code**, build the same tables by hand from the five results, following "How the plan is built". It's slower, but the method is the same.

### How the plan is built

1. **Window**: the line's launch month until its next line launches (or its fixed window).
2. **Expected sales per month of the window**: by collection (the past collection's month 1, month 2… lined up by months since launch; months beyond its history extrapolated at its last two months' rate) or by season (the same month last year).
3. **Units to make** = expected sales × (1 + growth) ÷ target sell-through.
4. **Silhouettes** (that line's category only) get units by their sales and Track A call: *carry* and *too new* at full weight, *watch* and *rework* at half, *drop* and *unproven* at zero. With lower confidence, part of the units is spread evenly across the eligible silhouettes (still at half weight for watch and rework). A silhouette whose share is under half a style is folded into the rest.
5. **Styles** = units ÷ units per style (10 per ready-to-wear piece, 20 per abaya, 6 per jalabiya).
6. **Print slots**: proven pairings on that silhouette (5+ units, normal discount and returns), up to half the styles. The rest are new slots.
7. **First run** = the confidence level's share of units, less anything already made for the collection in this line. The rest is the restock reserve.
8. **Capacity**, if given, caps the first run. **Track B** = the remaining 35% of the collection, reserved.

### The silhouette calls

| Call | Rule |
|---|---|
| **Too new to call** | on sale for fewer than 3 months |
| **Unproven** (low or medium confidence) | fewer than 5 units: too few sales to judge. Test as one small style, or leave to Track B |
| **Drop from Track A** (high confidence) | fewer than 5 units after 3+ months: could return as Track B |
| **Carry only if reworked: sold on discount** | discount more than 5 points above the line's average |
| **Carry only if reworked: high returns** | over 25% of units ordered came back: fix the pattern or make before it's remade |
| **Carry into Track A** | at or above its fair share of the line's sales |
| **Watch** | sells, below its share, normal discount and returns |

### How titles are read

- **Two naming eras.** Until April 2026 abayas were titled `The <Print> - Reversible Abaya` (or just `The <Print>`); from April 2026 `The Reversible Abaya in <Print>` / `The Abaya in <Print>`. Same product, merged by print and silhouette.
- **Print** = the text after the last ` in `, or before ` - ` in old titles; aliases fold colourway names into their print.
- **Category** = `product_type`; a blank type falls back to the title ("Abaya", `MKWR` → jalabiya, scrunchies, scarves, twillies → accessories). Category decides which line a listing belongs to.
- **Silhouette** = abayas: *Reversible Abaya* or *Abaya*; ready-to-wear: the text before ` in `. **Families** (tops, bottoms, dresses…) under `plan.families`.

## Step 4: Check the plan before sending it

- **Confidence.** Lead with it. If it's low, say what the plan is resting on.
- **Peak month.** If flagged, run `--drop-spike` and include its *What Track A needs* as the other reading.
- **Rework lines.** Name what has to be fixed before they're remade.
- **Capacity.** If none was given, say the first run is unchecked against the team.
- **Already made.** Stock already made for the collection is counted only in its own line; listings with the collection's name in another line are named but not counted (e.g. the Burlwood Wildflower abaya in an RTW plan).

## Step 5: Report

Write `track-a-line-plan-<collection>-<YYYY-MM-DD>.md` and send it with `SendUserFile`:

```
[line_plan.py output]

## ✍️ The other reading (only if a peak month was flagged)
[--drop-spike's What Track A needs, and one line on what would make each reading right.]

## ✍️ Settings used, and what to change
[Line and window, growth, target sell-through, first run (from confidence), capacity.]

## ✍️ Still needed to sign the stage 00 budget (not in Shopify)
| Input | Where it comes from |
|---|---|
| Materials cost per style (fabric, trims, print) | the costing sheet / suppliers |
| Labour minutes per style | the Atelier's standard times (estimates until it has data) |
| Team capacity before launch | the Atelier |
| Current cash position and committed spend | Zoho Books / the living cash model (Finance) |
| Non-product costs: shoots, gifting, launch marketing, any event | Zoho Books |

## Evidence
[collection_review.py --line output]

## ✍️ Data caveats
```

Then reply in chat with the confidence line, the **What Track A needs** bullets as written, and the other reading in one line if there is one.

If Khaled asks to share it with Hessa or the design seat, send the line plan and Part 2, and keep it out of Track B's work.

## Known data problems (as of 7 Oct 2026)

- **Unnamed sales.** Custom line items with no product (mostly one 668-item order in December 2025) can't be assigned to a line and are left out.
- **Placeholder abaya stock.** Pre-April 2026 abaya listings carry 4,000–5,000 units each and are skipped; newer ones (90–630) are *unverified*.
- **Pre-order listings** (`PRE ORDER - …`) are allowances, not stock.
- **No costs in Shopify**, so no margin.
- **No track tags** on listings yet.
- **One RTW collection so far** (the Jungle Edit, from June 2026), so RTW plans are low confidence until a second collection has sold for a season.
- **Data starts June 2025.**

When a new print, colourway, silhouette, channel, product type, **collection** or **calendar change** appears, update `references/catalogue-map.json`, not the scripts.

## Rules

- Read-only: Shopify analytics, and the Game Plan tracker if connected.
- One line per plan, from that line's category only.
- Counts, not designs. Never sketch, describe or name a design.
- Directional, with its confidence stated.
- Track A only. Never plan Track B from sales or average the tracks; never recommend dropping a print.
- Don't invent numbers: every figure comes from the scripts or the five query results.
- Hand-offs: prices and margins to Sales' `prntcode-pricing`; catalogue and track tags to Operations' `prntcode-catalogue-review`; making it to the Atelier (Operations, planned).
