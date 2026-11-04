import os as _os
"""7-day block bootstrap (B=5000, seed 7) of annualised % on S: level CI and paired difference vs base. Aggregates only."""
import numpy as np, pandas as pd
import os
O = os.environ.get("NFB_OUT", (_os.environ.get("SIGNALS_ROOT", ".") + "/out/")).rstrip("/") + "/"; DD = os.environ.get("NFB_DAILY", O + "r9_daily/").rstrip("/") + "/"
def daily(S, fix, w):
    x = np.load(DD + f"S{S}M__{fix}__{w}.npy"); k = len(x) // 24 * 24; return x[:k].reshape(-1, 24).sum(1)
def boot(d, S, blk=7, B=5000, seed=7):
    n = len(d); rng = np.random.default_rng(seed); nb = int(np.ceil(n / blk)); out = np.empty(B)
    for i in range(B):
        st = rng.integers(0, n, nb); idx = ((st[:, None] + np.arange(blk)[None, :]) % n).reshape(-1)[:n]; out[i] = d[idx].sum()
    yrs = n / 365.0; f = 100.0 / (S * 1e6) / yrs
    return d.sum() * f, np.quantile(out, .025) * f, np.quantile(out, .975) * f, (out <= 0).mean()
import sys
# usage: r9_boot.py [fixlist,comma separated] [out csv name]; default = round-9 list -> r9_bootstrap.csv
DEF = ("base", "f1", "f1m", "f2", "f2x", "f3a", "f3b", "f4", "f4m", "all", "allC", "allCx", "allm", "allx", "dlyS", "dlyP", "all_dlyS", "all_dlyP", "allC_dlyS", "allC_dlyP")
FIXES = sys.argv[1].split(",") if len(sys.argv) > 1 else DEF
OUTN = sys.argv[2] if len(sys.argv) > 2 else "r9_bootstrap.csv"
rows = []
for S in (10, 20):
    for w in ("IS", "HO", "FY"):
        b0 = daily(S, "base", w)
        try: c0 = daily(S, "cons", w)
        except FileNotFoundError: c0 = None
        for fix in FIXES:
            try: d = daily(S, fix, w)
            except FileNotFoundError: continue
            m, lo, hi, p = boot(d, S); dm, dlo, dhi, dp = boot(d - b0, S) if fix != "base" else (0, 0, 0, np.nan)
            cm_, clo, chi, cp = boot(d - c0, S) if (c0 is not None and fix != "cons") else (0, 0, 0, np.nan)
            rows.append(dict(S=S, win=w, fix=fix, ann=m, lo=lo, hi=hi, p_le0=p, d_ann=dm, d_lo=dlo, d_hi=dhi, d_p_le0=dp, dc_ann=cm_, dc_lo=clo, dc_hi=chi))
df = pd.DataFrame(rows); df.to_csv(O + OUTN, index=False); print(df.round(2).to_string())
