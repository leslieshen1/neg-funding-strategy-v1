import os as _os
"""Round 10 (0h/8h update): 7-day block bootstrap (B=5000, seed 7); level CI and paired difference vs a reference config. Aggregates only."""
import numpy as np, pandas as pd, os
from r10_boot import daily, boot
O = (_os.environ.get("SIGNALS_ROOT", ".") + "/out/")
def kk(k): return "" if k == 4 else f"_k{k}"
R = {"c48": "", "c0": "_c0", "c8": "_c8", "c12": "_c12", "c24": "_c24", "x2a": "_x2a", "x2b": "_x2b"}
pairs = []   # (S, fix, ref)
for S in (10, 20):
    for k in (0, 2, 4, 6):
        for r, tok in R.items():
            fix = "cons" + tok + kk(k)
            for ref_r in ("c48", "c0"):
                if r != ref_r: pairs.append((S, fix, "cons" + R[ref_r] + kk(k)))
            if r == "c0": pairs.append((S, fix, None))
    for k in (1, 3, 5, 7, 8, 9, 10, 11, 12): pairs.append((S, f"cons_c0_k{k}", None))
    for fx, ref in (("consM_c0", "cons_c0"), ("consI_c0", "cons_c0"), ("consI_c0_k2", "cons_c0_k2"), ("consM_c0_k2", "cons_c0_k2"), ("consM_c0_k6", "cons_c0_k6"),
                    ("cons_c0_dS", "cons_c0"), ("cons_c0_dP", "cons_c0"), ("cons_c0_r1", "cons_c0"), ("cons_c0_r5", "cons_c0"), ("cons_c0_r10", "cons_c0"), ("allC_c0", "cons_c0"), ("allC_c0_k0", "cons_c0_k0")):
        pairs.append((S, fx, ref))
rows = []; cache = {}
for S, fix, ref in pairs:
    for w in ("IS", "HO", "FY"):
        try: d = daily(S, fix, w); r_ = daily(S, ref, w) if ref else None
        except FileNotFoundError: continue
        key = (S, fix, w)
        if key not in cache: cache[key] = boot(d, S)
        m, lo, hi, p = cache[key]
        dm, dlo, dhi = (boot(d - r_, S)[:3] if ref else (np.nan,) * 3)
        rows.append(dict(S=S, win=w, fix=fix, ref=ref or "", ann=m, lo=lo, hi=hi, d=dm, dlo=dlo, dhi=dhi, net_wan=d.sum() / 1e4))
df = pd.DataFrame(rows); df.to_csv(O + "r10_bootstrap2.csv", index=False); print(len(df))
