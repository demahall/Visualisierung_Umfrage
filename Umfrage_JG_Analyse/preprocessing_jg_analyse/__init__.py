# Umfrage_JG_Analyse/preprocessing_jg_analyse/__init__.py

from .i_40_einsatz import compute_i40_einsatz_planung_summary
from .zustimmung import compute_zustimmung_summary
from .likert_skala import wrapper_all_likert_data_frame
from .crosstab_stueckzahl_kennzahl import compute_stueckzahl_kennzahlen_summary
from .crosstab_kw_mit_ks_und_zp import compute_kw_mit_kz_und_zp_summary
from .crosstab_us_mit_ks_und_zp import compute_us_mit_ks_und_zp_summary


df_jg_dict = [
    {
        "key": "i40_einsatz_planung",
        "func": compute_i40_einsatz_planung_summary,
        "needs": ["df_tidy", "gu_kmu"],
    },
    {
        "key": "zustimmung",
        "func": compute_zustimmung_summary,
        "needs": ["df_tidy", "gu_kmu"],
    },
    {
        "key": "likert_mean",
        "func": wrapper_all_likert_data_frame,
        "needs": ["df_tidy", "gu_kmu"],
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
