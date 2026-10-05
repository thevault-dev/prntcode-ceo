---
name: meeting-tasks
description: Turn Fellow meeting notes into tasks in the team Notion tracker ("Get Sh*t done!!!"). Use this skill whenever the user wants to create, log, add, or push tasks/action items from a meeting into Notion — including phrasings like "create tasks from my last meeting", "log the action items from [meeting] into the tracker", "turn my Fellow notes into tasks", "add this meeting's to-dos to Notion", "process the standup into tasks", or any request to get a meeting's commitments into the team tracker. Always use this skill for that workflow — even casual phrasing — because it knows the exact tracker schema, resolves assignees and projects, and ALWAYS confirms a table before writing anything to Notion.
---

# Meeting → Notion Tasks

Convert action items and commitments from a Fellow meeting into tasks in the team Notion tracker. This runs for the **whole PRNTCODE team**, not just the user's own items — but only for PRNTCODE members (external parties are excluded; see step 3). Nothing is written to Notion until the user approves a confirmation table.

## Prerequisites: load tools first

The Fellow and Notion tools are deferred. Before doing anything, load them:
- `tool_search(query="fellow meeting action items summary participants")`
- `tool_search(query="notion fetch create pages search user")`

## Fixed IDs (this tracker)

These never change — don't re-discover them each run:

- **Task data source** (where tasks go): `collection://287e351b-3578-8046-8163-000b2466af6e` — title is "💩 Get Sh*t done!!!"
- **Projects data source** (the "Projects" relation target): `collection://287e351b-3578-80d8-8aca-000b36f7f2a2` — title is "🧑‍🍳 The Game Plan…"

### Task properties (use these exact names)
| Property | Type | Notes |
|---|---|---|
| `Task` | title | The task text. Required. |
| `Assigned to` | person | JSON array of Notion **user IDs**. Resolve names → IDs (see below). |
| `Projects` | relation | JSON array of project **page URLs** in the Projects data source. |
| `date:Task Due Date:start` | date | Expanded date property. Add `date:Task Due Date:is_datetime` = 0 for date-only. |
| `Status` | status | One of: `Not started`, `In progress`, `On hold`, `!!وصلنا` (= done). **Default new tasks to `Not started`.** |
| `Notes` | text | Optional context. |

Leave `Needs Content` and `D-Day!!!` blank on tasks unless the user asks. The relevant deadline field for a task is **Task Due Date**, not D-Day.

### New project properties (when a task needs a project that doesn't exist)
| Property | Type | Notes |
|---|---|---|
| `Projects` | title | The project name. |
| `Project Status` | status | One of: `Not started`, `Up Next`, `Always on...`, `On hold`, `In progress`, `Done`. |
| `date:D-Day!!!:start` | date | The project due date. `date:D-Day!!!:is_datetime` = 0. |
| `icon` | emoji | Set via the page `icon` field on create. |

## Workflow

### 1. Identify the meeting

- If the user names a meeting, a date, or says "last / latest / today's / this morning's", use `search_meetings` to find it. Set `user_has_calendar_event=true` when they refer to their *own* meetings ("my meeting"). Default the date range to the last ~2 months and widen if nothing matches.
- **Always confirm the exact meeting with the user before pulling any material — even when only one meeting matches.** State the meeting title and date and ask them to confirm it's the right one before continuing. Never start the flow on an assumed meeting.
- If more than one plausible meeting matches, **list the top candidates (title + date) and ask which one(s)** before continuing. Don't guess.
- The user may point at several meetings ("this week's calls") — handle each, but keep tasks grouped by meeting in the confirmation table.

### 2. Pull the source material

For the chosen meeting ID(s):
- **Primary:** `get_action_items(meeting_ids=[...])`. With `meeting_ids` set, this returns **all** action items from the meeting (whole team), which is what we want. Each item typically carries the text, an assignee, and sometimes a due date.
- **Secondary:** `get_meeting_summary(meeting_ids=[...])` to catch decisions/commitments that were spoken but never logged as a formal action item. Mark anything derived this way as **inferred** in the table so the user can sanity-check it.
- Only pull the transcript (`get_meeting_transcript`) if the summary/action items are thin or the user asks for thoroughness.
- If helpful for assignee resolution, `get_meeting_participants(meeting_id=...)` gives names + emails.

### 3. Resolve assignees (names → Notion user IDs)

The `Assigned to` property needs Notion user IDs, but Fellow gives names/emails.

**Only log tasks for PRNTCODE team members.** Before resolving anyone, screen the action items: keep only those owned by a member of the PRNTCODE team (e.g. Hessa, Khaled, Harizel, Dee). Drop items whose owner is an external party — clients, suppliers (e.g. Shaijla), production agencies, or any other non-PRNTCODE contact — even if they were captured as action items in the meeting. List the dropped external items briefly so the user can see what was excluded and override if they want one kept.

**Known name → Notion handle mappings** (use these instead of the spoken name when searching):
- **Harizel** → her Notion handle is `smoothoperator`. Search `notion-search(query="smoothoperator", query_type="user")` to resolve her.

For each remaining owner:
- Call `notion-search(query="<name or email>", query_type="user")` to get the user ID. Prefer matching on email when available.
- Cache resolved people within the run so you don't re-search the same name.
- If a name can't be confidently matched to a Notion user, **don't assign it** — flag it in the table as `⚠️ unmatched` and ask the user how to handle it.
- If an action item has **no owner**, flag it as `⚠️ unassigned` and ask who it should go to (default: leave blank rather than auto-assigning).

### 4. Resolve projects

Each task should link to a project where one applies.
- To find an existing project, `notion-search(query="<project name>", data_source_url="collection://287e351b-3578-80d8-8aca-000b36f7f2a2")` and match on title. Use the returned page **URL** for the relation.
- **Duplicate project names:** this tracker often has multiple projects with the **same title** (e.g. two "RTW SHOOT" projects created days apart). If a search returns more than one project matching the name, **never silently pick one.** Flag it in the table (e.g. `RTW SHOOT ⚠️ 2 matches`) and ask the user which to use — list each candidate with its **creation date** (and due date if set) to help them disambiguate. Don't write the task until the user picks.
- If a task clearly belongs to a project that **doesn't exist yet**, propose creating it and ask the user for: **name, due date, status, and emoji** (all four). Collect these before writing.
- If a task has no clear project, mark it `— none —` rather than forcing a link; confirm with the user.

### 5. Screen for stale / past-due tasks

Meeting action items are often tied to an event that may already have passed by the time they're being logged (e.g. a call on the 10th about a shoot on the 15th, processed on the 23rd). Before showing the table:
- Compare each task's due date — and any event date implied in the task text or meeting summary — against **today's date**.
- Mark anything already past as `⏮ past` and anything still upcoming as `✅ live` in a **"Still live?"** column.
- When tasks are past-due, **default to proposing you skip them**, and ask the user whether to add only the live ones, all of them, or none. Don't assume past-due tasks are wanted just because they were in the meeting.

### 6. Confirm BEFORE writing (mandatory)

Present a **table in chat** of everything proposed. Never write to Notion before the user approves. Use this structure:

```
**Tasks to add — from "[Meeting title]" ([date])**

| # | Task | Assigned to | Project | Task Due Date | Notes | Still live? | Source |
|---|------|-------------|---------|---------------|-------|-------------|--------|
| 1 | ...  | Hessa       | Summer Collection | 2026-07-01 | ... | ✅ live | action item |
| 2 | ...  | ⚠️ unassigned | — none — | — | ... | ⏮ past | inferred |
```

If any **new projects** need creating, show a second table:

```
**New projects to create**

| Project | Status | Due date | Emoji |
|---------|--------|----------|-------|
| ...     | Not started | 2026-08-15 | 🎯 |
```

Then ask plainly: *"Want me to add these as-is, or change anything first?"*

- Support edits in natural language and **refresh the table** after each change: reassign a row, change a due date/status/project, edit task text, drop a row, add a row, split one item into two, or merge.
- Resolve every `⚠️` flag (unmatched/unassigned) and confirm any new projects before proceeding.
- Light duplicate check: if a proposed task looks like one already in the tracker, note it so the user can skip it.

### 7. Write to Notion (only after explicit approval)

Order matters:
1. **Create new projects first** with `notion-create-pages` into the Projects data source (`data_source_id: 287e351b-3578-80d8-8aca-000b36f7f2a2`), setting `Projects` (title), `Project Status`, `date:D-Day!!!:start`, and the `icon`. Capture each new page's URL.
2. **Create the tasks** with `notion-create-pages` into the Task data source (`data_source_id: 287e351b-3578-8046-8163-000b2466af6e`). For each task set: `Task`, `Assigned to` (array of user IDs), `Projects` (array containing the project page URL — existing or newly created), `date:Task Due Date:start` (+ `is_datetime: 0`), `Status` (default `Not started`), and `Notes`. You can pass all tasks in one call via the `pages` array.

### 8. Confirm what was created

Report back concisely: how many tasks were added, any projects created, and anything skipped (duplicates, unresolved items). Offer to open the tracker view.

## Example property payloads

A task assigned to one person, linked to an existing project, due July 1:
```json
{
  "Task": "Finalise summer collection pricing tiers",
  "Assigned to": "[\"<hessa-user-id>\"]",
  "Projects": "[\"https://app.notion.com/p/<project-page-id>\"]",
  "date:Task Due Date:start": "2026-07-01",
  "date:Task Due Date:is_datetime": 0,
  "Status": "Not started",
  "Notes": "Agreed Entry/Core/Hero split in the call."
}
```

A new project:
```json
{
  "properties": {
    "Projects": "Autumn Capsule",
    "Project Status": "Not started",
    "date:D-Day!!!:start": "2026-09-30",
    "date:D-Day!!!:is_datetime": 0
  },
  "icon": "🍂"
}
```

## Guardrails

- **Confirm the exact meeting with the user before starting** — even if only one matches. Never run the flow on an assumed meeting.
- **Only log tasks for PRNTCODE team members.** Drop action items owned by external parties (clients, suppliers, agencies) and surface what was dropped.
- **Never write to Notion before the user approves the table.** This is the core promise of the skill.
- Don't invent assignees, due dates, or projects. If the meeting didn't specify something, leave it blank and surface it, rather than filling a plausible-looking value.
- Don't mark anything `!!وصلنا` (done) — new tasks start as `Not started` unless the user says otherwise.
- Keep tasks grouped by their source meeting in the confirmation table so the user can see provenance.
