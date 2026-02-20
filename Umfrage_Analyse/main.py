# main.py
# ------------------------------------------------------------
# Main entrypoint for survey analysis pipeline.
# - Loads df_tidy + catalog once
# - Runs Layer-1 mapping (GU/KMU)
# - Runs analysis modules that return tidy summaries with consistent structure
# ------------------------------------------------------------

from pathlib import Path

from Umfrage_Analyse.analyses import ANALYSES
from preprocessing import prepare_data
from analyses.gu_kmu_classification import build_company_size_mapping
from src.plotting.plotting_config import apply_style

import hypothesen_CONST as const
from src.plotting.plot_i_40_einsatz import plot_grouped_pct_prepared
from src.plotting.plotting_hemmnisse import plot_grouped_likert_means
from src.plotting.plotting_crosstab_frage import plot_crosstab_frage
from src.plotting.plotting_zustimmung import plot_zustimmung_yesno_stacked_by_group
def main():

    current_path = Path(__file__).resolve()
    input_path = current_path.parent.parent
    EXCEL_PATH = input_path / "result-survey.xlsx"
    SPEC_PATH = input_path / "question_spec.json"
    FIRST_QUESTION_TEXT = "Welcher Art von Organisation gehören Sie an?"

    apply_style()
    # Load once
    _, _, catalog, df_tidy, base_map = prepare_data(
        excel_path=EXCEL_PATH,
        first_question_text=FIRST_QUESTION_TEXT,
        sheet_name=0,
        spec_path=SPEC_PATH,
    )

    # Optional: save to folder for plotting
    out_dir = Path("out")
    out_dir.mkdir(exist_ok=True)

    # Layer 1: company size classification
    df_size_class = build_company_size_mapping(df_tidy=df_tidy, catalog=catalog)
    df_size_class.to_csv(out_dir/"size_class.csv", index=False)

    # Shared context (all available inputs)
    ctx = {
        "df_tidy": df_tidy,
        "catalog": catalog,
        "base_map": base_map,
        "df_size_class": df_size_class,
    }

    # Run analyses using only required inputs
    results = {}
    for spec in ANALYSES:
        key = spec["key"]
        func = spec["func"]
        needs = spec.get("needs", [])

        kwargs = {name: ctx[name] for name in needs}  # <- only pass what is needed
        df_out = func(**kwargs)

        results[key] = df_out

        #df_out.to_csv(out_dir / f"{key}.csv", index=False)



    """
    
    
    fig = plot_grouped_pct_prepared(
        results["i40_einsatz_planung"],
        title="Einsatz Industrie 4.0 (in Planung)",
        answer_value="In Planung"
    )
    
    fig = plot_grouped_pct_prepared(
        results["i40_einsatz_planung"],
        title="Einsatz Industrie 4.0 (in Planung)",
        answer_value="Im Einsatz"
    )
    
    fig1 = plot_grouped_likert_means(
        results["likert_mean"],
    title="Hemmnisse 1",
    question_texts=const.Q31)
    
    fig2 = plot_grouped_likert_means(  
    results["likert_mean"],
    title="Hemmnisse 2",
    question_texts=const.Q33)
    
    fig3 = plot_grouped_likert_means(
    results["likert_mean"],
    title="Daten Erfassung",
    question_texts=const.Q16)
    
    fig4 = plot_grouped_likert_means(
    re
    
        fig = plot_crosstab_frage(
        results["stueckzahl_kennzahlen"],
    title="Stueckzahl Kennzahlen",
    question_text=const.Q10)
    
    
    fig = plot_crosstab_frage(
        results["kw_mit_kz_und_zp"],
        title= "kw_mit_kz_und_zp",
        question_text=const.Q11
    )
    
    fig = plot_zustimmung_yesno_stacked_by_group(
        df_plot=results["zustimmung"],
        title="Zustimmung zu Aussagen – Anteil Ja/Nein (GU vs KMU)"
    )
    """










if __name__ == "__main__":
    main()




