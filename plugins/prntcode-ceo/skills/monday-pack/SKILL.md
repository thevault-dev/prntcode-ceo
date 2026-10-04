---
name: monday-pack
description: Generate the PRNTCODE Monday Meeting Pack — a pre-meeting brief built from the Game Plan projects tracker and the Get Sh*t done!!! task tracker that shows what moved, what's stalled, what's overdue, and whether each project is on track for its D-Day. It doesn't just report — it PROPOSES back-planned due dates for undated tasks on near-term projects and flags tasks that appear to be MISSING based on what kind of project it is (event, collection, collab, shoot, pop-up). Use this skill whenever the user says "monday pack", "meeting pack", "prep the monday meeting", "are we on track", "what's falling behind", "project status check", "where are we on the trackers", or asks any question about overall project timelines, deadlines slipping, or readiness across PRNTCODE projects. Also runs as a scheduled task Monday mornings. Nothing is ever written to Notion without an approved proposal table.
---

# PRNTCODE Monday Meeting Pack

Build the brief that runs the Monday meeting: per-project timeline health, week-over-week movement, and a numbered proposal queue of concrete fixes (dates to set, tasks to create, questions to resolve). The pack is read-heavy and write-never — all writes go through numbered proposals the user approves explicitly, matching the meeting-tasks skill convention.

## Prerequisites: load tools first

Notion tools are deferred. Before anything: `tool_search(query="notion fetch query data sources create pages update page search")`.

For the **Your time asks** section, also load Supabase: `tool_search(query="supabase execute sql")`. (Added in the prntcode-ceo plugin.)

## Fixed IDs (never re-discover)

- **Projects data source** ("🧑‍🍳 The Game Plan…"): `collection://287e351b-3578-80d8-8aca-000b36f7f2a2`
  - Properties: `Projects` (title), `Project Status` (Not started / Up Next / Always on... / On hold / In progress / Done), `Needs Content` (Nah/Yeah), `Event` (Nah/Yeah), `date:D-Day!!!:start`
- **Task data source** ("💩 Get Sh*t done!!!"): `collection://287e351b-3578-8046-8163-000b2466af6e`
  - Properties: `Task` (title), `Status` (Not started / In progress / On hold / `!!وصلنا` = done), `Assigned to` (person, JSON array of user IDs), `Projects` (relation, JSON array of project page URLs), `date:Task Due Date:start`, `Notes`, `Needs Content`, `PRNTCODE Event`
- **Pack archive parent page**: search for a page titled "Monday Packs" under Trackers & Tings (parent page `2d7e351b357880368b73e882c7f2c8ae`). If it doesn't exist yet, propose creating it in the proposal queue (one-time).

Team reference: PRNTCODE members include Khaled, Hessa, Harizel (Notion handle `smoothoperator`), Dee. Resolve names → user IDs via `notion-search(query_type="user")`, cache within the run.

## Definitions

- **Done** for tasks means `Status = !!وصلنا`. Everything else is open.
- **Near-term project**: `Project Status` is `In progress` or `Up Next` AND D-Day within **42 days** of today (or already past).
- **Active project**: `Project Status` is `In progress` or `Up Next`. `Always on...` projects are tracked for overdue tasks only — no D-Day logic, no gap detection.
- **Stalled**: an active project with a D-Day whose open tasks have had no status change and no completions since the last pack (see archive diff below).
- **`Needs Content` is NOT a task signal.** It flags that a project needs social coverage, which is handled on a separate Notion page owned by the social team. Never propose content, social, caption, post, or coverage tasks from it, and never flag a missing content task as a gap. Production tasks that happen to be visual (a product shoot, a short film that's part of the deliverable) are fine — the test is whether it's social scheduling/coverage work.
- The hygiene rules apply **narrowly**: date/owner discipline is only demanded on near-term projects. Long-horizon and Always-on work is allowed to stay loose. Never propose dating every task in the tracker.

## Workflow

### 1. Pull the data (one pass)

Query both data sources via `notion-query-data-sources` (SQL mode):
- All projects: title, status, Needs Content, Event, D-Day, url.
- All open tasks (Status != `!!وصلنا`): title, status, due date, assignee, project relation, notes, url, createdTime.
- Duplicate project titles exist (e.g. two "RTW SHOOT" pages). When matching tasks to projects, always match on project **URL**, never on title.

Fetch the most recent page in the Monday Packs archive (if it exists) — it contains last week's per-task status snapshot in a collapsed toggle. Diff against it to compute **moved / stalled / newly completed** per project. If no previous pack exists, skip movement and say so in the pack.

### 1b. Pull your time asks (added in the prntcode-ceo plugin)

This step is read-only. It reports what Khaled's Coordinator did with the time blocks the Chief of Staff's half-week refresh (`/prntcode-ceo:refresh`) asked for. Ledger: Supabase project `hgkreprqxevayruqpibf`, table `public.requests`. "This week" means Monday 00:00 to Sunday 24:00, Abu Dhabi time (`Asia/Dubai`, UTC+4).

```sql
with wk as (
  select (date_trunc('week', now() at time zone 'Asia/Dubai')) at time zone 'Asia/Dubai' as s
)
select r.status, r.title, r.duration_min, r.decision_note,
       to_char(r.slot_start at time zone 'Asia/Dubai', 'Dy DD Mon HH24:MI') as slot_local,
       to_char(r.due_by at time zone 'Asia/Dubai', 'Dy DD Mon') as due_local
from public.requests r, wk
where r.source_agent = 'prntcode'
  and r.status in ('scheduled', 'proposed', 'bumped', 'declined')
  and ( (r.slot_start >= wk.s and r.slot_start < wk.s + interval '7 days')
        or (r.status in ('bumped', 'declined') and r.decided_at >= wk.s - interval '7 days') )
order by array_position(array['scheduled','proposed','bumped','declined'], r.status), r.slot_start nulls last;
```

Bumped and declined rows usually have no slot, so the query includes those decided since the start of last week. That way Monday's pack still shows what happened over the weekend and the week before.

Also count rows still waiting for the Coordinator (`status = 'new'`), for a one-line footnote.

Then compute the tasks the refresh **skipped** from the data already pulled in step 1, using the refresh's rules. Take open tasks with Khaled (`319cf6a3-548f-4fd3-b017-0514c79713b3`) in `Assigned to`:
- **Undated**: no `Task Due Date` and no D-Day on any linked project.
- **Overdue**: due date (the task date, or else the project D-Day; date-only means 23:59 Abu Dhabi) already passed, **and** the task has no `prntcode` row in the ledger. Check with `select source_ref from public.requests where source_agent = 'prntcode'`; source_ref is the page ID as a dashed UUID. Overdue tasks that the sync gave a catch-up block already appear in the groups above (their note starts "Overdue since …"), so don't list them twice.

If the ledger can't be reached, still produce the rest of the pack. Replace this section with one line: "Your time asks: ledger unreachable (check the Supabase connector)."

### 2. Classify each active project

Read `references/archetypes.md` and assign each active project an archetype from its name, `Event` flag, and `Needs Content` flag. The archetype determines (a) the expected task checklist for gap detection and (b) the back-planning offsets for date proposals. If no archetype fits confidently, use the **generic** archetype and mark the classification `~` (soft) in the pack so proposals from it are clearly lower-confidence.

### 3. Score timeline health per near-term project

For each near-term project compute:
- Days to D-Day.
- Open tasks: total, dated, undated, overdue, unassigned.
- Movement since last pack (from the archive diff).
- **Runway check**: compare days-to-D-Day against the archetype's minimum lead time. If D-Day is closer than the latest back-planning offset (e.g. an event 10 days out with no invites task done), flag it 🔴.
- Health flag: 🟢 on track / 🟡 attention (undated tasks, no movement, or gaps) / 🔴 at risk (overdue critical-path tasks, runway breach, or D-Day passed with open tasks).

### 4. Build proposals (the planning brain)

Generate a numbered proposal queue. Three proposal types:

**A. Back-planned dates** — for every undated open task on a near-term project, propose a due date by working back from D-Day using the archetype offsets in `references/archetypes.md`. Match the task title to the closest archetype milestone to pick its offset; if no milestone matches, distribute unmatched tasks evenly across the remaining runway, earliest-first in task creation order. Rules:
- Never propose a date in the past. If the offset lands before today, propose today + clearly mark it `⚠️ compressed`.
- Never propose a date after D-Day.
- **Compressed-majority rule**: if more than half a project's date proposals come out `⚠️ compressed`, the runway is gone and a task list is the wrong output. Lead that project with a single question proposal — "D-Day is in X days but the plan needs Y; move the date or cut scope?" — and hold the individual date proposals behind it. Exception: when the D-Day is externally fixed (a venue's date, a partner's launch), skip the question and state the runway breach plainly as a triage item for the meeting.
- If two tasks obviously sequence (e.g. "print samples" before "shoot samples"), keep the order.

**B. Missing tasks** — compare the project's open+done tasks against the archetype checklist. For each expected workstream with no matching task, propose creating one (with a back-planned date and a suggested assignee only if obvious from who owns sibling tasks — otherwise leave unassigned and flag). Phrase proposed task titles in the tracker's existing voice (short, imperative). Mark each with the archetype that generated it so the user can judge the inference. Gap detection is a **prompt, not an accusation** — some "missing" tasks are handled off-tracker; the user rejecting a proposal is a fine outcome.

**C. Questions** — things only the user can resolve, e.g.: in-progress projects with **no D-Day** ("deadline-driven or should it move to Always on...?"), projects with `Needs Content = Yeah` but zero content tasks, duplicate project titles that need merging, D-Day collisions (two events on the same date), and unassigned tasks on 🔴 projects.

### 5. Present the pack (phone-readable)

**When the refresh runs it on Sunday (refresh step 7e)**, the pack is **its own artifact**: a separate document titled `Monday Pack — Mon 5 Oct`. If the runtime can't make artifacts, it's the Notion archive page from step 7. The chat gets only a one-line link, never the pack itself. Asked directly ("monday pack"), present it in chat as before.

Order: worst first. Structure:

```
**Monday Pack — [date]**

**Headline:** X active projects, Y near-term. Z 🔴 at risk, W 🟡 need attention. [One-sentence biggest risk.]

**🔴 At risk**
[Per project: name — D-Day (days left) — why it's red — movement since last week]

**🟡 Attention**
[Same shape, shorter]

**🟢 On track**
[One line each]

**Overdue tasks** (In progress / Up Next projects only — suppress overdue on `On hold`, `Not started` and `Always on...` projects by default; give a one-line count of what was suppressed and list them only if asked)
| Task | Project | Owner | Was due |

**Your time asks** (what the Coordinator did with this week's PRNTCODE blocks)
✅ Scheduled
• [title] — [slot_local], [duration]m — [decision_note]
🕓 Proposed
• [title] — [slot_local] — [decision_note]
↪️ Bumped
• [title] — [decision_note]
✖️ Declined
• [title] — [decision_note]
[N still waiting for the Coordinator.]
Not posted, needs a date: [task] · [task]
Not posted, overdue: [task] (was due [date]) · …

**Proposals** (nothing happens without your approval)
| # | Type | Project | Proposal |
| 1 | Date | Wildflower | "Confirm print files" → Fri 4 Sep (D-Day −0, ⚠️ compressed) |
| 2 | New task | House Launch Event | Add "Send invites" → 16 Oct (event −15d) |
| 3 | Question | Studio | No D-Day — deadline-driven or Always on? |

Approve like: "1, 2, 4" / "all" / "all except 3" / "none".
```

In **Your time asks**, leave out empty groups and keep each decision_note to one line (cut at ~80 characters). If nothing at all happened this week, write "No PRNTCODE time asks this week."

Keep it tight — this is read on a phone before a meeting. No padding, no restating the tables in prose.

### 6. Execute approved proposals only

- Date proposals → `notion-update-page` on the task, setting `date:Task Due Date:start` (+ `is_datetime: 0`).
- New tasks → `notion-create-pages` into the task data source with `Task`, `Projects` (project page URL array), `date:Task Due Date:start`, `Status: Not started`, and `Notes: "Proposed by Monday Pack — [archetype] gap"` so provenance is visible in the tracker.
- Questions → apply whatever the user answers (set D-Day, change Project Status, etc.) via `notion-update-page`.
- Never mark anything done; never delete or archive anything; never touch projects/tasks not named in an approved proposal.

### 7. Archive the pack

After execution (or after "none"), save the pack as a new subpage of the Monday Packs page titled `Monday Pack — YYYY-MM-DD`. Include the rendered pack, and at the bottom a toggle block titled "Snapshot (for next week's diff)" containing a plain list of every open task as `project-url | task-url | task title | status | due date`. This snapshot is what next week's run diffs against — keep the format stable.

## Guardrails

- **Never write to Notion outside an approved, numbered proposal.** The pack itself is read-only.
- Proposals are suggestions from name-based inference — present them with appropriate confidence, never as facts. A rejected proposal should not be re-proposed the following week unless something changed; check the previous pack's archive for rejected items (record them in the archive under a "Declined" note).
- Don't demand dates on Always-on or far-horizon projects. Narrow hygiene is the whole design.
- Don't invent assignees. Suggest one only when sibling tasks make it obvious; otherwise leave blank.
- Match tasks to projects by URL, never title (duplicates exist).
- If the trackers are unreachable or a query fails, say so plainly and stop — never fabricate a pack.
