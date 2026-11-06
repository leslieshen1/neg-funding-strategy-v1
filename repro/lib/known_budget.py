"""Decision-time size limits.

The participation budget and the OI cap use only rows already known.
The current hour's volume may shrink a fill. It does not raise the budget
and it is not an input to coin selection. The fill price can still be this
hour's VWAP: that is an hourly-bar replay, not a tick fill.
"""

import numpy as np


def prior_oi_row(oih):
    """One-row lag. The current row and the next row are not included."""
    oih = np.asarray(oih, dtype=float)
    return np.vstack([np.full((1, oih.shape[1]), np.nan), oih[:-1]])


def shrink_to_realized(submitted, realized, enabled):
    """Current-hour capacity can only reduce a size that was already chosen."""
    if enabled and realized < submitted:
        return realized
    return submitted
