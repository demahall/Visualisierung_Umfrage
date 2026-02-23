# ------------------------------------------------------------
# Cross-tab:
# Segment = "KW ist Teil der Unternehmensstrategie" (Ja/Nein)
# Targets = two KPI-related items (Ja/Nein) from KPI matrix question:
#   1) Kennzahlenstruktur (Kaskade)...
#   2) Für zirkuläre Prozesse ... vergleichbare Kennzahlensysteme
#
# Output schema:
# segment | answer | n | total | pct | analysis_key | target_item
# ------------------------------------------------------------

from __future__ import annotations
import pandas as pd
import QUESTION_LIST as const
from Umfrage_JG_Analyse.preprocessing_jg_analyse.finalize_output import finalize_crosstab_output
from QUESTION_LIST import VALID_ANSWERS_YN

COL_ID = const.COL_ID
VALID_ANSWERS_YN = const.VALID_ANSWERS_YN

# --- Segment question + item ---

Q13 = const.Q13
ITEM_Q13 = "Kreislaufwirtschaft ist Teil der Unternehmensstrategie."

# --- Matrix question with KPI items ---
Q20 = const.Q20

ITEM_Q20_1 = const.ITEM_Q20_1
ITEM_Q20_2 = const.ITEM_Q20_2

ITEM_KASKADE = "In unserem Unternehmen ist die Kennzahlenstruktur (Kaskade) für lineare Produktionsprozesse klar definiert und mit den strategischen Zielen verknüpft."
ITEM_CIRC_KPIS = "Für zirkuläre Prozesse (z.B. Rückführung, Aufbereitung, Remanufacturing) existieren vergleichbare Kennzahlensysteme."


def _crosstab_segment_to_target(
    df_tidy: pd.DataFrame,
    segment_q: str,
    segment_item: str,
    target_q: str,
    target_item: str,
) -> pd.DataFrame:

    # segment = strategy yes/no
    df_seg = df_tidy.loc[
        (df_tidy["question_text"] == segment_q) & (df_tidy["item"] == segment_item),
        [COL_ID, "answer"]
    ].rename(columns={"answer": "segment"}).copy()

    # target = KPI yes/no for specific item
    df_tar = df_tidy.loc[
        (df_tidy["question_text"] == target_q) & (df_tidy["item"] == target_item),
        [COL_ID, "answer"]
    ].rename(columns={"answer": "answer"}).copy()

    # link (only respondents who answered both)
    df_link = df_seg.merge(df_tar, on=COL_ID, how="inner")

    # exclude "Keine Antwort" on both sides
    df_link = df_link[df_link["segment"].isin(VALID_ANSWERS_YN) & df_link["answer"].isin(VALID_ANSWERS_YN)].copy()

    # denominator per segment (valid answers only)
    denom = (
        df_link.groupby("segment")[COL_ID]
              .nunique()
              .rename("total")
              .reset_index()
    )

    # counts per segment x answer
    counts = (
        df_link.groupby(["segment", "answer"])[COL_ID]
              .nunique()
              .rename("n")
              .reset_index()
    )

    out = counts.copy()


    # complete grid
    all_segments = df_link["segment"].dropna().unique()
    full_idx = pd.MultiIndex.from_product([all_segments, VALID_ANSWERS_YN], names=["segment", "answer"])

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


def compute_us_mit_ks_und_zp_summary(df_tidy: pd.DataFrame) -> pd.DataFrame:
    out1 = _crosstab_segment_to_target(
        df_tidy=df_tidy,
        segment_q=Q13,
        segment_item=ITEM_Q13,
        target_q=Q20,
        target_item=ITEM_Q20_1
    )

    out2 = _crosstab_segment_to_target(
        df_tidy=df_tidy,
        segment_q=Q13,
        segment_item=ITEM_Q13,
        target_q=Q20,
        target_item=ITEM_Q20_2
    )

    out1 = finalize_crosstab_output(
        out1,
        analysis_key="us_mit_ks",
        segment_question=Q13,
        target_question=Q20,
        target_item=ITEM_Q20_1,
    )

    out2 = finalize_crosstab_output(
        out2,
        analysis_key="us_mit_zp",
        segment_question=Q13,
        target_question=Q20,
        target_item=ITEM_Q20_2,
    )

    out_final = pd.concat([out1, out2], ignore_index=True)

    return out_final
