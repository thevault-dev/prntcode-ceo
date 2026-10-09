# Finance v1 verification: 9 Oct 2026

Build of `BUILD BRIEF: PRNTCODE Finance agent (v1)` (9 Oct 2026) into prntcode-ceo **2.3.0**.

**This repo is public.** This page records pass or fail and *how* each check was made, never a real amount, balance, floor, salary or account number. Any figure shown is made up.

Legend: ✅ pass · ⏳ not run yet (and why) · ❌ fail

Live reads were **read-only** (Zoho Books organisation Prntcode, Shopify, the Ops tables, the Coordinator ledger). The only live writes: the `finance` schema migrations, and two self-tests that rolled themselves back.

## Definition of Done

| # | Check | Result | How |
|---|---|---|---|
| 1 | After plugin sync, `/prntcode-ceo:` lists `forecast`, `scenario`, `capital-review`, `po-check`, `finance-daily` | ✅ locally · ⏳ claude.ai | `claude plugin validate` passes on the marketplace and the plugin; the five skill folders have valid frontmatter. The claude.ai sync needs Khaled's account. |
| 2 | Setup asks for the cash floor and upcoming launches, shows the recurring-cost list; answers stored only in the `finance` schema | ✅ design + storage · ⏳ live | Setup is in `finance-reference.md` → Setup and writes only via `finance.set_setting`. Storage tested (schema test check 2). Needs Khaled's answers to run live. |
| 3 | No committed file holds a real amount, balance, floor, salary or account number | ✅ | Grepped every committed file for the balances, totals, monthly sales and masked account numbers seen in the live reads: no hits. Examples are made up and say so. |
| 4 | "How's cash?" in ≤ 8 lines; opening cash = the LLC Wio balance alone | ✅ shape and source · ⏳ live answer | The reply template is 8 lines (`forecast` §9). Live: `list_bank_accounts` returns the counted account's `bank_balance` separately, and the other four accounts are excluded by ID. |
| 5 | The forecast leaves the 29 Sep 2026 owner contribution and all "Shopfy" invoices out of sales | ✅ | Live: the 29 Sep money-in row on the cash account is `transaction_type = owner_contribution`, and B2C sales come from Shopify, not bank deposits, so it can't enter sales. Zoho has 41 invoices, 20 to "Shopfy" (7 overdue); `forecast` §3 filters that customer from sales and collections. |
| 6 | A launch Khaled entered shows a bump in its month; moving it moves the bump | ✅ dry run · ⏳ live | Dry run on live Shopify history (Jun 2025 to Sep 2026): the quiet-month baseline and the Jungle Edit RTW (July) window give a positive bump, and a test launch placed in April then May carried that bump to its new month. The Ops 1 Jan abaya "launch" shows no bump, so the rule now leaves it out. Needs a launch in settings for the live check. |
| 7 | "Hire a tailor at AED X a month from January" → base-vs-scenario chart, four numbers, verdict | ⏳ | Needs setup (floor) and the plugin in claude.ai for the artifact. Change type `cost`, the four numbers and the reply shape are in `scenario` §1–§3. |
| 8 | Stacking changes the result; saving and comparing up to three works | ✅ storage · ⏳ live | Schema test check 4 (save, edit while draft, status changes). Stacking and comparing are in `scenario` §4. |
| 9 | "Make it real" adds the scenario to the base; the next "how's cash?" reflects it | ✅ storage · ⏳ live | `finance.set_scenario_status(…, 'base')` tested (check 4), and a base scenario can't be edited. `forecast` §7 applies every `base` scenario. |
| 10 | A test draft PO is checked and the verdict stored; an oversized one gets `go smaller` with quantity and AED saved; nothing written to the Ops tables | ✅ storage · ⏳ live PO | Schema test check 5: `go_smaller` without a quantity and AED saved is refused, a stored verdict is kept for an unchanged PO, and the latest-check view follows a changed PO (this found and fixed a tie-break bug, migration `…103332`). There are **no POs in Ops yet**, and making one would mean writing to an Ops table, so the live check waits for Ops' first draft. |
| 11 | A non-`go` PO due before the next booked PRNTCODE block → exactly one brief line, sent as that day's notification | ✅ storage · ⏳ live | Schema test check 6: a second line the same day is refused. `plan_blocks` (kind, status, slot_start) exists in the Coordinator ledger as `finance-daily` §4 expects. |
| 12 | A test commitment dropping expected cash below the floor within 14 days → one push with options; the next day's run doesn't push again | ✅ rule · ⏳ live | Schema test check 7: the first push is due; the same gap the next day isn't (and `record_push` refuses it); a bigger or sooner gap, or 7 days on, is due again; closing the episode resets it. A live push needs the floor and the scheduled task. |
| 13 | A quiet daily run sends no notification | ✅ design · ⏳ live | `finance-daily` §7 sends nothing on a quiet run; the build report says to switch off the task's own completion notification. |
| 14 | A run dated the 3rd saves a snapshot, shows forecast vs actual, delivers the capital review artifact (≤ 5 ranked suggestions with AED, evidence, "simulate it") | ✅ storage · ⏳ live | Schema test checks 3 and 8: one snapshot a month (a second save keeps the first), scoring, reviews stored unopened. Needs a run on the 3rd. |
| 15 | `what-now` shows the Finance status line and lists the review until opened | ⏳ | Wired in `what-now` §2b (reads `finance.reviews.opened_at`); needs a live PRNTCODE block. |
| 16 | With the review unopened, `refresh` posts exactly one `sub_agent = finance` request; a re-run posts nothing; it's withdrawn once the review is opened | ✅ ledger | [`tests/finance_ledger_check.sql`](../tests/finance_ledger_check.sql): one post (`Finance — monthly review + 1 PO`, 45 min), 0 rows on re-run, title-only update, withdraw with `nothing pending in Finance`, no reopening. Result: `ALL FINANCE LEDGER CHECKS PASSED`, no rows left behind. |
| 17 | The withdraw sweep and `close-task` leave Finance rows alone | ✅ | Same test, check 4 (the sweep's filter skips `sub_agent = finance`) and check 5 (close-task's stamp is accepted); `close-task` replies `Finance item closed — nothing in the tracker` with no Notion call. |
| 18 | "What if we take a workshop at AED 8k a month?" reaches `scenario` | ✅ | `ceo` §3d routes "what if…" (this exact example) to `scenario`; it's also in `scenario`'s description. |
| 19 | The scheduled task's name, time and prompt are in the build report | ✅ | [`BUILD_REPORT_FINANCE.md`](../BUILD_REPORT_FINANCE.md#the-scheduled-task). |
| 20 | Charters, org table, README, plugin.json, marketplace.json updated; brief-line contract documented | ✅ | Finance charter live with its schedule; org table, CEO org table and org chart; README (Usage, When it reaches you, [Brief-line contract](../README.md#brief-line-contract)); both manifests at 2.3.0. |
| 21 | This verification doc, pass or fail per check, made-up numbers only | ✅ | This page. |

**Self-test results (9 Oct 2026):**
- [`tests/finance_schema_check.sql`](../tests/finance_schema_check.sql) on PRNTCODE-ops: `ALL FINANCE SCHEMA CHECKS PASSED` (the first run failed check 5, the latest-check tie-break; fixed by migration `20261009103332`, then passed). Rolled back.
- [`tests/finance_ledger_check.sql`](../tests/finance_ledger_check.sql) on coordinator: `ALL FINANCE LEDGER CHECKS PASSED`. Rolled back; `count(*) where source_ref like 'finance:%'` = 0 afterwards.

## Next checks once it's live

After the plugin syncs and `set up Finance` is done: re-run checks 2, 4, 6–9, 12–15 in chat, and 10–11 when Ops raises its first draft PO. Update this page with the results.
