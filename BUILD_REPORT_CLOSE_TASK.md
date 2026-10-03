# Build report: PRNTCODE close task from the digest (v1.2.0)

**Status:** Built and tested live on test tasks. The ledger migration is applied and the security advisor is clean. The work is pushed to `claude/nifty-allen-3vp5ph` in both repos. Merging to `main` is what syncs it to claude.ai, and that hasn't happened yet.

## Where it lives
- `prntcode-ceo`: new `skills/close-task/SKILL.md`. `sync` gains step 6a (safety net), step 6 skips rows with `resolution` set, and the CEO router knows about close-task. The README has the handoff contract. Version 1.1.0 → **1.2.0**.
- `coordinator`: migration `20261003081504_close_task_resolution.sql` (live). Also `20260930191251_agent_withdraw.sql`, which was missing from the repo and now matches the live version. README section, definition-of-done checks 7–9, and plugin 1.4.0 → **1.4.1**.

## How it's used
Khaled replies to the digest. The Coordinator sets `resolution` and then sends one line per item. **The handoff contract:**
```
close PRNTCODE task <source_ref> as <done|not_needed>: <reason>
```
- `source_ref` is the ledger `source_ref` (Notion page UUID). The row `id` is also accepted.
- `done_elsewhere` → `done`; `not_needed` → `not_needed`.
- The reason is Khaled's words, or `no reason given`.
- The skill can also be invoked directly as `prntcode-ceo:close-task` with the same line.

Replies are one line each: `Closed in tracker: <task> — <done|not needed> (<reason>)`, `Already closed in tracker: … Nothing changed.`, or `Not closed: <why>`.

## DoD results
| Check | Result |
|---|---|
| `not_needed` sets the right status, adds the comment and replies in one line | ✅ Test task A → `!!وصلنا` (no Cancelled option exists), comment added, stamped |
| A second run changes nothing | ✅ A's `page_last_edited_at` stayed at 08:17:30.701Z, and the existing ledger stamp was left as it was |
| A `source_ref` outside the tracker is refused | ✅ A ledger row pointing at a Game Plan project page was refused, and that page is unedited since 7 Jan |
| No other page modified | ✅ 5 neighbouring tasks have identical `page_last_edited_at` before and after (2 Oct 17:13, 3 Oct 07:39, 30 Sep 15:39/18:42/18:42) |
| Safety net | ✅ Step 6a found exactly B and the decoy D. It closed and stamped B, refused D, and left A alone |
| Reverse direction | ✅ Already worked with no change: C closed in Notion → `withdrawn by prntcode: task marked done in Notion` |
| Handoff works from a plain claude.ai chat | ⏳ Not testable from this session. Needs the merge to main, then one chat test |
| Both plugins validate; advisor clean | ✅ `claude plugin validate` passes ×4; security advisor shows 0 lints; ledger self-test `ALL LEDGER CHECKS PASSED` |
| Test tasks and rows removed | ⚠️ Partly. See Open questions |

## Deviations & decisions
- **I created the test tasks myself** (3 tasks titled `[TEST close-task] … delete me`, assigned to Khaled, no project link) because none existed yet. No real task was written.
- **Stamping doesn't touch `updated_at`.** `requests` now has its own trigger that ignores changes to only `resolution` or `tracker_closed_at`. Otherwise a stamp would show the row as "changed since booked" in the digest. Every other table keeps `set_updated_at`.
- `agent_mark_tracker_closed` doesn't require `resolution`, so close-task also works before the Coordinator brief ships. It's idempotent.
- The sync **never withdraws a row with `resolution` set**, because that row's status belongs to the Coordinator, as the brief asks.
- The ledger write is the only one close-task makes. It never writes `status` or `resolution`.

## Open questions
1. **Cleanup needs you (2 minutes).** The Supabase connector holds `DELETE`/`DROP` for a confirmation this session never receives, and the Notion connector can't trash pages. All 4 test rows are already `declined`, so they're harmless. To finish:
   - Supabase SQL: `delete from public.requests where title like '[TEST close-task]%';`
   - Notion: trash the 3 `[TEST close-task]` tasks.
2. Do you want a **Cancelled** status in the tracker? If you add one, `not_needed` uses it automatically.
3. Should these two branches go to `main` now? A PR for each, or a direct merge?

## Suggested next build
The **Coordinator brief**:
- digest replies `N done` / `N not needed (+ reason)`,
- a checked `coordinator_resolve(id, resolution, reason)` that sets `resolution` and keeps the reason in `decision_note` after `: `,
- the status choice for resolved rows,
- the handoff line above.
