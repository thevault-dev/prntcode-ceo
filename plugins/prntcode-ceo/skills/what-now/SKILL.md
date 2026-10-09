---
name: what-now
description: PRNTCODE focus-block helper (Chief of Staff), the CEO's opener in a PRNTCODE block. Khaled is in a PRNTCODE focus block, or has some free time, and asks what to work on. It shows one Finance status line, then reads the tracker live and returns the 1–3 picks that best fit the time he has (his tasks, ranked by nearest D-Day and then by whether teammates are waiting on him, with Finance items ranked among them when cash is AMBER or RED, the monthly review is due, or a Finance decision is unanswered), each with its first concrete step and a time estimate. Use it for "what do you need from me now?", "PRNTCODE focus, what's next?", "I have 90 minutes, what should I do?", "I've got an hour for PRNTCODE", "what should I work on?", "next PRNTCODE task", and the follow-ups "done", "done 2", "next", "skip". Read-only on the tracker, except "done", which closes the task through close-task.
---

# What now? (PRNTCODE focus)

Khaled has a block of time for PRNTCODE. Give him the **1–3 picks that best fit it**, each with the **first concrete step**, so he can start straight away. Keep it to one phone screen. Picks are his tracker tasks plus, when they're worth his time, **Finance items** (step 2b).

**Read-only.** You never edit the tracker, the ledger or the Finance page yourself. The one write is "done" on a task, which hands over to the **close-task** skill.

## 0. Load tools
Notion (`notion-query-data-sources`, `notion-fetch`) and Supabase (`execute_sql`). Load them with tool search. If Notion is missing, stop and say which connector to reconnect. If only Supabase is missing, carry on without ledger estimates.

Fixed IDs: the same as the refresh skill. Tasks `collection://287e351b-3578-8046-8163-000b2466af6e`, projects `collection://287e351b-3578-80d8-8aca-000b36f7f2a2`, Khaled `319cf6a3-548f-4fd3-b017-0514c79713b3`, done status `!!وصلنا`, ledger project `hgkreprqxevayruqpibf`. Time is Abu Dhabi (`Asia/Dubai`).

## 1. How much time?

1. **He said it:** "90 minutes", "an hour", "2h", "till 10".
2. **Otherwise, is he in a focus block right now?**
   ```sql
   select title, slot_end, request_ids from public.plan_blocks where kind = 'prntcode' and status = 'booked' and now() between slot_start and slot_end;
   ```
   If he is, the time is what's left of the block. Rank its `request_ids` tasks first (look up their `source_ref` in `public.requests`).
3. **Otherwise** assume 60 minutes and say so in the header: `(60 min assumed — tell me if you have more)`.

## 2. Read the tracker live

Run the refresh skill's queries **1a** (Khaled's open tasks) and **1b** (projects, with `Project Status` and `D-Day!!!`), plus:
```sql
SELECT url, "Task", "Status", "Assigned to", "Projects", "date:Task Due Date:start"
FROM "collection://287e351b-3578-8046-8163-000b2466af6e"
WHERE ("Status" IS NULL OR "Status" != ?) AND "Assigned to" NOT LIKE ?
```
params `["!!وصلنا", "%319cf6a3-548f-4fd3-b017-0514c79713b3%"]`. These are teammates' open tasks, used only to tell whether someone is waiting on him.

And the ledger estimates (optional): `select source_ref, duration_min, context from public.requests where source_agent = 'prntcode' and status in ('new','proposed','scheduled');`

## 2b. Finance status (read-only)

Read `../../org/finance/finance-reference.md`, then gather three things. Each is read-only; if a connector is missing, the status line says which part is unknown (`Cash unknown (Zoho not connected)`), and the rest still runs.

1. **Cash:** the `cash-outlook` skill's status (its step 6, "Called by another skill"): `{status, low_amount, low_week}`.
2. **Monthly review due?** The previous month's review is due from the 1st until the Finance **Monthly reviews** data source (`collection://6a13f42d-f158-4e3b-bf4c-a00e4562c40e`) has a row with `Month` = that month (`YYYY-MM`) and `Status = done`.
3. **Decisions waiting:** decision-log rows (`collection://414e0fe0-528a-4eec-a175-fbad713b915b`) with `Answer = pending`.

**The status line** (always, right under the header, one line):
```
Finance: Cash GREEN · low AED 14,200, week of 16 Nov · 2 decisions waiting · September review due
```
Leave out the parts that are empty (`Finance: Cash GREEN · low AED 14,200, week of 16 Nov`).

**Finance items** (candidates for the picks, only when they apply):

| Item | Estimate | First step |
|---|---|---|
| Cash **RED** or **AMBER** | 20m | `Say "how's cash?" and pick what to move or delay.` |
| `<Month> review` due | 20m | `Open the <Month> review and answer its 3 decisions.` (`<Month> review · 20 min · 3 decisions`) |
| Decisions waiting (n) | 10m (+5m each after the first) | `Answer the open Finance decisions: <first decision title>.` |

## 3. Pick and rank

**Candidates:** the Finance items from 2b, and Khaled's open tasks that need his own focused time (refresh skill 3f: reviewing, deciding, writing, prepping, calls). Leave out recurring chores and pure waiting.

**Estimate:** the ledger's `duration_min` if the task is posted, otherwise your own estimate in 15-minute steps (15–240).

**Rank Finance items among the tasks** by giving each an effective date:
- Cash **RED** → ranks first, above everything.
- Cash **AMBER** → as if due today.
- Monthly review due → due on the 7th of the month (from the 8th it counts as overdue, so it rises to the top).
- Decisions waiting → due 3 days after the oldest one's `Date`.

**Rank:**
1. **Nearest D-Day first** (a Finance item's effective date counts as its D-Day). Use the task due date, or else the earliest linked project's `D-Day!!!`. Overdue tasks on active projects come first, and undated tasks last.
2. **Then: are others blocked on him?** Teammates' open tasks on the same project, due on or after his task, while his task's verb is a decision or input (approve, sign, decide, review, choose, price, brief, send, confirm). Name who: `Hessa waiting`.
3. Then shorter tasks first.

**Fit the time:** walk the ranked list and take tasks whose estimates add up to no more than the time he has, **at most 3**.
- If the top task alone is longer than the time he has, give **only that one**, framed as `start: first 90 min`, with a step that fits.
- If nothing fits a very short slot (under 30 min), give the top task's first step anyway.

## 4. The first concrete step

For each task you return, `notion-fetch` its page (read-only) and read the title, `Notes` and page body. The first step is **one specific action he can start in the next minute**, naming the thing to open, write or decide. For example:
- `Open the Wildflower Abayas costing sheet and set RRP for the 4 styles (target ≥ 2.6× cost).`
- `Reply to Vibey's email: yes or no on 14–15 Nov, and ask for the stall fee.`
- `Draft 3 one-line concepts for the House Launch in the task page, then pick one.`

Never just repeat the task name. If the page gives you nothing to go on, make the step a short decision: `Decide who owns this (you or Hessa) and write it in Notes.`

## 5. Reply

```
PRNTCODE · 90 min
Finance: Cash AMBER · low AED 6,200, week of 16 Nov · September review due
1. September review · 20 min · 3 decisions
   → Open the September review and answer its 3 decisions.
2. Set pricing — Wildflower Abayas · 60m · due Wed · Hessa waiting
   → Open the Abayas costing sheet and set RRP for the 4 styles.
Reply: open 1 · done 2 · next · skip 2
```
(Made-up numbers.)
Keep the ranked list in mind for "next".

## 6. Follow-ups

- **"done" / "done 1" / "1 done"** (or "1 not needed — …"): hand over to the **close-task** skill with
  `close PRNTCODE task <page id as a dashed UUID> as <done|not_needed>: <his words, or "done in focus block"> (via what-now)`.
  It confirms in one line. Then offer the next task: `Next: <task> · <est> → <first step>`. A plain "done" with several tasks shown means task 1.
- **"open 1"** (or "start 1", or just "1") on a **Finance item**: run it. The review → the `monthly-review` skill. Cash → the `cash-outlook` skill ("how's cash?"). Decisions waiting → list the pending decision-log rows, numbered, each with its recommendation, and take his answers as `ask-finance` step 6 does. "done" on a Finance item closes nothing in the tracker; reply `Finance item: nothing to close in the tracker` and offer the next pick.
- **"next"**: show the next task from the ranked list (the one after those shown), in the same format, with its step.
- **"skip" / "skip 2"**: drop that task for this conversation only (nothing is written) and show the next one.
- **"I have 30 more minutes"**: re-fit from the remaining list.

## Rules
1. **Read-only** on Notion, the ledger, the Finance page, Zoho and the Ops App. The only write is close-task's, triggered by Khaled's "done" on a task you showed him. (Finance items, once opened, run under the Finance skills' own rules.)
2. **Only Khaled's tasks.** Teammates' tasks are read only to see who is waiting. Never suggest or close them.
3. At most 3 picks at a time (tasks and Finance items together), every one with a first step and an estimate. The Finance status line doesn't count as a pick.
4. Never touch a calendar.
