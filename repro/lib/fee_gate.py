"""Round-trip fee used by the income gate.

The historical gate used a fixed 0.30% round trip. The matched gate uses
twice the selected spot plus perpetual taker fee, the same rates the fill
charges. Impact and spread terms are unchanged, and this fee is not subtracted
again from the fill.
"""


class GateFee:
    match_tier = False
    fee_s = None
    fee_f = None


def configure(match_tier, fee_s=None, fee_f=None):
    GateFee.match_tier = bool(match_tier)
    GateFee.fee_s = None if fee_s is None else float(fee_s)
    GateFee.fee_f = None if fee_f is None else float(fee_f)


def reset():
    configure(False, None, None)


def roundtrip():
    if not GateFee.match_tier:
        return 0.0030
    if GateFee.fee_s is None or GateFee.fee_f is None:
        raise RuntimeError("fee-gate match is on, but the selected spot and perpetual fees are missing")
    return 2.0 * (GateFee.fee_s + GateFee.fee_f)
