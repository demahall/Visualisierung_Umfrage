
import pandas as pd
import numpy as np
from gu_kmu_classification import df_size_wide, df_size_class

# ------------------------------------------------------------
# INPUTS (expected in your environment):
# - df_tidy: long table with columns
#   ['respondent_id','question_text','item','answer','other_text']
# - df_size_wide (or df_size_class): mapping respondent_id -> company_size_class ("GU"/"KMU")
#   from the previous task
#
# OUTPUT:
# - df_summary: tidy summary with counts + percentages
#   columns: item, company_size_class, answer, n, total, pct
# ------------------------------------------------------------

COL_ID = "respondent_id"

# 1) Define the question (use contains to be robust against tiny text differences)
Q_PATTERN = r"Welche der nachfolgenden Industrie 4\.0\s*-\s*Technologien"

# Only the two answer categories we care about
VALID_ANSWERS = ["Im Einsatz", "In Planung"]

# ------------------------------------------------------------
# A) Build / get respondent -> GU/KMU mapping
# ------------------------------------------------------------
# If you already have df_size_wide from previous script:
# it should contain columns: respondent_id, company_size_class
# If your mapping table is named differently, just adapt here.

# Example expectation:
# df_size_wide["company_size_class"] in {"GU","KMU"}

if "df_size_wide" in globals():
    df_map = df_size_wide[[COL_ID, "company_size_class"]].copy()
elif "df_size_class" in globals():
    df_map = df_size_class[[COL_ID, "company_size_class"]].copy()
else:
    raise ValueError("Need df_size_wide or df_size_class mapping with respondent_id -> company_size_class.")

# ------------------------------------------------------------
# B) Filter df_tidy to the Industry 4.0 question
# ------------------------------------------------------------
df_q = df_tidy[
    df_tidy["question_text"].astype(str).str.contains(Q_PATTERN, regex=True, na=False)
].copy()

# keep only what we need
df_q = df_q[[COL_ID, "item", "answer"]]

# Join company size class
df_q = df_q.merge(df_map, on=COL_ID, how="left")

# Optional: if some respondents have no class (didn't answer size questions), drop them
df_q = df_q.dropna(subset=["company_size_class"])

# ------------------------------------------------------------
# C) Denominator (total respondents per company_size_class)
# ------------------------------------------------------------
# This matches your example: "10 Teilnehmer als GU" (all GU respondents).
# We compute totals from the mapping table, not from answers,
# so missing answers are still counted in the denominator.
totals = (
    df_map.dropna(subset=["company_size_class"])
          .groupby("company_size_class")[COL_ID]
          .nunique()
          .rename("total")
          .reset_index()
)

# ------------------------------------------------------------
# D) Count "Im Einsatz" and "In Planung" per item + GU/KMU
# ------------------------------------------------------------
df_counts = (
    df_q[df_q["answer"].isin(VALID_ANSWERS)]
    .groupby(["item", "company_size_class", "answer"])[COL_ID]
    .nunique()
    .rename("n")
    .reset_index()
)

# Add totals + percentage
df_summary = df_counts.merge(totals, on="company_size_class", how="left")
df_summary["pct"] = (df_summary["n"] / df_summary["total"]) * 100

# ------------------------------------------------------------
# E) Make it complete: ensure both answers appear for every (item, class)
# ------------------------------------------------------------
all_items = df_q["item"].dropna().unique().tolist()
all_classes = df_map["company_size_class"].dropna().unique().tolist()

full_index = pd.MultiIndex.from_product(
    [all_items, all_classes, VALID_ANSWERS],
    names=["item", "company_size_class", "answer"]
)

df_summary = (
    df_summary.set_index(["item", "company_size_class", "answer"])
              .reindex(full_index)
              .reset_index()
)

# Fill missing n with 0 and recompute pct
df_summary = df_summary.merge(totals, on="company_size_class", how="left", suffixes=("", "_tmp"))
df_summary["n"] = df_summary["n"].fillna(0).astype(int)
df_summary["pct"] = (df_summary["n"] / df_summary["total"]) * 100

# Clean columns
df_summary = df_summary[["item", "company_size_class", "answer", "n", "total", "pct"]]

print(df_summary.head(20))
