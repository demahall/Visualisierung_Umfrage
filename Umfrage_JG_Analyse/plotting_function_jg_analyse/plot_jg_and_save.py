from pathlib import Path
from typing import List, Tuple
from src.plotting import (
    plot_grouped_pct_prepared,
    plot_grouped_likert_means,
    plot_zustimmung_yesno_stacked_by_group,
    plot_crosstab_frage,
)
import QUESTION_LIST as const
import src.plotting.plotting_helper as helper
import src.plotting.plotting_config as cfg


def plot_jg_and_save(results: dict, out_dir: Path) -> Tuple[List[Path], List[str]]:

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

    # --- plotting_function_jg_analyse ---
    fig = plot_grouped_pct_prepared(
        results["i40_einsatz_planung"],
        title="Einsatz von Industrie 4.0 (in Planung)",
        answer_value="In Planung"
    )
    save(fig, "Einsatz von Industrie 4.0 (In Planung) ", "Einsatz von Industrie 4.0 (in Planung)")

    fig = plot_grouped_pct_prepared(
        results["i40_einsatz_planung"],
        title="Einsatz Industrie 4.0 (im Einsatz)",
        answer_value="Im Einsatz"
    )
    save(fig, "Einsatz von Industrie 4.0 (Im Einsatz) ", "Einsatz Industrie 4.0 (im Einsatz)")

    fig = plot_grouped_likert_means(
        results["likert_mean"],
        title="Hemmnisse für die Umsetzung von KL in dem Unternehmen",
        question_texts=const.Q31
    )
    save(fig, "Hemmnisse für die Umsetzung von KL in dem Unternehmen", "Hemmnisse für die Umsetzung von KL in dem Unternehmen")

    fig = plot_grouped_likert_means(
        results["likert_mean"],
        title="Hemmnisse für die Umsetzung zirkulärer Wertschöpfungsprozesse",
        question_texts=const.Q33
    )
    save(fig, "Hemmnisse für die Umsetzung zirkulärer Wertschöpfungsprozesse", "Hemmnisse für die Umsetzung zirkulärer Wertschöpfungsprozesse")

    fig = plot_grouped_likert_means(
        results["likert_mean"],
        title="Bewertung der Erfassung und Benutzung von Daten in Unternehmen",
        question_texts=const.Q16
    )
    save(fig, "Bewertung der Erfassung und Benutzung von Daten in Unternehmen", "Bewertung der Erfassung und Benutzung von Daten in Unternehmen")

    fig = plot_grouped_pct_prepared(
        df_plot=results["zustimmung"],
        answer_value="Ja",
        title="Zustimmung zur Digitalisierung und Quantifizierung zir. Wertschöpfungsprozesse (Stimmt zu)"
    )
    save(fig, "Zustimmung zur Digitalisierung und Quantifizierung zir. Wertschöpfungsprozesse (Stimmt zu)", "Zustimmung zur Digitalisierung und Quantifizierung zir. Wertschöpfungsprozesse (Stimmt zu)")

    fig = plot_grouped_pct_prepared(
        df_plot=results["zustimmung"],
        answer_value="Nein",
        title="Zustimmung zur Digitalisierung und Quantifizierung zir. Wertschöpfungsprozesse (Stimmt nicht zu)"
    )
    save(fig, "Zustimmung zur Digitalisierung und Quantifizierung zir. Wertschöpfungsprozesse (Stimmt nicht zu)",
         "Zustimmung zur Digitalisierung und Quantifizierung zir. Wertschöpfungsprozesse (Stimmt nicht zu)")

    fig = plot_crosstab_frage(
        results["stueckzahl_kennzahlen"],
        title="Korrespondenz Stückzahl vs Kennzahlenstruktur",
        target_item=const.ITEM_Q20_1,
        y_label="Monatliche Fertigungsstückzahl",
        y_ticks=None
    )
    save(fig, "Zustimmung zur KPI-Kaskade für lineare Produktionsprozesse nach monatlicher Fertigungsstückzahl", "Korrespondenz Stückzahl vs Kennzahlenstruktur")

    fig = plot_crosstab_frage(
        results["kw_mit_kz_und_zp"],
        title="Korrespondenz Kreislaufwirtschaft vs Kennzahlenstruktur",
        target_item=const.ITEM_Q20_1,
        y_label="Umsetzungsstand Kreislaufwirtschaft",
        y_ticks=["bereits umgesetzt","noch nicht umgesetzt"],
    )
    save(fig, "Zustimmung zur KPI-Kaskade (linear) und zu Kennzahlensystemen für zirkuläre Prozesse nach Umsetzungsstand der Kreislaufwirtschaft", "Korrespondenz Kreislaufwirtschaft vs Kennzahlenstruktur")

    fig = plot_crosstab_frage(
        results["kw_mit_kz_und_zp"],
        title="Korrespondenz Kreislaufwirtschaft vs zirkuläre Prozesse",
        target_item=const.ITEM_Q20_2,
        y_label="Umsetzungsstand Kreislaufwirtschaft",
        y_ticks=["bereits umgesetzt","noch nicht umgesetzt"],

    )
    save(fig,"Zustimmung zu Kennzahlensystemen für zirkuläre Prozesse nach Umsetzungsstand der Kreislaufwirtschaft","Korrespondenz Kreislaufwirtschaft vs zirkuläre Prozesse")

    fig = plot_crosstab_frage(
        results["us_mit_ks_und_zp"],
        title="Korrespondenz Unternehmensstrategie vs zirkuläre Prozesse",
        target_item=const.ITEM_Q20_1,
        y_label="CE ist ein Unternehmensstrategien",
        y_ticks=["zutreffend","nicht zutreffend"],
    )
    save(fig,"Zustimmung zur KPI-Kaskade (linear) nach strategischer Verankerung der Kreislaufwirtschaft.","Korrespondenz Unternehmensstrategie vs zirkuläre Prozesse")

    fig = plot_crosstab_frage(
        results["us_mit_ks_und_zp"],
        title="Korrespondenz Unternehmensstrategie vs zirkuläre Prozesse",
        y_label="CE ist ein Unternehmensstrategien",
        target_item=const.ITEM_Q20_2,
        y_ticks=["zutreffend","nicht zutreffend"],
    )

    save(fig, "Zustimmung zu Kennzahlensystemen für zirkuläre Prozesse nach strategischer Verankerung der Kreislaufwirtschaft", "Korrespondenz Unternehmensstrategie vs zirkuläre Prozesse")

    return out_paths, captions