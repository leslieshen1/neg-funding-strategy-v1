import os as _os
import numpy as np, pandas as pd
R = (_os.environ.get("SIGNALS_ROOT", ".") + "/out/r7_daily/"); V = (_os.environ.get("SIGNALS_ROOT", ".") + "/v9cmp/out/daily/")
def daily(p): x = np.load(p); k = len(x) // 24 * 24; return x[:k].reshape(-1, 24).sum(1)
def boot(a, b, S=10e6, blk=7, B=5000, seed=7):
    d = daily(a) - daily(b); n = len(d); rng = np.random.default_rng(seed); nb = int(np.ceil(n / blk)); out = []
    for _ in range(B):
        st = rng.integers(0, n, nb); idx = ((st[:, None] + np.arange(blk)[None, :]) % n).reshape(-1)[:n]; out.append(d[idx].sum())
    out = np.array(out); yrs = n / 365.0
    return d.sum() / S / yrs * 100, np.quantile(out, .025) / S / yrs * 100, np.quantile(out, .975) / S / yrs * 100, (out <= 0).mean()
rows = []
for w in ("IS", "HO"):
    v9 = V + f"V9_real__v11__{w}.npy"
    for sc in ("bp30", "cal"):
        F = R + f"v9cmp_FINAL_267__{sc}__{w}.npy"; REF = R + f"v9cmp_REF_ADL_267__{sc}__{w}.npy"; S0 = R + f"v9bridge_S0_v9like_267__bp30__{w}.npy"
        for nm, a, b in (("FINAL - REF(v9 rule, same env)", F, REF), ("FINAL - V9 native", F, v9), ("REF(v9 rule, round-7 env) - V9 native", REF, v9), ("V9 engine-in-ours (S0) - V9 native", S0, v9)):
            m, lo, hi, p = boot(a, b); rows.append(dict(win=w, scen=sc, cmp=nm, diff_ann_pp=m, lo=lo, hi=hi, p_le0=p))
df = pd.DataFrame(rows); df.to_csv((_os.environ.get("SIGNALS_ROOT", ".") + "/out/r7_v9boot.csv"), index=False); print(df.round(2).to_string())
