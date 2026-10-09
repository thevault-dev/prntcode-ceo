-- Applied to PRNTCODE-ops on 9 Oct 2026 as migration 20261009103332 finance_po_latest_tiebreak.
-- Two checks of the same PO in one transaction share checked_at (now() is fixed
-- per transaction), so the "latest" check needs id as a tie-breaker.

create or replace view finance.po_latest_check_v with (security_invoker = true) as
select distinct on (po_number) *
from finance.po_checks
order by po_number, checked_at desc, id desc;
revoke all on finance.po_latest_check_v from public, anon, authenticated;
grant select on finance.po_latest_check_v to service_role;
