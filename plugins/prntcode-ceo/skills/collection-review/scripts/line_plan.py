#!/usr/bin/env python3
"""PRNTCODE Track A line plan for one product line: how many of each silhouette, and why.

Usage:
    python3 line_plan.py <data_dir> --line rtw-ss [--year 2027] [--collection "Wildflower SS27"]
                         [--growth 0.1] [--capacity 300] [--focus Wildflower] [--drop-spike] [--json plan.json]

--line is one of the lines in ../references/catalogue-map.json ("rtw-ss", "rtw-fw", "abaya-initial",
"abaya-pre-ramadan", "abaya-summer", "jalabiya", "swimwear") or an alias ("spring summer").
Each line has its own launch and selling window from the Collection Calendar, and is planned
only from its own category's history. Lines are never blended.

Reads the saved ShopifyQL results (products.json and monthly.json are required; variants.json
gives sizes, inventory.json gives sell-through and stock already made).

It plans counts, not designs, and says how far the history behind them can be trusted.
Track B is reserved as a share of units and never planned from sales.
"""
import datetime
import math
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collection_review import (  # noqa: E402
    MAP, add, aed, clean_title, is_unnamed, load, month_index, new_agg, num, p100,
    parse_title, pct, silhouette_call, table,
)
from lines import (  # noqa: E402
    LINES, collection_demand, collection_history, confidence_for, default_launch, in_category,
    launch_of, month_name, month_str, resolve_line, seasonal_demand, spike, window_for,
)

P = MAP["plan"]


def split_by_ratio(total, ratio):
    if not ratio or total <= 0:
        return {}
    w = sum(ratio.values())
    raw = {k: total * v / w for k, v in ratio.items()}
    base = {k: int(v) for k, v in raw.items()}
    for k in sorted(raw, key=lambda k: raw[k] - base[k], reverse=True)[: total - sum(base.values())]:
        base[k] += 1
    return base


def plural(word, n):
    if n == 1:
        return word
    if word.endswith("ss"):
        return word + "es"
    if word.endswith("s"):
        return word
    return word + "s"


def singular_family(f):
    f = f.lower()
    if f.endswith("sses"):
        return f[:-2]
    if f.endswith("ies"):
        return f[:-3] + "y"
    return f[:-1] if f.endswith("s") else f


def main():
    args = sys.argv[1:]
    if not args or "--line" not in args:
        print(__doc__)
        sys.exit(1)
    data_dir = args[0]

    def opt(flag, default=None, cast=str):
        return cast(args[args.index(flag) + 1]) if flag in args else default

    line_key = resolve_line(opt("--line"))
    L = LINES[line_key]
    cat = L["category"]
    year = opt("--year", None, int)
    launch = launch_of(line_key, year) if year else default_launch(line_key)
    if not launch:
        sys.exit(f"Can't place the {L['name']} launch for {year}: check ramadan_starts in catalogue-map.json.")
    window, end_note = window_for(line_key, launch)
    growth = opt("--growth", P["growth"], float)
    capacity = opt("--capacity", None, int)
    collection = opt("--collection", f"{L['name']} {launch[:4]}")
    focus = opt("--focus")
    json_out = opt("--json")

    products = load(data_dir, "products.json")
    monthly = load(data_dir, "monthly.json")
    if products is None or not monthly:
        sys.exit("products.json and monthly.json are both needed (queries 1 and 4 in SKILL.md).")
    variants = load(data_dir, "variants.json") or []
    inventory = load(data_dir, "inventory.json") or []

    ptype_of = {clean_title(r["product_title"]): r.get("product_type", "") for r in products}

    def classify(t):
        return parse_title(t, ptype_of.get(clean_title(t), ""))

    # ---------- this line's category only ----------
    other_cats = sorted({v["category"] for v in LINES.values() if v["category"] != cat})
    other_txt = ", ".join(c.lower() for c in other_cats[:-1]) + (" and " if len(other_cats) > 1 else "") + other_cats[-1].lower()
    products = in_category(products, cat, classify)
    monthly_c = in_category(monthly, cat, classify)
    variants = [r for r in variants if not is_unnamed(r.get("product_title", ""))
                and parse_title(r["product_title"], r.get("product_type", ""))[0] == cat]
    inventory_all = inventory
    inventory = in_category(inventory, cat, classify)

    this_month = datetime.date.today().strftime("%Y-%m")
    data_months = sorted({r["month"][:7] for r in monthly if r["month"][:7] < this_month})
    last_m = data_months[-1] if data_months else None
    last6 = [m for m in data_months if last_m and month_index(last_m) - month_index(m) < 6]

    # ---------- evidence ----------
    by_cat, by_sil, by_psil = new_agg(), defaultdict(new_agg), defaultdict(new_agg)
    for r in products:
        _, prnt, sil = classify(r["product_title"])
        add(by_cat, r)
        add(by_sil[sil], r)
        add(by_psil[(sil, prnt)], r)
    cat_disc = pct(by_cat["disc"], by_cat["gross"])

    cat_month, pace_first = defaultdict(float), {}
    for r in monthly_c:
        m = r["month"][:7]
        if m >= this_month:
            continue
        _, prnt, sil = classify(r["product_title"])
        u = num(r["net_items_sold"])
        cat_month[m] += u
        if u > 0:
            pace_first[(sil, prnt)] = min(pace_first.get((sil, prnt), m), m)
    first_sale_cat = min((m for m, u in cat_month.items() if u > 0), default=None)

    def months_on(sil):
        firsts = [m for k, m in pace_first.items() if k[0] == sil]
        return month_index(last_m) - month_index(min(firsts)) + 1 if firsts and last_m else None

    sold_left = defaultdict(lambda: [0.0, 0.0])
    made = defaultdict(float)
    made_titles, made_elsewhere = [], []
    for r in inventory_all:
        t = clean_title(r["product_title"])
        end = num(r["ending_inventory_units"])
        if focus and focus.lower() in t.lower() and 0 < end < MAP["placeholder_stock_units"]:
            c_, _, s_ = classify(t)
            if c_ == cat:
                made[s_] += end
                made_titles.append(f"{t} ({end:.0f})")
            else:
                made_elsewhere.append(f"{t} ({end:.0f}, {c_.lower()})")
    for r in inventory:
        t = clean_title(r["product_title"])
        if num(r["ending_inventory_units"]) >= MAP["placeholder_stock_units"]:
            continue
        if any(t.upper().startswith(x.upper()) for x in MAP["not_stock_title_prefixes"]):
            continue
        _, _, sil = classify(t)
        sold_left[sil][0] += max(num(r["inventory_units_sold"]), 0)
        sold_left[sil][1] += max(num(r["ending_inventory_units"]), 0)

    sizes = defaultdict(float)
    for r in variants:
        for part in [p.strip() for p in (r.get("product_variant_title") or "").split("/")]:
            key = next((k for k in MAP["size_words"] if k.lower() == part.lower()), None)
            if key:
                sizes[MAP["size_words"][key]] += num(r["net_items_sold"])
    order = ["XS", "Small", "Medium", "Large", "XL"]
    ratio = {z: sizes[z] for z in order if sizes.get(z, 0) > 0}

    # ---------- 1. demand over this line's window ----------
    comps, spike_info, alt_total = [], None, None
    if L["basis"] == "collection":
        comps = collection_history(cat, monthly_c, classify, last_m) if last_m else []
        if not comps:
            sys.exit(f"No past {cat.lower()} collection with sales to learn from: {L['name']} can't be planned from data. "
                     "Plan it as Track B (or a small test), or add its past collection under 'collections'.")
        per_month, observed = collection_demand(comps, len(window), drop_spike="--drop-spike" in args)
        conf = confidence_for(observed, len(comps), "collection")
        s = None if L.get("expect_launch_peak") or "--drop-spike" in args else spike(comps[-1]["curve"])
        if s:
            spike_info = s
            alt, _ = collection_demand(comps, len(window), drop_spike=True)
            alt_total = sum(u for u, _ in alt)
    else:
        per_month, run_rate = seasonal_demand(cat_month, window, data_months, first_sale_cat, last6)
        observed = month_index(last_m) - month_index(first_sale_cat) + 1 if first_sale_cat and last_m else 0
        conf = confidence_for(observed, 0, "seasonal")
    demand = sum(u for u, _ in per_month)
    C = MAP["confidence"][conf]
    st, fr, blend = P["target_sell_through"], C["first_run_share"], C["blend_equal"]
    make = demand * (1 + growth) / st
    ups = P["units_per_style"].get(cat, 10)

    # ---------- 2. silhouettes ----------
    sils = list(by_sil)
    fair = by_cat["net"] / len(sils) if sils else 0
    cand, dropped = [], []
    for sil in sils:
        v = by_sil[sil]
        disc, ret = pct(v["disc"], v["gross"]), pct(v["returned"], v["ordered"])
        mo = months_on(sil)
        call = silhouette_call(v["units"], disc, cat_disc, ret, mo, v["net"], fair, conf)
        sold, left = sold_left.get(sil, [0, 0])
        ev = {"units": v["units"], "ordered": v["ordered"], "returned": v["returned"], "disc": disc, "ret": ret,
              "months": mo, "st": pct(sold, sold + left) if (sold + left) and cat in MAP["sell_through_categories"] else None,
              "price": pct(v["gross"], v["ordered"]), "call": call}
        w = P["weight_by_call"].get(call, 0.0)
        if w <= 0:
            dropped.append((sil, ev, call))
        else:
            cand.append([sil, v["units"] * w, ev, w])
    if cand:
        tw = sum(c[1] for c in cand) or 1
        tcw = sum(c[3] for c in cand) or 1
        for c in cand:  # spread more evenly when the history is thin, still by each line's call
            c[1] = (1 - blend) * c[1] / tw + blend * c[3] / tcw
    for _ in range(3):
        tw = sum(c[1] for c in cand) or 1
        small = [c for c in cand if make * c[1] / tw < ups / 2]
        if not small or len(small) == len(cand):
            break
        for c in small:
            cand.remove(c)
            dropped.append((c[0], c[2], f"its share (~{make * c[1] / tw:.0f} units) is under half a style's {ups} units"))
    alloc = split_by_ratio(round(make), {c[0]: c[1] for c in cand})

    lines_out = []
    for sil, w, ev, _ in cand:
        units = alloc.get(sil, 0)
        styles = max(1, round(units / ups))
        pairs = []
        for (s2, prnt), v in by_psil.items():
            if s2 != sil or v["units"] < MAP["min_units_to_call"]:
                continue
            d, r_ = pct(v["disc"], v["gross"]), pct(v["returned"], v["ordered"])
            if d > cat_disc + MAP["rework_discount_margin"] or r_ > MAP["rework_returns_rate"]:
                continue
            f_ = pace_first.get((sil, prnt))
            mo = month_index(last_m) - month_index(f_) + 1 if f_ and last_m else None
            pairs.append((v["units"] / mo if mo else v["units"], prnt, v["units"]))
        pairs.sort(reverse=True)
        carry = pairs[: int(styles * P["carryover_max_share"] + 0.5)]
        already = int(min(made.get(sil, 0), units))
        first_run = max(math.ceil(units * fr) - already, 0)
        lines_out.append({"family": P["families"].get(sil, cat), "silhouette": sil, "styles": styles, "units": units,
                          "already_made": already, "first_run": first_run, "restock": units - first_run - already,
                          "sizes": split_by_ratio(first_run, ratio), "price": ev["price"],
                          "carry": [(p, u) for _, p, u in carry], "new_slots": styles - len(carry), "evidence": ev})

    fr_total = sum(l["first_run"] for l in lines_out)
    scaled = None
    if capacity and fr_total > capacity:
        scaled = capacity / fr_total
        for l in lines_out:
            l["first_run"] = max(1, math.floor(l["first_run"] * scaled))
            l["restock"] = l["units"] - l["first_run"] - l["already_made"]
            l["sizes"] = split_by_ratio(l["first_run"], ratio)
        fr_total = sum(l["first_run"] for l in lines_out)
    a_units = sum(l["units"] for l in lines_out)
    b_units = a_units / P["track_a_share"] - a_units

    # =================== output ===================
    out = []
    out.append(f"# Track A line plan · {collection}")
    out.append(f"_{L['name']} · launches {month_name(window[0])} · on sale {end_note} ({len(window)} months). "
               f"{cat} only, from {cat.lower()} sales only; {other_txt} run on their own calendars and are planned separately. "
               "Counts, not designs. Track B is reserved, never planned from sales._")

    out.append(f"\n## How much to trust this: {conf.upper()}")
    if L["basis"] == "collection":
        for c in comps:
            curve_txt = ", ".join(f"{month_name(month_str(month_index(c['launch']) + i))[:3]} {u:.0f}" for i, u in enumerate(c["curve"]))
            out.append(f"- Learned from **{c['name']}** (launched {month_name(c['launch'])}{'; ' + c['note'] if c.get('note') else ''}): "
                       f"{len(c['curve'])} months of sales so far ({curve_txt}).")
        ext = sum(1 for _, s in per_month if s == "extrapolated")
        if ext:
            out.append(f"- {collection} sells for {len(window)} months, longer than the history: it covers only the first {observed}. "
                       f"Months {observed + 1}–{len(window)} are extrapolated at the last two months' rate.")
        if spike_info:
            i, share = spike_info
            out.append(f"- **{p100(share)} of {comps[-1]['name']}'s units came in month {i + 1}** "
                       f"({month_name(month_str(month_index(comps[-1]['launch']) + i))}). The plan assumes {collection}'s month {i + 1} "
                       f"({month_name(window[i]) if i < len(window) else '–'}) gets the same push. If it doesn't, expected sales fall from "
                       f"{demand:.0f} to about {alt_total:.0f}, and units to make from {make:.0f} to about {alt_total * (1 + growth) / st:.0f}.")
        if "--drop-spike" in args:
            out.append(f"- **Peak month smoothed:** {comps[-1]['name']}'s biggest month is replaced by its median month, "
                       "as if that month was a one-off.")
        if L.get("peak_note"):
            out.append(f"- {L['peak_note']}")
    else:
        out.append(f"- {observed} months of {cat.lower()} sales; each month of the window uses the same month last year.")
    out.append({"low": f"- **What low confidence changes:** a smaller first run ({p100(fr)}, the rest held back to restock what sells), "
                       f"units spread more evenly across silhouettes, and silhouettes with under {MAP['min_units_to_call']} sales called "
                       "*unproven*, not dropped.",
                "medium": f"- **What medium confidence changes:** first run {p100(fr)}, units spread a little more evenly, thin silhouettes called *unproven*.",
                "high": f"- First run {p100(fr)}; silhouettes allocated by their sales."}[conf])

    fam = defaultdict(lambda: [0, 0, []])
    for l in lines_out:
        f = fam[l["family"]]
        f[0] += l["styles"]
        f[1] += l["units"]
        f[2].append(f"{l['styles']} {plural(l['silhouette'].lower(), l['styles'])}")
    out.append("\n## What Track A needs")
    for f_, (n, u, parts) in sorted(fam.items(), key=lambda x: -x[1][1]):
        label = f_.lower() if n != 1 else singular_family(f_)
        out.append(f"- **{n} {label}** ({', '.join(parts)}) · {u} units")
    made_total = sum(l["already_made"] for l in lines_out)
    out.append(f"- **Total:** {sum(l['styles'] for l in lines_out)} styles, {a_units} units. "
               + (f"{made_total:.0f} already made. " if made_total else "")
               + f"First run {fr_total} to make, {sum(l['restock'] for l in lines_out):.0f} held back to restock what sells.")
    out.append(f"- **Track B reserve:** about {b_units:.0f} more units ({p100(1 - P['track_a_share'])} of {collection}), "
               "planned by Hessa and the design seat without sales data.")

    out.append("\n## The line, and why")
    rows = []
    for l in lines_out:
        ev = l["evidence"]
        why = [f"{ev['call'].split(':')[0]}: sold {ev['units']:.0f}" + (f" in {ev['months']} months" if ev["months"] else ""),
               f"discount {p100(ev['disc'])} vs {p100(cat_disc)} line average"]
        if ev["returned"]:
            why.append(f"{ev['returned']:.0f} of {ev['ordered']:.0f} returned")
        if ev["st"] is not None:
            why.append(f"sell-through {p100(ev['st'])}")
        if ev["call"].startswith("Carry only if reworked"):
            why.append("fix it before it's remade: " + ev["call"].split(": ", 1)[1])
        if l["already_made"]:
            why.append(f"{l['already_made']:.0f} already made for {focus}")
        prints = ", ".join(f"{p} ({u:.0f} sold)" for p, u in l["carry"]) or "none proven yet"
        made_txt = f"{l['already_made']:.0f} made + " if l["already_made"] else ""
        rows.append([l["family"], l["silhouette"], str(l["styles"]), f"{made_txt}{l['first_run']} + {l['restock']:.0f}",
                     " / ".join(f"{k[0]} {v}" for k, v in l["sizes"].items()) or "–", f"~{aed(l['price'])}",
                     f"{len(l['carry'])} carry-over: {prints}; {l['new_slots']} new", "; ".join(why)])
    out.append(table(["Family", "Silhouette", "Styles", "Units (first run + restock)", "First-run sizes",
                      "AED (last price)", "Print slots", "Why"], rows))
    out.append(f"_A style is one silhouette in one print. Carry-over = a print that already sold well on this silhouette "
               f"({MAP['min_units_to_call']}+ units, normal discount and returns); at most {p100(P['carryover_max_share'])} of a "
               "silhouette's styles carry over, and only if Hessa keeps that print in the year's allocation. New slots are hers to fill._")
    if made_titles:
        out.append(f"_Already made for {focus}, counted against the plan: " + "; ".join(made_titles) + "._")
    if made_elsewhere:
        out.append(f"_Also named {focus} but in another line, so not counted here: " + "; ".join(made_elsewhere) + "._")

    out.append("\n## Not in Track A, and why")
    if dropped:
        rows = []
        for sil, ev, why in dropped:
            note = why
            if why.startswith("Unproven"):
                note = "Unproven: too few sales to judge. Test it as one small style, or leave it to Track B"
            elif why.startswith("Drop"):
                note = "Dropped: too few sales after 3+ months (could return as Track B)"
            rows.append([sil, f"{ev['units']:.0f}" + (f" in {ev['months']} months" if ev["months"] else ""), note])
        out.append(table(["Silhouette", "Sold", "Why not"], rows))
    else:
        out.append("Nothing left out.")

    out.append("\n## How the numbers were reached")
    rows = []
    for i, (m, (u, src)) in enumerate(zip(window, per_month)):
        if L["basis"] == "collection":
            ref = comps[-1]
            src_txt = (f"{ref['name']} month {i + 1} ({month_name(month_str(month_index(ref['launch']) + i))})"
                       if src == "observed" else "extrapolated (past the history)")
        else:
            src_txt = src
        rows.append([f"{i + 1} · {month_name(m)}", f"{u:.0f}", src_txt])
    rows.append(["**Total**", f"**{demand:.0f}**", ""])
    out.append(table(["Month of the collection", "Expected sales", "From"], rows))
    out.append(f"\nUnits to make = {demand:.0f} expected × (1 + growth {p100(growth)}) ÷ target sell-through {p100(st)} = **{make:.0f}**. "
               f"Units go to silhouettes by their sales, at half weight for *watch* and *rework* lines"
               + (f", then {p100(blend)} spread evenly because confidence is {conf}" if blend else "")
               + f". Styles = units ÷ {ups}. First run = {p100(fr)} of units, less anything already made; the rest is held back to restock.")
    if capacity:
        out.append(f"\n**Capacity:** first run capped at {capacity} units" + (f"; scaled to {p100(scaled)} of plan." if scaled else "; the plan fits."))
    else:
        out.append("\n**Capacity:** not checked. Pass `--capacity <units the team can make before launch>` once the Atelier knows its output.")

    print("\n".join(out))
    if json_out:
        import json
        json.dump({"line": line_key, "collection": collection, "window": window, "confidence": conf, "demand": demand,
                   "make": make, "lines": lines_out, "dropped": [(s, w) for s, _, w in dropped],
                   "track_a_units": a_units, "track_b_units": b_units, "first_run": fr_total},
                  open(json_out, "w"), indent=2, default=str)


if __name__ == "__main__":
    main()
