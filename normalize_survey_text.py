import re
import unicodedata
import pandas as pd
from typing import Dict

LIKERT_HINTS = re.compile(
    r"(Wirkung|Hemmnis|Zustimmung|Mehrwert|entscheidend|Kenntnisse|Erfassung|Auswertung|Antwort|Nichtentscheidend|KeineAntwort)",
    re.IGNORECASE
)

#Normalize spec question
ORDER_KEYS = ("options_order", "answer_order", "items_order")

# Core direct mappings (most important)
CANON_MAP = {
    "KeineAntwort": "Keine Antwort",
    "Keine Antwort": "Keine Antwort",
    "Nichtentscheidend": "Nicht entscheidend",
    "Nicht entscheidend": "Nicht entscheidend",
    "KeinHemmnis": "Kein Hemmnis",
    "KeineZustimmung": "Keine Zustimmung",
    "KeineKenntnisse": "Keine Kenntnisse",
    "KeineWirkung": "Keine Wirkung",
    "HoheWirkung": "Hohe Wirkung",
    "GeringeWirkung": "Geringe Wirkung",
    "TeilweiseWirkung": "Teilweise Wirkung",
    "SehrhoheWirkung": "Sehr hohe Wirkung",
    "Sehr hoheWirkung": "Sehr hohe Wirkung",
    "Sehr hohe Wirkung": "Sehr hohe Wirkung",
    "SehrstarkesHemmnis": "Sehr starkes Hemmnis",
    "StarkesHemmnis": "Starkes Hemmnis",
    "GeringesHemmnis": "Geringes Hemmnis",
    "MittleresHemmnis": "Mittleres Hemmnis",
    "HoheZustimmung": "Hohe Zustimmung",
    "GeringeZustimmung": "Geringe Zustimmung",
    "TeilweiseZustimmung": "Teilweise Zustimmung",
    "SehrhoheZustimmung": "Sehr hohe Zustimmung",
    "MittlererMehrwert": "Mittlerer Mehrwert",
    "HoherMehrwert": "Hoher Mehrwert",
    "GeringerMehrwert": "Geringer Mehrwert",
    "Sehr hoherMehrwert": "Sehr hoher Mehrwert",
    "SehrhoherMehrwert": "Sehr hoher Mehrwert",
    "Teilsentscheidend": "Teils entscheidend",
    "Eherentscheidend": "Eher entscheidend",
    "Sehrentscheidend": "Sehr entscheidend",
    "Geringentscheidend": "Gering entscheidend",
    "ManuelleErfassung,keineNutzung": "Manuelle Erfassung, keine Nutzung",
    "ManuelleErfassung,manuelleAuswertung": "Manuelle Erfassung, manuelle Auswertung",
    "AutomatisierteErfassung,manuelleAuswertung": "Automatisierte Erfassung, manuelle Auswertung",
    "AutomatisierteErfassung,automatisierteAuswertung": "Automatisierte Erfassung, automatisierte Auswertung",
    "KeineErfassung": "Keine Erfassung",
    "GuteKenntnisse": "Gute Kenntnisse",
    "MittlereKenntnisse": "Mittlere Kenntnisse",
    "GeringeKenntnisse": "Geringe Kenntnisse",
    "SehrumfassendeKenntnisse": "Sehr umfassende Kenntnisse",
}


def normalize_by_canon_map(x, canon_map: Dict[str, str]):
    """
    Combined normalizer:
    - robust Unicode cleanup (spaces, dashes, quotes) to make matching stable
    - apply CANON_MAP only when a match exists (direct / comma-normalized / nospace)
    - if no match, return cleaned original (NOT aggressively changed beyond cleanup)

    Cleanup covers:
    - NBSP and other unicode spaces -> normal space
    - remove zero-width chars
    - normalize en/em dash/minus -> "-"
    - collapse whitespace
    - standardize hyphen spacing: "50-250" / "50 – 250" -> "50 - 250"
    """

    if pd.isna(x):
        return x

    s = str(x)

    # ---------- A) robust cleanup ----------
    s = unicodedata.normalize("NFKC", s)

    # normalize unicode spaces
    s = (
        s.replace("\u00A0", " ")  # NBSP
         .replace("\u2007", " ")  # figure space
         .replace("\u202F", " ")  # narrow NBSP
         .replace("\u2009", " ")  # thin space
         .replace("\u200A", " ")  # hair space
         .replace("\u200B", "")   # zero-width space
         .replace("\uFEFF", "")   # BOM / zero-width no-break space
    )

    # normalize dash variants to hyphen
    s = (
        s.replace("\u2013", "-")  # en dash
         .replace("\u2014", "-")  # em dash
         .replace("\u2212", "-")  # minus sign
    )

    # normalize quotes (optional but helps matching)
    s = (s.replace("„", '"').replace("“", '"').replace("”", '"')
           .replace("‚", "'").replace("‘", "'").replace("’", "'"))

    # collapse whitespace
    s = re.sub(r"\s+", " ", s).strip()

    if not s:
        return s

    # standardize hyphen spacing (ranges etc.)
    s = re.sub(r"\s*-\s*", " - ", s)
    s = re.sub(r"\s+", " ", s).strip()

    # ---------- B) CANON MAP matching (your logic) ----------
    # 1) direct hit
    if s in canon_map:
        return canon_map[s]

    # 2) normalize commas (remove spaces around comma)
    s_commas = re.sub(r"\s*,\s*", ",", s)
    if s_commas in canon_map:
        return canon_map[s_commas]

    # 3) remove ALL spaces (handles KeineAntwort, SehrhoheWirkung, etc.)
    s_nospace = s_commas.replace(" ", "")
    if s_nospace in canon_map:
        return canon_map[s_nospace]

    # If no match, return cleaned original
    return s
