# Finance · 🟢 live

**Owns:** three things for Khaled.
1. An **accurate forecast** of PRNTCODE's sales, costs, profit and cash.
2. **Scenarios**: simulate a decision and see its financial impact before making it.
3. A **capital efficiency review**: how the business uses its money, and moves that free or earn cash.

It takes Zoho **as it is**. Keeping Zoho correct is the **Auditor's** job, not Finance's.

**Doesn't own:** checking or fixing Zoho, bookkeeping, financial statements, VAT; writing to Zoho, Shopify or the Ops tables; approving, editing or sending POs (Finance only gives a verdict); payments; building the Coordinator's daily brief (Finance only writes its line); running ad campaigns.

**Skills (live)**
- [`forecast`](../../skills/forecast/SKILL.md): the base: 12 months by month (sales, costs, profit, cash) and 8 weeks of cash by week, against the floor, with a running accuracy figure. "How's cash?" in 8 lines or fewer.
- [`scenario`](../../skills/scenario/SKILL.md): "what if…" in plain words → explicit changes and assumptions → base-vs-scenario chart, four numbers and a verdict. Stack, save, compare three, make it real, drop it.
- [`capital-review`](../../skills/capital-review/SKILL.md): monthly: up to five moves ranked by AED over 90 days, each with evidence and "simulate it"; forecast vs actual; the 12-month chart. A PRNTCODE-branded artifact.
- [`po-check`](../../skills/po-check/SKILL.md): every draft PO: can we afford it, is the quantity right, could it wait → `go`, `go smaller` or `wait until <date>`.
- [`finance-daily`](../../skills/finance-daily/SKILL.md): the one scheduled task (below).

Shared facts, storage and rules: [`finance-reference.md`](finance-reference.md). Data: the `finance` schema in PRNTCODE-ops ([migration](../../../../supabase/migrations/20261009103151_finance_schema.sql)).

## Schedule

| When | What | Reaches Khaled? |
|---|---|---|
| **Daily ~06:30 Abu Dhabi** (`PRNTCODE Finance daily`, `/prntcode-ceo:finance-daily`) | rebuild the forecast, check new draft POs, push rule, brief line | Only by the push rule or the brief line; a quiet run sends nothing |
| **3rd of each month** (same task) | save the forecast snapshot, score last month, run the capital review | No; the review waits for his PRNTCODE block |
| **Sun and Wed 20:00** (the refresh) | one time request when the review is unopened or a non-`go` PO is undecided | Through planning |
| **PRNTCODE block** (`what-now`) | Finance status line, POs checked, the review until opened, new suggestions | When he asks the CEO |
| **Any time** | forecast and scenario questions | On request |

**Push rule:** expected cash falls below the floor within 14 days → one push with the date, the gap and two or three ways to close it. Repeats only if the gap gets worse or 7 days pass.

**Brief line:** at most one a day, only when a draft PO's verdict isn't `go` and it's due before his next booked PRNTCODE block. Sent as that day's notification until the Coordinator's daily brief exists ([contract](../../../../README.md#brief-line-contract)).

## Data

- **Reads (read-only, always):** Zoho Books (bank balance, expenses, bills, invoices), Shopify (orders, channels, inventory, cost per item), PRNTCODE-ops (`purchase_orders`, `purchase_order_lines`, products, stock views), and the Coordinator ledger's `plan_blocks`.
- **Writes:** only the `finance` schema, through its functions; plus `refresh`'s one ledger row and the one Todoist item when a push or brief line is sent. **Real numbers live only there**; this repo is public.

**Scorecard:** the running forecast accuracy (sales, costs, cash) from `finance.accuracy_v`.

## Planned (not v1)

An interactive scenario page with sliders · forecasts by product line (RTW, abayas, jalabiyas, swimwear) once each has enough history · Stripe payouts, once Stripe is connected.
