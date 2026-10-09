# Build report: PRNTCODE Finance agent (v1) · prntcode-ceo 2.3.0

Built from `BUILD BRIEF: PRNTCODE Finance agent (v1)`, 9 Oct 2026 (it supersedes every earlier Finance brief; the earlier 5 Oct "analyst" design is not shipped).

## What's in it

- **Five skills:** `forecast`, `scenario`, `capital-review`, `po-check` and `finance-daily` (the scheduled run), sharing [`org/finance/finance-reference.md`](plugins/prntcode-ceo/org/finance/finance-reference.md).
- **Finance's own data:** a `finance` schema in **PRNTCODE-ops** (`nhimagmpcwlkbfygiowq`), applied 9 Oct 2026 as migrations `20261009103151 finance_schema` and `20261009103332 finance_po_latest_tiebreak` (both in [`supabase/migrations/`](supabase/migrations/)). Tables: `settings`, `forecast_snapshots`, `scenarios`, `po_checks`, `brief_lines`, `pushes`, `reviews`. Row-level security is on, anon and authenticated get nothing, and writes go only through `finance.*` functions. The schema is empty: setup fills it.
- **Wiring:** `ceo` routes money questions to Finance; `what-now` shows the Finance status line and ranks the review and undecided PO verdicts among its picks; `refresh` posts one `sub_agent = finance` time request when something is pending and withdraws it after; the refresh's withdraw sweep and `close-task` leave Finance rows alone.
- **Docs:** Finance charter (live, with its schedule), org table, org chart, README (Usage, the brief-line contract), plugin.json and marketplace.json at **2.3.0**, two self-tests, and [`docs/verification-2026-10-09-finance.md`](docs/verification-2026-10-09-finance.md).

## The scheduled task

Create it yourself on the **claude.ai Scheduled page** (not from a Claude Code session: tasks made inside a session run without connectors). The prntcode-ceo plugin (2.3.0 or later) must be installed and synced, and the task needs **Zoho Books, Shopify, Supabase and Todoist**.

| Field | Value |
|---|---|
| **Name** | `PRNTCODE Finance daily` |
| **When** | Every day, **06:30**, time zone **Abu Dhabi (GMT+4)** |
| **Prompt** | (below, copy exactly) |
| **Notifications** | If the Scheduled page offers a "notify me when it finishes" option for the task, turn it **off**. Finance sends its own push and brief line; everything else must stay silent. |

```
/prntcode-ceo:finance-daily

Run the PRNTCODE Finance daily run exactly as the finance-daily skill says. Run silently: send nothing unless its push rule or its brief-line rule fires, and end with its one status line.
```

The old **PRNTCODE sync** task also ran at 06:30. It's retired: if it's still there, switch it off (README section 3).

## First steps after the plugin syncs

1. In a new chat: `set up Finance`. It asks for your cash floor and upcoming launches, and shows the costs it treats as recurring so you can correct them. Answers are stored only in the `finance` schema.
2. `how's cash?`, then `chart`.
3. Try a scenario: `what if we take a workshop at AED 8k a month?`
4. Create the scheduled task above.

## Found while building (9 Oct 2026)

- **VAT is added at checkout.** Shopify orders have `taxesIncluded = false`, so Shopify's `net_sales` is already ex-VAT. Finance never divides it by 1.05.
- **20 of the 41 Zoho invoices are to "Shopfy"** (Shopify sales posted to Zoho), 7 of them showing overdue. All are left out of B2B sales and collections.
- **No POs yet in Ops**, so stock spend comes from Zoho production and material spend until the first one.
- **Launch history is thin.** Jungle Edit RTW (July 2026) is the one clear launch to size bumps from, so bump ranges are wide. The Jungle Edit Abaya collection's Ops launch date (1 Jan) shows no clear bump, so it's not used as a comparable.
- **The summer factor can't be learned yet:** summer 2026 was the launch month. The forecast says so instead of guessing.
- **Several Zoho bills show as unpaid for months.** Finance takes Zoho as it is and pays them out on their due dates (overdue ones in week 1), with a one-line note. Checking them is the Auditor's job.
- **Phone pushes go through Todoist**, the channel the Coordinator already uses. If the Scheduled runtime has its own push tool, Finance uses that instead.

## Not verified from this session

Installing in claude.ai, creating the scheduled task, and anything that needs your answers (floor, launches) or a real draft PO. See the verification doc for each check.

## Left over from the earlier brief

The earlier (superseded) build created a Notion page **Trackers & Tings → Finance** with five empty databases and a Settings table holding only defaults and Zoho IDs. Nothing uses it any more. Archive or delete it whenever you like (or ask Claude to).
