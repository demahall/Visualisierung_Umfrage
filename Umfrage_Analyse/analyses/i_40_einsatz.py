from __future__ import annotations
import pandas as pd
from typing import List, Dict

import hypothesen_CONST as const
from Umfrage_Analyse.finalize_output import finalize_matrix_output
from hypothesen_CONST import VALID_ANSWERS_Q17

COL_ID = const.COL_ID
Q17 = const.Q17


def _get_question_from_catalog(catalog: List[Dict], question_text: str) -> Dict:
    q = next((x for x in catalog if x.get("question_text") == question_text), None)
    if not q:
        raise ValueError(f"Question not found in catalog: {question_text}")
    return q


def compute_i40_einsatz_planung_summary(
    df_tidy: pd.DataFrame,
    df_size_class: pd.DataFrame
) -> pd.DataFrame:
    """
    For each I4.0 item, compute counts & % of respondents in GU/KMU who chose each answer option.
    Denominator = total respondents per company_size_class (GU/KMU), as you described.
    """

    df_i40 = df_tidy.loc[df_tidy["question_text"] == Q17, [COL_ID, "item", "answer"]].copy()

    # merge class
    df_i40 = df_i40.merge(df_size_class, on=COL_ID, how="left").dropna(subset=["company_size_class"])

    # denominator: total respondents per group (from mapping, not from df_i40)
    totals = (
        df_size_class.groupby("company_size_class")[COL_ID]
                     .nunique()
                     .rename("total")
                     .reset_index()
    )

    # counts (unique respondents)
    df_counts = (
        df_i40[df_i40["answer"].isin(VALID_ANSWERS_Q17)]
        .groupby(["item", "company_size_class", "answer"])[COL_ID]
        .nunique()
        .rename("n")
        .reset_index()
    )

    # add totals & pct
    out = df_counts.merge(totals, on="company_size_class", how="left")
    out["pct"] = (out["n"] / out["total"]) * 100.0

    # complete grid (fill missing with 0)
    all_items = df_i40["item"].dropna().unique()
    all_classes = df_size_class["company_size_class"].dropna().unique()

    full_idx = pd.MultiIndex.from_product(
        [all_items, all_classes, VALID_ANSWERS_Q17],
        names=["item", "company_size_class", "answer"]
    )

    out = (
        out.set_index(["item", "company_size_class", "answer"])
           .reindex(full_idx)
           .reset_index()
           .merge(totals, on="company_size_class", how="left", suffixes=("", "_tmp"))
    )

    out["n"] = out["n"].fillna(0).astype(int)
    out["pct"] = (out["n"] / out["total"]) * 100.0

    out = finalize_matrix_output(
        out,
        analysis_key="i40_einsatz",
        question_text=Q17,
        target_question=Q17,
        denom_type="total",
    )

    return out

