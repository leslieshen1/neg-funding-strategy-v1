import os as _os
"""Round 12: KuCoin spot + Binance perp under current headline conventions: cons (k_imp=4), 0h exit (X5: 24h cum funding turns positive), S=10M; IS/HO/FY + r10 circular 7d block bootstrap (B=5000, seed 7). Aggregates only. Binance comparison = paired with stored r11 results (out/r11/*.npy), not re-run here."""
import os, sys
KC = (_os.environ.get("SIGNALS_ROOT", ".") + "/kucoin/")
DSN = "ds"; SUB = os.environ.get("KC_SUB", ""); TAG = "_" + SUB if SUB else ""
os.environ["NFB_DS_DIR"] = KC + DSN
os.environ.setdefault("NFB_DERISK", "2"); os.environ["NFB_S"] = "1e7"
O12 = KC + f"out/r12{TAG}/"; os.makedirs(O12, exist_ok=True); os.environ["NFB_DAILY"] = O12
sys.path.insert(0, (_os.environ.get("SIGNALS_ROOT", ".") + "/code")); sys.path.insert(0, KC + "code")
import r10_run as R10, r9_run as R9
from r9_run import *
import r10_boot as B
import numpy as np, pandas as pd
meta = pd.read_csv(KC + DSN + "/dataset_meta.csv")
R9.RR.D.fsm = meta.fsm.to_numpy(float).copy(); assert np.isfinite(R9.RR.D.fsm).all()
if __name__ == "__main__":
    print("hours", A0, A_IS, A1, flush=True)
    with mp.get_context("fork").Pool(3) as p: rows = p.map(R9.job9, [("cons_c0", w) for w in ("IS", "HO", "FY")], chunksize=1)
    df = pd.DataFrame(rows); keep = [c for c in df.columns if c not in ("max_coin_ratio", "share_hours_gt1", "notional_share_gt1")]
    df[keep].to_csv(KC + f"out/r12_kc_runs{TAG}.csv", index=False)
    br = []
    for w in ("IS", "HO", "FY"):
        x = np.load(O12 + f"S10M__cons_c0__{w}.npy"); k = len(x)//24*24; d = x[:k].reshape(-1, 24).sum(1)
        m, lo, hi, pz = B.boot(d, 10); br.append(dict(win=w, days=len(d), ann=m, lo=lo, hi=hi, p_le0=pz, net_wan=d.sum()/1e4))
        bx = np.load((_os.environ.get("SIGNALS_ROOT", ".") + "/out/r11/") + f"S10M__cons_c0__{w}.npy") if os.path.exists((_os.environ.get("SIGNALS_ROOT", ".") + "/out/r11/") + f"S10M__cons_c0__{w}.npy") else None
        if bx is not None and len(bx) == len(x):
            db = bx[:k].reshape(-1, 24).sum(1); m2, l2, h2, p2 = B.boot(d - db, 10); br[-1].update(d_vs_bn=m2, d_lo=l2, d_hi=h2, bn_ann=db.sum()*100/1e7/(len(d)/365))
    bd = pd.DataFrame(br); bd.to_csv(KC + f"out/r12_kc_boot{TAG}.csv", index=False); print(bd.round(2).to_string())
    print(df[["win", "ann", "net_u", "avg_cost_used_u", "avg_mtm_used_u", "peak_mtm_u", "episodes"]].round(1).to_string())
