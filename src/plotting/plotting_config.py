# plotting_config.py
"""
Central styling + brand colors for uniform plotting.

Call apply_style() once in main.py BEFORE you create any plotting_function_jg_analyse.
"""

from __future__ import annotations

from pathlib import Path
import matplotlib as mpl

#--------------------
# Input config
#--------------------

EXCEL_PATH = Path("new_survey_result.xlsx")
FIRST_QUESTION_TEXT = "Welcher Art von Organisation gehören Sie an?"
SPEC_PATH = Path("question_spec.json")

# -----------------------------
# Output config
# -----------------------------
BASE_DIR = Path("/Users/buayaguruun21/PycharmProjects/Visualisierung_Umfrage/plotting_output") #CHANGE THIS

OUTPUT_DIR = BASE_DIR / "plotting_output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PLOTS_Q_DIR = OUTPUT_DIR / "plots_all_question"
PLOTS_H_DIR = OUTPUT_DIR / "hypotheses"
PLOTS_JG_DIR = OUTPUT_DIR / "jg_analyse"

PLOTS_Q_DIR.mkdir(parents=True, exist_ok=True)
PLOTS_H_DIR.mkdir(parents=True, exist_ok=True)
PLOTS_JG_DIR.mkdir(parents=True, exist_ok=True)

SAVE_FORMAT = "png"
SAVE_DPI = 300


SAVE_BBOX = None
SAVE_PAD_INCHES = 0.0

# -----------------------------
# Figure sizes (consistent)
# -----------------------------

FIGSIZE = (13.0, 9.0)

# fixed axes box (relative to figure)
AX_BOX_WIDTH = 0.50
AX_BOX_LEFT  = 0.35 # to keep long y index
AX_BOX_RIGHT = AX_BOX_LEFT + AX_BOX_WIDTH

AX_BOX_BOTTOM = 0.26   # room for caption
AX_BOX_TOP = 0.92
AX_BOX_HEIGHT = AX_BOX_TOP - AX_BOX_BOTTOM

# For donut plot
FIGSIZE_DONUT = FIGSIZE
FONT_TITLE = 11
AX_BOX_LEFT_DONUT =  (1- AX_BOX_WIDTH) /2

# For network diagmram
FIGSIZE_NETZDIAGRAMM = (8,8)

# -----------------------------
# Brand colors (from your slide)
# -----------------------------
# Hauptfarben (top-left swatches)
ACATECH_GREEN      = "#8FC73E"  # (143,199,62)
ACATECH_BLUE       = "#003B6A"  # (0,59,106)
ACATECH_GREEN_70   = "#B0D577"  # (176,213,119)
ACATECH_BLUE_50    = "#6283AA"  # (98,131,170)

# Weitere Farben 100% (right palette, 100% blocks)
ACATECH_ORANGE     = "#DC912F"  # (220,145,47)
ACATECH_LIGHTBLUE  = "#93BBDC"  # (147,187,220)
ACATECH_GREEN_ALT  = "#8EB923"  # (142,185,35)
ACATECH_YELLOW     = "#F9C803"  # (249,200,3)

# A good categorical palette for plotting_function_jg_analyse (cycle)
# (Use blue/green as primary; others as accents)
PALETTE = [
    ACATECH_BLUE,
    ACATECH_GREEN,
    ACATECH_ORANGE,
    ACATECH_LIGHTBLUE,
    ACATECH_YELLOW,
    ACATECH_BLUE_50,
    ACATECH_GREEN_70,
    ACATECH_GREEN_ALT,
]

# Optional: tints (for gradients / secondary)
# (from the slide’s 80/60/40/20/10% blocks, approximate)
TINTS_ORANGE = ["#DC912F", "#E6B173", "#EBC59A", "#EED3B6", "#EFDCC9", "#F0E7DB"]
TINTS_BLUE   = ["#93BBDC", "#B2CCE5", "#C5D7EA", "#D2E1EE", "#DCE6F1", "#E5ECF3"]
TINTS_GREEN  = ["#8EB923", "#B0C96C", "#C5D691", "#D3E0B6", "#DCE7CA", "#E5EEDF"]
TINTS_YELLOW = ["#F9C803", "#FAD862", "#FAE295", "#FBE9B6", "#FBEECC", "#FCF4DF"]

# -----------------------------
# Typography & styling
# -----------------------------

# --- fixed typography (uniform for all plotting_function_jg_analyse) ---
FONT_BASE = 12
FONT_AXIS_LABEL = 12
FONT_TICK = 12
FONT_BAR_LABEL = 12
FONT_CAPTION = 12


#---y index wrap width
TICKS_WRAP_WIDTH = 50
MAX_LINE_WRAP = 3

# caption wrapping

CAPTION_WRAP_WIDTH = 65  # characters per line
CAPTION_Y = 0.04  # move caption slightly up
CAPTION_LINE_SPACING = 1.1


#Font Caption

HORIZONTAL_THRESHOLD = 4  # >4 categories => horizontal bars
LABEL_PCT_DECIMALS = 0  # labels on bars
AXIS_PCT_DECIMALS = 0  # axis ticks
CAPTION_FONTSIZE = 11
FONT_LEGEND_SIZE = 8


#Horinzontale Bar config

HBAR_GROUP_GAP = 1      # space between dimensions (increase for more gap)
HBAR_INNER_GAP = 0.55    # space between GU & KMU (small)
HBAR_BAR_HEIGHT = 0.35    # thinner bars


STYLE = {
    # Fonts
    "font.family": "DejaVu Sans",
    "font.size": 12,

    # axis titles (xlabel / ylabel)
    "axes.labelsize": 12,
    "axes.titlesize": 12,

    # tick labels (DEINE Kategorien!)
    "xtick.labelsize": 12,
    "ytick.labelsize": 12,

    # weights
    "axes.labelweight": "regular",
    "axes.titleweight": "regular",

    # Axes / grid
    "axes.edgecolor": "#333333",
    "axes.linewidth": 0.9,
    "grid.color": "#D0D0D0",
    "grid.linewidth": 0.8,

    # Figure
    "figure.facecolor": "white",
    "axes.facecolor": "white",

    # Legend
    "legend.fontsize": 12,
    "legend.frameon": False,

    # Saving
    "savefig.dpi": SAVE_DPI,
}

def apply_style() -> None:
    """Call once at program start (main.py)."""
    mpl.rcParams.update(STYLE)




