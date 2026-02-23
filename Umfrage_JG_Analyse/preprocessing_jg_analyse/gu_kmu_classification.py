# Builds respondent_id -> company_size_class (GU/KMU) mapping.
#
# Inputs:
# - df_tidy: long dataframe with columns: respondent_id, question_text, answer
# - catalog: list[dict] question metadata (options_order etc.)
# - const: provides Q2 (employees question text) and Q3 (turnover question text)
#
# Output:
# - df_size_class: DataFrame with columns: respondent_id, company_size_class
# ------------------------------------------------------------

from __future__ import annotations
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple

import QUESTION_LIST as const

COL_ID = const.COL_ID
Q1 = const.Q1
Q2 = const.Q2
Q3 = const.Q3


def gu_kmu_classification(df_tidy: pd.DataFrame) ->(pd.DataFrame):

    filter_ids = set(df_tidy.loc[
                       (df_tidy["question_text"] == Q1) &
                       (df_tidy["answer"].isin(["Produzierendes Unternehmen","IT - /Entwicklungsdienstleister"])),
                        COL_ID
                   ])

    other_filter_ids = set(df_tidy.loc[
                               (df_tidy["question_text"] == Q1) &
        (df_tidy["other_text"].isin(["Sonstiges: Ingenieurbüro",
                                     "Sonstiges: Sondermaschinenbau + Service",
                                     "Sonstiges: Sensortechnik-Unternehmen"])),
        COL_ID
                         ])

    merge_filter_ids = np.array(sorted(filter_ids | other_filter_ids))
    n_filter_ids = int(len(merge_filter_ids))

    # 2) only those respondents for Q2/Q3
    out = (df_tidy[df_tidy[COL_ID].isin(merge_filter_ids) & df_tidy["question_text"].isin([Q2, Q3])]
            .pivot_table(index=COL_ID, columns="question_text", values="answer", aggfunc="first")
            .reset_index())

    # 3) GU / KMU logic
    kmu = ((out[Q2] != "> 250") |
           ((out[Q3] == "< 5 Mio. EUR") |
           (out[Q3] == "5 - 50 Mio. EUR")))

    gu = ((out[Q2] == "> 250") &
          ((out[Q3] == "> 250 Mio. EUR") |
           (out[Q3] == "50 - 250 Mio. EUR")))

    out["company_size_class"] = np.where(gu, "GU", np.where(kmu, "KMU", "KMU"))

    df_size_class = out[[COL_ID, "company_size_class"]].copy()

    counts = df_size_class["company_size_class"].value_counts().astype(int).to_dict()

    return df_size_class
