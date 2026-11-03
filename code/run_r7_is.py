import os as _os
"""Round 7 IS stage (window 2025-10-28 -> 2026-06-30 only). Step 1: gate grid; step 2: exit grids; writes out/r7_is_*.csv. No holdout here."""
import sys; sys.path.insert(0, (_os.environ.get("SIGNALS_ROOT", ".") + "/code"))
ARGV = list(sys.argv)
import run_r7 as R
import numpy as np
import pandas as pd, json, time, os
OUT = R.OUT
step = ARGV[1]
t0 = time.time()
WIN = ARGV[2] if len(ARGV) > 2 else "IS"
if step == "calib_check":                     # aggregates only
    ys = np.array([r[2] for r in R.CRAW[0]]) if False else None
if step == "gate":
    MS = [1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 6.0]
    J = [("base_nogate", "none", {}, "cal", WIN), ("old_gate_m3", "old", {}, "cal", WIN)]
    for m in MS:
        J.append((f"r7f_m{m}", ("r7f", m), {}, "cal", WIN)); J.append((f"r7fb_m{m}", ("r7", m), {}, "cal", WIN))
    res = R.pool_run(J, 8); df = pd.DataFrame(res); df.to_csv(OUT + "r7_%s_gate.csv" % ("is" if WIN == "IS" else "ho"), index=False)
    print(df[["cfg", "net_u", "ann10", "ann_pkc", "episodes", "volcap_pct", "avg_hold_h"]].to_string())
if step == "exits":
    g = json.load(open(OUT + "r7_gate_choice.json")); gs = (g["kind"], g["m"])
    J = []
    for c in (6, 12, 24, 48, 72, 120): J.append((f"X5_c{c}", gs, dict(conf_h=float(c)), "cal", WIN))
    for k in (0.05, 0.1, 0.25, 0.5, 1.0, 1.5, 2.0, 3.0):
        for h in (3, 6, 12, 24):
            J.append((f"EV_k{k}_h{h}", gs, dict(xmode=0.0, x_ev_k=k, x_ev_h=float(h)), "cal", WIN))
    for a in (0.003, 0.006, 0.010, 0.015, 0.025, 0.04, 0.06):
        for gb in (0.002, 0.004, 0.008, 0.012, 0.020):
            J.append((f"TP_a{a}_gb{gb}", gs, dict(x_tp_act=a, x_tp_gb=gb), "cal", WIN))
    for f in (0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0):
        J.append((f"BR_f{f}", gs, dict(x_br_fr=f), "cal", WIN))
    for mh in (24, 48, 96, 168, 336, 504, 720):
        J.append((f"TIME_h{mh}", gs, dict(xmode=0.0, max_hold_h=float(mh), sch_mode=1.0, sch_w=12.0), "cal", WIN))
    res = R.pool_run(J, 8); df = pd.DataFrame(res); df.to_csv(OUT + "r7_%s_exits_ext.csv" % ("is" if WIN == "IS" else "ho"), index=False)
    print(df[["cfg", "net_u", "ann10", "ann_pkc", "episodes", "avg_hold_h", "volcap_pct"]].to_string())
print("elapsed", time.time() - t0)

if step == "scen":
    FR = dict(conf_h=48.0); B24 = dict(conf_h=24.0)
    cf = {"frozen_m2fb_c48": (("r7", 2.0), FR), "newgate_c24": (("r7", 2.0), B24), "oldgate_c24": ("old", B24), "nogate_c24": ("none", B24)}
    J = []
    for w in ("IS", "HO"):
        for sc in ("cal", "book", "sqrt1", "bp30") + (("bp30c",) if os.environ.get("NFB_DERISK") == "1" else ()):
            for nm, (g, e) in cf.items(): J.append((nm, g, e, sc, w))
    res = R.pool_run(J, 8); df = pd.DataFrame(res); df.to_csv(OUT + "r7_scen.csv", index=False)
    print(df[["cfg", "scen", "win", "net_u", "ann10", "ann_pkc", "ann_pkm", "ex5_ann", "volcap_pct"]].round(2).to_string())
