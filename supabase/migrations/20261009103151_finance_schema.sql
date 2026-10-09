-- PRNTCODE Finance (prntcode-ceo 2.3.0): Finance's own data.
-- Applied to PRNTCODE-ops on 9 Oct 2026 as migration 20261009103151 finance_schema.
--
-- Project: PRNTCODE-ops (nhimagmpcwlkbfygiowq). A separate `finance` schema,
-- so nothing here touches the Ops tables. Row-level security is on with no
-- policies, and anon/authenticated get nothing: rows are read by the Finance
-- skills over the service connection, and written ONLY through the
-- finance.* functions below.
--
-- The repo is public: this file holds structure only, never data. The cash
-- floor, launches, recurring-cost list and partner terms are written at
-- setup through finance.set_setting().

create schema if not exists finance;
revoke all on schema finance from public, anon, authenticated;
grant usage on schema finance to service_role;

-- ---------------------------------------------------------------- tables

-- One row per setting. Keys used by the skills:
--   cash_floor            number, AED
--   months_cover_target   number, default 3
--   launches              [{name, line, date (YYYY-MM-DD)}]
--   recurring_costs       {"<zoho account or vendor>": {"recurring": bool, "note": text}}
--   partner_payment_terms {"<ops partner_id>": {"deposit_pct": n, "deposit_on": "sent", "balance_days_after_received": n}}
--   baseline_calibration  {"b2c": factor, "b2b": factor, "costs": factor}
--   setup_done            date
create table finance.settings (
  key        text primary key check (length(btrim(key)) > 0),
  value      jsonb not null,
  updated_at timestamptz not null default now()
);

-- One forecast snapshot per month, saved on the 3rd, for the accuracy check.
-- snapshot_month is the first month the snapshot forecasts.
create table finance.forecast_snapshots (
  snapshot_month   date primary key check (extract(day from snapshot_month) = 1),
  made_at          timestamptz not null default now(),
  months           jsonb not null,  -- [{month, b2c, b2b, costs, cogs, profit, cash_end}] x 12
  weeks            jsonb not null,  -- [{week_start, cash_end}] x 8
  assumptions      jsonb not null default '{}'::jsonb,
  actual           jsonb,           -- {b2c, b2b, costs, profit, cash_end} for snapshot_month
  sales_error_pct  numeric,         -- (forecast - actual) / actual * 100
  costs_error_pct  numeric,
  cash_error_pct   numeric,
  scored_at        timestamptz
);

create table finance.scenarios (
  id           uuid primary key default gen_random_uuid(),
  name         text not null unique check (length(btrim(name)) > 0),
  ask          text not null,                       -- his words
  changes      jsonb not null default '[]'::jsonb,  -- explicit changes (see forecast skill)
  assumptions  jsonb not null default '[]'::jsonb,
  status       text not null default 'draft' check (status in ('draft', 'base', 'dropped')),
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now(),
  made_real_at timestamptz,
  dropped_at   timestamptz
);

-- Every check of a PO. A new row only when the PO changed (fingerprint).
create table finance.po_checks (
  id             bigint generated always as identity primary key,
  po_number      text not null,
  po_fingerprint text not null,      -- status + lines, so an unchanged PO isn't re-checked
  po_status      text not null,
  po_total_aed   numeric,
  verdict        text not null check (verdict in ('go', 'go_smaller', 'wait')),
  suggested_qty  jsonb,              -- {"<sku>": qty} for go_smaller
  aed_saved      numeric,
  wait_until     date,
  reasons        text not null check (length(btrim(reasons)) > 0),
  checked_at     timestamptz not null default now(),
  unique (po_number, po_fingerprint),
  check (verdict <> 'go_smaller' or (suggested_qty is not null and aed_saved is not null)),
  check (verdict <> 'wait' or wait_until is not null)
);

-- At most one brief line a day, for the Coordinator's daily brief
-- (sent as that day's notification until the brief exists).
create table finance.brief_lines (
  for_date     date primary key,      -- Abu Dhabi date
  line         text not null check (length(btrim(line)) > 0),
  po_number    text,
  written_at   timestamptz not null default now(),
  delivered_as text not null default 'notification' check (delivered_as in ('notification', 'daily_brief')),
  read_at      timestamptz            -- stamped by the Coordinator when its brief uses the line
);

-- Low-cash pushes, so nothing repeats inside an episode.
create table finance.pushes (
  id                bigint generated always as identity primary key,
  sent_at           timestamptz not null default now(),
  gap_date          date not null,    -- first day expected cash is below the floor
  gap_aed           numeric not null check (gap_aed > 0),
  message           text not null,
  channel           text not null,
  episode_closed_at timestamptz       -- set when cash is back above the floor for the next 14 days
);

create table finance.reviews (
  month        date primary key check (extract(day from month) = 1),  -- the month reviewed
  artifact_url text,
  suggestions  jsonb not null default '[]'::jsonb,  -- up to 5 ranked moves
  delivered_at timestamptz not null default now(),
  opened_at    timestamptz
);

alter table finance.settings           enable row level security;
alter table finance.forecast_snapshots enable row level security;
alter table finance.scenarios          enable row level security;
alter table finance.po_checks          enable row level security;
alter table finance.brief_lines        enable row level security;
alter table finance.pushes             enable row level security;
alter table finance.reviews            enable row level security;

revoke all on all tables in schema finance from public, anon, authenticated;
grant select on all tables in schema finance to service_role;

-- ---------------------------------------------------------------- views

-- Latest check per PO.
create view finance.po_latest_check_v with (security_invoker = true) as
select distinct on (po_number) *
from finance.po_checks
order by po_number, checked_at desc;

-- Running accuracy over the last 6 scored months: 100 - mean absolute error %.
create view finance.accuracy_v with (security_invoker = true) as
select count(*)                                          as months_scored,
       round(100 - avg(abs(sales_error_pct)), 1)         as sales_accuracy_pct,
       round(100 - avg(abs(costs_error_pct)), 1)         as costs_accuracy_pct,
       round(100 - avg(abs(cash_error_pct)), 1)          as cash_accuracy_pct
from (select * from finance.forecast_snapshots
      where scored_at is not null
      order by snapshot_month desc limit 6) s;

revoke all on finance.po_latest_check_v, finance.accuracy_v from public, anon, authenticated;
grant select on finance.po_latest_check_v, finance.accuracy_v to service_role;

-- ---------------------------------------------------------------- write functions
-- The only write paths. SECURITY DEFINER with an empty search_path;
-- EXECUTE for service_role only (postgres owns them).

create function finance.set_setting(p_key text, p_value jsonb)
returns finance.settings
language plpgsql security definer set search_path = ''
as $$
declare r finance.settings;
begin
  if p_value is null then
    raise exception 'finance.set_setting: value for % is null', p_key;
  end if;
  insert into finance.settings (key, value) values (btrim(p_key), p_value)
  on conflict (key) do update set value = excluded.value, updated_at = now()
  returning * into r;
  return r;
end $$;

create function finance.save_snapshot(p_month date, p_months jsonb, p_weeks jsonb, p_assumptions jsonb default '{}'::jsonb)
returns finance.forecast_snapshots
language plpgsql security definer set search_path = ''
as $$
declare r finance.forecast_snapshots;
begin
  -- One per month: a second save the same month keeps the first.
  insert into finance.forecast_snapshots (snapshot_month, months, weeks, assumptions)
  values (date_trunc('month', p_month)::date, p_months, p_weeks, coalesce(p_assumptions, '{}'::jsonb))
  on conflict (snapshot_month) do nothing;
  select * into r from finance.forecast_snapshots where snapshot_month = date_trunc('month', p_month)::date;
  return r;
end $$;

create function finance.score_snapshot(p_month date, p_actual jsonb,
                                       p_sales_error_pct numeric, p_costs_error_pct numeric, p_cash_error_pct numeric)
returns finance.forecast_snapshots
language plpgsql security definer set search_path = ''
as $$
declare r finance.forecast_snapshots;
begin
  update finance.forecast_snapshots
     set actual = p_actual, sales_error_pct = p_sales_error_pct,
         costs_error_pct = p_costs_error_pct, cash_error_pct = p_cash_error_pct, scored_at = now()
   where snapshot_month = date_trunc('month', p_month)::date
  returning * into r;
  if not found then
    raise exception 'finance.score_snapshot: no snapshot for %', date_trunc('month', p_month)::date;
  end if;
  return r;
end $$;

create function finance.save_scenario(p_name text, p_ask text, p_changes jsonb, p_assumptions jsonb)
returns finance.scenarios
language plpgsql security definer set search_path = ''
as $$
declare r finance.scenarios;
begin
  insert into finance.scenarios (name, ask, changes, assumptions)
  values (btrim(p_name), p_ask, coalesce(p_changes, '[]'::jsonb), coalesce(p_assumptions, '[]'::jsonb))
  on conflict (name) do update
     set ask = excluded.ask, changes = excluded.changes, assumptions = excluded.assumptions, updated_at = now()
   where finance.scenarios.status = 'draft'
  returning * into r;
  if r.id is null then
    raise exception 'finance.save_scenario: "%" is already % and can''t be edited; save it under a new name', p_name,
      (select status from finance.scenarios where name = btrim(p_name));
  end if;
  return r;
end $$;

create function finance.set_scenario_status(p_name text, p_status text)
returns finance.scenarios
language plpgsql security definer set search_path = ''
as $$
declare r finance.scenarios;
begin
  if p_status not in ('base', 'dropped', 'draft') then
    raise exception 'finance.set_scenario_status: bad status %', p_status;
  end if;
  update finance.scenarios
     set status = p_status, updated_at = now(),
         made_real_at = case when p_status = 'base' then now() else made_real_at end,
         dropped_at   = case when p_status = 'dropped' then now() else null end
   where name = btrim(p_name)
  returning * into r;
  if not found then
    raise exception 'finance.set_scenario_status: no scenario named "%"', p_name;
  end if;
  return r;
end $$;

create function finance.record_po_check(p_po_number text, p_fingerprint text, p_po_status text, p_po_total_aed numeric,
                                        p_verdict text, p_suggested_qty jsonb, p_aed_saved numeric,
                                        p_wait_until date, p_reasons text)
returns finance.po_checks
language plpgsql security definer set search_path = ''
as $$
declare r finance.po_checks;
begin
  -- An unchanged PO keeps its verdict: same (po, fingerprint) writes nothing.
  insert into finance.po_checks (po_number, po_fingerprint, po_status, po_total_aed, verdict,
                                 suggested_qty, aed_saved, wait_until, reasons)
  values (p_po_number, p_fingerprint, p_po_status, p_po_total_aed, p_verdict,
          p_suggested_qty, p_aed_saved, p_wait_until, p_reasons)
  on conflict (po_number, po_fingerprint) do nothing
  returning * into r;
  if r.id is null then
    select * into r from finance.po_checks where po_number = p_po_number and po_fingerprint = p_fingerprint;
  end if;
  return r;
end $$;

create function finance.write_brief_line(p_for_date date, p_line text, p_po_number text, p_delivered_as text default 'notification')
returns finance.brief_lines
language plpgsql security definer set search_path = ''
as $$
declare r finance.brief_lines;
begin
  -- At most one a day: a second write the same day returns NULL and changes nothing.
  insert into finance.brief_lines (for_date, line, po_number, delivered_as)
  values (p_for_date, p_line, p_po_number, p_delivered_as)
  on conflict (for_date) do nothing
  returning * into r;
  return r;
end $$;

create function finance.mark_brief_line_read(p_for_date date)
returns finance.brief_lines
language sql security definer set search_path = ''
as $$
  update finance.brief_lines set read_at = coalesce(read_at, now()) where for_date = p_for_date returning *;
$$;

-- The push rule's memory. TRUE when a push should go out now: no open
-- episode, or the gap got worse (bigger, or sooner) than the last push,
-- or 7 days have passed since it.
create function finance.push_due(p_gap_date date, p_gap_aed numeric)
returns boolean
language sql stable security definer set search_path = ''
as $$
  select coalesce((
    select p_gap_aed > last.gap_aed
        or p_gap_date < last.gap_date
        or last.sent_at <= now() - interval '7 days'
    from finance.pushes last
    where last.episode_closed_at is null
    order by last.sent_at desc limit 1
  ), true);
$$;

create function finance.record_push(p_gap_date date, p_gap_aed numeric, p_message text, p_channel text)
returns finance.pushes
language plpgsql security definer set search_path = ''
as $$
declare r finance.pushes;
begin
  if not finance.push_due(p_gap_date, p_gap_aed) then
    raise exception 'finance.record_push: not due (same episode, not worse, under 7 days)';
  end if;
  insert into finance.pushes (gap_date, gap_aed, message, channel)
  values (p_gap_date, p_gap_aed, p_message, p_channel)
  returning * into r;
  return r;
end $$;

create function finance.close_push_episode()
returns integer
language sql security definer set search_path = ''
as $$
  with c as (update finance.pushes set episode_closed_at = now() where episode_closed_at is null returning 1)
  select count(*)::int from c;
$$;

create function finance.record_review(p_month date, p_artifact_url text, p_suggestions jsonb)
returns finance.reviews
language plpgsql security definer set search_path = ''
as $$
declare r finance.reviews;
begin
  insert into finance.reviews (month, artifact_url, suggestions)
  values (date_trunc('month', p_month)::date, p_artifact_url, coalesce(p_suggestions, '[]'::jsonb))
  on conflict (month) do update
     set artifact_url = excluded.artifact_url, suggestions = excluded.suggestions
  returning * into r;
  return r;
end $$;

create function finance.mark_review_opened(p_month date)
returns finance.reviews
language plpgsql security definer set search_path = ''
as $$
declare r finance.reviews;
begin
  update finance.reviews set opened_at = coalesce(opened_at, now())
   where month = date_trunc('month', p_month)::date
  returning * into r;
  if not found then
    raise exception 'finance.mark_review_opened: no review for %', date_trunc('month', p_month)::date;
  end if;
  return r;
end $$;

revoke all on all functions in schema finance from public, anon, authenticated;
grant execute on all functions in schema finance to service_role;

comment on schema finance is 'PRNTCODE Finance (prntcode-ceo plugin). Read-only on the Ops tables; writes only through finance.* functions.';
