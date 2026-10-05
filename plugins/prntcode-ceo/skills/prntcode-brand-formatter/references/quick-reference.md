# PRNTCODE Brand Formatter — Quick Reference

## Colour hex codes (copy-paste ready)

### For CSS / HTML
```css
:root {
  --off-white: #FFF9EF;
  --off-white-alt: #EFEADF;
  --jungle-green: #282300;
  --plum: #360D1E;
  --plum-alt: #391323;
  --charcoal: #1B1B1B;
  --feature-pink: #FF9395;
  --white: #FFFFFF;
}
```

### For openpyxl (Excel)
```python
PLUM       = "360D1E"   # Header fill
PINK       = "FF9395"   # Header text / accent
GREEN      = "282300"   # Accent row fill
CHARCOAL   = "1B1B1B"   # Dark text / subheader fill
OFF_WHITE  = "FFF9EF"   # Row 1 fill
OFF_WHITE2 = "F5EFE0"   # Row 2 fill (alternating)
WHITE      = "FFFFFF"   # Text on dark fills
```

## Grid CSS background (inline)
```css
background-image: repeating-linear-gradient(
  0deg,
  transparent,
  transparent 91px,
  rgba(27,27,27,0.08) 91px,
  rgba(27,27,27,0.08) 92px
),
repeating-linear-gradient(
  90deg,
  transparent,
  transparent 91px,
  rgba(27,27,27,0.08) 91px,
  rgba(27,27,27,0.08) 92px
);
background-color: #FFF9EF;
```

## Google Fonts import (HTML documents)
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600;700;800&family=Geist+Mono:wght@300;400;500&display=swap" rel="stylesheet">
```

## Document header HTML snippet
```html
<header style="
  background: #360D1E;
  padding: 24px 40px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 2px solid #FF9395;
">
  <img src="[logo-pink-wordmark]" height="28" alt="PRNTCODE">
  <div style="text-align:right;">
    <div style="font-family:'Geist Mono',monospace;font-size:9px;color:#FF9395;letter-spacing:2px;text-transform:uppercase;">[DOCUMENT TYPE]</div>
    <div style="font-family:'Geist Mono',monospace;font-size:9px;color:#FFF9EF;opacity:0.6;">[DATE]</div>
  </div>
</header>
```

## Document footer HTML snippet
```html
<footer style="
  background: #1B1B1B;
  padding: 20px 40px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 60px;
">
  <img src="[logo-pink-flexi]" height="24" alt="Prntcode">
  <span style="font-family:'Geist Mono',monospace;font-size:8px;color:#FF9395;letter-spacing:2px;text-transform:uppercase;">PRINT FIRST, ALWAYS.</span>
</footer>
```

## Excel table setup (openpyxl)
```python
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter

FILLS = {
    'plum':       PatternFill("solid", fgColor="360D1E"),
    'charcoal':   PatternFill("solid", fgColor="1B1B1B"),
    'green':      PatternFill("solid", fgColor="282300"),
    'off_white':  PatternFill("solid", fgColor="FFF9EF"),
    'off_white2': PatternFill("solid", fgColor="F5EFE0"),
}

FONTS = {
    'header':    Font(name="Courier New", bold=True, color="FF9395", size=9),
    'subheader': Font(name="Courier New", bold=True, color="FFFFFF", size=9),
    'body':      Font(name="Arial", color="1B1B1B", size=10),
    'body_dark': Font(name="Arial", color="FFF9EF", size=10),
    'accent':    Font(name="Courier New", bold=True, color="FF9395", size=10),
    'label':     Font(name="Courier New", color="FF9395", size=8),
}

BORDER_PLUM = Border(
    left=Side(style='medium', color='360D1E'),
    right=Side(style='medium', color='360D1E'),
    top=Side(style='medium', color='360D1E'),
    bottom=Side(style='medium', color='360D1E'),
)

def style_header_row(ws, row, cols):
    for col in range(1, cols+1):
        cell = ws.cell(row=row, column=col)
        cell.fill = FILLS['plum']
        cell.font = FONTS['header']
        cell.alignment = Alignment(horizontal='left', vertical='center')

def style_data_row(ws, row, cols, is_odd=True):
    fill = FILLS['off_white'] if is_odd else FILLS['off_white2']
    for col in range(1, cols+1):
        cell = ws.cell(row=row, column=col)
        cell.fill = fill
        cell.font = FONTS['body']

def style_accent_row(ws, row, cols):
    for col in range(1, cols+1):
        cell = ws.cell(row=row, column=col)
        cell.fill = FILLS['green']
        cell.font = FONTS['body_dark']
```

## Logo palette guide
| Background | Logo to use | File |
|---|---|---|
| Plum / Jungle Green / Charcoal | Pink wordmark | `logo-pink-wordmark.png` |
| Off-White / Light | Charcoal wordmark | `logo-charcoal-wordmark.png` |
| Any dark (alternative) | White wordmark | `logo-white-wordmark.png` |
| Footer / editorial | Pink flexi (script) | `logo-pink-flexi.png` |
| Busy digital layouts | Pink supporting mark | `logo-pink-supporting.png` |

## Figma template nodes (file: 0bhyfVEy0vxACwjve7ESqu)
| Node | Template name | Best for |
|---|---|---|
| `90:717` | Product announcement (light) | Product sheets, pricing |
| `1:2102` | Instagram post 512 | Editorial document reference |
| `1:1680` | Key reference node | General brand reference |
