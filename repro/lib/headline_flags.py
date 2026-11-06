"""Headline switches for the three accounting changes.

A known budget, B fee-gate match, and C open residual are independent.
They are not engine defaults by themselves: the headline command turns all
three on, and the comparison runner turns them one at a time.
"""


def engine_extra(known_budget, fee_gate_match, open_residual, entry_fav_n):
    extra = {"entry_fav_n": float(entry_fav_n), "fee_gate_match": bool(fee_gate_match)}
    if known_budget:
        extra["same_hour"] = False
        extra["f_prior"] = 1.0
        extra["fill_cap"] = 1.0
    else:
        extra["same_hour"] = True
        extra["fill_cap"] = 0.0
    if open_residual:
        extra["res_mode"] = 3.0
        extra["acct_book"] = 1.0
    else:
        extra["res_mode"] = 2.0
        extra["acct_book"] = 0.0
    return extra
