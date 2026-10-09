---
name: monthly-review
description: PRNTCODE Finance monthly review of the previous calendar month. Profit by print, product and channel after materials, labour share, fees, shipping, returns and ads (revenue from Shopify, excluding VAT, net of discounts and refunds); cash tied up in finished stock and fabric per print; what moved against the month before and why; Finance's own track record (predicted vs actual at 30 and 90 days, hit rate, biggest miss); and it ends with three yes/no decisions, each with its AED impact on profit and cash and the report line it comes from. Delivered as a PRNTCODE-branded artifact. Not pushed: from the 1st of each month the CEO opener lists it ("September review · 20 min · 3 decisions") until it's done. Use for "monthly review", "September review", "run the finance review", "how did we do last month?", and the replies "yes 1, no 2, yes 3" after it.
---

# Monthly review (Finance)

You are **Finance** in Khaled's PRNTCODE agent. Once a month, **when he picks it**, you show him where the profit came from, where cash is stuck, how good Finance's own advice has been, and the **three decisions** that would move profit most.

**First, read `../../org/finance/finance-reference.md`.** Its IDs, settings, formatting and hard rules apply.

**Not pushed.** This skill never runs on a schedule. From the 1st, `what-now` lists it among its picks and `refresh` asks planning for time until it's done.

**Read-only** on Shopify, Zoho and the Ops App. Writes: the Monthly reviews row, decision-log rows and their follow-up columns.

## 0. Load tools and pick the month
Shopify analytics, Supabase, Zoho Books, Notion. The month is the **previous calendar month** (Abu Dhabi), unless he names one ("August review"). `M` = that month, `M−1` = the one before.

## 1. Revenue (Shopify)

```
FROM sales SHOW orders, gross_sales, discounts, returns, net_sales, taxes
GROUP BY sales_channel SINCE <M first day> UNTIL <M last day> WITH TOTALS
```
**Revenue = `net_sales`**: excluding VAT, net of discounts and returns/refunds (reference → VAT). It must equal Shopify's net sales for the month to within AED 1; if a later step's per-SKU total doesn't add up to it, show the difference as `unallocated`.

Per SKU and channel:
```
FROM sales SHOW net_sales, net_items_sold, returns
GROUP BY product_variant_sku, sales_channel SINCE <M first day> UNTIL <M last day>
```
**Print** = the Ops App's `products.print_id` for the SKU (`public.print_of_sku(sku)`); if the SKU isn't in the Ops App or has no print, fall back to the product's Shopify tags (the PRNTCODE tag standard's print tag); else `no print`. Channel = Shopify's sales channel.

## 2. Profit by print, product and channel

For each SKU × channel: revenue − pieces × **full cost** − payment fees − courier − returns cost − ads (online only), using `unit-economics` steps 2–4 for the month M (ads and courier from Zoho for M).

Roll up to **print**, **product type** and **channel**. Then:
- **Cost missing:** the share of revenue with no full cost (`cost missing` or `labour missing`) and the top SKUs behind it. Their profit is shown as `—`, never estimated.
- **Fixed costs not in products** (rent, salaries outside the atelier, software): one line from Zoho expenses for M, so the month ends in an operating result. (Not a P&L: Zoho keeps the books.)

## 3. Cash tied up in stock, per print

- **Finished stock:** on-hand units per SKU from `public.stock_by_location_v` (all locations except `shipped`), × extra cost (materials). Roll up per print.
- **Fabric:** `public.material_stock_v` (`stock_qty` × `unit_cost` for `kind = 'fabric'`). Per print where a fabric is used by only that print's BOMs; otherwise `shared fabric`.
- Units with no cost are counted and shown as `value missing`.

## 4. What moved, and why

Compare M with M−1 (same queries): revenue, profit, units and cash in stock, for the total and the top movers by print and channel. Each mover gets a **why** drawn from the data (more orders vs higher price, a pop-up in M, a markdown, ad spend up, a new print launched, a stock-out from `demand_stats_v`/stock), never a guess presented as fact; if the data doesn't show why, say `reason not in the data`.

## 5. Track record (the decision log)

```sql
SELECT url, "userDefined:ID", "Decision", "Type", "date:Date:start", "Recommendation", "Answer",
       "Profit 30d", "Profit 90d", "Cash 30d", "Cash 90d", "Subject",
       "Actual 30d", "Actual 90d", "date:Scored 30d:start", "date:Scored 90d:start"
FROM "collection://414e0fe0-528a-4eec-a175-fbad713b915b"
WHERE "Answer" IN ('yes', 'changed')
```
For each row **30+ days old with no `Scored 30d`** (and **90+ days old with no `Scored 90d`**):
1. Measure the actual over the same window from its `Subject` (`print_id=BTF` → that print's profit and cash since the decision date; `event=…` → the pop-up's result; `cost=…` → the saving in Zoho).
2. Write `Actual 30d` (or `90d`) as `profit AED <x> · cash AED <y>` and set `Scored 30d` (or `90d`) to today.
3. **Hit** = actual profit within ±25% of the prediction, or better than it.

Show: `Track record: 7 of 9 hit (78%) · biggest miss: restock Butterfly, predicted +AED 4,100, actual +AED 1,200 (sold slower)`. With nothing to score yet: `Track record: nothing 30 days old yet`. This is Finance's scorecard for the Observatory.

## 6. Three decisions

Pick the **three** biggest profit or cash levers the report shows (e.g. markdown slow stock with high cash tied up, restock a print selling out at good contribution, reprice a print with thin contribution, drop a cost that buys nothing). Each one:
- is phrased for a **yes or no**,
- gives its AED impact **on profit and on cash** (over 90 days),
- names **the report line it comes from**.

```
1. Mark down Checkered Orchid 30%: frees AED 9,800 of stock, gives up AED 2,100 of margin (from: Cash in stock · Checkered Orchid)
```
(Made-up numbers.) Log each as a decision-log row (`Type` as fits, `Source ref = review:<YYYY-MM>`, `Answer = pending`).

## 7. Deliver: a PRNTCODE-branded artifact

Build it with **`prntcode-brand-formatter`** (Marketing's skill, in this plugin): one HTML artifact titled `PRNTCODE · <Month YYYY> review`, sections in this order: **Headline** (revenue, profit, cash in stock, cost-missing share) · **Profit by print** · **by product type** · **by channel** · **Cash tied up in stock** · **What moved** · **Track record** · **Three decisions**. Tables, no long prose. In claude.ai, make it an artifact and link it; if the runtime can't make artifacts, put the same content on a Notion page under the Finance page and link that.

Then, in chat, **only**:
```
September review: <link>
1. Mark down Checkered Orchid 30%? profit −2,100 · cash +9,800
2. …
3. …
Reply e.g. "yes 1, no 2, yes 3"
```

Write the Monthly reviews row: `Month = YYYY-MM`, `Status = done`, `Artifact` = the link, `Decision 1–3` = the three lines, `Delivered` = today.

## 8. His answers

"yes 1, no 2, yes 3" (or "1 yes", "all yes", "no 3 — we're keeping it"): update each decision-log row's `Answer` (`yes`/`no`/`changed`) and `Answer note` with his words. Reply in one line: `Logged: 1 yes · 2 no · 3 yes.` A "yes" with a spend doesn't create a commitment by itself; for that, run the decision through ask-finance and say "go".

## Due or done? (used by what-now and refresh)

The review for `M` is **due** from the 1st of the following month until a Monthly reviews row with `Month = M` and `Status = done` exists. Opener pick: `<Month> review · 20 min · 3 decisions`.

## Rules
1. Revenue = Shopify `net_sales` for the month (ex-VAT, net of discounts and returns), within AED 1.
2. **Never estimate a missing cost**; show its share of revenue.
3. Not pushed; runs only when he picks it.
4. Read-only on Shopify, Zoho and the Ops App.
5. No real numbers in this repo; examples are made up.
