# main.py
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
4) Loops through all questions and saves plots to the output folder

How to run:
- Set EXCEL_PATH and FIRST_QUESTION_TEXT below
- Run: python main.py
"""

# main.py
from __future__ import annotations

from pathlib import Path
import pandas as pd
from preprocessing import prepare_data
from src.plotting.plotting_config import apply_style, OUTPUT_DIR
from typing import List
from logger import TinyLogger
from plotting_function import plot_question_and_save,plot_hypotheses_and_save
import hypothesen_CONST as hyp_const


# -----------------------------
# USER SETTINGS
# -----------------------------
EXCEL_PATH = Path("new_result_survey.xlsx")
FIRST_QUESTION_TEXT = "Welcher Art von Organisation gehören Sie an?"
SPEC_PATH = Path("question_spec.json")

# Filter what to plot
PLOT_ONLY_TYPES = None
# Example:
# PLOT_ONLY_TYPES = {"single", "likert", "checkbox", "matrix"}  # skip text

EXCLUDE_QUESTIONS_CONTAINS = [
    # e.g. "E-Mail", "Name", "Telefon"
]
INCLUDE_ONLY_QUESTIONS_CONTAINS = None

PREFIX_WITH_INDEX = True


def should_skip_question(qtext: str) -> bool:
    if INCLUDE_ONLY_QUESTIONS_CONTAINS:
        if not any(s.lower() in qtext.lower() for s in INCLUDE_ONLY_QUESTIONS_CONTAINS):
            return True
    if EXCLUDE_QUESTIONS_CONTAINS:
        if any(s.lower() in qtext.lower() for s in EXCLUDE_QUESTIONS_CONTAINS):
            return True
    return False


def main() -> None:
    if not EXCEL_PATH.exists():
        raise FileNotFoundError(f"Excel file not found: {EXCEL_PATH.resolve()}")
    if not SPEC_PATH.exists():
        raise FileNotFoundError(f"Spec file not found: {SPEC_PATH.resolve()}")

    apply_style()

    df_raw, df_q, catalog, df_tidy, base_map = prepare_data(
        excel_path=EXCEL_PATH,
        first_question_text=FIRST_QUESTION_TEXT,
        sheet_name=0,
        spec_path=SPEC_PATH,
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # logger
    logger = TinyLogger(OUTPUT_DIR / "run_log.txt")
    logger.write(f"Excel: {EXCEL_PATH.resolve()}")
    logger.write(f"Spec:  {SPEC_PATH.resolve()}")
    logger.write(f"Output:{OUTPUT_DIR.resolve()}")
    logger.write(f"Catalog entries: {len(catalog)}")
    logger.write("")

    # debug exports (optional)
    try:
        df_tidy.to_csv(OUTPUT_DIR / "df_tidy.csv", index=False, encoding="utf-8-sig")
        pd.DataFrame(catalog).to_json(
            OUTPUT_DIR / "catalog.json", orient="records", force_ascii=False, indent=2
        )
    except Exception:
        logger.write("[WARN] Could not export df_tidy/catalog debug files.")

    saved: List[Any] = []
    list_of_figures: List[str] = []

    plot_i = 0

    ok_count = 0
    skip_count = 0
    fail_count = 0

    # -------------------------
    # 1) NORMAL QUESTION PLOTS
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

        if PLOT_ONLY_TYPES is not None and qtype not in PLOT_ONLY_TYPES:
            logger.write(f"[SKIP type]   | type={qtype} | plot={ptype} | {qtext}")
            skip_count += 1
            continue

        # If you want to force-skip text here too (even if plot_question_and_save already does it):
        if qtype == "text":
            # keep figure numbering consistent (your FYI: 20, 28, 31, 33)
            plot_i += 1
            caption_text = (q.get("caption") or qtext).strip()
            logger.write(f"[SKIP text]   | Abbildung {plot_i} | {qtext}")
            list_of_figures.append(f"Abbildung {plot_i}: {caption_text}" if PREFIX_WITH_INDEX else f"Abbildung: {caption_text}")
            skip_count += 1
            continue

        # increment Abbildung index (you do this regardless of success, consistent numbering)
        plot_i += 1
        caption_text = (q.get("caption") or qtext).strip()

        try:
            out_paths = plot_question_and_save(
                q=q,
                df_tidy=df_tidy,
                base_map=base_map,
                out_dir=OUTPUT_DIR,
                prefix_index=plot_i if PREFIX_WITH_INDEX else None,
            )

            # If plot_question_and_save returns [] (e.g., internal skip), treat as skip
            if not out_paths:
                logger.write(f"[SKIP none]   | Abbildung {plot_i} | type={qtype} | plot={ptype} | {qtext}")
                list_of_figures.append(f"Abbildung {plot_i}: {caption_text}" if PREFIX_WITH_INDEX else f"Abbildung: {caption_text}")
                skip_count += 1
                continue

            saved.extend(out_paths)
            ok_count += 1

            if PREFIX_WITH_INDEX:
                list_of_figures.append(f"Abbildung {plot_i}: {caption_text}")
                logger.write(f"[OK]          | Abbildung {plot_i} | type={qtype} | plot={ptype} | saved={len(out_paths)} | {out_paths[0].name}")
            else:
                list_of_figures.append(f"Abbildung: {caption_text}")
                logger.write(f"[OK]          | type={qtype} | plot={ptype} | saved={len(out_paths)} | {out_paths[0].name}")

        except Exception as e:
            fail_count += 1
            logger.write(f"[FAIL]        | Abbildung {plot_i} | type={qtype} | plot={ptype} | {qtext}")
            logger.write(f"               error={repr(e)}")
            logger.write("               traceback:")
            logger.write_traceback()

    # -------------------------
    # 2) HYPOTHESES (RUN ONCE!)
    # -------------------------
    logger.write("")
    logger.write("=== PLOTTING HYPOTHESES ===")
    try:
        hyp_paths, hyp_caps = plot_hypotheses_and_save(
            df_tidy=df_tidy,
            out_dir=OUTPUT_DIR,
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

        # if your hypotheses function already returns captions like "Abbildung X: ...",
        # keep it. If it returns raw captions, you already handle it there.
        if PREFIX_WITH_INDEX:
            plot_i += len(hyp_paths)

        logger.write(f"[OK] Hypotheses plots saved={len(hyp_paths)}")
    except Exception as e:
        logger.write(f"[FAIL] Hypotheses | error={repr(e)}")
        logger.write("traceback:")
        logger.write_traceback()

    # -------------------------
    # 3) WRITE LIST OF FIGURES
    # -------------------------
    if list_of_figures:
        (OUTPUT_DIR / "list_of_figures.txt").write_text(
            "\n".join(list_of_figures), encoding="utf-8"
        )
        logger.write(f"[OK] Wrote list_of_figures.txt ({len(list_of_figures)} lines)")
    else:
        logger.write("[WARN] list_of_figures is empty (nothing written)")

    # Summary
    logger.write("")
    logger.write("=== SUMMARY ===")
    logger.write(f"Questions OK:      {ok_count}")
    logger.write(f"Questions skipped: {skip_count}")
    logger.write(f"Questions failed:  {fail_count}")
    logger.write(f"Saved plot files:  {len(saved)}")
    logger.write(f"Output folder:     {OUTPUT_DIR.resolve()}")

    logger.close()

    print(f"\nDone. Saved {len(saved)} plot(s) to: {OUTPUT_DIR.resolve()}")
    if saved:
        print("Example output:")
        for p in saved[:5]:
            print(" -", p)




if __name__ == "__main__":
    main()
