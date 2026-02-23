# plotting_function.py
from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List, Union
from matplotlib.figure import Figure
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import src.plotting.plotting_config as cfg
import src.plotting.plotting_helper as helper
import string


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

    # wrap FIRST, then compute margin so labels never get cut
    wrapped = helper._wrap_labels(labels)

    if use_horizontal:

        y = np.arange(len(labels))
        ax.barh(y, pcts, color=cfg.PALETTE[0])
        ax.set_yticks(y)
        ax.set_yticklabels(wrapped)
        ax.tick_params(labelsize=cfg.FONT_TICK)

        ax.set_xlabel("Anteil der Teilnehmer in %")

        xmax = max(5, float(np.nanmax(pcts)) * 1.15)
        ax.set_xlim(0, xmax)
        ax.xaxis.set_major_formatter(mtick.PercentFormatter(xmax=100, decimals=0))


        for i, v in enumerate(pcts):
            ax.text(min(v + 1.0, xmax), i, f"{v:.0f}%", va="center", fontsize=9)

        ax.grid(axis="x", alpha=0.25)
        ax.set_axisbelow(True)

        return fig


    x = np.arange(len(labels))
    ax.bar(x, pcts, color=cfg.PALETTE[0])
    ax.set_xticks(x)
    ax.set_xticklabels(wrapped)
    ax.set_ylabel("Anteil der Teilnehmer in %")


    ymax = max(5, float(np.nanmax(pcts)) * 1.20)
    ax.set_ylim(0, ymax)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=100, decimals=0))

    ax.tick_params(labelsize=cfg.FONT_TICK)

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

    wrapped = helper._wrap_labels(labels)

    if use_horizontal:

        y = np.arange(len(labels))
        ax.barh(y, pcts, color=cfg.PALETTE[0])
        ax.set_yticks(y)
        ax.set_yticklabels(wrapped)
        ax.set_xlabel("Anteil der Nennungen (%)")

        xmax = max(5, float(np.nanmax(pcts)) * 1.15)
        ax.set_xlim(0, xmax)
        ax.xaxis.set_major_formatter(mtick.PercentFormatter(xmax=100, decimals=0))

        ax.tick_params(labelsize=cfg.FONT_TICK)

        for i, v in enumerate(pcts):
            ax.text(min(v + 1.0, xmax), i, f"{v:.0f}%", va="center", fontsize=9)

        ax.grid(axis="x", alpha=0.25)
        ax.set_axisbelow(True)

    else:

        x = np.arange(len(labels))
        ax.bar(x, pcts, color=cfg.PALETTE[0])
        ax.set_xticks(x)
        ax.set_xticklabels(wrapped)
        ax.set_ylabel("Anteil der Nennungen in %")

        ymax = max(5, float(np.nanmax(pcts)) * 1.20)
        ax.set_ylim(0, ymax)
        ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=100, decimals=0))

        ax.tick_params(labelsize=cfg.FONT_TICK)
        ax.legend(fontsize=cfg.FONT_LEGEND_SIZE)

        for i, v in enumerate(pcts):
            ax.text(i, min(v + 1.0, ymax), f"{v:.0f}%", ha="center", va="bottom", fontsize=9)

        ax.grid(axis="y", alpha=0.25)
        ax.set_axisbelow(True)

    return fig

def plot_matrix_stacked_percent(
    df_tidy: pd.DataFrame,
    question_text: str,
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
      - y labels wrapped via _wrap_labels()
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

    legend_farbe = [cfg.PALETTE[1],cfg.PALETTE[2],cfg.PALETTE[3]] #green for ja, orange for no, light blue for no answer

    for i, ans in enumerate(pivot_pct.columns):
        vals = pivot_pct[ans].values
        ax.barh(
            y,
            vals,
            left=left,
            color=legend_farbe[i],
            label=str(ans),
        )
        ax.legend(loc = "upper right", bbox_to_anchor=(1.1, 0.9))

        # add inside labels when big enough
        for j, v in enumerate(vals):
            if v >= label_min_pct:
                ax.text(
                    left[j] + v / 2,
                    j,
                    f"{v:.0f}%",
                    ha="center",
                    va="center",
                    fontsize=cfg.FONT_LEGEND_SIZE,   # keep uniform
                    color="white"
                )

        left += vals


    # y labels (wrapped)
    labels = pivot_pct.index.astype(str).tolist()
    wrapped = helper._wrap_labels(labels)

    ax.set_yticks(y)
    ax.set_yticklabels(wrapped)

    # x axis percent
    ax.set_xlim(0, 100)
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(xmax=100, decimals=0))
    ax.set_xlabel("Anteil der Teilnehmer in %")

    ax.tick_params(labelsize=cfg.FONT_TICK)
    ax.legend(fontsize=cfg.FONT_LEGEND_SIZE)

    # grid + style
    ax.grid(axis="x", alpha=0.25)
    ax.set_axisbelow(True)

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
    ax = fig.add_axes([cfg.AX_BOX_LEFT_DONUT, cfg.AX_BOX_BOTTOM, cfg.AX_BOX_WIDTH, cfg.AX_BOX_HEIGHT])
    helper._donut_one(ax, labels=helper._wrap_labels(labels), pcts=pcts)

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
        helper._add_caption(fig, cap)

        safe = helper._make_filename_safe(q["question_text"])
        filename = f"{prefix_index:02d}_{safe}.{cfg.SAVE_FORMAT}" if prefix_index is not None else f"{safe}.{cfg.SAVE_FORMAT}"

        out_path = out_dir / filename
        helper._save_fig(fig, out_path)
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

            helper._add_caption(fig, cap)

            safe_q = helper._make_filename_safe(q["question_text"])
            safe_item = helper._make_filename_safe(item_label)
            filename = f"{filename_prefix}{safe_q}__{safe_item}.{cfg.SAVE_FORMAT}"
            out_path = out_dir / filename

            helper._save_fig(fig, out_path)
            out_paths.append(out_path)

        return out_paths

    return out_paths

