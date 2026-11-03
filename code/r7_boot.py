import os as _os
import numpy as np, pandas as pd, sys
D = (_os.environ.get("SIGNALS_ROOT", ".") + "/out/r7_daily/")
def daily(n):
    x = np.load(D + n + ".npy"); k = len(x) // 24 * 24; return x[:k].reshape(-1, 24).sum(1)
def boot(a, b, S=10e6, blk=7, B=5000, seed=7):
    d = daily(a) - daily(b); n = len(d); rng = np.random.default_rng(seed); nb = int(np.ceil(n / blk)); out = []
    for _ in range(B):
        st = rng.integers(0, n, nb); idx = ((st[:, None] + np.arange(blk)[None, :]) % n).reshape(-1)[:n]; out.append(d[idx].sum())
    out = np.array(out); yrs = n / 365.0
    return d.sum() / S / yrs * 100, np.quantile(out, .025) / S / yrs * 100, np.quantile(out, .975) / S / yrs * 100, (out <= 0).mean()
if __name__ == "__main__":
    rows = []
    for w in ("IS", "HO"):
        for sc in ("cal", "book", "sqrt1", "bp30"):
            for b in ("newgate_c24", "oldgate_c24", "nogate_c24"):
                m, lo, hi, p = boot(f"frozen_m2fb_c48__{sc}__{w}", f"{b}__{sc}__{w}"); rows.append(dict(win=w, scen=sc, vs=b, diff_ann_pp=m, lo=lo, hi=hi, p_le0=p))
    df = pd.DataFrame(rows); df.to_csv((_os.environ.get("SIGNALS_ROOT", ".") + "/out/r7_bootstrap.csv"), index=False); print(df.round(2).to_string())
