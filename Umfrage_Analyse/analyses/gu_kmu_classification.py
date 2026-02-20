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
from typing import List, Dict, Optional, Union

import hypothesen_CONST as const

COL_ID = const.COL_ID
COL_EMPLOYEES = const.Q2
COL_TURNOVER = const.Q3


def _get_question_from_catalog(catalog: List[Dict], question_text: str) -> Optional[Dict]:
    return next((q for q in catalog if q.get("question_text") == question_text), None)


def build_company_size_mapping(df_tidy: pd.DataFrame, catalog: List[Dict])-> (pd.DataFrame):
    """
    GU if:
      - employees answer is '> 250' (robust to spaces)
      - AND turnover answer is in the GU turnover set
        (here: taken from catalog options_order BUT filtered to the two GU turnover categories)
    else -> KMU
    """

    # 1) take only the two questions
    df_size = df_tidy[df_tidy["question_text"].isin([COL_EMPLOYEES, COL_TURNOVER])][
        [COL_ID, "question_text", "answer"]
    ].copy()

    # 2) pivot to one row per respondent
    wide = (
        df_size.pivot_table(index=COL_ID, columns="question_text", values="answer", aggfunc="first")
              .reset_index()
    )

    # 3) turnover options: pick only the GU ones from catalog
    q3_cat = _get_question_from_catalog(catalog, COL_TURNOVER)
    if not q3_cat:
        raise ValueError(f"Turnover question not found in catalog: {COL_TURNOVER}")

    GU_TURNOVER_SET = q3_cat.get("options_order") or []

    def is_gu(row) -> bool:
        emp = str(row.get(COL_EMPLOYEES, "")).strip().replace(" ", "")
        turn = str(row.get(COL_TURNOVER, "")).strip()

        cond_emp = (emp == ">250")
        cond_turn = (turn in GU_TURNOVER_SET)
        return bool(cond_emp and cond_turn)

    wide["company_size_class"] = np.where(wide.apply(is_gu, axis=1), "GU", "KMU")

    return wide[[COL_ID, "company_size_class"]].copy()
