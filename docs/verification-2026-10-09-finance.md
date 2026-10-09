# Finance v1 verification: 9 Oct 2026

Build of `BUILD BRIEF: PRNTCODE Finance, the analyst (v1)` into prntcode-ceo **2.3.0**.

**This repo is public.** This page records pass or fail and *how* each check was made, never a real amount, balance, floor, fee rate, salary or account number. Any figure shown is made up.

Legend: ✅ pass · ⏳ not run yet (and why) · ❌ fail

All live reads were **read-only** (Zoho Books organisation Prntcode, Shopify, the Ops App `PRNTCODE-ops`). The only live writes were the Notion Finance page set-up, and one ledger test that rolled itself back.

## Definition of Done

| # | Check | Result | How |
|---|---|---|---|
| 1 | After plugin sync, `/prntcode-ceo:` lists `unit-economics`, `ask-finance`, `cash-outlook`, `monthly-review` | ✅ locally · ⏳ claude.ai | `claude plugin validate` passes on the marketplace and the plugin; the four skill folders have valid frontmatter. The claude.ai plugin sync needs Khaled's account. |
| 2 | Setup creates the Notion Finance page with settings, commitments, bill answers, decision log and monthly reviews; real numbers only there | ✅ | Created *Trackers & Tings → Finance* with its five data sources. Settings are seeded only with the brief's defaults and Zoho IDs; floor, atelier cost, minutes and fee rates are left **empty** for Khaled. |
| 3 | No committed file holds a real amount, balance, floor, fee rate, salary or account number | ✅ | Grepped every committed file for the balances, totals and masked account numbers seen in the live reads: no hits. Examples are made up and say so. |
| 4 | Unit economics for a named SKU shows each material × quantity × cost | ⏳ blocked on costs | The query returns each SKU's BOM lines (e.g. `JGLEDT-ABY-BTF-TER-L` → `MAKE-ABY` × 1), but **no material or product has a cost yet**, so every line reads `cost missing`. Re-run once costs are in the reference sheet. |
| 5 | With costs missing, unit economics lists the gap ranked by revenue touched, labels the product "cost missing", writes nothing to the Ops App or sheet | ✅ | Live: 302 products, 204 with a BOM, 5 materials, 0 costs. Ranked by trailing-12-month Shopify revenue: **revenue with no SKU match** (blank or unknown SKU) is the biggest gap, then `MAKE-ABY` (Abaya stitching), then `MAKE-RTW`. Only `select` statements ran. |
| 6 | Full cost and extra cost, labour share follows the atelier cost in Settings | ⏳ | Needs the atelier cost, minutes and standard minutes (setup step 3) and material costs. The formula reads the Settings row live on every run. |
| 7 | "Should I restock <print>?" gives the five-part answer on one screen, with a funding check, and logs it | ⏳ | Needs costs (profit per piece) and a cash floor. Shape and logging are in `ask-finance` §4–5. |
| 8 | A pop-up question with a made-up stall fee returns sales needed to break even | ⏳ | Needs in-person contribution margin, so costs. `pop_up_events` has no rows yet, so no past pop-ups to compare against. |
| 9 | A deliberately unaffordable funding check → RED with max amount, earliest date and split | ⏳ | Needs the cash floor set. Method in `ask-finance` §3. |
| 10 | No commitment until "go"; after "go" it appears in the next outlook | ⏳ | Needs a live run with Khaled. |
| 11 | The Operations contract line returns exactly one line in one of three formats | ⏳ | Formats fixed in `ask-finance` §7; Operations isn't wired yet. |
| 12 | Opening cash equals the LLC Wio bank-feed balance alone | ✅ | `list_bank_accounts` returns the counted account's `bank_balance` (feed) separately from its book `balance`. DEEPWEAR (cash type), Hessa Artist Wio, Petty Cash and Undeposited Funds are all present in the list and excluded by ID. |
| 13 | Book-vs-bank gap and uncategorised count appear when the gap is over tolerance | ✅ | Live, book and bank differ by more than the AED 1,000 tolerance, and the account reports **9** uncategorised transactions, so both lines would show. |
| 14 | Each of the 8 weekly rows shows both lines; status follows the rule | ⏳ | Needs the floor. `show weeks` format in `cash-outlook` §6. |
| 15 | `show details` lists the 29 Sep 2026 owner contribution among excluded deposits | ✅ | Live: the 29 Sep money-in row on the counted account is `transaction_type = owner_contribution`, so the first classification rule excludes it as `owner top-up`. |
| 16 | Bill triage lists only open bills over the threshold, records answers, doesn't ask again; Zoho unchanged | ✅ list · ⏳ answers | Live: 9 unpaid bills; after converting the two INR bills at their bill rate, 7 are over AED 1,000 and 2 are under (shown as a count). Recording answers and "don't ask again" need Khaled's reply. Only list calls ran. |
| 17 | Test commitment "rent AED X monthly on the 1st" appears in every month in the 8 weeks, disappears once cancelled | ⏳ | Needs a live run (expansion rules in `cash-outlook` §2a, cancel in §7). |
| 18 | September review revenue = Shopify September net sales ex-VAT, within AED 1 | ✅ source · ⏳ full review | ShopifyQL `net_sales` by `sales_channel` for 1–30 Sep sums exactly to the `WITH TOTALS` figure. See finding F1 on VAT. |
| 19 | The review shows cost-missing share and cash tied up in stock, ends with three yes/no decisions, answers logged | ⏳ | Needs costs for anything other than "100% cost missing". |
| 20 | A seeded decision-log entry 30+ days old shows predicted vs actual; test row removed | ⏳ | Needs a review run. |
| 21 | `what-now` shows the Finance status line and lists the review when due | ⏳ | Wired in `what-now` §2b; needs a live PRNTCODE block. The September review counts as due from 1 Oct. |
| 22 | A refresh with an AMBER test commitment posts exactly one `sub_agent = finance` request and one pre-brief line | ✅ ledger · ⏳ end to end | [`tests/finance_ledger_check.sql`](../tests/finance_ledger_check.sql) check 1: one Finance row. The pre-brief line is in `refresh` §6b/§7. |
| 23 | A second refresh writes nothing; removing the test commitment withdraws the request | ✅ | Same test, checks 2 (0 rows), 3 (title-only update, estimate kept), 6 (`withdrawn by prntcode: nothing pending in Finance`), 7 (not reopened). |
| 24 | The withdraw sweep and `close-task` leave Finance rows alone | ✅ | Same test, check 4 (the sweep's filter skips `sub_agent = finance`) and check 5 (close-task's stamp is accepted on a Finance row); `close-task` replies `Finance item closed — nothing in the tracker` and makes no Notion call. |
| 25 | No new scheduled task; no Finance skill sends a message on its own | ✅ | No task was created. None of the four Finance skills mention a schedule, cron or push; each says it only answers. |
| 26 | "how's cash?" and "should I mark down Checkered Orchid?" both reach Finance | ✅ | `ceo` §3d routes both (to `cash-outlook` and `ask-finance`); both phrases are in the skills' descriptions too. |
| 27 | Charters, org table, README, plugin.json and marketplace.json updated and at 2.3.0 | ✅ | Finance charter live with its report list; org table, CEO org table, org chart, README (Usage section) and both manifests at 2.3.0. |
| 28 | This verification doc, pass or fail per check, made-up numbers only | ✅ | This page. |

**Ledger test result** (Supabase `coordinator`, run 9 Oct 2026): `ALL FINANCE LEDGER CHECKS PASSED`; afterwards `count(*) where source_ref like 'finance:%'` = 0, so nothing was left behind.

## Findings for Khaled

- **F1. VAT is added at checkout, not included in prices.** The brief says prices include VAT. On 9 Oct every September order had `taxesIncluded = false`: VAT is added on top for UAE orders and zero-rated for orders shipped abroad. The skills therefore take revenue from Shopify's `net_sales`, which is already ex-VAT, and never divide by 1.05 (which would understate revenue by about 5%).
- **F2. Online card payouts arrive from Ziina**, often uncategorised, with no deposits named Shopify or Stripe. Ziina is added to `operating_deposit_payers` in Settings so the sales run-rate counts it. Confirm or remove it.
- **F3. The biggest cost gap is revenue with no SKU match.** A large share of the last 12 months' Shopify revenue sits on lines with a blank SKU, plus a few SKUs the Ops App doesn't know (e.g. `JGLEDTABY-…`, missing a dash). Those lines can't be costed until Shopify SKUs match the Ops App.
- **F4. The BOMs only hold "making" lines.** Every BOM line is one of the four `MAKE-*` materials × 1. Fabric, trims and packaging aren't in the materials list yet, so even after making costs are entered, full cost will be understated until they're added.
- **F5. `purchase_orders` and `pop_up_events` are empty**, so the outlook has no PO outflows yet and pop-up questions have no history to compare against.
- **F6. Bill triage will matter.** Several recurring bills show as unpaid for up to three months; per the brief's note they may already be paid. The first triage settles which ones count.

## Next steps for Khaled (in chat, after the plugin syncs)

1. `set up Finance`: answer the four settings questions (floor, atelier cost and minutes, standard minutes per type, fee rates), then the bill triage.
2. Enter making, fabric, trims and packaging costs in the reference sheet's inputs tab, and fix the unmatched Shopify SKUs.
3. Then re-run checks 4, 6–11, 14, 17 and 19–21 and update this page.
