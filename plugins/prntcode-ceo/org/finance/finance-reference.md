# Finance reference (read by every Finance skill)

Shared facts, IDs, settings and rules for `unit-economics`, `ask-finance`, `cash-outlook` and `monthly-review`. Each of those skills reads this file first (from its own base directory: `../../org/finance/finance-reference.md`).

> **This repo is public.** No real amount, balance, floor, fee rate, salary or account number goes in any committed file, including docs and tests. Real numbers live only in the Notion **Finance** page. Examples in these files use made-up numbers.

## Who and how

- **Khaled only**, in claude.ai chat, mostly on his phone.
- **Finance never messages him on its own schedule.** It runs only when he asks, when the CEO opener (`what-now`) asks for its status line, or inside the Sun/Wed 20:00 `refresh`. No Finance skill creates a scheduled task.
- **Not Finance's job:** financial statements, month-end close, reconciliations, VAT returns, tax advice, payments, running ad campaigns, campaign attribution, late-order or resupply alerts, Atelier planning. Zoho keeps the books; Finance never repeats them.

## Fixed IDs (never re-discover)

| What | Value |
|---|---|
| Notion page "Finance" (under Trackers & Tings) | `3f4e351b-3578-81e9-9c48-f5de1684deb3` |
| Settings | `collection://b18d7ed9-92a5-4e66-99cf-eaed13b146a1` |
| Commitments | `collection://d15ff5ba-c916-478b-8118-980f9ab48ee9` |
| Bill answers | `collection://9cd6bc93-8659-4e23-9cc4-1ba9437aed40` |
| Decision log | `collection://414e0fe0-528a-4eec-a175-fbad713b915b` |
| Monthly reviews | `collection://6a13f42d-f158-4e3b-bf4c-a00e4562c40e` |
| Zoho organisation "Prntcode" | `891803522` (the default). **Ignore** "PRNTCODE FOR TEXTILE TRADING" (`939188804`), an expired trial. |
| Zoho counted account | `6643263000000504278`, "PRNTCODE FOR FASHION AND CLOTHES DESIGNING - L.L.C" (Wio, live bank feed). **Only this one.** Never count DEEPWEAR (a cash-type account), Hessa Artist Wio, Petty Cash or Undeposited Funds. |
| Ops App (Supabase `PRNTCODE-ops`) | `nhimagmpcwlkbfygiowq`, **read-only** |
| Coordinator ledger (Supabase `coordinator`) | `hgkreprqxevayruqpibf`, `public.requests` (only the `refresh` skill writes Finance rows there) |
| Time zone | Abu Dhabi, `Asia/Dubai`, UTC+4, no daylight saving |

The Zoho IDs are also stored in Settings (`zoho_org_id`, `cash_account_id`). If they ever differ, Settings wins and the run says so in one line.

## Load tools first

All connectors are deferred. Load what the skill needs before anything else:
- Notion: `tool_search("notion query data sources fetch create pages update page")`
- Zoho Books: `tool_search("zoho books bank accounts transactions bills invoices expenses")`
- Supabase: `tool_search("supabase execute sql")`
- Shopify: `tool_search("shopify analytics orders graphql")`

If a connector a step needs is missing or fails with an auth error, say which one in one line (README → Connectors) and carry on with what's left, labelling the gap. **Never** fill a gap with a guess.

## Settings (Notion, one row per key)

Read them all at the start of a run:
```sql
SELECT "Key", "Value", "Unit" FROM "collection://b18d7ed9-92a5-4e66-99cf-eaed13b146a1"
```

| Key | Meaning | If empty |
|---|---|---|
| `zoho_org_id`, `cash_account_id` | as above | use the fixed IDs |
| `cash_floor` | AED; the line cash must not drop below | use 0 and add `floor not set` to the status line |
| `book_bank_tolerance` | AED, default 1,000 | 1,000 |
| `bill_triage_threshold` | AED, default 1,000 | 1,000 |
| `lookahead_weeks` | default 8 | 8 |
| `fee_rates` | JSON, % of the order total incl. VAT, per channel: `network_international`, `shopify_payments`, `stripe`, `ziina` | that channel's fee shows as `fee missing` |
| `atelier_monthly_cost` | AED a month, salaried tailors and embroiderers | labour share shows as `labour missing` |
| `atelier_minutes_per_month` | working minutes the atelier has in a month | same |
| `standard_minutes` | JSON per `product_type`, until the Atelier supplies them | ask once (setup step 3) |
| `operating_deposit_payers` | `;`-separated names; a deposit whose description contains one counts as sales | `NETWORK INTERNATIONAL; SHOPIFY; STRIPE; ZIINA` |
| `excluded_deposit_types` | left out of the run-rate | `owner_contribution; transfer_fund; refund; reversal` |
| `bill_triage_done` | `no`, or the date of the first triage | `no` |

**Changing a setting by chat** ("set cash floor AED 20,000", "atelier cost is AED 9,000 a month", "Stripe fee 2.9%"): confirm in one line first (`Set cash floor → AED 20,000? (yes/no)`), then `notion-update-page` that row's `Value` only. Never print a setting's real value anywhere but the chat.

## Formatting (phone, one screen)

- Money: `AED 12,400`. Whole dirhams with thousands separators; `−AED 3,100` for negatives. Other currencies: convert (below) and show the AED figure.
- Dates: `Mon 16 Nov`, `week of 16 Nov` (weeks start Monday).
- Short lines, no jargon. Say "money in / money out", "profit per piece", "low point".
- Status words are always `GREEN`, `AMBER` or `RED`.

**Currency.** Some Zoho bills are in USD or INR. Use the bill's own `exchange_rate` (AED per one unit of the bill's currency, so AED = `balance × exchange_rate`); otherwise the latest rate (Zoho's currency settings, or the Ops App reference sheet's FX), and say which: `(USD at bill rate)` / `(INR at latest rate)`.

## Money facts the skills rely on

- **Opening cash** = the counted account's **bank-feed balance** (`bank_balance` from `ZohoBooks_list_bank_accounts`), never the book balance. If `|balance − bank_balance|` (book minus bank) is over `book_bank_tolerance`, show both and the account's `uncategorized_transactions` count.
- **Open bills are not a forward payables list.** Bills are often entered on the day they're paid, with the due date set to the bill date, and several show 60–90 days overdue that may already be paid. That's why bill triage exists; a bill counts as money out only when Khaled answered `owed`.
- **Owner top-ups** arrive as `transaction_type = owner_contribution`. **Network International** settlements arrive as `other_income` to "Network Control a/c" (or uncategorised, description `From NETWORK INTERNATIONAL LLC`). Online card payouts arrive as `From ZIINA PAYMENT LLC` (often uncategorised).
- **Shopify sales are posted to Zoho as one lump item**, so per-order detail always comes from Shopify.
- **Ad spend** = Zoho expenses and bank transactions whose offset account is **Paid Ads**.
- **Courier cost** = Zoho expenses to the courier accounts/vendors (Quiqup, Aramex and the like), divided by shipped orders in the same period.
- **VAT:** revenue is always shown **excluding the 5% VAT**. Take it from ShopifyQL `net_sales` (`FROM sales SHOW net_sales …`), which Shopify reports net of discounts and returns and **without tax**, whichever way prices are set. Never divide `net_sales` by 1.05. Only when working from raw order amounts, check each order's `taxesIncluded`: if `true`, revenue = amount − `totalTaxSet`; if `false`, the amount is already ex-VAT. (On 9 Oct 2026 the store's September orders all had `taxesIncluded = false`: VAT is added at checkout, and zero-rated for orders shipped outside the UAE.)
- **Channels:** Shopify's `sales_channel` (Online Store, Shopify Mobile / POS, Draft Orders…). Online orders carry ad spend; in-person ones don't. The payment-fee channel comes from the order's `paymentGatewayNames` (Network International terminal, Shopify Payments, Stripe, Ziina, cash, bank transfer = no fee).

### Deposit classification (run-rate and `show details`)

For each **money-in** bank transaction (`debit_or_credit = debit`) on the counted account:

| Rule (first match wins) | Class |
|---|---|
| `transaction_type` = `owner_contribution` | excluded: owner top-up |
| `transaction_type` in `transfer_fund`, `deposit` from an own account, or the description names another own account (DEEPWEAR, Hessa, Petty Cash) | excluded: own-account transfer |
| description starts `Reversal of`, or `transaction_type` = `expense_refund` / `refund` | excluded: refund or reversal |
| description contains one of `operating_deposit_payers` | **operating** (sales) |
| anything else | excluded: other (listed, so Khaled can say "count X as sales") |

Uncategorised transactions are classified by the same rules; Zoho is never changed.

## Unit costs never come from Notion

Costs live in the Ops App (`products.unit_cost`, `materials.unit_cost`, BOMs), mastered in the reference Google Sheet's inputs tab and synced in (`reference_sync_log`). Finance never writes to the Ops App or the sheet; it lists what's missing and tells Khaled where to enter it. For stock Deepwear already made, it may use the landed cost (`TOTAL PER PIECE`) from that collection's costing sheet (the one `prntcode-pricing` reads), labelled `landed cost from costing sheet`.

## The decision log (feature 5: the track record)

Every Ask Finance answer, every funding check and every monthly-review decision is one row:

| Property | Value |
|---|---|
| `Decision` (title) | `<type>: <subject>`, e.g. `restock: Butterfly` |
| `Date` | today (Abu Dhabi) |
| `Type` | one of the select options (restock, markdown, bundle, archive, price, wholesale, pop-up go/no-go, pop-up post-mortem, ad budget, quote floor, hire, workspace, equipment, cut a cost, funding check, monthly review, other) |
| `Recommendation` | the one-line recommendation |
| `Answer` | `pending` until Khaled replies; then `yes`, `no` or `changed` (+ `Answer note` with his words) |
| `Profit 30d`, `Profit 90d`, `Cash 30d`, `Cash 90d` | predicted AED impact of the **recommended** option |
| `Spend`, `Spend due`, `Verdict` | the affordability check, if there was a spend |
| `Confidence`, `Missing data` | as shown in the answer |
| `Subject` | the print, SKU, event or cost, written so the review can measure it later (`print_id=BTF`, `event=Vibey Nov`, `cost=Klaviyo`) |
| `Source ref` | `chat`, `review:<YYYY-MM>`, or the Operations `source_ref` |

Writing the row needs no confirmation (the brief makes it part of every answer). The monthly review fills `Actual 30d` / `Actual 90d` and `Scored 30d` / `Scored 90d`.

## Setup ("set up Finance", or the first time a skill finds a required setting empty)

Run once; each step is skipped if it's already done.

1. **Notion page.** Check the Finance page and the five data sources above exist (`notion-fetch`). If one is missing, recreate it under the Finance page with the schema in [Notion schemas](#notion-schemas) and say so.
2. **Cost gap list** (`unit-economics` step 2): materials and products that need a cost, ranked by the revenue they touch. Tell Khaled to enter them in the reference sheet's inputs tab, which syncs to the Ops App.
3. **Settings Khaled must give**, one question each, in this order, only if empty: cash floor; atelier monthly cost and working minutes a month; standard minutes per product type (`ABAYA`, `RTW`, `Jalabiya`, `Accessories`; 0 for a type the atelier doesn't touch); fee rate per channel. Each answer is confirmed in one line, then written.
4. **Bill triage** (`cash-outlook` step 3).
5. Reply with one line: `Finance set up · <n> settings still empty · <n> costs missing`.

## Hard rules (every Finance skill)

1. **Read-only, always:** Zoho, Shopify, the Ops App and the reference sheet. No create, update, categorise, delete or payment call, ever.
2. **Notion writes only to the Finance page's five data sources.** Commitments and settings are confirmed in one line first; bill answers are written from Khaled's triage reply; decision-log rows are written with every answer.
3. **No commitment exists until Khaled says "go"** (or confirms an add in chat).
4. **Costs are never guessed.** A missing cost is `cost missing` with its share of revenue.
5. **No message on its own schedule. No scheduled task.**
6. **Nothing real in the repo.** Examples use made-up numbers.

## Notion schemas

Used only by setup step 1 to recreate a missing data source under the Finance page (`notion-create-database`, parent page `3f4e351b-3578-81e9-9c48-f5de1684deb3`). After recreating one, update its `collection://` ID in this file's Fixed IDs in the next build.

```sql
-- Finance settings
CREATE TABLE ("Key" TITLE, "Value" RICH_TEXT, "Unit" RICH_TEXT,
  "Group" SELECT('Zoho':blue, 'Cash':green, 'Costs':orange, 'Fees':purple, 'Run-rate':gray),
  "Notes" RICH_TEXT, "Updated" LAST_EDITED_TIME)

-- Finance commitments
CREATE TABLE ("Name" TITLE, "Counterparty" RICH_TEXT, "Direction" SELECT('out':red, 'in':green),
  "Amount" NUMBER, "Currency" SELECT('AED':default, 'USD':blue, 'EUR':purple, 'GBP':pink, 'INR':orange),
  "Due date" DATE, "Repeat" RICH_TEXT,
  "Status" SELECT('planned':gray, 'confirmed':blue, 'paid':green, 'cancelled':red),
  "Source" SELECT('chat':default, 'Zoho bill':blue, 'funding check':purple),
  "Zoho bill ID" RICH_TEXT, "Source ref" RICH_TEXT, "Notes" RICH_TEXT, "Created" CREATED_TIME)

-- Finance bill answers
CREATE TABLE ("Bill" TITLE, "Zoho bill ID" RICH_TEXT, "Answer" SELECT('owed':red, 'paid':green),
  "Answered" DATE, "Bill date" DATE, "Notes" RICH_TEXT)

-- Finance decision log
CREATE TABLE ("Decision" TITLE, "ID" UNIQUE_ID PREFIX 'FIN', "Date" DATE,
  "Type" SELECT('restock', 'markdown', 'bundle', 'archive', 'price', 'wholesale', 'pop-up go/no-go',
    'pop-up post-mortem', 'ad budget', 'quote floor', 'hire', 'workspace', 'equipment', 'cut a cost',
    'funding check', 'monthly review', 'other'),
  "Recommendation" RICH_TEXT, "Answer" SELECT('pending', 'yes', 'no', 'changed'), "Answer note" RICH_TEXT,
  "Profit 30d" NUMBER, "Profit 90d" NUMBER, "Cash 30d" NUMBER, "Cash 90d" NUMBER,
  "Spend" NUMBER, "Spend due" DATE, "Verdict" SELECT('GREEN', 'AMBER', 'RED'),
  "Confidence" SELECT('high', 'medium', 'low'), "Missing data" RICH_TEXT,
  "Source ref" RICH_TEXT, "Subject" RICH_TEXT,
  "Actual 30d" RICH_TEXT, "Actual 90d" RICH_TEXT, "Scored 30d" DATE, "Scored 90d" DATE)

-- Finance monthly reviews
CREATE TABLE ("Month" TITLE, "Status" SELECT('due':yellow, 'done':green), "Artifact" URL,
  "Decision 1" RICH_TEXT, "Decision 2" RICH_TEXT, "Decision 3" RICH_TEXT, "Delivered" DATE)
```
