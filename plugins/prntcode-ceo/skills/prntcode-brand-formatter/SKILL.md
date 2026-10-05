---
name: prntcode-brand-formatter
description: >
  PRNTCODE brand formatter. Use this skill whenever the user wants to format,
  style, or present any document, report, table, plan, or output in the PRNTCODE
  visual brand system. Triggers on: "put this in PRNTCODE format", "brand this",
  "make this on-brand", "format this as a PRNTCODE document", "apply brand
  guidelines", "style this for PRNTCODE", or any request to produce a
  professionally branded output for PRNTCODE. Works on any input — pricing
  sheets, content plans, reports, proposals, one-pagers, briefs, tables.
---

# PRNTCODE Brand Formatter

You are producing a branded document for PRNTCODE — a print-first creative
studio founded by Emirati artist Hessa Al Suwaidi. Every output must feel like
it came from the brand's design system: considered, editorial, intentional.
Not a generic formatted document. A PRNTCODE document.

Read this entire skill before producing any output.

---

## Brand Assets (bundled with this skill)

All assets are in `references/assets/` relative to this skill file:

### Grid backgrounds (use as document background texture)
- `grid-white.svg` — Off-White `#EFEADF` background, charcoal `#1B1B1B` grid lines at 10% opacity. Grid spacing: ~92px columns, ~92px rows.
- `grid-plum.svg` — Plum/dark `#391323` background, Feature Pink `#FF9395` grid lines at 10% opacity.
- `grid-green.svg` — Jungle Green `#282300` background, Feature Pink `#FF9395` grid lines at 10% opacity.

### Logos (use exact files, never recreate)
- `logo-pink-wordmark.png` — Core Wordmark in Feature Pink. Use on dark backgrounds (Plum, Green, Charcoal).
- `logo-white-wordmark.png` — Core Wordmark in White. Use on dark backgrounds as alternative.
- `logo-charcoal-wordmark.png` — Core Wordmark in Charcoal. Use on light/off-white backgrounds.
- `logo-pink-flexi.png` — Flexi-Wordmark (script) in Feature Pink. Use for document footers, cover pages, editorial signature.
- `logo-pink-supporting.png` — Supporting Wordmark (PRNTCODE©). Use on busy layouts, large-scale digital.

---

## Brand Colour System

### Primary palette
| Name | Hex | RGB | Use |
|---|---|---|---|
| Off-White | `#FFF9EF` / `#EFEADF` | 255,249,239 | Light bg, body text areas |
| Jungle Green | `#282300` | 40,35,0 | Dark palette bg |
| Plum | `#360D1E` / `#391323` | 54,13,30 | Dark accent bg |
| Charcoal | `#1B1B1B` | 27,27,27 | Dark body bg, text on light |
| Feature Pink | `#FF9395` | 255,147,149 | Primary accent, headlines on dark |
| Bright White | `#FFFFFF` | 255,255,255 | Text on darkest bgs |

### Palette selection
**Dark palette** (Jungle Green or Plum bg): Use Feature Pink `#FF9395` for headlines and accents. Off-White `#FFF9EF` for body text. Plum for secondary panels.

**Light palette** (Off-White bg): Use Charcoal `#1B1B1B` for all text. Feature Pink for accent labels and highlights only. Never use pink as body text on light bg.

### Excel/spreadsheet colour codes (openpyxl)
- Off-White bg: `FEFFF9EF` → use `FFF9EF`
- Jungle Green: `FF282300`
- Plum header: `FF360D1E`
- Feature Pink accent: `FFFF9395`
- Charcoal text: `FF1B1B1B`
- White text: `FFFFFFFF`

---

## Typography System

| Role | Font | Weight | Size guidance |
|---|---|---|---|
| Display / cover title | Silkscreen or Geist ExtraBold | 800 | 32–48pt |
| Section header | Geist SemiBold | 600 | 18–24pt |
| Sub-header | Geist Medium | 500 | 14–16pt |
| Body copy | Geist Regular | 400 | 10–12pt |
| Micro labels / tags | Geist Mono Regular | 400 | 8–10pt, UPPERCASE |
| Captions / footnotes | Geist Mono Light | 300 | 8pt |
| Accent / stamp text | Silkscreen Regular | 400 | 10–14pt |

**Font fallbacks for documents:** Courier New (Geist Mono substitute), Arial (Geist substitute), Georgia (display fallback).

**Never use:** Helvetica, Times New Roman, Calibri, or any system default font as a primary choice. Always substitute with the closest available from the PRNTCODE type system.

---

## Layout System (from Figma template board)

### Grid structure
- Documents use a visible grid as background texture — thin lines at 10% opacity
- Grid spacing: approximately 92px (web) / 0.96in (print)
- All content sits on this grid — nothing is placed arbitrarily

### Document anatomy (any format)
1. **Header strip** — Full-width. Dark palette (Plum or Jungle Green). Contains: logo left, document title right, date/ref right. Feature Pink wordmark on dark.
2. **Section labels** — Small Geist Mono uppercase tags. Feature Pink on dark sections. Charcoal on light sections. Acts as a wayfinding system.
3. **Content body** — Off-White or light bg. Charcoal text. Grid texture visible.
4. **Accent panels** — Plum or Jungle Green panels for callouts, summaries, key figures. Feature Pink headlines inside.
5. **Footer strip** — Full-width. Charcoal or dark bg. Flexi-Wordmark (script) left. Page number or tagline right in Geist Mono. "PRINT FIRST, ALWAYS." or similar micro-copy.
6. **Data tables** — Plum header row, Feature Pink header text, alternating Off-White / slightly darker rows. Charcoal body text. No default Excel blue.

### Figma template reference
The full PRNTCODE social template library is at:
- File: `0bhyfVEy0vxACwjve7ESqu`
- Key post nodes: `1:2102`, `1:1680` (node from brand brief)
- Key document patterns: Off-White body with Plum accent headers, grid texture, Geist Mono labels

---

## Output Types & How to Execute Each

### HTML document (preferred for rich formatting)
- Use inline CSS with PRNTCODE colour variables
- Embed grid texture as repeating SVG background-image
- Use Google Fonts import for Geist + Geist Mono
- Include logo as base64 or reference path
- Export to PDF via print-to-PDF

### Excel / XLSX spreadsheet
- Read the xlsx SKILL.md at `/mnt/skills/public/xlsx/SKILL.md` before building
- Use openpyxl
- Header rows: fill `FF360D1E` (Plum), font `FFFF9395` (Feature Pink), bold
- Subheader rows: fill `FF1B1B1B` (Charcoal), font `FFFFFFFF` (white)
- Alternating data rows: `FFFFF9EF` (Off-White) and `FFF5EFE0` (slightly darker)
- Accent rows (totals, highlights): fill `FF282300` (Jungle Green), font `FFFF9395`
- All column headers: Geist Mono style → set as Courier New, uppercase, 9pt
- Body data: Arial 10pt (Geist substitute)
- Apply thick Plum border `FF360D1E` around primary data tables
- Never use default blue Excel header style

### PDF document
- Read `/mnt/skills/public/pdf/SKILL.md` before building
- Use reportlab or weasyprint
- Background: Off-White `#FFF9EF` with SVG grid texture overlay
- Header band: Plum `#360D1E`, full width
- Body text: Charcoal `#1B1B1B`

### Notion page
- Use Notion callout blocks for accent panels (set colour to match brand)
- Use dividers between sections
- Can't apply custom fonts in Notion — use heading sizes and block types to approximate hierarchy
- Include logo URL in page header/cover if relevant

---

## Step-by-Step Process

### Step 1 — Understand the document
Read the input document fully. Identify:
- Document type (report, pricing sheet, brief, plan, table, etc.)
- Key sections and hierarchy
- Any data tables, images, or special content
- The intended audience (internal team, client, partner, public)

### Step 2 — Choose palette
- Internal / operational document → Light palette (Off-White bg, Charcoal text)
- Client-facing / presentation / cover → Dark palette (Plum or Jungle Green header, Off-White body)
- Creative brief / brand document → Mix: Dark header, light body, Plum accent panels

### Step 3 — Choose output format
Ask the user if not specified:
> "Would you prefer this as an Excel file, an HTML document (exportable to PDF), or a Notion page?"

Default to HTML if unspecified — it gives the richest PRNTCODE formatting and can be printed to PDF.

### Step 4 — Map content to layout
Apply the document anatomy:
- Extract document title → Header strip
- Extract section names → Section labels (Geist Mono uppercase)
- Extract body content → Content body with grid bg
- Extract key figures or callouts → Accent panels (Plum bg, Feature Pink text)
- Extract tables → Branded data tables
- Add footer with Flexi-Wordmark and "PRINT FIRST, ALWAYS."

### Step 5 — Build the output
For Excel: use openpyxl following xlsx SKILL.md
For HTML/PDF: build complete branded HTML with inline CSS
For Notion: use Notion MCP to create a properly structured page

### Step 6 — Add product images (if pricing or product document)
If the document references PRNTCODE products or prints:
- Fetch product images from `https://www.prntcode.com` using `web_fetch`
- For each product, find its URL on the site and extract the product image URL
- Embed images in the document alongside their product entry
- Images should be displayed at consistent size (e.g. 120×120px thumbnail in Excel, full-bleed in HTML)
- Do not use placeholder images — always use real PRNTCODE product photography

---

## Guardrails

- Never use default Microsoft Office formatting (blue headers, Calibri, etc.)
- Never use generic colour schemes — always PRNTCODE palette only
- Never omit the logo — every document gets a logo in the header
- Never omit the footer — every document gets the Flexi-Wordmark and tagline
- Grid texture background is mandatory on all digital outputs
- Tables must use Plum headers — never grey or blue
- Product documents must include product photography — never blank or placeholder
- All text labels and tags must be UPPERCASE in Geist Mono
- "PRINT FIRST, ALWAYS." is the standard footer tagline unless instructed otherwise

---

## Figma Template Reference Nodes

If Figma MCP is available (file: `0bhyfVEy0vxACwjve7ESqu`), pull these nodes
for visual reference before building:
- `1:2102` — Instagram post layout showing light palette document structure
- `1:1680` — Key reference node from brand brief
- `90:717` — Product announcement template (zigzag border, three-column layout)

Rate limit note: Figma MCP on Starter plan allows ~1 frame per session.
Prioritise fetching the most relevant template for the document type being built.
