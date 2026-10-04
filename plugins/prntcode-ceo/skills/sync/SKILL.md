---
name: sync
description: RETIRED daily PRNTCODE sync (it used to run at 06:30). Use only when "/prntcode-ceo:sync" is run, e.g. by the old daily scheduled task. It writes nothing and tells Khaled to switch that task off. The half-week refresh (refresh skill) replaced it; "sync my PRNTCODE time" typed in chat goes to the refresh skill.
---

# Retired: the daily 06:30 sync

The daily sync was replaced in the prntcode-ceo plugin's half-week version by the **refresh** (Sunday and Wednesday 20:00), which also hands over to Coordinator planning.

**Don't read or write anything.** Reply with exactly this:

```
The daily 06:30 PRNTCODE sync is retired. Switch this task off: Cowork → Scheduled → "PRNTCODE sync" (/prntcode-ceo:sync) → turn it off or delete it. The refresh now runs Sun and Wed 20:00; say "refresh PRNTCODE" to run it now.
```

If Khaled then says "refresh PRNTCODE" (or "yes, run it"), follow the **refresh** skill.
