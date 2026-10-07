#!/usr/bin/env python3
"""PRNTCODE Track A line plan for one product line: what to make, how many, from which fabric, and why.

Usage:
    python3 line_plan.py <data_dir> --line rtw-ss [--year 2027] [--collection "Wildflower SS27"]
                         [--growth 0.1] [--capacity 300] [--prints 7] [--focus Wildflower]
                         [--drop-spike] [--json plan.json]

--line is one of the lines in ../references/catalogue-map.json or an alias ("spring summer").
Each line runs on its own calendar and is planned only from its own categories' sales
(RTW lines include their accessories, which come from the same fabrics). Lines are never blended.

Reads the saved ShopifyQL results (products.json and monthly.json required; variants.json gives
sizes, inventory.json gives sell-through and stock already made) and, when present, ops.json from
the Ops App (collections and their dates, which listing belongs to which collection, fabric stock
and metres per piece).

The plan is built holistically for in-house production: how many units the line can sell, spread
wide and shallow across silhouettes, small test runs for unproven shapes, then grouped into print
stories so each fabric makes a set of pieces that work together, with accessories from its offcuts.
Counts, not designs. Track B is reserved as a share of units and never planned from sales.
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
    launch_of, line_categories, load_ops, month_name, month_str, ops_collection_by_name, resolve_line,
    seasonal_demand, spike, window_for,
)

P = MAP["plan"]
CODES = MAP.get("print_codes", {})


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
    if word.endswith("scarf"):
        return word[:-1] + "ves"
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
    cats = line_categories(line_key)
    main_cat = L["category"]
    ops = load_ops(data_dir)
    collection = opt("--collection")
    ops_new = ops_collection_by_name(ops, collection) if collection else None
    year = opt("--year", None, int)

    # launch and window: the Ops App's dates for this collection if it has them, else the line's calendar
    if ops_new and ops_new.get("launch_date"):
        launch = ops_new["launch_date"][:7]
    else:
        launch = launch_of(line_key, year) if year else default_launch(line_key)
    if not launch:
        sys.exit(f"Can't place the {L['name']} launch for {year}: check ramadan_starts in catalogue-map.json.")
    window, end_note = window_for(line_key, launch)
    if ops_new and ops_new.get("sunset_date"):
        end = ops_new["sunset_date"][:7]
        window = [month_str(month_index(launch) + i) for i in range(month_index(end) - month_index(launch) + 1)]
        end_note = f"until it closes on {ops_new['sunset_date']} (Ops App)"
    collection = collection or f"{L['name']} {launch[:4]}"
    launch_txt = (f"launches {ops_new['launch_date']} (Ops App)" if ops_new and ops_new.get("launch_date")
                  else f"launches {month_name(window[0])}")
    growth = opt("--growth", P["growth"], float)
    capacity = opt("--capacity", None, int)
    focus = opt("--focus")
    json_out = opt("--json")

    products = load(data_dir, "products.json")
    monthly = load(data_dir, "monthly.json")
    if products is None or not monthly:
        sys.exit("products.json and monthly.json are both needed (queries 1 and 4 in SKILL.md).")
    variants = load(data_dir, "variants.json") or []
    inventory_all = load(data_dir, "inventory.json") or []

    ptype_of = {clean_title(r["product_title"]): r.get("product_type", "") for r in products}

    def classify(t):
        return parse_title(t, ptype_of.get(clean_title(t), ""))

    # ---------- this line's categories only ----------
    products = in_category(products, cats, classify)
    monthly_c = in_category(monthly, cats, classify)
    variants = [r for r in variants if not is_unnamed(r.get("product_title", ""))
                and parse_title(r["product_title"], r.get("product_type", ""))[0] in cats]
    inventory = in_category(inventory_all, cats, classify)

    this_month = datetime.date.today().strftime("%Y-%m")
    data_months = sorted({r["month"][:7] for r in monthly if r["month"][:7] < this_month})
    last_m = data_months[-1] if data_months else None
    last6 = [m for m in data_months if last_m and month_index(last_m) - month_index(m) < 6]

    # ---------- evidence ----------
    by_line, by_sil, by_psil, by_print = new_agg(), defaultdict(new_agg), defaultdict(new_agg), defaultdict(new_agg)
    cat_of_sil = {}
    for r in products:
        c, prnt, sil = classify(r["product_title"])
        add(by_line, r)
        add(by_sil[sil], r)
        add(by_psil[(sil, prnt)], r)
        if c == main_cat:
            add(by_print[prnt], r)
        cat_of_sil[sil] = c
    line_disc = pct(by_line["disc"], by_line["gross"])

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

    def months_on(sil=None, prnt=None):
        firsts = [m for k, m in pace_first.items() if (sil is None or k[0] == sil) and (prnt is None or k[1] == prnt)]
        return month_index(last_m) - month_index(min(firsts)) + 1 if firsts and last_m else None

    sold_left = defaultdict(lambda: [0.0, 0.0])
    made, made_titles, made_elsewhere = defaultdict(float), [], []
    for r in inventory_all:
        t = clean_title(r["product_title"])
        end_u = num(r["ending_inventory_units"])
        if focus and focus.lower() in t.lower() and 0 < end_u < MAP["placeholder_stock_units"]:
            c_, _, s_ = classify(t)
            if c_ in cats:
                made[s_] += end_u
                made_titles.append(f"{t} ({end_u:.0f})")
            else:
                made_elsewhere.append(f"{t} ({end_u:.0f}, {c_.lower()})")
    for r in inventory:
        t = clean_title(r["product_title"])
        if num(r["ending_inventory_units"]) >= MAP["placeholder_stock_units"]:
            continue
        if any(t.upper().startswith(x.upper()) for x in MAP["not_stock_title_prefixes"]):
            continue
        _, _, sil = classify(t)
        sold_left[sil][0] += max(num(r["inventory_units_sold"]), 0)
        sold_left[sil][1] += max(num(r["ending_inventory_units"]), 0)

    sizes = defaultdict(lambda: defaultdict(float))
    for r in variants:
        c = parse_title(r["product_title"], r.get("product_type", ""))[0]
        for part in [p.strip() for p in (r.get("product_variant_title") or "").split("/")]:
            key = next((k for k in MAP["size_words"] if k.lower() == part.lower()), None)
            if key:
                sizes[c][MAP["size_words"][key]] += num(r["net_items_sold"])
    order = ["XS", "Small", "Medium", "Large", "XL"]
    ratio = {c: {z: s[z] for z in order if s.get(z, 0) > 0} for c, s in sizes.items()}

    # ---------- 1. how many units the line can sell in the window ----------
    comps, spike_info, alt_total = [], None, None
    if L["basis"] == "collection":
        comps = collection_history(cats, monthly_c, classify, last_m, ops) if last_m else []
        if not comps:
            sys.exit(f"No past {main_cat.lower()} collection with sales to learn from: {L['name']} can't be planned from data. "
                     "Plan it as Track B (or a small test), or add its past collection under 'collections'.")
        per_month, observed = collection_demand(comps, len(window), drop_spike="--drop-spike" in args)
        conf = confidence_for(observed, len(comps), "collection")
        s = None if L.get("expect_launch_peak") or "--drop-spike" in args else spike(comps[-1]["curve"])
        if s:
            spike_info = s
            alt, _ = collection_demand(comps, len(window), drop_spike=True)
            alt_total = sum(u for u, _ in alt)
    else:
        per_month, _ = seasonal_demand(cat_month, window, data_months, first_sale_cat, last6)
        observed = month_index(last_m) - month_index(first_sale_cat) + 1 if first_sale_cat and last_m else 0
        conf = confidence_for(observed, 0, "seasonal")
    demand = sum(u for u, _ in per_month)
    C = MAP["confidence"][conf]
    st, fr, blend = P["target_sell_through"], C["first_run_share"], C["blend_equal"]
    make = demand * (1 + growth) / st

    # ---------- 2. silhouettes: wide and shallow ----------
    sils = list(by_sil)
    fair = by_line["net"] / len(sils) if sils else 0
    cand, dropped, tests = [], [], []
    for sil in sils:
        v = by_sil[sil]
        disc, ret = pct(v["disc"], v["gross"]), pct(v["returned"], v["ordered"])
        mo = months_on(sil=sil)
        call = silhouette_call(v["units"], disc, line_disc, ret, mo, v["net"], fair, conf)
        sold, left = sold_left.get(sil, [0, 0])
        c = cat_of_sil[sil]
        ev = {"units": v["units"], "ordered": v["ordered"], "returned": v["returned"], "disc": disc, "ret": ret,
              "months": mo, "st": pct(sold, sold + left) if (sold + left) and c in MAP["sell_through_categories"] else None,
              "price": pct(v["gross"], v["ordered"]), "call": call, "category": c}
        w = P["weight_by_call"].get(call, 0.0)
        if call.startswith("Unproven"):
            tests.append((sil, ev))
        elif w <= 0:
            dropped.append((sil, ev, call))
        else:
            cand.append([sil, v["units"] * w, ev, w])
    if cand:
        tw = sum(c[1] for c in cand) or 1
        tcw = sum(c[3] for c in cand) or 1
        for c in cand:  # spread more evenly when the history is thin, still by each line's call
            c[1] = (1 - blend) * c[1] / tw + blend * c[3] / tcw

    def ups(sil):
        return P["units_per_style"].get(cat_of_sil.get(sil, main_cat), 5)

    for _ in range(3):
        tw = sum(c[1] for c in cand) or 1
        small = [c for c in cand if make * c[1] / tw < ups(c[0]) / 2]
        if not small or len(small) == len(cand):
            break
        for c in small:
            cand.remove(c)
            dropped.append((c[0], c[2], f"its share (~{make * c[1] / tw:.0f} units) is under half a style"))
    alloc = split_by_ratio(round(make), {c[0]: c[1] for c in cand})

    # tests: unproven shapes get one small run each, in-house makes this cheap
    tests.sort(key=lambda x: -x[1]["units"])
    test_lines = tests[: P["max_test_styles"]]
    for sil, ev in tests[P["max_test_styles"]:]:
        dropped.append((sil, ev, "Unproven, and past the test limit: leave it to Track B"))

    lines_out = []
    for sil, w, ev, _ in cand:
        units = alloc.get(sil, 0)
        styles = max(1, round(units / ups(sil)))
        already = int(min(made.get(sil, 0), units))
        first_run = max(math.ceil(units * fr) - already, 0)
        lines_out.append({"family": P["families"].get(sil, ev["category"]), "silhouette": sil, "category": ev["category"],
                          "styles": styles, "units": units, "already_made": already, "first_run": first_run,
                          "restock": units - first_run - already, "test": False,
                          "sizes": split_by_ratio(first_run, ratio.get(ev["category"], {})), "price": ev["price"], "evidence": ev})
    for sil, ev in test_lines:
        u = P["test_style_units"]
        lines_out.append({"family": P["families"].get(sil, ev["category"]), "silhouette": sil, "category": ev["category"],
                          "styles": 1, "units": u, "already_made": 0, "first_run": u, "restock": 0, "test": True,
                          "sizes": split_by_ratio(u, ratio.get(ev["category"], {})), "price": ev["price"], "evidence": ev})

    # ---------- 3. print stories: which pieces each fabric makes ----------
    last_prints = set()
    if ops and comps:
        last_id = comps[-1].get("id")
        for p_ in ops.get("products", []):
            if p_.get("collection_id") == last_id and p_.get("print_id"):
                last_prints.add(p_["print_id"])
    n_prints = opt("--prints", None, int) or P.get("prints_per_collection") or len(last_prints) or len(by_print) or 5
    ranked = []
    for prnt, v in by_print.items():
        mo = months_on(prnt=prnt)
        if v["units"] >= MAP["min_units_to_call"] and pct(v["disc"], v["gross"]) <= line_disc + MAP["rework_discount_margin"]:
            ranked.append((v["units"] / mo if mo else v["units"], prnt, v))
    ranked.sort(reverse=True)
    carried = [p for _, p, _ in ranked[: int(n_prints * P["carryover_max_share"] + 0.5)]]
    stories = [{"print": p, "carry": True, "pieces": [], "units": 0,
                "why": f"carry-over: sold {by_print[p]['units']:.0f} {main_cat.lower()} pieces at {p100(pct(by_print[p]['disc'], by_print[p]['gross']))} discount"}
               for p in carried]
    for i in range(n_prints - len(carried)):
        stories.append({"print": f"New print {chr(65 + i)}", "carry": False, "pieces": [], "units": 0,
                        "why": "new: Hessa allocates it from the print workstream"})

    def proven_on(prnt, sil):
        v = by_psil.get((sil, prnt))
        return v["units"] if v else 0

    garments = [l for l in lines_out if l["category"] == main_cat]
    extras = [l for l in lines_out if l["category"] != main_cat]
    g_styles = sum(l["styles"] for l in garments)
    n_wanted = n_prints
    n_prints = max(1, min(n_prints, g_styles // P.get("min_styles_per_print", 4) or 1))
    if n_prints < n_wanted:  # too few styles for every print to be a set: keep the strongest carried prints and fewer new ones
        n_carry = min(len(carried), max(1, int(n_prints * P["carryover_max_share"] + 0.5)))
        stories = [s_ for s_ in stories if s_["carry"]][:n_carry] + [s_ for s_ in stories if not s_["carry"]][: n_prints - n_carry]
    per_print = math.ceil(g_styles / n_prints)
    fam_count = lambda s, fam: sum(1 for x in s["pieces"] if x["family"] == fam)  # noqa: E731
    for l in sorted(garments, key=lambda l: (l["test"], -l["styles"])):
        per = [l["units"] // l["styles"] + (1 if i < l["units"] % l["styles"] else 0) for i in range(l["styles"])]
        for u in per:
            best = min(stories, key=lambda s: (
                sum(1 for x in s["pieces"] if x["silhouette"] == l["silhouette"]),  # one of each shape per print first
                sum(1 for x in s["pieces"] if x["family"] != "Accessories") >= per_print,  # fill prints evenly
                -proven_on(s["print"], l["silhouette"]) if s["carry"] else 0,     # then a carried print where it already sold
                fam_count(s, l["family"]),                                          # spread families: tops and bottoms in every print
                s["units"]))
            best["pieces"].append({"silhouette": l["silhouette"], "family": l["family"], "units": u, "test": l["test"]})
            best["units"] += u
    for l in extras:  # accessories: from the offcuts of the prints with the most garments
        per = [l["units"] // l["styles"] + (1 if i < l["units"] % l["styles"] else 0) for i in range(l["styles"])]
        for u in per:
            best = min(stories, key=lambda s: (any(x["silhouette"] == l["silhouette"] for x in s["pieces"]), -s["units"]))
            best["pieces"].append({"silhouette": l["silhouette"], "family": l["family"], "units": u, "test": l["test"]})
            best["units"] += u
    stories = [s for s in stories if s["pieces"]]

    # fabric on hand, by print (Ops App materials of kind 'fabric')
    fabric_by_print, yields = defaultdict(float), {}
    if ops:
        for f in ops.get("fabric", []):
            text = f"{f.get('material_id', '')} {f.get('name', '')}".upper()
            for code, name in CODES.items():
                if code in text or name.upper() in text:
                    fabric_by_print[name] += num(f.get("on_hand"))
                    break
        for y in ops.get("yields", []):
            _, _, sil = classify(y["product_title"])
            yields.setdefault(sil, []).append(num(y.get("per_unit")))
    yields = {k: sum(v) / len(v) for k, v in yields.items() if v}

    # ---------- capacity ----------
    fr_total = sum(l["first_run"] for l in lines_out)
    scaled = None
    if capacity and fr_total > capacity:
        scaled = capacity / fr_total
        for l in lines_out:
            if l["test"]:
                continue
            l["first_run"] = max(1, math.floor(l["first_run"] * scaled))
            l["restock"] = l["units"] - l["first_run"] - l["already_made"]
            l["sizes"] = split_by_ratio(l["first_run"], ratio.get(l["category"], {}))
        fr_total = sum(l["first_run"] for l in lines_out)
    core = [l for l in lines_out if not l["test"]]
    a_units = sum(l["units"] for l in core)
    t_units = sum(l["units"] for l in lines_out if l["test"])
    b_units = a_units / P["track_a_share"] - a_units

    # =================== output ===================
    out = []
    other_cats = sorted({v["category"] for v in LINES.values() if v["category"] not in cats})
    other_txt = ", ".join(c.lower() for c in other_cats[:-1]) + (" and " if len(other_cats) > 1 else "") + other_cats[-1].lower()
    out.append(f"# Track A line plan · {collection}")
    out.append(f"_{L['name']} · {launch_txt} · on sale {end_note} ({len(window)} months). "
               f"{' and '.join(c.lower() for c in cats)} only, from their own sales; {other_txt} run on their own calendars. "
               "Counts, not designs. Track B is reserved, never planned from sales._")
    if L.get("accessories_note") and len(cats) > 1:
        out.append(f"_{L['accessories_note']}_")

    out.append(f"\n## How much to trust this: {conf.upper()}")
    if L["basis"] == "collection":
        for c in comps:
            curve_txt = ", ".join(f"{month_name(month_str(month_index(c['launch']) + i))[:3]} {u:.0f}" for i, u in enumerate(c["curve"]))
            pre_txt = f", including {c['prelaunch']:.0f} sold before launch" if c.get("prelaunch") else ""
            out.append(f"- Learned from **{c['name']}** ({c.get('note') or 'launched ' + month_name(c['launch'])}; {c.get('source', '')}): "
                       f"{len(c['curve'])} months on sale so far ({curve_txt}{pre_txt}).")
        if any(s_ == "extrapolated" for _, s_ in per_month):
            out.append(f"- {collection} sells for {len(window)} months, longer than that history, which covers only its first {observed}. "
                       f"Months {observed + 1}–{len(window)} are extrapolated at the last two months' rate.")
        if spike_info:
            i, share = spike_info
            where = "its launch month" if i == 0 else f"month {i + 1}"
            out.append(f"- **{p100(share)} of {comps[-1]['name']}'s units sold in {where}.** The plan assumes {collection} gets the same "
                       f"push in its {where if i else 'launch month'} ({month_name(window[i]) if i < len(window) else '–'}). With a quieter launch, "
                       f"expected sales fall from {demand:.0f} to about {alt_total:.0f}, and units to make from {make:.0f} to about {alt_total * (1 + growth) / st:.0f}.")
        if "--drop-spike" in args:
            out.append(f"- **Quieter-launch reading:** {comps[-1]['name']}'s biggest month is replaced by its median month.")
        if L.get("peak_note"):
            out.append(f"- {L['peak_note']}")
    else:
        out.append(f"- {observed} months of {main_cat.lower()} sales; each month of the window uses the same month last year.")
    out.append({"low": f"- **What low confidence changes:** first run {p100(fr)} (the rest held back to restock what sells), units spread "
                       f"more evenly across silhouettes, and silhouettes with under {MAP['min_units_to_call']} sales get a small test run instead of a full line.",
                "medium": f"- **What medium confidence changes:** first run {p100(fr)}, units spread a little more evenly, thin silhouettes get a test run.",
                "high": f"- First run {p100(fr)}; silhouettes allocated by their sales."}[conf])

    out.append("\n## What Track A needs")
    fam = defaultdict(lambda: [0, 0, []])
    for l in lines_out:
        f = fam[l["family"]]
        f[0] += l["styles"]
        f[1] += l["units"]
        f[2].append(f"{l['styles']} {plural(l['silhouette'].lower(), l['styles'])}" + (" (test)" if l["test"] else ""))
    fam_rank = {f: i for i, f in enumerate(P.get("family_order", []))}
    for f_, (n, u, parts) in sorted(fam.items(), key=lambda x: fam_rank.get(x[0], 99)):
        label = f_.lower() if n != 1 else singular_family(f_)
        out.append(f"- **{n} {label}** ({', '.join(parts)}) · {u} units")
    made_total = sum(l["already_made"] for l in lines_out)
    n_styles = sum(l["styles"] for l in lines_out)
    out.append(f"- **Total:** {n_styles} styles in {len(stories)} prints, {a_units + t_units} units"
               + (f" ({t_units} of them in {len(test_lines)} test runs)" if test_lines else "") + ". "
               + (f"{made_total:.0f} already made. " if made_total else "")
               + f"First run {fr_total} to make, {sum(l['restock'] for l in lines_out):.0f} held back to restock what sells.")
    out.append(f"- **Track B reserve:** about {b_units:.0f} more units ({p100(1 - P['track_a_share'])} of {collection}), "
               "planned by Hessa and the design seat without sales data.")

    out.append("\n## Print stories: what each fabric makes")
    rows = []
    for s in stories:
        grouped = {}
        for x in s["pieces"]:
            g = grouped.setdefault(x["silhouette"], [0, 0, x["test"]])
            g[0] += 1
            g[1] += x["units"]
        pcs = ", ".join(f"{k.lower()}{' ×' + str(n) if n > 1 else ''} {u}" + (" (test)" if t else "") for k, (n, u, t) in grouped.items())
        fabric = f"{fabric_by_print[s['print']]:.0f} m" if s["print"] in fabric_by_print else "–"
        rows.append([s["print"], str(len(s["pieces"])), pcs, str(s["units"]), fabric, s["why"]])
    out.append(table(["Print", "Styles", "Pieces (units)", "Units", "Fabric on hand", "Why"], rows))
    out.append(f"_{n_prints} prints" + (f" (fewer than the {n_wanted} in {comps[-1]['name'] if comps else 'the last collection'}, so each print has at least "
               f"{P.get('min_styles_per_print', 4)} garments)" if n_prints < n_wanted else
               f", the number in {comps[-1]['name'] if comps else 'the last collection'}{' (set with --prints)' if '--prints' in args else ''}") + ". Each print gets one of each shape before any shape repeats (×2 = a second colourway), and a top and a bottom "
               "where it can, so a print works as a set and is cut from one fabric run. Carried prints take the shapes they already sold in. "
               f"Up to {p100(P['carryover_max_share'])} of prints carry over, and only if Hessa keeps them in the year's allocation; "
               "new prints are hers. Accessories come from the offcuts of the prints with the most garments._")
    if fabric_by_print and yields:
        out.append("\n**Fabric check:** metres needed per print = units × metres per piece (Ops App yields).")
        for s in stories:
            need = sum(x["units"] * yields.get(x["silhouette"], 0) for x in s["pieces"])
            have = fabric_by_print.get(s["print"])
            if have is not None and need:
                out.append(f"- {s['print']}: needs ~{need:.0f} m, {have:.0f} m on hand → " + ("enough" if have >= need else f"**short by {need - have:.0f} m**"))
    else:
        missing = []
        if not fabric_by_print:
            missing.append("fabric stock (no material of kind *fabric* in the Ops App yet)")
        if not yields:
            missing.append("metres per piece (no fabric lines in the Ops App's bills of materials yet; the Atelier will measure them)")
        out.append(f"\n**Fabric check: not possible yet.** Missing: {'; '.join(missing)}. Once both are in the Ops App, this plan checks every "
                   "print story against the fabric you hold, and flags prints that are short or have fabric left over for more pieces.")

    out.append("\n## The line, and why")
    rows = []
    for l in lines_out:
        ev = l["evidence"]
        why = [f"{ev['call'].split(':')[0]}: sold {ev['units']:.0f}" + (f" in {ev['months']} months" if ev["months"] else ""),
               f"discount {p100(ev['disc'])} vs {p100(line_disc)} line average"]
        if ev["returned"]:
            why.append(f"{ev['returned']:.0f} of {ev['ordered']:.0f} returned")
        if ev["st"] is not None:
            why.append(f"sell-through {p100(ev['st'])}")
        if ev["call"].startswith("Carry only if reworked"):
            why.append("fix it before it's remade: " + ev["call"].split(": ", 1)[1])
        if l["test"]:
            why.append(f"a test run of {l['units']}: too few sales to judge, and cheap to try in-house")
        if l["already_made"]:
            why.append(f"{l['already_made']:.0f} already made for {focus}")
        made_txt = f"{l['already_made']:.0f} made + " if l["already_made"] else ""
        rows.append([l["family"], l["silhouette"] + (" (test)" if l["test"] else ""), str(l["styles"]),
                     f"{made_txt}{l['first_run']} + {l['restock']:.0f}",
                     " / ".join(f"{k[0]} {v}" for k, v in l["sizes"].items()) or "–", f"~{aed(l['price'])}", "; ".join(why)])
    out.append(table(["Family", "Silhouette", "Styles", "Units (first run + restock)", "First-run sizes", "AED (last price)", "Why"], rows))
    if made_titles:
        out.append(f"_Already made for {focus}, counted against the plan: " + "; ".join(made_titles) + "._")
    if made_elsewhere:
        out.append(f"_Also named {focus} but in another line, so not counted here: " + "; ".join(made_elsewhere) + "._")

    out.append("\n## Not in Track A, and why")
    if dropped:
        out.append(table(["Silhouette", "Sold", "Why not"],
                         [[sil, f"{ev['units']:.0f}" + (f" in {ev['months']} months" if ev["months"] else ""), why] for sil, ev, why in dropped]))
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
    depth = ", ".join(f"{P['units_per_style'][c]} per {c.lower()} style" for c in cats if c in P["units_per_style"])
    out.append(f"\nUnits to make = {demand:.0f} expected × (1 + growth {p100(growth)}) ÷ target sell-through {p100(st)} = **{make:.0f}**. "
               "Units go to silhouettes by their sales, at half weight for *watch* and *rework* lines"
               + (f", then {p100(blend)} spread evenly because confidence is {conf}" if blend else "")
               + f". Styles = units ÷ {depth} (wide and shallow: restock what sells). Unproven shapes get a test run of "
               f"{P['test_style_units']} each, up to {P['max_test_styles']}. First run = {p100(fr)} of units, less anything already made.")
    if capacity:
        out.append(f"\n**Capacity:** first run capped at {capacity} units" + (f"; scaled to {p100(scaled)} of plan." if scaled else "; the plan fits."))
    else:
        out.append("\n**Capacity:** not checked. Pass `--capacity <units the team can make before launch>` once the Atelier knows its output.")

    print("\n".join(out))
    if json_out:
        import json
        json.dump({"line": line_key, "collection": collection, "window": window, "confidence": conf, "demand": demand,
                   "make": make, "lines": lines_out, "stories": stories, "dropped": [(s_, w) for s_, _, w in dropped],
                   "track_a_units": a_units, "test_units": t_units, "track_b_units": b_units, "first_run": fr_total},
                  open(json_out, "w"), indent=2, default=str)


if __name__ == "__main__":
    main()
