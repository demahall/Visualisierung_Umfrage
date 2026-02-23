
# Output
# item | company_size_class | answer | n | total | pct | analysis_key
#
# "total" = n_valid per (item, company_size_class), excludes "Keine Antwort"
# ------------------------------------------------------------

from __future__ import annotations
import pandas as pd
import QUESTION_LIST as const
from Umfrage_JG_Analyse.preprocessing_jg_analyse.finalize_output import finalize_matrix_output

COL_ID = const.COL_ID
Q20 = const.Q20
VALID_ANSWERS_YN = const.VALID_ANSWERS_YN


def compute_zustimmung_summary(
    df_tidy: pd.DataFrame,
    gu_kmu: pd.DataFrame,

) -> pd.DataFrame:


    df_q = df_tidy.loc[df_tidy["question_text"] == Q20, [COL_ID, "item", "answer"]].copy()

    # 2) Merge GU/KMU
    df_q = (
        df_q.merge(gu_kmu, on=COL_ID, how="left")
            .dropna(subset=["company_size_class"])
    )

    # 3) Keep valid answers only (drops "Keine Antwort")
    df_q = df_q[df_q["answer"].isin(VALID_ANSWERS_YN)].copy()

    # 4) Denominator per item+class (valid respondents)
    denom = (
        df_q.groupby(["item", "company_size_class"])[COL_ID]
            .nunique()
            .rename("total")
            .reset_index()
    )

    # 5) Counts per answer
    counts = (
        df_q.groupby(["item", "company_size_class", "answer"])[COL_ID]
            .nunique()
            .rename("n")
            .reset_index()
    )

    out = counts.copy()

    # 7) Ensure full grid (fill missing with 0)
    all_items = df_q["item"].dropna().unique()
    all_classes = gu_kmu["company_size_class"].dropna().unique()

    full_idx = pd.MultiIndex.from_product(
        [all_items, all_classes, VALID_ANSWERS_YN],
        names=["item", "company_size_class", "answer"]
    )

    out = (
        out.set_index(["item", "company_size_class", "answer"])
           .reindex(full_idx)
           .reset_index()
    )

    out = out.merge(denom, on=["item","company_size_class"], how = "left")

    out["n"] = out["n"].fillna(0).astype(int)
    out["total"] = out["total"].fillna(0).astype(int)
    out["pct"] = out.apply(lambda r: (r["n"] / r["total"] * 100.0) if r["total"] > 0 else 0.0, axis=1)

    out = finalize_matrix_output(
        out,
        analysis_key="zustimmung",
        question_text=Q20,
        target_question=Q20,
    )

    return out
