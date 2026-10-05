---
name: collection-review
description: PRNTCODE Strategy's collection review. Reads Shopify sales and works out what sold in past collections, by print, silhouette, size, colourway and channel, how fast and at what discount, then turns it into what the next collection should repeat, rework or retire, ready for the brief to Hessa and the collection designer. Use when Khaled says "collection review", "run the collection review", "what sold in past collections", "which prints sell", "what silhouettes work", "what should the next collection repeat", "check Wildflower against past sales", "what should we keep for the next drop", or asks for the sales input to a collection brief. Read-only. Not the catalogue (tag) review, which is Operations' prntcode-catalogue-review.
---

# PRNTCODE collection review (Strategy)

## What this is for

Before a collection's line is locked, look back at what customers actually bought. PRNTCODE sells a small set of house prints across abayas, ready-to-wear, MKWR jalabiyas and accessories, so the useful questions are always the same:

- Which **prints** sell, and do they sell at full price or only with a discount?
- Which **silhouettes** sell, in each category?
- Does a print that works as an abaya also work as ready-to-wear? (Often not.)
- What **size curve** and **colourways** to cut.
- **Where** it sells: in person and on WhatsApp, or online.
- How fast new pieces sold after launch.

The answer ends in three lists the designer can act on: **repeat, rework, retire**. The review is most useful while a collection's line can still change, so run it before samples are signed off.

**Read-only.** It never writes to Shopify, Notion, the ledger or a calendar.

Khaled often reads on his phone. Lead with the answer, keep tables narrow, and put the detail in the file.

## Step 1: Scope

From the request, settle two things without asking unless the request is truly unclear:

- **Focus collection** (optional): the collection being designed, e.g. "Wildflower". If named, the report checks whether it already has listings and ends with calls aimed at it.
- **Period**: all history by default (`SINCE 2023-01-01`; the store's first sale is June 2025). If Khaled names a period or a collection to look back at, narrow `SINCE`/`UNTIL` to it.

## Step 2: Pull the data (five ShopifyQL queries)

Use the Shopify connector's `run-analytics-query` tool (load it with ToolSearch if it's deferred). Run the queries **one at a time, about 30 seconds apart**. The analytics API rate-limits fast: if a query returns "Rate limited", wait about 75 seconds and retry it once. Don't fire them in parallel; a parallel batch fails together.

Save each result **exactly as the tool returned it** (the JSON object with `columns` and `rows`) to a file in a working folder, e.g. `collection-review-data/`. The file names matter: the script looks for them.

| # | File | Query |
|---|---|---|
| 1 | `products.json` | `FROM sales SHOW orders, net_items_sold, gross_sales, discounts, net_sales GROUP BY product_title, product_type SINCE 2023-01-01 UNTIL today ORDER BY net_sales DESC LIMIT 1000` |
| 2 | `channels.json` | `FROM sales SHOW net_items_sold, gross_sales, discounts, net_sales GROUP BY product_title, sales_channel SINCE 2023-01-01 UNTIL today ORDER BY net_sales DESC LIMIT 1000` |
| 3 | `variants.json` | `FROM sales SHOW net_items_sold, net_sales GROUP BY product_title, product_type, product_variant_title SINCE 2023-01-01 UNTIL today ORDER BY net_items_sold DESC LIMIT 1000` |
| 4 | `monthly.json` | `FROM sales SHOW net_items_sold, gross_sales, discounts GROUP BY product_title TIMESERIES month SINCE 2023-01-01 UNTIL today LIMIT 1000` |
| 5 | `inventory.json` | `FROM inventory SHOW ending_inventory_units, inventory_units_sold, sell_through_rate GROUP BY product_title SINCE 2023-01-01 UNTIL today ORDER BY inventory_units_sold DESC LIMIT 1000` |

Query 1 is required. If any other query keeps failing after its retry, carry on without it: the script skips that section and says so, and the report names what's missing.

The tool also renders each result as a chart in the chat. Don't restate those numbers in the reply.

## Step 3: Run the script

```
python3 <this skill's folder>/scripts/collection_review.py collection-review-data --focus "Wildflower" --json collection-review-data/summary.json
```

Leave out `--focus` if no collection was named. The script reads `references/catalogue-map.json` for how titles map to prints, categories and channels, and prints markdown tables:

- headline and the sales it can't tie to a product,
- by category, by print, print × category, silhouettes per category,
- size curve, abaya colourways,
- where each category and each abaya print sells,
- launch and pace per print and silhouette,
- stock: real sell-through, placeholder stock, listings with no sales yet,
- suggested calls by silhouette and by print,
- the focus collection's listings.

**If you can't run code** in this session, build the same tables by hand from the five results, following the rules in "How titles are read" and step 4. It's slower but the method is the same.

### How titles are read

The script groups listings, not raw titles, so relisted and renamed versions count together:

- **Two naming eras.** Until April 2026 abayas were titled `The <Print> - Reversible Abaya` (or just `The <Print>`). From April 2026 they're `The Reversible Abaya in <Print>` / `The Abaya in <Print>`. Same product, relisted. Merge them by print and silhouette; never report them as two products.
- **Print** = the text after the last ` in `, or before ` - ` in old titles. Aliases in `catalogue-map.json` fold colourway names into their print (`Metamorphosis Lavender` → Metamorphosis).
- **Category** = `product_type` (ABAYA, RTW, Jalabiya, Accessories). Old Butterfly listings have a blank type, so the title decides: anything with "Abaya" is an abaya, anything with `MKWR` is a jalabiya, scrunchies, scarves and twillies are accessories.
- **Silhouette**: abayas are *Reversible Abaya* or *Abaya*; ready-to-wear is the text before ` in ` (Long Skirt, Smocked Top…).
- **New print names need no code change.** `The Reversible Abaya in Burlwood Wildflower` reads as print "Burlwood Wildflower" automatically. Add an alias only when a name should fold into an existing print.

## Step 4: Make the calls

The script's suggested calls follow these rules. Use them as the starting point, then overrule any of them with a stated reason (a print that's new, a silhouette held back by stock, a one-off bulk order).

| Call | Rule |
|---|---|
| **Too new to call** | on sale for fewer than 3 months |
| **Retire candidate** | fewer than 5 units after 3+ months on sale |
| **Rework** | sold, but its discount is more than 5 points above its category's average: customers wanted it cheaper |
| **Repeat** | at or above its fair share of its category's sales (category sales ÷ number of groups) without heavy discounting |
| **Hold** | sells, below its share, normal discount: keep only if it earns a place |

Thresholds live in `catalogue-map.json` (`min_units_to_call`, `launch_window_months`, `rework_discount_margin`).

Then read across the tables for the things rules can't see:

- **Print translation.** Compare a print's abaya and ready-to-wear units. A print that sells as an abaya but not as ready-to-wear (Butterfly so far) shouldn't carry the ready-to-wear line, and the reverse.
- **Discount is the full-price proxy.** Shopify can't say which units sold at full price, so the discount share stands in for it. Low discount = sold at full price.
- **Pace.** Units per month since launch, and units in the first 3 months, compare pieces fairly when they launched at different times. A launch marked `≤` was already selling when the data starts, so its first-3-month number isn't a real launch.
- **Size curve → cut ratio.** Turn the shares into a suggested ratio per category (e.g. 5:3:2 S:M:L).
- **Colourways.** Only older abaya listings carry colour in the variant name; newer ones keep it in the SKU. Say so, and treat colour shares as indicative.
- **Channel.** "Staff-entered" (the Shopify app and POS) is in-person and WhatsApp sales and pop-ups; it can't be split further from Shopify. A print that sells mostly in person needs to be seen; that matters for how Wildflower is launched.
- **Focus collection.** If listings already exist (e.g. `The Reversible Abaya in Burlwood Wildflower`, 90 in stock, no sales on 5 Oct 2026), say so: stock is already committed to that piece.

## Step 5: Report

Write the report as a markdown file named `collection-review-<YYYY-MM-DD>.md` and send it with `SendUserFile`. Structure:

```
# PRNTCODE collection review: <date>
_Shopify sales <period> · focus: <collection or none>_

## The answer
[3–5 bullets: what sells, what doesn't, the one thing the next line must get right.]

## Brief for <focus collection | the next collection>
**Repeat:** [prints, silhouettes, colourways, each with the number that earns it]
**Rework:** [what, and what to change]
**Retire:** [what, and why]
**Cut:** [size ratio per category]
**Launch:** [where it will sell: in person, online, pop-ups]

## What sold
[Category, print, print × category tables, trimmed to what matters.]

## Silhouettes
## Size and colour
## Where it sells
## Launch and pace
## Stock

## Data caveats
[Unnamed sales left out and how much; placeholder stock; missing queries;
the period covered; anything overruled in step 4 and why.]
```

Then reply in chat in **five lines or fewer**: the headline, the repeat / rework / retire in one line each, and one line naming the biggest caveat. Don't paste the tables.

## Known data problems (as of 5 Oct 2026)

- **Unnamed sales.** About a fifth of net sales are custom line items on draft orders with no product, mostly one 668-item order in December 2025. They can't be split by print, so they're left out and reported as a caveat.
- **Placeholder abaya stock.** The pre-April 2026 abaya listings carry 4,000–5,000 units each. Sell-through is meaningless there; the script lists them and skips them. Newer abaya listings carry a few hundred units, which look like made-to-order allowances, so abaya sell-through isn't reported at all; only ready-to-wear, jalabiyas and accessories get it.
- **Returns** show as negative units in a month. Totals net them off; don't read a negative month as an error.
- **Launch dates** aren't stored in Shopify. The first month with a sale stands in for launch.
- **Data starts June 2025**, so anything launched before then has no true launch window.

When a new print, colourway name, channel or product type appears, add it to `references/catalogue-map.json` (an alias or a channel group), not to the script. Record the change in "Known data problems" if it affects how numbers read.

## Rules

- Read-only: Shopify analytics only. Never write to Shopify, Notion, the ledger or a calendar.
- Don't invent numbers. Every figure in the report comes from the script's tables or the five query results.
- A call the report makes against the script's rule says why, in one line.
- Hand-offs: pricing questions go to Sales' `prntcode-pricing`; catalogue tags and badges to Operations' `prntcode-catalogue-review`.
