
# Output schema aligned with einsatz_technologie summary:
# item | company_size_class | answer | n | total | pct
#
# NOTE:
# - "total" here means n_valid for (item, company_size_class),
#   i.e., denominator excludes "keine Antwort".
# ------------------------------------------------------------

from __future__ import annotations
import pandas as pd
import hypothesen_CONST as const
from typing import List,Dict

from Umfrage_Analyse.finalize_output import finalize_matrix_output

COL_ID = const.COL_ID

#question_text
Q16 = const.Q16
VALID_ANSWER_Q16 = const.VALID_ANSWER_Q16

def _get_question_from_catalog(catalog: List[Dict], question_text: str) -> Dict:
    q = next((x for x in catalog if x.get("question_text") == question_text), None)
    if not q:
        raise ValueError(f"Question not found in catalog: {question_text}")
    return q

def compute_data_capture_summary(
    df_tidy: pd.DataFrame,
    catalog: List[Dict],
    df_size_class: pd.DataFrame,
) -> pd.DataFrame:
    """
    For each item, compute distribution of answer categories within GU/KMU.
    Denominator excludes "keine Antwort" -> total == n_valid.
    """

    # 1) Filter question
    df_data = df_tidy.loc[df_tidy["question_text"] == Q16,[COL_ID, "item", "answer"]].copy()
    q_cat = _get_question_from_catalog(catalog, Q16)

    # 2) Merge GU/KMU
    df_data = df_data.merge(df_size_class, on=COL_ID, how="left").dropna(subset=["company_size_class"])


    # 3) Keep only valid answers (implicitly drops "keine Antwort")
    df_data = df_data[df_data["answer"].isin(VALID_ANSWER_Q16)].copy()

    # 4) Denominator per (item, class) = valid respondents who answered something
    denom = (
        df_data.groupby(["item", "company_size_class"])[COL_ID]
               .nunique()
               .rename("total")
               .reset_index()
    )

    # 5) Counts per answer
    counts = (
        df_data.groupby(["item", "company_size_class", "answer"])[COL_ID]
               .nunique()
               .rename("n")
               .reset_index()
    )

    out = counts.copy()

    # 7) Ensure full grid (fill missing answers with 0)
    all_items = df_data["item"].dropna().unique()
    all_classes = df_size_class["company_size_class"].dropna().unique()

    full_idx = pd.MultiIndex.from_product(
        [all_items, all_classes, VALID_ANSWER_Q16],
        names=["item", "company_size_class", "answer"]
    )

    out = (
        out.set_index(["item", "company_size_class", "answer"])
           .reindex(full_idx)
           .reset_index()
    )

    # 6) pct
    out = counts.merge(denom, on=["item", "company_size_class"], how="left")

    out["n"] = out["n"].fillna(0).astype(int)
    out["total"] = out["total"].fillna(0).astype(int)
    out["pct"] = out.apply(lambda r: (r["n"] / r["total"] * 100.0) if r["total"] > 0 else 0.0, axis=1)

    out = out[["item", "company_size_class", "answer", "n", "total", "pct"]].copy()
    out["analysis_key"] = "data_capture_matrix"

    out = finalize_matrix_output(
        out,
        analysis_key="daten_erfassung",
        question_text=Q16,
        target_question=Q16,
    )
    return out
