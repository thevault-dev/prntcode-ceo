#!/usr/bin/env python3
"""PRNTCODE range plan: how many tops, bottoms and dresses a collection needs to feel whole.

Usage:
    python3 range_plan.py <data_dir> --line rtw-ss [--collection "Wildflower SS27"] [--styles 13]

Answers one question from sales data: what shape should the next collection have?
- How many styles in total (by default, as many silhouettes as the line's last collection had).
- How they split across families (tops, bottoms, dresses), from what customers bought,
  with a minimum per family so the collection feels whole.
- Within each family, a named silhouette only where the data says customers liked it;
  every other slot stays open ("open top") for the designer.

It does not choose prints or quantities to make. One line at a time (see lines.py);
reads products.json and monthly.json (required), inventory.json (sell-through) and ops.json
(which listings belong to which collection) from <data_dir>.
"""
import datetime
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collection_review import (  # noqa: E402
    MAP, add, clean_title, is_unnamed, load, month_index, new_agg, num, p100, parse_title, pct,
    silhouette_call,
)
from lines import (  # noqa: E402
    LINES, collection_history, confidence_for, in_category, line_categories, load_ops, resolve_line,
)

R = MAP["range"]


def singular(family):
    f = family.lower()
    return f[:-2] if f.endswith("sses") else f[:-1] if f.endswith("s") else f


def plural(word, n):
    if n == 1:
        return word
    if word.endswith("ss"):
        return word + "es"
    if word.endswith("s"):
        return word
    return word + "s"


def split_slots(total, weights, minimum):
    """Whole-number slots per key, each at least `minimum`, the rest by weight (largest remainder)."""
    keys = list(weights)
    base = {k: minimum for k in keys}
    left = total - minimum * len(keys)
    if left <= 0:
        return base
    w = sum(weights.values()) or 1
    raw = {k: left * weights[k] / w for k in keys}
    add_ = {k: int(raw[k]) for k in keys}
    for k in sorted(keys, key=lambda k: raw[k] - add_[k], reverse=True)[: left - sum(add_.values())]:
        add_[k] += 1
    return {k: base[k] + add_[k] for k in keys}


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
    collection = opt("--collection", f"the next {L['name']} collection")
    ops = load_ops(data_dir)

    products = load(data_dir, "products.json")
    monthly = load(data_dir, "monthly.json")
    if products is None or not monthly:
        sys.exit("products.json and monthly.json are both needed (queries 1 and 4 in SKILL.md).")
    inventory = load(data_dir, "inventory.json") or []

    ptype_of = {clean_title(r["product_title"]): r.get("product_type", "") for r in products}

    def classify(t):
        return parse_title(t, ptype_of.get(clean_title(t), ""))

    # garments only: the families that make a collection feel whole
    families = R["families"].get(main_cat, {})
    products = [r for r in in_category(products, [main_cat], classify)]
    monthly_c = in_category(monthly, cats, classify)
    this_month = datetime.date.today().strftime("%Y-%m")
    data_months = sorted({r["month"][:7] for r in monthly if r["month"][:7] < this_month})
    last_m = data_months[-1] if data_months else None

    # how far to trust the history
    if L["basis"] == "collection":
        comps = collection_history(cats, monthly_c, classify, last_m, ops) if last_m else []
        observed = max((len(c["curve"]) for c in comps), default=0)
        conf = confidence_for(observed, len(comps), "collection")
    else:
        comps = []
        sold = sorted(r["month"][:7] for r in monthly_c if num(r["net_items_sold"]) > 0 and r["month"][:7] < this_month)
        observed = month_index(last_m) - month_index(sold[0]) + 1 if sold and last_m else 0
        conf = confidence_for(observed, 0, "seasonal")

    # evidence per silhouette
    by_line, by_sil, first = new_agg(), defaultdict(new_agg), {}
    for r in products:
        _, _, sil = classify(r["product_title"])
        add(by_line, r)
        add(by_sil[sil], r)
    for r in monthly_c:
        m = r["month"][:7]
        if m >= this_month or num(r["net_items_sold"]) <= 0:
            continue
        c, _, sil = classify(r["product_title"])
        if c == main_cat:
            first[sil] = min(first.get(sil, m), m)
    sold_left = defaultdict(lambda: [0.0, 0.0])
    for r in inventory:
        t = clean_title(r["product_title"])
        if is_unnamed(t) or classify(t)[0] != main_cat or num(r["ending_inventory_units"]) >= MAP["placeholder_stock_units"]:
            continue
        sil = classify(t)[2]
        sold_left[sil][0] += max(num(r["inventory_units_sold"]), 0)
        sold_left[sil][1] += max(num(r["ending_inventory_units"]), 0)
    line_disc = pct(by_line["disc"], by_line["gross"])
    fair = by_line["net"] / len(by_sil) if by_sil else 0

    sil_info = {}
    for sil, v in by_sil.items():
        mo = month_index(last_m) - month_index(first[sil]) + 1 if sil in first and last_m else None
        disc, ret = pct(v["disc"], v["gross"]), pct(v["returned"], v["ordered"])
        sold, left = sold_left.get(sil, [0, 0])
        sil_info[sil] = {
            "family": families.get(sil), "units": v["units"], "ordered": v["ordered"], "returned": v["returned"],
            "disc": disc, "ret": ret, "months": mo, "net": v["net"],
            "st": pct(sold, sold + left) if (sold + left) and main_cat in MAP["sell_through_categories"] else None,
            "call": silhouette_call(v["units"], disc, line_disc, ret, mo, v["net"], fair, conf),
        }
    unmapped = [s for s, i in sil_info.items() if not i["family"]]

    # 1. how many styles: the breadth of the line's last collection, unless set
    last_sils = set()
    if ops and comps and comps[-1].get("id"):
        cid = comps[-1]["id"]
        for p in ops.get("products", []):
            if p.get("collection_id") == cid and parse_title(p["product_title"], p.get("product_type", ""))[0] == main_cat:
                last_sils.add(parse_title(p["product_title"], p.get("product_type", ""))[2])
    if not last_sils:
        last_sils = {s for s, i in sil_info.items() if i["family"]}
    n_styles = opt("--styles", None, int) or R.get("styles") or len(last_sils)
    breadth_src = ("set with --styles" if "--styles" in args else "set in the catalogue map" if R.get("styles")
                   else f"as many silhouettes as {comps[-1]['name'] if comps else 'the last collection'} had")

    # 2. the split across families: what customers bought, with a floor per family
    fam_units = defaultdict(float)
    for s, i in sil_info.items():
        if i["family"]:
            fam_units[i["family"]] += max(i["units"], 0)
    fam_order = [f for f in R["family_order"] if f in set(families.values())]
    weights = {f: fam_units.get(f, 0) for f in fam_order}
    slots = split_slots(n_styles, weights, R["min_per_family"])
    tot_units = sum(weights.values()) or 1

    # 3. inside each family: name what customers liked, keep the rest open
    liked_calls = set(R["liked_calls"])
    plan = {}
    for f in fam_order:
        liked = [(s, i) for s, i in sil_info.items() if i["family"] == f and i["call"] in liked_calls]
        liked.sort(key=lambda x: -x[1]["units"])
        n = slots[f]
        open_min = min(R["open_slots_per_family"], n)
        named_room = n - open_min
        named = {}
        if liked and named_room > 0:
            liked = liked[:named_room]
            named = {s_: 1 for s_, _ in liked}
            fam_total = sum(i["units"] for s_, i in sil_info.items() if i["family"] == f) or 1
            # a second version for shapes customers wanted more of
            for s_, i in liked:
                if sum(named.values()) >= named_room:
                    break
                wanted_more = (i["st"] is not None and i["st"] > R["second_slot_sell_through"]) or \
                              (i["st"] is None and i["units"] / fam_total >= R["second_slot_family_share"])
                if wanted_more and R["max_per_silhouette"] > 1:
                    named[s_] = 2
        open_n = n - sum(named.values())
        others = [(s, i) for s, i in sil_info.items() if i["family"] == f and s not in named]
        plan[f] = {"slots": n, "named": [(s, named[s], sil_info[s]) for s, _ in liked if s in named], "open": open_n, "others": others}

    # =================== output ===================
    out = []
    parts = ", ".join(f"{plan[f]['slots']} {plural(singular(f), plan[f]['slots'])}" for f in fam_order)
    out.append(f"# What {collection} needs to feel whole")
    out.append(f"**{n_styles} styles: {parts}.**")
    out.append(f"_{L['name']} · {main_cat.lower()} only · from sales data. A named silhouette means customers clearly liked it; "
               "an open slot is the designer's call. Prints and quantities aren't part of this._")

    for f in fam_order:
        p = plan[f]
        out.append(f"\n## {f} ({p['slots']})")
        for s, k, i in p["named"]:
            bits = [f"sold {i['units']:.0f}" + (f" in {i['months']} months" if i["months"] else "")]
            if i["st"] is not None:
                bits.append(f"{p100(i['st'])} sold through")
            bits.append(f"{p100(i['disc'])} discount" if i["disc"] else "no discount")
            bits.append(f"{i['returned']:.0f} of {i['ordered']:.0f} returned" if i["returned"] else "none returned")
            extra = " Two versions, because it sold through more than half its stock." if k > 1 and i["st"] is not None else \
                    " Two versions, because it carried its family's sales." if k > 1 else ""
            out.append(f"- **{s}{' ×' + str(k) if k > 1 else ''}**: customers liked it ({', '.join(bits)}).{extra}")
        if p["open"]:
            label = plural("open " + singular(f), p["open"])
            out.append(f"- **{p['open']} {label}**: no clear signal, the designer's call.")
        notes = []
        for s, i in sorted(p["others"], key=lambda x: -x[1]["units"]):
            if i["call"].startswith("Carry only if reworked"):
                why = "high returns" if "returns" in i["call"] else "sold on discount"
                notes.append(f"{s.lower()} sold {i['units']:.0f} but {'%d of %d came back' % (i['returned'], i['ordered']) if why == 'high returns' else 'needed a ' + p100(i['disc']) + ' discount'}")
            elif i["call"].startswith(("Unproven", "Drop", "Too few")):
                notes.append(f"{s.lower()} sold {i['units']:.0f}")
            elif i["call"] == "Watch":
                notes.append(f"{s.lower()} sold {i['units']:.0f}, below its share")
        if notes:
            out.append(f"  _Not named, because the data doesn't say customers liked it: {'; '.join(notes)}._")

    out.append("\n## Why this shape")
    split_txt = ", ".join(f"{f.lower()} {p100(weights[f] / tot_units)}" for f in fam_order)
    out.append(f"- **{n_styles} styles:** {breadth_src}.")
    out.append(f"- **The split** follows what customers bought ({split_txt} of {main_cat.lower()} pieces sold), "
               f"with at least {R['min_per_family']} of each family so every part of a wardrobe is there.")
    out.append(f"- **Named silhouettes** are those the data marks as liked: at or above their fair share of sales, "
               f"{MAP['min_units_to_call']}+ sold, discount within {p100(MAP['rework_discount_margin'])} points of the line's average "
               f"({p100(line_disc)}), and no more than {p100(MAP['rework_returns_rate'])} returned. A shape gets two slots "
               f"(a second version) when it sold through more than {p100(R['second_slot_sell_through'])} of its stock. Each family keeps at least {R['open_slots_per_family']} open slot for something new.")
    if L["basis"] == "collection" and comps:
        c = comps[-1]
        out.append(f"- **How much to trust it: {conf}.** It rests on {len(comps)} collection{'s' if len(comps) > 1 else ''} "
                   f"({c['name']}, {len(c['curve'])} months on sale). Treat the split as a starting point, not a rule.")
    else:
        out.append(f"- **How much to trust it: {conf}** ({observed} months of sales).")
    if unmapped:
        out.append(f"- Not counted (no family set under range.families): {', '.join(unmapped)}.")

    print("\n".join(out))


if __name__ == "__main__":
    main()
