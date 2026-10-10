# Chief of Staff · 🟢 live

**Owns:** Khaled's PRNTCODE time and the weekly rhythm. It turns the team tracker into time asks for the Coordinator and runs the Monday meeting pack.

**Skills (live)**
- [`refresh`](../../skills/refresh/SKILL.md) (`/prntcode-ceo:refresh`): reads "Get Sh*t done!!!" and posts what needs Khaled's time in the coming half-week to the Coordinator ledger. **v2.4:** it's the Coordinator's first feeder, run silently by the Sun + Wed 20:00 collect, which stores its 5-line pre-brief (and the Finance line) as its board line for the 21:00 plan. Typed by hand, it still sends the pre-brief (plus the Monday Pack link on Sundays) and hands over to Coordinator planning.
- [`what-now`](../../skills/what-now/SKILL.md): in a focus block, returns the 1–3 tasks that fit the time he has, each with its first concrete step. "done" closes the task via close-task.
- [`close-task`](../../skills/close-task/SKILL.md): closes one tracker task Khaled marked done or not needed.
- [`monday-pack`](../../skills/monday-pack/SKILL.md): the Monday Meeting Pack, ported unchanged, plus **Your time asks**. **v2.4:** also a Sunday feeder: it builds the pack as its own artifact at the 20:00 collect, leaves the link on the board and its proposal queue in the ledger, and `pack 1 3` approves from any chat.
- [`meeting-tasks`](../../skills/meeting-tasks/SKILL.md): turns Fellow meeting action items into tasks in "Get Sh*t done!!!" for the whole PRNTCODE team. Nothing is written until Khaled approves the confirmation table.

**Will take on later:** pipeline cadence (check the Game Plan pipeline against Strategy's cadence and flag a gap while there's still lead time). Guess-accuracy tracking moves to the Auditor.

**Writes:** the ledger top half (upsert) and `agent_withdraw` only, plus (v2.4, as feeders) one `prep_record` per run for their own board line and outputs. Notion only after an approved Monday Pack proposal or an approved meeting-tasks table, or when close-task closes one task Khaled marked done. Never calendars.
