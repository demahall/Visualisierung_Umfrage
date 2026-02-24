from __future__ import annotations
from typing import  Optional,List,Tuple
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import src.plotting.plotting_config as cfg
import src.plotting.plotting_helper as helper
from pathlib import Path



# ============================================================
# Plot for H1,H3
# ============================================================
def plot_diverging(
    df_hypotheses: pd.DataFrame,
    ylabel: str,
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
    df = df_hypotheses.copy()

    labels_raw = df["initial_question_label"].astype(str).tolist()
    labels = helper._wrap_labels(labels_raw)

    if show_n_in_labels:
        labels = [f"{lab} (n={n})" for lab, n in zip(labels, df["base_n"].tolist())]

    yes = df["yes_pct"].to_numpy(float)
    no  = df["no_pct"].to_numpy(float)

    y = np.arange(len(labels))

    fig = plt.figure(figsize=cfg.FIGSIZE)
    ax = fig.add_axes([cfg.AX_BOX_LEFT, cfg.AX_BOX_BOTTOM, cfg.AX_BOX_WIDTH, cfg.AX_BOX_HEIGHT])

    h = cfg.HBAR_BAR_HEIGHT
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

    ax.tick_params(labelsize=cfg.FONT_TICK)

    min_inbar = 6  # if a bar size is too small, skip it

    for i, (yp, npct) in enumerate(zip(yes, no)):
        # LEFT (no) is negative in your plot => use abs for width decisions
        if npct > 0 and abs(npct) >= min_inbar:
            ax.text(-abs(npct) / 2, i, f"{abs(npct):.0f}%",
                    va="center", ha="center", fontsize=cfg.FONT_TICK,color="white")

        # RIGHT (yes) is positive
        if yp > 0 and yp >= min_inbar:
            ax.text(yp / 2, i, f"{yp:.0f}%",
                    va="center", ha="center", fontsize=cfg.FONT_TICK,color="white")

    # grid
    ax.grid(axis="x", alpha=0.18)
    ax.set_axisbelow(True)

    # legend outside (top-right) like your stacked bar example
    ax.legend(
        loc="upper left",
        bbox_to_anchor=(1.02, 1.0),
        frameon=False,
        fontsize=cfg.FONT_LEGEND_SIZE,
    )


    return fig


def plot_diverging_h1(df_hypotheses: pd.DataFrame,
                      ylabel = "Anzahl der Beschäftigten",
                      show_n_in_labels = False)-> plt.Figure:

    #labels -> 10-49, 50-250,<10,<250
    df = df_hypotheses.copy()
    # rearrange index

    order = ["< 10", "10 - 49", "50 - 250", "> 250"]

    df["initial_question_label"] = pd.Categorical(
        df["initial_question_label"],
        categories=order,
        ordered=True
    )

    df = df.sort_values("initial_question_label").reset_index(drop=True)

    fig = plot_diverging(df,ylabel=ylabel,show_n_in_labels=show_n_in_labels)
    return fig

# ============================================================
# Plot for H2
# ============================================================
def plot_diverging_h2(df_hypotheses: pd.DataFrame) -> plt.Figure:

    df = df_hypotheses.copy()

    # sort: high first, then low, then other; inside group by yes_pct desc
    order_map = {"Hohe Materialkosten": 0, "Geringe Materialkosten": 1, "Sonstige/unklar": 2}

    df["_grp"] = df["cost_group"].map(order_map).fillna(9)
    df = df.sort_values(["_grp", "yes_pct"], ascending=[True, False]).drop(columns=["_grp"])

    # feed into base plotter by renaming label
    s2 = df.rename(columns={"label": "label_orig"})
    s2["initial_question_label"] = s2["label_marked"]

    fig = plot_diverging(
        df_hypotheses=s2,
        ylabel="Branche (▲ hoch / ▼ niedrig / • unklar)",
    )
    return fig

# ============================================================
# Plot H4
# ============================================================
def plot_netzdiagramm(
    df_hypotheses: "pd.Series",
):
    # --- 1) Top-k auswählen (und NaNs absichern) ---
    s = df_hypotheses.dropna().sort_values(ascending=False)

    k = 5 # nur 5 am meisten ausgewählte options
    r_step = 5

    s = s.head(k)

    labels = s.index.astype(str).tolist()
    values = s.values.astype(float).tolist()

    # OPTIONAL: _wrap_labels aus deinem plotting_function.py nutzen
    labels_wrapped = helper._wrap_labels(labels,width=30,max_lines=3)

    n = len(labels_wrapped)

    # --- 2) Angles passend zu Top-k bauen ---
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()

    # Close polygon
    angles_closed = angles + angles[:1]
    values_closed = values + values[:1]

    # --- 3) Plot ---
    fig = plt.figure(figsize=cfg.FIGSIZE)
    ax = fig.add_axes([0.15, 0.2, 0.7, 0.7], polar=True)



    ax.plot(angles_closed, values_closed, linewidth=2)
    ax.fill(angles_closed, values_closed, alpha=0.12)

    # --- 4) Ticks/Labels: EXACT MATCH ---
    ax.set_xticks(angles)
    ax.set_xticklabels(labels_wrapped)

    #damit das Label nicht überlappen
    ax.tick_params(axis='x', pad=38)

    # --- 5) Radius/Skalierung ---
    vmax = max(values) if values else 0
    rmax = int(np.ceil(vmax / r_step) * r_step) if vmax > 0 else r_step
    ax.set_ylim(0, rmax)
    ax.set_yticks(list(range(0, rmax + 1, r_step)))
    ax.set_yticklabels([str(v) for v in range(0, rmax + 1, r_step)])

    ax.tick_params(labelsize=cfg.FONT_LEGEND_SIZE)

    for a, v in zip(angles, values):
        ax.text(a, v +2, f"{int(v)}", ha="center", va="center", fontsize=10)

    return fig

def plot_hypotheses_and_save(
    df_hypotheses: dict,
    out_dir: Path,
    start_abbildung_index: int | None = None,
) -> Tuple[List[Path], List[str]]:


    out_dir = Path(out_dir) / "hypotheses"
    out_dir.mkdir(parents=True, exist_ok=True)

    out_paths: List[Path] = []
    captions: List[str] = []
    prefix_index = 1

    def save(fig, caption_text: str, safe_name: str):
        nonlocal prefix_index

        cap = f"Abbildung {prefix_index}: {caption_text}"
        helper._add_caption(fig, cap)

        filename = f"{prefix_index:02d}_{safe_name}.{cfg.SAVE_FORMAT}"
        out_path = out_dir / filename
        helper._save_fig(fig, out_path)

        out_paths.append(out_path)
        captions.append(cap)
        prefix_index += 1



    # --- plotting_function_hypotheses ---

    # ------H1--------
    fig = plot_diverging_h1(
        df_hypotheses=df_hypotheses["H1"],
        ylabel="Anzahl der Beschäftigten",
        show_n_in_labels=False,
    )

    save(fig, caption_text="Hypothese 1 – Größere Unternehmen setzen häufiger bereits Kreislaufwirtschaft um als kleine Unternehmen.",
         safe_name="Hypothese 1 – Größere Unternehmen setzen häufiger bereits Kreislaufwirtschaft um als kleine Unternehmen.")


    # --- H2 ---
    fig = plot_diverging_h2(
        df_hypotheses=df_hypotheses["H2"])

    save(fig, caption_text="Hypothese 2 – Branchen mit hohen Materialkosten sind eher bereit, Kreislaufwirtschaft umzusetzen als Branchen mit geringeren Materialkosten.",
         safe_name="Hypothese 2 – Branchen mit hohen Materialkosten sind eher bereit, Kreislaufwirtschaft umzusetzen als Branchen mit geringeren Materialkosten.")

    # --- H3 ---

    fig = plot_diverging(
        df_hypotheses=df_hypotheses["H3"],
        ylabel="Monatliche Stückzahl",
        show_n_in_labels=False,
    )

    save(fig,caption_text="Hypothese 3 – Kleinserien oder Einzelanfertigungen eignen sich für die Wiederaufbereitung eher als Großserienprodukte.",
        safe_name="Hypothese 3 – Kleinserien oder Einzelanfertigungen eignen sich für die Wiederaufbereitung eher als Großserienprodukte.")


    # --- H4.1  ---

    fig = plot_netzdiagramm(
        df_hypotheses=df_hypotheses["H4.1"],
    )

    save(fig,caption_text="Top-5 bewertete Hemmnisse für die Umsetzung von Kreislaufwirtschaft in Unternehmen.",
         safe_name="Top-5 bewertete Hemmnisse für die Umsetzung von Kreislaufwirtschaft in Unternehmen.")


    # ------H4.2 ----------
    fig = plot_netzdiagramm(
        df_hypotheses=df_hypotheses["H4.2"] )

    save(fig,caption_text="Top-5 bewertete Zustimmung zur Aussage der Umsetzung von CE bezogen auf die Wettbewerbsfähigkeit",
         safe_name="Top-5 bewertete Zustimmung zur Aussage der Umsetzung von CE bezogen auf die Wettbewerbsfähigkeit")

    #------H4.3 ----------
    fig = plot_netzdiagramm(
        df_hypotheses=df_hypotheses["H4.3"],
    )

    save(fig,caption_text="Top-5 der bewerteten Hemmnisse für die Elementen der Umsetzung zirkulärer Wertschöpfungsprozesse",
         safe_name="Top-5 der bewerteten Hemmnisse für die Elementen der Umsetzung zirkulärer Wertschöpfungsprozesse")

    return out_paths, captions

