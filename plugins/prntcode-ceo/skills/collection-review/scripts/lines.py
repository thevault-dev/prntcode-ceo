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


def in_category(rows, category, classify, title_key="product_title"):
    kept, unnamed = [], 0
    for r in rows:
        t = r.get(title_key, "")
        if is_unnamed(t):
            unnamed += 1
            continue
        if classify(t)[0] == category:
            kept.append(r)
    return kept


# ---------- history ----------

def collection_history(category, monthly, classify, last_complete):
    """Per past collection of this category: units by month since launch (month 1 = launch month).

    A listing belongs to the latest collection that launched on or before its first sale.
    Returns a list of {name, launch, note, curve: [units month 1, month 2, …]} for collections
    with at least one month of data.
    """
    comps = sorted([c for c in MAP["collections"] if c["category"] == category], key=lambda c: c["launch"])
    if not comps:
        return []
    first_sale = {}
    by_listing = defaultdict(lambda: defaultdict(float))
    for r in monthly:
        t, m = clean_title(r["product_title"]), r["month"][:7]
        if m > last_complete:
            continue
        u = num(r["net_items_sold"])
        by_listing[t][m] += u
        if u > 0:
            first_sale[t] = min(first_sale.get(t, m), m)
    out = []
    for c in comps:
        out.append({**c, "curve_by_month": defaultdict(float), "listings": []})
    for t, months in by_listing.items():
        fs = first_sale.get(t)
        if not fs:
            continue
        owner = None
        for c in out:
            if c["launch"] <= fs:
                owner = c
        if owner is None:
            owner = out[0]
        owner["listings"].append(t)
        for m, u in months.items():
            owner["curve_by_month"][m] += u
    for c in out:
        n = month_index(last_complete) - month_index(c["launch"]) + 1
        c["curve"] = [c["curve_by_month"].get(month_str(month_index(c["launch"]) + i), 0.0) for i in range(max(n, 0))]
    return [c for c in out if c["curve"]]


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
