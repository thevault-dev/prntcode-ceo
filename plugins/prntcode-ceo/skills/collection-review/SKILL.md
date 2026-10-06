---
name: collection-review
description: PRNTCODE Strategy's collection review. Ends in the Track A line plan for the next collection, as counts not designs (e.g. "10 tops, 5 of them long-sleeve"), with units, first run and restock, size split, last year's price, carry-over and new print slots, and the reason for every line, built from prior-year Shopify sales and planned for in-house production. Also gives the evidence behind it and the stage 00 budget inputs. Use when Khaled says "collection review", "line plan", "what does Track A need", "how many tops / abayas do we need", "plan the Track A collection", "starting point for the next collection", "stage 00 pack", "check Wildflower against past sales", or asks what the next collection should be made of. Read-only. Never plans Track B (the brand track runs without sales data). Not the catalogue (tag) review, which is Operations' prntcode-catalogue-review.
---

# PRNTCODE collection review (Strategy)

## The end goal

**The full Track A line plan for a collection, and why.** Counts, not designs:

```
## What Track A needs
- 9 abayas (8 reversible abayas, 1 abaya) · 184 units
- 10 tops (5 long sleeve tops, 4 smocked tops, 1 halter top) · 103 units
- 8 bottoms (4 long skirts, 3 pants, 1 midi skirt) · 78 units
- 2 dresses (2 long dresses) · 21 units
- Total: 32 styles, 408 units. First run 290 to make, 118 held back to restock what sells.
- Track B reserve: about 220 more units, planned by Hessa and the design seat without sales data.
```

Then one line per silhouette: styles, units (first run + restock), first-run sizes, last year's price, print slots (proven carry-over pairings vs new slots for Hessa) and **why** (the call and the numbers behind it). After that comes what was left out of Track A and why, and how the numbers were reached.

Everything else in this skill is the evidence for that plan.

## Where this sits in the Collection Design Process

The process doc is **🧵 Collection Design Process** (PC-OPS-CDP-09) in Notion: `https://app.notion.com/p/3c5e351b3578817d97f6e7ba21561ad7`.

**Production and sampling are now in-house** (the tailors and embroiderers; see the Atelier brief). The process doc still describes Deepwear blocks, factory sampling, MOQs and freight. Until it's revised, this skill assumes:

- **Track A is built on proven silhouettes**: PRNTCODE's own patterns that have already sold, not a factory block catalogue.
- **No minimum orders.** So the buy is a **first run plus a restock reserve**, not one bulk order. Restock what sells, during the season.
- **Capacity limits the first run**, not MOQs or freight. The Atelier will know the team's weekly output; until then capacity isn't checked unless Khaled gives a number.
- **The main lumpy cost is materials** (fabric and trims), plus the team's time.

How the plan feeds the process:

| Stage | Use |
|---|---|
| **00 · Collection budget** (Khaled, GATE) | Track A units → materials and labour cost → the budget. The evidence tables give prior-year sell-through by print and category, as the process asks |
| 01 · Trend research and brand track | **Nothing.** Track B is designed without sales data. The plan only reserves its share of units |
| **02 · Silhouette selection and commercial core** | The line plan **is** the draft Track A style list: which silhouettes, how many styles, price tier and print slots |
| **11 · Buy commitment** | First run, restock reserve and size curve per silhouette |

Rules this skill keeps:

- **Directional.** Khaled signs the budget and Hessa signs the range. The plan is a starting point to change, never a decision.
- **Two scoreboards.** Track A only. Never plan Track B from sales, never assign past pieces to a track, never average the tracks.
- **Prints are Hessa's.** The plan names print *slots*. A carry-over slot names a print that already sold well on that silhouette, and it holds only if Hessa keeps that print in the year's allocation. The skill never recommends dropping a print.

**Read-only.** It never writes to Shopify, Notion, the ledger or a calendar.

## Step 1: Scope

Settle these from the request, the Game Plan tracker (if Notion is connected) and the defaults. Ask only if the collection or its launch month is truly unknown.

| Setting | Default | Flag |
|---|---|---|
| Collection name | "the next collection" | `--collection "Wildflower SS27"` |
| Launch month | the project's D-Day in the Game Plan; otherwise next month | `--launch 2027-04` |
| Selling window | 6 months | `--months 6` |
| Growth on last year | 0% (Khaled's call) | `--growth 0.1` |
| Team capacity before launch | not checked | `--capacity 300` |
| Focus (existing listings to count as already made) | the collection's name, e.g. "Wildflower" | `--focus Wildflower` |
| Sales period to learn from | the 12 complete months before this month | in the queries |

Other settings (target sell-through 80%, first run 70%, Track A 65% of the collection, units per style, carry-over cap 50%) live under `plan` in `references/catalogue-map.json`. Say in the report which defaults were used.

**Seasonality matters.** The plan uses the same months last year as the selling window wherever there's history, so a window must have been sold through last year to be planned well. If the selling window starts more than 12 months after the last month of data, widen the query period.

## Step 2: Pull the data (five ShopifyQL queries)

Use the Shopify connector's `run-analytics-query` tool (load it with ToolSearch if it's deferred). Run the queries **one at a time, about 30 seconds apart**. The analytics API rate-limits fast: if a query returns "Rate limited", wait about 75 seconds and retry it once. Don't fire them in parallel; a parallel batch fails together.

Replace `<SINCE>` and `<UNTIL>` with the period (on 6 Oct 2026: `2025-10-01` and `2026-09-30`). Save each result **exactly as the tool returned it** (the JSON object with `columns` and `rows`) to a working folder, e.g. `collection-review-data/`. The file names matter.

| # | File | Query | Needed for |
|---|---|---|---|
| 1 | `products.json` | `FROM sales SHOW orders, quantity_ordered, quantity_returned, net_items_sold, gross_sales, discounts, sales_reversals, net_sales GROUP BY product_title, product_type SINCE <SINCE> UNTIL <UNTIL> ORDER BY net_sales DESC LIMIT 1000` | everything (required) |
| 2 | `channels.json` | `FROM sales SHOW net_items_sold, gross_sales, discounts, net_sales GROUP BY product_title, sales_channel SINCE <SINCE> UNTIL <UNTIL> ORDER BY net_sales DESC LIMIT 1000` | evidence |
| 3 | `variants.json` | `FROM sales SHOW net_items_sold, net_sales GROUP BY product_title, product_type, product_variant_title SINCE <SINCE> UNTIL <UNTIL> ORDER BY net_items_sold DESC LIMIT 1000` | size split |
| 4 | `monthly.json` | `FROM sales SHOW net_items_sold, gross_sales, discounts GROUP BY product_title TIMESERIES month SINCE <SINCE> UNTIL <UNTIL> LIMIT 1000` | the line plan (required) |
| 5 | `inventory.json` | `FROM inventory SHOW ending_inventory_units, inventory_units_sold, sell_through_rate GROUP BY product_title SINCE <SINCE> UNTIL <UNTIL> ORDER BY inventory_units_sold DESC LIMIT 1000` | sell-through, stock already made |

If query 2, 3 or 5 keeps failing after its retry, carry on: the scripts skip what they can't build and say so. Without query 4 there's no line plan; say so and deliver the evidence only.

The tool also renders each result as a chart in the chat. Don't restate those numbers in the reply.

## Step 3: Run the two scripts

```
python3 <skill>/scripts/line_plan.py collection-review-data --collection "Wildflower SS27" --launch 2027-04 --focus Wildflower --json collection-review-data/plan.json
python3 <skill>/scripts/collection_review.py collection-review-data --period "Oct 2025 – Sep 2026" --focus Wildflower
```

- **`line_plan.py`** writes the end goal: what Track A needs, the line and why, what's not in Track A and why, and how the numbers were reached.
- **`collection_review.py`** writes the evidence: Part 1 for stage 00 (sell-through by print and category, what the year absorbed, stock on hand, sales not tied to a product), Part 2 for stage 02 (silhouette calls, print × category pairing, price tiers, size run) and an appendix (channels, launch and pace).

**If you can't run code**, build the same tables by hand from the five results, following "How the plan is built" and "How titles are read". It's slower, but the method is the same.

### How the plan is built

1. **Expected sales per category in the window**: units sold in the same months last year. Months with no history (e.g. before ready-to-wear launched) use the last-6-months rate.
2. **Units to make** = expected sales × (1 + growth) ÷ target sell-through.
3. **Silhouettes** get those units in proportion to last year's units, by their Track A call: *carry* and *too new* at full weight, *watch* and *rework* at half weight, *drop* at zero. A silhouette whose share is under half a style is folded into the rest.
4. **Styles** = units ÷ units per style (20 per abaya, 10 per ready-to-wear piece, 6 per jalabiya, 10 per accessory).
5. **Print slots**: proven pairings on that silhouette (5+ units, normal discount and returns), ranked by pace, fill up to half the styles. The rest are new slots.
6. **First run** = 70% of units, less anything already made for the collection. The rest is the restock reserve. First-run sizes follow the category's size curve.
7. **Capacity**: if given, the first run is scaled to fit it.
8. **Track B** = the remaining 35% of the collection's units, reserved and not planned.

A category with too few expected sales in the window is left out, and the plan says when it does sell. For example, jalabiyas sold only in February and March 2026 (Ramadan and Eid), so they belong in their own drop, not an April collection.

### The silhouette calls

| Call | Rule |
|---|---|
| **Too new to call** | on sale for fewer than 3 months |
| **Drop from Track A (could return as Track B)** | fewer than 5 units after 3+ months on sale |
| **Carry only if reworked: sold on discount** | discount more than 5 points above its category's average |
| **Carry only if reworked: high returns** | over 25% of units ordered came back: fix the pattern or make before it's remade |
| **Carry into Track A** | at or above its fair share of its category's sales |
| **Watch** | sells, below its share, normal discount and returns |

### How titles are read

- **Two naming eras.** Until April 2026 abayas were titled `The <Print> - Reversible Abaya` (or just `The <Print>`). From April 2026 they're `The Reversible Abaya in <Print>` / `The Abaya in <Print>`. Same product, relisted, and merged by print and silhouette.
- **Print** = the text after the last ` in `, or before ` - ` in old titles. Aliases in `catalogue-map.json` fold colourway names into their print (`Metamorphosis Lavender` → Metamorphosis).
- **Category** = `product_type`. Old Butterfly listings have a blank type, so the title decides: "Abaya" → abaya, `MKWR` → jalabiya, scrunchies, scarves and twillies → accessories.
- **Silhouette**: abayas are *Reversible Abaya* or *Abaya*; ready-to-wear is the text before ` in `. **Families** (tops, bottoms, dresses…) are set under `plan.families`. Add a new silhouette there when one appears.
- **New print names need no code change.**

## Step 4: Check the plan before sending it

Read the plan as Khaled would, and note in the report anything that needs his judgement:

- **One-off spikes.** A pop-up or bulk month in last year's window inflates the plan (ready-to-wear's July 2026 is the obvious one). Say so if one month carries a large share of a category's window.
- **Rework lines.** A *carry only if reworked* silhouette stays in the plan at half weight. Name what has to be fixed.
- **Capacity.** If no capacity was given, say the first run is unchecked against the team.
- **Already made.** Stock already made for the focus collection is counted against its silhouette (e.g. 90 Burlwood Wildflower reversible abayas).

## Step 5: Report

Write `track-a-line-plan-<collection>-<YYYY-MM-DD>.md` and send it with `SendUserFile`:

```
[line_plan.py output: What Track A needs · The line, and why · Not in Track A · How the numbers were reached]

## ✍️ Settings used, and what to change
[Window, growth, target sell-through, first run share, capacity: one line each, with the defaults named.
Any step 4 flags.]

## ✍️ Still needed to sign the stage 00 budget (not in Shopify)
| Input | Where it comes from |
|---|---|
| Materials cost per style (fabric, trims, print) | the costing sheet / suppliers |
| Labour minutes per style | the Atelier's standard times (estimates until it has data) |
| Team capacity before launch | the Atelier |
| Current cash position and committed spend | Zoho Books / the living cash model (Finance) |
| Non-product costs: shoots, gifting, launch marketing, any event | Zoho Books |
| Book value of stock on hand | units × cost |

## Evidence
[collection_review.py output: Part 1 · Part 2 · Appendix]

## ✍️ Data caveats
[Period; sales not tied to a product; placeholder and pre-order stock; abaya pace is not
sell-through; no costs or margin in Shopify; missing queries.]
```

Then reply in chat with the **What Track A needs** bullets as written, plus one line on the biggest caveat or flag. Nothing else; the file has the rest.

If Khaled asks to share it with Hessa or the design seat, send the line plan and Part 2, and keep it out of Track B's work.

## Known data problems (as of 6 Oct 2026)

- **Unnamed sales.** About a fifth of net sales are custom line items with no product, mostly one 668-item order in December 2025. They're left out.
- **Placeholder abaya stock.** Pre-April 2026 abaya listings carry 4,000–5,000 units each and are skipped. Newer abaya listings (90–630 units) may be made-to-order allowances: shown as *unverified*, never used for sell-through.
- **Pre-order listings** (`PRE ORDER - …`) are allowances, not stock.
- **No costs in Shopify**, so no margin.
- **No track tags** on listings yet. Tagging each listing with its track (an Operations catalogue-review job) will let next year's review score each track on its own.
- **Launch dates** aren't stored; the first month with a sale stands in.
- **Data starts June 2025.**

When a new print, colourway name, silhouette, channel or product type appears, add it to `references/catalogue-map.json`, not to the scripts.

## Rules

- Read-only: Shopify analytics, and the Game Plan tracker if connected.
- Counts, not designs. Never sketch, describe or name a design.
- Directional. Every number is a starting point the gate owners can change.
- Track A only. Never plan Track B from sales or average the tracks; never recommend dropping a print.
- Don't invent numbers: every figure comes from the scripts or the five query results.
- Hand-offs: prices and margins to Sales' `prntcode-pricing`; catalogue and track tags to Operations' `prntcode-catalogue-review`; making it to the Atelier (Operations, planned).
