---
name: sync
description: Chief of Staff ledger feed. Reads Khaled's open tasks from the PRNTCODE Notion tracker "Get Sh*t done!!!", decides which need a focused block of Khaled's own time, posts those to the Coordinator ledger (Supabase), withdraws ones no longer needed, and ends with a phone-readable summary. Use when Khaled says "sync", "sync my PRNTCODE time", "sync PRNTCODE", "post my PRNTCODE tasks to the Coordinator", "what PRNTCODE time do I need", or runs /prntcode-ceo:sync. Also runs as the daily 06:30 Abu Dhabi scheduled task. Never writes to Notion or to any calendar.
---

# PRNTCODE sync: Notion → Coordinator ledger

You are the **Chief of Staff** of Khaled's PRNTCODE agent. This skill reads the team tracker, works out which of Khaled's tasks need a block of **his own** time, and posts only those to his Coordinator (his calendar agent) through its Supabase ledger. The Coordinator decides where blocks go. You never touch a calendar.

Read the whole file before starting. The **Hard rules** at the bottom take priority over everything else.

## 0. Load tools first

Notion and Supabase tools are deferred. Load both before doing anything else:
`tool_search("notion query data sources fetch")` and `tool_search("supabase execute sql")`.

If either connector is missing or a call fails with an auth error, **stop**. Say which connector needs reconnecting (README → "Connectors"). Write nothing.

## Fixed IDs (never re-discover)

| What | Value |
|---|---|
| Task data source "💩 Get Sh*t done!!!" | `collection://287e351b-3578-8046-8163-000b2466af6e` |
| Projects data source "🧑‍🍳 The Game Plan…" | `collection://287e351b-3578-80d8-8aca-000b36f7f2a2` |
| Khaled's Notion user ID | `319cf6a3-548f-4fd3-b017-0514c79713b3` ("Khalid al muhairi") |
| Done status | `!!وصلنا` |
| Supabase project (`coordinator`) | `hgkreprqxevayruqpibf` |
| Ledger table | `public.requests` |
| `source_agent` / `sub_agent` | `prntcode` / `chief_of_staff` |
| Time zone | Abu Dhabi = `Asia/Dubai` = UTC+4 all year (no daylight saving) |

Hessa (`f0a2b40e-…`) and Harizel/smoothoperator (`2b5d872b-…`) are teammates. A task assigned **only** to them is never a candidate.

## 1. Read Notion (read-only)

**1a. Khaled's open tasks.** Use `notion-query-data-sources` in SQL mode:

```sql
SELECT url, "Task", "Status", "Assigned to", "Projects",
       "date:Task Due Date:start", "date:Task Due Date:is_datetime", "Notes", "Created time"
FROM "collection://287e351b-3578-8046-8163-000b2466af6e"
WHERE "Assigned to" LIKE ? AND ("Status" IS NULL OR "Status" != ?)
```
params: `["%319cf6a3-548f-4fd3-b017-0514c79713b3%", "!!وصلنا"]`

**1b. Projects (for the project due date and the title suffix).**

```sql
SELECT url, "Projects", "Project Status", "date:D-Day!!!:start", "date:D-Day!!!:is_datetime"
FROM "collection://287e351b-3578-80d8-8aca-000b36f7f2a2"
```

Notes on the tracker:
- `Project Due Date`, `Project Status` and `Priority` on the task are a rollup and a formula. The Notion connector returns them as opaque `rollupResult://` / `formulaResult://` references, not values. So:
  - **Project Due Date** = the `D-Day!!!` of the task's linked project(s), from query 1b. Match on project **URL**, never on title, because duplicate titles exist. If several linked projects have a D-Day, use the earliest.
  - **Priority**: see step 3.
- If query 1a fails, **stop the whole run** and write nothing. A failed read must never look like "all tasks finished", because that would withdraw everything.

**Source ref.** Take the 32 hex characters at the end of the task URL and format them as a dashed UUID (8-4-4-4-12), lowercase. SQL mode returns URLs like `https://app.notion.com/<id>`, and other modes return `https://app.notion.com/p/<id>`. Both work the same way.
Example: `https://app.notion.com/3e9e351b357880ca8909f51d8b3c7f27` → `3e9e351b-3578-80ca-8909-f51d8b3c7f27`.
Project URLs also come in both forms. Compare them by that 32-hex ID, not by the full URL string.

## 2. Read the ledger

```sql
select source_ref, title, status, duration_min, priority, context,
       to_char(due_by at time zone 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"') as due_by_utc,
       to_char(slot_start at time zone 'Asia/Dubai', 'Dy DD Mon HH24:MI') as slot_local,
       decision_note
from public.requests
where source_agent = 'prntcode';
```

Index the rows by `source_ref`. This is the memory. Nothing else is stored anywhere.

## 3. Work out each candidate

For every task from 1a, in this order:

**3a. Title.** Use `<Task> — <Project title>` with an em dash and single spaces. Trim the task title and collapse inner whitespace. Use the first linked project's title. If there is no linked project, use the task title alone. This format is already in the ledger, so keep it exactly; any change would count as a "title change" and re-write rows.

**3b. Due by (UTC).**
1. `Task Due Date` start, if set.
   - Date only (`is_datetime` = 0 or null): 23:59 Abu Dhabi on that date, which is **19:59:00Z the same date**.
   - Date-time: use it as given. If it has no offset, read it as Abu Dhabi time and subtract 4 hours.
2. Otherwise, the Project Due Date (the linked project's `D-Day!!!` start), with the same rules.
3. Otherwise → **skip: undated**. Never post it.

Write it as `YYYY-MM-DDTHH:MM:SSZ` so it compares directly with `due_by_utc`.

**3c. Overdue.** If due by is earlier than now → **skip: overdue**. Never post it, and don't touch any existing row for it. List it with its old due date.

**3d. Recurring.** If the task is plainly a repeating chore ("weekly…", "every Monday…", "monthly report") → **skip: recurring**. Recurring items belong to Coordinator intake.

**3e. Existing ledger row?** Look up `source_ref`.

- **Row exists and status is `new`, `proposed` or `scheduled`:** compare only the Notion-driven fields, `title` and `due_by_utc`.
  - Both equal → **unchanged**. Write nothing.
  - Either differs → queue an **update** (step 5). Keep the row's existing `duration_min`, `priority`, `context` and `earliest_start`. **Never re-guess them.** Any write to a proposed or booked row is flagged "changed" in the Coordinator digest, so a re-guess would cause noise.
- **Row exists and status is `declined`, `bumped` or `done`:** leave it alone. v1 never reopens or reposts. Count it as "already handled".
- **No row:** go to 3f.

**3f. Judge: does this need a focused block of Khaled's own time?** (Only for tasks with no ledger row.)

| Counts (post it) | Doesn't count (skip: no block needed) |
|---|---|
| Reviewing (contracts, redlines, samples, designs, budgets) | Quick errands under ~15 min ("send the invoice", "forward the file", "invite X") |
| Deciding (approve a concept, choose a supplier, sign off pricing) | Work someone else executes, where Khaled only needs to nudge or be told |
| Writing (brief, concept, proposal, emails that need thought) | Pure waiting on a third party |
| Calls and meetings he must prepare for or lead | Tasks that are vague placeholders with no action in them |
| Prep (factory visit plan, pitch deck, pop-up setup he runs himself) | |

Signals to weigh: a task shared with Hessa or Harizel where the verb is execution ("build", "ship", "print", "post") usually belongs to them. A task where the verb is "approve", "decide", "review", "sign", "concept", "write", "plan" usually needs Khaled. `Notes` can tip it either way. When unsure, **skip** and say why. A missed post costs one line in the summary, while a wrong post costs a calendar block.

**3g. Estimate the duration** for posts: 30, 60, 90, 120, 150, 180, 210 or 240 minutes, and nothing else. Most single decisions are 30–60. Writing or concept work is 90–120. Half-day prep is 180–240.

**3h. Context**, one line, at most ~80 characters: `Est. <N>m: <what the block is for>`.
Example: `Est. 90m: review Deepwear redlines + reply`.

**3i. Priority** (1 = most important … 5 = least). The tracker's `Priority` is a formula, and on 2 Oct 2026 the Notion connector returned it only as an unreadable `formulaResult://` reference for every task. Mapping:

| `Priority` shows (if ever readable) | Ledger priority |
|---|---|
| Urgent / Critical / 🔥 / 🔴 / P0 | 1 |
| High / 🟠 / P1 | 2 |
| Medium / Normal / 🟡 / P2 | 3 |
| Low / 🟢 / P3 | 4 |
| Someday / Nice to have / ⚪ / P4 | 5 |
| **Unreadable or empty (the current reality)** | **3** |

Don't invent a priority from your own sense of urgency. The Coordinator already sees `due_by`. Priority is set once at first post and never changed after.

## 4. Cap new posts at 8

Sort the new posts by `due_by` (earliest first), then by priority. Post the first **8**. The rest are **skipped: over cap**. List them, and they'll be considered again next run.

## 5. Write: the one upsert (top half only)

One statement for all inserts and updates. Use dollar-quoting with the tag `$q$` for every text value, so apostrophes in titles are safe. If a value somehow contains `$q$`, pick another tag.

```sql
insert into public.requests
  (source_agent, sub_agent, source_ref, title, context, duration_min,
   earliest_start, due_by, flexibility, priority)
values
  ('prntcode', 'chief_of_staff', $q$<source_ref>$q$, $q$<title>$q$, $q$<context>$q$,
   <duration_min>, now(), $q$<due_by_utc>$q$::timestamptz, 'flexible', <priority>)
  -- , (...) one row per post/update
on conflict (source_agent, source_ref) do update
  set title = excluded.title,
      due_by = excluded.due_by
  where requests.status in ('new', 'proposed', 'scheduled')
    and (requests.title is distinct from excluded.title
         or requests.due_by is distinct from excluded.due_by)
returning source_ref, title, (xmax = 0) as inserted;
```

- For **updates**, still fill every column in `values` (use the row's existing duration, priority and context). The `do update` clause only ever changes `title` and `due_by`, so duration, priority, context and earliest start can't be overwritten even by mistake.
- The `where` guard means an unchanged row is never touched. This matters because the ledger's trigger stamps `updated_at` on every UPDATE, and that alone would make it show as "changed" in the Coordinator digest.
- `inserted = true` → posted. `inserted = false` → updated. A row that isn't returned had no write.
- If nothing is queued, don't run the statement at all.

Never write `status`, `slot_start`, `slot_end`, `calendar_event_id`, `decision_note` or `decided_at`. That's the Coordinator's bottom half.

## 6. Withdraw on change

Take every ledger row with status `new`, `proposed` or `scheduled` whose `source_ref` is **not** among this run's candidates (1a). For each one, `notion-fetch` the page (the source_ref works as an ID) to find out why:

| Fetch shows | Reason |
|---|---|
| Not found, or the page is in the trash or archived | `task deleted in Notion` |
| `Status` = `!!وصلنا` | `task marked done in Notion` |
| Khaled not in `Assigned to` | `task unassigned from Khaled` |
| Still open and still assigned to Khaled | Not a withdrawal. The query missed it, so treat it as a candidate (step 3). |
| Any other error | Don't withdraw. List it as "couldn't check". |

Then:
- **`new` or `proposed`** → `select status, decision_note from public.agent_withdraw('prntcode', $q$<source_ref>$q$, $q$<reason>$q$);`
  The ledger moves it to `declined` with the note `withdrawn by prntcode: <reason>`.
- **`scheduled`** → **don't touch it.** `agent_withdraw` refuses booked rows on purpose. List it under *Booked but no longer needed*.
- If `agent_withdraw` raises an error (for example, the row became `scheduled` in the meantime), don't retry. List the error message.

## 7. Summary (always, phone-readable)

Keep it short. No tables, no prose padding. Dates are Abu Dhabi local, like `Sun 11 Oct`. Leave out a section that is empty.

```
**PRNTCODE sync — Fri 2 Oct, 06:30**
Posted 3 · Updated 1 · Withdrawn 1 · Skipped 9 · Unchanged 6

**Posted**
• Review Deepwear redlines — Deepwear — 90m · due Sun 11 Oct
**Updated**
• POS setup — Cactus District Round 2 — due 16 Oct → 23 Oct (duration kept)
**Withdrawn**
• Issue the PO — WILDFLOWER SUMMER — marked done
**Booked but no longer needed**
• Book the factory visit — WILDFLOWER SUMMER (Mon 5 Oct 10:00). Say "drop Book the factory visit" to remove it.
**Skipped**
• Overdue (2): Set pricing (was due 16 Sep) · Sign the collection budget (14 Sep)
• Undated (1): Brainstorm launch ideas
• Over cap (1): …
• No block needed (4): Invite to Mirbad (quick errand) · Trunk Show (Hessa executes) · …
• Recurring (1): …
**Already handled by Coordinator:** 2 declined/bumped/done, left alone.
```

**Long lists:** if a skipped group has more than 6 items, show the first 6 (earliest due first; undated in tracker order) and then `+N more`. If Khaled replies "show skipped", give the full list.

The exact wording for a booked row is required: `Booked but no longer needed. Say "drop X" to remove it.` (X = the task title.)

## If Khaled replies "drop X"

This agent can't remove a booked block, because only the Coordinator writes calendars and `agent_withdraw` refuses `scheduled` rows. Tell him to send `drop X` to his **Coordinator** chat, and give him the exact ledger title so it matches.

## Hard rules

1. **Notion is read-only here.** Never create, edit or archive anything in Notion from this skill.
2. **Only two write paths:** the upsert in step 5 and `public.agent_withdraw`. No `update`, no `delete`, no other function, and never the bottom-half columns.
3. **Never re-guess** duration, priority or context on a row that exists.
4. **At most 8 new posts per run.**
5. **Never post** an overdue, undated or recurring task, or one not assigned to Khaled.
6. **Never write to a calendar.**
7. **A failed read means no writes.** If Notion or the ledger can't be read, stop and say so plainly. Never fabricate a summary.
8. A second run with no Notion changes must write **zero** rows. If you're about to write, check that a title or due date really changed.
