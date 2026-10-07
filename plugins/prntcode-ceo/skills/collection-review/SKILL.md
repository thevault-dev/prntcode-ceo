---
name: collection-review
description: PRNTCODE Strategy's collection review. Designs the Track A side of one line's next collection holistically for in-house production (RTW spring/summer, RTW fall/winter, an abaya drop or the Ramadan jalabiyas, each on its own calendar), as counts not designs. It says how many of each piece (e.g. "18 tops, 8 of them long-sleeve"), wide and shallow with small test runs, grouped into print stories (what each fabric makes, accessories from the offcuts, checked against fabric in the Ops App), with first run and restock, sizes, last price, the reason for every line, and how far the history can be trusted. Use when Khaled says "collection review", "line plan", "what does Track A need", "how many tops do we need", "plan spring summer", "plan the Ramadan drop", "what should each print make", "starting point for the next collection", "check Wildflower against past sales". Read-only. Never plans Track B. Not the catalogue (tag) review, which is Operations' prntcode-catalogue-review.
---

# PRNTCODE collection review (Strategy)

## The end goal

**The Track A side of one line's next collection, designed as a whole, and why.** Counts, not designs:

```
## How much to trust this: LOW
- Learned from Jungle Edit RTW SS (launched 2026-07-01; Ops App): 3 months on sale so far.
- 78% of its units sold in its launch month. With a quieter launch, units to make fall from 222 to about 114.

## What Track A needs
- 18 tops (8 long sleeve tops, 7 smocked tops, 3 halter tops) · 91 units
- 17 bottoms (7 long skirts, 6 pants, 2 midi skirts, 1 short skirt (test), 1 shorts (test)) · 85 units
- 7 dresses (5 long dresses, 1 panel dress (test), 1 slit dress (test)) · 33 units
- 5 accessories (3 scrunchies, 2 head scarves) · 25 units
- Total: 47 styles in 7 prints, 234 units. First run 125 to make, 109 held back to restock what sells.

## Print stories: what each fabric makes
| Checkered Orchid | long sleeve top ×2, long skirt, smocked top, pants, long dress, halter top, … , scrunchie |
| New print A      | long sleeve top, long skirt, smocked top, pants, long dress |
```

Then: the fabric check, one line per silhouette (styles, first run + restock, sizes, last price, **why**), what's not in Track A and why, and month by month how the numbers were reached. Everything else in this skill is the evidence for that plan.

## How a collection is designed now (in-house)

Sampling and production are in-house, and fabric is bought and held as stock, then cut into whatever it suits. So the plan is built as a whole, not as a list of products:

1. **How much the line can sell** in its window, from its own history (next section), adjusted for how far that history can be trusted.
2. **Wide and shallow.** About 5 pieces per ready-to-wear style, not 10, because there's no minimum order and what sells can be restocked mid-season. More styles, less risk on each.
3. **Small test runs for unproven shapes.** A silhouette with too few sales to judge gets one style of 3 pieces (up to 4 tests), rather than being dropped. Trying it costs little in-house.
4. **Print stories.** The styles are grouped by print so each fabric makes a set: one of each shape first, a top and a bottom where possible, a second colourway only when a shape has more styles than there are prints. Carried prints take the shapes they already sold in; new prints are Hessa's to fill. Accessories (scrunchies, head scarves) come from the offcuts of the prints with the most garments. That's why RTW lines include accessories, as the Ops App's RTW collection does.
5. **Fabric check.** With fabric stock and metres per piece in the Ops App, every print story is checked against the fabric on hand: short, or fabric left over for more pieces. Until the Atelier measures yields, the plan says the check isn't possible yet.

Ready-to-wear is designed this way on its own. Abayas and jalabiyas run on their own calendars and are separate plans.

## Lines run on their own calendars

**A plan is always for one line, from that line's categories only.** The calendar comes from the PRNTCODE Collection Calendar (PC-OPS-CAL-01) and lives under `lines` in `references/catalogue-map.json`:

| Line | Categories | Launch | On sale until | Learns from |
|---|---|---|---|---|
| `rtw-ss` RTW Spring/Summer | ready-to-wear + accessories | April | the Fall/Winter launch | past RTW collections, by months since launch |
| `rtw-fw` RTW Fall/Winter | ready-to-wear + accessories | October | the Spring/Summer launch | past RTW collections, by months since launch |
| `abaya-initial` | abayas | September | the pre-Ramadan drop | the same months last year |
| `abaya-pre-ramadan` | abayas | a week before Ramadan | the summer drop | the same months last year |
| `abaya-summer` | abayas | June | the initial drop | the same months last year |
| `jalabiya` | jalabiyas | a week before Ramadan | through Ramadan and Eid | past Ramadan drops, by months since launch |
| `swimwear` | swimwear | May | 5 months | nothing yet: Track B or a test |

"Spring summer" means `rtw-ss`. If the Ops App has the collection (e.g. Wildflower, 15 April 2027), its launch and close dates win over the calendar.

**Learning by collection** (RTW, jalabiyas) lines the new collection up against past ones **by months since launch**: the new month 1 against the last collection's month 1. Sales before a collection's official launch (a soft launch or pre-sale) count towards month 1. **By season** (abayas) uses the same calendar month last year.

## How much to trust the history

| Confidence | When | What it changes |
|---|---|---|
| **Low** | one past collection with under 6 months of sales, or under 6 months of seasonal history | first run 50%, units spread half by sales and half evenly, thin silhouettes get test runs |
| **Medium** | 6+ months of history | first run 60%, units spread a quarter evenly, thin silhouettes get test runs |
| **High** | 2+ past collections with 6+ months, or 12+ months of seasonal history | first run 70%, units allocated by sales, thin silhouettes dropped |

The planner also flags **a window longer than the history** (the extra months are extrapolated and marked) and **one month carrying the history** (over half the units; for the Jungle Edit, its launch month). It gives the quieter-launch number and `--drop-spike` gives that reading's full plan. Lines meant to peak at launch (jalabiyas at Ramadan) aren't flagged.

## Where this sits in the Collection Design Process

The process doc is **🧵 Collection Design Process** (PC-OPS-CDP-09) in Notion: `https://app.notion.com/p/3c5e351b3578817d97f6e7ba21561ad7`. It still describes Deepwear blocks, factory sampling and MOQs; until it's revised for in-house production, this skill assumes own patterns, no minimum orders (first run plus restock), capacity from the Atelier, and fabric held as stock.

| Stage | Use |
|---|---|
| **00 · Collection budget** (Khaled, GATE) | Track A units → materials and labour cost → the budget |
| 01 · Trend research and brand track | **Nothing.** Track B is designed without sales data; the plan only reserves its share |
| **02 · Silhouette selection and commercial core** | The line plan and print stories **are** the draft Track A style list |
| **11 · Buy commitment** | First run, restock reserve, size curve, and fabric per print |

Rules: **directional** (Khaled signs the budget, Hessa signs the range); **Track A only** (never plan Track B from sales, never average the tracks); **prints are Hessa's** (carried prints hold only if she keeps them; new prints are hers). **Read-only**: never writes to Shopify, the Ops App, Notion, the ledger or a calendar.

## Step 1: Scope

| Setting | Default | Flag |
|---|---|---|
| Line | from the request ("spring summer" → `rtw-ss`) | `--line rtw-ss` (or an alias) |
| Collection | the Ops App's upcoming collection for the line, else "<line> <year>" | `--collection "Wildflower SS27"` |
| Year | the line's next launch (ignored when the Ops App has the collection's dates) | `--year 2027` |
| Number of prints | as many as the last collection of the line | `--prints 6` |
| Growth on last year | 0% (Khaled's call) | `--growth 0.1` |
| Team capacity before launch | not checked | `--capacity 300` |
| Focus (listings to count as already made) | the collection's name | `--focus Wildflower` |
| Sales period | the 12 complete months before this month | in the queries |

Other settings (target sell-through 80%, Track A 65%, pieces per style, test runs, carry-over cap 50%) live under `plan` in the catalogue map. Say in the report which were used.

## Step 2: Pull the data

### Shopify (five ShopifyQL queries)

Use the Shopify connector's `run-analytics-query` tool. Run the queries **one at a time, about 30 seconds apart**; if one returns "Rate limited", wait about 75 seconds and retry once. Replace `<SINCE>` and `<UNTIL>` with the period (on 7 Oct 2026: `2025-10-01` and `2026-09-30`) and save each result **exactly as returned** to a working folder, e.g. `collection-review-data/`.

| # | File | Query | Needed for |
|---|---|---|---|
| 1 | `products.json` | `FROM sales SHOW orders, quantity_ordered, quantity_returned, net_items_sold, gross_sales, discounts, sales_reversals, net_sales GROUP BY product_title, product_type SINCE <SINCE> UNTIL <UNTIL> ORDER BY net_sales DESC LIMIT 1000` | everything (required) |
| 2 | `channels.json` | `FROM sales SHOW net_items_sold, gross_sales, discounts, net_sales GROUP BY product_title, sales_channel SINCE <SINCE> UNTIL <UNTIL> ORDER BY net_sales DESC LIMIT 1000` | evidence |
| 3 | `variants.json` | `FROM sales SHOW net_items_sold, net_sales GROUP BY product_title, product_type, product_variant_title SINCE <SINCE> UNTIL <UNTIL> ORDER BY net_items_sold DESC LIMIT 1000` | size split |
| 4 | `monthly.json` | `FROM sales SHOW net_items_sold, gross_sales, discounts GROUP BY product_title TIMESERIES month SINCE <SINCE> UNTIL <UNTIL> LIMIT 1000` | the line plan (required) |
| 5 | `inventory.json` | `FROM inventory SHOW ending_inventory_units, inventory_units_sold, sell_through_rate GROUP BY product_title SINCE <SINCE> UNTIL <UNTIL> ORDER BY inventory_units_sold DESC LIMIT 1000` | sell-through, stock already made |

### The Ops App (one read-only query)

The Ops App's database is the Supabase project **PRNTCODE-ops** (`nhimagmpcwlkbfygiowq`). Run this with the Supabase connector's `execute_sql` and save the `ops` object as `ops.json` in the same folder:

```sql
select json_build_object(
 'collections', (select json_agg(c) from (select collection_id, name, launch_date, sunset_date, status from public.collections where active order by launch_date) c),
 'products', (select json_agg(p) from (select distinct product_title, product_type, collection_id, print_id, made_to_order from public.products where active order by 1) p),
 'fabric', (select coalesce(json_agg(f), '[]'::json) from (select m.material_id, m.name, m.unit, coalesce(sum(case t.type when 'consumption' then -abs(t.qty) else t.qty end),0) on_hand from public.materials m left join public.material_transactions t using (material_id) where m.kind='fabric' and m.active group by 1,2,3) f),
 'yields', (select coalesce(json_agg(y), '[]'::json) from (select p.product_title, b.material_id, avg(b.standard_qty_per_unit) per_unit from public.boms b join public.products p using (sku) join public.materials m using (material_id) where m.kind='fabric' group by 1,2) y)
) ops;
```

It gives which listing belongs to which collection, each collection's launch and close dates, fabric on hand, and metres per piece. **Read only: never write to the Ops App.** If Supabase isn't connected, carry on without `ops.json`: the plan falls back to the `collections` list in the catalogue map and says the fabric check isn't possible.

Fabric is matched to prints by the print code (`BLM`, `CHKOR`…, under `print_codes`) or print name in the material's ID or name, so fabric materials need one of those in them.

## Step 3: Run the scripts

```
python3 <skill>/scripts/line_plan.py collection-review-data --line rtw-ss --collection "Wildflower SS27" --focus Wildflower
python3 <skill>/scripts/line_plan.py collection-review-data --line rtw-ss --collection "Wildflower SS27" --focus Wildflower --drop-spike   # only if a peak month is flagged
python3 <skill>/scripts/collection_review.py collection-review-data --line rtw-ss --period "Oct 2025 – Sep 2026"
```

- **`line_plan.py`** writes the end goal: trust, what Track A needs, print stories and the fabric check, the line and why, what's not in Track A, and how the numbers were reached.
- **`collection_review.py --line`** writes the evidence for that line's categories: sell-through by print, stock on hand, silhouette calls, print pairings, price tiers, size run, channels, launch and pace.
- **`lines.py`** holds the calendars, the Ops App reader, the launch-aligned history and the confidence rules.

**If you can't run code**, build the same tables by hand from the results, following "How a collection is designed now" and "The silhouette calls".

### The silhouette calls

| Call | Rule | In the plan |
|---|---|---|
| **Too new to call** | on sale for fewer than 3 months | full weight |
| **Carry into Track A** | at or above its fair share of the line's sales | full weight |
| **Watch** | sells, below its share, normal discount and returns | half weight |
| **Carry only if reworked** | discount over 5 points above the line's average, or over 25% returned | half weight; name what to fix |
| **Unproven** (low or medium confidence) | fewer than 5 units: too few sales to judge | a test run of 3, up to 4 tests; the rest to Track B |
| **Drop from Track A** (high confidence) | fewer than 5 units after 3+ months | left out (could return as Track B) |

### How titles are read

- **Two naming eras.** Until April 2026 abayas were `The <Print> - Reversible Abaya` (or `The <Print>`); since then `The Reversible Abaya in <Print>` / `The Abaya in <Print>`. Merged by print and silhouette.
- **Print** = the text after the last ` in `, or before ` - ` in old titles; aliases fold colourways into their print.
- **Category** = `product_type`; a blank type falls back to the title. Category decides the line.
- **Silhouette** = abayas: *Reversible Abaya* or *Abaya*; ready-to-wear: the text before ` in `. **Families** (tops, bottoms, dresses, accessories…) under `plan.families`.

## Step 4: Check the plan before sending it

- **Confidence.** Lead with it, and say what the plan rests on.
- **Peak month.** If flagged, run `--drop-spike` and include its *What Track A needs* as the other reading.
- **Print stories.** Check every print has a top and a bottom; say which carried prints depend on Hessa keeping them.
- **Rework lines and tests.** Name what to fix, and that tests are 3 pieces each.
- **Fabric and capacity.** Say plainly if either is unchecked.
- **Already made.** Counted only in its own line; same-name listings in another line are named, not counted.

## Step 5: Report

Write `track-a-line-plan-<collection>-<YYYY-MM-DD>.md` and send it with `SendUserFile`:

```
[line_plan.py output]

## ✍️ The other reading (only if a peak month was flagged)
[--drop-spike's What Track A needs, and one line on what would make each reading right.]

## ✍️ Settings used, and what to change
[Line and window, prints, pieces per style, tests, growth, target sell-through, first run, capacity.]

## ✍️ Still needed to sign the stage 00 budget
| Input | Where it comes from |
|---|---|
| Fabric on hand per print | the Ops App (materials of kind fabric) |
| Metres per piece | the Atelier, recorded as fabric lines in the Ops App's bills of materials |
| Materials cost per style (fabric, trims, print) | the costing sheet / suppliers |
| Labour minutes per style and team capacity before launch | the Atelier |
| Cash position and committed spend | Zoho Books / the living cash model (Finance) |
| Non-product costs: shoot, gifting, launch marketing, any event | Zoho Books |

## Evidence
[collection_review.py --line output]

## ✍️ Data caveats
```

Then reply in chat with the confidence line, the **What Track A needs** bullets as written, one line on the print stories, and the other reading in one line if there is one.

If Khaled asks to share it with Hessa or the design seat, send the line plan, print stories and Part 2, and keep it out of Track B's work.

## Known data problems (as of 7 Oct 2026)

- **Unnamed sales.** Custom line items with no product (mostly one 668-item order in December 2025) can't be assigned to a line.
- **Abayas are made to order** (Ops App), so their Shopify stock figures (4,000–5,000 on old listings, 90–630 on new) are allowances, never sell-through.
- **Pre-order listings** (`PRE ORDER - …`) are allowances, not stock.
- **No costs** in Shopify or the Ops App yet, so no margin.
- **No fabric or yields** in the Ops App yet, so no fabric check.
- **One RTW collection so far** (Jungle Edit RTW SS, launched 1 July 2026, closes 31 October), so RTW plans are low confidence until a second has sold through.
- **Ops App catalogue slips:** *The Twilly in Flutter Dot* carries print `CHKOR`, and *The Smocked Top in Bloomingfield* has no print. Fix them in the Ops App's reference sheet.
- **Data starts June 2025.**

When a print, colourway, silhouette, channel, product type, collection or calendar changes, update `references/catalogue-map.json` (or the Ops App), not the scripts.

## Rules

- Read-only: Shopify analytics, the Ops App (one SELECT), and the Game Plan tracker if connected.
- One line per plan, from that line's categories only.
- Counts, not designs. Never sketch, describe or name a design; new prints stay "New print A, B…".
- Directional, with confidence stated.
- Track A only. Never plan Track B from sales or average the tracks; never recommend dropping a print.
- Don't invent numbers: every figure comes from the scripts or the query results.
- Hand-offs: prices and margins to Sales' `prntcode-pricing`; catalogue and track tags to Operations' `prntcode-catalogue-review`; making it to the Atelier (Operations, planned).
