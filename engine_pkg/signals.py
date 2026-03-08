import pandas as pd

def decide_ratio(ret_t, ret_s, vol_t, vol_s):
    # Avoid division by zero or NaN
    if pd.isna(ret_t) or pd.isna(ret_s) or vol_t == 0 or vol_s == 0:
        return 0.5, 0.5

    # Risk-adjusted scores
    score_t = ret_t / vol_t
    score_s = ret_s / vol_s

    # Convert negative scores to zero (no weight)
    score_t = abs(ret_t) / vol_t
    score_s = abs(ret_s) / vol_s

    total = score_t + score_s
    if total == 0:
        return 0.5, 0.5

    w_t = score_t / total
    w_s = score_s / total

    return w_t, w_s