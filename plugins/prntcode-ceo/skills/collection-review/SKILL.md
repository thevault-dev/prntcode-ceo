---
name: collection-review
description: PRNTCODE Strategy's collection review, the starting point of the Collection Design Process (PC-OPS-CDP-09). Reads prior-year Shopify sales and builds the stage 00 sell-through input for Khaled's collection budget (sell-through by print and category, what the year absorbed, stock still on hand) plus the directional stage 02 input for the Track A commercial core (silhouettes to carry, print × category pairings, price tiers, size run). Use when Khaled says "collection review", "run the collection review", "stage 00 pack", "starting point for the next collection", "prior-year sell-through", "what sold last year", "which silhouettes should Track A carry", "check Wildflower against past sales", or asks for the sales input to a collection budget. Read-only. Never feeds stage 01 (trend research and the brand track run without sales data). Not the catalogue (tag) review, which is Operations' prntcode-catalogue-review.
---

# PRNTCODE collection review (Strategy)

## Where this sits in the Collection Design Process

The process doc is **🧵 Collection Design Process** (PC-OPS-CDP-09) in Notion: `https://app.notion.com/p/3c5e351b3578817d97f6e7ba21561ad7`. This review supplies its sales inputs. Until the operator ledger exists, it also stands in for the sales half of the stage 19 year-end review pack, which "feeds directly into the next collection budget at stage 00".

| Stage | What the process asks for | Where it is in this review |
|---|---|---|
| **00 · Envelope and collection budget** (Khaled, GATE) | Prior-year sell-through by print and category, *directional only*; Archive stock still carrying book value | **Part 1**: the starting point |
| 01 · Trend research and brand track (Hessa + design seat) | **Sell-through data explicitly excluded** | Nothing. Never send this review into stage 01 |
| **02 · Factory silhouette selection and commercial core** (design seat + Hessa, GATE) | Prior sell-through, caveated as directional; established price tier structure | **Part 2**, handed over at stage 02, after Hessa has approved Track B direction |

Rules from the process that this skill follows:

- **Directional, never decisive.** Every table carries that caveat. Khaled signs the budget; Hessa and the design seat select blocks. The review informs; it doesn't decide.
- **Two scoreboards, never averaged.** Track A is judged on sell-through and gross margin; Track B on editorial pickup, collaboration interest and brand search lift. Past Shopify listings aren't tagged by track, so the review reports sales by print, category and silhouette and **never assigns past pieces to a track or blends the two into one number**. A silhouette that fails Track A's test can still return as a Track B piece; say so rather than "retire".
- **Prints are allocated, not chosen by sales.** Print allocation is Hessa's at stage 01, from the print workstream. The review shows which print sold on which category as pairing evidence for stage 02; it never recommends dropping or keeping a print.

**Read-only.** It never writes to Shopify, Notion, the ledger or a calendar.

Khaled often reads on his phone. Lead with the answer, keep tables narrow, and put the detail in the file.

## Step 1: Scope

Settle these without asking unless the request is truly unclear:

- **Period.** Default **prior year**: the 12 complete months before the current month (on 6 Oct 2026: `SINCE 2025-10-01 UNTIL 2026-09-30`). Use all history (`SINCE 2023-01-01 UNTIL today`; the store's first sale is June 2025) only if Khaled asks, or to give a launch-and-pace view for pieces that started before the prior year.
- **Focus collection** (optional), e.g. "Wildflower". Look it up in the Game Plan projects tracker if Notion is connected, to see which stage it's at. If it's past buy commitment (stage 11), Part 1 feeds the *next* collection's budget, and Part 2 matters for this one only through pre-sale depth (stage 14), and only if Deepwear's PO adjustment window allows (an open item in §10 of the process doc). Say which applies in the report.

## Step 2: Pull the data (five ShopifyQL queries)

Use the Shopify connector's `run-analytics-query` tool (load it with ToolSearch if it's deferred). Run the queries **one at a time, about 30 seconds apart**. The analytics API rate-limits fast: if a query returns "Rate limited", wait about 75 seconds and retry it once. Don't fire them in parallel; a parallel batch fails together.

Replace `<SINCE>` and `<UNTIL>` with the period from step 1. Save each result **exactly as the tool returned it** (the JSON object with `columns` and `rows`) to a file in a working folder, e.g. `collection-review-data/`. The file names matter: the script looks for them.

| # | File | Query |
|---|---|---|
| 1 | `products.json` | `FROM sales SHOW orders, quantity_ordered, quantity_returned, net_items_sold, gross_sales, discounts, sales_reversals, net_sales GROUP BY product_title, product_type SINCE <SINCE> UNTIL <UNTIL> ORDER BY net_sales DESC LIMIT 1000` |
| 2 | `channels.json` | `FROM sales SHOW net_items_sold, gross_sales, discounts, net_sales GROUP BY product_title, sales_channel SINCE <SINCE> UNTIL <UNTIL> ORDER BY net_sales DESC LIMIT 1000` |
| 3 | `variants.json` | `FROM sales SHOW net_items_sold, net_sales GROUP BY product_title, product_type, product_variant_title SINCE <SINCE> UNTIL <UNTIL> ORDER BY net_items_sold DESC LIMIT 1000` |
| 4 | `monthly.json` | `FROM sales SHOW net_items_sold, gross_sales, discounts GROUP BY product_title TIMESERIES month SINCE <SINCE> UNTIL <UNTIL> LIMIT 1000` |
| 5 | `inventory.json` | `FROM inventory SHOW ending_inventory_units, inventory_units_sold, sell_through_rate GROUP BY product_title SINCE <SINCE> UNTIL <UNTIL> ORDER BY inventory_units_sold DESC LIMIT 1000` |

Query 1 is required. If any other query keeps failing after its retry, carry on without it: the script skips that section and says so, and the report names what's missing.

The tool also renders each result as a chart in the chat. Don't restate those numbers in the reply.

## Step 3: Run the script

```
python3 <this skill's folder>/scripts/collection_review.py collection-review-data --period "Oct 2025 – Sep 2026" --focus "Wildflower" --json collection-review-data/summary.json
```

Leave out `--focus` if no collection was named. The script reads `references/catalogue-map.json` for how titles map to prints, categories and channels, and for every threshold. It prints the report's tables in process order:

- **Part 1 · Stage 00**: 1.1 sell-through by print and category · 1.2 what the year absorbed, by category (the demand baseline) · 1.3 stock still on hand · 1.4 sales not tied to a product
- **Part 2 · Stage 02**: 2.1 silhouettes, with a call each · 2.2 print × category pairing · 2.3 price tier coverage · 2.4 size run, as a ratio out of 10, and abaya colourways
- **Appendix**: where it sells · launch and pace · the focus collection's listings

**If you can't run code** in this session, build the same tables by hand from the five results, following "How titles are read" and step 4. It's slower but the method is the same.

### How titles are read

The script groups listings, not raw titles, so relisted and renamed versions count together:

- **Two naming eras.** Until April 2026 abayas were titled `The <Print> - Reversible Abaya` (or just `The <Print>`). From April 2026 they're `The Reversible Abaya in <Print>` / `The Abaya in <Print>`. Same product, relisted. Merge them by print and silhouette; never report them as two products.
- **Print** = the text after the last ` in `, or before ` - ` in old titles. Aliases in `catalogue-map.json` fold colourway names into their print (`Metamorphosis Lavender` → Metamorphosis).
- **Category** = `product_type` (ABAYA, RTW, Jalabiya, Accessories). Old Butterfly listings have a blank type, so the title decides: anything with "Abaya" is an abaya, anything with `MKWR` is a jalabiya, scrunchies, scarves and twillies are accessories.
- **Silhouette**: abayas are *Reversible Abaya* or *Abaya*; ready-to-wear is the text before ` in ` (Long Skirt, Smocked Top…). These are the shapes Deepwear's blocks will be chosen against at stage 02.
- **New print names need no code change.** `The Reversible Abaya in Burlwood Wildflower` reads as print "Burlwood Wildflower" automatically. Add an alias only when a name should fold into an existing print.

## Step 4: Read the tables

The script's calls for each silhouette (2.1) follow these rules. They're a starting point: overrule any of them with a one-line reason (a block that's new, a silhouette held back by stock, a one-off bulk order).

| Call | Rule |
|---|---|
| **Too new to call** | on sale for fewer than 3 months |
| **Drop from Track A (could return as Track B)** | fewer than 5 units after 3+ months on sale |
| **Carry only if reworked: sold on discount** | discount more than 5 points above its category's average |
| **Carry only if reworked: high returns** | over 25% of units ordered came back: a fit or quality question for Deepwear's block |
| **Carry into Track A** | at or above its fair share of its category's sales (category sales ÷ number of silhouettes) |
| **Watch** | sells, below its share, normal discount and returns |

Thresholds live in `catalogue-map.json` (`min_units_to_call`, `launch_window_months`, `rework_discount_margin`, `rework_returns_rate`, `price_bands_aed`).

Then read across the tables for what rules can't see:

- **Sell-through vs units a month.** The process defines sell-through as units sold ÷ units bought. Shopify only knows stock on hand, so the review uses sold ÷ (sold + still in stock), and only where stock counts are real (ready-to-wear, jalabiyas, accessories). Abaya stock isn't reliable (see "Known data problems"), so abayas show units a month. Say this every time; don't present abaya pace as sell-through.
- **Demand baseline (1.2).** Units a month over the year and over the last 6 months, per category. This is what each stage 00 scenario's unit buy should be checked against. Ready-to-wear launched mid-year, so use its last-6-months rate.
- **Discount is the full-price proxy.** Shopify can't say which units sold at full price, so the discount share stands in for it.
- **No margin.** Shopify holds no product costs (`gross_profit` reads zero), so Track A's margin half comes from the live costing sheet (stage 10), not from this review. Say so.
- **Pairing (2.2) is evidence, not a verdict.** "Butterfly: 49 abayas, 1 ready-to-wear" tells the design seat how the print has carried on each category. It doesn't say to drop it.
- **Size run (2.4) → stage 11.** The ratio out of 10 is the starting size curve for the buy sheet.
- **Channel (Appendix A).** "Staff-entered" (the Shopify app and POS) is in-person and WhatsApp sales and pop-ups; it can't be split further. Useful later for stage 16 routing.

## Step 5: Report

Write the report as a markdown file named `collection-review-<YYYY-MM-DD>.md` and send it with `SendUserFile`. Start from the script's output and add the parts marked ✍️:

```
# PRNTCODE collection review · stage 00 starting point
_Shopify sales <period> · directional only (PC-OPS-CDP-09) · focus: <collection or none>_

## ✍️ The answer
[3–5 bullets for Khaled at the stage 00 gate: what the year absorbed by category,
which prints and categories sold through, stock still carried into next year,
and the one number his budget scenarios should be checked against.]

## Part 1 · Stage 00 inputs            ← script 1.1–1.4

## ✍️ Still needed to sign the stage 00 budget (not in Shopify)
| Input | Where it comes from |
|---|---|
| Current cash position and committed spend | Zoho Books / the living cash model (Finance) |
| Deepwear payment terms, deposit %, MOQs per block | Deepwear (Sophie); MOQs per block are an open item in §10 |
| Prior landed costs and freight | the costing sheet (stage 10) |
| Prior non-product costs: sampling, shoots, freelance seat, gifting, launch marketing, factory visit | Zoho Books |
| Book value of stock on hand | units in 1.3 × landed cost |
| Track A / Track B split | Khaled's proposal; past sales aren't tagged by track |
[Mark any row Khaled has already supplied in the conversation as done.]

## Part 2 · Stage 02 inputs (hand over at stage 02, not before)   ← script 2.1–2.4
[Add one line under 2.1 for every call you overruled, with the reason.]

## ✍️ Focus: <collection>
[Which stage it's at, what that means for how this review is used, and its existing listings.]

## Appendix                              ← script A–B

## ✍️ Data caveats
[Period; sales not tied to a product and how much; placeholder and pre-order stock;
abaya pace is not sell-through; no margin in Shopify; missing queries.]
```

Then reply in chat in **five lines or fewer**: the demand baseline in one line, the strongest and weakest print-category pairings in one line, Track A silhouettes to carry and drop in one line, the stage 00 inputs still missing in one line, and the biggest caveat. Don't paste the tables.

If Khaled asks for the review "for Hessa" or "for the designer", send **Part 2 only**, and only once the collection is at stage 02. Before that, say in one line that the process keeps sales data out of stage 01, and offer it for stage 02.

## Known data problems (as of 6 Oct 2026)

- **Unnamed sales.** About a fifth of net sales are custom line items on draft orders with no product, mostly one 668-item order in December 2025. They can't be split by print, so they're left out and reported in 1.4.
- **Placeholder abaya stock.** The pre-April 2026 abaya listings carry 4,000–5,000 units each; the script lists and skips them. Newer abaya listings carry 90–630 units, which may be made-to-order allowances rather than stock: shown in 1.3 as *unverified* and never used for sell-through.
- **Pre-order listings** (`PRE ORDER - …`, 99 units each) are allowances, not stock, and are left out of 1.3.
- **No costs in Shopify**, so no margin. Margin comes from the costing sheet.
- **No track tags.** Listings carry no Track A / Track B tag. Once a collection is built under the two-track model, tagging each listing (an Operations catalogue-review job) lets the review report each track on its own scoreboard.
- **Returns** show as negative units in a month and as `quantity_returned`. Totals net them off; don't read a negative month as an error.
- **Launch dates** aren't stored in Shopify. The first month with a sale stands in for launch; `≤` marks pieces already selling when the data starts.
- **Data starts June 2025.**

When a new print, colourway name, channel or product type appears, add it to `references/catalogue-map.json` (an alias or a channel group), not to the script. Record the change here if it affects how numbers read.

## Rules

- Read-only: Shopify analytics, and the Game Plan tracker if connected. Never write to Shopify, Notion, the ledger or a calendar.
- Directional only. Never present a table as a decision; the gate owners decide.
- Never feed stage 01, never assign past pieces to a track, never average the tracks, never recommend dropping a print.
- Don't invent numbers. Every figure in the report comes from the script's tables or the five query results.
- Hand-offs: pricing and margin go to Sales' `prntcode-pricing`; catalogue tags (including future track tags) to Operations' `prntcode-catalogue-review`.
