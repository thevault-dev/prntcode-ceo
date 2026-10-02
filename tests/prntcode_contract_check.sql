-- PRNTCODE CEO ↔ Coordinator ledger contract check
-- Paste into Supabase → project "coordinator" → SQL Editor → Run.
-- Everything runs inside a transaction that is ROLLED BACK at the end:
-- it never leaves a row behind. The last result row says
-- 'ALL PRNTCODE CONTRACT CHECKS PASSED' or names the first failing check.

begin;

create temp table _result(msg text) on commit drop;

do $$
declare
  n int;
  r public.requests;
  e text;
  upsert text := $u$
    with w as (
      insert into public.requests
        (source_agent, sub_agent, source_ref, title, context, duration_min,
         earliest_start, due_by, flexibility, priority)
      values ('prntcode', 'chief_of_staff', '__check', %L, %L, %s, now(), %L::timestamptz, 'flexible', %s)
      on conflict (source_agent, source_ref) do update
        set title = excluded.title, due_by = excluded.due_by
        where requests.status in ('new', 'proposed', 'scheduled')
          and (requests.title is distinct from excluded.title
               or requests.due_by is distinct from excluded.due_by)
      returning (xmax = 0) as inserted)
    select count(*) from w $u$;
begin
  -- 1. First post inserts one row.
  execute format(upsert, 'Khaled''s check — Proj', 'Est. 90m: check', 90, '2026-12-01T19:59:00Z', 3) into n;
  assert n = 1, 'check 1: first post should write 1 row, wrote ' || n;

  -- Coordinator proposes it (simulated).
  update public.requests
     set status = 'proposed', slot_start = now() + interval '2 days',
         slot_end = now() + interval '2 days 90 minutes', decided_at = now()
   where source_agent = 'prntcode' and source_ref = '__check';

  -- 2. Identical second run writes zero rows.
  execute format(upsert, 'Khaled''s check — Proj', 'Est. 90m: check', 90, '2026-12-01T19:59:00Z', 3) into n;
  assert n = 0, 'check 2: unchanged re-run should write 0 rows, wrote ' || n;

  -- 3. Due date change updates due_by only; a different duration/priority/context is ignored.
  execute format(upsert, 'Khaled''s check — Proj', 'Est. 30m: reguess', 30, '2026-12-05T19:59:00Z', 1) into n;
  select * into r from public.requests where source_agent = 'prntcode' and source_ref = '__check';
  assert n = 1, 'check 3: due change should write 1 row, wrote ' || n;
  assert r.due_by = '2026-12-05T19:59:00Z'::timestamptz, 'check 3: due_by not updated';
  assert r.duration_min = 90 and r.priority = 3 and r.context = 'Est. 90m: check',
    'check 3: duration/priority/context were re-guessed';
  assert r.status = 'proposed', 'check 3: status changed';

  -- 4. agent_withdraw: proposed -> declined with the note.
  r := public.agent_withdraw('prntcode', '__check', 'task marked done in Notion');
  assert r.status = 'declined', 'check 4: withdraw did not decline';
  assert r.decision_note = 'withdrawn by prntcode: task marked done in Notion', 'check 4: wrong note: ' || r.decision_note;

  -- 5. Upsert never touches a declined row.
  execute format(upsert, 'Renamed — Proj', 'x', 30, '2026-12-09T19:59:00Z', 3) into n;
  assert n = 0, 'check 5: upsert wrote to a declined row';

  -- 6. agent_withdraw refuses a scheduled row.
  insert into public.requests (source_agent, sub_agent, source_ref, title, duration_min, status,
                               slot_start, slot_end, calendar_event_id, decided_at)
  values ('prntcode', 'chief_of_staff', '__check_booked', 'booked check', 60, 'scheduled',
          now() + interval '1 day', now() + interval '1 day 1 hour', 'evt_check', now());
  begin
    perform public.agent_withdraw('prntcode', '__check_booked', 'x');
    e := 'not refused';
  exception when others then e := 'refused';
  end;
  assert e = 'refused', 'check 6: agent_withdraw did not refuse a scheduled row';

  -- 7. agent_withdraw refuses a missing row.
  begin
    perform public.agent_withdraw('prntcode', '__check_missing', 'x');
    e := 'not refused';
  exception when others then e := 'refused';
  end;
  assert e = 'refused', 'check 7: agent_withdraw did not refuse a missing row';

  insert into _result values ('ALL PRNTCODE CONTRACT CHECKS PASSED');
exception when assert_failure then
  insert into _result values ('FAILED: ' || sqlerrm);
end $$;

select msg from _result;

rollback;
