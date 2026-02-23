
from __future__ import annotations

import pandas as pd

import QUESTION_LIST as const
from Umfrage_JG_Analyse.preprocessing_jg_analyse.finalize_output import finalize_crosstab_output

# ---- CONFIG (set exact texts to match your df_tidy) ----
COL_ID = const.COL_ID
Q10 = const.Q10
Q20 = const.Q20
ITEM_Q20_1 = const.ITEM_Q20_1
VALID_YN = ["Ja", "Nein"]


def compute_stueckzahl_kennzahlen_summary(df_tidy: pd.DataFrame) -> pd.DataFrame:
    # segment
    df_seg = df_tidy.loc[
        df_tidy["question_text"] == Q10,
        [COL_ID, "answer"]
    ].rename(columns={"answer": "segment"}).copy()

    # target item
    df_tar = df_tidy.loc[
        (df_tidy["question_text"] == Q20) & (df_tidy["item"] == ITEM_Q20_1),
        [COL_ID, "answer"]
    ].rename(columns={"answer": "answer"}).copy()

    # link
    df_link = df_seg.merge(df_tar, on=COL_ID, how="inner")
    df_link = df_link[df_link["answer"].isin(VALID_YN)].copy()

    # denom per segment
    denom = (
        df_link.groupby("segment")[COL_ID]
              .nunique()
              .rename("total")
              .reset_index()
    )

    # counts
    counts = (
        df_link.groupby(["segment", "answer"])[COL_ID]
              .nunique()
              .rename("n")
              .reset_index()
    )

    out = counts.copy()

    # ensure full grid (fill missing)
    all_segments = df_link["segment"].dropna().unique()
    full_idx = pd.MultiIndex.from_product(
        [all_segments, VALID_YN],
        names=["segment", "answer"]
    )

    out = (
        out.set_index(["segment", "answer"])
           .reindex(full_idx)
           .reset_index()
    )

    out = counts.merge(denom, on="segment", how="left")

    out["n"] = out["n"].fillna(0).astype(int)
    out["total"] = out["total"].fillna(0).astype(int)
    out["pct"] = out.apply(lambda r: (r["n"] / r["total"] * 100.0) if r["total"] > 0 else 0.0, axis=1)

    out = finalize_crosstab_output(
        out,
        analysis_key="stueckzahl_kennzahlstruktur",
        segment_question=Q10,
        target_question=Q20,
        target_item=ITEM_Q20_1,
    )
    return out