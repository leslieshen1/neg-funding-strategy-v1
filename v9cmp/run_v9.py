import os as _os
"""v9 engine (unmodified public repo @dbe839a, read-only) run under the round-7 settings: S, windows, cap file, pool. Aggregates only (nothing per coin written)."""
import sys, os, json, numpy as np, pandas as pd, multiprocessing as mp
V9 = _os.environ.get("V9_REPO", "./upstream/v9/repo"); sys.path.insert(0, V9); os.chdir(V9)
import config as C, run_backtest as R
OUT = (_os.environ.get("SIGNALS_ROOT", ".") + "/v9cmp/out/")
C.WINDOWS.update({"IS": ("2025-10-28", "2026-07-01"), "HO": ("2026-07-01", "2026-10-28")})
D = R.Data(C.data_dir(_os.environ.get("V9_DATA", "./upstream/v9/data"))); ok = R.load_ok(D)
CAPF = {"v11": _os.environ["NFB_HOLDINGS_CAP"], "v9": _os.environ["NFB_HOLDINGS_CAP_V9"]}
VARS = {"V9_real": dict(imp=30, k=4.0, lag=1, pov=0.20), "V9_opt": dict(imp=20, k=0.0, lag=0, pov=0.20),
        "V9_real_pov3": dict(imp=30, k=4.0, lag=1, pov=0.03), "V9_real_k0": dict(imp=30, k=0.0, lag=1, pov=0.20), "V9_lag0_30_k4": dict(imp=30, k=4.0, lag=0, pov=0.20)}
def one(a):
    var, S, win, capn = a; v = VARS[var]
    cap = R.make_cap(D, ok, S, "holdings", CAPF[capn])
    P = R.base_params(v["imp"], k_imp=v["k"], pov=v["pov"])
    r = D.run(win, S, ok, cap, P, oi_extra_lag_h=v["lag"]); m = R.metrics(r)
    cum = np.concatenate([[0.0], r["cum"]]); H = len(cum) - 1; y = H / 8760.0; ep = r["ep"]; net = cum[-1]; dg = r["diag"]
    o = dict(var=var, S=S, win=win, cap=capn, days=H / 24, net_u=net, episodes=int(r["episodes"]), funding_u=r["funding"], fees_u=-r["fees"], slip_u=-r["cost"], traded_u=r["traded"],
             peak_cost_used_u=dg[12], peak_mtm_used_u=dg[13], avg_mtm_used_u=float(r["used"].mean()), volcap_hours=dg[0], oicap_hours=dg[1], held_hours=dg[11],
             fills=int(r["fills"]), fills_over_same_hour_pov=int(dg[6]), ann10=net / S / y * 100)
    o["ann_pkc"] = net / o["peak_cost_used_u"] / y * 100; o["ann_pkm"] = net / o["peak_mtm_used_u"] / y * 100
    o["basis_u"] = net - o["funding_u"] - o["fees_u"] - o["slip_u"]; o["volcap_pct"] = 100 * dg[0] / dg[11] if dg[11] > 0 else np.nan
    if len(ep):
        dur = ep[:, 2] - ep[:, 1]; en = ep[:, 3] - ep[:, 6]
        for nm, lo, hi in (("lt24", 0, 24), ("d24_72", 24, 72), ("d72_168", 72, 168), ("gt168", 168, 1e18)):
            mm = (dur >= lo) & (dur < hi); o[f"n_{nm}"] = int(mm.sum()); o[f"net_{nm}_u"] = float(en[mm].sum())
        cp = np.bincount(ep[:, 0].astype(int), weights=en, minlength=D.N); top = np.sort(cp)[::-1][:5]
        o["ex5_ann"] = float(cp.sum() - top.sum()) / S / y * 100; o["avg_hold_h"] = float(dur.mean()); o["coins_traded"] = int((np.bincount(ep[:, 0].astype(int), minlength=D.N) > 0).sum())
    if S == 1e7: np.save(OUT + f"daily/{var}__{capn}__{win}.npy", np.diff(cum))
    return o
if __name__ == "__main__":
    step = sys.argv[1]
    if step == "repro":   # S=70M, 1y/6m, A (both cap files) and B -> compare with v9 report (A 8.38/5.03, B 10.50/7.12 realistic; 20.43/11.64, 17.45/11.99 optimistic)
        rows = []
        for var in ("V9_real", "V9_opt"):
            for capn in ("v9", "v11"):
                for w in ("1y", "6m"):
                    o = one((var, 7e7, w, capn)); rows.append(o); print(var, capn, w, round(o["ann10"], 2), round(o["net_u"] / 1e4, 1), flush=True)
        pd.DataFrame(rows).to_csv(OUT + "v9_repro_70M.csv", index=False)
    else:
        jobs = [(v, 1e7, w, "v11") for v in VARS for w in ("IS", "HO")]
        with mp.get_context("fork").Pool(8) as p: rows = p.map(one, jobs)
        pd.DataFrame(rows).to_csv(OUT + "v9_10M.csv", index=False); print(pd.DataFrame(rows)[["var", "win", "ann10", "ann_pkc", "ann_pkm", "episodes", "volcap_pct"]].to_string())
