import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import src.plotting.plotting_helper as helper
import src.plotting.plotting_config as cfg


def plot_zustimmung_yesno_stacked_by_group(
    df_plot: "pd.DataFrame",
    *,
    title: str,
    question_text: str | None = None,   # optional if your df has question_text
    group_order: tuple[str, str] = ("GU", "KMU"),
    answer_order: tuple[str, str] = ("Ja", "Nein"),
    item_order: list[str] | None = None,
) -> plt.Figure:
    """
    Stacked horizontal bars for Yes/No per group (GU/KMU) for each item.
    Layout: for each item -> two rows: GU (top), KMU (bottom)

    Required columns:
      - item
      - company_size_class
      - answer  ("Ja"/"Nein")
      - pct     (0..100)

    Optional:
      - question_text (if you want filtering)
      - total (for legend n per group)
    """

    required = {"item", "company_size_class", "answer", "pct"}
    missing = required - set(df_plot.columns)
    if missing:
        raise ValueError(f"df_plot missing columns: {missing}")

    d = df_plot.copy()

    # optional question filter
    if question_text is not None:
        if "question_text" not in d.columns:
            raise ValueError("question_text provided but df_plot has no 'question_text' column")
        d = d[d["question_text"] == question_text].copy()
        if d.empty:
            raise ValueError(f"No rows found for question_text == {question_text!r}")

    # item order
    if item_order is None:
        items = d["item"].astype(str).unique().tolist()
    else:
        items = item_order

    # --- build table: index = (item, group), columns = answer -> pct ---
    piv = (
        d.assign(item=d["item"].astype(str))
         .pivot_table(index=["item", "company_size_class"], columns="answer", values="pct", aggfunc="mean")
    )

    # ensure all answers exist
    for a in answer_order:
        if a not in piv.columns:
            piv[a] = 0.0
    piv = piv[list(answer_order)].fillna(0.0)

    # ensure all item x group combinations exist (fill with 0)
    idx = [(it, g) for it in items for g in group_order]
    piv = piv.reindex(idx, fill_value=0.0)

    # y labels: only show item on first row; second row blank (like “grouped under item”)
    y_labels = []
    for it in items:
        y_labels.append(it)      # first row (GU)
        y_labels.append("")      # second row (KMU)

    wrapped = helper.wrap_labels(y_labels, width=55, max_lines=2)
    left = helper._left_margin_for_labels(wrapped, base=0.24, per_char=0.0035, cap=0.52)

    # values in plotting order
    yes = piv[answer_order[0]].values
    no  = piv[answer_order[1]].values

    # --- figure/axes ---
    fig = plt.figure(figsize=cfg.FIGSIZE)
    ax = fig.add_axes([cfg.AX_BOX_LEFT, cfg.AX_BOX_BOTTOM, cfg.AX_BOX_WIDTH, cfg.AX_BOX_HEIGHT])

    y = np.arange(len(idx))

    # colors
    c_yes = cfg.PALETTE[0]
    c_no  = cfg.PALETTE[1]

    ax.barh(y, yes, color=c_yes, label=answer_order[0])
    ax.barh(y, no,  left=yes, color=c_no, label=answer_order[1])

    ax.set_yticks(y)
    ax.set_yticklabels(wrapped)

    ax.set_xlim(0, 100)
    ax.set_xticks([0, 50, 100])
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(xmax=100, decimals=cfg.AXIS_PCT_DECIMALS))
    ax.set_xlabel("Anteil (%)")
    ax.set_title(title, fontsize=cfg.FONT_TITLE)

    # write "GU"/"KMU" at left of each row (inside axis area)
    ymin, ymax = ax.get_ylim()
    for i, (it, g) in enumerate(idx):
        # convert data-y (i) to axes-y (0..1)
        y_ax = (i - ymin) / (ymax - ymin)
        ax.text(
            1.01, y_ax, g,
            transform=ax.transAxes,
            va="center", ha="left",
            fontsize=cfg.FONT_TICK,
            clip_on=False,  # IMPORTANT: allow drawing outside
        )

    # labels inside bar segments (only if enough space)
    inside_threshold = 8.0
    for i in range(len(y)):
        if yes[i] >= inside_threshold:
            ax.text(yes[i] / 2, i, f"{yes[i]:.0f}%", ha="center", va="center",
                    fontsize=cfg.FONT_BAR_LABEL, color="white")
        if no[i] >= inside_threshold:
            ax.text(yes[i] + no[i] / 2, i, f"{no[i]:.0f}%", ha="center", va="center",
                    fontsize=cfg.FONT_BAR_LABEL, color="white")

    ax.grid(axis="x", alpha=0.25)
    ax.set_axisbelow(True)

    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.18), ncol=2, fontsize=cfg.FONT_LEGEND_SIZE)

    ax.invert_yaxis()
    fig.subplots_adjust(left=left, right=0.92, top=0.95, bottom=0.26)
    plt.show()

    return fig