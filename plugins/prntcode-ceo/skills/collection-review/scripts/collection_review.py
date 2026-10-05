#!/usr/bin/env python3
"""PRNTCODE collection review: turns saved ShopifyQL results into the review tables.

Usage:
    python3 collection_review.py <data_dir> [--focus "Wildflower"] [--json out.json]

<data_dir> holds the query results saved in step 2 of SKILL.md, each as the JSON object
the Shopify run-analytics-query tool returned (it has "columns" and "rows"):

    products.json   sales by product_title, product_type        (required)
    channels.json   sales by product_title, sales_channel
    variants.json   sales by product_title, product_type, product_variant_title
    monthly.json    sales by product_title, TIMESERIES month
    inventory.json  inventory by product_title

Any file except products.json may be missing; its section is skipped and says so.
Reads catalogue-map.json from ../references. Prints markdown to stdout. Writes nothing else
unless --json is given.
"""
import json
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
MAP = json.load(open(os.path.join(HERE, "..", "references", "catalogue-map.json")))


# ---------- loading ----------

def load(data_dir, name):
    path = os.path.join(data_dir, name)
    if not os.path.exists(path):
        return None
    obj = json.load(open(path))
    if isinstance(obj, dict) and "rows" in obj:
        cols = [c["name"] if isinstance(c, dict) else c for c in obj["columns"]]
        rows = obj["rows"]
    else:  # already a list of dicts
        return obj
    return [dict(zip(cols, r)) for r in rows]


def num(v):
    if v in (None, ""):
        return 0.0
    return float(v)


# ---------- reading titles ----------

def clean_title(t):
    return re.sub(r"[\s\-]+$", "", (t or "").strip())


def is_unnamed(t):
    t = clean_title(t)
    return t == "" or t.startswith("Untitled")


def canon_print(p):
    p = p.strip()
    for k, v in MAP["print_aliases"].items():
        if p.lower() == k.lower():
            return v
    if p.isupper():
        p = p.title()
    return p


def parse_title(title, ptype=""):
    """Return (category, print, silhouette) for a product title."""
    t = clean_title(title)
    low = t.lower()
    cat = MAP["category_from_product_type"].get((ptype or "").strip().upper())
    marker = MAP["jalabiya_marker"].lower()
    acc_words = MAP["accessory_words"]

    if marker in low:
        cat = "Jalabiya"
    if not cat:
        if any(w.lower() in low for w in acc_words):
            cat = "Accessories"
        elif "abaya" in low:
            cat = "Abaya"
        elif " in " in t:
            cat = "Ready-to-wear"
        else:
            cat = "Unclassified"

    body = re.sub(r"^The\s+", "", t)
    prnt = None
    if cat == "Jalabiya":
        for p in MAP["known_prints"]:
            if p.lower() in low:
                prnt = p
        prnt = prnt or "MKWR own prints"
        sil = "Jalabiya"
    else:
        if " in " in body:
            sil_part, prnt = body.rsplit(" in ", 1)
        elif " - " in body:
            left, right = body.split(" - ", 1)
            if any(left.lower() == w.lower() for w in acc_words):
                sil_part, prnt = left, right
            else:
                prnt, sil_part = left, right
        else:
            sil_part, prnt = "", body
        if cat == "Accessories":
            sil = next((w for w in sorted(acc_words, key=len, reverse=True) if w.lower() in low), "Accessory")
            sil = {"Scrunchies": "Scrunchie", "Twillies": "Twilly"}.get(sil, sil)
            if any(prnt.lower() == w.lower() for w in acc_words) or prnt.lower().startswith(("scrunchies", "head scarf")):
                prnt = "Unprinted / mixed"
        elif cat == "Abaya":
            sil = "Reversible Abaya" if "reversible" in low else "Abaya"
        else:
            sil = sil_part.strip() or "Unknown"
        prnt = canon_print(prnt.replace(" - Small", "").strip())
    return cat, prnt, sil


# ---------- helpers ----------

def pct(a, b):
    return (a / b) if b else 0.0


def fmt_aed(v):
    return f"{v:,.0f}"


def fmt_pct(v):
    return f"{v * 100:.0f}%"


def table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(c) for c in r) + " |")
    return "\n".join(out)


# ---------- main ----------

def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)
    data_dir = args[0]
    focus = None
    json_out = None
    if "--focus" in args:
        focus = args[args.index("--focus") + 1]
    if "--json" in args:
        json_out = args[args.index("--json") + 1]

    products = load(data_dir, "products.json")
    if products is None:
        sys.exit("products.json is missing: run query 1 in SKILL.md first.")
    channels = load(data_dir, "channels.json")
    variants = load(data_dir, "variants.json")
    monthly = load(data_dir, "monthly.json")
    inventory = load(data_dir, "inventory.json")

    ptype_of = {}
    for r in products:
        ptype_of[clean_title(r["product_title"])] = r.get("product_type", "")

    def classify(title):
        return parse_title(title, ptype_of.get(clean_title(title), ""))

    out = []
    result = {}

    # --- headline and unnamed sales
    tot_net = sum(num(r["net_sales"]) for r in products)
    unnamed = [r for r in products if is_unnamed(r["product_title"])]
    un_net = sum(num(r["net_sales"]) for r in unnamed)
    un_units = sum(num(r["net_items_sold"]) for r in unnamed)
    named = [r for r in products if not is_unnamed(r["product_title"])]
    named_net = sum(num(r["net_sales"]) for r in named)

    months = sorted({r["month"][:7] for r in monthly}) if monthly else []
    active_months = sorted({r["month"][:7] for r in monthly if num(r["net_items_sold"]) or num(r["gross_sales"])}) if monthly else []
    span = f"{active_months[0]} to {active_months[-1]}" if active_months else "unknown"

    out.append("## Headline")
    out.append(f"- Period with sales: {span}")
    out.append(f"- Net sales: AED {fmt_aed(tot_net)}, of which AED {fmt_aed(named_net)} ({fmt_pct(pct(named_net, tot_net))}) is on named products and is what this review analyses")
    out.append(f"- Not tied to a product (custom line items, blank or 'Untitled' listings): AED {fmt_aed(un_net)} across {un_units:.0f} items ({fmt_pct(pct(un_net, tot_net))})")
    if monthly:
        big = [r for r in monthly if is_unnamed(r["product_title"]) and num(r["net_items_sold"]) >= 50]
        for r in big:
            out.append(f"  - {r['month'][:7]}: {num(r['net_items_sold']):.0f} unnamed items, AED {fmt_aed(num(r['gross_sales']) + num(r['discounts']))} net (likely one bulk or custom order)")
    result["headline"] = {"span": span, "net_sales": tot_net, "named_net": named_net, "unnamed_net": un_net, "unnamed_units": un_units}

    # --- aggregate named products
    agg = lambda: {"units": 0.0, "gross": 0.0, "disc": 0.0, "net": 0.0, "listings": set()}
    by_cat = defaultdict(agg)
    by_print = defaultdict(agg)
    by_pc = defaultdict(agg)
    by_sil = defaultdict(agg)
    for r in named:
        t = clean_title(r["product_title"])
        cat, prnt, sil = classify(t)
        for d, k in ((by_cat, cat), (by_print, prnt), (by_pc, (prnt, cat)), (by_sil, (cat, sil))):
            d[k]["units"] += num(r["net_items_sold"])
            d[k]["gross"] += num(r["gross_sales"])
            d[k]["disc"] += -num(r["discounts"])
            d[k]["net"] += num(r["net_sales"])
            d[k]["listings"].add(t)

    def rows_for(d, keyfmt, total):
        rows = []
        for k, v in sorted(d.items(), key=lambda x: -x[1]["net"]):
            rows.append([keyfmt(k), f"{v['units']:.0f}", fmt_aed(v["net"]), fmt_pct(pct(v["net"], total)),
                         fmt_aed(pct(v["net"], v["units"])), fmt_pct(pct(v["disc"], v["gross"]))])
        return rows

    H = ["", "Units", "Net AED", "Share", "Avg AED", "Discount"]
    out.append("\n## By category")
    out.append(table(["Category"] + H[1:], rows_for(by_cat, str, named_net)))
    out.append("\n## By print (all categories)")
    out.append(table(["Print"] + H[1:], rows_for(by_print, str, named_net)))

    cats = sorted(by_cat, key=lambda c: -by_cat[c]["net"])
    prints = sorted(by_print, key=lambda p: -by_print[p]["net"])
    out.append("\n## Print × category (units · net AED)")
    rows = []
    for p in prints:
        row = [p]
        for c in cats:
            v = by_pc.get((p, c))
            row.append(f"{v['units']:.0f} · {fmt_aed(v['net'])}" if v and v["units"] else "–")
        rows.append(row)
    out.append(table(["Print"] + cats, rows))

    for c in cats:
        sils = {k: v for k, v in by_sil.items() if k[0] == c}
        if len(sils) < 2:
            continue
        cat_net = by_cat[c]["net"]
        out.append(f"\n## {c}: by silhouette")
        out.append(table(["Silhouette"] + H[1:], rows_for(sils, lambda k: k[1], cat_net)))

    cat_disc = {c: pct(v["disc"], v["gross"]) for c, v in by_cat.items()}
    result["categories"] = {c: {k: v for k, v in d.items() if k != "listings"} for c, d in by_cat.items()}
    result["prints"] = {p: {k: v for k, v in d.items() if k != "listings"} for p, d in by_print.items()}

    # --- sizes and colours
    if variants:
        sizes = defaultdict(lambda: defaultdict(float))
        colours = defaultdict(float)
        fabrics = defaultdict(float)
        for r in variants:
            t = clean_title(r.get("product_title", ""))
            if is_unnamed(t):
                continue
            cat, prnt, sil = parse_title(t, r.get("product_type", ""))
            u = num(r["net_items_sold"])
            parts = [p.strip() for p in (r.get("product_variant_title") or "").split("/") if p.strip()]
            size = None
            colour = None
            for p in parts:
                key = next((k for k in MAP["size_words"] if k.lower() == p.lower()), None)
                if key:
                    size = MAP["size_words"][key]
                elif p.isdigit():
                    continue
                elif any(p.lower() == f.lower() for f in MAP["fabric_words"]):
                    if cat == "Jalabiya":
                        fabrics[p.title()] += u
                elif cat in ("Abaya",):
                    colour = p.title()
            if size and cat in ("Abaya", "Ready-to-wear"):
                sizes[cat][size] += u
            if colour:
                colours[colour] += u
        out.append("\n## Size curve (units)")
        order = ["XS", "Small", "Medium", "Large", "XL"]
        rows = []
        for c, s in sizes.items():
            tot = sum(s.values())
            rows.append([c] + [f"{s.get(z, 0):.0f} ({fmt_pct(pct(s.get(z, 0), tot))})" if s.get(z) else "–" for z in order])
        out.append(table(["Category"] + order, rows))
        if colours:
            tot = sum(colours.values())
            out.append("\n## Abaya colourways (older listings only; newer listings keep colour in the SKU, not the variant)")
            out.append(table(["Colour", "Units", "Share"],
                             [[k, f"{v:.0f}", fmt_pct(pct(v, tot))] for k, v in sorted(colours.items(), key=lambda x: -x[1]) if v]))
        result["sizes"] = {c: dict(s) for c, s in sizes.items()}
        result["colours"] = dict(colours)
    else:
        out.append("\n## Size curve\n_variants.json missing: skipped._")

    # --- channels
    if channels:
        group_of = {}
        for g, names in MAP["channel_groups"].items():
            for n in names:
                group_of[n] = g
        groups = list(MAP["channel_groups"].keys()) + ["Other"]
        ch_cat = defaultdict(lambda: defaultdict(float))
        ch_print = defaultdict(lambda: defaultdict(float))
        for r in channels:
            t = clean_title(r["product_title"])
            if is_unnamed(t):
                continue
            cat, prnt, sil = classify(t)
            g = group_of.get(r["sales_channel"], "Other")
            ch_cat[cat][g] += num(r["net_sales"])
            ch_print[(cat, prnt)][g] += num(r["net_sales"])
        out.append("\n## Where it sells (share of net sales)")
        rows = []
        for c in cats:
            d = ch_cat.get(c, {})
            tot = sum(d.values())
            rows.append([c] + [fmt_pct(pct(d.get(g, 0), tot)) for g in groups])
        out.append(table(["Category"] + groups, rows))
        top_cat = cats[0]
        out.append(f"\n## {top_cat}: where each print sells")
        rows = []
        for p in prints:
            d = ch_print.get((top_cat, p))
            if not d:
                continue
            tot = sum(d.values())
            rows.append([p, fmt_aed(tot)] + [fmt_pct(pct(d.get(g, 0), tot)) for g in groups])
        out.append(table(["Print", "Net AED"] + groups, rows))
        result["channels"] = {c: dict(d) for c, d in ch_cat.items()}
    else:
        out.append("\n## Where it sells\n_channels.json missing: skipped._")

    # --- launch and pace (print × silhouette, relisted listings merged)
    pace = {}
    if monthly:
        last_month = months[-1] if months else None
        series = defaultdict(lambda: defaultdict(lambda: [0.0, 0.0, 0.0]))
        for r in monthly:
            t = clean_title(r["product_title"])
            if is_unnamed(t):
                continue
            cat, prnt, sil = classify(t)
            m = r["month"][:7]
            s = series[(cat, prnt, sil)][m]
            s[0] += num(r["net_items_sold"])
            s[1] += num(r["gross_sales"])
            s[2] += -num(r["discounts"])

        def month_index(m):
            y, mo = m.split("-")
            return int(y) * 12 + int(mo) - 1

        W = MAP["launch_window_months"]
        rows = []
        for key, ms in series.items():
            sold = sorted(m for m, v in ms.items() if v[0] > 0)
            if not sold:
                continue
            launch = sold[0]
            on_sale = month_index(last_month) - month_index(launch) + 1 if last_month else 0
            win = [m for m in ms if 0 <= month_index(m) - month_index(launch) < W]
            wu = sum(ms[m][0] for m in win)
            wg = sum(ms[m][1] for m in win)
            wd = sum(ms[m][2] for m in win)
            tu = sum(v[0] for v in ms.values())
            # A first sale in the first month of data means it was probably on sale before the data starts
            before_data = bool(active_months) and launch == active_months[0]
            pace[key] = {"launch": launch, "launch_is_data_start": before_data, "months_on_sale": on_sale,
                         "window_units": wu, "window_discount": pct(wd, wg), "units": tu, "per_month": pct(tu, on_sale)}
            rows.append([key[0], key[1], key[2], ("≤" if before_data else "") + launch, str(on_sale),
                         f"{wu:.0f}", fmt_pct(pct(wd, wg)), f"{pct(tu, on_sale):.1f}"])
        rows.sort(key=lambda r: (r[0], -float(r[7])))
        out.append(f"\n## Launch and pace (relisted versions merged; launch = first month with a sale; window = first {W} months)")
        out.append(f"_Months counted to {last_month}, which may be part-way through. ≤ means it already sold in the first month of data, so it was probably launched earlier and its first-{W}-month figures are not a true launch._")
        out.append(table(["Category", "Print", "Silhouette", "Launch", "Months on sale", f"Units in first {W}m", "Discount then", "Units / month"], rows))
    else:
        out.append("\n## Launch and pace\n_monthly.json missing: skipped._")

    # --- stock
    if inventory:
        thr = MAP["placeholder_stock_units"]
        st_cats = set(MAP["sell_through_categories"])
        placeholder, waiting, st_rows = [], [], []
        for r in inventory:
            t = clean_title(r["product_title"])
            if is_unnamed(t):
                continue
            cat, prnt, sil = classify(t)
            end = num(r["ending_inventory_units"])
            sold = num(r["inventory_units_sold"])
            if end >= thr:
                placeholder.append(f"{t} ({end:.0f})")
                continue
            if sold <= 0 and end > 0:
                waiting.append(f"{t} ({end:.0f} in stock)")
                continue
            if cat in st_cats and sold > 0:
                st_rows.append([t, f"{sold:.0f}", f"{max(end, 0):.0f}", fmt_pct(num(r["sell_through_rate"]))])
        out.append("\n## Stock")
        if st_rows:
            st_rows.sort(key=lambda r: -float(r[3].rstrip("%")))
            out.append(f"Sell-through where stock counts are real ({', '.join(sorted(st_cats))}):")
            out.append(table(["Listing", "Sold", "Left", "Sell-through"], st_rows))
        if placeholder:
            out.append(f"\nPlaceholder stock (≥{thr} units, so sell-through means nothing): " + "; ".join(placeholder))
        if waiting:
            out.append("\nListed with stock but no sales yet: " + "; ".join(waiting))
        result["stock"] = {"placeholder": placeholder, "no_sales_yet": waiting}
    else:
        out.append("\n## Stock\n_inventory.json missing: skipped._")

    # --- suggested calls
    minu = MAP["min_units_to_call"]
    margin = MAP["rework_discount_margin"]
    W = MAP["launch_window_months"]
    calls = []
    for (cat, sil), v in sorted(by_sil.items(), key=lambda x: (x[0][0], -x[1]["net"])):
        n_groups = len([k for k in by_sil if k[0] == cat])
        fair = by_cat[cat]["net"] / n_groups if n_groups else 0
        # None when monthly.json is missing: age unknown, so no "too new" call
        months_on = max((p["months_on_sale"] for k, p in pace.items() if k[0] == cat and k[2] == sil), default=None)
        disc = pct(v["disc"], v["gross"])
        if months_on is not None and months_on < W:
            call = "Too new to call"
        elif v["units"] < minu:
            call = "Retire candidate" if months_on is not None else "Too few to call"
        elif disc > cat_disc[cat] + margin:
            call = "Rework: needed discounts to sell"
        elif v["net"] >= fair:
            call = "Repeat"
        else:
            call = "Hold: sells, but below its share"
        calls.append([cat, sil, f"{v['units']:.0f}", fmt_pct(disc), f"{fmt_pct(cat_disc[cat])}", call])
    out.append("\n## Suggested calls by silhouette (rules in SKILL.md, step 4; the report can overrule them with a reason)")
    out.append(table(["Category", "Silhouette", "Units", "Discount", "Category avg", "Call"], calls))

    pcalls = []
    for (p, cat), v in sorted(by_pc.items(), key=lambda x: (x[0][1], -x[1]["net"])):
        if cat not in ("Abaya", "Ready-to-wear"):
            continue
        disc = pct(v["disc"], v["gross"])
        n_groups = len([k for k in by_pc if k[1] == cat])
        fair = by_cat[cat]["net"] / n_groups if n_groups else 0
        if v["units"] < minu:
            call = "Too few to call / retire candidate"
        elif disc > cat_disc[cat] + margin:
            call = "Rework: needed discounts to sell"
        elif v["net"] >= fair:
            call = "Repeat"
        else:
            call = "Hold"
        pcalls.append([cat, p, f"{v['units']:.0f}", fmt_aed(v["net"]), fmt_pct(disc), call])
    out.append("\n## Suggested calls by print, per category")
    out.append(table(["Category", "Print", "Units", "Net AED", "Discount", "Call"], pcalls))
    result["calls_by_silhouette"] = calls
    result["calls_by_print"] = pcalls

    # --- focus collection
    if focus:
        f = focus.lower()
        hits = []
        for src, rows_ in (("sales", products), ("stock", inventory or [])):
            for r in rows_:
                if f in (r.get("product_title") or "").lower():
                    hits.append((src, r))
        out.append(f"\n## Focus: {focus}")
        if hits:
            for src, r in hits:
                if src == "sales":
                    out.append(f"- Sales: {r['product_title']}: {num(r['net_items_sold']):.0f} units, AED {fmt_aed(num(r['net_sales']))}")
                else:
                    out.append(f"- Listed: {r['product_title']}: {num(r['ending_inventory_units']):.0f} in stock, {num(r['inventory_units_sold']):.0f} sold")
        else:
            out.append(f"- No listing with '{focus}' in its title yet.")
        result["focus"] = [r.get("product_title") for _, r in hits]

    print("\n".join(out))
    if json_out:
        json.dump(result, open(json_out, "w"), indent=2, default=list)


if __name__ == "__main__":
    main()
