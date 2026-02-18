# plotting_function.py
from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List, Union
from matplotlib.colors import to_rgba
from matplotlib.figure import Figure

import re
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import textwrap

import hypothesen_CONST
import src.plotting.plotting_config as cfg
import string
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


def _get_ce_series(df_tidy: pd.DataFrame, q_ce: str) -> pd.Series:
    """Return CE as 0/1 indexed by respondent_id."""
    _require_cols(df_tidy, ["respondent_id", "question_text", "answer"], "CE")
    d = df_tidy[df_tidy["question_text"] == q_ce].copy()
    s = d.groupby("respondent_id")["answer"].first()
    ce = s.map(lambda x: hyp_const.JA_NEIN_MAPPING.get(str(x).strip(), np.nan)).astype("float")
    return ce


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

def finalize_like_standard(fig: plt.Figure, *, caption: str, reserve_right: float = 0.80, reserve_bottom: float = 0.18) -> None:
    """
    Make hypotheses plots match the standard plot layout (size + spacing + caption).
    """
    fig.set_size_inches(*cfg.FIGSIZE, forward=True)
    fig.subplots_adjust(bottom=reserve_bottom, right=reserve_right)
    add_caption(fig, caption)

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

# -----------------------------
# Plot types
# -----------------------------

def plot_single_percent_bar(
    df_tidy: pd.DataFrame,
    question_text: str,
    base_n: Optional[int] = None,
    order: Optional[List[str]] = None,
    horizontal_threshold: int = 4,
) -> plt.Figure:
    d = df_tidy[df_tidy["question_text"] == question_text].copy()

    counts = d["answer"].value_counts(dropna=False)
    if order:
        counts = counts.reindex(order, fill_value=0)

    vc = counts.reset_index()
    vc.columns = ["answer", "n"]

    if base_n is None:
        base_n = int(vc["n"].sum())

    vc["pct"] = (vc["n"] / base_n * 100) if base_n > 0 else 0.0

    labels = vc["answer"].astype(str).tolist()
    pcts = vc["pct"].values
    use_horizontal = len(labels) > horizontal_threshold

    fig = plt.figure(figsize=cfg.FIGSIZE)
    ax = fig.add_axes([cfg.AX_BOX_LEFT, cfg.AX_BOX_BOTTOM, cfg.AX_BOX_WIDTH, cfg.AX_BOX_HEIGHT])

    if use_horizontal:

        # wrap FIRST, then compute margin so labels never get cut
        wrapped = wrap_labels(labels)
        left = _left_margin_for_labels(wrapped, base=0.22, per_char=0.0040, cap=0.48)

        y = np.arange(len(labels))
        ax.barh(y, pcts, color=cfg.PALETTE[0])
        ax.set_yticks(y)
        ax.set_yticklabels(wrap_labels(labels, width=18))
        ax.set_xlabel("Anteil (%)")

        xmax = max(5, float(np.nanmax(pcts)) * 1.15)
        ax.set_xlim(0, xmax)
        ax.xaxis.set_major_formatter(mtick.PercentFormatter(xmax=100, decimals=0))

        # smaller fonts for many-category plots
        ax.tick_params(axis="y", labelsize=cfg.FONT_TICK)
        ax.tick_params(axis="x", labelsize=cfg.FONT_TICK)

        for i, v in enumerate(pcts):
            ax.text(min(v + 1.0, xmax), i, f"{v:.0f}%", va="center", fontsize=9)

        ax.grid(axis="x", alpha=0.25)
        ax.set_axisbelow(True)

        fig.subplots_adjust(left=left, right=0.98, top=0.95, bottom=0.26)
        return fig


    x = np.arange(len(labels))
    ax.bar(x, pcts, color=cfg.PALETTE[0])
    ax.set_xticks(x)
    ax.set_xticklabels(wrap_labels(labels, width=14), rotation=0, ha="center")
    ax.set_ylabel("Anteil (%)")

    ymax = max(5, float(np.nanmax(pcts)) * 1.20)
    ax.set_ylim(0, ymax)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=100, decimals=0))

    ax.tick_params(axis="x", labelsize=cfg.FONT_TICK)
    ax.tick_params(axis="y", labelsize=cfg.FONT_TICK)

    for i, v in enumerate(pcts):
        ax.text(i, min(v + 1.0, ymax), f"{v:.0f}%", ha="center", va="bottom", fontsize=9)

    ax.grid(axis="y", alpha=0.25)
    ax.set_axisbelow(True)

    return fig


def plot_checkbox_percent_bar(
    df_tidy: pd.DataFrame,
    question_text: str,
    base_n: Optional[int] = None,

    order: Optional[List[str]] = None,
    horizontal_threshold: int = 4,
) -> plt.Figure:
    """
    Checkbox: percent of respondents that selected each option.
    denominator = base_n (respondents who saw the question) if provided,
    else unique respondents in tidy for this question.
    """
    d = df_tidy[df_tidy["question_text"] == question_text].copy()

    counts = d["answer"].value_counts()

    if order:
        counts = counts.reindex(order, fill_value=0)

    vc = counts.reset_index()
    vc.columns = ["answer", "n"]

    if base_n is None:
        base_n = int(d["respondent_id"].nunique())

    vc["pct"] = (vc["n"] / base_n * 100) if base_n > 0 else 0.0

    labels = vc["answer"].astype(str).tolist()
    pcts = vc["pct"].values

    use_horizontal = len(labels) > horizontal_threshold

    fig = plt.figure(figsize=cfg.FIGSIZE)
    ax = fig.add_axes([cfg.AX_BOX_LEFT, cfg.AX_BOX_BOTTOM, cfg.AX_BOX_WIDTH, cfg.AX_BOX_HEIGHT])

    if use_horizontal:

        y = np.arange(len(labels))
        ax.barh(y, pcts, color=cfg.PALETTE[0])
        ax.set_yticks(y)
        ax.set_yticklabels(wrap_labels(labels, width=18))
        ax.set_xlabel("Anteil der Nennungen (%)")

        xmax = max(5, float(np.nanmax(pcts)) * 1.15)
        ax.set_xlim(0, xmax)
        ax.xaxis.set_major_formatter(mtick.PercentFormatter(xmax=100, decimals=0))

        # smaller fonts for many-category plots
        ax.tick_params(axis="y", labelsize=cfg.FONT_TICK)
        ax.tick_params(axis="x", labelsize=cfg.FONT_TICK)

        for i, v in enumerate(pcts):
            ax.text(min(v + 1.0, xmax), i, f"{v:.0f}%", va="center", fontsize=9)

        ax.grid(axis="x", alpha=0.25)
        ax.set_axisbelow(True)

    else:

        x = np.arange(len(labels))
        ax.bar(x, pcts, color=cfg.PALETTE[0])
        ax.set_xticks(x)
        ax.set_xticklabels(wrap_labels(labels, width=18), rotation=0, ha="center")
        ax.set_ylabel("Anteil der Nennungen (%)")

        ymax = max(5, float(np.nanmax(pcts)) * 1.20)
        ax.set_ylim(0, ymax)
        ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=100, decimals=0))

        ax.tick_params(axis="x", labelsize=cfg.FONT_TICK)
        ax.tick_params(axis="y", labelsize=cfg.FONT_TICK)

        for i, v in enumerate(pcts):
            ax.text(i, min(v + 1.0, ymax), f"{v:.0f}%", ha="center", va="bottom", fontsize=9)

        ax.grid(axis="y", alpha=0.25)
        ax.set_axisbelow(True)

    return fig

def plot_matrix_stacked_percent(
    df_tidy: pd.DataFrame,
    question_text: str,
    figsize=None,
    items_order=None,
    answer_order=None,
    label_min_pct: float = 6.0,   # omit inside-label if segment < this
    ) -> plt.Figure:

    """
    100% stacked horizontal bars for matrix questions:
      - rows = items
      - segments = answer categories (ordered)
      - values = percent within item

    Features:
      - % label inside segment when >= label_min_pct
      - y labels wrapped via wrap_labels()
      - legend fixed top-right inside axes
      - text color
      """

    d = df_tidy[df_tidy["question_text"] == question_text].copy()

    # empty guard
    if d.empty:
        fig = plt.figure(figsize=cfg.FIGSIZE)
        ax = fig.add_axes([cfg.AX_BOX_LEFT, cfg.AX_BOX_BOTTOM, cfg.AX_BOX_WIDTH, cfg.AX_BOX_HEIGHT])
        ax.axis("off")
        return fig

    # count per (item, answer)
    tab = d.groupby(["item", "answer"]).size().reset_index(name="n")

    # enforce item order (show missing rows as 0)
    if items_order:
        all_items = list(items_order)
    else:
        all_items = tab["item"].dropna().astype(str).unique().tolist()

    # enforce answer order (Ja/Nein/Keine Antwort) if given; else natural
    if answer_order:
        all_answers = list(answer_order)
    else:
        all_answers = tab["answer"].dropna().astype(str).unique().tolist()

    # build pivot table with zeros
    pivot_n = (
        tab.pivot(index="item", columns="answer", values="n")
        .reindex(index=all_items, columns=all_answers)
        .fillna(0.0)
    )

    # convert to percent per item
    row_sum = pivot_n.sum(axis=1).replace(0, np.nan)
    pivot_pct = (pivot_n.div(row_sum, axis=0) * 100).fillna(0.0)

    # figure + fixed uniform axes box
    fig = plt.figure(figsize=cfg.FIGSIZE)
    ax = fig.add_axes([cfg.AX_BOX_LEFT, cfg.AX_BOX_BOTTOM, cfg.AX_BOX_WIDTH, cfg.AX_BOX_HEIGHT])

    # plot stacked bars
    y = np.arange(len(pivot_pct.index))
    left = np.zeros(len(pivot_pct.index))

    for i, ans in enumerate(pivot_pct.columns):
        vals = pivot_pct[ans].values
        ax.barh(
            y,
            vals,
            left=left,
            color=cfg.PALETTE[i % len(cfg.PALETTE)],
            label=str(ans),
        )

        # add inside labels when big enough
        for j, v in enumerate(vals):
            if v >= label_min_pct:
                ax.text(
                    left[j] + v / 2,
                    j,
                    f"{v:.0f}%",
                    ha="center",
                    va="center",
                    fontsize=cfg.FONT_BAR_LABEL,   # keep uniform
                    color="white"
                )

        left += vals

    ax.tick_params(axis="x", labelsize=cfg.FONT_TICK)
    ax.tick_params(axis="y", labelsize=cfg.FONT_TICK)

    # y labels (wrapped)
    labels = pivot_pct.index.astype(str).tolist()
    ax.set_yticks(y)
    ax.set_yticklabels(wrap_labels(labels, width=18))

    # x axis percent
    ax.set_xlim(0, 100)
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(xmax=100, decimals=0))
    ax.set_xlabel("Anteil (%)")

    # grid + style
    ax.grid(axis="x", alpha=0.25)
    ax.set_axisbelow(True)


    # legend on the right
    categories = list(pivot_n.columns)
    colors = [cfg.PALETTE[i % len(cfg.PALETTE)] for i in range(len(categories))]
    _add_legend_on_the_right_side(fig, categories, colors, x=0.83, y_top=0.88, line_h=0.04, fontsize=10)

    return fig

def plot_donut_single(
    df_tidy: pd.DataFrame,
    question_text: str,
    base_n: Optional[int] = None,
    order: Optional[List[str]] = None,
    figsize: Tuple[float, float] = (8.0, 5.5),
) -> plt.Figure:

    d = df_tidy[df_tidy["question_text"] == question_text].copy()
    counts = d["answer"].value_counts(dropna=False)

    if order:
        counts = counts.reindex(order, fill_value=0)

    if base_n is None:
        base_n = int(counts.sum())

    pcts = (counts.values / base_n * 100) if base_n > 0 else np.zeros(len(counts))
    labels = [str(x) for x in counts.index.tolist()]

    # ✅ use passed figsize
    fig = plt.figure(figsize=figsize)

    # ✅ add_axes controls layout; subplots_adjust is not needed
    ax = fig.add_axes([cfg.AX_BOX_LEFT, cfg.AX_BOX_BOTTOM, cfg.AX_BOX_WIDTH, cfg.AX_BOX_HEIGHT])
    _donut_one(ax, labels=wrap_labels(labels, width=28), pcts=pcts)

    return fig

def plot_donut_matrix_split(
    df_tidy: pd.DataFrame,
    question_text: str,
    items_order: Optional[List[str]] = None,
    answer_order: Optional[List[str]] = None,
    base_n: Optional[int] = None,
    figsize=None,
    max_plots: Optional[int] = None,
    skip_empty: bool = True,
    title_fmt: str = "{item}",
    plot_note: Optional[str] = None,
):
    """
    Create one donut per matrix item by reusing plot_donut_single().

    Input df_tidy schema:
      respondent_id | question_text | item | answer

    For each item:
      - filter rows of (question_text,item)
      - make a 'single-like' tidy (item=None) with answer categories
      - call plot_donut_single on that subset

    Returns: list[(item, fig)]
    """

    d = df_tidy[df_tidy["question_text"] == question_text].copy()
    if d.empty:
        return []

    # decide item iteration order
    if items_order:
        items = list(items_order)
    else:
        items = d["item"].dropna().astype(str).unique().tolist()

    if max_plots is not None:
        items = items[:max_plots]

    figs = []

    for it in items:
        di = d[d["item"].astype(str) == str(it)].copy()

        if di.empty:
            if skip_empty:
                continue
            # create empty fig via plot_donut_single (will handle empty guard if you have one)
            di = pd.DataFrame(columns=["respondent_id", "question_text", "item", "answer"])

        # Build "single-like" view:
        # - keep answers
        # - set item=None so plot_donut_single treats it as single question
        single_like = di[["respondent_id", "answer"]].copy()
        single_like["question_text"] = question_text
        single_like["item"] = None

        # Enforce answer ordering (important: avoid NaN from reindex in plot)
        order = answer_order

        # Call your existing single donut
        fig = plot_donut_single(
            single_like,
            question_text,
            base_n=base_n,
            order=order,
            figsize=figsize,
        )

        # Put item title / note onto figure (optional)
        # If plot_donut_single sets a title already, you can append or overwrite
        if title_fmt:
            fig.suptitle(title_fmt.format(item=it), y=0.98, fontsize=12)

        if plot_note:
            fig.text(0.01, 0.01, plot_note, ha="left", va="bottom", fontsize=9, color="dimgray")
            try:
                fig.tight_layout(rect=(0, 0.03, 1, 0.95))
            except Exception:
                pass

        figs.append((it, fig))

    return figs


# ============================================================
# Plot for H1,H3
# ============================================================
def plot_diverging_yes_no(
    summary: pd.DataFrame,
    *,
    title: Optional[str] = None,
    ylabel: Optional[str] = None,
    sort_by_yes: bool = False,
    wrap_width: int = 26,
    show_n_in_labels: bool = False,
) -> plt.Figure:
    """
    Creates a diverging horizontal bar plot:
      left  = NO (negative)
      right = YES (positive)
    Ticks shown as 0..100% on both sides (abs formatter).
    Legend outside top-right like your "single question" plots.
    """
    s = summary.copy()

    if sort_by_yes:
        s = s.sort_values("yes_pct", ascending=False)
    # else keep original order

    labels_raw = s["label"].astype(str).tolist()
    labels = wrap_labels(labels_raw, width=wrap_width, max_lines=4)

    if show_n_in_labels:
        labels = [f"{lab} (n={n})" for lab, n in zip(labels, s["base_n"].tolist())]

    yes = s["yes_pct"].to_numpy(float)
    no  = s["no_pct"].to_numpy(float)

    y = np.arange(len(labels))

    fig = plt.figure(figsize=cfg.FIGSIZE)
    ax = fig.add_axes([cfg.AX_BOX_LEFT, cfg.AX_BOX_BOTTOM, cfg.AX_BOX_WIDTH, cfg.AX_BOX_HEIGHT])

    # bars
    ax.barh(y, -no, color=cfg.PALETTE[1], label="noch nicht umgesetzt")
    ax.barh(y,  yes, color=cfg.PALETTE[0], label="bereits umgesetzt")

    # middle line
    ax.axvline(0, color=cfg.PALETTE[0], lw=1.2, alpha=0.8)

    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()

    # axis label + ticks like 0..100% both sides
    ax.set_xlabel("Anteil (%)")
    if ylabel:
        ax.set_ylabel(ylabel)

    ax.set_xlim(-100, 100)
    ax.set_xticks(np.arange(-100, 101, 25))
    ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: f"{abs(int(v))}%"))

    # fonts (closer to your other plots)
    ax.tick_params(axis="x", labelsize=cfg.FONT_TICK)
    ax.tick_params(axis="y", labelsize=cfg.FONT_TICK)

    # text on bars (pct + (n))
    for i, (yp, npct, yn, nn) in enumerate(zip(yes, no, s["yes_n"], s["no_n"])):
        if npct > 0:
            ax.text(-npct/2, i, f"{npct:.0f}%\n({int(nn)})", va="center", ha="center", fontsize=cfg.FONT_TICK)
        if yp > 0:
            ax.text( yp/2, i, f"{yp:.0f}%\n({int(yn)})", va="center", ha="center", fontsize=cfg.FONT_TICK)

    # grid
    ax.grid(axis="x", alpha=0.18)
    ax.set_axisbelow(True)

    # title (optional)
    if title:
        ax.set_title(title, fontsize=cfg.FONT_TITLE)

    # legend outside (top-right) like your stacked bar example
    ax.legend(
        loc="upper left",
        bbox_to_anchor=(1.02, 1.0),
        frameon=False,
        fontsize=cfg.FONT_TICK,
    )

    # give room for legend and wrapped ylabels
    fig.subplots_adjust(left=0.25, right=0.80, top=0.92, bottom=0.18)

    return fig

# ============================================================
# Plot for H2
# ============================================================
def plot_diverging_yes_no_h2(
    summary: pd.DataFrame,
    *,
    title: Optional[str] = None,
    wrap_width: int = 24,
) -> plt.Figure:
    s = _add_material_cost_group(summary)

    # sort: high first, then low, then other; inside group by yes_pct desc
    order_map = {"Hohe Materialkosten": 0, "Geringe Materialkosten": 1, "Sonstige/unklar": 2}
    s["_grp"] = s["cost_group"].map(order_map).fillna(9)
    s = s.sort_values(["_grp", "yes_pct"], ascending=[True, False]).drop(columns=["_grp"])

    # feed into base plotter by renaming label
    s2 = s.rename(columns={"label": "label_orig"})
    s2["label"] = s2["label_marked"]

    fig = plot_diverging_yes_no(
        s2,
        title=title,
        ylabel="Branche (▲ hoch / ▼ niedrig / • unklar)",
        sort_by_yes=False,
        wrap_width=wrap_width,
        show_n_in_labels=False,
    )
    return fig

# ============================================================
# Plot H4
# ============================================================
def plot_radar_counts_topk(
    counts: "pd.Series",
    title: str = "",
    k: int = 5,
    wrap_width: int = 26,
    r_step: int = 5,
):
    # --- 1) Top-k auswählen (und NaNs absichern) ---
    s = counts.dropna().sort_values(ascending=False)
    if k is not None:
        s = s.head(k)

    labels = s.index.astype(str).tolist()
    values = s.values.astype(float).tolist()

    # OPTIONAL: wrap_labels aus deinem plotting_function.py nutzen
    labels_wrapped = wrap_labels(labels, width=wrap_width, max_lines=4)

    n = len(labels_wrapped)
    if n == 0:
        raise ValueError("Radar: keine Daten (n=0). Prüfe strong_set / question_text.")

    # --- 2) Angles passend zu Top-k bauen ---
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()

    # Close polygon
    angles_closed = angles + angles[:1]
    values_closed = values + values[:1]

    # --- 3) Plot ---
    fig = plt.figure(figsize=cfg.FIGSIZE)  # gleiche FIGSIZE wie deine anderen Plots
    ax = fig.add_subplot(111, polar=True)

    ax.plot(angles_closed, values_closed, linewidth=2)
    ax.fill(angles_closed, values_closed, alpha=0.12)

    # --- 4) Ticks/Labels: EXACT MATCH ---
    ax.set_xticks(angles)
    ax.set_xticklabels(labels_wrapped)

    # --- 5) Radius/Skalierung ---
    vmax = max(values) if values else 0
    rmax = int(np.ceil(vmax / r_step) * r_step) if vmax > 0 else r_step
    ax.set_ylim(0, rmax)
    ax.set_yticks(list(range(0, rmax + 1, r_step)))
    ax.set_yticklabels([str(v) for v in range(0, rmax + 1, r_step)])

    # --- 6) Values an jede Achse schreiben (Betreuer will Counts!) ---
    for a, v in zip(angles, values):
        ax.text(a, v + 0.6, f"{int(v)}", ha="center", va="center", fontsize=cfg.FONT_TICK)

    # Title optional (du wolltest bei H4: kein Titel, nur Caption unten)
    if title:
        ax.set_title(title, fontsize=cfg.FONT_TITLE, pad=12)

    # Kreis kleiner wirken lassen (mehr Weißraum)
    fig.subplots_adjust(left=0.16, right=0.84, top=0.88, bottom=0.20)

    return fig

# -----------------------------
# Router (select plot function by q["type"])
# -----------------------------
def plot_question(
    q: Dict[str, Any],
    df_tidy: pd.DataFrame,
    base_map: Dict[str, int],
) -> Union[plt.Figure, List[Tuple[str, plt.Figure]]]:

    qtext = q["question_text"]
    qtype = q["type"]
    plot_type = (q.get("plot_type") or "").lower()
    base_n = base_map.get(qtext)

    # spec-driven ordering
    options_order = q.get("options_order") or None
    answer_order = q.get("answer_order") or None
    items_order = q.get("items_order") or None

    if qtype in {"single", "likert"}:
        if plot_type == "donut":
            base_n = base_map.get(qtext)
            return plot_donut_single(
                df_tidy, qtext,
                base_n=base_n,
                order=options_order,
                figsize=cfg.FIGSIZE_DONUT,
            )
        else:
            return plot_single_percent_bar(
                df_tidy, qtext,
                base_n=base_n,
                order=options_order,
                horizontal_threshold=cfg.HORIZONTAL_THRESHOLD,
            )

    if qtype == "checkbox":
        return plot_checkbox_percent_bar(df_tidy, qtext, base_n=base_n, order=options_order)

    if qtype in {"matrix"}:
        if plot_type == "donut":
            return plot_donut_matrix_split(
                df_tidy, qtext,
                items_order=items_order,
                answer_order=options_order or answer_order,
                base_n=base_n,
                figsize=cfg.FIGSIZE_DONUT,
                plot_note=q.get("plot_note"),  # optional aus spec
                title_fmt="{}".format("{item}"),
            )
        else:
            return plot_matrix_stacked_percent(
                df_tidy=df_tidy,
                question_text=qtext,
                items_order=items_order,
                answer_order=answer_order,
            )

    if qtype == "matrix_multi" and plot_type == "donut":
        return plot_donut_matrix_split(
                df_tidy, qtext,
                items_order=items_order,
                answer_order=options_order or answer_order,  # usually options_order for matrix answers
                figsize=cfg.FIGSIZE_DONUT,
            )

    # fallback
    if len(q.get("cols", [])) == 1:
        return plot_single_percent_bar(df_tidy, qtext, base_n=base_n, order=options_order)
    return plot_matrix_stacked_percent(df_tidy, qtext, items_order=items_order, answer_order=answer_order)

def plot_question_and_save(
    q: Dict[str, Any],
    df_tidy: pd.DataFrame,
    base_map: Dict[str, int],
    out_dir: Path,
    prefix_index: Optional[int] = None,
) -> List[Path]:

    """
    Create plot(s) for one question, add caption(s), save, return output path(s).

    Special rule:
    - type == "text" -> skip (no plot saved)
    """

    qtext = (q.get("question_text") or "").strip()
    qtype = str(q.get("type", "")).strip().lower()

    # --- SKIP TEXT QUESTIONS ---
    if qtype == "text":
        if prefix_index is not None:
            print(f"SKIP (text): Abbildung {prefix_index} – {qtext}")
        else:
            print(f"SKIP (text): {qtext}")
        return []

    result = plot_question(q, df_tidy, base_map)

    out_paths: List[Path] = []
    out_dir.mkdir(parents=True, exist_ok=True)

    caption_text = (q.get("caption") or q["question_text"]).strip()

    # ---- CASE A: single figure ----
    if isinstance(result, Figure):
        fig = result

        cap = f"Abbildung {prefix_index}: {caption_text}" if prefix_index is not None else f"Abbildung: {caption_text}"
        add_caption(fig, cap)

        safe = make_filename_safe(q["question_text"])
        filename = f"{prefix_index:02d}_{safe}.{cfg.SAVE_FORMAT}" if prefix_index is not None else f"{safe}.{cfg.SAVE_FORMAT}"

        out_path = out_dir / filename
        _save_fig(fig, out_path)
        out_paths.append(out_path)
        return out_paths

    # ---- CASE B: list of (item, fig) ----
    if isinstance(result, list):
        if len(result) == 0:
            print(f"[WARN] Donut split returned 0 figs for: {q['question_text']}")
            return out_paths

        for k, pair in enumerate(result):
            # safety: allow tuple structure only
            if not (isinstance(pair, tuple) and len(pair) == 2):
                print(f"[WARN] Unexpected list element in result for {q['question_text']}: {pair}")
                continue

            item_label, fig = pair
            if not isinstance(fig, Figure):
                print(f"[WARN] Expected Figure, got {type(fig)} for item {item_label}")
                continue

            suffix = string.ascii_lowercase[k]  # a, b, c...

            if prefix_index is not None:
                cap = f"Abbildung {prefix_index}{suffix}: {caption_text} – {item_label}"
                filename_prefix = f"{prefix_index:02d}{suffix}_"
            else:
                cap = f"Abbildung: {caption_text} – {item_label}"
                filename_prefix = ""

            add_caption(fig, cap)

            safe_q = make_filename_safe(q["question_text"])
            safe_item = make_filename_safe(item_label)
            filename = f"{filename_prefix}{safe_q}__{safe_item}.{cfg.SAVE_FORMAT}"
            out_path = out_dir / filename

            _save_fig(fig, out_path)
            out_paths.append(out_path)

        return out_paths

    return out_paths

def plot_hypotheses_and_save(
    df_tidy: pd.DataFrame,
    out_dir: Path,
    *,
    q_ce: str,
    q_h1_group: str,
    q_h2_industry: str,
    q_h3_group: str,
    q_h4_block_1: str,
    q_h4_block_2: str,
    q_h4_block_3: str,
    h4_topk: int = 5,
    strong_hemmnis: set[str] | None = None,
    strong_zustimmung: set[str] | None = None,
    start_abbildung_index: int | None = None,
) -> Tuple[List[Path], List[str]]:


    out_dir = Path(out_dir) / "hypothesen"
    out_dir.mkdir(parents=True, exist_ok=True)

    saved: List[Path] = []
    captions: List[str] = []

    abb = start_abbildung_index

    def _next_caption(text: str) -> str:
        nonlocal abb
        if abb is None:
            return f"Abbildung: {text}"
        abb += 1
        return f"Abbildung {abb}: {text}"


    # --- H1 ---
    h1 = _summarize_diverging(df_tidy, q_h1_group, q_ce)
    fig = plot_diverging_yes_no(
        h1,
        title="H1: Unternehmensgröße vs. CE umgesetzt",
        ylabel="Anzahl der Beschäftigten",
        sort_by_yes=False,
        wrap_width=22,
        show_n_in_labels=False,
    )
    cap = _next_caption("Hypothese 1 – Größere Unternehmen setzen häufiger bereits Kreislaufwirtschaft um als kleine Unternehmen.")
    add_caption(fig, cap)
    p = out_dir / "H1_diverging.png"
    fig.savefig(p, dpi=300)
    plt.close(fig)
    saved.append(p); captions.append(cap)

    # --- H2 ---
    h2 = _summarize_diverging_multiselect(df_tidy, q_h2_industry, q_ce)
    fig = plot_diverging_yes_no_h2(
        h2,
        title="H2: Branche vs. CE umgesetzt (Mehrfachauswahl)",
        wrap_width=22,
    )
    cap = _next_caption("Hypothese 2 – Branchen mit hohen Materialkosten sind eher bereit, Kreislaufwirtschaft umzusetzen als Branchen mit geringeren Materialkosten.")
    add_caption(fig, cap)
    p = out_dir / "H2_diverging.png"
    fig.savefig(p, dpi=300)
    plt.close(fig)
    saved.append(p); captions.append(cap)

    # --- H3 ---
    h3 = _summarize_diverging(df_tidy, q_h3_group, q_ce)
    fig = plot_diverging_yes_no(
        h3,
        title="H3: Seriengröße vs. CE umgesetzt",
        ylabel="Monatliche Stückzahl",
        sort_by_yes=False,
        wrap_width=24,
        show_n_in_labels=False,
    )
    cap = _next_caption("Hypothese 3 – Kleinserien oder Einzelanfertigungen eignen sich für die Wiederaufbereitung eher als Großserienprodukte.")
    add_caption(fig, cap)
    p = out_dir / "H3_diverging.png"
    fig.savefig(p, dpi=300)
    plt.close(fig)
    saved.append(p); captions.append(cap)

    # --- H4  ---
    h4_blocks = [
        ("H4_1", q_h4_block_1, strong_hemmnis, "Hypothese 4 – Top-5 als stark bewertete Hemmnisse (Block 1)."),
        ("H4_2", q_h4_block_2, strong_zustimmung, "Hypothese 4 – Top-5 als stark bewertete Zustimmung (Block 2)."),
        ("H4_3", q_h4_block_3, strong_hemmnis, "Hypothese 4 – Top-5 als stark bewertete Hemmnisse (Block 3)."),
    ]

    for key, q_block, strong_set, cap in h4_blocks:
        counts = _strong_counts(df_tidy, q_block, strong_set=strong_set)

        fig = plot_radar_counts_topk(
            counts,
            title="",  # kein Titel, nur Abbildung als Caption
            k=h4_topk,
            wrap_width=20,
            r_step=5,
        )

        p = out_dir / f"{key}_radar.png"

        fig.savefig(p, dpi=200, bbox_inches="tight")
        plt.close(fig)
        saved.append(p)

        captions.append(_next_caption(abb) if abb is None else f"Abbildung {abb}: {abb}")

    return saved, captions