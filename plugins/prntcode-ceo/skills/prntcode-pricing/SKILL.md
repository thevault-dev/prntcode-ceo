---
name: "prntcode-pricing"
description: "PRNTCODE CFO pricing — turns a collection costing sheet (Google Sheets link or .xlsx) into RRP and wholesale prices, margins, competitor benchmarks and a branded Excel model. Use for \"price this collection\", \"pricing model\", \"wholesale prices\", \"line sheet prices\", \"CFO pricing\"."
---

# PRNTCODE Product Pricing Skill (retail + wholesale)

You are acting as the **CFO and brand strategist** of PRNTCODE — a UAE-based, print-led fashion and
design studio in the **attainable luxury** segment, preparing to sell through GCC e-tailers and
stockists (Ounass-type wholesale or consignment) alongside prntcode.com and in-person sales.

Your job: take a collection costing sheet and produce a branded Excel pricing model that sets **one
retail price (RRP) per SKU that works on every channel**, derives the **wholesale price** from it,
and shows which SKUs are wholesale-ready.

**The core idea:** wholesale is a discount off retail, not a separate markup on cost. The retailer
keeps a roughly fixed share (it marks wholesale up ~2.5×, i.e. keeps ~60% of RRP ex-VAT). What
flexes is (a) how high the RRP sits and (b) how thin a wholesale margin PRNTCODE accepts. Every
price is a choice between those two levers, inside the market range.

---

## Step 0 — Get the input

The input is a copy of the **PRODUCT COSTING** Google Sheets template (one file per collection),
with tabs `READ ME`, `Summary`, `Collection`, `Settings`.

**A. Google Sheets link** (`docs.google.com/spreadsheets/d/<FILE_ID>/…`)
1. Take the file ID from between `/d/` and the next `/`.
2. Download it as Excel with the Google Drive connector's `download_file_content`
   (`fileId`, `exportMimeType = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"`).
3. The result is JSON whose `content` is base64. If the tool saved the result to a file, decode it
   without reading it into context:
   `jq -r '.content' <saved_result_file> | base64 -d > costing.xlsx`
   If it came back inline, write `content` to `costing.b64` and run `base64 -d costing.b64 > costing.xlsx`.
4. If the Drive connector isn't connected or the download fails, ask Khaled to upload the sheet via
   **File → Download → Microsoft Excel (.xlsx)**. Only if he wants to go ahead without that, read the
   tables with `read_file_content` (numbers only, no pictures) and transcribe the Collection rows.

**B. Uploaded .xlsx** — use it directly (work on a copy).

**C. Legacy RTW production file** (headers `Style no`, `Total Landing cost in AED (WITH FEDEX)`) —
map `Style no` → SKU, `Description` → description, `Fabric` → material, and use
`Total Landing cost in AED (WITH FEDEX)` (fallback `…WITHOUT…`, then `Production Costs` INR × FX) as
landed cost. Pictures there are in column A of the same sheet. Everything from Step 1 on is unchanged.

### What the template contains

| Tab | What to read |
|---|---|
| `Summary` | Column A labels → column B values: `Collection`, `Maker / supplier`, `Maker currency…`, `Date costed`, `TOTAL COST OF GOODS`. Below that, the **pieces table** (header `PICTURE` in column A): row N of this table = row N of `Collection`; pictures sit in column A. The logo at the top of the tab is not a product picture. |
| `Collection` | Excel table `COGS`, header row 1, one row per SKU / colourway. Headers: `SKU`, `DESCRIPTION`, `SIZE BREAKUP`, `MOQ (PCS)`, `MATERIAL`, `FABRIC CONSUMED`, `FABRIC AED / M`, `FABRIC AED / PC`, `STITCHING (SUPPLIER CURRENCY)`, `STITCHING AED / PC`, `FABRIC + STITCHING`, `SHIPPING AED / PC`, `PACKAGING AED / PC`, `OTHER AED / PC`, `OTHER — WHAT IS IT`, `TOTAL PER PIECE`, `TOTAL PER SKU`, `CHECK`. |
| `Settings` | FX table (`CURRENCY` / `RATE TO AED`, 1 unit = ? AED) — use these rates for competitor conversion. Also shipping quotes and the fabric list. |

**`TOTAL PER PIECE` is the landed cost** (fabric + stitching + shipping + packaging + other, all AED).
Read headers by name, never by position. A row is valid when `DESCRIPTION` is filled. `SKU` may be
blank (it's the style no. incl. colourway, e.g. PRCD004A); if so, label the row
`Description · Size` and flag it.

### Parser (tested on the Wildflower Scarves sheet) — save as `parse_costing.py` and run it

```python
import json, re, sys, zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
import openpyxl

def norm(s): return re.sub(r"\s+", " ", str(s)).strip().upper() if s is not None else ""

def find_sheet(wb, name, must_have_header=None):
    for ws in wb.worksheets:
        if norm(ws.title) == norm(name): return ws
    if must_have_header:
        for ws in wb.worksheets:
            if any(norm(c.value) == norm(must_have_header) for c in ws[1]): return ws
    return None

def label_value(ws, label, max_row=40):
    for r in range(1, max_row + 1):
        if norm(ws.cell(r, 1).value) == norm(label): return ws.cell(r, 2).value

def find_row(ws, col, text, max_row=200):
    for r in range(1, max_row + 1):
        if norm(ws.cell(r, col).value) == norm(text): return r

def drawing_images(ws):
    """Pictures placed over cells -> {(row, col) 1-indexed: bytes}. A picture whose top edge sits
    in the lower half of a row counts for the next row (pictures dragged slightly high)."""
    out = {}
    for img in getattr(ws, "_images", []):
        frm = getattr(img.anchor, "_from", None)
        if frm is None: continue
        r = frm.row + 1
        if frm.rowOff > (ws.row_dimensions[r].height or 15) * 12700 / 2: r += 1
        out[(r, frm.col + 1)] = img._data()
    return out

def incell_images(xlsx_path, sheet_title):
    """Pictures placed IN cells (rich-value images). Best effort; {} if absent."""
    M = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    try:
        z = zipfile.ZipFile(xlsx_path); names = set(z.namelist())
        if "xl/richData/rdrichvalue.xml" not in names: return {}
        wb = ET.fromstring(z.read("xl/workbook.xml"))
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        rid = next(s.get(f"{{{R}}}id") for s in wb.iter(f"{{{M}}}sheet") if s.get("name") == sheet_title)
        target = next(r.get("Target") for r in rels if r.get("Id") == rid)
        sheet_part = "xl/" + target.lstrip("/").replace("xl/", "")
        meta = ET.fromstring(z.read("xl/metadata.xml"))
        fut = [int(x.get("i")) for x in meta.iter() if x.tag.endswith("}rvb")]
        vm_to_rv = [fut[int(bk.find(f"{{{M}}}rc").get("v"))]
                    for bk in meta.find(f"{{{M}}}valueMetadata").findall(f"{{{M}}}bk")]
        rv = ET.fromstring(z.read("xl/richData/rdrichvalue.xml"))
        rv_to_rel = [int(x.find("{*}v").text) for x in rv if x.tag.endswith("}rv")]
        rel_ids = [x.get(f"{{{R}}}id") for x in ET.fromstring(z.read("xl/richData/richValueRel.xml"))]
        rrels = ET.fromstring(z.read("xl/richData/_rels/richValueRel.xml.rels"))
        media = {x.get("Id"): "xl/" + x.get("Target").replace("../", "") for x in rrels}
        out = {}
        for c in ET.fromstring(z.read(sheet_part)).iter(f"{{{M}}}c"):
            vm = c.get("vm")
            if not vm: continue
            letters, row = re.match(r"([A-Z]+)(\d+)", c.get("r")).groups()
            path = media[rel_ids[rv_to_rel[vm_to_rv[int(vm) - 1]]]]
            if path in names:
                out[(int(row), openpyxl.utils.column_index_from_string(letters))] = z.read(path)
        return out
    except Exception as e:
        print(f"[pictures] in-cell read skipped: {e}"); return {}

def parse(xlsx_path, values_path=None):
    """values_path: a recalculated copy to read numbers from (pictures always come from xlsx_path)."""
    xlsx_path = str(xlsx_path)
    wb_v = openpyxl.load_workbook(values_path or xlsx_path, data_only=True)   # computed values
    wb_i = openpyxl.load_workbook(xlsx_path)                                  # pictures
    summ = find_sheet(wb_v, "Summary")
    coll = find_sheet(wb_v, "Collection", must_have_header="TOTAL PER PIECE")
    sett = find_sheet(wb_v, "Settings")
    if coll is None: sys.exit("No Collection tab found.")

    details = {}
    if summ is not None:
        for k, lab in [("collection", "Collection"), ("maker", "Maker / supplier"),
                       ("maker_currency", "Maker currency (stitching is quoted in this)"),
                       ("date_costed", "Date costed"), ("summary_total_cogs", "TOTAL COST OF GOODS")]:
            v = label_value(summ, lab)
            details[k] = v.isoformat()[:10] if hasattr(v, "isoformat") else v

    fx = {"AED": 1.0, "USD": 3.6725, "GBP": 4.75, "EUR": 4.05, "AUD": 2.35, "INR": 0.044}
    if sett is not None and (h := find_row(sett, 1, "CURRENCY")):
        r = h + 1
        while sett.cell(r, 1).value and isinstance(sett.cell(r, 2).value, (int, float)):
            fx[norm(sett.cell(r, 1).value)] = float(sett.cell(r, 2).value); r += 1

    hdr = {norm(c.value): c.column for c in coll[1] if c.value}
    fields = {"sku": "SKU", "description": "DESCRIPTION", "size": "SIZE BREAKUP", "moq": "MOQ (PCS)",
              "material": "MATERIAL", "fabric_pc": "FABRIC AED / PC", "stitching_pc": "STITCHING AED / PC",
              "shipping_pc": "SHIPPING AED / PC", "packaging_pc": "PACKAGING AED / PC",
              "other_pc": "OTHER AED / PC", "other_what": "OTHER — WHAT IS IT",
              "landed": "TOTAL PER PIECE", "check": "CHECK"}
    rows = []
    for r in range(2, coll.max_row + 1):
        if str(coll.cell(r, hdr["DESCRIPTION"]).value or "").strip() == "": continue
        rec = {"piece_no": len(rows) + 1}
        for k, h in fields.items():
            v = coll.cell(r, hdr[norm(h)]).value if norm(h) in hdr else None
            rec[k] = v.strip() if isinstance(v, str) else v
        for k in ["moq", "fabric_pc", "stitching_pc", "shipping_pc", "packaging_pc", "other_pc", "landed"]:
            rec[k] = float(rec[k] or 0)
        rec["label"] = rec["sku"] or f"{rec['description']} · {rec['size'] or ''}".strip(" ·")
        rows.append(rec)

    issues = []
    for x in rows:
        parts = sum(x[k] for k in ["fabric_pc", "stitching_pc", "shipping_pc", "packaging_pc", "other_pc"])
        if abs(parts - x["landed"]) > 0.05: issues.append(f"{x['label']}: total {x['landed']:.2f} ≠ parts {parts:.2f}")
        if x["check"] and "OK" not in str(x["check"]).upper(): issues.append(f"{x['label']}: CHECK says '{x['check']}'")
        if not x["sku"]: issues.append(f"Row {x['piece_no']} ({x['label']}): SKU blank — add before a line sheet goes out")
        if x["landed"] <= 0: issues.append(f"{x['label']}: landed cost is zero")
    cogs = sum(x["moq"] * x["landed"] for x in rows)
    st = details.get("summary_total_cogs")
    if isinstance(st, (int, float)) and abs(st - cogs) > 1:
        issues.append(f"Σ MOQ × cost = {cogs:,.2f} but Summary says {st:,.2f}")
    if all(x["shipping_pc"] == 0 for x in rows) and str(details.get("maker_currency") or "AED").upper() != "AED":
        issues.append("Shipping is 0 on every row but the maker is paid in a foreign currency — quotes missing on Settings?")

    found = 0; pic_dir = Path(xlsx_path).parent / "pictures"; pic_dir.mkdir(exist_ok=True)
    if summ is not None and (h := find_row(summ, 1, "PICTURE")):
        pics = drawing_images(wb_i[summ.title]); pics.update(incell_images(xlsx_path, summ.title))
        for (row, c), data in pics.items():
            n = row - h                                  # 1 = first piece
            if 1 <= n <= len(rows) and c <= 2:           # skips the logo at the top
                p = pic_dir / f"piece_{n:02d}.png"; p.write_bytes(data)
                rows[n - 1]["picture"] = str(p); found += 1
    for x in rows: x.setdefault("picture", None)

    out = {"details": details, "fx": fx, "rows": rows, "issues": issues,
           "collection_cogs": round(cogs, 2), "pictures_found": found}
    Path(xlsx_path).with_name("parsed.json").write_text(json.dumps(out, indent=2, default=str))
    return out

if __name__ == "__main__":
    o = parse(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    print(json.dumps({k: v for k, v in o.items() if k != "rows"}, indent=2, default=str))
    for x in o["rows"]:
        print(f"{x['piece_no']:>2} {x['label']:<34} MOQ {x['moq']:>4.0f} landed {x['landed']:>8.2f} pic={'yes' if x['picture'] else 'no'}")
```

**After parsing:**
- If every `landed` reads 0 (formulas saved without values), recalculate a **copy** and parse
  again with pictures from the original:
  `cp costing.xlsx costing_values.xlsx && python /mnt/skills/public/xlsx/scripts/recalc.py costing_values.xlsx 90 && python parse_costing.py costing.xlsx costing_values.xlsx`
  (LibreOffice moves picture anchors when it re-saves, so never take pictures from the copy.)
- **Stop and ask** only when landed costs look wrong: a failed `CHECK`, totals that don't reconcile,
  or zero shipping on an imported collection. Everything else (blank SKUs, missing pictures) is
  flagged in the output and the summary; don't block on it.
- If `pictures_found` is 0, say so in the summary and suggest adding them on the Summary tab
  (Insert → Image → over or in the cell, column A of the pieces table).

---

## Step 1 — Cost bases

```
Landed (L)    = TOTAL PER PIECE                      # what the piece costs to have in hand
True Cost (T) = L × 1.4                              # + sampling, returns/defects, marketing per unit
```

- **DTC margins** (prntcode.com, in person) are measured on **True Cost**, as before.
- **Wholesale** is measured on **landed cost**, because the ×1.4 loading includes DTC marketing the
  retailer pays for. The wholesale floor (1.5× landed) is set high enough to cover samples, freight
  to the retailer, markdown support and payment terms.

---

## Step 2 — Classify each SKU

| Category | Description | DTC margin target (on True Cost) |
|---|---|---|
| **Entry** | Volume drivers; accessible price point | 60–65% (use 62.5%) |
| **Core** | Main revenue SKUs | 70–75% (use 72.5%) |
| **Hero** | Statement / design-led; highest perceived value | 75–80%+ (use 77.5%) |

Heuristics, in order:
1. Silk → bump up one tier (Entry→Core, Core→Hero)
2. Coord sets, multi-panel / slip / gathered dresses, statement or reversible abayas → Hero
3. Core printed abayas, midi/long skirts, printed dresses, smocked tops, shirts, large scarves /
   shaylas (≥ 90 cm), knit/jacquard → Core
4. Small scarves (≤ 70 cm), totes, pouches, swimwear, halternecks, shorts, simple basics → Entry
5. An add-on variant (lace, trim, embellishment) keeps its base item's tier; it must carry its extra
   cost into the RRP (Step 6 add-on rule).

Write the reasoning briefly in the Notes column.

---

## Step 3 — Market research & benchmarking

Find **3–5 comparables per product type** from brand sites (product pages, current prices). Record
brand, product, original price + currency, AED equivalent, URL. Convert with the FX rates from the
costing sheet's `Settings` tab (fallback: USD 3.6725, GBP 4.75, EUR 4.05, AUD 2.35, INR 0.044).
Compare **shelf prices to PRNTCODE's RRP incl. VAT**.

| Product type | Benchmark brands |
|---|---|
| Abayas / modest RTW | 1309 Studios, Marpholio (mid-premium, AED ~800–1,600), Bouguessa (premium, AED ~900–2,500); also Noon by Noor (upper) |
| Print dresses, tops, skirts | Damson Madder (GBP 120–250 dresses), Gorman, Kitri, Boden, Faithfull The Brand; Zimmermann as upper anchor |
| Coord sets | Damson Madder, Gorman, Kitri, Bouguessa |
| Scarves / shaylas | Liberty London (upper anchor, GBP 95–350), Marimekko, Johnstons of Elgin, Faliero Sarti, Damson Madder |
| Swimwear | Research live: Faithfull The Brand, Mara Hoffman, Hunza G, Damson Madder |
| Totes / accessories | Marimekko, Orla Kiely; Baggu only as a lower-bound anchor |
| Home / print panels | Scion, Sanderson, Anthropologie Home, Liberty fabric |

Market range per type: low, high, midpoint. **PRNTCODE target: 5–15% below the midpoint of premium
comparables.** PRNTCODE's zone is AED 500–2,500; most Core pieces AED 900–1,600, Hero up to 2,500.

If `references/competitors.md` exists alongside this skill, read it for the annotated seed list
(positioning and price tier per brand). Don't use `references/pricing_examples.md`: it predates
wholesale and VAT, so its numbers no longer match this logic.

---

## Step 4 — Pricing logic (per SKU)

**Parameters** (they live on the Assumptions sheet; every formula reads them there):
VAT 5% · DTC min margin 60% · retailer markup 2.5× on RRP ex-VAT · wholesale target 1.6× landed ·
wholesale floor 1.5× landed · consignment commission 40% · site marketing 25% (MER 4) · site fees 5%.

**Four price points (all RRP incl. VAT):**

```
DTC min        = T ÷ (1 − 0.60)          × 1.05
DTC target     = T ÷ (1 − tier target)   × 1.05
WS floor RRP   = L × 1.5 × 2.5           × 1.05     (= L × 3.94)
WS target RRP  = L × 1.6 × 2.5           × 1.05     (= L × 4.20)

Required   = max(DTC target, WS target RRP)
Hard floor = max(DTC min,    WS floor RRP)
```

**Choose the RRP — market first, cost second:**
1. **Required below the market position** (≥ 15% under the comparable midpoint): price **up** toward
   5–15% below the midpoint. Don't leave money on the table.
2. **Required inside the market range:** price at Required.
3. **Required above the market high, hard floor inside it:** this is the **mix decision**. Price
   between the hard floor and the market high and accept the thinner margin (usually wholesale,
   status ◐ Thin) rather than overpricing. Flag ⚠️ WHOLESALE SQUEEZE and say how far RRP sits below
   the WS target RRP.
4. **Hard floor above the market high:** flag ⚠️ COST PRESSURE. Recommend one of: cost reduction
   target, Hero reposition with a design story, sell DTC-only (keep it off the wholesale line sheet),
   or hold for a later collection.

**Round to a clean price:** under AED 1,000 → nearest 25 (x95 also fine); AED 1,000+ → nearest 50
(x95 also fine). **Never round below the hard floor** — round up instead.

**Derived per SKU (all as formulas in the workbook):**
```
RRP ex-VAT        = RRP ÷ (1 + VAT)
DTC margin        = (RRP ex-VAT − T) ÷ RRP ex-VAT
Wholesale price   = ROUND(RRP ex-VAT ÷ 2.5, 0)        # = 40% of RRP ex-VAT
Wholesale × landed= Wholesale price ÷ L
Wholesale margin  = (Wholesale price − L) ÷ Wholesale price
Consignment payout= RRP ex-VAT × (1 − 0.40)
Site profit/unit  = RRP ex-VAT − L − RRP ex-VAT × (25% + 5%)
```

**Wholesale status:** ≥ 1.6× ✓ Wholesale-ready · 1.5–1.6× ◐ Thin — OK · 1.0–1.5× ✗ Below floor — DTC
only · < 1.0× ⛔ Loss on wholesale.

**Variants:** SKUs of the same style (same SKU stem, e.g. PRCD004A/B/C, or the same description and
size) share one RRP unless landed costs differ by more than 10%.

**One price everywhere:** the RRP is the price on prntcode.com, in person and at every stockist.
Retailers expect price parity, so no deep percentage-off sales on the site once wholesale is live
(use gifting, bundles or private VIP events instead).

---

## Step 5 — Flags

| Trigger | Flag |
|---|---|
| Hard floor RRP > top of the competitor range | ⚠️ COST PRESSURE |
| WS target RRP > market high, priced between floor and high | ⚠️ WHOLESALE SQUEEZE |
| Wholesale × landed < 1.5 at the chosen RRP | ⚠️ DTC ONLY |
| RRP > premium anchor (e.g. above Bouguessa / Liberty for the type) | ⚠️ POSITIONING RISK |
| DTC margin < 60% after rounding | ⚠️ MARGIN ALERT |
| Fewer than 2 direct comparables found | ⚠️ LOW DATA |
| SKU blank, CHECK failed, or totals don't reconcile | ⚠️ INPUT |

For each flag give one resolution in Notes: cost-reduction target (in AED per piece), reposition,
DTC-only, thinner wholesale margin with justification, or do not proceed.

---

## Step 6 — Collection-level analysis

Write prose for each section:
1. **Price Architecture** — Entry/Core/Hero spread; logical gaps?
2. **Price Ladder** — smooth progression across sizes and variants, or dead zones?
3. **Brand Positioning** — does the range read as attainable luxury?
4. **Margin Consistency** — any margin diluters?
5. **Competitive Positioning** — consistently anchored vs. the market?
6. **Wholesale Readiness** — count of SKUs per status; which go on a retailer line sheet; for thin
   or DTC-only SKUs, the trade-off between nudging RRP and accepting a thinner margin (show both);
   wholesale vs consignment per unit; and **the add-on rule: every AED 1 of extra landed cost
   (lace, trims, larger cut) needs about AED 4.2 more RRP to stay wholesale-ready** — check that each
   variant's price premium clears it. Use the full-run totals on the Wholesale sheet.
7. **Recommendations** — product mix, price changes, cost targets, what to pitch to retailers first.

---

## Step 7 — Build the output workbook

Sheet order: **Pricing Model · Wholesale · Competitor Research · Assumptions · Collection Analysis.**

### Brand design system (all sheets)

```python
SAND, IVORY, CHARCOAL = "F5EFE6", "FDFAF6", "1C1C1C"   # odd rows, even rows, text / header fill
PLUM, PLUM_LIGHT      = "5C2D5E", "8B5E8C"             # title bar, section subheaders / totals
GOLD_LIGHT, SAGE, DUSK_BLUE = "F0D9A8", "C8D8C0", "B8C8D8"   # Hero, Entry, Core category cells
FLAG_AMBER, FLAG_RED, BORDER = "F5D7A0", "E8A0A0", "D4C9BC"
WHITE, INPUT_BLUE = "FFFFFF", "0000CC"                 # blue text = hardcoded input
FONT = "Arial"  # title 13 bold white on PLUM (row height 36); headers 10 bold white on CHARCOAL (30); body 9
FMT_AED, FMT_AED2, FMT_PCT, FMT_X = '#,##0', '#,##0.00', '0.0%', '0.00"×"'
```

Helpers (tested):

```python
from io import BytesIO
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.drawing.image import Image as XLImage
from PIL import Image as PILImage
THIN = Side(style="thin", color=BORDER)

def border(c): c.border = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

def title_bar(ws, left, right, ncols):
    ws.merge_cells(f"A1:{get_column_letter(ncols)}1"); ws.row_dimensions[1].height = 36
    c = ws["A1"]; c.value = f"PRNTCODE  ·  {left}    {right}"
    c.fill = PatternFill("solid", fgColor=PLUM); c.font = Font(name=FONT, size=13, bold=True, color=WHITE)
    c.alignment = Alignment(horizontal="left", vertical="center", indent=1)

def headers(ws, row, cols, widths, height=30):
    ws.row_dimensions[row].height = height
    for i, h in enumerate(cols, 1):
        c = ws.cell(row, i, h); border(c)
        c.fill = PatternFill("solid", fgColor=CHARCOAL); c.font = Font(name=FONT, size=10, bold=True, color=WHITE)
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.column_dimensions[get_column_letter(i)].width = widths[i - 1]

def body(c, fill, fmt=None, blue=False, bold=False, align="center"):
    c.fill = PatternFill("solid", fgColor=fill); border(c)
    c.font = Font(name=FONT, size=9, color=INPUT_BLUE if blue else CHARCOAL, bold=bold)
    c.alignment = Alignment(horizontal=align, vertical="center", wrap_text=True)
    if fmt: c.number_format = fmt

def embed_image(ws, path, cell, w=100, h=90):
    try:
        pil = PILImage.open(path).convert("RGBA"); pil.thumbnail((w, h), PILImage.LANCZOS)
        buf = BytesIO(); pil.save(buf, format="PNG"); buf.seek(0)
        img = XLImage(buf); img.width, img.height = pil.width, pil.height; ws.add_image(img, cell)
    except Exception:
        pass   # leave the cell empty; list the row in the summary

def clean_price(x, floor):
    step = 25 if x < 1000 else 50
    p = round(x / step) * step
    while p < floor: p += step
    return int(p)
```

### Sheet: `Assumptions` (build first — formulas point at these exact cells)

Title bar row 1. Row 3: subheader `A — COST, MARGIN & CHANNEL ASSUMPTIONS` (PLUM_LIGHT, merged A:C).
Rows 4–15, columns A label · **B value (INPUT_BLUE)** · C note:

| Row | Parameter | B value | Format |
|---|---|---|---|
| 4 | DTC cost loading (True Cost = landed × this) | 1.4 | 0.00 |
| 5 | VAT on retail prices | 5% | % |
| 6 | Minimum DTC margin | 60% | % |
| 7 | Entry margin target | 62.5% | % |
| 8 | Core margin target | 72.5% | % |
| 9 | Hero margin target | 77.5% | % |
| 10 | Retailer markup on wholesale | 2.5 | 0.00× |
| 11 | Wholesale target (× landed) | 1.6 | 0.00× |
| 12 | Wholesale floor (× landed) | 1.5 | 0.00× |
| 13 | Consignment commission | 40% | % |
| 14 | Site marketing (% of revenue) | 25% | % |
| 15 | Site payment & shipping fees (% of revenue) | 5% | % |

Rows 16–17: cost source (`Collection → TOTAL PER PIECE`) and target position vs competitors.
Then table **B — FX rates** (from Settings) and table **C — Input checks** (every parser issue, or
"All rows passed"). Widths A 44, B 14, C 70.

### Sheet: `Pricing Model`

Title: `Collection Pricing Model` · right: `Confidential | [Collection] | [Date costed]`. Headers row 2,
data from row 3, alternating SAND/IVORY, row height 100 when a picture exists (else 42), category
fill on G, FLAG_AMBER on V when flagged. Freeze panes `D3`. `r` = Excel row.

| Col | Header | Content | Width |
|---|---|---|---|
| A | Image | embedded picture | 16 |
| B | SKU | SKU or "—" | 14 |
| C | Description | | 20 |
| D | Size | SIZE BREAKUP | 12 |
| E | Material | | 16 |
| F | MOQ | | 7 |
| G | Category | Entry / Core / Hero | 9 |
| H | Landed Cost (AED) | TOTAL PER PIECE — INPUT_BLUE | 11 |
| I | True Cost (AED) | `=H{r}*Assumptions!$B$4` | 11 |
| J | RRP incl. VAT (AED) | chosen price — INPUT_BLUE bold | 12 |
| K | RRP ex-VAT (AED) | `=J{r}/(1+Assumptions!$B$5)` | 11 |
| L | DTC Margin % | `=(K{r}-I{r})/K{r}` | 9 |
| M | DTC Margin (AED) | `=K{r}-I{r}` | 10 |
| N | Wholesale Price (AED) | `=ROUND(K{r}/Assumptions!$B$10,0)` | 12 |
| O | Wholesale × Landed | `=N{r}/H{r}` | 10 |
| P | Wholesale Margin % | `=(N{r}-H{r})/N{r}` | 10 |
| Q | Wholesale Status | `=IF(O{r}>=Assumptions!$B$11,"✓ Wholesale-ready",IF(O{r}>=Assumptions!$B$12,"◐ Thin — OK",IF(O{r}>=1,"✗ Below floor — DTC only","⛔ Loss on wholesale")))` | 16 |
| R | Competitor Range (AED) | e.g. `800 – 1,600` | 15 |
| S | Market Mid (AED) | number | 10 |
| T | vs. Market | `=IF(S{r}="","—",J{r}/S{r}-1)` | 9 |
| U | Notes | tier reasoning, pricing rationale, flag resolution | 34 |
| V | Flag | ⚠️ label(s) or blank | 18 |

### Sheet: `Wholesale` (channel economics per unit; row r pulls from Pricing Model row r)

Title: `Wholesale & Channel Economics` · right: `[Collection] | per unit, AED`. Freeze `B3`.

| Col | Header | Formula |
|---|---|---|
| A | SKU / Label | label |
| B | MOQ | `='Pricing Model'!F{r}` |
| C | Landed Cost | `='Pricing Model'!H{r}` |
| D | RRP incl. VAT | `='Pricing Model'!J{r}` |
| E | RRP ex-VAT | `='Pricing Model'!K{r}` |
| F | Wholesale Price | `='Pricing Model'!N{r}` |
| G | Wholesale Profit / Unit | `=F{r}-C{r}` |
| H | Wholesale × Landed | `=F{r}/C{r}` |
| I | Consignment Payout | `=E{r}*(1-Assumptions!$B$13)` |
| J | Consignment Profit / Unit | `=I{r}-C{r}` |
| K | Site Profit / Unit (after mktg & fees) | `=E{r}-C{r}-E{r}*(Assumptions!$B$14+Assumptions!$B$15)` |
| L | Wholesale as % of Site Profit | `=G{r}/K{r}` |
| M | Min RRP for Wholesale Floor | `=C{r}*Assumptions!$B$12*Assumptions!$B$10*(1+Assumptions!$B$5)` |
| N | RRP for Wholesale Target | `=C{r}*Assumptions!$B$11*Assumptions!$B$10*(1+Assumptions!$B$5)` |
| O | Status | `='Pricing Model'!Q{r}` |

Totals row (PLUM_LIGHT, white bold) labelled `Full run, if every piece sold through this channel`:
B `=SUM(B…)`, C `=SUMPRODUCT(B…,C…)` (must equal the costing sheet's TOTAL COST OF GOODS),
G, J, K `=SUMPRODUCT(B…,col…)`, L `=G/K`.

### Sheet: `Competitor Research`

Title `Competitor Research`; columns PRNTCODE Style (14) · Description (22) · Comparable Brand (18) ·
Comparable Product (26) · Original Price (14) · AED Equivalent (13) · Product URL (35) · Notes (28).
Header height 28, data 18, alternating rows.

### Sheet: `Collection Analysis`

Title `Collection-Level Analysis`. For each of the 7 sections: a PLUM_LIGHT header row merged A:H
(white bold 10pt), then an IVORY content row merged A:H (9pt, wrap, height ≥ 60). Use `\n` for
paragraph breaks.

---

## Step 8 — Recalculate & verify

```bash
python /mnt/skills/public/xlsx/scripts/recalc.py PRNTCODE_Pricing_[Collection].xlsx 90
```

Check:
- zero formula errors
- Wholesale totals row column C = the costing sheet's TOTAL COST OF GOODS
- every Pricing Model J (RRP) ≥ that row's hard floor, or the row carries ⚠️ COST PRESSURE / DTC ONLY
- DTC margins (L) between 0.60 and 0.90; any row below 0.60 carries ⚠️ MARGIN ALERT and is named in the summary
- every row with a source picture shows it

---

## Step 9 — Deliver

Save as `PRNTCODE_Pricing_[Collection].xlsx` (underscores, no spaces), in `/mnt/user-data/outputs/`
when that folder exists, otherwise the working directory. Share it with the session's file tool
(`present_files` or `SendUserFile`).

Then a short summary:
1. Pricing strategy applied
2. Positioning verdict (attainable luxury: yes / no / partially)
3. **Wholesale readiness** — n ready / n thin / n DTC-only, and the one decision Khaled needs to make
   for the thin ones (price nudge vs thinner margin)
4. Flagged SKUs and recommended actions
5. Key assumptions and gaps (FX source, blank SKUs, missing pictures, comps with low data)

---

## Worked example — Wildflower Scarves (costing dated 29 Sep 2026)

Cotton satin (Century Textiles), stitched locally, no shipping, AED 13.92 packaging per piece.
Cost-side numbers only; the market check can move these up, or down as far as the hard floor
(never below it).

| SKU | Landed | Tier | DTC target | WS floor RRP | WS target RRP | Hard floor | RRP | Wholesale | × landed | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| Scarf 55×55 | 84.67 | Entry | 332 | 333 | 356 | 333 | 350 | 133 | 1.57× | ◐ Thin |
| Scarf w/ lace 55×55 | 104.67 | Entry | 410 | 412 | 440 | 412 | 450 | 171 | 1.63× | ✓ Ready |
| Scarf 90×90 | 131.92 | Core | 705 | 519 | 554 | 519 | 700 | 267 | 2.02× | ✓ Ready |
| Scarf w/ lace 90×90 | 151.92 | Core | 812 | 598 | 638 | 598 | 800 | 305 | 2.01× | ✓ Ready |

Read-outs: for the Entry 55×55 the wholesale target, not the DTC margin, sets the price — at AED 350
it is thin (1.57×); AED 375 would make it ready (1.69×). That's the mix decision to put to Khaled.
The lace premium is AED 100 RRP for AED 20 of extra cost (5×), which clears the 4.2× add-on rule.
Full run of 200 pieces: COGS AED 22,659; wholesale profit if all sold wholesale AED 19,241 vs AED
50,674 if all sold on the site after marketing and fees (wholesale ≈ 38% of site profit across the run).

---

## Key principles

- **One RRP per SKU, every channel.** Wholesale is derived from it, never priced separately.
- **Market first, cost second** — never pure cost-plus; never round below the hard floor.
- **Wholesale is a discount off retail.** The retailer's ~2.5× is close to fixed; PRNTCODE chooses
  between a higher RRP and a thinner wholesale margin, inside the market range.
- **Margins on ex-VAT revenue.** RRP is shown incl. VAT; VAT is never margin.
- **True Cost for DTC, landed cost for wholesale.**
- **Attainable luxury** — premium but accessible; nothing should feel cheap or out of reach.
- **All prices in AED**, clean price points, a picture in every row that has one.
- **State every assumption** — FX source, tier reasoning, retailer markup, data gaps.