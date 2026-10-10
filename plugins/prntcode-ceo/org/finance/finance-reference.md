# Finance reference (read by every Finance skill)

Shared facts, IDs, storage and rules for `forecast`, `scenario`, `capital-review`, `po-check` and `finance-daily`. Each of those skills reads this file first (from its own base directory: `../../org/finance/finance-reference.md`).

> **This repo is public.** No real amount, balance, floor, salary or account number goes in any committed file, including docs and tests. Real numbers live only in the `finance` schema. Examples here use made-up numbers.

## What Finance is for

1. Keep an accurate **forecast** of PRNTCODE's sales, costs, profit and cash.
2. Let Khaled **simulate scenarios** and see their financial impact before he decides.
3. **Review how money is used** and suggest ways to be more capital-efficient.

It takes Zoho **as it is**. Keeping Zoho correct is the Auditor's job. Out of scope: checking or fixing Zoho, bookkeeping, financial statements, VAT, writes to Zoho, Shopify or the Ops tables, approving/editing/sending POs (Finance only gives a verdict), payments, building the Coordinator's daily brief (Finance only writes its line), running ad campaigns.

## How it reaches Khaled

| Where | What | How often |
|---|---|---|
| Push to his phone | Expected cash falls below the floor within 14 days | Only then; once per episode, again only if worse or after 7 days |
| Daily brief | One line, only when a draft PO's verdict isn't `go` and the PO is due before his next PRNTCODE block | Rarely; until the brief exists it's sent as that day's notification |
| PRNTCODE block (`what-now`) | Finance status line; POs checked; the monthly review until opened; new suggestions | When he asks the CEO |
| Planning (Sun/Wed `refresh`) | One time request when the review is unopened or a non-`go` PO is undecided | As needed |
| Any time | Forecast and scenario questions | On request |

Nothing else is ever sent. A quiet daily run sends **nothing**.

## Fixed IDs (never re-discover)

| What | Value |
|---|---|
| Zoho organisation "Prntcode" | `891803522`. **Ignore** "PRNTCODE FOR TEXTILE TRADING" (`939188804`), an expired trial. |
| Zoho cash account | `6643263000000504278`, "PRNTCODE FOR FASHION AND CLOTHES DESIGNING - L.L.C" (Wio, live bank feed). **Only this one.** Leave out DEEPWEAR, Hessa Artist Wio, Petty Cash and Undeposited Funds. |
| PRNTCODE-ops (Supabase) | `nhimagmpcwlkbfygiowq`. Ops tables (`purchase_orders`, `purchase_order_lines`, `products`, `partners`, stock views) are **read-only**. Finance's own data is the **`finance` schema** here. |
| Coordinator ledger (Supabase `coordinator`) | `hgkreprqxevayruqpibf`. Finance reads `public.plan_blocks` (his PRNTCODE blocks); only `refresh` writes a Finance row to `public.requests`. |
| Shopify | the connected PRNTCODE store (history starts June 2025) |
| Time zone | Abu Dhabi, `Asia/Dubai`, UTC+4, no daylight saving |

## Load tools first

Deferred; load before anything else:
- Supabase: `tool_search("supabase execute sql")`
- Zoho Books: `tool_search("zoho books bank accounts transactions bills invoices expenses")`
- Shopify: `tool_search("shopify analytics orders graphql inventory")`

If one is missing, say which in one line (README → Connectors) and use what's left, labelling the gap. **Never** fill a gap with a guess. In `finance-daily`, a missing connector means: write nothing, send nothing (except the push if cash data is complete).

## Finance's own data: the `finance` schema

Migration: `supabase/migrations/20261009103151_finance_schema.sql` (+ `…103332_finance_po_latest_tiebreak.sql`). Row-level security on; anon and authenticated get nothing; **every write goes through a `finance.*` function**. Never `insert`, `update` or `delete` a `finance` table directly, and never any Ops table.

| Table | Holds | Write with |
|---|---|---|
| `finance.settings` (key → jsonb) | `cash_floor`, `months_cover_target` (default 3), `recurring_costs`, `partner_payment_terms`, `baseline_calibration`, `setup_done` | `finance.set_setting(key, value)` |
| `finance.forecast_snapshots` | one per month, saved on the 3rd | `finance.save_snapshot(month, months, weeks, assumptions)` (a second save the same month keeps the first), `finance.score_snapshot(month, actual, sales_err, costs_err, cash_err)` |
| `finance.scenarios` | name, ask, changes, assumptions, status `draft` / `base` / `dropped` | `finance.save_scenario(name, ask, changes, assumptions)` (drafts only), `finance.set_scenario_status(name, status)` |
| `finance.po_checks` | PO number, fingerprint, verdict, quantity, AED saved, wait-until, reasons | `finance.record_po_check(…)` (same PO + fingerprint writes nothing) |
| `finance.brief_lines` | at most one line a day | `finance.write_brief_line(for_date, line, po_number, delivered_as)`, `finance.mark_brief_line_read(for_date)` (Coordinator) |
| `finance.pushes` | low-cash pushes | `finance.push_due(gap_date, gap_aed)`, `finance.record_push(…)`, `finance.close_push_episode()` |
| `finance.reviews` | month, artifact link, suggestions, opened | `finance.record_review(month, url, suggestions)`, `finance.mark_review_opened(month)` |

Views: `finance.po_latest_check_v` (latest check per PO), `finance.accuracy_v` (running accuracy over the last 6 scored months).

Read settings at the start of every run:
```sql
select key, value from finance.settings;
```
Use `$q$…$q$` dollar-quoting for text and `'…'::jsonb` for JSON in every call.

**Settings by chat** ("set the floor to AED 20k", "rent isn't recurring, it's annual"): confirm in one line first (`Set cash floor → AED 20,000? (yes/no)`), then call `finance.set_setting`. Recurring costs are read, changed and written back as a whole JSON value.

**Launch dates are not a setting.** They come only from the Ops reference sheet (collections tab → `public.collections`), with each collection's product line read from its products (`forecast` §2). A date change in chat is pointed back to the sheet; a "what if" is a scenario. Never store a `launches` setting.

## Setup ("set up Finance", or the first time `setup_done` is missing)

1. **Cash floor**: ask once, store `cash_floor`.
2. **Upcoming launches**: show what Ops has (name, line, date) and anything that looks off (a placeholder date, a collection with no products yet). Corrections go in the Ops reference sheet, not here.
3. **Recurring costs**: show the list the forecast treats as recurring (forecast §4), one line each with its recent monthly level, and take corrections ("Klaviyo is cancelled", "the shoot isn't recurring", "the studio is quarterly"). Store as `recurring_costs` (shape in `forecast` §4; quarterly and yearly costs need `every` and `next_due`). New people on payroll are not a recurring-cost correction: they're a `cost` scenario made real, because Zoho has no history for them yet.
4. **Partner payment terms** (optional): "Deepwear takes 50% when the PO is sent and the rest on delivery". Store per Ops `partner_id` in `partner_payment_terms`. Default without terms: the full PO amount goes out the day it's sent.
5. `months_cover_target` = 3 unless he says otherwise. Set `setup_done` to today.
6. Reply in one line: `Finance set up · floor set · 2 launches · 14 recurring costs`.

## Money facts every skill relies on

- **Cash today** = the cash account's **`bank_balance`** from `ZohoBooks_list_bank_accounts` (the live bank feed), nothing else.
- **B2C sales** = Shopify **`net_sales`** from ShopifyQL (`FROM sales SHOW net_sales …`). It's net of discounts and returns and **excludes VAT**. Never divide it by 1.05. (On 9 Oct 2026 the store added VAT at checkout: `taxesIncluded = false` on every order.)
- **B2B sales** = Zoho invoices, **excluding the customer "Shopfy"** (Shopify sales posted to Zoho; 20 of 41 invoices on 9 Oct 2026; counting them double-counts Shopify) and **excluding drafts** until they're sent.
- **Deposits that aren't sales:** `owner_contribution` (owner top-ups, e.g. 29 Sep 2026), transfers between own accounts, refunds and reversals ("Reversal of …"). They never count in any sales figure. Network International card settlements arrive as `other_income` to "Network Control a/c"; they're the cash side of sales already counted in Shopify, so they aren't added again.
- **Costs** = Zoho expenses and bills. Ad spend is the "Paid Ads" account.
- **Currency:** some bills are in USD or INR. Use the bill's own `exchange_rate` (AED per unit of the bill currency: AED = amount × `exchange_rate`); otherwise the latest rate. Say which: `(INR at bill rate)`.

## Formatting (phone, one screen)

- `AED 12,400`, whole dirhams with thousands separators; `AED 12k` is fine in status lines and charts; `−AED 3,100` for negatives.
- Months `Dec`, `Jan 27`; dates `Mon 16 Nov`; weeks `w/c 16 Nov`.
- Short lines, no jargon ("money in", "money out", "low point", "profit").
- Charts and the monthly review are PRNTCODE-branded artifacts made with **`prntcode-brand-formatter`**; charts follow the `dataviz` skill if it's available.

## Hard rules (every Finance skill)

1. **Read-only, always:** Zoho, Shopify and the Ops tables.
2. **Writes only through `finance.*` functions** (and `refresh`'s one ledger row).
3. **Never guess a number.** Missing data is named; low-confidence parts (seasonality, launch bumps) are labelled as such.
4. **Nothing reaches his phone** except the push rule and the one brief line, both on `finance-daily`'s rules.
5. **No real numbers in this repo.** Examples are made up.
