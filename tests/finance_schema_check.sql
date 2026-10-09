-- PRNTCODE Finance schema check (v2.3)
-- Paste into Supabase → project "PRNTCODE-ops" → SQL Editor → Run.
-- Runs inside a transaction that is ROLLED BACK: it never leaves a row behind,
-- and it never touches an Ops table. The last row says
-- 'ALL FINANCE SCHEMA CHECKS PASSED' or names the first failing check.
-- All figures are made up.

begin;

create temp table _result(msg text) on commit drop;

do $$
declare
  n int;
  b boolean;
  s finance.scenarios;
  c finance.po_checks;
  l finance.brief_lines;
  p finance.pushes;
  e text;
begin
  -- 1. Locked down: anon and authenticated can't read or call anything.
  assert not has_table_privilege('anon', 'finance.settings', 'select'), 'check 1: anon can read settings';
  assert not has_table_privilege('authenticated', 'finance.scenarios', 'select'), 'check 1: authenticated can read scenarios';
  assert not has_function_privilege('anon', 'finance.set_setting(text, jsonb)', 'execute'), 'check 1: anon can write settings';
  select count(*) into n from pg_tables where schemaname = 'finance' and not rowsecurity;
  assert n = 0, 'check 1: a finance table has RLS off';

  -- 2. Settings: write, then overwrite.
  perform finance.set_setting('__check_floor', '10000'::jsonb);
  perform finance.set_setting('__check_floor', '12000'::jsonb);
  select count(*) into n from finance.settings where key = '__check_floor' and value = '12000'::jsonb;
  assert n = 1, 'check 2: setting not overwritten';

  -- 3. One snapshot per month: the second save keeps the first.
  perform finance.save_snapshot('2099-01-03', '[{"month":"2099-01","b2c":1}]', '[]');
  perform finance.save_snapshot('2099-01-20', '[{"month":"2099-01","b2c":999}]', '[]');
  select count(*) into n from finance.forecast_snapshots
   where snapshot_month = '2099-01-01' and months -> 0 ->> 'b2c' = '1';
  assert n = 1, 'check 3: snapshot overwritten or missing';
  perform finance.score_snapshot('2099-01-01', '{"b2c":1}', 10, -5, 2);
  select count(*) into n from finance.forecast_snapshots where snapshot_month = '2099-01-01' and scored_at is not null;
  assert n = 1, 'check 3: snapshot not scored';

  -- 4. Scenarios: save, edit while draft, make real, then edits are refused; drop.
  s := finance.save_scenario('__check hire', 'hire a tailor at AED 4,000 a month from January',
                             '[{"type":"cost","label":"tailor","amount_aed":4000,"per":"month","from":"2099-01"}]', '[]');
  assert s.status = 'draft', 'check 4: new scenario not draft';
  s := finance.save_scenario('__check hire', 'hire a tailor from February',
                             '[{"type":"cost","label":"tailor","amount_aed":4000,"per":"month","from":"2099-02"}]', '[]');
  assert s.changes -> 0 ->> 'from' = '2099-02', 'check 4: draft edit not saved';
  s := finance.set_scenario_status('__check hire', 'base');
  assert s.status = 'base' and s.made_real_at is not null, 'check 4: make it real failed';
  begin
    perform finance.save_scenario('__check hire', 'x', '[]', '[]');
    e := 'accepted';
  exception when others then e := 'refused';
  end;
  assert e = 'refused', 'check 4: a base scenario was edited';
  s := finance.set_scenario_status('__check hire', 'dropped');
  assert s.status = 'dropped' and s.dropped_at is not null, 'check 4: drop failed';

  -- 5. PO checks: go_smaller needs a quantity and AED saved; an unchanged PO isn't re-checked.
  begin
    perform finance.record_po_check('__CHECK-PO', 'fp1', 'draft', 30000, 'go_smaller', null, null, null, 'too big');
    e := 'accepted';
  exception when check_violation then e := 'refused';
  end;
  assert e = 'refused', 'check 5: go_smaller without quantity accepted';
  c := finance.record_po_check('__CHECK-PO', 'fp1', 'draft', 30000, 'go_smaller',
                               '{"TEST-SKU-M": 60}', 12000, null, '7 months of cover at the current pace; 60 pcs gives 3');
  assert c.verdict = 'go_smaller', 'check 5: verdict not stored';
  perform finance.record_po_check('__CHECK-PO', 'fp1', 'draft', 30000, 'go', null, null, null, 'rerun');
  select count(*) into n from finance.po_checks where po_number = '__CHECK-PO';
  assert n = 1, 'check 5: unchanged PO was re-checked';
  perform finance.record_po_check('__CHECK-PO', 'fp2', 'draft', 18000, 'go', null, null, null, 'resized to 60 pcs');
  select verdict into e from finance.po_latest_check_v where po_number = '__CHECK-PO';
  assert e = 'go', 'check 5: latest check view wrong';

  -- 6. At most one brief line a day.
  l := finance.write_brief_line('2099-01-05', 'PO __CHECK-PO test restock AED 30,000: Finance says go smaller (60 pcs).', '__CHECK-PO');
  assert l.for_date is not null, 'check 6: first line not written';
  l := finance.write_brief_line('2099-01-05', 'a second line', null);
  assert l.for_date is null, 'check 6: second line the same day was written';

  -- 7. Push rule: once per episode, again only if worse or after 7 days.
  perform finance.close_push_episode();                       -- start clean inside the test
  b := finance.push_due('2099-01-12', 5000);
  assert b, 'check 7: first push not due';
  p := finance.record_push('2099-01-12', 5000, 'test push', 'test');
  b := finance.push_due('2099-01-12', 5000);                  -- the next day, same gap
  assert not b, 'check 7: same gap would push again';
  begin
    perform finance.record_push('2099-01-12', 5000, 'again', 'test');
    e := 'accepted';
  exception when others then e := 'refused';
  end;
  assert e = 'refused', 'check 7: record_push accepted a repeat';
  assert finance.push_due('2099-01-12', 8000), 'check 7: a bigger gap is not due';
  assert finance.push_due('2099-01-09', 5000), 'check 7: a sooner gap is not due';
  update finance.pushes set sent_at = now() - interval '8 days' where id = p.id;
  assert finance.push_due('2099-01-12', 5000), 'check 7: not due after 7 days';
  perform finance.close_push_episode();
  assert finance.push_due('2099-01-12', 5000), 'check 7: closing the episode did not reset';

  -- 8. Reviews: unopened until opened.
  perform finance.record_review('2099-01-03', 'https://example.invalid/review', '[{"rank":1,"aed_90d":5000}]');
  select count(*) into n from finance.reviews where month = '2099-01-01' and opened_at is null;
  assert n = 1, 'check 8: review not stored as unopened';
  perform finance.mark_review_opened('2099-01-01');
  select count(*) into n from finance.reviews where month = '2099-01-01' and opened_at is not null;
  assert n = 1, 'check 8: review not marked opened';

  insert into _result values ('ALL FINANCE SCHEMA CHECKS PASSED');
exception when assert_failure then
  insert into _result values ('FAILED: ' || sqlerrm);
end $$;

select msg from _result;

rollback;
