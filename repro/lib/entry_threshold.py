"""Headline entry threshold on the 8h-normalized funding rate.

The engine admits a coin only when ``-rate8 > ENTRY_FAV_N``, which is the same
statement as ``rate8 < -ENTRY_FAV_N``. A rate that normalizes to exactly
-0.001 does not enter. ``ENTRY_FAV_N_HISTORICAL`` is the previous headline
value and remains signal E1. It is not the default command.
"""

ENTRY_FAV_N = 0.001
ENTRY_FAV_N_HISTORICAL = 0.0005


def rate8_from_interval(rate, interval_h):
    """Scale a settlement print of ``interval_h`` hours onto an 8h rate."""
    return float(rate) * 8.0 / float(interval_h)


def passes_entry_rate(rate8, entry_fav_n=ENTRY_FAV_N):
    """Match engine_v12s: ``-r > entry_fav_n``. Equality does not pass."""
    return (-float(rate8)) > float(entry_fav_n)
