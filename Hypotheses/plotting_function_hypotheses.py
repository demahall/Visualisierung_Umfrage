from __future__ import annotations
from typing import  Optional,List,Tuple
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import src.plotting.plotting_config as cfg
import src.plotting.plotting_helper as helper
from pathlib import Path
from Hypotheses.preprocessing_hypotheses import summarize_diverging,summarize_diverging_multiselect,_strong_counts


# ============================================================
# Plot for H1,H3
# ============================================================
def plot_diverging_yes_no(
    summary: pd.DataFrame,
    *,
    title: Optional[str] = None,
    ylabel: Optional[str] = None,
    wrap_width: int = 26,
    show_n_in_labels: bool = False,
) -> plt.Figure:
    """
    Creates a diverging horizontal bar plot:
      left  = NO (negative)
      right = YES (positive)
    Ticks shown as 0..100% on both sides (abs formatter).
    Legend outside top-right like your "single question" plotting_function_jg_analyse.
    """

    #labels -> 10-49, 50-250,<10,<250
    s = summary.copy()


    labels_raw = s["label"].astype(str).tolist()
    labels = helper._wrap_labels(labels_raw, width=wrap_width, max_lines=4)

    if show_n_in_labels:
        labels = [f"{lab} (n={n})" for lab, n in zip(labels, s["base_n"].tolist())]

    yes = s["yes_pct"].to_numpy(float)
    no  = s["no_pct"].to_numpy(float)

    y = np.arange(len(labels))

    fig = plt.figure(figsize=cfg.FIGSIZE)
    ax = fig.add_axes([cfg.AX_BOX_LEFT, cfg.AX_BOX_BOTTOM, cfg.AX_BOX_WIDTH, cfg.AX_BOX_HEIGHT])

    # bars
    ax.barh(y, -no, color=cfg.PALETTE[2], label="noch nicht umgesetzt")
    ax.barh(y,  yes, color=cfg.PALETTE[0], label="bereits umgesetzt")

    # middle line
    ax.axvline(0, color=cfg.PALETTE[0], lw=1.2, alpha=0.8)

    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()

    # axis label + ticks like 0..100% both sides
    ax.set_xlabel("Anteil der Teilnehmer in %")
    if ylabel:
        ax.set_ylabel(ylabel)

    ax.set_xlim(-100, 100)
    ax.set_xticks(np.arange(-100, 101, 25))
    ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: f"{abs(int(v))}%"))

    # fonts (closer to your other plotting_function_jg_analyse)
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

    s = helper._add_material_cost_group(summary)

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

    # OPTIONAL: _wrap_labels aus deinem plotting_function.py nutzen
    labels_wrapped = helper._wrap_labels(labels, width=wrap_width, max_lines=4)

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

def plot_hypotheses_and_save(
    df_tidy: pd.DataFrame,
    out_dir: Path,
    *,
    q_ce:str,
    q_h1_group:str,
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


    out_dir = Path(out_dir) / "hypotheses"
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

    h1 = summarize_diverging(df_tidy,initial_question=q_h1_group,target_question=q_ce)
    fig = plot_diverging_yes_no(
        h1,
        title="H1: Unternehmensgröße vs. CE umgesetzt",
        ylabel="Anzahl der Beschäftigten",
        sort_by_yes=False,
        wrap_width=22,
        show_n_in_labels=False,
    )
    cap = _next_caption("Hypothese 1 – Größere Unternehmen setzen häufiger bereits Kreislaufwirtschaft um als kleine Unternehmen.")
    helper._add_caption(fig, cap)
    p = out_dir / "H1_diverging.png"
    fig.savefig(p, dpi=300)
    plt.close(fig)
    saved.append(p); captions.append(cap)

    # --- H2 ---
    h2 = summarize_diverging_multiselect(df_tidy)
    fig = plot_diverging_yes_no_h2(
        h2,
        title="H2: Branche vs. CE umgesetzt (Mehrfachauswahl)",
        wrap_width=22,
    )
    cap = _next_caption("Hypothese 2 – Branchen mit hohen Materialkosten sind eher bereit, Kreislaufwirtschaft umzusetzen als Branchen mit geringeren Materialkosten.")
    helper._add_caption(fig, cap)
    p = out_dir / "H2_diverging.png"
    fig.savefig(p, dpi=300)
    plt.close(fig)
    saved.append(p); captions.append(cap)

    # --- H3 ---
    h3 = summarize_diverging(df_tidy, q_h3_group, q_ce)
    fig = plot_diverging_yes_no(
        h3,
        title="H3: Seriengröße vs. CE umgesetzt",
        ylabel="Monatliche Stückzahl",
        sort_by_yes=False,
        wrap_width=24,
        show_n_in_labels=False,
    )
    cap = _next_caption("Hypothese 3 – Kleinserien oder Einzelanfertigungen eignen sich für die Wiederaufbereitung eher als Großserienprodukte.")
    helper._add_caption(fig, cap)
    p = out_dir / "H3_diverging.png"
    fig.savefig(p, dpi=300)
    plt.close(fig)
    saved.append(p); captions.append(cap)

    # --- H4  ---
    h4_blocks = [
        ("H4_1", q_h4_block_1, strong_hemmnis, "Hypothese 4 – Top-5 als stark bewertete Hemmnisse."),
        ("H4_2", q_h4_block_2, strong_zustimmung, "Hypothese 4 – Top-5 als stark bewertete Zustimmung."),
        ("H4_3", q_h4_block_3, strong_hemmnis, "Hypothese 4 – Top-5 als stark bewertete Hemmnisse."),
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

        fig.savefig(p, dpi=300, bbox_inches="tight")
        plt.close(fig)
        saved.append(p)

        captions.append(_next_caption(abb) if abb is None else f"Abbildung {abb}: {abb}")

    return saved, captions

