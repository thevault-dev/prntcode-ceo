---
name: collection-review
description: PRNTCODE Strategy's collection review. From sales data, says what shape a line's next collection needs to feel whole, as how many tops, bottoms and dresses (or abayas, jalabiyas). It names a silhouette only where customers clearly liked it and leaves every other slot open for the designer. It doesn't choose prints or quantities. One line at a time, each on its own calendar (RTW spring/summer, RTW fall/winter, the abaya drops, Ramadan jalabiyas), with how far the history can be trusted and the evidence behind it. Use when Khaled says "collection review", "how many tops / pants / dresses do we need", "what does the collection need to feel whole", "range plan", "shape of the next collection", "plan spring summer", "check Wildflower against past sales". Read-only. Not the catalogue (tag) review, which is Operations' prntcode-catalogue-review.
---

# PRNTCODE collection review (Strategy)

## The end goal

**What shape the next collection needs to feel whole, from data.** Counts per family, named only where customers clearly liked something:

```
# What Wildflower SS27 needs to feel whole
13 styles: 5 tops, 5 bottoms, 3 dresses.

## Tops (5)
- Long Sleeve Top: customers liked it (sold 24 in 3 months, 38% sold through, none returned).
- Smocked Top ×2: customers liked it (19 sold, 54% sold through). Two versions, because it sold through more than half its stock.
- 2 open tops: no clear signal, the designer's call.
  Not named: halter top sold 11 but 4 of 15 came back; short sleeve top sold 2.
…
```

**What it is not:** it doesn't choose prints, quantities to make, or designs. Those are Hessa's and the designer's calls, and the buy is Khaled's. A named silhouette says "customers liked this shape"; an open slot says "the data has nothing to add here".

## How the shape is worked out

1. **How many styles.** As many silhouettes as the line's last collection had (the Jungle Edit RTW SS had 13), unless Khaled sets a number (`--styles`).
2. **The split across families** follows what customers bought: each family's share of pieces sold (ready-to-wear: tops 46%, bottoms 40%, dresses 14%). Each family gets at least 2 styles, so every part of a wardrobe is there.
3. **Inside each family**, a silhouette is **named** only if the data marks it as liked:
   - at or above its fair share of the line's sales,
   - 5 or more sold,
   - discount within 5 points of the line's average,
   - no more than 25% returned.

   A liked silhouette gets **two slots** (a second version) when it sold through more than half its stock, meaning customers wanted more of it. For abayas, where stock isn't tracked, it needs 40% of its family's sales instead.
4. **Every other slot is open.** Each family keeps at least 1 open slot for something new. Shapes that sold but weren't liked (high returns, needed discounts, too few sales) are listed under the family, so the designer sees why they weren't named, without the plan ruling them in or out.

Settings are under `range` in `references/catalogue-map.json` (`styles`, `min_per_family`, `open_slots_per_family`, `second_slot_sell_through`, `second_slot_family_share`, and the silhouette → family map).

## Lines run on their own calendars

**One line per plan, from that line's own sales.** Ready-to-wear, abayas and jalabiyas don't share a season, so they're never blended. The calendar lives under `lines` in the catalogue map (from the Collection Calendar, PC-OPS-CAL-01):

| Line | Families | Launch | Learns from |
|---|---|---|---|
| `rtw-ss` RTW Spring/Summer | tops, bottoms, dresses | April | past RTW collections |
| `rtw-fw` RTW Fall/Winter | tops, bottoms, dresses | October | past RTW collections |
| `abaya-initial` / `abaya-pre-ramadan` / `abaya-summer` | abayas | September / before Ramadan / June | the same months last year |
| `jalabiya` | jalabiyas | before Ramadan | past Ramadan drops |
| `swimwear` | — | May | nothing yet |

"Spring summer" means `rtw-ss`. The Ops App (when connected) says which listings belong to which collection and when each launched; past collections are otherwise listed under `collections` in the catalogue map.

## How much to trust it

Every result states a confidence level, because one short collection can't carry the weight of several seasons:

| Confidence | When |
|---|---|
| **Low** | one past collection with under 6 months on sale (or under 6 months of seasonal history) |
| **Medium** | 6+ months of history |
| **High** | 2+ past collections with 6+ months, or 12+ months of seasonal history |

With low or medium confidence, a shape with fewer than 5 sales is *unproven* (too few to judge), not disliked. Ready-to-wear is low confidence until a second collection has sold for a season: the Jungle Edit RTW SS (launched 1 July 2026) is the only one so far.

## Step 1: Scope

| Setting | Default | Flag |
|---|---|---|
| Line | from the request ("spring summer" → `rtw-ss`) | `--line rtw-ss` (or an alias) |
| Collection name | "the next <line> collection"; use the Game Plan / Ops App name if known | `--collection "Wildflower SS27"` |
| Number of styles | as many silhouettes as the line's last collection | `--styles 12` |
| Sales period | the 12 complete months before this month | in the queries |

## Step 2: Pull the data

**Shopify** (the connector's `run-analytics-query`; one query at a time, about 30 seconds apart; if one returns "Rate limited", wait about 75 seconds and retry once). Replace `<SINCE>`/`<UNTIL>` with the period (on 7 Oct 2026: `2025-10-01` and `2026-09-30`) and save each result **exactly as returned** to a working folder, e.g. `collection-review-data/`:

| # | File | Query | Needed for |
|---|---|---|---|
| 1 | `products.json` | `FROM sales SHOW orders, quantity_ordered, quantity_returned, net_items_sold, gross_sales, discounts, sales_reversals, net_sales GROUP BY product_title, product_type SINCE <SINCE> UNTIL <UNTIL> ORDER BY net_sales DESC LIMIT 1000` | required |
| 4 | `monthly.json` | `FROM sales SHOW net_items_sold, gross_sales, discounts GROUP BY product_title TIMESERIES month SINCE <SINCE> UNTIL <UNTIL> LIMIT 1000` | required |
| 5 | `inventory.json` | `FROM inventory SHOW ending_inventory_units, inventory_units_sold, sell_through_rate GROUP BY product_title SINCE <SINCE> UNTIL <UNTIL> ORDER BY inventory_units_sold DESC LIMIT 1000` | sell-through (for second versions) |
| 2 | `channels.json` | `FROM sales SHOW net_items_sold, gross_sales, discounts, net_sales GROUP BY product_title, sales_channel SINCE <SINCE> UNTIL <UNTIL> ORDER BY net_sales DESC LIMIT 1000` | evidence only |
| 3 | `variants.json` | `FROM sales SHOW net_items_sold, net_sales GROUP BY product_title, product_type, product_variant_title SINCE <SINCE> UNTIL <UNTIL> ORDER BY net_items_sold DESC LIMIT 1000` | evidence only |

**The Ops App** (optional, read-only): the Supabase project **PRNTCODE-ops** (`nhimagmpcwlkbfygiowq`). Run this with `execute_sql` and save the `ops` object as `ops.json`:

```sql
select json_build_object(
 'collections', (select json_agg(c) from (select collection_id, name, launch_date, sunset_date, status from public.collections where active order by launch_date) c),
 'products', (select json_agg(p) from (select distinct product_title, product_type, collection_id, print_id, made_to_order from public.products where active order by 1) p)
) ops;
```

Without it, the catalogue map's `collections` list is used. **Never write to the Ops App.**

## Step 3: Run

```
python3 <skill>/scripts/range_plan.py collection-review-data --line rtw-ss --collection "Wildflower SS27"
python3 <skill>/scripts/collection_review.py collection-review-data --line rtw-ss --period "Oct 2025 – Sep 2026"
```

- **`range_plan.py`** writes the end goal: styles per family, named and open slots, and why.
- **`collection_review.py --line`** writes the evidence for that line: sales and sell-through by print and silhouette, returns, price tiers, size run, channels, launch and pace. It's background, for anyone who asks "why"; it doesn't change the shape.
- **`lines.py`** holds the calendars, the Ops App reader and the confidence rules.

**If you can't run code**, work out the same thing by hand from the results, following "How the shape is worked out".

## Step 4: Report

Reply in chat with the `range_plan.py` output as it stands. It's short enough to read on a phone. Add one line only if something needs Khaled's judgement (a family with no liked silhouette at all, or a shape that just missed being named).

If Khaled asks for the evidence, send the `collection_review.py --line` output as a markdown file with `SendUserFile`.

## How titles are read

- **Two naming eras.** Until April 2026 abayas were `The <Print> - Reversible Abaya` (or `The <Print>`); since then `The Reversible Abaya in <Print>` / `The Abaya in <Print>`. Merged.
- **Category** = `product_type`; a blank type falls back to the title. Category decides the line.
- **Silhouette** = ready-to-wear: the text before ` in `; abayas: *Reversible Abaya* or *Abaya*. A new silhouette needs a family under `range.families`, or it's listed as not counted.

## Known data problems (as of 7 Oct 2026)

- **One RTW collection so far**, so ready-to-wear is low confidence.
- **Abayas are made to order** (Ops App), so their Shopify stock figures are allowances: no sell-through for abayas.
- **Unnamed sales** (custom line items, mostly one bulk order in December 2025) can't be assigned to a silhouette and are left out.
- **Ops App catalogue slips:** *The Twilly in Flutter Dot* carries print code CHKOR; *The Smocked Top in Bloomingfield* has no print.

## Rules

- Read-only: Shopify analytics and the Ops App (one SELECT).
- One line per plan, from that line's sales only.
- Counts of styles by family. **No prints, no quantities, no designs.**
- Name a silhouette only where the data says customers liked it; everything else stays open.
- State the confidence. Don't invent numbers.
