# 同环境对比(冻结规则 − v9 规则)在 339 币池上的 7 天块自助置信区间;与 r7_v9cmp.csv 的 339 池年化口径一致
import os as _os
import numpy as np, pandas as pd
R = (_os.environ.get("SIGNALS_ROOT", ".") + "/out/r7_daily/")
def daily(p): x = np.load(p); k = len(x) // 24 * 24; return x[:k].reshape(-1, 24).sum(1)
def boot(a, b, S=10e6, blk=7, B=5000, seed=7):
    d = daily(a) - daily(b); n = len(d); rng = np.random.default_rng(seed); nb = int(np.ceil(n / blk)); out = []
    for _ in range(B):
        st = rng.integers(0, n, nb); idx = ((st[:, None] + np.arange(blk)[None, :]) % n).reshape(-1)[:n]; out.append(d[idx].sum())
    out = np.array(out); yrs = n / 365.0
    return d.sum() / S / yrs * 100, np.quantile(out, .025) / S / yrs * 100, np.quantile(out, .975) / S / yrs * 100, (out <= 0).mean()
rows = []
for w in ("IS", "HO"):
    for sc in ("bp30", "cal"):
        m, lo, hi, p = boot(R + f"v9cmp_FINAL_339__{sc}__{w}.npy", R + f"v9cmp_REF_ADL_339__{sc}__{w}.npy")
        rows.append(dict(win=w, scen=sc, pool=339, cmp="FINAL - REF(v9 rule, same env)", diff_ann_pp=m, lo=lo, hi=hi, p_le0=p))
df = pd.DataFrame(rows); df.to_csv(_os.environ.get("SIGNALS_ROOT", ".") + "/out/r7_v9boot339.csv", index=False); print(df.round(2).to_string())
