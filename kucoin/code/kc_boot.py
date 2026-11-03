"""Circular 7-day block bootstrap (5000 resamples) on daily net PnL, 10M denominator. Aggregates only."""
import numpy as np, pandas as pd, os
H = os.path.dirname(os.path.abspath(__file__)) + "/../"; K = H + "out/daily/"; B_ = os.environ.get("NFB_BIN_DAILY", H + "../out/r7_daily/")
def daily(p): x = np.load(p); k = len(x) // 24 * 24; return x[:k].reshape(-1, 24).sum(1)
def boot(d, S=10e6, blk=7, B=5000, seed=7):
    n = len(d); rng = np.random.default_rng(seed); nb = int(np.ceil(n / blk)); out = []
    for _ in range(B):
        st = rng.integers(0, n, nb); idx = ((st[:, None] + np.arange(blk)[None, :]) % n).reshape(-1)[:n]; out.append(d[idx].sum())
    out = np.array(out); y = n / 365.0
    return d.sum() / S / y * 100, np.quantile(out, .025) / S / y * 100, np.quantile(out, .975) / S / y * 100, (out <= 0).mean()
rows = []
for w in ("IS", "HO"):
    for sc in ("cal", "bp30"):
        f = daily(K + f"v9cmp_FINAL_339__{sc}__{w}.npy"); r = daily(K + f"v9cmp_REF_ADL_339__{sc}__{w}.npy"); b = daily(B_ + f"v9cmp_FINAL_339__{sc}__{w}.npy"); bR = daily(B_ + f"v9cmp_REF_ADL_339__{sc}__{w}.npy")
        v9 = daily(K + f"v9bridge_S0_v9like_339__bp30__{w}.npy")
        for nm, d in (("KC FINAL", f), ("KC REF(v9 rule)", r), ("KC V9 native cfg", v9), ("Binance FINAL", b), ("KC FINAL - Binance FINAL", f - b), ("KC FINAL - KC REF", f - r), ("KC FINAL - KC V9 native", f - v9), ("KC REF - Binance REF", r - bR)):
            if nm == "KC V9 native cfg" and sc == "cal": continue
            m, lo, hi, p = boot(d); rows.append(dict(win=w, scen=sc, item=nm, ann_pp=m, lo=lo, hi=hi, p_le0=p))
df = pd.DataFrame(rows); df.to_csv(H + "out/kc_boot.csv", index=False); print(df.round(2).to_string())
