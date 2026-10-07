#!/usr/bin/env python3
"""Line schedules, collection history and confidence for the PRNTCODE collection review.

Each product line (RTW spring/summer, RTW fall/winter, the abaya drops, jalabiyas…) runs on
its own calendar, set under "lines" in ../references/catalogue-map.json. A plan is always for
one line, against that line's own history. Lines are never blended.

Two ways a line learns from the past:
- "collection": line the new collection up against past collections of the same category by
  months since launch (month 1 = launch month), not by calendar month. Right for RTW and
  jalabiyas, whose sales depend on when a collection launched.
- "seasonal": use the same calendar months last year. Right for abayas, which sell all year.
"""
import datetime
from collections import defaultdict

from collection_review import MAP, clean_title, is_unnamed, month_index, num

LINES = MAP["lines"]


def month_str(idx):
    return f"{idx // 12:04d}-{idx % 12 + 1:02d}"


def month_name(m):
    return datetime.date(int(m[:4]), int(m[5:7]), 1).strftime("%b %Y")


def ramadan_start(year):
    s = MAP["ramadan_starts"].get(str(year))
    return datetime.date.fromisoformat(s) if s else None


def launch_of(line_key, year):
    """The launch month of a line in a given year, or None."""
    L = LINES[line_key]
    if "launch_month" in L:
        return f"{year:04d}-{L['launch_month']:02d}"
    if L.get("launch") == "pre-ramadan":
        d = ramadan_start(year)
        if d:
            return (d - datetime.timedelta(days=7)).strftime("%Y-%m")
    return None


def next_launch(line_key, after):
    """First launch of a line strictly after the month `after`."""
    y0 = int(after[:4])
    for y in range(y0, y0 + 3):
        m = launch_of(line_key, y)
        if m and m > after:
            return m
    return None


def default_launch(line_key, today=None):
    today = today or datetime.date.today()
    return next_launch(line_key, today.strftime("%Y-%m"))


def window_for(line_key, launch):
    """Months the collection is on sale: launch until the line's next launch (or a fixed length)."""
    L = LINES[line_key]
    if "window_months" in L:
        n = L["window_months"]
        end_note = f"through {L['window_note']}" if L.get("window_note") else "for a fixed window"
    else:
        end = next_launch(L["ends_at_line"], launch)
        n = month_index(end) - month_index(launch)
        end_note = f"until the {LINES[L['ends_at_line']]['name']} launch in {month_name(end)}"
    return [month_str(month_index(launch) + i) for i in range(n)], end_note


def resolve_line(key_or_name):
    k = key_or_name.lower().strip()
    if k in LINES:
        return k
    for key, L in LINES.items():
        if k == L["name"].lower() or k in [a.lower() for a in L.get("aliases", [])]:
            return key
    raise SystemExit(f"Unknown line '{key_or_name}'. Known: " + ", ".join(LINES))


def line_categories(line_key):
    L = LINES[line_key]
    return L.get("categories", [L["category"]])


def in_category(rows, categories, classify, title_key="product_title"):
    """Rows whose listing belongs to one of the categories (a string or a list). Unnamed rows are dropped."""
    cats = {categories} if isinstance(categories, str) else set(categories)
    kept = []
    for r in rows:
        t = r.get(title_key, "")
        if is_unnamed(t):
            continue
        if classify(t)[0] in cats:
            kept.append(r)
    return kept


# ---------- the Ops App (PRNTCODE-ops) ----------

def load_ops(data_dir):
    """ops.json from the Ops App, or None. Products may come as rows with a products_columns header."""
    import json
    import os
    path = os.path.join(data_dir, "ops.json")
    if not os.path.exists(path):
        return None
    d = json.load(open(path))
    if d.get("products") and isinstance(d["products"][0], list):
        cols = d.get("products_columns", ["product_title", "product_type", "collection_id", "print_id", "made_to_order"])
        d["products"] = [dict(zip(cols, r)) for r in d["products"]]
    return d


def ops_collection_by_name(ops, name):
    """An Ops App collection whose name appears in `name` (or the reverse), e.g. 'Wildflower SS27' → WLDFLWR."""
    if not ops or not name:
        return None
    n = name.lower()
    for c in ops.get("collections", []):
        cn = c["name"].lower()
        if cn in n or n in cn:
            return c
    return None


# ---------- history ----------

def _curves(comps, monthly, last_complete, owner_of):
    """Units by month since launch for each collection. Sales before launch fold into month 1."""
    by = {c["name"]: defaultdict(float) for c in comps}
    pre = defaultdict(float)
    launch_of_c = {c["name"]: c["launch"] for c in comps}
    for r in monthly:
        t, m = clean_title(r["product_title"]), r["month"][:7]
        if m > last_complete:
            continue
        owner = owner_of(t)
        if owner is None:
            continue
        u = num(r["net_items_sold"])
        if m < launch_of_c[owner]:
            pre[owner] += u
            m = launch_of_c[owner]
        by[owner][m] += u
    out = []
    for c in comps:
        n = month_index(last_complete) - month_index(c["launch"]) + 1
        if n <= 0:
            continue
        curve = [by[c["name"]].get(month_str(month_index(c["launch"]) + i), 0.0) for i in range(n)]
        if sum(curve) <= 0:
            continue
        out.append({**c, "curve": curve, "prelaunch": pre[c["name"]]})
    return out


def collection_history(categories, monthly, classify, last_complete, ops=None):
    """Per past collection of these categories: units by month since launch (month 1 = launch month).

    With the Ops App (ops.json), a listing belongs to the collection the Ops App gives it, and launch
    and close dates come from there. Without it, the 'collections' list in the catalogue map is used,
    and a listing belongs to the latest collection that launched on or before its first sale.
    Sales before a collection's launch (a pre-launch or soft launch) count towards month 1.
    """
    cats = {categories} if isinstance(categories, str) else set(categories)
    type_to_cat = MAP["category_from_product_type"]
    if ops and ops.get("collections") and ops.get("products"):
        coll_of, types_of = {}, defaultdict(set)
        for p in ops["products"]:
            if p.get("collection_id"):
                coll_of[clean_title(p["product_title"])] = p["collection_id"]
                types_of[p["collection_id"]].add(type_to_cat.get((p.get("product_type") or "").upper(), p.get("product_type")))
        comps = []
        for c in sorted(ops["collections"], key=lambda c: c["launch_date"] or "9999"):
            if not c.get("launch_date") or not (types_of[c["collection_id"]] & cats):
                continue
            if c["launch_date"][:7] > last_complete:
                continue
            comps.append({"name": c["name"], "id": c["collection_id"], "launch": c["launch_date"][:7],
                          "sunset": (c.get("sunset_date") or "")[:7] or None, "source": "Ops App",
                          "note": f"launched {c['launch_date']}" + (f", closes {c['sunset_date']}" if c.get("sunset_date") else "")})
        name_of = {c["id"]: c["name"] for c in comps}

        def owner_of(t):
            if classify(t)[0] not in cats:
                return None
            return name_of.get(coll_of.get(t))
        found = _curves(comps, monthly, last_complete, owner_of)
        if found:
            return found
        # the Ops App has no collection for these categories yet: fall back to the catalogue map

    comps = sorted([c for c in MAP["collections"] if c["category"] in cats], key=lambda c: c["launch"])
    if not comps:
        return []
    first_sale = {}
    for r in monthly:
        t, m = clean_title(r["product_title"]), r["month"][:7]
        if num(r["net_items_sold"]) > 0 and classify(t)[0] in cats:
            first_sale[t] = min(first_sale.get(t, m), m)

    def owner_of(t):
        fs = first_sale.get(t)
        if not fs or classify(t)[0] not in cats:
            return None
        owner = comps[0]["name"]
        for c in comps:
            if c["launch"] <= fs:
                owner = c["name"]
        return owner
    return _curves([{**c, "source": "catalogue map"} for c in comps], monthly, last_complete, owner_of)


def confidence_for(months_observed, n_collections, basis):
    """How far the history can be trusted: low, medium or high."""
    if basis == "seasonal":
        return "high" if months_observed >= 12 else "medium" if months_observed >= 6 else "low"
    if n_collections >= 2 and months_observed >= 6:
        return "high"
    if months_observed >= 6:
        return "medium"
    return "low"


def spike(curve):
    """(index, share) of a month carrying more than half a curve's units, else None."""
    tot = sum(curve)
    if tot <= 0 or len(curve) < 2:
        return None
    i = max(range(len(curve)), key=lambda k: curve[k])
    share = curve[i] / tot
    return (i, share) if share > MAP["spike_share"] else None


def collection_demand(comps, window_len, drop_spike=False):
    """Expected units for each month of the new window, lined up by months since launch.

    Months the past collections reached are averaged across them. Later months are
    extrapolated at the latest collection's tail rate (mean of its last two observed months).
    Returns (per-month list of (units, source)), months observed.
    """
    curves = []
    for c in comps:
        cv = list(c["curve"])
        if drop_spike:
            s = spike(cv)
            if s:
                others = sorted(v for k, v in enumerate(cv) if k != s[0])
                cv[s[0]] = others[len(others) // 2] if others else cv[s[0]]
        curves.append(cv)
    observed = max(len(cv) for cv in curves)
    latest = curves[-1]
    tail = sum(latest[-2:]) / len(latest[-2:])
    months = []
    for i in range(window_len):
        vals = [cv[i] for cv in curves if i < len(cv)]
        if vals:
            months.append((sum(vals) / len(vals), "observed"))
        else:
            months.append((tail, "extrapolated"))
    return months, observed


def seasonal_demand(category_month, window, data_months, first_sale, last6):
    """Expected units per window month from the same month last year (run rate where there's no history)."""
    run_rate = sum(category_month.get(m, 0) for m in last6) / len(last6) if last6 else 0.0
    months = []
    for m in window:
        ly = month_str(month_index(m) - 12)
        if first_sale and ly >= first_sale and ly in data_months:
            months.append((max(category_month.get(ly, 0), 0), f"same month last year ({month_name(ly)})"))
        else:
            months.append((run_rate, "last-6-months rate"))
    return months, run_rate
