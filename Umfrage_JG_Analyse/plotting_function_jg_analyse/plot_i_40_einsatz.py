import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

import src.plotting.plotting_config as cfg
import src.plotting.plotting_helper as helper


def plot_grouped_pct_prepared(
    df_plot: "pd.DataFrame",
    answer_value: str,                 # "Im Einsatz" oder "In Planung"
    title: str,
    order: list[str] | None = None,
    group_order: tuple[str, str] = ("KMU", "GU"),
) -> plt.Figure:
    """
    Grouped horizontal percent bar chart from a prepared dataframe.

    Required columns:
      - item
      - company_size_class  (KMU/GU)
      - answer              ("Im Einsatz" / "In Planung")
      - pct                 (0..100)
      - total               (base N per group, repeated per row)
    """

    # 1) Filter rows for this answer
    d = df_plot[df_plot["answer"] == answer_value].copy()

    # 2) Get base N per group from column "total"
    # (assumes total is constant within each company_size_class)
    n_map = d.groupby("company_size_class")["total"].first().to_dict()

    def legend_label(g: str) -> str:
        return f"{g} (n={int(n_map.get(g, 0))})"

    # 3) Category order
    items = d["item"].astype(str).unique().tolist() if order is None else order

    # 4) Pivot to two series (KMU vs GU)
    piv = (
        d.assign(item=d["item"].astype(str))
         .pivot_table(index="item", columns="company_size_class", values="pct", aggfunc="mean")
         .reindex(items)
         .fillna(0.0)
    )
    for g in group_order:
        if g not in piv.columns:
            piv[g] = 0.0
    piv = piv[list(group_order)]

    labels = piv.index.tolist()

    #group_order[0]-> KMU, v2-> KMU
    v1 = piv[group_order[1]].values
    v2 = piv[group_order[0]].values

    # 5) Wrap labels + compute margin to avoid cutting
    wrapped = helper._wrap_labels(labels)
    # 6) Figure + axes
    fig = plt.figure(figsize=cfg.FIGSIZE)
    ax = fig.add_axes([cfg.AX_BOX_LEFT, cfg.AX_BOX_BOTTOM, cfg.AX_BOX_WIDTH, cfg.AX_BOX_HEIGHT])

    # 7) Bars (two per category)
    y = np.arange(len(labels))
    h = cfg.HBAR_BAR_HEIGHT
    off = h / 2.0

    ax.barh(y - off, v1, height=h, color=cfg.PALETTE[0], label=legend_label(group_order[1]))
    ax.barh(y + off, v2, height=h, color=cfg.PALETTE[1], label=legend_label(group_order[0]))
    ax.legend(fontsize=cfg.FONT_LEGEND_SIZE)

    ax.set_yticks(y)
    ax.tick_params(labelsize=cfg.FONT_TICK)
    ax.set_yticklabels(wrapped)
    ax.set_xlabel("Anteil der Teilnehmer in %")
    #ax.set_title(title, fontsize=cfg.FONT_TITLE)

    # 8) X axis fixed 0–100
    ax.set_xlim(0, 100)
    ax.set_xticks([0,25, 50,75, 100])
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(xmax=100, decimals=cfg.AXIS_PCT_DECIMALS))

    # 9) Value labels at bar end
    for i, v in enumerate(v1):
        ax.text(min(v + 1.0, 100), y[i] - off, f"{v:.0f}%", va="center", fontsize=cfg.FONT_BAR_LABEL)
    for i, v in enumerate(v2):
        ax.text(min(v + 1.0, 100), y[i] + off, f"{v:.0f}%", va="center", fontsize=cfg.FONT_BAR_LABEL)

    # 10) Grid + legend
    ax.grid(axis="x", alpha=0.25)
    ax.set_axisbelow(True)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.18), ncol=2, fontsize=cfg.FONT_LEGEND_SIZE)

    # match your examples: first category at top
    ax.invert_yaxis()

    # avoid label cut
    fig.subplots_adjust(left=0.50)

    return fig