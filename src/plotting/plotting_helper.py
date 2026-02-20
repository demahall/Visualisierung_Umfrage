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
import hypothesen_CONST as hyp_const


# -----------------------------
# Helpers
# -----------------------------
def make_filename_safe(text: str, max_len: int = 60) -> str:
    safe = re.sub(r"[^\w\s\-]+", "_", text, flags=re.UNICODE).strip()
    safe = re.sub(r"\s+", " ", safe)
    safe = safe.replace(" ", "_")
    return safe[:max_len]
def wrap_labels(labels, width=80, max_lines=5):
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

def add_caption(fig: plt.Figure, caption: str) -> None:
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


# -----------------------------
# Helpers Hypotheses
# -----------------------------
def _require_cols(df: pd.DataFrame, cols: List[str], ctx: str) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"[{ctx}] df_tidy missing columns: {missing}. Found: {df.columns.tolist()}")


def _summarize_diverging(df_tidy: pd.DataFrame, q_group: str, q_ce: str) -> pd.DataFrame:
    """
    For single-select grouping question:
    returns df with columns: group, yes_n, no_n, base_n, yes_pct, no_pct
    """
    d = df_tidy.copy()
    g = d[d["question_text"] == q_group][["respondent_id", "answer"]].rename(columns={"answer": "group"})
    ce = d[d["question_text"] == q_ce][["respondent_id", "answer"]].rename(columns={"answer": "ce"})

    m = g.merge(ce, on="respondent_id", how="inner")
    m["ce"] = m["ce"].astype(str)

    # normalize CE labels
    m["is_yes"] = m["ce"].str.strip().str.lower().eq("ja")
    m["is_no"]  = m["ce"].str.strip().str.lower().eq("nein")

    agg = (
        m.groupby("group", dropna=False)
        .agg(
            yes_n=("is_yes", "sum"),
            no_n=("is_no", "sum"),
            base_n=("ce", "count"),
        )
        .reset_index()
        .rename(columns={"group": "label"})
    )

    agg["yes_pct"] = np.where(agg["base_n"] > 0, agg["yes_n"] / agg["base_n"] * 100, 0.0)
    agg["no_pct"]  = np.where(agg["base_n"] > 0, agg["no_n"]  / agg["base_n"] * 100, 0.0)
    return agg


def _summarize_diverging_multiselect(df_tidy: pd.DataFrame, q_multi: str, q_ce: str) -> pd.DataFrame:
    """
    For multi-select grouping question:
    each respondent can appear multiple times (one per selected industry).
    returns df with columns: label, yes_n, no_n, base_n, yes_pct, no_pct
    """
    d = df_tidy.copy()
    g = d[d["question_text"] == q_multi][["respondent_id", "answer"]].rename(columns={"answer": "label"})
    ce = d[d["question_text"] == q_ce][["respondent_id", "answer"]].rename(columns={"answer": "ce"})

    m = g.merge(ce, on="respondent_id", how="inner")
    m["ce"] = m["ce"].astype(str)

    m["is_yes"] = m["ce"].str.strip().str.lower().eq("ja")
    m["is_no"]  = m["ce"].str.strip().str.lower().eq("nein")

    agg = (
        m.groupby("label", dropna=False)
        .agg(
            yes_n=("is_yes", "sum"),
            no_n=("is_no", "sum"),
            base_n=("ce", "count"),
        )
        .reset_index()
    )
    agg["yes_pct"] = np.where(agg["base_n"] > 0, agg["yes_n"] / agg["base_n"] * 100, 0.0)
    agg["no_pct"]  = np.where(agg["base_n"] > 0, agg["no_n"]  / agg["base_n"] * 100, 0.0)
    return agg


def _likert_means_pct(df_tidy: pd.DataFrame, q_block: str, mapping: Dict[str, float]) -> pd.DataFrame:
    """
    mapping: answer -> numeric score in [0..1] or [0..100] style.
    We convert to 0..100%.
    """
    d = df_tidy[df_tidy["question_text"] == q_block].copy()
    d = d[d["answer"].notna()]

    # map answers
    d["score"] = d["answer"].map(mapping)
    d = d[d["score"].notna()]

    # if mapping is 0..1 -> scale to 0..100
    mx = float(np.nanmax(d["score"])) if len(d) else 1.0
    if mx <= 1.0:
        d["pct"] = d["score"] * 100.0
    else:
        d["pct"] = d["score"]

    means = d.groupby("item", dropna=False)["pct"].mean().reset_index()
    means.columns = ["dimension", "pct_mean"]
    return means.sort_values("pct_mean", ascending=False)

def _strong_counts(
    df_tidy: pd.DataFrame,
    block_question_text: str,
    strong_set: set[str],
) -> pd.Series:
    d = df_tidy[df_tidy["question_text"] == block_question_text].copy()

    d = d[d["answer"].notna()]
    d = d[d["answer"].isin(strong_set)]

    # count per item (dimension)
    return d.groupby("item")["respondent_id"].nunique().sort_values(ascending=False)



def _add_material_cost_group(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    def grp(x: str) -> str:
        if x in hyp_const.HIGH_COST_INDUSTRIES:
            return "Hohe Materialkosten"
        if x in hyp_const.LOW_COST_INDUSTRIES:
            return "Geringe Materialkosten"
        return "Sonstige/unklar"
    df["cost_group"] = df["label"].astype(str).map(grp)

    def prefix(row) -> str:
        if row["cost_group"] == "Hohe Materialkosten":
            return "▲ "
        if row["cost_group"] == "Geringe Materialkosten":
            return "▼ "
        return "• "
    df["label_marked"] = df.apply(lambda r: prefix(r) + str(r["label"]), axis=1)
    return df