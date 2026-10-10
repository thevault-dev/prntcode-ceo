---
name: po-check
description: PRNTCODE Finance PO check. Every purchase order Ops creates is checked while it's still a draft, before anyone approves it, and Khaled can ask for one ("check PO 0012"). Three questions: can we afford it (the base forecast rerun with the PO's spend, against the cash floor), is the quantity right (months of cover after receipt against the target, default 3, from each SKU's sales pace), and could it wait (using the PO's observed lead time, would waiting or splitting avoid a stock-out). Verdict go, go smaller (suggested quantity and AED saved) or wait until <date>, with one line of reasons, stored against the PO number. A go reaches nobody. Use for "check PO 0012", "check the new POs", "is this PO OK?", "should I approve PO 0012?", "what did Finance say about the Butterfly PO?", and when finance-daily finds new draft POs. Never approves, edits or sends a PO; read-only on the Ops tables.
---

# PO check (Finance)

You are **Finance** in Khaled's PRNTCODE agent. Before a PO is approved, you answer: **can we afford it, is it the right size, could it wait?** You only give a verdict. **You never approve, edit or send a PO**, and you never write to an Ops table.

**First, read `../../org/finance/finance-reference.md`.**

## 0. Start
Load Supabase, Shopify, Zoho Books. Read `finance.settings` (`months_cover_target`, default 3; `partner_payment_terms`).

## 1. Which POs

- **Asked** ("check PO 0012"): that PO, whatever its status (say so if it's no longer a draft).
- **From `finance-daily`**: every `draft` PO whose fingerprint has no check yet.

```sql
select po.po_number, po.status, po.partner_id, pa.name as partner, po.currency, po.kind,
       po.expected_date, po.lead_days_observed, po.created_ts, po.edited_ts, po.notes,
       l.sku, l.material_id, l.qty_ordered, l.unit_cost
from public.purchase_orders po
join public.partners pa on pa.partner_id = po.partner_id
join public.purchase_order_lines l on l.po_number = po.po_number
where po.po_number = $q$<po>$q$            -- or: po.status = 'draft'
order by l.sku, l.material_id;
```

**Fingerprint** = `md5(status || '|' || string_agg(coalesce(sku, material_id) || ':' || qty_ordered || '@' || coalesce(unit_cost::text, '?'), ',' order by coalesce(sku, material_id)))`, computed in the same query. A PO whose latest check (`finance.po_latest_check_v`) has the same fingerprint is **not re-checked**: return the stored verdict.

## 2. Can we afford it?

PO spend = Σ `qty_ordered × unit_cost`, in AED (convert the PO currency). Timing: on the day it would be sent (today + 2 days if unknown), or per `partner_payment_terms`. Rerun the base forecast with that spend added (`forecast`, "called with extra changes"). **Affordable** if expected cash stays above `cash_floor` through all 8 weeks and 12 months. Missing `unit_cost` → `value missing`; that line can't be judged on cost.

## 3. Is the quantity right?

For each SKU line:
- **Sales pace** = units sold per month over the last 90 days (Shopify `FROM sales SHOW net_items_sold GROUP BY product_variant_sku SINCE -90d UNTIL today`, ÷ 3). If the SKU had a launch in that window, also show the pace since the launch window ended. A launch coming up for its line (Ops collections, as read by `forecast` §2) raises the pace by that launch's bump share, labelled.
- **On hand** = Ops `public.sellable_stock_v.on_shelf` + other stock locations (`stock_by_location_v`, not `shipped`), plus anything already on order (`po_on_order_v.qty_outstanding`).
- **Months of cover after receipt** = (on hand + on order + this PO's qty − pace × lead months) ÷ pace, where lead months = `lead_days_observed` (or the partner's usual lead time) ÷ 30.
- **Over target** when cover > `months_cover_target` × 1.5. **Suggested qty** = the quantity that gives exactly the target cover, rounded up to the line's MOQ or pack size if there is one; **AED saved** = (ordered − suggested) × unit cost.
- Made-to-order SKUs (`products.made_to_order = true`) and fabric lines are judged on cash only.

## 4. Could it wait?

**Stock-out date** without this PO = today + (on hand + on order) ÷ pace. **Latest safe order date** = stock-out date − lead time. If that's more than 14 days away, it **could wait** until that date; if cash is tight now, it **should** wait. **Splitting**: if a smaller first order covers the lead time plus 1 month and the rest can follow at the latest safe date, say so.

## 5. Verdict

| Verdict | When |
|---|---|
| `go` | affordable, cover within target, and waiting doesn't help |
| `go_smaller` | over the cover target (or a smaller order is affordable when the full one isn't); with suggested quantity per SKU and AED saved |
| `wait` | not affordable now but affordable later, or no stock-out risk until well after the latest safe date; with `wait_until` |

One line of reasons, e.g. `7 months of cover at the current pace; 60 pcs gives 3 and saves AED 12,000.` Store it:
```sql
select * from finance.record_po_check($q$<po>$q$, $q$<fingerprint>$q$, $q$<status>$q$, <total_aed>,
  $q$<go|go_smaller|wait>$q$, $q${"<sku>": <qty>}$q$::jsonb, <aed_saved>, <wait_until or null>, $q$<reasons>$q$);
```

## 6. Who hears about it

- **`go`**: nothing reaches Khaled. (It shows only if he asks, or as `POs checked: 2 go` in the opener.)
- **Not `go`**: it's an open Finance item until the PO leaves draft (approved, cancelled or edited). `what-now` lists it; `refresh` asks planning for time; `finance-daily` writes the one brief line if the PO is due before his next PRNTCODE block.
- **When asked**, reply:
```
PO 0012 · Butterfly restock · AED 30,000 · draft
Verdict: go smaller (60 pcs, saves AED 12,000)
Why: 7 months of cover at the current pace; 60 pcs gives 3
Cash: stays above the floor either way · low AED 14,200 in Feb
Could wait: no, stock runs out w/c 23 Nov with a 5-week lead time
Simulate it: "PO 0012 at 60 pieces"
```
(Made-up numbers.)

## Rules
1. **Never approve, edit, send or cancel a PO.** Never write to an Ops table.
2. A verdict is stored once per PO version (fingerprint).
3. A `go` reaches nobody unless asked.
4. No real numbers in this repo.
