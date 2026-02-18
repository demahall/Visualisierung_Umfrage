# preprocessing.py
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Sequence

import numpy as np
import pandas as pd
from normalize_survey_text import normalize_by_canon_map,CANON_MAP,ORDER_KEYS

HEADER_RE = re.compile(r"^(.*?)(?:\s*\[(.+?)\])?\s*$")

#-------
Q1_TEXT = "Welche der nachfolgenden Industrie 4.0-Technologien generieren für Sie einen Mehrwert bei der Umsetzung zirkulärer Wertschöpfungsprozesse?"
Q2_TEXT = "In welchen Lebenszyklusphasen bzw. Elementen des zirkulären Wertschöpfungsprozesses erwarten Sie den größten Mehrwert durch Industrie 4.0-Technologien? (Mehrfachauswahl möglich)"
Q1_ITEMS_ORDER = [
        "Traceability-Technologien(z. B. RFID, Barcode, QR-Code)",
        "Sensorik in Produkten(z.B. Druck, Drehzahl, Temperatur, …)",
        "Sensorik in Maschinen(z.B. Strom- oder Druckluftverbrauch, …)",
        "Standards zum Datenaustausch (z.B. OPC UA)",
        "Datenplattformen, Ökosysteme und Dateninfrastrukturen (z. B. Digitaler Produktpass)",
        "Künstliche Intelligenz und Datenanalyse (z.B. Zustandsüberwachung, datengetriebene Entscheidungsfindung, …)",
        "Simulationen (z.B. Materialflusssimulation)",
        "Verwaltungsschale (Asset Administration Shell, AAS)"
      ]
#---------------------

#---------------------
#HELPER
#---------------------

def _norm_key(s: str) -> str:
    # normalize whitespace + NBSP + trim
    s = str(s).replace("\u00a0", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _norm_list_values(lst, canon_map):
    if not isinstance(lst, list):
        return lst
    return [normalize_by_canon_map(v, canon_map) for v in lst]

def split_header(colname: str) -> Tuple[str, Optional[str]]:
    m = HEADER_RE.match(str(colname))
    if not m:
        return str(colname).strip(), None
    q = (m.group(1) or "").strip()
    item = (m.group(2) or "").strip() if m.group(2) else None
    return q, item


def normalize_str(x: Any) -> Any:
    if isinstance(x, str):
        return x.strip()
    return x


def normalize_yes_no(x: Any) -> Any:
    if not isinstance(x, str):
        return x
    s = x.strip()
    if s.lower() == "ja":
        return "Ja"
    if s.lower() == "nein":
        return "Nein"
    if s.lower() in {"keine antwort", "keineangabe", "k.a.", "k. a."}:
        return "Keine Antwort"
    if s == "":
        return pd.NA
    return s


def load_spec(spec_path: Optional[str | Path]) -> Dict[str, Any]:
    if spec_path is None:
        return {}
    p = Path(spec_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def merge_other_text_into_main(
    df_q: pd.DataFrame,
    main_col: str,
    other_col: str,
    other_prefix: str = "Sonstiges: ",
    trigger_value: str = "Sonstiges",
) -> None:
    """
    If respondent selected 'Sonstiges' in main_col and wrote text in other_col,
    replace main_col with 'Sonstiges: <text>'.
    """
    if main_col not in df_q.columns or other_col not in df_q.columns:
        return
    mask = (
        df_q[main_col].astype(str).str.strip().eq(trigger_value)
        & df_q[other_col].notna()
    )
    df_q.loc[mask, main_col] = other_prefix + df_q.loc[mask, other_col].astype(str).str.strip()


def build_catalog(
    df_q,
    spec: Dict[str, Any],
    exclude_cols: Optional[List[str]] = None
) -> List[Dict[str, Any]]:

    exclude_cols = exclude_cols or []
    cols = [c for c in df_q.columns if c not in exclude_cols]

    # --- normalize spec keys once ---
    defaults = spec.get("__defaults__", {})
    spec_norm = {_norm_key(k): v for k, v in spec.items() if k != "__defaults__"}

    q_to_cols: Dict[str, List[str]] = {}
    q_to_items: Dict[str, set] = {}
    col_to_item: Dict[str, Optional[str]] = {}

    for c in cols:
        qtext, item = split_header(c)
        q_to_cols.setdefault(qtext, []).append(c)
        if item is not None:
            q_to_items.setdefault(qtext, set()).add(item)
        col_to_item[c] = item

    catalog: List[Dict[str, Any]] = []
    col_index = {c: i for i, c in enumerate(df_q.columns)}

    for qtext, qcols in q_to_cols.items():

        qtext_norm = normalize_by_canon_map(qtext, CANON_MAP)

        # normalize items from headers so later items_order matches
        items = sorted([normalize_by_canon_map(it, CANON_MAP) for it in q_to_items.get(qtext, set())])

        sp = spec_norm.get(_norm_key(qtext_norm), {})

        # normalize spec order lists (options_order / answer_order / items_order)
        sp = dict(sp)  # do not mutate global dict
        for k in ORDER_KEYS:
            if k in sp:
                sp[k] = _norm_list_values(sp[k], CANON_MAP)


        entry: Dict[str, Any] = {
            "question_text": qtext_norm,
            "cols": qcols,
            "items": items,
            "col_to_item": {c: col_to_item.get(c) for c in qcols},
        }

        # 1) apply global defaults (if present)
        entry.update(defaults)

        # 2) apply question-specific spec (overrides defaults)
        entry.update(sp)

        # 3) hard fallback if type still missing
        entry.setdefault("type", "single")

        catalog.append(entry)

    catalog.sort(key=lambda q: col_index.get(q["cols"][0], 10**9))
    return catalog


def tidy_single_like(df_q: pd.DataFrame, q: Dict[str, Any]) -> pd.DataFrame:
    col = q["cols"][0]
    out = df_q[["respondent_id", col]].rename(columns={col: "answer"})
    out["question_text"] = q["question_text"]
    out["item"] = None
    return out[["respondent_id", "question_text", "item", "answer"]]



def tidy_text(df_q: pd.DataFrame, q: Dict[str, Any]) -> pd.DataFrame:
    # same structure; you typically plot as text overview
    return tidy_single_like(df_q, q)


def tidy_checkbox(df_q: pd.DataFrame, q: Dict[str, Any]) -> pd.DataFrame:
    """
    Checkbox export: one column per option, values are Ja/Nein/empty.
    Keep only selected options (Ja). answer=option label
    """
    melted = df_q[["respondent_id"] + q["cols"]].melt(
        id_vars="respondent_id", var_name="col", value_name="raw"
    )
    melted["question_text"] = q["question_text"]
    melted["item"] = melted["col"].map(q["col_to_item"])
    melted = melted[melted["raw"] == "Ja"].copy()
    melted["answer"] = melted["item"].fillna(melted["col"])
    melted["item"] = None
    return melted[["respondent_id", "question_text", "item", "answer"]]


def tidy_matrix(df_q: pd.DataFrame, q: Dict[str, Any]) -> pd.DataFrame:
    """
    Matrix grid: each column is an item/statement, each cell is categorical (Ja/Nein/Keine Antwort, etc.)
    """
    melted = df_q[["respondent_id"] + q["cols"]].melt(
        id_vars="respondent_id", var_name="col", value_name="answer"
    )
    melted["question_text"] = q["question_text"]
    melted["item"] = melted["col"].map(q["col_to_item"]).fillna(melted["col"])
    melted = melted.dropna(subset=["answer"])
    return melted[["respondent_id", "question_text", "item", "answer"]]


def tidy_matrix_single(df_q: pd.DataFrame, q: Dict[str, Any]) -> pd.DataFrame:
    """
    matrix-single where each technology is encoded as:
      <question prefix> [<item>]
    and each cell contains a categorical text (Likert).

    Output:
      respondent_id | question_text | item | answer
    """

    # 1) pick columns: either explicit q["cols"] OR auto-detect by prefix
    if q.get("cols"):
        qcols = [c for c in q["cols"] if c in df_q.columns]
    else:
        prefix = q.get("cols_prefix")
        if not prefix:
            raise KeyError("tidy_matrix_single_bracket needs either q['cols'] or q['cols_prefix']")
        qcols = [c for c in df_q.columns if str(c).startswith(prefix)]

    if not qcols:
        return pd.DataFrame(columns=["respondent_id", "question_text", "item", "answer"])

    # 2) melt
    melted = df_q[["respondent_id"] + qcols].melt(
        id_vars="respondent_id", var_name="col", value_name="answer"
    )

    # 3) normalize column text (NBSP etc.)
    col_norm = (
        melted["col"]
        .astype(str)
        .str.replace("\u00A0", " ", regex=False)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )

    # 4) parse single bracket item at end: [... ]
    pattern = (q.get("col_parse") or {}).get("pattern") or r"\[(?P<item>[^\]]+)\]\s*$"
    extracted = col_norm.str.extract(pattern)

    melted["question_text"] = q["question_text"]
    melted["item"] = extracted["item"].fillna(col_norm).astype(str).str.strip()

    # 5) keep only answered
    melted = melted.dropna(subset=["answer"])

    return melted[["respondent_id", "question_text", "item", "answer"]]


def tidy_matrix_multi(df_q: pd.DataFrame, q: Dict[str, Any]) -> pd.DataFrame:
    """
    Multi-select matrix from many binary columns:
      <question prefix> ... [<item>][<answer>]
    cell value = 1 if selected, else NaN/empty

    Returns ONLY selected cells:
      respondent_id | question_text | item | answer
    where:
      item   = technology
      answer = phase ("1".."10" or "Keine Antwort")
    """

    # 1) detect columns by prefix (recommended for long question text exports)
    prefix = q.get("cols_prefix")
    if prefix:
        qcols = [c for c in df_q.columns if str(c).startswith(prefix)]
    else:
        qcols = [c for c in q.get("cols", []) if c in df_q.columns]

    if not qcols:
        return pd.DataFrame(columns=["respondent_id", "question_text", "item", "answer"])

    # 2) melt (IMPORTANT: value column must NOT be named "answer")
    melted = df_q[["respondent_id"] + qcols].melt(
        id_vars="respondent_id",
        var_name="col",
        value_name="value",
    )

    # 3) keep only selected checkboxes
    def _is_selected(v: Any) -> bool:
        if pd.isna(v):
            return False
        if isinstance(v, bool):
            return v
        try:
            return float(v) == 1.0
        except Exception:
            return str(v).strip().lower() in {"1", "x", "ja", "true"}

    melted = melted[melted["value"].map(_is_selected)]
    if melted.empty:
        return pd.DataFrame(columns=["respondent_id", "question_text", "item", "answer"])

    # 4) normalize column string
    col_norm = (
        melted["col"]
        .astype(str)
        .str.replace("\u00A0", " ", regex=False)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )

    # 5) parse [item][answer] from end of column name
    pattern = (q.get("col_parse") or {}).get("pattern") or r"\[(?P<item>[^\]]+)\]\[(?P<answer>[^\]]+)\]\s*$"
    extracted = col_norm.str.extract(pattern)

    # 6) assign parsed item/answer (CRITICAL)
    melted["item"] = extracted["item"].astype(str).str.strip()
    melted["answer"] = extracted["answer"].astype(str).str.strip()
    melted["question_text"] = q["question_text"]

    # 7) drop parse failures
    melted = melted[melted["item"].ne("nan") & melted["answer"].ne("nan")]

    return melted[["respondent_id", "question_text", "item", "answer"]]


def build_q2_conditional_virtual_questions(
    df_tidy: pd.DataFrame,
    q1_text: str,
    q2_text: str,
    items_order: Optional[List[str]] = None,
    q1_high_answers: Sequence[str] = ("Hoher Mehrwert", "Sehr hoher Mehrwert"),
    q2_answer_keep: Optional[Sequence[str]] = None,  # if you want only "1..10 + Keine Antwort"
    q2_virtual_prefix: str = "Q2 (filtered by Q1 high value)",
) -> pd.DataFrame:
    """
    Creates virtual questions for Q2 conditioned on Q1 high answers per technology item.

    Output rows schema matches df_tidy:
      respondent_id | question_text | item | answer

    For each technology item t:
      - Filter respondents who answered Q1(t) in q1_high_answers
      - Take their Q2 selections for the SAME item t
      - Emit a virtual question where item=None and answer=phase
    """

    # --- Q1 subset
    d1 = df_tidy[df_tidy["question_text"] == q1_text].copy()
    d1["item"] = d1["item"].astype(str)
    d1["answer"] = d1["answer"].astype(str)

    # --- Q2 subset
    d2 = df_tidy[df_tidy["question_text"] == q2_text].copy()
    d2["item"] = d2["item"].astype(str)
    d2["answer"] = d2["answer"].astype(str)

    if items_order:
        items = list(items_order)
    else:
        # intersection of items appearing in either Q1 or Q2
        items = sorted(set(d1["item"].dropna().unique()).intersection(set(d2["item"].dropna().unique())))

    out_rows = []

    for it in items:
        # respondents with high value for this technology in Q1
        keep_ids = d1.loc[
            (d1["item"] == it) & (d1["answer"].isin(q1_high_answers)),
            "respondent_id"
        ].unique()

        if len(keep_ids) == 0:
            continue

        # their Q2 selections for the same item
        sel = d2.loc[(d2["item"] == it) & (d2["respondent_id"].isin(keep_ids)), ["respondent_id", "answer"]].copy()

        if q2_answer_keep is not None:
            sel = sel[sel["answer"].isin(set(map(str, q2_answer_keep)))]

        if sel.empty:
            # still create nothing; or you can create a dummy "Keine Antwort" row if you prefer
            continue

        v_qtext = f"{q2_virtual_prefix} | {it}"
        sel["question_text"] = v_qtext
        sel["item"] = None  # makes it single-like
        out_rows.append(sel[["respondent_id", "question_text", "item", "answer"]])

    if not out_rows:
        return pd.DataFrame(columns=["respondent_id", "question_text", "item", "answer"])

    return pd.concat(out_rows, ignore_index=True)


def build_tidy(df_q: pd.DataFrame, catalog: List[Dict[str, Any]]) -> pd.DataFrame:
    frames: List[pd.DataFrame] = []
    for q in catalog:
        t = q["type"]
        if t in {"single", "likert"}:
            frames.append(tidy_single_like(df_q, q))
        elif t == "text":
            frames.append(tidy_text(df_q, q))
        elif t == "checkbox":
            frames.append(tidy_checkbox(df_q, q))
        elif t == "matrix":
            frames.append(tidy_matrix(df_q, q))
        elif t == "matrix_single":
            frames.append(tidy_matrix_single(df_q,q))
        elif t == "matrix_multi":
            frames.append(tidy_matrix_multi(df_q,q))
        else:
            # fallback
            if len(q["cols"]) == 1:
                frames.append(tidy_single_like(df_q, q))
            else:
                frames.append(tidy_matrix(df_q, q))

    if not frames:
        return pd.DataFrame(columns=["respondent_id", "question_text", "item", "answer"])

    df_tidy = pd.concat(frames, ignore_index=True)
    df_tidy["question_text"] = df_tidy["question_text"].astype(str).str.strip()
    df_tidy["answer"] = df_tidy["answer"].apply(normalize_str)

    #Handling Sonstiges answer, make a new column to keep the sonstiges information

    mask = df_tidy["answer"].astype("string").str.startswith("Sonstiges:", na=False)
    df_tidy.loc[mask, "other_text"] = df_tidy.loc[mask, "answer"].astype("string")
    df_tidy.loc[mask, "answer"] = "Sonstiges"

    return df_tidy


def compute_base_map(df_q: pd.DataFrame, catalog: list[dict]) -> dict[str, int]:
    base_map: dict[str, int] = {}

    for q in catalog:
        qtext = q["question_text"]
        cols = q.get("cols", [])

        # keep only columns that actually exist
        cols_present = [c for c in cols if c in df_q.columns]

        if not cols_present:
            # no columns found -> base is 0 (or len(df_q) if you prefer)
            base_map[qtext] = 0
            continue

        mask = df_q[cols_present].notna().any(axis=1)
        base_map[qtext] = int(mask.sum())

    return base_map



def prepare_data(
    excel_path: str | Path,
    first_question_text: str,
    sheet_name: int | str = 0,
    spec_path: Optional[str | Path] = "question_spec.json",
) -> Tuple[pd.DataFrame, pd.DataFrame, List[Dict[str, Any]], pd.DataFrame, Dict[str, int]]:

    """
    Spec-driven preprocessing:
    - Loads question_spec.json (if exists)
    - Applies Sonstiges merge when configured
    """

    excel_path = Path(excel_path)
    df_raw = pd.read_excel(excel_path, sheet_name=sheet_name,dtype=str)
    df_raw.columns = df_raw.columns.astype(str).str.strip().str.replace("\n", " ", regex=False)

    if first_question_text not in df_raw.columns:
        raise ValueError(
            f"first_question_text not found.\nExpected: {first_question_text}\n"
            f"First 20 columns: {list(df_raw.columns[:20])}"
        )

    start_idx = df_raw.columns.get_loc(first_question_text)
    df_q = df_raw.iloc[:, start_idx:].copy()

    # normalize values
    df_q = df_q.map(normalize_str)
    df_q = df_q.map(normalize_yes_no)

    # respondent id
    df_q["respondent_id"] = np.arange(1, len(df_q) + 1)

    # load spec
    spec = load_spec(spec_path)

    # Apply Sonstiges merge according to spec (if provided)
    # and drop the other text columns afterwards
    drop_cols = []
    for qtext, sp in spec.items():
        other_col = sp.get("other_text_col")
        main_col = sp.get("main_col") or qtext  # default: main col equals qtext
        if other_col and main_col in df_q.columns and other_col in df_q.columns:
            merge_other_text_into_main(
                df_q,
                main_col=main_col,
                other_col=other_col,
                other_prefix=sp.get("other_prefix", "Sonstiges: "),
                trigger_value=sp.get("other_trigger_value", "Sonstiges"),
            )
            drop_cols.append(other_col)

    if drop_cols:
        df_q = df_q.drop(columns=[c for c in drop_cols if c in df_q.columns])

    # build catalog using spec types/order
    catalog = build_catalog(df_q, spec=spec, exclude_cols=["respondent_id"])

    # tidy
    df_tidy = build_tidy(df_q, catalog)

    #base
    df_tidy_base = df_tidy

    #normalize
    df_tidy["question_text"] = df_tidy["question_text"].map(lambda v: normalize_by_canon_map(v, CANON_MAP))
    df_tidy["answer"] = df_tidy["answer"].map(lambda v: normalize_by_canon_map(v, CANON_MAP))
    if "item" in df_tidy.columns:
        df_tidy["item"] = df_tidy["item"].map(lambda v: normalize_by_canon_map(v, CANON_MAP))

    #
    df_tidy_virtual = build_q2_conditional_virtual_questions(
        df_tidy=df_tidy_base,
        q1_text=Q1_TEXT,
        q2_text=Q2_TEXT,
        items_order=Q1_ITEMS_ORDER,  # your 8 technologies
        q1_high_answers=("Hoher Mehrwert", "Sehr hoher Mehrwert"),
        q2_answer_keep=[str(i) for i in range(1, 11)] + ["Keine Antwort"],
        q2_virtual_prefix="Q2 – Erwarteter Mehrwert nach Lebenszyklusphase (nur Hoher/Sehr hoher Mehrwert in Q1)",
    )

    df_tidy = pd.concat([df_tidy_base, df_tidy_virtual], ignore_index=True)

    # base map
    base_map = compute_base_map(df_q, catalog)

    return df_raw, df_q, catalog, df_tidy, base_map
