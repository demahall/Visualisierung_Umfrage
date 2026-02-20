import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import src.plotting.plotting_helper as helper

import src.plotting.plotting_config as cfg


def plot_crosstab_frage(
    df_plot: "pd.DataFrame",
    *,
    target_item: str,          # target_question filter
    title: str,                  # plot title
    answer_order: tuple[str, str] = ("Ja", "Nein"),
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

    for a in answer_order:
        if a not in piv.columns:
            piv[a] = 0.0
    piv = piv[list(answer_order)]

    y_labels = piv.index.tolist()
    ja = piv[answer_order[0]].values
    nein = piv[answer_order[1]].values

    # wrap + margin
    wrapped = helper.wrap_labels(y_labels, width=42, max_lines=2)
    left = helper._left_margin_for_labels(wrapped, base=0.22, per_char=0.0040, cap=0.50)

    # 5) figure / axes
    fig = plt.figure(figsize=cfg.FIGSIZE)
    ax = fig.add_axes([cfg.AX_BOX_LEFT, cfg.AX_BOX_BOTTOM, cfg.AX_BOX_WIDTH, cfg.AX_BOX_HEIGHT])

    y = np.arange(len(y_labels))
    h = getattr(cfg, "GROUPED_BAR_HEIGHT", 0.35)
    off = h / 2.0

    # colors (new variables not required; fallback to palette)
    c_ja = cfg.PALETTE[0]
    c_nein = cfg.PALETTE[1]

    v_yes_draw = np.nan_to_num(ja, nan=0.0)
    v_no_draw = np.nan_to_num(nein, nan=0.0)

    ax.barh(y - off, v_yes_draw, height=h, color=c_ja, label=answer_order[0])
    ax.barh(y + off, v_no_draw, height=h, color=c_nein, label=answer_order[1])


    ax.set_yticks(y)
    ax.set_yticklabels(wrapped)

    ax.set_xlim(0, 100)
    ax.set_xticks([0, 50, 100])
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(xmax=100, decimals=cfg.AXIS_PCT_DECIMALS))
    ax.set_xlabel("Anteil (%)")

    ax.set_title(title, fontsize=cfg.FONT_TITLE)

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
    fig.subplots_adjust(left=left, right=0.98, top=0.95, bottom=0.26)

    plt.show()
    return fig