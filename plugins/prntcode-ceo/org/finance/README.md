# Finance · 🟢 live

**Owns:** helping Khaled run PRNTCODE more profitably. Finance is his analyst: it answers money decisions with numbers, options and a recommendation, finds the biggest profit levers each month, keeps cash safe while he acts, and keeps a track record of its own advice so he knows how far to trust it.

**Doesn't own:** the books. Zoho keeps them and produces the statements; Finance never repeats them. Also out: month-end close, reconciliations, VAT returns, tax advice, making or scheduling payments, running ad campaigns (Paid Social), attribution (Marketing), late-order and resupply alerts (Operations) and Atelier planning.

**Skills (live)**
- [`unit-economics`](../../skills/unit-economics/SKILL.md): what each piece costs (full cost and extra cost) and leaves behind, by product and channel. Setup's first job is the gap list of missing costs, ranked by revenue touched.
- [`ask-finance`](../../skills/ask-finance/SKILL.md): the analyst. Any money decision in a fixed five-part answer on one phone screen, with a funding check inside; the Operations handoff line. Every answer goes in the decision log; a spend becomes a commitment only on "go".
- [`cash-outlook`](../../skills/cash-outlook/SKILL.md): the 8-week cash guardrail (committed-only and expected lines, GREEN / AMBER / RED), bill triage and commitments by chat.
- [`monthly-review`](../../skills/monthly-review/SKILL.md): the previous month's profit by print, product and channel, cash tied up in stock, what moved and why, the track record, and three yes/no decisions, as a PRNTCODE-branded artifact.

Shared facts, IDs and rules: [`finance-reference.md`](finance-reference.md).

## Reports (the list Khaled asked for)

| Report | When | Where it reaches him |
|---|---|---|
| Finance status line (`Cash GREEN · low AED X, week of 16 Nov`) | every PRNTCODE block | the CEO opener (`what-now`) |
| Cash outlook (≤ 8 lines; `show weeks`, `show details`) | when he asks ("how's cash?") | chat |
| Ask Finance answer (recommendation, 3 numbers, options, affordability, confidence) | when he asks a money question | chat |
| Funding check (GREEN / AMBER / RED, max amount, earliest date, split) | inside every Ask Finance answer, or on its own | chat; one line back to Operations |
| Unit economics and the cost gap list | when he asks, and at setup | chat |
| Monthly review + 3 decisions | from the 1st, until done, when he picks it | an opener pick (`September review · 20 min · 3 decisions`), then a branded artifact |
| Track record (hit rate, biggest miss) | inside the monthly review | the review artifact |
| Finance time request + one pre-brief line | Sun and Wed 20:00, only when cash is AMBER/RED, a review is due or decisions are waiting | the refresh → Coordinator planning |

**Finance never messages him on its own schedule.** No scheduled task belongs to Finance.

## Data

- **Reads (read-only, always):** Zoho Books (organisation Prntcode; cash, bills, invoices, expenses), Shopify (orders and channels), the Ops App (products, bills of materials, materials, purchase orders, stock, pop-ups) and, for landed cost, the collection costing sheets.
- **Writes:** only its own Notion page, **Finance** (under Trackers & Tings): Settings, Commitments, Bill answers, Decision log, Monthly reviews. **Real numbers live only there**; this repo is public.
- Costs live in the Ops App, entered in the reference sheet's inputs tab. There's no cost database in Notion.

**Scorecard:** the decision log's hit rate at 30 and 90 days, and the biggest miss (for the Observatory).

## Planned (not v1)

Collection budgets (a materials budget per collection, agreed before cutting starts) · an overhead review (every fixed monthly cost and what it buys, including the second, expired-trial Zoho organisation) · a daily cash check that alerts only when cash would go RED within 7 days, once the Coordinator's daily brief and feed exist · Stripe payouts, once Stripe is connected.
