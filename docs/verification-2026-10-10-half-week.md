# Verification: half-week routine, PRNTCODE feeders (10 Oct 2026)

prntcode-ceo's part of the build: `refresh` collect mode and `monday-pack` as its own Sunday feeder (**2.4.0**). The checks are the brief's full list, shared with the coordinator and personal-agent repos; the ones this repo owns are **7, 8, 9** and its half of **2, 3, 18, 20**.

Build of `BUILD BRIEF: Half-week routine (collect + plan)` (10 Oct 2026): coordinator **2.3.0**, prntcode-ceo **2.4.0**, personal-agent **1.1.0**.

**This repo is public.** Every example here is made up. No names, birthdays, places, pantry contents or amounts.

Legend: ✅ pass · ⏳ built, not yet run live (and what to check) · ❌ fail

## How it was checked

- **Live ledger** (Supabase `hgkreprqxevayruqpibf`): migration `20261010182849_half_week_feeders` applied. Self-test checks **17–24** (`supabase/tests/definition_of_done.sql`) were run on the live ledger inside a block that raises at the end, so everything rolled back: result `V23 CHECKS 17-24 PASSED (rolled back on purpose)`. Afterwards: 0 `prep_runs`, 0 `prep_outputs`, 0 test requests, 0 test blocks, `selftest` still paused.
- **Scratch ledger:** every migration in `supabase/migrations/` replayed on a local Postgres 16, then the whole self-test 1–24: `ALL LEDGER CHECKS PASSED`.
- **Artifact:** `half-week.html` rendered in Chromium at 390 px with made-up picks: no console errors, no horizontal scroll, picks numbered with day, time, place, booking and why. The live "Khaled's half-week" page was republished in place (version 3) with the same plan data and capability.
- **Live reads (read-only):** the Birthdays calendar is readable by its registry ID (owner access); its upcoming events are yearly all-day events in the expected title format.
- **Plugins:** `claude plugin validate` passes for the marketplace and plugin in all three repos.
- Anything that needs a real Sunday or Wednesday in claude.ai (scheduled tasks, Notion, Todoist, web search, the planning chat) is ⏳: the branches must be merged to `main` and the plugins synced first.

## Definition of Done

| # | Check | Result | How / what's left |
|---|---|---|---|
| 1 | Switching a test feeder row paused → live makes it run in the next collect with no code change; pausing it removes it from the board | ✅ ledger · ⏳ live collect | Check 17: `feeder_set_status('selftest','live')` puts it in `prep_due_feeders('sun')`, which is the only list `collect` runs. Check 21: paused → gone from `prep_board`. Live: say "switch the test feeder on", run collect, see `Self-test ✓ ran fine`, switch it off. |
| 2 | A collect run sends no notification and writes nothing to Todoist, Notion or any calendar | ✅ design · ⏳ live | `collect` hard rules 1–2; every feeder's collect mode writes only the ledger (refresh skips 7e and 8; Monday Pack never takes the Notion fallback; meals reads only; milestones/scout/birthdays write only `requests`/`prep_record`). The task's notifications are off. Live: Sun 11 Oct 20:00, nothing on the phone, nothing new in Todoist/Notion/calendars. |
| 3 | Running collect twice in the same half-week leaves the same outputs and ledger rows, no duplicates | ✅ ledger · ⏳ live | Check 18: the same `prep_record` twice → 1 run row (attempts 2), same 3 outputs. Check 20: a re-run keeps an added pick and doesn't duplicate its ref. Time asks use the guarded upsert (writes nothing when unchanged), check 23 for personal. |
| 4 | A feeder forced to fail is recorded as failed, the feeders after it still run, the 21:00 board shows ⚠ with the reason | ✅ ledger · ⏳ live | Check 19: failed needs a reason; the board shows `failed` + reason; the next feeder records `ok`. `feeder-selftest` with `{"mode":"fail"}` fails on purpose; `collect` step 3 never stops on a failure and records one for a feeder that didn't. Plan step 3 renders `<label> ⚠ <reason>`. |
| 5 | With no collect run for the half-week, the plan says so, and "run collect" fills the board in the chat | ✅ design · ⏳ live | `prep_board` returns null run status for every feeder; plan step 3 shows `Collect didn't run for Mon–Wed · … say "run collect"`; section B runs `coordinator:collect` in the chat and re-shows the board. |
| 6 | Sunday 21:00 opening is one message: the board, then the commitments question; ≤ 8 board lines, ≤ 2 extra questions | ✅ design · ⏳ live | Plan step 3: one message, 8-line cap with `+N more · say "board"`, at most 2 feeder questions in run order. |
| 7 | "refresh PRNTCODE" typed by hand still gives the full message and hands over to planning, as in 2.3.0 | ✅ diff · ⏳ live | prntcode-ceo diff: steps 0–8 untouched; only a "Collect mode" section, a hard-rule exception and the description were added. Collect mode applies only with the `collect prntcode_refresh <date>` argument. |
| 8 | The refresh run by collect writes the same ledger rows as a manual refresh | ✅ by construction · ⏳ live | Collect mode runs steps 0–6b "exactly as written" with the same upsert, `agent_withdraw` and Finance row; the only extra write is its own `prep_record`. Live: after Sunday's collect, a manual refresh should write 0 rows (its hard rule 8). |
| 9 | The Monday Pack is linked on the board on Sundays only | ✅ ledger | Registry row `monday_pack` has `days = {sun}`; check 21: not on a Thursday board. |
| 10 | A Tuesday dinner commitment leaves only Wednesday's dinner in the meal plan | ✅ design · ⏳ live | Plan step 4.3b passes `nights=Wed` when Tuesday's dinner is a commitment; meal plan "Plan mode" builds only those nights. |
| 11 | "book it" writes the groceries and the Notion page; "skip meals" writes neither | ✅ design · ⏳ live | Plan step 6.5c hands `apply <HW> M3` to the meal plan's Apply mode (6a + 6b, idempotent Notion check); `skip meals` → approval `declined`, and Apply mode writes nothing for a declined approval. |
| 12 | A milestone task appears in the ledger as `source_agent = personal` and gets placed; a re-run posts nothing new | ✅ ledger · ⏳ live | Check 23: a `personal`/`milestones` row upserts once and withdraws via `agent_withdraw`. Milestones collect mode uses the refresh's guarded upsert (cap 5). The plan places personal non-fixed requests as before. Live: needs an open Personal Task due this half-week. |
| 13 | The Wednesday board shows up to 5 weekend picks W1–W5 from editorial sources, each with day, time, place, why and booking | ✅ ledger + skill · ⏳ live (Wed 14 Oct) | Check 20: 6 picks refused, wrong letter refused, title + day required. `weekend-scout` requires every field, editorial sources only, times confirmed on the venue's page. The plan shows them in the artifact (`board` stage) before you answer. |
| 14 | "add W2" places that pick as a fixed block with travel around it | ✅ design · ⏳ live | Plan step 3: pick → fixed commitment at its place, through the place check (3b) and travel; marked `added`. |
| 15 | A test birthday 14 days out appears on the board, and one 30 days out doesn't | ✅ design + live read · ⏳ board | `birthdays` shows `1 ≤ days ≤ 21` not shown before, plus the half-week it lands; reads only 21 days ahead. Live read: the calendar returns this month's birthdays in the expected format; for Sun 11 Oct the ones 11–17 days out qualify and nothing past 21 days is read. |
| 16 | "book it" sets a Todoist reminder on the birthday itself | ✅ design · ⏳ live | `birthdays` leaves a `reminder` due 09:00 on the day for birthdays in the half-week; plan step 6.5d sets it in Personal Tasks, with a duplicate check. |
| 17 | Neither plan books anything over Sunday or Wednesday 21:00–21:45 | ✅ ledger | Check 22 (live): a dinner over Wed 21:00 is refused by the `plan_blocks` trigger; the held "Plan the half-week" block and a fixed commitment are allowed. The plan always drafts the held block (step 4.2). |
| 18 | A search of every committed file in the two public repos finds no real names, birthdays, places or amounts | ❌ (pre-existing files) · ✅ this build | This build's new and changed lines were searched for the names seen in the live reads, venues, pantry items and amounts: no hits. In the coordinator, three personal examples in skills/README/old reports were replaced with made-up ones. **Still present, from earlier builds:** coordinator: a personal email address used as the personal calendar ID (`plan`, `coordinator` skills, two old build reports), one neighbourhood in an applied migration's comments, the Dubai home's community name in intake's parsing table. prntcode-ceo: teammates' first names, Notion user names and project names in the refresh, Monday Pack and what-now skills and README; real prices and competitors in the pricing references; finance and verification docs. Git history also keeps everything. Needs Khaled's call (build report, open question 1). |
| 19 | The build report gives both scheduled tasks (name, time, prompt) and names the three tasks to switch off | ✅ | `BUILD_REPORT_V2_3.md`. |
| 20 | Versions are bumped in all three repos | ✅ | coordinator 2.2.0 → 2.3.0, prntcode-ceo 2.3.0 → 2.4.0, personal-agent 1.0.1 → 1.1.0 (plugin.json and marketplace.json). |
| 21 | Each repo has a verification doc in `docs/` recording every check | ✅ | This file; `coordinator/docs/verification-2026-10-10.md`; `personal-agent/docs/verification-2026-10-10.md`. |

## First live run: what to look at

- **Sun 11 Oct 20:00** (collect): no notification. Then `select feeder_key, status, reason from public.prep_runs where half_week_start = '2026-10-12';` should list 5 rows.
- **Sun 11 Oct 21:00** (plan): one message like the README example; the Wednesday 21:00 planning block in "Already on"; the protein question.
- **Wed 14 Oct**: the weekend picks in the artifact, `add W2`, and the Sunday 18 Oct planning block.
