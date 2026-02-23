from __future__ import annotations

from pathlib import Path
from typing import Dict, List
from matplotlib.colors import to_rgba


import re

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import textwrap


import src.plotting.plotting_config as cfg
import QUESTION_LIST as hyp_const


# -----------------------------
# Helpers
# -----------------------------
def _make_filename_safe(text: str, max_len: int = 60) -> str:
    safe = re.sub(r"[^\w\s\-]+", "_", text, flags=re.UNICODE).strip()
    safe = re.sub(r"\s+", " ", safe)
    safe = safe.replace(" ", "_")
    return safe[:max_len]

def _wrap_labels(labels, width=50, max_lines=5):
    """
    Wrap long labels into multiple lines.
    width: max characters per line
    max_lines: maximum lines before truncating with "…"
    """
    wrapped = []
    for l in labels:
        lines = textwrap.wrap(str(l), width=width)
        if len(lines) > max_lines:
            lines = lines[:max_lines]
            lines[-1] = lines[-1] + "…"
        wrapped.append("\n".join(lines))
    return wrapped
def _add_legend_on_the_right_side(fig, categories, colors, x=0.90, y_top=0.88, line_h=0.03, fontsize=10):
    """
    Draws a legend-like vertical list outside the plot on the right side.
    """
    for i, (cat, col) in enumerate(zip(categories, colors)):
        y = y_top - i * line_h

        # colored square + text
        fig.text(x, y, "■", color=col, fontsize=fontsize+2, va="center", ha="left")
        fig.text(x + 0.02, y, str(cat), fontsize=fontsize, va="center", ha="left")

def _add_caption(fig: plt.Figure, caption: str) -> None:
    """
    Adds a centered bottom caption. Automatically wraps into multiple lines
    so the text never gets cut.
    """
    wrapped = "\n".join(textwrap.wrap(caption, width=cfg.CAPTION_WRAP_WIDTH))
    fig.text(
        0.5,
        cfg.CAPTION_Y,
        wrapped,
        ha="center",
        va="bottom",
        fontsize=cfg.FONT_CAPTION,
        linespacing=cfg.CAPTION_LINE_SPACING,
    )

def _left_margin_for_labels(labels: list[str], base: float = 0.18, per_char: float = 0.003, cap: float = 0.42) -> float:
    """
    Estimate needed left margin based on longest label length.
    Returns a fraction for fig.subplots_adjust(left=...).
    """
    max_len = max((len(str(x)) for x in labels), default=10)
    return min(cap, max(base, base + per_char * max_len))


def _save_fig(fig: plt.Figure, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    kwargs = {"dpi": cfg.SAVE_DPI}
    if cfg.SAVE_BBOX is not None:
        kwargs["bbox_inches"] = cfg.SAVE_BBOX
        kwargs["pad_inches"] = cfg.SAVE_PAD_INCHES

    fig.savefig(out_path, **kwargs)
    plt.close(fig)


#-----------------
#HELPER DONUT CHART
#-----------------

def _donut_one(ax, labels: List[str], pcts: np.ndarray) -> None:
    """
    Draw a donut into an existing axis.
    - labels: category names
    - pcts: percentages (sum ~ 100)
    """
    colors = [cfg.PALETTE[i % len(cfg.PALETTE)] for i in range(len(labels))]

    # donut
    wedges, _ = ax.pie(
        pcts,
        startangle=90,
        counterclock=False,
        colors=colors,
        wedgeprops=dict(width=0.35, edgecolor="white"),
    )
    ax.set_aspect("equal")

    # labels outside with small connector line
    # (keeps the donut clean)
    for w, lab, pct in zip(wedges, labels, pcts):
        if pct <= 0:
            continue

        ang = (w.theta2 + w.theta1) / 2.0
        x = np.cos(np.deg2rad(ang))
        y = np.sin(np.deg2rad(ang))

        # text position outside
        r_text = 1.25
        ha = "left" if x >= 0 else "right"

        ax.plot([0.88 * x, 1.10 * x], [0.88 * y, 1.10 * y], lw=1.0, color=to_rgba("black", 0.35))
        ax.text(
            r_text * x,
            r_text * y,
            f"{pct:.0f}%\n{lab}",
            ha=ha,
            va="center",
            fontsize=cfg.FONT_TICK,   # define in config
        )


