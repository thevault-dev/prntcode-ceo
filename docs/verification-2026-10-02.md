# Build verification: 2 Oct 2026

All checks ran against the **live** tracker and ledger. Nothing was left in the ledger: every write test ran inside a transaction that rolled itself back.

| Check | Result |
|---|---|
| `claude plugin validate` on the marketplace and the plugin | ✅ passed |
| Local install: `ceo`, `sync` and `monday-pack` skills discovered | ✅ |
| `agent_withdraw` live: new → declined, note `withdrawn by prntcode: …` | ✅ |
| `agent_withdraw` refuses a `scheduled` row | ✅ |
| `agent_withdraw` refuses a missing row | ✅ |
| EXECUTE on `agent_withdraw` limited to `postgres` and `service_role` | ✅ |
| Upsert: identical second run writes **0** rows | ✅ |
| Upsert: due-date change updates `due_by` only (duration, priority and context kept) | ✅ |
| Upsert never touches a declined row | ✅ |
| `tests/prntcode_contract_check.sql` | ✅ ALL PRNTCODE CONTRACT CHECKS PASSED |
| "Your time asks" query, week = Mon 28 Sep 00:00 Abu Dhabi | ✅ returns the 6 proposed prntcode rows |

## Sync dry run (read-only, no writes)

Khaled's open tasks: 63. Ledger rows for `prntcode`: 6, all `proposed`, posted 30 Sep.

- **Unchanged (6):** Get back to them — Vibey Pop Up · Book the factory visit — WILDFLOWER SUMMER · Issue the PO — WILDFLOWER SUMMER · Have a backup for Harizel — Cactus District Round 2 · POS setup — Cactus District Round 2 · Come up with concept — PRNTCODE House Launch Event. Title and due date match exactly, so **0 writes**.
- **Withdraw:** none. All 6 tasks are still open and assigned to Khaled.
- **New dated candidate (1):** Book tickets — Premier Vision - NYC (due 21 Jan 2027). Judged a quick errand, so no block.
- **Overdue (~20):** e.g. Sign the collection budget (14 Sep), Set pricing (16 Sep), Hire the design freelancer (25 Sep), Calculate for the price (29 Sep), plus Website tasks whose project D-Day (22 May) has passed.
- **Undated (~35):** tasks with no due date on projects with no D-Day (Studio, Operations & Systems, Finance time with Raju, The Boring Stuff: Admin, 25 hour hotel, and others).

Expected first live run: **Posted 0 · Updated 0 · Withdrawn 0 · Unchanged 6**, with the skipped lists.

## Not verified from this session

- The `thevault-dev/coordinator` repo (README, version bump, `definition_of_done.sql`): the session had no access to that repo. See `coordinator-handoff.md`.
- Installing in claude.ai and the Cowork 06:30 task: these need Khaled's account. Follow README sections 1–3.
- The `Priority` formula's real values: the Notion connector doesn't expose them (see README → Priority mapping).
