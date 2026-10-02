# BUILD REPORT: PRNTCODE CEO Agent — v1.1
Date: 2 Oct 2026 · Responds to: BUILD BRIEF v1 (30 Sep 2026) · Status: **Built and pushed. Coordinator repo part still open.**

## Where it is
- Repo: `thevault-dev/prntcode-ceo`, branch `claude/new-session-78ory5`, plugin version **1.1.0**.
- Shape: a plugin marketplace with one plugin, `prntcode-ceo`, containing three skills:
  - `ceo`: the router
  - `sync`: the Chief of Staff ledger feed
  - `monday-pack`: the Monday Pack
- Both manifests pass `claude plugin validate`. A local install found all three skills.

## Must-haves

| # | Feature | Status | Notes |
|---|---|---|---|
| 1 | Org skeleton | ✅ | The CEO is a thin router. The Chief of Staff is live. The other 7 roles each have a folder with a charter README. The README opens with a branded SVG org chart of all 9 roles, plus a Mermaid diagram of the feedback loop. |
| 2 | Ledger feed (`/prntcode-ceo:sync`) | ✅ | It reads the tracker, judges whether a task needs Khaled's time, estimates 30–240 minutes, writes only the top half of the ledger, never re-guesses, posts at most 8 new items per run, and ends with a phone summary. |
| 3 | Withdraw on change | ✅ | Done, deleted or unassigned tasks are withdrawn with `agent_withdraw`. Booked rows are left alone and listed with "Booked but no longer needed. Say 'drop X' to remove it." |
| 4 | Coordinator migration | ⚠️ Half | The function is **already live** in the ledger (migration `20260930191251 agent_withdraw`) and tested. The **coordinator repo** couldn't be opened from this session, so its README, version bump and DoD test weren't checked. The handoff, with the exact function code and test lines, is in `docs/coordinator-handoff.md`. |
| 5 | Monday Pack moves in | ✅ | Copied unchanged, plus one section, **Your time asks** (scheduled, proposed, bumped and declined, each with the Coordinator's note), followed by the undated and overdue tasks. |

## Definition of Done

| Item | Status |
|---|---|
| Repo exists; installs from Customize → Plugins → Add marketplace; `/prntcode-ceo:sync` appears | ⏳ Repo exists and validates. **Not yet tried in claude.ai.** |
| README opens with an org chart of all 9 roles; each stub department has a charter | ✅ |
| Live sync posts only Khaled's tasks with the right fields and a one-line estimate | ✅ Practice run (read-only) and the 6 existing rows conform. No real sync has been run from the plugin yet. |
| Second run writes zero rows; `coordinator_changed_since_decision` stays empty | ✅ Proven on the live ledger in a test that rolled itself back. |
| Due-date change updates only `due_by`; duration unchanged | ✅ Same test. |
| Done task: new/proposed → declined "withdrawn by prntcode"; scheduled left alone and listed | ✅ |
| Overdue and undated never posted with their past date; listed; max 8 new | ✅ Changed in v1.1, see decision 1. |
| `agent_withdraw` migrated, refuses scheduled; coordinator self-test prints `ALL LEDGER CHECKS PASSED` | ⚠️ Live and refuses scheduled ✅. The coordinator repo's self-test wasn't run (no access). This repo's own check prints `ALL PRNTCODE CONTRACT CHECKS PASSED`. |
| Monday Pack runs from the plugin with original sections plus "Your time asks" | ✅ Built; the time-asks query was tested on live data. |
| README has click-by-click steps for install, connectors and the 06:30 task; all files pushed | ✅ |

## Decisions made during the build

1. **Overdue tasks get a catch-up block instead of being ignored.** Agreed with Khaled during the build.
   - The brief said overdue tasks were never posted.
   - Now, a task overdue by **21 days or less**, on a project that's **In progress** or **Always on…**, gets **one** catch-up block: due in 3 days (or the project's D-Day if sooner), priority 2, note "Overdue since …".
   - The catch-up deadline is never pushed again. Older or inactive overdue tasks are still only listed.
   - Window: 21 days, not the 14 first suggested, so that "Set pricing" (D-Day 7 Oct) and "Sign the collection budget" qualify.
2. **Priority is always 3 for now.** The Notion connector returns the `Priority` formula as an unreadable reference, so its real values couldn't be inspected. A mapping is documented for when it becomes readable. Catch-ups get 2.
3. **Project Due Date comes from the project's D-Day.** The tracker's rollup isn't readable through the connector either, so the sync reads the linked project's `D-Day!!!` directly (earliest, if several).
4. **Title format is `<Task> — <Project>`.** An earlier run on 30 Sep already posted 6 rows in this format. Keeping it means the first sync from the plugin changes nothing.
5. **"drop X" goes to the Coordinator.** This agent can't remove booked blocks (`agent_withdraw` refuses them, and calendars are out of scope), so the reply tells Khaled to say it in his Coordinator chat.
6. **Tasks with no linked project don't get catch-ups.** There's no project status to check whether the task is still live.

## Found in the live systems
- **Ledger:** 6 `prntcode` rows already exist, all `proposed`, posted 30 Sep. Each one matches today's Notion title and due date.
- **Database rule:** the ledger requires `due_by > earliest_start`, so a past deadline is refused. But the refusal fails the whole write, so the sync filters past dates out before writing.
- **Practice run today** (read-only, 63 open tasks for Khaled): 6 unchanged, 0 to withdraw, up to 4 catch-ups (Sign the collection budget, Set pricing, Hire the design freelancer, Calculate for the price), about 17 overdue listed only, about 35 undated.
- **Tracker hygiene:** about 35 of Khaled's open tasks have no date and sit on projects with no D-Day. Several open tasks are on projects marked **Done**. Neither can ever be posted until someone cleans it up.

## Khaled's next steps (README sections 1–3)
1. Make the branch available to claude.ai: merge `claude/new-session-78ory5` into `main`, or confirm it's the repo's default branch.
2. Customize → Plugins → Add marketplace → `thevault-dev/prntcode-ceo` → turn Sync automatically on → Install.
3. Turn **off** the old standalone `monday-pack` skill.
4. Check that the Notion and Supabase connectors are connected and switched on.
5. Cowork → Scheduled → New task: `/prntcode-ceo:sync`, daily at 06:30 Abu Dhabi time. Point the existing Monday task at `/prntcode-ceo:monday-pack`.
6. Run `sync my PRNTCODE time` once by hand and check the summary.
7. Coordinator repo: whoever has access applies `docs/coordinator-handoff.md` (README, version bump, DoD block) and runs its self-test.

## Open questions for the next brief
- **Undated pile:** should the Monday Pack propose dates for Khaled's undated and older overdue tasks (writing to Notion only after approval), so they can reach the Coordinator? This was offered as "option 2" and not taken in v1.1.
- **Priority:** what does the `Priority` formula actually show? Once known, the mapping can be pinned or replaced.
- **Catch-up limits:** are 21 days and a 3-day deadline right after a week of real use?
- **Stale tasks:** should open tasks on Done projects be flagged for closing in the Monday Pack?
