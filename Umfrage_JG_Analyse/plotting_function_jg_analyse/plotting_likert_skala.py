import numpy as np
import matplotlib.pyplot as plt
import src.plotting.plotting_helper as helper
import src.plotting.plotting_config as cfg

def plot_grouped_likert_means(
    df_plot: "pd.DataFrame",
    *,
    question_texts: str,
    title: str,
    group_order: tuple[str, str] = ("KMU", "GU"),
    order: list[str] | None = None,
    xlim: tuple[float, float] = (1, 5),
    xticks: tuple[int, ...] = (1, 2, 3, 4, 5),
    footnote_text: str = "n variiert je Dimension aufgrund fehlender Antworten.",
) -> plt.Figure:
    """
    Required columns:
      - item
      - company_size_class
      - value
      - n_total
    """

    d = df_plot[df_plot["question_text"] == question_texts].copy()
    required = {"item", "company_size_class", "value", "n_total"}
    missing = required - set(d.columns)
    if missing:
        raise ValueError(f"df_plot missing columns: {missing}")

    if title is None:
        title = question_texts

    # n_total per group (constant)
    n_map = d.groupby("company_size_class")["n_total"].first().to_dict()

    def legend_label(g: str) -> str:
        return f"{g} (n={int(n_map.get(g, 0))})"

    # item order
    items = d["item"].astype(str).unique().tolist() if order is None else order

    piv = (
        d.assign(item=d["item"].astype(str))
         .pivot_table(index="item", columns="company_size_class", values="value", aggfunc="mean")
         .reindex(items)
         .fillna(0.0)
    )
    for g in group_order:
        if g not in piv.columns:
            piv[g] = 0.0
    piv = piv[list(group_order)]

    # group_order[0]-> KMU
    labels = piv.index.tolist()
    v1 = piv[group_order[1]].values
    v2 = piv[group_order[0]].values

    wrapped = helper._wrap_labels(labels, width=40, max_lines=3)
    left = helper._left_margin_for_labels(wrapped, base=0.24, per_char=0.0035, cap=0.52)

    fig = plt.figure(figsize=cfg.FIGSIZE)
    ax = fig.add_axes([cfg.AX_BOX_LEFT, cfg.AX_BOX_BOTTOM, cfg.AX_BOX_WIDTH, cfg.AX_BOX_HEIGHT])

    y = np.arange(len(labels))
    h = getattr(cfg, "GROUPED_BAR_HEIGHT", 0.35)
    off = h / 2.0


    ax.barh(y - off, v1, height=h, color=cfg.PALETTE[0], label=legend_label(group_order[1]))
    ax.barh(y + off, v2, height=h, color=cfg.PALETTE[1], label=legend_label(group_order[0]))

    ax.set_yticks(y)
    ax.set_yticklabels(wrapped)

    ax.set_xlim(*xlim)
    ax.set_xticks(list(xticks))
    #ax.set_title(title, fontsize=cfg.FONT_TITLE)

    # value labels
    for i, v in enumerate(v1):
        ax.text(v + 0.05, y[i] - off, f"{v:.1f}".replace(".", ","), va="center", fontsize=cfg.FONT_BAR_LABEL)
    for i, v in enumerate(v2):
        ax.text(v + 0.05, y[i] + off, f"{v:.1f}".replace(".", ","), va="center", fontsize=cfg.FONT_BAR_LABEL)

    ax.grid(axis="x", alpha=0.25)
    ax.set_axisbelow(True)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.18), ncol=2, fontsize=cfg.FONT_LEGEND_SIZE)

    ax.invert_yaxis()
    fig.subplots_adjust(left=left, right=0.98, top=0.95, bottom=0.26)

    fig.text(0.5, cfg.CAPTION_Y + 0.1, footnote_text, ha="center", va="bottom", fontsize=cfg.FONT_LEGEND_SIZE)

    return fig