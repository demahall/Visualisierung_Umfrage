
# Output:
# segment | answer | n | total | pct |
# ------------------------------------------------------------

from __future__ import annotations
import pandas as pd
import hypothesen_CONST as const
from Umfrage_Analyse.finalize_output import finalize_crosstab_output

COL_ID = const.COL_ID

#Segment question
Q11 = const.Q11

#target question
Q20 = const.Q20

ITEM_Q20_1 = const.ITEM_Q20_1
ITEM_Q20_2 = const.ITEM_Q20_2

VALID_YN = ["Ja", "Nein"]


def _crosstab_segment_to_item(df_tidy: pd.DataFrame, segment_q: str, matrix_q: str, target_item: str) -> pd.DataFrame:
    df_seg = df_tidy.loc[
        df_tidy["question_text"] == segment_q,
        [COL_ID, "answer"]
    ].rename(columns={"answer": "segment"}).copy()

    df_tar = df_tidy.loc[
        (df_tidy["question_text"] == matrix_q) & (df_tidy["item"] == target_item),
        [COL_ID, "answer"]
    ].rename(columns={"answer": "answer"}).copy()

    df_link = df_seg.merge(df_tar, on=COL_ID, how="inner")
    df_link = df_link[df_link["answer"].isin(VALID_YN)].copy()

    denom = (
        df_link.groupby("segment")[COL_ID]
              .nunique()
              .rename("total")
              .reset_index()
    )

    counts = (
        df_link.groupby(["segment", "answer"])[COL_ID]
              .nunique()
              .rename("n")
              .reset_index()
    )

    out = counts.copy()


    all_segments = df_link["segment"].dropna().unique()
    full_idx = pd.MultiIndex.from_product([all_segments, VALID_YN], names=["segment", "answer"])

    out = (
        out.set_index(["segment", "answer"])
           .reindex(full_idx)
           .reset_index()
    )

    out = counts.merge(denom, on="segment", how="left")

    out["n"] = out["n"].fillna(0).astype(int)
    out["total"] = out["total"].fillna(0).astype(int)
    out["pct"] = out.apply(lambda r: (r["n"] / r["total"] * 100.0) if r["total"] > 0 else 0.0, axis=1)

    return out[["segment", "answer", "n", "total", "pct"]].copy()


def compute_kw_mit_kz_und_zp_summary(df_tidy: pd.DataFrame) -> pd.DataFrame:
    out1 = _crosstab_segment_to_item(
        df_tidy=df_tidy,
        segment_q=Q11,
        matrix_q=Q20,
        target_item=ITEM_Q20_1,
    )

    out2 = _crosstab_segment_to_item(
        df_tidy=df_tidy,
        segment_q=Q11,
        matrix_q=Q20,
        target_item=ITEM_Q20_2,
    )

    out1 = finalize_crosstab_output(
        out1,
        analysis_key="kw_mit_ks",
        segment_question=Q11,
        target_question=Q20,
        target_item=ITEM_Q20_1,
    )
    out2 = finalize_crosstab_output(
        out2,
        analysis_key="kw_mit_zp",
        segment_question=Q11,
        target_question=Q20,
        target_item=ITEM_Q20_2,
    )

    out_final = pd.concat([out1, out2])

    return out_final
