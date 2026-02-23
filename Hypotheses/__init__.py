from .preprocessing_hypotheses import (
    compute_verknuepfung_hypotheses,
    compute_verknuepfung_h2_hypotheses,
    compute_strong_counts_hypotheses)

import QUESTION_LIST as hyp_const

df_hypotheses_dict = [
    {
        "key": "H1",
        "func": compute_verknuepfung_hypotheses,
        "params": {
            "initial_question": hyp_const.Q2,
            "target_question": hyp_const.Q11,
        }
    },
    {
        "key": "H2",
        "func": compute_verknuepfung_h2_hypotheses,
        "params": {
            "initial_question": hyp_const.Q4,
            "target_question": hyp_const.Q11
        }
    },
    {
        "key": "H3",
        "func": compute_verknuepfung_hypotheses,
        "params": {
            "initial_question": hyp_const.Q10,
            "target_question": hyp_const.Q11,
        }
    },
    {
        "key": "H4.1",
        "func": compute_strong_counts_hypotheses,
        "params": {
            "target_question": hyp_const.Q31,
            "strong_set": hyp_const.STRONG_CATEGORY_HEMMNIS
        },

    },
    {
        "key": "H4.2",
        "func": compute_strong_counts_hypotheses,
        "params": {
            "target_question": hyp_const.Q32,
            "strong_set": hyp_const.STRONG_CATEGORY_ZUSTIMMUNG
        },
    },
    {
        "key": "H4.3",
        "func": compute_strong_counts_hypotheses,
        "params": {
            "target_question": hyp_const.Q33,
            "strong_set": hyp_const.STRONG_CATEGORY_HEMMNIS
        },
    }

]