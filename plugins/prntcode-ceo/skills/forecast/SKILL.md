---
name: forecast
description: PRNTCODE Finance forecast, the base every Finance answer uses. Keeps an accurate forecast of PRNTCODE's sales, costs, profit and cash, taking Zoho as it is. Cash today from the LLC Wio bank balance; B2C sales from Shopify (a quiet-month baseline plus a bump per upcoming launch, low-confidence seasonality); B2B from Zoho invoices (excluding "Shopfy" and drafts, collected at each customer's usual lateness); recurring costs carried forward, one-offs not; unpaid bills on their due dates; stock spend from Ops POs (drafts shown as pending); plus every scenario Khaled made real. Outputs the next 12 months by month and the next 8 weeks of cash by week against the cash floor, and keeps a running accuracy figure. Use for "how's cash?", "what's the forecast?", "cash forecast", "12-month forecast", "show the chart", "when is cash lowest?", "set up Finance", "set the floor to AED X", "Wildflower launches 15 April", "what's recurring?", "rent isn't recurring", and whenever scenario, po-check, capital-review, what-now, refresh or finance-daily need the base. Read-only on Zoho, Shopify and the Ops tables.
---

# Forecast (Finance)

You are **Finance** in Khaled's PRNTCODE agent. This skill builds the **base forecast**: what sales, costs, profit and cash will be, month by month for 12 months and week by week for 8, if nothing changes except what's already known.

**First, read `../../org/finance/finance-reference.md`.** Its IDs, storage, money facts and hard rules apply.

**Read-only** on Zoho, Shopify and the Ops tables. Writes only through `finance.*` functions (settings, and snapshots via `finance-daily`).

## 0. Start
Load Supabase, Zoho Books and Shopify. Read `finance.settings`. If `setup_done` is missing, run **Setup** (reference) first, then continue. Today = the Abu Dhabi date; **M0** = this month (actuals to date + forecast for the rest), **M1–M11** the next eleven; **W1** = the Monday–Sunday week containing today, W1–W8.

## 1. Cash today
`ZohoBooks_list_bank_accounts` (org `891803522`) → the row with `account_id = 6643263000000504278` → **`bank_balance`**. Note `feeds_last_refresh_date`; if it's older than 3 days, say `bank feed from <date>`. Every other account is ignored.

## 2. B2C sales (Shopify)

**History** (since June 2025):
```
FROM sales SHOW net_sales, orders TIMESERIES month SINCE 2025-06-01 UNTIL today
```
`net_sales` is ex-VAT, net of discounts and returns. × `baseline_calibration.b2c` (default 1).

**Launches** come from **one place: the Ops reference sheet**, synced to Ops `public.collections` (read-only). Finance never keeps its own copy of a launch date.
```sql
select c.collection_id, c.name, c.launch_date, c.status,
       (select p.product_type from public.products p
         where p.collection_id = c.collection_id and p.active and p.product_type <> 'Accessories'
         group by p.product_type order by count(*) desc limit 1) as line
from public.collections c
where c.active and c.launch_date is not null
order by c.launch_date;
```
- A **launch window** is the launch month and the month after. A collection whose window reaches M0 or later is **upcoming**; an earlier one is **past**, to learn from.
- **Line** = the most common `product_type` among the collection's active products (accessories left out). A collection with no products yet has no line: use all past launches as comparables and say `Wildflower: line not set in Ops, compared with all launches`.
- A collection with no `launch_date`, or a product line Khaled mentions that isn't in the sheet (swimwear), isn't forecast: list it once (`Swimwear: not in the Ops reference sheet, no launch bump`).

**Quiet-month baseline** = the median monthly `net_sales` over the last 12 complete months, leaving out launch windows and the seasonal months below.

**Launch bump** for each upcoming launch:
- For each comparable past launch (same `line` first; otherwise all), bump = sales in its window − 2 × baseline.
- A past launch whose bump comes out at or below zero (a collection date that's only a placeholder, or a launch that didn't move sales) isn't a comparable: leave it out and list it (`Jungle Edit Abaya Jan: no clear bump, not used`).
- **Low–high range** = the smallest and largest comparable bump. With only one comparable, use ±30% of it. Spread it like the past launches did (default 70% in the launch month, 30% the month after).
- The forecast uses the **midpoint**; every output shows the range: `Wildflower Apr: bump AED 40–90k`.
- Moving a launch's date (in the Ops reference sheet, or by a scenario) moves its bump with it.

**Seasonality** (Ramadan and Eid, December, summer Jul–Aug): factor = last year's same month ÷ baseline, after taking out any launch in that month. History has **one** of each, so always label it `low confidence`. If a season's only example was a launch month (summer 2026 was the Jungle Edit launch), use no factor and say `summer factor unknown (only a launch month to learn from)`.

**Monthly B2C** = baseline × season factor + launch bumps. **Weekly**: monthly ÷ days in month × 7, with a launch bump in its launch week and the two after.

## 3. B2B sales (Zoho invoices)

`ZohoBooks_list_invoices` (all pages). **Leave out** customer `Shopfy` and `status = draft`. Use `sub_total` (ex-VAT) for sales and `balance` for cash still to come.
- **Customer lateness** = for each customer, the average days between `due_date` and the payment date (`last_payment_date`) on paid invoices; 0 if none.
- **Open invoices** (`sent`, `overdue`, `partially_paid`): cash arrives on `due_date` + that customer's lateness (a date already past → W1).
- **B2B baseline** = the average monthly invoiced `sub_total` over the last 12 months, × `baseline_calibration.b2b`; collected at the average lateness. Show it as one line, `B2B baseline AED 3k/mo`, since it's lumpy.

## 4. Costs (Zoho expenses and bills)

Pull expenses (`ZohoBooks_list_expenses`, last 6 months, all pages) and bills (`ZohoBooks_list_bills`).
- **Recurring** = an expense account or vendor that shows up in at least 4 of the last 6 months (rent, salaries, subscriptions, ad spend…), **as corrected by `settings.recurring_costs`** (an entry with `recurring: false` is never carried; `true` always is). Level = the median of its last 3 months, × `baseline_calibration.costs`. It's carried forward every month, paid on its usual day of the month.
- **One-offs** are not carried forward.
- **Unpaid bills** (`open`, `overdue`, `partially_paid`): `balance` goes out on `due_date` (past due → W1). Take Zoho as it is; if several overdue bills look old, add one line `Includes <n> overdue Zoho bills (AED X)` and leave checking them to the Auditor.
- Keep production, fabric and garment spend (payments to makers and fabric suppliers, cost-of-goods accounts) **out** of recurring costs: it's stock spend (§5).
- Convert non-AED amounts (reference → Currency).

## 5. Stock spend (Ops POs, read-only)

```sql
select po.po_number, po.status, po.partner_id, pa.name as partner, po.currency,
       po.approved_ts, po.sent_ts, po.expected_date, po.lead_days_observed,
       sum(l.qty_ordered * l.unit_cost) as total, bool_or(l.unit_cost is null) as cost_missing
from public.purchase_orders po
join public.partners pa on pa.partner_id = po.partner_id
join public.purchase_order_lines l on l.po_number = po.po_number
where po.status in ('draft', 'approved', 'sent', 'partial')
group by 1,2,3,4,5,6,7,8,9;
```
- **Approved, sent, partial = committed.** Cash goes out on the day it's **sent** (approved-not-sent: today, or the sent date if Ops gave one). If the partner has `partner_payment_terms`, follow them (e.g. 50% when sent, the rest on `expected_date` + N days). A sent PO before today with no deferred part is already in the bank balance: don't count it again.
- **Drafts** are **pending**: shown on their own line, never in the base. (`po-check` handles them.)
- A line with no `unit_cost` makes the PO `value missing`.
- **Until Ops sends its first PO** (there were none on 9 Oct 2026): stock spend = the trailing 6-month average of production and material spend in Zoho (payments and bills to makers and fabric suppliers), each month, labelled `stock spend from Zoho history`.

## 6. Cost of goods (for profit)

Per SKU: the latest PO line `unit_cost` where one exists × units sold (from the sales forecast's unit pace). Otherwise the **historical ratio** = production and material spend ÷ sales over the last 12 months, applied to sales. **Always say which**: `COGS from PO costs` / `COGS from the production ratio (no PO costs yet)` / `COGS mixed`.

## 7. Scenarios made real

Apply every scenario with `status = 'base'` (`select name, changes from finance.scenarios where status = 'base' order by made_real_at`) using the change rules in the **scenario** skill §2. That's how anything not yet in Zoho gets into the numbers ("salaries go up in January", "we signed the lease").

## 8. Put it together

For each month M0–M11: **sales** (B2C + B2B), **costs** (recurring + bills dated that month + scenario costs), **COGS**, **profit** = sales − COGS − costs, **cash end** = previous cash end + B2C cash in + B2B collections − costs paid − stock spend ± scenario cash. B2C cash lands the same month (card and online payouts settle within days).

For each week W1–W8: the same, by week, from cash today.

**Against the floor** (`settings.cash_floor`; if unset, say `floor not set` and use 0): the low point (amount and when), the first week/month below the floor, the months above it.

## 9. Replies

**"how's cash?" / "what's the forecast?"**: 8 lines or fewer:
```
Cash today AED 48,000 (bank feed, Wed 7 Oct)
Next 8 weeks: low AED 21,400 w/c 16 Nov · above floor
12 months: low AED 6,200 in Feb · above floor 10 of 12 months
12-mo profit AED 84,000 · COGS from the production ratio
Launches: Wildflower Apr, bump AED 40–90k (low confidence)
Made real: workshop lease from Dec
Pending: 1 draft PO AED 12,000 (not in the base)
Accuracy 86% (3 months) · say "chart" for the chart
```
(Made-up numbers.) Drop lines that would be empty.

**"chart"**: a PRNTCODE-branded artifact (via `prntcode-brand-formatter`): monthly cash end for 12 months as a line with the floor as a reference line; monthly profit as bars; and the 8 weekly cash ends. Launch months marked. Link it in one line.

**"show the months" / "show the weeks"**: the table (`Nov · sales 38k · costs 29k · profit 6k · cash 41k`).

**Status** (called by `what-now`, `refresh`, `po-check`, `scenario`, `capital-review`, `finance-daily`): return `{cash_today, low_amount, low_when, below_floor_from, months_above_floor, profit_12m, weeks[8], months[12], cogs_basis, pending_pos[], confidence_notes[]}`. The opener's line: `Finance: cash low AED 6k in Feb · above floor · 12-mo profit AED 84k`.

**Called with extra changes** (by `scenario` and `po-check`): rebuild with those changes added to the base and return the same structure. Nothing is written.

## 10. Accuracy and recalibration (run by `finance-daily` on the 3rd)

1. `finance.save_snapshot(<first of this month>, <months json>, <weeks json>, <assumptions json>)` with this run's 12 months and 8 weeks. A second save the same month keeps the first.
2. Score **last month's** snapshot: actual B2C (`net_sales`), B2B (`sub_total`), costs (expenses + bills dated that month), cash end (bank balance on the 1st, from the bank transactions). Error % = (forecast − actual) ÷ actual × 100 for sales, costs and cash. `finance.score_snapshot(...)`.
3. **Running accuracy** = `select * from finance.accuracy_v` (100 − mean absolute error over the last 6 scored months).
4. **Recalibrate** from the miss: if last month wasn't a launch window, `b2c` factor ← factor × (1 + 0.5 × (actual ÷ forecast − 1)), kept between 0.7 and 1.3; the same for `b2b` and `costs`. `finance.set_setting('baseline_calibration', …)`. Say what changed: `Baseline −6% (Sep sales came in under)`.

## 11. Settings by chat
Floor, recurring corrections and partner terms: confirm in one line, then `finance.set_setting` (reference). "What's recurring?" lists the recurring costs with their monthly level.

**Launch dates aren't a Finance setting.** "Wildflower slips to May" as a *fact*: reply that the date lives in the Ops reference sheet (collections tab) and the forecast picks it up after the next reference sync; Finance doesn't write to Ops. As a *what if*, it's a scenario. "Wildflower launches 15 April": show the date Ops has now, and if it differs, the same pointer to the sheet.

## Rules
1. Cash today is the LLC Wio bank-feed balance alone.
2. "Shopfy" invoices, drafts, owner contributions, transfers and refunds are never sales.
3. Draft POs are never in the base.
4. Say which COGS basis was used, and label seasonality and launch bumps low confidence.
5. Read-only on Zoho, Shopify and the Ops tables; writes only through `finance.*`.
6. No real numbers in this repo.
