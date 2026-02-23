import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import QUESTION_LIST as hyp_const
import textwrap
from typing import Dict


#-----------------
#Preprocessing Helper
#-----------------




def _add_material_cost_group(df: pd.DataFrame) -> pd.DataFrame:

    df = df.copy()

    def grp(x: str) -> str:
        if x in hyp_const.HIGH_COST_INDUSTRIES:
            return "Hohe Materialkosten"
        if x in hyp_const.LOW_COST_INDUSTRIES:
            return "Geringe Materialkosten"
        return "Sonstige/unklar"
    df["cost_group"] = df["initial_question_label"].astype(str).map(grp)

    def prefix(row) -> str:
        if row["cost_group"] == "Hohe Materialkosten":
            return "▲ "
        if row["cost_group"] == "Geringe Materialkosten":
            return "▼ "
        return "• "
    df["label_marked"] = df.apply(lambda r: prefix(r) + str(r["initial_question_label"]), axis=1)
    return df

# For H1,H2,H3
def compute_verknuepfung_hypotheses(df_tidy: pd.DataFrame,initial_question:str,target_question:str) -> pd.DataFrame:

    """
    For single-select grouping question:
    returns df with columns: group, yes_n, no_n, base_n, yes_pct, no_pct
    """
    df = df_tidy.copy()
    group_initial = df[df["question_text"] == initial_question][["respondent_id", "answer"]].rename(columns={"answer": "initial_question_label"})
    group_target = df[df["question_text"] == target_question][["respondent_id", "answer"]].rename(columns={"answer": "target_question"})

    m = group_initial.merge(group_target, on="respondent_id", how="inner")
    m["target_question"] = m["target_question"].astype(str)

    m["is_yes"] = m["target_question"].str.strip().str.lower().eq("ja")
    m["is_no"]  = m["target_question"].str.strip().str.lower().eq("nein")

    agg = (
        m.groupby("initial_question_label", dropna=False)
        .agg(
            yes_n=("is_yes", "sum"),
            no_n=("is_no", "sum"),
            base_n=("target_question", "count"),
        )
        .reset_index()
        .rename(columns={"group": "label"})
    )

    agg["yes_pct"] = np.where(agg["base_n"] > 0, agg["yes_n"] / agg["base_n"] * 100, 0.0)
    agg["no_pct"]  = np.where(agg["base_n"] > 0, agg["no_n"]  / agg["base_n"] * 100, 0.0)

    out = agg
    return out

def compute_verknuepfung_h2_hypotheses(df_tidy: pd.DataFrame,initial_question:str,target_question:str,)-> pd.DataFrame:
    out2 = compute_verknuepfung_hypotheses(df_tidy=df_tidy,initial_question=initial_question,target_question=target_question)
    out2_final = _add_material_cost_group(out2)
    return out2_final


def compute_strong_counts_hypotheses(
    df_tidy: pd.DataFrame,
    target_question: str,
    strong_set: set[str],
) -> pd.Series:

    d = df_tidy[df_tidy["question_text"] == target_question].copy()

    d = d[d["answer"].notna()]
    d = d[d["answer"].isin(strong_set)]

    # count per item (dimension)

    counts = d.groupby("item")["respondent_id"].nunique().sort_values(ascending=False)
    return counts


def get_df_hypotheses(df_tidy:pd.DataFrame, hypotheses_config:dict) -> dict:
    results = {}

    for job in hypotheses_config:
        func = job["func"]
        params = job["params"]

        result_df = func(
            df_tidy=df_tidy,
            initial_question=params["initial_question"],
            target_question=params["target_question"]
        )

        results[job["key"]] = result_df

    return results




