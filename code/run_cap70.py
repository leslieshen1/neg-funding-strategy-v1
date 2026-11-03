import os as _os
import sys; sys.path.insert(0, (_os.environ.get("SIGNALS_ROOT", ".") + "/code"))
from run_adapt import *
RULESC = {"adaptive_m3_c24": (3, 24), "fixed_E7X5": (0, 1)}
SC = {"imp20": dict(imp=20), "imp30": dict(imp=30), "imp50": dict(imp=50), "sqrt1": dict(imp=30, extra=dict(sqrt_y=1.0)), "sqrt2": dict(imp=30, extra=dict(sqrt_y=2.0))}
WINS = {"IS": (A0, A_IS), "HO": (A_IS, A1)}
def job(a):
    cap, rn, sc, w = a; m, conf = RULESC[rn]; hw = WINS[w]; kw = dict(SC[sc])
    ok = ~ADL_MASK & gate(m, conf)
    ex = dict(ENTRY["E7"]); ex.update(EXIT["X5"]); ex.update(FIXED); ex["x_obs"] = 1.0
    if conf > 1: ex["conf_h"] = float(conf)
    ex.update(kw.get("extra", {}))
    r = run(D, cap, ok_t=ok, extra=ex, imp=kw["imp"], dl_stop=False, advmode=1.0, s24=sum24, hw=hw, same_hour=True, **MODES["i"])
    cum = np.concatenate([[0.0], r["cum"]]); H = len(cum) - 1; y = H / 8760.0; ep = r["ep"]
    o = dict(cap=cap, rule=rn, scen=sc, win=w, net_u=cum[-1], ann=cum[-1] / cap / y * 100, episodes=int(r["episodes"]))
    if len(ep):
        net = ep[:, 3] - ep[:, 6]; cp = np.bincount(ep[:, 0].astype(int), weights=net, minlength=N); top = np.sort(cp)[::-1][:5]
        o["ex5_u"] = float(cp.sum() - top.sum()); o["ex5_ann"] = o["ex5_u"] / cap / y * 100; o["top5_share"] = float(top.sum() / cp.sum() * 100) if cp.sum() else np.nan
        o["n_coins"] = int((np.abs(cp) > 0).sum())
    dg = r["diag"]; o["avg_cost_used_u"] = dg[15] / H; o["peak_cost_used_u"] = dg[12]; o["avg_mtm_used_u"] = float(r["used"].mean()); o["peak_mtm_used_u"] = dg[13]
    x = r["xd"]
    for i, nm in enumerate(["inv", "oi", "vol", "pov", "capital"]): o[f"bind_{nm}"] = float(x[i])
    o["cand_hours"] = float(x[15]); o["filled_notional"] = float(x[16])
    return o
if __name__ == "__main__":
    jobs = [(cap, rn, sc, w) for cap in (1e7, 7e7) for rn in RULESC for sc in SC for w in WINS]
    with mp.get_context("fork").Pool(8) as p: res = p.map(job, jobs)
    df = pd.DataFrame(res); df.to_csv(OUT + "cap70.csv", index=False)
    print(df[["cap","rule","scen","win","ann","net_u","ex5_ann","episodes"]].round(1).to_string())
