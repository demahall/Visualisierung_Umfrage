# Umfrage_Analyse/analyses/__init__.py

from .i_40_einsatz import compute_i40_einsatz_planung_summary
from .zustimmung import compute_zustimmung_summary
from .hemmnisse import wrapper_all_likert_data_frame
from .crosstab_stueckzahl_kennzahl import compute_stueckzahl_kennzahlen_summary
from .crosstab_kw_mit_ks_und_zp import compute_kw_mit_kz_und_zp_summary
from .crosstab_us_mit_ks_und_zp import compute_us_mit_ks_und_zp_summary


ANALYSES = [
    {
        "key": "i40_einsatz_planung",
        "func": compute_i40_einsatz_planung_summary,
        "needs": ["df_tidy", "df_size_class"],
    },
    {
        "key": "zustimmung",
        "func": compute_zustimmung_summary,
        "needs": ["df_tidy", "df_size_class"],
    },
    {
        "key": "likert_mean",
        "func": wrapper_all_likert_data_frame,
        "needs": ["df_tidy", "df_size_class"],
    },
    {
        "key": "stueckzahl_kennzahlen",
        "func": compute_stueckzahl_kennzahlen_summary,
        "needs": ["df_tidy"],
    },
    {
        "key": "kw_mit_kz_und_zp",
        "func": compute_kw_mit_kz_und_zp_summary,
        "needs": ["df_tidy"],
    },
    {
        "key": "us_mit_ks_und_zp",
        "func": compute_us_mit_ks_und_zp_summary,
        "needs": ["df_tidy"],
    },
]
