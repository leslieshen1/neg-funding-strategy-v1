import os as _os
"""Round 10: 7-day block bootstrap (B=5000, seed 7), level CI and paired difference vs the 48h reference (same k_imp). Aggregates only."""
import numpy as np, pandas as pd
O = (_os.environ.get("SIGNALS_ROOT", ".") + "/out/"); DD = O + "r10_daily/"
def daily(S, fix, w):
    x = np.load(DD + f"S{S}M__{fix}__{w}.npy"); k = len(x) // 24 * 24; return x[:k].reshape(-1, 24).sum(1)
def boot(d, S, blk=7, B=5000, seed=7):
    n = len(d); rng = np.random.default_rng(seed); nb = int(np.ceil(n / blk)); out = np.empty(B)
    for i in range(B):
        st = rng.integers(0, n, nb); idx = ((st[:, None] + np.arange(blk)[None, :]) % n).reshape(-1)[:n]; out[i] = d[idx].sum()
    f = 100.0 / (S * 1e6) / (n / 365.0)
    return d.sum() * f, np.quantile(out, .025) * f, np.quantile(out, .975) * f, (out <= 0).mean()
if __name__ == '__main__':
    rows = []
    for S in (10, 20):
        for w in ("IS", "HO", "FY"):
            for k in ("", "_k2", "_k6"):
                ref = daily(S, "cons" + k, w)
                for v in (("", "_c0", "_c12", "_c24", "_x2a", "_x2b") if k == "" else ("", "_c0", "_x2a", "_c24")):
                    fix = "cons" + v + k; d = daily(S, fix, w); m, lo, hi, p = boot(d, S)
                    dm, dlo, dhi, dp = boot(d - ref, S) if v else (0, 0, 0, np.nan)
                    rows.append(dict(S=S, win=w, k=k or "_k4", rule=v or "_c48", ann=m, lo=lo, hi=hi, d_ann=dm, d_lo=dlo, d_hi=dhi, d_p_le0=dp, net_wan=d.sum() / 1e4))
    df = pd.DataFrame(rows); df.to_csv(O + "r10_bootstrap.csv", index=False); print(df.round(1).to_string())
