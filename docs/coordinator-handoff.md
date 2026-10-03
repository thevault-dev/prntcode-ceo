# Coordinator repo handoff: `agent_withdraw`

> **Resolved 3 Oct 2026.** The close-task build had access to `thevault-dev/coordinator` and added `supabase/migrations/20260930191251_agent_withdraw.sql`, the README entry, the definition-of-done checks and a version bump there. This page is kept for history.

Brief must-have 4 asks for `agent_withdraw` in `thevault-dev/coordinator`. This build session **couldn't open that repo** (access to it wasn't granted to the session), so the repo side couldn't be checked or pushed from here.

## What is already true in the live ledger (checked 2 Oct 2026)

- Migration **`20260930191251 agent_withdraw`** is applied to Supabase project `coordinator` (`hgkreprqxevayruqpibf`).
- `public.agent_withdraw(p_source_agent text, p_source_ref text, p_reason text) returns public.requests`
  - `new` / `proposed` → `declined`, `decision_note = 'withdrawn by <agent>: <reason>'`, `decided_at = now()`.
  - Refuses `scheduled` ("a booked block can only be dropped by Khaled"), any other status, a missing row, and an empty reason.
  - `SET search_path = ''`, not SECURITY DEFINER. EXECUTE is granted to `postgres` and `service_role` only, like the other functions.
- Behaviour checked with a transaction that rolls itself back (see `tests/prntcode_contract_check.sql` in this repo). All checks passed and no rows were left behind.

## What the coordinator repo needs (if not already there)

Whoever has push access to `thevault-dev/coordinator` should check and, if anything is missing, add:

1. **Migration file** `supabase/migrations/20260930191251_agent_withdraw.sql` with the live definition below. The version must match the one already applied, so Supabase doesn't try to apply it twice.
2. **README**: under the ledger contract, add `agent_withdraw` next to the existing functions, saying who calls it (domain agents, on their own rows) and that it refuses booked rows.
3. **Plugin version bump** in `.claude-plugin/plugin.json` (and the marketplace entry), a minor bump.
4. **`supabase/tests/definition_of_done.sql`**: add the block below in the file's existing style, so the self-test still ends with `ALL LEDGER CHECKS PASSED`.

### Live definition (from `pg_get_functiondef`, 2 Oct 2026)

```sql
create or replace function public.agent_withdraw(p_source_agent text, p_source_ref text, p_reason text)
returns public.requests
language plpgsql
set search_path to ''
as $function$
declare
  r public.requests;
begin
  if length(btrim(coalesce(p_reason, ''))) = 0 then
    raise exception 'a reason is required to withdraw %/%', p_source_agent, p_source_ref;
  end if;

  select * into r from public.requests
   where source_agent = p_source_agent and source_ref = p_source_ref
   for update;
  if not found then
    raise exception 'request %/% not found', p_source_agent, p_source_ref;
  end if;
  if r.status = 'scheduled' then
    raise exception 'request %/% is scheduled (event %): a booked block can only be dropped by Khaled',
      p_source_agent, p_source_ref, r.calendar_event_id;
  end if;
  if r.status not in ('new', 'proposed') then
    raise exception 'request %/% is %; only new or proposed requests can be withdrawn',
      p_source_agent, p_source_ref, r.status;
  end if;

  update public.requests
     set status = 'declined',
         decision_note = 'withdrawn by ' || p_source_agent || ': ' || btrim(p_reason),
         decided_at = now()
   where id = r.id
  returning * into r;
  return r;
end;
$function$;

comment on function public.agent_withdraw(text, text, text) is
  'Domain agent withdraws its own new/proposed request (-> declined, "withdrawn by <agent>: <reason>"). Refuses scheduled and missing rows.';

revoke all on function public.agent_withdraw(text, text, text) from public, anon, authenticated;
grant execute on function public.agent_withdraw(text, text, text) to service_role;
```

### Definition-of-done checks to add

```sql
-- agent_withdraw: new -> declined with note; refuses scheduled and missing rows
do $$
declare r public.requests; e text;
begin
  insert into public.requests (source_agent, sub_agent, source_ref, title, duration_min)
  values ('prntcode', 'chief_of_staff', '__dod_withdraw', 'dod withdraw', 30);
  r := public.agent_withdraw('prntcode', '__dod_withdraw', 'task marked done');
  assert r.status = 'declined', 'agent_withdraw: new row not declined';
  assert r.decision_note = 'withdrawn by prntcode: task marked done', 'agent_withdraw: wrong note';

  insert into public.requests (source_agent, source_ref, title, duration_min, status,
                               slot_start, slot_end, calendar_event_id, decided_at)
  values ('prntcode', '__dod_withdraw_booked', 'dod booked', 30, 'scheduled',
          now() + interval '1 day', now() + interval '1 day 30 minutes', 'evt_dod', now());
  begin perform public.agent_withdraw('prntcode', '__dod_withdraw_booked', 'x'); e := 'ok';
  exception when others then e := 'refused'; end;
  assert e = 'refused', 'agent_withdraw: scheduled row not refused';

  begin perform public.agent_withdraw('prntcode', '__dod_missing', 'x'); e := 'ok';
  exception when others then e := 'refused'; end;
  assert e = 'refused', 'agent_withdraw: missing row not refused';

  assert not exists (
    select 1 from information_schema.routine_privileges
     where routine_schema = 'public' and routine_name = 'agent_withdraw'
       and grantee in ('anon', 'authenticated', 'PUBLIC')
  ), 'agent_withdraw: granted beyond service_role';

  delete from public.requests where source_ref like '\_\_dod\_withdraw%';
end $$;
```
