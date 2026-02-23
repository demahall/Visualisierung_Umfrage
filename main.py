"""
Main runner script.

What it does:
1) Loads the Excel survey export
2) Preprocesses into:
   - df_raw (full table)
   - df_q (question-only wide table + respondent_id)
   - catalog (question definitions + inferred types)
   - df_tidy (long/tidy table)
   - base_map (denominators per question; skip-logic aware)
3) Applies a uniform plotting style
4) Loops through all questions and saves plotting_function_jg_analyse to the output folder
5) Plots hypotheses (once)
6) Runs JG analysis (GU/KMU) and saves plotting_function_jg_analyse

How to run:
- Set EXCEL_PATH and FIRST_QUESTION_TEXT below
- Run: python main.py
"""

from __future__ import annotations

from typing import Any, List
from preprocessing import prepare_data
from logger import TinyLogger

import src.plotting.plotting_config as cfg
from plotting_function import plot_question_and_save

from Hypotheses.preprocessing_hypotheses import get_df_hypotheses
from Hypotheses import df_hypotheses_dict

from Umfrage_JG_Analyse.preprocessing_jg_analyse.gu_kmu_classification import gu_kmu_classification
from Umfrage_JG_Analyse.preprocessing_jg_analyse.finalize_output import get_df_jg
from Umfrage_JG_Analyse.plotting_function_jg_analyse.plot_jg_and_save import plot_jg_and_save
from Umfrage_JG_Analyse.preprocessing_jg_analyse import df_jg_dict

EXCLUDE_QUESTIONS_CONTAINS: List[str] = [
    # e.g. "E-Mail", "Name", "Telefon"
]
INCLUDE_ONLY_QUESTIONS_CONTAINS = None

PREFIX_WITH_INDEX = True


def should_skip_question(qtext: str) -> bool:
    """Return True if question should be skipped due to include/exclude filters."""
    if INCLUDE_ONLY_QUESTIONS_CONTAINS:
        if not any(s.lower() in qtext.lower() for s in INCLUDE_ONLY_QUESTIONS_CONTAINS):
            return True
    if EXCLUDE_QUESTIONS_CONTAINS:
        if any(s.lower() in qtext.lower() for s in EXCLUDE_QUESTIONS_CONTAINS):
            return True
    return False


def main() -> None:


    cfg.apply_style()

    # -------------------------
    # 1) LOAD + PREPROCESS
    # -------------------------
    df_raw, df_q, catalog, df_tidy, base_map = prepare_data(
        excel_path=cfg.EXCEL_PATH,
        first_question_text=cfg.FIRST_QUESTION_TEXT,
        sheet_name=0,
        spec_path=cfg.SPEC_PATH,
    )

    # gu_kmu für JG Analyse (GU/KMU classification)
    gu_kmu = gu_kmu_classification(df_tidy=df_tidy)

    # -------------------------
    # 2) LOGGER + DEBUG EXPORTS
    # -------------------------
    logger = TinyLogger(cfg.OUTPUT_DIR / "run_log.txt")
    logger.write(f"Excel: {cfg.EXCEL_PATH.resolve()}")
    logger.write(f"Spec:  {cfg.SPEC_PATH.resolve()}")
    logger.write(f"Output:{cfg.OUTPUT_DIR.resolve()}")
    logger.write(f"Catalog entries: {len(catalog)}")
    logger.write("")


    # state collectors
    saved: List[Any] = []
    list_of_figures: List[str] = []
    plot_i = 0

    ok_count = 0
    skip_count = 0
    fail_count = 0

    # -------------------------
    # 3) NORMAL QUESTION PLOTS
    # -------------------------
    logger.write("=== PLOTTING QUESTIONS ===")

    for q in catalog:
        qtext = (q.get("question_text") or "").strip()
        qtype = str(q.get("type") or "").strip().lower()
        ptype = str(q.get("plot_type") or "").strip().lower()

        # filters
        if should_skip_question(qtext):
            logger.write(f"[SKIP filter] | type={qtype} | plot={ptype} | {qtext}")
            skip_count += 1
            continue


        # explicitly skip text questions but keep numbering consistent
        if qtype == "text":
            plot_i += 1
            caption_text = (q.get("caption") or qtext).strip()

            logger.write(f"[SKIP text]   | Abbildung {plot_i} | {qtext}")
            if PREFIX_WITH_INDEX:
                list_of_figures.append(f"Abbildung {plot_i}: {caption_text}")
            else:
                list_of_figures.append(f"Abbildung: {caption_text}")

            skip_count += 1
            continue

        # increment Abbildung index (regardless of success to keep consistent numbering)
        plot_i += 1
        caption_text = (q.get("caption") or qtext).strip()

        try:
            out_paths = plot_question_and_save(
                q=q,
                df_tidy=df_tidy,
                base_map=base_map,
                out_dir= cfg.PLOTS_Q_DIR,
                prefix_index=plot_i if PREFIX_WITH_INDEX else None,
            )

            # If plot_question_and_save returns [] (e.g. internal skip), treat as skip
            if not out_paths:
                logger.write(
                    f"[SKIP none]   | Abbildung {plot_i} | type={qtype} | plot={ptype} | {qtext}"
                )
                if PREFIX_WITH_INDEX:
                    list_of_figures.append(f"Abbildung {plot_i}: {caption_text}")
                else:
                    list_of_figures.append(f"Abbildung: {caption_text}")
                skip_count += 1
                continue

            saved.extend(out_paths)
            ok_count += 1

            if PREFIX_WITH_INDEX:
                list_of_figures.append(f"Abbildung {plot_i}: {caption_text}")
                logger.write(
                    f"[OK]          | Abbildung {plot_i} | type={qtype} | plot={ptype} | "
                    f"saved={len(out_paths)} | {out_paths[0].name}"
                )
            else:
                list_of_figures.append(f"Abbildung: {caption_text}")
                logger.write(
                    f"[OK]          | type={qtype} | plot={ptype} | saved={len(out_paths)} | {out_paths[0].name}"
                )

        except Exception as e:
            fail_count += 1
            logger.write(
                f"[FAIL]        | Abbildung {plot_i} | type={qtype} | plot={ptype} | {qtext}"
            )
            logger.write(f"               error={repr(e)}")
            logger.write("               traceback:")
            logger.write_traceback()

    # -------------------------
    # 4) HYPOTHESES (RUN ONCE!)
    # -------------------------
    logger.write("")
    logger.write("=== PLOTTING HYPOTHESES ===")


    df_hypotheses = get_df_hypotheses(df_tidy,df_hypotheses_dict)
    print(df_hypotheses)

    try:
        hyp_paths, hyp_caps = plot_hypotheses_and_save(
            df_tidy=df_tidy,
            out_dir=cfg.PLOTS_H_DIR,
            q_ce=hyp_const.Q11,
            q_h1_group=hyp_const.Q2,
            q_h2_industry=hyp_const.Q4,
            q_h3_group=hyp_const.Q10,
            q_h4_block_1=hyp_const.Q31,
            q_h4_block_2=hyp_const.Q32,
            q_h4_block_3=hyp_const.Q33,
            h4_topk=5,
            strong_hemmnis=hyp_const.STRONG_CATEGORY_HEMMNIS,
            strong_zustimmung=hyp_const.STRONG_CATEGORY_ZUSTIMMUNG,
            start_abbildung_index=(plot_i if PREFIX_WITH_INDEX else None),
        )

        saved.extend(hyp_paths)
        list_of_figures.extend(hyp_caps)

        # keep numbering consistent
        if PREFIX_WITH_INDEX:
            plot_i += len(hyp_paths)

        logger.write(f"[OK] Hypotheses plotting_function_jg_analyse saved={len(hyp_paths)}")

    except Exception as e:
        logger.write(f"[FAIL] Hypotheses | error={repr(e)}")
        logger.write("traceback:")
        logger.write_traceback()

    # -------------------------
    # 5) JG ANALYSE (GU/KMU PLOTS)
    # -------------------------
    context = {
        "df_tidy": df_tidy,
        "gu_kmu": gu_kmu,
    }


    results = get_df_jg(df_jg_dict, context) #df_jg_dict ist eine Dict von verchiedene Plot Funktion

    out_paths, captions = plot_jg_and_save(results, out_dir=cfg.PLOTS_JG_DIR)

    print("Saved figures:")
    for p in out_paths:
        print("-", p)

    # -------------------------
    # 6) WRITE LIST OF FIGURES
    # -------------------------
    if list_of_figures:
        (cfg.OUTPUT_DIR / "list_of_figures.txt").write_text(
            "\n".join(list_of_figures), encoding="utf-8"
        )
        logger.write(f"[OK] Wrote list_of_figures.txt ({len(list_of_figures)} lines)")
    else:
        logger.write("[WARN] list_of_figures is empty (nothing written)")

    # -------------------------
    # 7) SUMMARY
    # -------------------------
    logger.write("")
    logger.write("=== SUMMARY ===")
    logger.write(f"Questions OK:      {ok_count}")
    logger.write(f"Questions skipped: {skip_count}")
    logger.write(f"Questions failed:  {fail_count}")
    logger.write(f"Saved plot files:  {len(saved)}")
    logger.write(f"Output folder:     {cfg.OUTPUT_DIR.resolve()}")

    logger.close()

    print(f"\nDone. Saved {len(saved)} plot(s) to: {cfg.OUTPUT_DIR.resolve()}")
    if saved:
        print("Example output:")
        for p in saved[:5]:
            print(" -", p)

    #SAVE df_tidy
    df_tidy.to_csv(cfg.OUTPUT_DIR / "df_tidy.csv", index=False, encoding="utf-8-sig")

if __name__ == "__main__":
 main()




