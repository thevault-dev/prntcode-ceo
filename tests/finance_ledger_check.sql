-- PRNTCODE Finance ↔ Coordinator ledger check (v2.3)
-- Paste into Supabase → project "coordinator" → SQL Editor → Run.
-- Everything runs inside a transaction that is ROLLED BACK at the end:
-- it never leaves a row behind. The last result row says
-- 'ALL FINANCE LEDGER CHECKS PASSED' or names the first failing check.
-- No real amounts: the row carries only a title and an estimate.

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
      values ('prntcode', 'finance', 'finance:__check', %L, %L, %s, now(), %L::timestamptz, 'flexible', %s)
      on conflict (source_agent, source_ref) do update
        set title = excluded.title, due_by = excluded.due_by
        where requests.status in ('new', 'proposed', 'scheduled')
          and (requests.title is distinct from excluded.title
               or requests.due_by is distinct from excluded.due_by)
      returning (xmax = 0) as inserted)
    select count(*) from w $u$;
begin
  -- 1. Cash AMBER + 2 decisions: the refresh posts exactly one Finance row.
  execute format(upsert, 'Finance decisions — cash AMBER, 2 to decide', 'Est. 60m: cash AMBER + 2 Finance decisions', 60, '2099-01-07T19:59:00Z', 2) into n;
  assert n = 1, 'check 1: first Finance post should write 1 row, wrote ' || n;
  select count(*) into n from public.requests
   where source_agent = 'prntcode' and sub_agent = 'finance' and source_ref like 'finance:__check%';
  assert n = 1, 'check 1: expected exactly one Finance row, found ' || n;

  -- 2. A second refresh with nothing changed writes nothing.
  execute format(upsert, 'Finance decisions — cash AMBER, 2 to decide', 'Est. 60m: cash AMBER + 2 Finance decisions', 60, '2099-01-07T19:59:00Z', 2) into n;
  assert n = 0, 'check 2: unchanged re-run should write 0 rows, wrote ' || n;

  -- 3. One more decision: only the title changes; the estimate is never re-guessed.
  execute format(upsert, 'Finance decisions — cash AMBER, 3 to decide', 'Est. 90m: reguess', 90, '2099-01-07T19:59:00Z', 1) into n;
  select * into r from public.requests where source_agent = 'prntcode' and source_ref = 'finance:__check';
  assert n = 1, 'check 3: title change should write 1 row, wrote ' || n;
  assert r.title = 'Finance decisions — cash AMBER, 3 to decide', 'check 3: title not updated';
  assert r.duration_min = 60 and r.priority = 2 and r.context = 'Est. 60m: cash AMBER + 2 Finance decisions',
    'check 3: duration/priority/context were re-guessed';

  -- 4. The refresh's withdraw sweep (step 6) never picks a Finance row,
  --    even though its source_ref isn't a tracker task.
  select count(*) into n from public.requests
   where source_agent = 'prntcode'
     and status in ('new', 'proposed', 'scheduled')
     and resolution is null
     and sub_agent is distinct from 'finance'
     and source_ref = 'finance:__check';
  assert n = 0, 'check 4: the withdraw sweep would pick up the Finance row';

  -- 5. close-task on a Finance row: stamp only (no Notion), and the stamp is accepted.
  update public.requests set resolution = 'done_elsewhere'
   where source_agent = 'prntcode' and source_ref = 'finance:__check';
  r := public.agent_mark_tracker_closed((select id from public.requests
                                           where source_agent = 'prntcode' and source_ref = 'finance:__check'));
  assert r.tracker_closed_at is not null, 'check 5: Finance row was not stamped';
  update public.requests set resolution = null, tracker_closed_at = null
   where source_agent = 'prntcode' and source_ref = 'finance:__check';

  -- 6. Nothing pending any more: step 6b withdraws it with the Finance reason.
  r := public.agent_withdraw('prntcode', 'finance:__check', 'nothing pending in Finance');
  assert r.status = 'declined', 'check 6: Finance withdraw did not decline';
  assert r.decision_note = 'withdrawn by prntcode: nothing pending in Finance', 'check 6: wrong note: ' || r.decision_note;

  -- 7. A withdrawn Finance row isn't reopened in the same half-week.
  execute format(upsert, 'Finance decisions — cash RED', 'x', 30, '2099-01-08T19:59:00Z', 1) into n;
  assert n = 0, 'check 7: upsert reopened a withdrawn Finance row';

  insert into _result values ('ALL FINANCE LEDGER CHECKS PASSED');
exception when assert_failure then
  insert into _result values ('FAILED: ' || sqlerrm);
end $$;

select msg from _result;

rollback;
