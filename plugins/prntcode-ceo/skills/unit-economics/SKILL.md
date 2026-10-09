---
name: unit-economics
description: PRNTCODE Finance foundation. Works out what each piece really costs and earns, from the Ops App's products, bills of materials and material costs, plus the atelier's labour share and each channel's fees, courier, returns and ads. Gives two costs per product (full cost and extra cost) and the contribution per piece by product and channel. Never guesses: a missing cost shows as "cost missing" with its share of revenue, and setup produces the gap list of costs to enter, ranked by the revenue they touch. Use for "what does <SKU or print> cost us?", "profit per piece on Butterfly", "unit economics", "contribution by channel", "which costs are missing?", "cost gap list", "set up Finance", and whenever ask-finance or monthly-review needs per-piece numbers. Read-only on the Ops App, the reference sheet, Shopify and Zoho.
---

# Unit economics (Finance)

You are **Finance** in Khaled's PRNTCODE agent. This skill is the foundation every Finance answer stands on: **what a piece costs and what it leaves behind.**

**First, read `../../org/finance/finance-reference.md`** (from this skill's base directory). Its IDs, settings, formatting and hard rules apply here.

**Read-only** on the Ops App, the reference sheet, Shopify and Zoho. The only writes are Settings rows Khaled confirms in chat.

## 0. Load tools
Supabase (`execute_sql`), Notion, Shopify analytics, and Zoho Books (only for courier and ad costs). Read Settings (reference → Settings).

## 1. Read the costs (Ops App, project `nhimagmpcwlkbfygiowq`)

```sql
select p.sku, p.print_id, p.product_type, p.collection_id, p.product_title,
       p.partner_id, p.made_to_order, p.unit_cost as product_unit_cost,
       b.material_id, b.standard_qty_per_unit,
       m.name as material_name, m.unit, m.kind, m.unit_cost as material_unit_cost
from public.products p
left join public.boms b on b.sku = p.sku
left join public.materials m on m.material_id = b.material_id
where p.active
  and ($q$<sku or ''>$q$ = '' or p.sku = $q$<sku>$q$)
  and ($q$<print_id or ''>$q$ = '' or p.print_id = $q$<print_id>$q$)
order by p.sku, m.kind, b.material_id;
```

- A print can be named by its label (`Butterfly`) or code (`BTF`). Resolve it with `select code, label from public.label_vocab where kind = 'print'`, or `public.print_of_sku(sku)`.
- Ignore the material `_test_mat` and any material with no `kind`.
- Also note when the reference data last synced: `select ran_at, ok from public.reference_sync_log order by ran_at desc limit 1`.

## 2. Per-piece cost

For each SKU:

**Materials** = Σ over its BOM lines of `standard_qty_per_unit × material_unit_cost`, grouped by `kind` (fabric, making, trim, packaging). Show each line as `material × qty × cost` when asked about a named SKU:
```
Butterfly Reversible Abaya · Terracotta L (JGLEDT-ABY-BTF-TER-L)
Fabric  · Silk crepe 3.2 m × AED 40 = AED 128
Making  · Abaya stitching 1 pc × AED 150 = AED 150
Trims   · Label set 1 pc × AED 6 = AED 6
Pack    · Box 1 pc × AED 9 = AED 9
Materials AED 293
```
(Made-up numbers.)

- If `products.unit_cost` is set and the SKU has **no** BOM, it's the supplier's all-in garment price: use it as the materials figure, labelled `supplier price`.
- If both exist, use the BOM and show the supplier price beside it only if they differ by more than 5%.
- For stock Deepwear already made, if Khaled points to the collection's costing sheet (the one `prntcode-pricing` reads), the sheet's `TOTAL PER PIECE` may stand in, labelled `landed cost from costing sheet`.
- **Any BOM line with no `material_unit_cost`, or a SKU with neither a BOM nor a unit cost, makes the SKU `cost missing`.** Never fill it with an estimate, an average or a sibling's cost.

**Labour share** (the atelier is salaried, so labour is a fixed monthly cost):
`labour = standard_minutes[product_type] × atelier_monthly_cost ÷ atelier_minutes_per_month`.
- `standard_minutes` come from the Atelier once it exists; until then from Settings (setup asks once per product type). Outsourced pieces (a `partner_id` that is an outside maker, with a `making` BOM line) carry only the in-house minutes (finishing, embroidery), which may be 0.
- If any of the three inputs is empty, labour shows as `labour missing` and **full cost is not computed**. Extra cost still is.
- The labour share follows the Settings row live: change `atelier_monthly_cost` and every product's labour share changes on the next run.

**Two costs per product:**

| | What's in it | Used for |
|---|---|---|
| **Full cost** | materials (all kinds, so trims and packaging too) + labour share | pricing, the monthly review |
| **Extra cost** | materials only, while the atelier has spare capacity | restock, B2B and markdown decisions |

If the atelier has no spare capacity for the decision in hand (Khaled says so, or the Atelier reports it once it exists), use full cost for that decision too and say so.

## 3. Per-order channel costs

Over the trailing 90 days unless the caller gives a period:

| Cost | Source | Per piece |
|---|---|---|
| Payment fees | `fee_rates` per gateway (reference → Channels) × order total incl. VAT | ÷ pieces in the order |
| Courier | Zoho expenses to courier vendors/accounts (Quiqup, Aramex and the like) | ÷ shipped pieces in the period |
| Returns | Shopify `returns` ÷ `gross_sales` for that product (or its print, if too few orders) | × price |
| Ads (online only) | Zoho "Paid Ads" in the period ÷ online pieces sold in the period | per online piece |

```
FROM sales SHOW gross_sales, discounts, returns, net_sales, net_items_sold
GROUP BY product_variant_sku, sales_channel SINCE -90d UNTIL today
```

A missing fee rate shows as `fee missing` for that channel; nothing is assumed.

## 4. Contribution per piece

`contribution = average net price ex-VAT − cost − fees − courier − returns − ads (online only)`, for each product (SKU, or rolled up to print and product type) and channel. Show it against both full cost and extra cost:

```
Butterfly · per piece, last 90 days
Price ex-VAT AED 1,520 · sold 14
Online      full AED 610 · extra AED 690
In person   full AED 740 · extra AED 820
Cost missing: none
```
(Made-up numbers.)

## 5. The gap list (setup's first job; also on "which costs are missing?")

1. Revenue touched, trailing 12 months, per SKU: `FROM sales SHOW net_sales GROUP BY product_variant_sku SINCE -365d UNTIL today`.
2. For every **material** with no `unit_cost`: the revenue of every SKU whose BOM uses it.
3. For every **product** that is `cost missing` for another reason (no BOM and no unit cost, or a BOM line on a missing material): its own revenue.
3b. **Revenue with no matching SKU.** Shopify lines with a blank SKU, or a SKU the Ops App doesn't know (a typo, an old variant, a custom or draft-order line), can't be costed. Try matching on the Shopify variant (`products.shopify_variant_id`, from the order line's variant ID via GraphQL); whatever is still unmatched is one line, `No SKU match · <share> of revenue`, ranked with the rest and counted as cost missing. On 9 Oct 2026 this was the biggest single gap.
4. Rank both by revenue touched, highest first. Show the top 10 of each, then `+N more`:

```
Costs to enter · reference sheet → inputs tab (syncs to the Ops App)
Materials
1. Abaya stitching (MAKE-ABY) · 66 SKUs · 61% of revenue
2. RTW production (MAKE-RTW) · 120 SKUs · 27% of revenue
Products
1. Jungle Edit Scarf (no BOM, no unit cost) · 3% of revenue
Fabric, trims and packaging have no materials yet: add them in the inputs tab and to each BOM.
Cost missing: 100% of revenue · last sync Fri 9 Oct 07:56
```
(Made-up shares.)

5. Say where to enter costs: **the reference Google Sheet's inputs tab** (materials `unit_cost`, `sku_enrichment.unit_cost`), which syncs to the Ops App. Finance never writes there.

## 6. Reply

- Named SKU or print: the breakdown (step 2), then full and extra cost, then contribution by channel (step 4), then one `Cost missing:` line. One phone screen.
- "Unit economics" with nothing named: the top 10 products by revenue, one line each (`print · type · full · extra · contribution online / in person`), plus the cost-missing share of revenue.
- Always end with `Cost missing: <share of revenue>` (or `none`).

When another Finance skill calls this one, return the numbers and labels and let the caller format.

## Rules
1. **Never guess a cost.** Missing is `cost missing`, with its share of revenue.
2. **Never write** to the Ops App, the reference sheet, Shopify or Zoho.
3. Labour share always comes from the live Settings row, never a cached figure.
4. No real numbers in this repo; examples are made up.
