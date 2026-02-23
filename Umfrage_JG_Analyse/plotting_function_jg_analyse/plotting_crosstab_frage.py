import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import src.plotting.plotting_helper as helper
from typing import List, Optional

import src.plotting.plotting_config as cfg


def plot_crosstab_frage(
    df_plot: "pd.DataFrame",
    *,
    target_item: str,          # target_question filter
    title: str,                  # plot title
    y_ticks:Optional[List],
    y_label: str,
) -> plt.Figure:
    """
    Input df_plot must contain:
      - segment
      - target_question
      - target_item
      - answer  (Ja/Nein)
      - pct     (0..100)
      - total   (optional, for legend n per segment, not used now)

    Output:
      horizontal stacked bar chart (Ja + Nein = 100%) for each segment.
    """

    required = {"segment", "target_question", "target_item", "answer", "pct"}
    missing = required - set(df_plot.columns)
    if missing:
        raise ValueError(f"df_plot missing columns: {missing}")

    # 1) filter question
    d = df_plot[df_plot["target_item"] == target_item].copy()
    if d.empty:
        raise ValueError(f"No rows found for target_question == {target_item!r}")


    segments = d["segment"].astype(str).unique().tolist()


    # 4) pivot Ja/Nein
    piv = (
        d.assign(segment=d["segment"].astype(str))
         .pivot_table(index="segment", columns="answer", values="pct", aggfunc="mean")
         .reindex(segments)
         .fillna(0.0)
    )


    y_labels = piv.index.tolist()
    ja = piv["Ja"].values
    nein = piv["Nein"].values

    # wrap
    wrapped = helper._wrap_labels(y_labels, width=42, max_lines=2)

    # 5) figure / axes
    fig = plt.figure(figsize=cfg.FIGSIZE)
    ax = fig.add_axes([cfg.AX_BOX_LEFT, cfg.AX_BOX_BOTTOM, cfg.AX_BOX_WIDTH, cfg.AX_BOX_HEIGHT])

    y = np.arange(len(y_labels))
    h = cfg.HBAR_BAR_HEIGHT
    off = h / 2.0


    v_yes_draw = np.nan_to_num(ja, nan=0.0)
    v_no_draw = np.nan_to_num(nein, nan=0.0)

    #hbar legend
    hbar_legend= ("Stimme zu", "Stimme gar nicht zu")
    if y_ticks is None:
        y_ticks = wrapped

    ax.barh(y - off, v_yes_draw, height=h, color=cfg.PALETTE[0], label=hbar_legend[0])
    ax.barh(y + off, v_no_draw, height=h, color=cfg.PALETTE[2], label=hbar_legend[1])
    ax.legend(fontsize=cfg.FONT_LEGEND_SIZE)

    ax.set_yticks(y)
    ax.set_yticklabels(y_ticks)
    ax.tick_params(labelsize=cfg.FONT_TICK)
    ax.set_xlim(0, 100)
    ax.set_xticks([0, 50, 100])
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(xmax=100, decimals=cfg.AXIS_PCT_DECIMALS))
    ax.set_xlabel("Anteil der Teilnehmer in %")
    ax.set_ylabel(y_label)

    #ax.set_title(title, fontsize=cfg.FONT_TITLE)

    inside_threshold = 8.0  # % width needed to fit text inside nicely

    for i, v in enumerate(ja):
        if np.isnan(v):
            continue
        if v >= inside_threshold:
            ax.text(v * 0.5, y[i] - off, f"{v:.0f}%", ha="center", va="center",
                    fontsize=cfg.FONT_BAR_LABEL, color="white")
        else:
            ax.text(min(v + 1.0, 100), y[i] - off, f"{v:.0f}%", va="center",
                    fontsize=cfg.FONT_BAR_LABEL)

    for i, v in enumerate(nein):
        if np.isnan(v):
            continue
        if v >= inside_threshold:
            ax.text(v * 0.5, y[i] + off, f"{v:.0f}%", ha="center", va="center",
                    fontsize=cfg.FONT_BAR_LABEL, color="white")
        else:
            ax.text(min(v + 1.0, 100), y[i] + off, f"{v:.0f}%", va="center",
                    fontsize=cfg.FONT_BAR_LABEL)


    ax.grid(axis="x", alpha=0.25)
    ax.set_axisbelow(True)

    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.18), ncol=2, fontsize=cfg.FONT_LEGEND_SIZE)

    ax.invert_yaxis()

    return fig