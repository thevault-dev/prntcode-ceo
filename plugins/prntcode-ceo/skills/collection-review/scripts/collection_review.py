#!/usr/bin/env python3
"""PRNTCODE collection review: the stage 00 starting point, from saved ShopifyQL results.

Usage:
    python3 collection_review.py <data_dir> [--focus "Wildflower"] [--period "Oct 2025 – Sep 2026"] [--json out.json]

<data_dir> holds the query results saved in step 2 of SKILL.md, each as the JSON object
the Shopify run-analytics-query tool returned (it has "columns" and "rows"):

    products.json   sales by product_title, product_type        (required)
    channels.json   sales by product_title, sales_channel
    variants.json   sales by product_title, product_type, product_variant_title
    monthly.json    sales by product_title, TIMESERIES month
    inventory.json  inventory by product_title

Any file except products.json may be missing; its section is skipped and says so.
Reads catalogue-map.json from ../references. Prints markdown to stdout, laid out by
Collection Design Process stage (PC-OPS-CDP-09): Part 1 feeds stage 00, Part 2 feeds
stage 02. Writes nothing else unless --json is given.
"""
import datetime
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
        return [dict(zip(cols, r)) for r in obj["rows"]]
    return obj  # already a list of dicts


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
    acc_words = MAP["accessory_words"]

    if MAP["jalabiya_marker"].lower() in low:
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

    body = re.sub(r"^(PRE ORDER - )?The\s+", "", t)
    if cat == "Jalabiya":
        prnt = next((p for p in MAP["known_prints"] if p.lower() in low), "MKWR own prints")
        return cat, prnt, "Jalabiya"

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
        if any(prnt.lower().startswith(w.lower()) for w in acc_words):
            prnt = "Unprinted / mixed"
    elif cat == "Abaya":
        sil = "Reversible Abaya" if "reversible" in low else "Abaya"
    else:
        sil = sil_part.strip() or "Unknown"
    return cat, canon_print(prnt.replace(" - Small", "").strip()), sil


# ---------- helpers ----------

def pct(a, b):
    return (a / b) if b else 0.0


def aed(v):
    return f"{v:,.0f}"


def p100(v):
    return f"{v * 100:.0f}%"


def table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def month_index(m):
    y, mo = m[:7].split("-")
    return int(y) * 12 + int(mo) - 1


def ratio_of_ten(shares):
    """Largest-remainder rounding of shares to whole numbers summing to 10."""
    total = sum(shares.values())
    if not total:
        return {}
    raw = {k: v / total * 10 for k, v in shares.items()}
    base = {k: int(v) for k, v in raw.items()}
    left = 10 - sum(base.values())
    for k in sorted(raw, key=lambda k: raw[k] - base[k], reverse=True)[:left]:
        base[k] += 1
    return base


def new_agg():
    return {"units": 0.0, "gross": 0.0, "disc": 0.0, "net": 0.0, "ordered": 0.0, "returned": 0.0}


def ordered_qty(r):
    """Units ordered (before returns); falls back to net units on older saved data."""
    q = num(r.get("quantity_ordered"))
    return q if q > 0 else max(num(r.get("net_items_sold")), 0)


def add(a, r):
    a["ordered"] += ordered_qty(r)
    a["returned"] += abs(num(r.get("quantity_returned")))
    a["units"] += num(r.get("net_items_sold"))
    a["gross"] += num(r.get("gross_sales"))
    a["disc"] += -num(r.get("discounts"))
    a["net"] += num(r.get("net_sales"))


# ---------- main ----------

def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)
    data_dir = args[0]

    def opt(flag):
        return args[args.index(flag) + 1] if flag in args else None

    focus, period_label, json_out = opt("--focus"), opt("--period"), opt("--json")

    products = load(data_dir, "products.json")
    if products is None:
        sys.exit("products.json is missing: run query 1 in SKILL.md first.")
    channels = load(data_dir, "channels.json")
    variants = load(data_dir, "variants.json")
    monthly = load(data_dir, "monthly.json")
    inventory = load(data_dir, "inventory.json")

    ptype_of = {clean_title(r["product_title"]): r.get("product_type", "") for r in products}

    def classify(title):
        return parse_title(title, ptype_of.get(clean_title(title), ""))

    minu = MAP["min_units_to_call"]
    W = MAP["launch_window_months"]
    margin = MAP["rework_discount_margin"]
    ret_max = MAP["rework_returns_rate"]
    thr = MAP["placeholder_stock_units"]
    real_st = set(MAP["sell_through_categories"])
    out, result = [], {}

    # ---------- period ----------
    this_month = datetime.date.today().strftime("%Y-%m")
    months_all = sorted({r["month"][:7] for r in monthly}) if monthly else []
    complete = [m for m in months_all if m < this_month]
    active = sorted({r["month"][:7] for r in monthly if (num(r["net_items_sold"]) or num(r["gross_sales"])) and r["month"][:7] < this_month}) if monthly else []
    first_m = active[0] if active else None
    last_m = complete[-1] if complete else None
    n_months = (month_index(last_m) - month_index(first_m) + 1) if first_m and last_m else None
    period = period_label or (f"{first_m} to {last_m}" if first_m else "period not known (monthly.json missing)")

    # ---------- aggregate named products ----------
    named = [r for r in products if not is_unnamed(r["product_title"])]
    unnamed = [r for r in products if is_unnamed(r["product_title"])]
    tot_net = sum(num(r["net_sales"]) for r in products)
    named_net = sum(num(r["net_sales"]) for r in named)
    un_net = sum(num(r["net_sales"]) for r in unnamed)
    un_units = sum(num(r["net_items_sold"]) for r in unnamed)

    by_cat, by_pc, by_sil = defaultdict(new_agg), defaultdict(new_agg), defaultdict(new_agg)
    by_band = defaultdict(new_agg)
    bands = MAP["price_bands_aed"]

    def band_of(price):
        for lo, hi, label in bands:
            if lo <= price < hi:
                return label
        return bands[-1][2]

    for r in named:
        cat, prnt, sil = classify(r["product_title"])
        add(by_cat[cat], r)
        add(by_pc[(prnt, cat)], r)
        add(by_sil[(cat, sil)], r)
        q = ordered_qty(r)
        if q > 0 and cat in ("Abaya", "Ready-to-wear"):
            add(by_band[(cat, band_of(num(r["gross_sales"]) / q))], r)

    cats = sorted(by_cat, key=lambda c: -by_cat[c]["net"])
    cat_disc = {c: pct(v["disc"], v["gross"]) for c, v in by_cat.items()}

    # ---------- stock ----------
    stock_pc, stock_sil = defaultdict(lambda: [0.0, 0.0]), defaultdict(lambda: [0.0, 0.0])
    placeholder, no_sales, preorder = [], [], []
    if inventory:
        for r in inventory:
            t = clean_title(r["product_title"])
            if is_unnamed(t):
                continue
            cat, prnt, sil = classify(t)
            end, sold = num(r["ending_inventory_units"]), num(r["inventory_units_sold"])
            if end >= thr:
                placeholder.append(f"{t} ({end:.0f})")
                continue
            if any(t.upper().startswith(x.upper()) for x in MAP["not_stock_title_prefixes"]):
                preorder.append(f"{t} ({end:.0f})")
                continue
            if sold <= 0 and end > 0:
                no_sales.append((cat, t, end))
            for d, k in ((stock_pc, (prnt, cat)), (stock_sil, (cat, sil))):
                d[k][0] += max(sold, 0)
                d[k][1] += max(end, 0)

    def st_cell(cat, d, key):
        if not inventory:
            return "–"
        sold, left = d.get(key, [0, 0])
        if cat not in real_st:
            return "not reliable"
        return p100(pct(sold, sold + left)) if sold + left else "–"

    # ---------- pace (print × silhouette, relisted versions merged) ----------
    pace = {}
    if monthly:
        series = defaultdict(lambda: defaultdict(lambda: [0.0, 0.0, 0.0]))
        for r in monthly:
            if is_unnamed(r["product_title"]) or r["month"][:7] >= this_month:
                continue
            cat, prnt, sil = classify(r["product_title"])
            s = series[(cat, prnt, sil)][r["month"][:7]]
            s[0] += num(r["net_items_sold"])
            s[1] += num(r["gross_sales"])
            s[2] += -num(r["discounts"])
        for key, ms in series.items():
            sold = sorted(m for m, v in ms.items() if v[0] > 0)
            if not sold or not last_m:
                continue
            launch = sold[0]
            on_sale = month_index(last_m) - month_index(launch) + 1
            win = [m for m in ms if 0 <= month_index(m) - month_index(launch) < W]
            tu = sum(v[0] for v in ms.values())
            pace[key] = {
                "launch": launch, "before_data": launch == first_m, "months_on_sale": on_sale,
                "window_units": sum(ms[m][0] for m in win),
                "window_discount": pct(sum(ms[m][2] for m in win), sum(ms[m][1] for m in win)),
                "units": tu, "per_month": pct(tu, on_sale),
            }

    def months_on(cat, sil=None, prnt=None):
        vals = [p["months_on_sale"] for k, p in pace.items()
                if k[0] == cat and (sil is None or k[2] == sil) and (prnt is None or k[1] == prnt)]
        return max(vals) if vals else None

    # =====================================================================
    out.append("# PRNTCODE collection review · stage 00 starting point")
    out.append(f"_Shopify sales, {period}. Directional only (PC-OPS-CDP-09). Feeds stage 00 and stage 02. Not for stage 01, which runs without sales data._")

    # ---------- PART 1 ----------
    out.append("\n## Part 1 · Stage 00 inputs (envelope and collection budget)")

    out.append("\n### 1.1 Sell-through by print and category")
    out.append(f"_Sell-through = units sold ÷ (sold + still in stock), shown only where stock counts are real ({', '.join(sorted(real_st))}). Abaya stock isn't reliable, so abayas show units a month instead._")
    rows = []
    for c in cats:
        prs = sorted([k for k in by_pc if k[1] == c], key=lambda k: -by_pc[k]["net"])
        for k in prs:
            v = by_pc[k]
            mo = months_on(c, prnt=k[0])
            rows.append([c, k[0], f"{v['units']:.0f}", aed(v["net"]), p100(pct(v["disc"], v["gross"])),
                         st_cell(c, stock_pc, k), f"{pct(v['units'], mo):.1f}" if mo else "–"])
    out.append(table(["Category", "Print", "Units", "Net AED", "Discount", "Sell-through", "Units / month"], rows))

    out.append("\n### 1.2 What the year absorbed, by category")
    out.append("_The demand baseline behind each budget scenario's unit buy. Last 6 months shows the current run rate; ready-to-wear launched mid-year, so its average understates it._")
    cat_month = defaultdict(lambda: defaultdict(float))
    if monthly:
        for r in monthly:
            if is_unnamed(r["product_title"]) or r["month"][:7] >= this_month:
                continue
            cat, _, _ = classify(r["product_title"])
            cat_month[cat][r["month"][:7]] += num(r["net_items_sold"])
    rows = []
    last6 = [m for m in complete if last_m and month_index(last_m) - month_index(m) < 6]
    for c in cats:
        v = by_cat[c]
        cm = cat_month.get(c, {})
        rows.append([c, f"{v['units']:.0f}", aed(v["net"]), p100(pct(v["net"], named_net)),
                     aed(pct(v["net"], v["units"])),
                     f"{pct(v['units'], n_months):.1f}" if n_months else "–",
                     f"{sum(cm.get(m, 0) for m in last6) / len(last6):.1f}" if last6 and cm else "–"])
    out.append(table(["Category", "Units", "Net AED", "Share", "Avg AED / unit", "Units / month", "Last 6 months / month"], rows))
    result["categories"] = {c: dict(by_cat[c]) for c in cats}

    out.append("\n### 1.3 Stock still on hand")
    out.append("_Units only. Book value needs landed cost from the costing sheet._")
    if inventory:
        rows = []
        for k in sorted(stock_pc, key=lambda k: (k[1], -stock_pc[k][1])):
            left = stock_pc[k][1]
            if left <= 0:
                continue
            rows.append([k[1], k[0], f"{left:.0f}", "unverified: check against a count" if k[1] not in real_st else ""])
        out.append(table(["Category", "Print", "Units in stock", "Note"], rows))
        if placeholder:
            out.append(f"\nLeft out as placeholder stock (≥{thr} units): " + "; ".join(placeholder))
        if preorder:
            out.append("\nLeft out as pre-order allowances, not stock: " + "; ".join(preorder))
        if no_sales:
            out.append("\nIn stock but no sale in the period: " + "; ".join(f"{t} ({e:.0f})" for _, t, e in no_sales))
        result["stock"] = {f"{k[0]} / {k[1]}": v[1] for k, v in stock_pc.items()}
    else:
        out.append("_inventory.json missing: skipped._")

    out.append("\n### 1.4 Sales not tied to a product")
    out.append(f"AED {aed(un_net)} across {un_units:.0f} items ({p100(pct(un_net, tot_net))} of net sales of AED {aed(tot_net)}): custom line items and blank or 'Untitled' listings. Left out of every table above.")
    if monthly:
        for r in monthly:
            if is_unnamed(r["product_title"]) and num(r["net_items_sold"]) >= 50:
                out.append(f"- {r['month'][:7]}: {num(r['net_items_sold']):.0f} items, AED {aed(num(r['gross_sales']) + num(r['discounts']))} (likely one bulk or custom order)")
    result["headline"] = {"period": period, "net_sales": tot_net, "named_net": named_net, "unnamed_net": un_net, "unnamed_units": un_units}

    # ---------- PART 2 ----------
    out.append("\n## Part 2 · Stage 02 inputs (factory silhouette selection and commercial core, Track A)")
    out.append("_Prior sell-through, directional. For choosing blocks and pairing prints to them. Print allocation itself is Hessa's, at stage 01._")

    out.append("\n### 2.1 Silhouettes: what to carry into Track A")
    rows, calls = [], []
    for c in cats:
        sils = sorted([k for k in by_sil if k[0] == c], key=lambda k: -by_sil[k]["net"])
        fair = by_cat[c]["net"] / len(sils) if sils else 0
        for k in sils:
            v = by_sil[k]
            disc = pct(v["disc"], v["gross"])
            mo = months_on(c, sil=k[1])
            if mo is not None and mo < W:
                call = "Too new to call"
            elif v["units"] < minu:
                call = "Drop from Track A (could return as Track B)" if mo is not None else "Too few to call"
            elif disc > cat_disc[c] + margin:
                call = "Carry only if reworked: sold on discount"
            elif pct(v["returned"], v["ordered"]) > ret_max:
                call = "Carry only if reworked: high returns"
            elif v["net"] >= fair:
                call = "Carry into Track A"
            else:
                call = "Watch"
            ret = pct(v["returned"], v["ordered"])
            rows.append([c, k[1], f"{v['units']:.0f}", aed(v["net"]), p100(disc), p100(ret), st_cell(c, stock_sil, k), call])
            calls.append({"category": c, "silhouette": k[1], "units": v["units"], "discount": disc, "returns": ret, "call": call})
    out.append(f"_Rules: fewer than {W} months on sale = too new; under {minu} units = drop from Track A; discount over {p100(margin)} points above its category, or returns over {p100(ret_max)}, = rework; at or above its fair share of category sales = carry. Overrule any call with a reason._")
    out.append(table(["Category", "Silhouette", "Units", "Net AED", "Discount", "Returns", "Sell-through", "Call"], rows))
    out.append("_Returns = units returned ÷ units ordered. A high rate on a block-based silhouette is a fit or quality question for Deepwear at stage 02._")
    result["silhouettes"] = calls

    out.append("\n### 2.2 Print × category pairing")
    out.append("_Which prints have sold on which category. Evidence for pairing at stage 02, not for choosing prints._")
    pc_cats = [c for c in cats if c in ("Abaya", "Ready-to-wear")] or cats
    prints = sorted({k[0] for k in by_pc if k[1] in pc_cats and by_pc[k]["units"] > 0},
                    key=lambda p: -sum(by_pc[k]["net"] for k in by_pc if k[0] == p))
    rows, pairs = [], []
    for p in prints:
        row = [p]
        for c in pc_cats:
            v = by_pc.get((p, c))
            n_pr = len([k for k in by_pc if k[1] == c])
            fair = by_cat[c]["net"] / n_pr if n_pr else 0
            if not v or v["units"] <= 0:
                label = "not tried"
            elif v["units"] < minu:
                label = f"{v['units']:.0f} · thin"
            elif pct(v["disc"], v["gross"]) > cat_disc[c] + margin:
                label = f"{v['units']:.0f} · on discount"
            elif v["net"] >= fair:
                label = f"{v['units']:.0f} · proven"
            else:
                label = f"{v['units']:.0f} · modest"
            row.append(label)
            pairs.append({"print": p, "category": c, "label": label})
        rows.append(row)
    out.append(table(["Print"] + pc_cats, rows))
    result["pairings"] = pairs

    out.append("\n### 2.3 Price tier coverage")
    out.append("_List price = gross sales ÷ units ordered, before discount and returns. Bands are set in catalogue-map.json; swap in the established price tier structure when it's written down._")
    rows = []
    for c in pc_cats:
        tot = sum(v["units"] for k, v in by_band.items() if k[0] == c)
        for _, _, label in bands:
            v = by_band.get((c, label))
            if v and v["units"]:
                rows.append([c, label, f"{v['units']:.0f}", p100(pct(v["units"], tot)), aed(v["net"]), p100(pct(v["disc"], v["gross"]))])
    out.append(table(["Category", "List price (AED)", "Units", "Share", "Net AED", "Discount"], rows))

    out.append("\n### 2.4 Size run")
    if variants:
        sizes = defaultdict(lambda: defaultdict(float))
        colours = defaultdict(float)
        for r in variants:
            t = r.get("product_title", "")
            if is_unnamed(t):
                continue
            cat, _, _ = parse_title(t, r.get("product_type", ""))
            u = num(r["net_items_sold"])
            size = colour = None
            for part in [p.strip() for p in (r.get("product_variant_title") or "").split("/") if p.strip()]:
                key = next((k for k in MAP["size_words"] if k.lower() == part.lower()), None)
                if key:
                    size = MAP["size_words"][key]
                elif part.isdigit() or any(part.lower() == f.lower() for f in MAP["fabric_words"]):
                    continue
                elif cat == "Abaya":
                    colour = part.title()
            if size and cat in ("Abaya", "Ready-to-wear"):
                sizes[cat][size] += u
            if colour:
                colours[colour] += u
        order = ["XS", "Small", "Medium", "Large", "XL"]
        rows = []
        for c in pc_cats:
            s = sizes.get(c)
            if not s:
                continue
            tot = sum(s.values())
            ratio = ratio_of_ten({z: s[z] for z in order if s.get(z)})
            rows.append([c] + [f"{s[z]:.0f} ({p100(pct(s[z], tot))})" if s.get(z) else "–" for z in order]
                        + [" : ".join(str(ratio[z]) for z in order if z in ratio)])
        out.append(table(["Category"] + order + ["Ratio out of 10"], rows))
        if colours:
            tot = sum(colours.values())
            out.append("\n**Abaya colourways (indicative):** older listings only; newer ones keep colour in the SKU. "
                       + ", ".join(f"{k} {p100(pct(v, tot))}" for k, v in sorted(colours.items(), key=lambda x: -x[1]) if v))
        result["sizes"] = {c: dict(s) for c, s in sizes.items()}
    else:
        out.append("_variants.json missing: skipped._")

    # ---------- APPENDIX ----------
    out.append("\n## Appendix")

    out.append("\n### A. Where it sells (share of net sales)")
    if channels:
        group_of = {n: g for g, names in MAP["channel_groups"].items() for n in names}
        groups = list(MAP["channel_groups"]) + ["Other"]
        ch = defaultdict(lambda: defaultdict(float))
        for r in channels:
            if is_unnamed(r["product_title"]):
                continue
            cat, _, _ = classify(r["product_title"])
            ch[cat][group_of.get(r["sales_channel"], "Other")] += num(r["net_sales"])
        out.append(table(["Category"] + groups,
                         [[c] + [p100(pct(ch[c].get(g, 0), sum(ch[c].values()))) for g in groups] for c in cats if c in ch]))
    else:
        out.append("_channels.json missing: skipped._")

    out.append(f"\n### B. Launch and pace (first {W} months after the first sale)")
    if pace:
        out.append(f"_≤ = already selling when the data starts, so not a true launch. Counted to {last_m}._")
        rows = [[k[0], k[1], k[2], ("≤" if p["before_data"] else "") + p["launch"], str(p["months_on_sale"]),
                 f"{p['window_units']:.0f}", p100(p["window_discount"]), f"{p['per_month']:.1f}"]
                for k, p in sorted(pace.items(), key=lambda x: (x[0][0], -x[1]["per_month"]))]
        out.append(table(["Category", "Print", "Silhouette", "First sale", "Months", f"Units, first {W}m", "Discount then", "Units / month"], rows))
    else:
        out.append("_monthly.json missing: skipped._")

    if focus:
        f = focus.lower()
        out.append(f"\n### C. Focus: {focus}")
        hits = [f"Sold: {r['product_title']}: {num(r['net_items_sold']):.0f} units, AED {aed(num(r['net_sales']))}"
                for r in products if f in (r.get("product_title") or "").lower()]
        hits += [f"Listed: {r['product_title']}: {num(r['ending_inventory_units']):.0f} in stock, {num(r['inventory_units_sold']):.0f} sold"
                 for r in (inventory or []) if f in (r.get("product_title") or "").lower()]
        out += [f"- {h}" for h in hits] or [f"- No listing with '{focus}' in its title yet."]
        result["focus"] = hits

    print("\n".join(out))
    if json_out:
        json.dump(result, open(json_out, "w"), indent=2, default=list)


if __name__ == "__main__":
    main()
