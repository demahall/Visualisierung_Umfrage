# generate_spec_template.py
"""
Generate a template question specification from an Excel survey export.

Output: question_spec.json
You then copy/rename it to question_spec.json and edit:
- type: single | likert | checkbox | matrix | text
- options_order (for single/likert/checkbox to show zeros)
- answer_order and items_order for matrix
- other_text_col (optional) for "Sonstiges" free text

Run:
    python generate_spec_template.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd


EXCEL_PATH = Path("result-survey.xlsx")
FIRST_QUESTION_TEXT = "Welcher Art von Organisation gehören Sie an?"
OUT_PATH = Path("question_spec.json")


HEADER_RE = re.compile(r"^(.*?)(?:\s*\[(.+?)\])?\s*$")


def split_header(colname: str) -> Tuple[str, Optional[str]]:
    m = HEADER_RE.match(str(colname))
    if not m:
        return str(colname).strip(), None
    q = (m.group(1) or "").strip()
    item = (m.group(2) or "").strip() if m.group(2) else None
    return q, item


def is_other_item(item: Optional[str]) -> bool:
    if item is None:
        return False
    return item.strip().lower() in {"sonstiges", "other"}


def suggest_type_from_structure(cols: List[str], items: List[str]) -> str:
    """
    Minimal suggestion (not fancy):
    - 1 col -> 'single_or_text_or_likert'
    - >1 col with items -> 'matrix_or_checkbox'
    - >1 col without items -> 'multi_col'
    """
    if len(cols) == 1 and len(items) == 0:
        return "single_or_text_or_likert"
    if len(cols) > 1 and len(items) > 0:
        return "matrix_or_checkbox"
    return "multi_col"


def main() -> None:
    if not EXCEL_PATH.exists():
        raise FileNotFoundError(f"Excel not found: {EXCEL_PATH.resolve()}")

    df = pd.read_excel(EXCEL_PATH, sheet_name=0)
    df.columns = df.columns.astype(str).str.strip().str.replace("\n", " ", regex=False)

    if FIRST_QUESTION_TEXT not in df.columns:
        raise ValueError(
            f"FIRST_QUESTION_TEXT not found: {FIRST_QUESTION_TEXT}\n"
            f"First 20 columns: {list(df.columns[:20])}"
        )

    start_idx = df.columns.get_loc(FIRST_QUESTION_TEXT)
    q_cols = list(df.columns[start_idx:])

    # Group by question_text
    q_to_cols: Dict[str, List[str]] = {}
    q_to_items: Dict[str, set] = {}
    col_to_item: Dict[str, Optional[str]] = {}

    for c in q_cols:
        q, item = split_header(c)
        q_to_cols.setdefault(q, []).append(c)
        if item is not None:
            q_to_items.setdefault(q, set()).add(item)
        col_to_item[c] = item

    # Build template spec
    spec: Dict[str, Any] = {}
    for qtext, cols in q_to_cols.items():
        items = sorted(list(q_to_items.get(qtext, set())))
        other_cols = [c for c in cols if is_other_item(col_to_item.get(c))]
        main_cols = [c for c in cols if col_to_item.get(c) is None]

        entry: Dict[str, Any] = {
            "type": "TODO",  # <-- you will edit this
            "suggested_type": suggest_type_from_structure(cols, items),
            "cols": cols,  # helpful for you while editing
        }

        # helpful fields you can fill in
        if len(cols) == 1 and len(items) == 0:
            entry["options_order"] = []  # fill if you want zero categories shown
        else:
            entry["items"] = items  # bracket items detected
            entry["items_order"] = items[:]  # you can reorder
            entry["answer_order"] = ["Ja", "Nein", "Keine Antwort"]  # typical matrix order
            entry["options_order"] = []  # for checkbox

        if other_cols:
            entry["other_text_col"] = other_cols[0]  # often exactly one
            entry["other_prefix"] = "Sonstiges: "

        if main_cols:
            entry["main_col"] = main_cols[0]  # for single+sonstiges pattern

        spec[qtext] = entry

    OUT_PATH.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ Wrote template: {OUT_PATH.resolve()}")
    print("Next: rename to question_spec.json and edit the 'type' and ordering fields.")


if __name__ == "__main__":
    main()
