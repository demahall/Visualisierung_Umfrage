# gu_kmu_classification.py
# ------------------------------------------------------------
# Goal:
# - classify each respondent_id as GU or KMU based on:
#   GU if:
#     employees > 250
#     AND turnover in {"50-250 Mio.Euro", "> 250 Mio.Euro"}  (exact strings configurable)
#   else -> KMU
#
# Input:
# - df_tidy (pandas DataFrame) must exist in your environment
#   and contain respondent_id + the two columns below.
# Output:
# - gu_ids: list of respondent_id classified as GU
# - kmu_ids: list of respondent_id classified as KMU
# - df_size_class: mapping table respondent_id -> company_size_class
# ------------------------------------------------------------

import pandas as pd
import numpy as np
from preprocessing import prepare_data
from pathlib import Path

EXCEL_PATH = Path("result-survey.xlsx")
FIRST_QUESTION_TEXT = "Welcher Art von Organisation gehören Sie an?"
SPEC_PATH = Path("question_spec.json")



# --- CONFIG: adjust to your exact column names in df_tidy ---
COL_ID = "respondent_id"
COL_EMPLOYEES = "Wie viele Beschäftigte hat Ihr Unternehmen?"   # <-- adjust if needed
COL_TURNOVER = "Wie hoch ist der jährliche Umsatz Ihres Unternehmens?"             # <-- adjust if needed

# Turnover categories that count as ">= 50 Mio" (GU condition)
GU_TURNOVER_SET = {
    "< 5 Mio. EUR",
      "5 - 50 Mio. EUR",
      "50 - 250 Mio. EUR",
      "> 250 Mio. EUR"
}

# --- Industry 4.0 question (use contains for robustness) ---
Q_I40_PATTERN = r"Welche der nachfolgenden Industrie 4\.0\s*-\s*Technologien"

VALID_ANSWERS = ["Im Einsatz", "In Planung"]


_, _, _, df_tidy, base_map = prepare_data(
        excel_path=EXCEL_PATH,
        first_question_text=FIRST_QUESTION_TEXT,
        sheet_name=0,
        spec_path=SPEC_PATH,
    )

# ------------------------------------------------------------
# 1) Build respondent -> GU/KMU mapping (df_size_class)
# ------------------------------------------------------------

def build_company_size_mapping(df_tidy: pd.DataFrame) -> pd.DataFrame:
    df_size = df_tidy[df_tidy["question_text"].isin([COL_EMPLOYEES, COL_TURNOVER])][
        [COL_ID, "question_text", "answer"]
    ].copy()

    # Pivot -> one row per respondent_id
    wide = (
        df_size.pivot(index=COL_ID, columns="question_text", values="answer")
              .reset_index()
    )

    # GU logic: employees > 250 AND turnover in 50-250 or >250
    def is_gu(row):
        emp = str(row.get(COL_EMPLOYEES, "")).strip()
        turn = str(row.get(COL_TURNOVER, "")).strip()

        cond_emp = emp.replace(" ", "") == ">250"  # your data shows "> 250"
        cond_turn = turn in GU_TURNOVER_SET
        return cond_emp and cond_turn

    wide["company_size_class"] = np.where(wide.apply(is_gu, axis=1), "GU", "KMU")

    # This is the mapping table we need later:
    df_size_class = wide[[COL_ID, "company_size_class"]].copy()
    return df_size_class


df_size_class = build_company_size_mapping(df_tidy)

# Lists (if you need them)
gu_ids  = df_size_class.loc[df_size_class["company_size_class"] == "GU", COL_ID].tolist()
kmu_ids = df_size_class.loc[df_size_class["company_size_class"] == "KMU", COL_ID].tolist()

print("GU count:", len(gu_ids))
print("KMU count:", len(kmu_ids))


# ------------------------------------------------------------
# 2) Industry 4.0 analysis by GU/KMU
# ------------------------------------------------------------

# Filter to the I4.0 question
df_i40 = df_tidy[
    df_tidy["question_text"].astype(str).str.contains(Q_I40_PATTERN, regex=True, na=False)
][[COL_ID, "item", "answer"]].copy()

# Merge GU/KMU class onto the I4.0 answers
df_i40 = df_i40.merge(df_size_class, on=COL_ID, how="left")

# Keep only respondents with a class
df_i40 = df_i40.dropna(subset=["company_size_class"])

# Denominators: total respondents per class (like your "10 GU participants")
totals = (
    df_size_class.groupby("company_size_class")[COL_ID]
                 .nunique()
                 .rename("total")
                 .reset_index()
)

# Count unique respondents per item + class + answer
df_counts = (
    df_i40[df_i40["answer"].isin(VALID_ANSWERS)]
    .groupby(["item", "company_size_class", "answer"])[COL_ID]
    .nunique()
    .rename("n")
    .reset_index()
)

# Add totals and compute %
df_summary = df_counts.merge(totals, on="company_size_class", how="left")
df_summary["pct"] = (df_summary["n"] / df_summary["total"]) * 100

# Ensure both answers exist for each item+class (fill missing with 0)
all_items = df_i40["item"].dropna().unique()
all_classes = df_size_class["company_size_class"].dropna().unique()

full_idx = pd.MultiIndex.from_product(
    [all_items, all_classes, VALID_ANSWERS],
    namses=s["item", "company_size_class", "answer"]
)

df_summary = (
    df_summary.set_index(["item", "company_size_class", "answer"])
              .reindex(full_idx)
              .reset_index()
)

df_summary = df_summary.merge(totals, on="company_size_class", how="left", suffixes=("", "_tmp"))
df_summary["n"] = df_summary["n"].fillna(0).astype(int)
df_summary["pct"] = (df_summary["n"] / df_summary["total"]) * 100

df_summary = df_summary[["item", "company_size_class", "answer", "n", "total", "pct"]]

print(df_summary.head(30))
