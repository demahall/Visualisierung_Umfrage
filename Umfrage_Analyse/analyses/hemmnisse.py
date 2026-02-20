
# ------------------------------------------------------------
# Pure analysis module (no IO)
#
# Output schema aligned to other summaries:
# question_text | item | company_size_class | metric | value | n_valid | n_total | pct_valid
# ------------------------------------------------------------

from __future__ import annotations
import pandas as pd
import hypothesen_CONST as const
from Umfrage_Analyse.finalize_output import finalize_metric_output

COL_ID = const.COL_ID
Q31 = const.Q31
Q33 = const.Q33
LIKERT_MAP = const.LIKERT_HEMMNIS_MAPPING  # maps 1..5, missing for "Keine Antwort"


def compute_likert_mean_summary(
    df_tidy: pd.DataFrame,
    df_size_class: pd.DataFrame,
    *,
    question_texts: list[str],
    answer_to_value_map: dict[str, int],
) -> pd.DataFrame:
    """
    Computes mean Likert score per item and company size (GU/KMU),
    excluding "Keine Antwort" (mapped to NaN).

    Denominators:
    - n_total: total respondents per company_size_class (from df_size_class)
    - n_valid: valid answers per (question_text,item,company_size_class)
    - pct_valid: n_valid / n_total
    """


    # 1) filter exact questions
    df_q = df_tidy.loc[
        df_tidy["question_text"].isin(question_texts),
        [COL_ID, "question_text", "item", "answer"]
    ].copy()

    # 2) merge size class
    df_q = (
        df_q.merge(df_size_class, on=COL_ID, how="left")
        .dropna(subset=["company_size_class"])
    )

    # 3) map to numeric (unmapped -> NaN => excludes "Keine Antwort")
    df_q["ordinal_value"] = df_q["answer"].map(answer_to_value_map)
    df_valid = df_q.dropna(subset=["ordinal_value"]).copy()

    # 4) totals per class (constant)
    totals = (
        df_size_class.groupby("company_size_class")[COL_ID]
        .nunique()
        .rename("n_total")
        .reset_index()
    )

    # 5) mean per question+item+class
    out = (
        df_valid.groupby(["question_text", "item", "company_size_class"], as_index=False)
        .agg(
            value=("ordinal_value", "mean"),
            n_valid=("ordinal_value", "count"),
        )
    )

    out = out.merge(totals, on="company_size_class", how="left")
    out["pct_valid"] = (out["n_valid"] / out["n_total"]) * 100.0


    out = out[
        ["question_text", "item", "company_size_class", "value", "n_valid", "n_total", "pct_valid"]
    ].copy()

    return out


def wrapper_all_likert_data_frame(
        df_tidy: pd.DataFrame,
        df_size_class: pd.DataFrame,
) -> pd.DataFrame:

    # Hemmnisse mapping (already in const)
    hemmnisse_map = const.LIKERT_HEMMNIS_MAPPING
    daten_erfassung_map = const.LIKERT_Q16_MAPPING

    df_hemmnisse = compute_likert_mean_summary(
        df_tidy=df_tidy,
        df_size_class=df_size_class,
        question_texts=[const.Q31, const.Q33],
        answer_to_value_map=hemmnisse_map,
    )

    df_data_capture = compute_likert_mean_summary(
        df_tidy=df_tidy,
        df_size_class=df_size_class,
        question_texts=[const.Q16],
        answer_to_value_map=daten_erfassung_map,
    )

    return pd.concat([df_hemmnisse, df_data_capture], ignore_index=True)

