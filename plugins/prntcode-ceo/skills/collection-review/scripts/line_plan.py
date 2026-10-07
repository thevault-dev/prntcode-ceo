#!/usr/bin/env python3
"""PRNTCODE Track A line plan: how many of each silhouette the next collection needs, and why.

Usage:
    python3 line_plan.py <data_dir> --launch 2027-04 [--months 6] [--growth 0.1]
                         [--capacity 300] [--collection "Wildflower SS27"] [--json plan.json]

Reads the same saved ShopifyQL results as collection_review.py (products.json is required;
monthly.json and variants.json make the plan seasonal and sized, inventory.json adds sell-through).
Settings and their defaults live under "plan" in ../references/catalogue-map.json.

It plans counts, not designs: "4 tops: 2 long-sleeve tops, 2 smocked tops", with units,
size split, last year's price and how many print slots are carry-overs of proven pairings
versus new prints for Hessa to allocate. Every line carries the reason it is there.
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
    parse_title, pct, ratio_of_ten, silhouette_call, table,
)

P = MAP["plan"]


def month_str(idx):
    return f"{idx // 12:04d}-{idx % 12 + 1:02d}"


def month_name(m):
    return datetime.date(int(m[:4]), int(m[5:7]), 1).strftime("%b %Y")


def split_by_ratio(total, ratio):
    """Split whole units by a {size: weight} ratio, largest remainder."""
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


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)
    data_dir = args[0]

    def opt(flag, default=None, cast=str):
        return cast(args[args.index(flag) + 1]) if flag in args else default

    today = datetime.date.today()
    nxt = month_str(month_index(today.strftime("%Y-%m")) + 1)
    launch = opt("--launch", nxt)
    months = opt("--months", P["selling_months"], int)
    growth = opt("--growth", P["growth"], float)
    capacity = opt("--capacity", None, int)
    collection = opt("--collection", "the next collection")
    focus = opt("--focus")
    json_out = opt("--json")

    products = load(data_dir, "products.json")
    if products is None:
        sys.exit("products.json is missing: run query 1 in SKILL.md first.")
    monthly = load(data_dir, "monthly.json")
    if not monthly:
        sys.exit("monthly.json is missing: the line plan needs month-by-month sales (query 4 in SKILL.md) to size the selling window.")
    variants = load(data_dir, "variants.json") or []
    inventory = load(data_dir, "inventory.json") or []

    ptype_of = {clean_title(r["product_title"]): r.get("product_type", "") for r in products}

    def classify(t):
        return parse_title(t, ptype_of.get(clean_title(t), ""))

    this_month = today.strftime("%Y-%m")

    # ---------- evidence aggregates ----------
    by_cat, by_sil, by_psil = defaultdict(new_agg), defaultdict(new_agg), defaultdict(new_agg)
    for r in products:
        if is_unnamed(r["product_title"]):
            continue
        cat, prnt, sil = classify(r["product_title"])
        add(by_cat[cat], r)
        add(by_sil[(cat, sil)], r)
        add(by_psil[(cat, sil, prnt)], r)
    cat_disc = {c: pct(v["disc"], v["gross"]) for c, v in by_cat.items()}

    cat_month = defaultdict(lambda: defaultdict(float))
    first_sale, pace_first = {}, {}
    for r in monthly:
        m = r["month"][:7]
        if is_unnamed(r["product_title"]) or m >= this_month:
            continue
        cat, prnt, sil = classify(r["product_title"])
        u = num(r["net_items_sold"])
        cat_month[cat][m] += u
        if u > 0:
            first_sale[cat] = min(first_sale.get(cat, m), m)
            k = (cat, sil, prnt)
            pace_first[k] = min(pace_first.get(k, m), m)
    data_months = sorted({r["month"][:7] for r in monthly if r["month"][:7] < this_month})
    last_m = data_months[-1] if data_months else None
    last6 = [m for m in data_months if last_m and month_index(last_m) - month_index(m) < 6]

    def months_on(cat, sil):
        firsts = [m for k, m in pace_first.items() if k[0] == cat and k[1] == sil]
        return month_index(last_m) - month_index(min(firsts)) + 1 if firsts and last_m else None

    sold_left = defaultdict(lambda: [0.0, 0.0])
    made = defaultdict(float)  # stock already made for the focus collection, by (cat, sil)
    made_titles = []
    for r in inventory:
        t = clean_title(r["product_title"])
        if focus and focus.lower() in t.lower() and 0 < num(r["ending_inventory_units"]) < MAP["placeholder_stock_units"]:
            c_, _, s_ = classify(t)
            made[(c_, s_)] += num(r["ending_inventory_units"])
            made_titles.append(f"{t} ({num(r['ending_inventory_units']):.0f})")
    for r in inventory:
        t = clean_title(r["product_title"])
        if is_unnamed(t) or num(r["ending_inventory_units"]) >= MAP["placeholder_stock_units"]:
            continue
        if any(t.upper().startswith(x.upper()) for x in MAP["not_stock_title_prefixes"]):
            continue
        cat, prnt, sil = classify(t)
        sold_left[(cat, sil)][0] += max(num(r["inventory_units_sold"]), 0)
        sold_left[(cat, sil)][1] += max(num(r["ending_inventory_units"]), 0)

    # size ratio per category
    sizes = defaultdict(lambda: defaultdict(float))
    for r in variants:
        if is_unnamed(r.get("product_title", "")):
            continue
        cat, _, _ = parse_title(r.get("product_title", ""), r.get("product_type", ""))
        for part in [p.strip() for p in (r.get("product_variant_title") or "").split("/")]:
            key = next((k for k in MAP["size_words"] if k.lower() == part.lower()), None)
            if key:
                sizes[cat][MAP["size_words"][key]] += num(r["net_items_sold"])
    order = ["XS", "Small", "Medium", "Large", "XL"]
    ratio = {c: {z: s[z] for z in order if s.get(z, 0) > 0} for c, s in sizes.items()}

    # ---------- 1. demand per category over the selling window ----------
    window = [month_str(month_index(launch) + i) for i in range(months)]
    demand, basis = {}, {}
    for cat in by_cat:
        run_rate = sum(cat_month[cat].get(m, 0) for m in last6) / len(last6) if last6 else 0.0
        total, used_actual, used_rate = 0.0, [], []
        for m in window:
            ly = month_str(month_index(m) - 12)
            live = cat in first_sale and ly >= first_sale[cat] and ly in data_months
            if live:
                total += max(cat_month[cat].get(ly, 0), 0)
                used_actual.append(ly)
            else:
                total += run_rate
                used_rate.append(m)
        demand[cat] = total
        sold_months = sorted(m for m, u in cat_month[cat].items() if u > 0)
        basis[cat] = {"actual_months": used_actual, "rate_months": used_rate, "run_rate": run_rate,
                      "sold_months": sold_months}

    # ---------- 2. units to make per category ----------
    st, fr = P["target_sell_through"], P["first_run_share"]
    make = {c: demand[c] * (1 + growth) / st for c in demand}

    # ---------- 3. allocate to silhouettes ----------
    weights_by_call = P["weight_by_call"]
    lines, dropped = [], []
    for cat in sorted(by_cat, key=lambda c: -make[c]):
        sils = [k for k in by_sil if k[0] == cat]
        fair = by_cat[cat]["net"] / len(sils) if sils else 0
        ups = P["units_per_style"].get(cat, 10)
        cand = []
        for k in sils:
            v = by_sil[k]
            disc = pct(v["disc"], v["gross"])
            ret = pct(v["returned"], v["ordered"])
            mo = months_on(cat, k[1])
            call = silhouette_call(v["units"], disc, cat_disc[cat], ret, mo, v["net"], fair)
            w = weights_by_call.get(call, 0.0)
            sold, left = sold_left.get(k, [0, 0])
            ev = {"units": v["units"], "net": v["net"], "disc": disc, "ret": ret, "months": mo,
                  "st": pct(sold, sold + left) if (sold + left) and cat in MAP["sell_through_categories"] else None,
                  "price": pct(v["gross"], v["ordered"]), "call": call}
            if w <= 0:
                dropped.append((cat, k[1], ev, "dropped by the Track A rules"))
            else:
                cand.append([k[1], v["units"] * w, ev])
        if make[cat] < ups / 2:
            for sil, _, ev in cand:
                dropped.append((cat, sil, ev, f"the whole category is too small this window: about {make[cat]:.0f} units against {ups} a style"))
            continue
        # cut silhouettes too small to make one style, redistribute their units
        for _ in range(3):
            tw = sum(c[1] for c in cand)
            small = [c for c in cand if make[cat] * c[1] / tw < ups / 2]
            if not small or len(small) == len(cand):
                break
            for c in small:
                cand.remove(c)
                dropped.append((cat, c[0], c[2], f"its share (~{make[cat] * c[1] / tw:.0f} units) is under half a style's {ups} units; folded into the rest"))
        tw = sum(c[1] for c in cand)
        alloc = split_by_ratio(round(make[cat]), {c[0]: c[1] for c in cand})
        for sil, w, ev in cand:
            units = alloc.get(sil, 0)
            styles = max(1, round(units / ups))
            # proven print pairings on this silhouette
            pairs = []
            for (c2, s2, prnt), v in by_psil.items():
                if c2 != cat or s2 != sil or v["units"] < MAP["min_units_to_call"]:
                    continue
                d, r_ = pct(v["disc"], v["gross"]), pct(v["returned"], v["ordered"])
                if d > cat_disc[cat] + MAP["rework_discount_margin"] or r_ > MAP["rework_returns_rate"]:
                    continue
                first = pace_first.get((cat, sil, prnt))
                mo = month_index(last_m) - month_index(first) + 1 if first and last_m else None
                pairs.append((v["units"] / mo if mo else v["units"], prnt, v["units"], d))
            pairs.sort(reverse=True)
            max_carry = int(styles * P["carryover_max_share"] + 0.5)
            carry = pairs[:max_carry]
            already = int(min(made.get((cat, sil), 0), units))
            first_run = max(math.ceil(units * fr) - already, 0)
            lines.append({
                "category": cat, "family": P["families"].get(sil, cat), "silhouette": sil,
                "styles": styles, "units": units, "already_made": already, "first_run": first_run,
                "restock": units - first_run - already,
                "sizes": split_by_ratio(first_run, ratio.get(cat, {})),
                "price": ev["price"], "carry": [(p, u, d) for _, p, u, d in carry],
                "new_slots": styles - len(carry), "evidence": ev, "share": w / tw,
            })

    # ---------- 4. capacity ----------
    fr_total = sum(l["first_run"] for l in lines)
    scaled = None
    if capacity and fr_total > capacity:
        scaled = capacity / fr_total
        for l in lines:
            l["first_run"] = max(1, math.floor(l["first_run"] * scaled))
            l["restock"] = l["units"] - l["first_run"] - l["already_made"]
            l["sizes"] = split_by_ratio(l["first_run"], ratio.get(l["category"], {}))
        fr_total = sum(l["first_run"] for l in lines)

    a_units = sum(l["units"] for l in lines)
    total_units = a_units / P["track_a_share"] if P["track_a_share"] else a_units
    b_units = total_units - a_units

    # =================== output ===================
    out = []
    w0, w1 = month_name(window[0]), month_name(window[-1])
    out.append(f"# Track A line plan · {collection}")
    out.append(f"_Selling window {w0} – {w1} ({months} months). Counts, not designs. Built from prior sales; directional. Track B is reserved, never planned from sales._")

    # headline: "you need 3 tops"
    fam = defaultdict(lambda: [0, 0, []])
    for l in lines:
        f = fam[(l["category"], l["family"])]
        f[0] += l["styles"]
        f[1] += l["units"]
        f[2].append(f"{l['styles']} {plural(l['silhouette'].lower(), l['styles'])}")
    out.append("\n## What Track A needs")
    for (cat, f_), (n, u, parts) in sorted(fam.items(), key=lambda x: -x[1][1]):
        label = f_.lower()
        if n == 1:
            label = label[:-2] if label.endswith("sses") else label[:-3] + "y" if label.endswith("ies") else label[:-1] if label.endswith("s") else label
        out.append(f"- **{n} {label}** ({', '.join(parts)}) · {u} units")
    made_total = sum(l["already_made"] for l in lines)
    out.append(f"- **Total:** {sum(l['styles'] for l in lines)} styles, {a_units} units. "
               + (f"{made_total:.0f} already made. " if made_total else "")
               + f"First run {fr_total} to make, {sum(l['restock'] for l in lines):.0f} held back to restock what sells.")
    out.append(f"- **Track B reserve:** about {b_units:.0f} more units ({p100(1 - P['track_a_share'])} of the collection), planned by Hessa and the design seat without sales data.")

    out.append("\n## The line, and why")
    rows = []
    for l in lines:
        ev = l["evidence"]
        why = [f"{ev['call'].split(':')[0]}: sold {ev['units']:.0f}", f"discount {p100(ev['disc'])} vs {p100(cat_disc[l['category']])} category"]
        if ev["ret"]:
            why.append(f"returns {p100(ev['ret'])}")
        if ev["st"] is not None:
            why.append(f"sell-through {p100(ev['st'])}")
        if ev["call"].startswith("Carry only if reworked"):
            why.append("fix it before it's remade: " + ev["call"].split(": ", 1)[1])
        prints = ", ".join(f"{p} ({u:.0f} sold)" for p, u, _ in l["carry"]) or "none proven yet"
        size_txt = " / ".join(f"{k[0]} {v}" for k, v in l["sizes"].items()) or "–"
        if l["already_made"]:
            why.append(f"{l['already_made']:.0f} already made for {focus}")
        made_txt = f"{l['already_made']:.0f} made + " if l["already_made"] else ""
        rows.append([l["family"], l["silhouette"], str(l["styles"]), f"{made_txt}{l['first_run']} + {l['restock']:.0f}",
                     size_txt, f"~{aed(l['price'])}", f"{len(l['carry'])} carry-over: {prints}; {l['new_slots']} new",
                     "; ".join(why)])
    out.append(table(["Family", "Silhouette", "Styles", "Units (first run + restock)", "First-run sizes", "AED (last year)", "Print slots", "Why"], rows))
    out.append("_A style is one silhouette in one print. Carry-over = a print that already sold well on this silhouette (at least 5 units, normal discount and returns); "
               f"at most {p100(P['carryover_max_share'])} of a silhouette's styles carry over so the collection stays new. A carry-over holds only if Hessa keeps that print in the year's allocation; otherwise it becomes a new slot. New slots are for Hessa's print allocation._")
    if made_titles:
        out.append(f"_Already made for {focus}, counted against the plan: " + "; ".join(made_titles) + "._")

    out.append("\n## Not in Track A, and why")
    if dropped:
        out.append(table(["Category", "Silhouette", "Sold", "Why not"],
                         [[c, s, f"{ev['units']:.0f}", why if why != "dropped by the Track A rules" else ev["call"]] for c, s, ev, why in dropped]))
    for cat in by_cat:
        if not any(l["category"] == cat for l in lines) and not any(d[0] == cat for d in dropped):
            out.append(f"- {cat}: nothing to plan.")
    for cat, b in basis.items():
        if make.get(cat, 0) < P["units_per_style"].get(cat, 10) / 2 and b["sold_months"]:
            out.append(f"- **{cat}** sold only in {', '.join(month_name(m) for m in b['sold_months'])}, outside this window. Plan it for the window it sells in (a separate drop), not here.")

    out.append("\n## How the numbers were reached")
    rows = []
    for cat in sorted(make, key=lambda c: -make[c]):
        b = basis[cat]
        src = []
        if b["actual_months"]:
            src.append(f"same months last year ({month_name(b['actual_months'][0])} – {month_name(b['actual_months'][-1])})")
        if b["rate_months"]:
            src.append(f"{len(b['rate_months'])} month(s) at the last-6-months rate of {b['run_rate']:.1f}/month (no sales history for those months)")
        rows.append([cat, f"{demand[cat]:.0f}", " + ".join(src) or "–", f"{make[cat]:.0f}"])
    out.append(table(["Category", "Expected sales in window", "Based on", "Units to make"], rows))
    out.append(f"\nUnits to make = expected sales × (1 + growth {p100(growth)}) ÷ target sell-through {p100(st)}. "
               f"Units go to silhouettes by last year's units, with weight {weights_by_call.get('Watch')} for *watch* and *rework* silhouettes. "
               f"Styles = units ÷ {', '.join(f'{v} per {k.lower()} style' for k, v in P['units_per_style'].items())}. "
               f"First run = {p100(fr)} of units; the rest is held back to restock, which in-house production allows without minimum orders.")
    if capacity:
        out.append(f"\n**Capacity:** first run capped at {capacity} units (the team's capacity before launch)"
                   + (f"; scaled down to {p100(scaled)} of plan." if scaled else "; the plan fits."))
    else:
        out.append("\n**Capacity:** not checked. Pass `--capacity <units the team can make before launch>` once the Atelier knows its weekly output.")
    out.append("\nAll settings are in `references/catalogue-map.json` under `plan`, and can be overridden per run.")

    print("\n".join(out))
    if json_out:
        import json
        json.dump({"collection": collection, "window": window, "lines": lines, "dropped": [(c, s, w) for c, s, _, w in dropped],
                   "track_a_units": a_units, "track_b_units": b_units, "first_run": fr_total, "demand": demand, "make": make},
                  open(json_out, "w"), indent=2, default=str)


if __name__ == "__main__":
    main()
