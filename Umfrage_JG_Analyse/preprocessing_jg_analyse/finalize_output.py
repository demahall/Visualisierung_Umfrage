
from __future__ import annotations
import pandas as pd

def finalize_crosstab_output(
    df: pd.DataFrame,
    *,
    analysis_key: str,
    segment_question: str,
    target_question: str,
    target_item: str | None = None,
    denom_type: str = "segment_valid_total",
) -> pd.DataFrame:

    """
    Expect df has: segment, answer, n, total, pct
    Adds metadata columns and reorders.
    """

    out = df.copy()
    out["analysis_key"] = analysis_key
    out["denom_type"] = denom_type
    out["segment_question"] = segment_question
    out["target_question"] = target_question
    out["target_item"] = target_item

    cols = [
        "analysis_key",
        "segment_question", "segment",
        "target_question", "target_item",
        "answer",
        "n", "total", "pct",
        "denom_type",
    ]
    return out[cols]


def finalize_matrix_output(
    df: pd.DataFrame,
    *,
    analysis_key: str,
    question_text: str,
    target_question: str,
    denom_type: str = "item_valid_total",
) -> pd.DataFrame:
    """
    Expect df has: item, company_size_class, answer, n, total, pct
    Adds question metadata and reorders.
    """
    out = df.copy()
    out["analysis_key"] = analysis_key
    out["denom_type"] = denom_type
    out["question_text"] = question_text
    out["target_question"] = target_question

    cols = [
        "analysis_key",
        "question_text", "target_question",
        "item", "company_size_class",
        "answer",
        "n", "total", "pct",
        "denom_type",
    ]
    return out[cols]

# output_contracts.py (same file)
def finalize_metric_output(
    df: pd.DataFrame,
    *,
    analysis_key: str,
    scale_label: str,
    scale_min: int,
    scale_max: int,
) -> pd.DataFrame:
    """
    Expect df has: item, company_size_class, metric, value, n_valid, n_total, pct_valid
    Adds question + scale metadata and reorders.
    """
    out = df.copy()
    out["analysis_key"] = analysis_key
    out["target_question"] = out["question_text"]
    out["scale_label"] = scale_label
    out["scale_min"] = scale_min
    out["scale_max"] = scale_max

    cols = [
        "analysis_key",
        "question_text", "target_question",
        "item", "company_size_class",
        "metric", "value",
        "n_valid", "n_total", "pct_valid",
        "scale_label", "scale_min", "scale_max",
    ]
    return out[cols]

def get_df_jg(df_jg_dict: dict, context: dict) -> dict:
    """
    Runs each preprocessing job and returns:
        results[job["key"]] = job["func"](**kwargs)
    """
    results = {}

    for spec in df_jg_dict:
        key = spec["key"]
        func = spec["func"]
        needs = spec.get("needs", [])

        kwargs = {n: context[n] for n in needs}
        df_jg_dict = func(**kwargs)

        results[key] = df_jg_dict

    return results
