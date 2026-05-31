"""
Luffi UI Theme — Pure black & white professional palette.
Monochrome, minimal, clean. Used across all popups.
"""

# Core palette (grayscale only)
BLACK = "#000000"
BG = "#0a0a0a"          # main background
PANEL = "#141414"       # header/footer panels
PANEL_HOVER = "#1e1e1e"
CARD = "#161616"        # list rows
BORDER = "#2a2a2a"      # subtle borders
DIVIDER = "#222222"

# Text
WHITE = "#ffffff"
TEXT = "#e8e8e8"        # primary text
TEXT_DIM = "#9a9a9a"    # secondary text
TEXT_MUTED = "#5a5a5a"  # hints, labels
ACCENT = "#ffffff"      # accent = white (monochrome)

# State (grayscale instead of color)
GOOD = "#ffffff"        # full white
MID = "#bbbbbb"         # light gray
LOW = "#777777"         # dim gray
DANGER = "#ffffff"      # white (use intensity, not red)

# Fonts
FONT_MAIN = "Segoe UI"
FONT_MONO = "Consolas"

# Opacity
ALPHA = 0.96


def gray_for_pct(pct: float) -> str:
    """Grayscale shade for a usage percentage (brighter = higher)."""
    if pct < 40:
        return "#5a5a5a"
    elif pct < 70:
        return "#9a9a9a"
    elif pct < 88:
        return "#cccccc"
    return "#ffffff"


# Professional monochrome glyph icons (Segoe UI Symbol / Unicode)
class Icon:
    LOGO = "◆"          # diamond — brand mark
    CLOSE = "✕"
    SEARCH = "⌕"
    TERMINAL = "▸"
    CPU = "▦"
    RAM = "▤"
    DISK = "▥"
    BATTERY = "▮"
    CLOCK = "◷"
    NET = "↓"
    APP = "▪"
    TASKBAR = "▭"
    DESKTOP = "▢"
    ASK = "›"
    AGENT = "◈"
    DONE = "✓"
    ERROR = "✕"
    THINKING = "◌"
    BULLET = "▌"
