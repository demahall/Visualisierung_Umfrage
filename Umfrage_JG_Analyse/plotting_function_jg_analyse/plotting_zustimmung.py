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

    wrapped = helper._wrap_labels(y_labels)

    # values in plotting order
    yes = piv[answer_order[0]].values
    no  = piv[answer_order[1]].values

    # --- figure/axes ---
    fig = plt.figure(figsize=cfg.FIGSIZE)
    ax = fig.add_axes([cfg.AX_BOX_LEFT, cfg.AX_BOX_BOTTOM, cfg.AX_BOX_WIDTH, cfg.AX_BOX_HEIGHT])

    # idx is list of tuples (dimension_text, "GU"/"KMU") length 12
    y = []
    cur = 0.0
    prev_dim = None

    for dim, grp in idx:
        if prev_dim is None:
            pass
        elif dim != prev_dim:
            cur += cfg.HBAR_GROUP_GAP  # big gap between dimensions
        else:
            cur += cfg.HBAR_INNER_GAP  # small gap within dimension (GU -> KMU)
        y.append(cur)
        prev_dim = dim

    y = np.array(y)

    # colors
    c_yes = cfg.PALETTE[0]
    c_no  = cfg.PALETTE[2]

    ax.barh(y, yes, height=cfg.HBAR_BAR_HEIGHT ,color=c_yes, label="Stimme zu")
    ax.barh(y, no,height= cfg.HBAR_BAR_HEIGHT,  left=yes, color=c_no, label="Stimme nicht zu")

    ax.set_yticks(y)
    ax.set_yticklabels(wrapped)
    ax.tick_params(labelsize=cfg.FONT_TICK)
    ax.legend(fontsize=cfg.FONT_LEGEND_SIZE)

    ax.set_xlim(0, 100)
    ax.set_xticks([0, 25, 50,75, 100])
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(xmax=100, decimals=cfg.AXIS_PCT_DECIMALS))
    ax.set_xlabel("Anteil der Teilnehmer in %")

    #ax.set_title(title, fontsize=cfg.FONT_TITLE)

    # write "GU"/"KMU" at left of each row (inside axis area)
    ymin, ymax = ax.get_ylim()
    for yi, (_, g) in zip(y, idx):
        # Convert data y -> axes y (0..1)
        y_ax = (yi - ymin) / (ymax - ymin)

        ax.text(
            1.01, ymax-y_ax, g,  # x slightly outside axis
            transform=ax.transAxes,
            va="center", ha="left",
            fontsize=cfg.FONT_TICK,
            clip_on=False,  # allow outside drawing
        )
    inside_threshold = 8.0  # show label only if segment >= 8%

    for i in range(len(y)):
        yi = y[i]

        if yes[i] >= inside_threshold:
            ax.text(
                yes[i] / 2, yi, f"{yes[i]:.0f}%",
                ha="center", va="center",
                fontsize=cfg.FONT_BAR_LABEL,
                color="white",
            )

        if no[i] >= inside_threshold:
            ax.text(
                yes[i] + no[i] / 2, yi, f"{no[i]:.0f}%",
                ha="center", va="center",
                fontsize=cfg.FONT_BAR_LABEL,
                color="white",
            )

    ax.grid(axis="x", alpha=0.25)
    ax.set_axisbelow(True)

    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.18), ncol=2, fontsize=cfg.FONT_LEGEND_SIZE)

    ax.invert_yaxis()

    return fig