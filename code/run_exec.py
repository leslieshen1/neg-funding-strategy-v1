import os as _os
"""Round 6: execution-mode comparison on the frozen adaptive rule (m=3, conf_h=24), 10M, derisk_force=1. Aggregates only."""
import sys; sys.path.insert(0, (_os.environ.get("SIGNALS_ROOT", ".") + "/code"))
from run_adapt import *
SC = {"bp30": dict(imp=30, extra=dict(derisk_force=1.0)), "sqrt1": dict(imp=30, extra=dict(derisk_force=1.0, sqrt_y=1.0, cutb_sqrt=1.0))}
WINS = {"IS": (A0, A_IS), "HO": (A_IS, A1)}
CF = {}   # name -> dict(mode, mk=dict(...), extra=dict(...))
CF["M1_taker"] = dict(mode="1 taker", mk=dict(mkm=0), extra={})
HX = dict(hx_off=1.0, gap_sym=2.0)
for f in (0.3, 0.6, 0.9):
    t = int(f * 100)
    for aw in (0.0, 1.0, 2.0):      # mkm=2 (both legs maker, same fill rate), PAIR-basis adverse selection, weight 0/1/2
        CF[f"M2_both_f{t}_advB{aw:g}"] = dict(mode="2 hybrid both-maker", mk=dict(mkm=2, pen=0.0, fshare=f, advw=aw, advmode=2.0), extra=dict(HX))
    CF[f"M2_both_f{t}_advO1"] = dict(mode="2 hybrid both-maker, outright adv", mk=dict(mkm=2, pen=0.0, fshare=f, advw=1.0, advmode=1.0), extra=dict(HX))
    CF[f"M2_both_f{t}_gapsym"] = dict(mode="2 hybrid both-maker, gap symmetric", mk=dict(mkm=2, pen=0.0, fshare=f, advw=1.0, advmode=2.0), extra=dict(hx_off=1.0, gap_sym=1.0))
    CF[f"M2_both_f{t}_pen"] = dict(mode="2 hybrid both-maker, trade-through 0.2%", mk=dict(mkm=2, pen=0.002, fshare=f, advw=1.0, advmode=2.0), extra=dict(HX))
    for aw in (0.0, 1.0):           # mkm=1 (perp passive, spot taker hedge), outright adverse move of the maker leg to next close
        CF[f"M2_one_f{t}_adv{aw:g}"] = dict(mode="2 hybrid one-maker", mk=dict(mkm=1, pen=0.0, fshare=f, advw=aw, advmode=0.0), extra=dict(HX))
for nm, sm in (("TWAP", 1.0), ("VWAP", 2.0)):
    for w in (6, 12, 24): CF[f"M3_{nm}_{w}h"] = dict(mode=f"3 {nm}", mk=dict(mkm=0), extra=dict(sch_mode=sm, sch_w=float(w)))

def job(a):
    cn, sc, w = a; c = CF[cn]; hw = WINS[w]; s = SC[sc]
    ok = ~ADL_MASK & gate(3, 24)
    ex = dict(ENTRY["E7"]); ex.update(EXIT["X5"]); ex.update(FIXED); ex["x_obs"] = 1.0; ex["conf_h"] = 24.0
    ex.update(s["extra"]); ex.update(c["extra"])
    mk = dict(c["mk"]); mk.setdefault("advmode", 1.0)
    r = run(D, S, ok_t=ok, extra=ex, imp=s["imp"], dl_stop=False, s24=sum24, hw=hw, same_hour=True, **mk)
    cum = np.concatenate([[0.0], r["cum"]]); H = len(cum) - 1; y = H / 8760.0; ep = r["ep"]; net = cum[-1]
    dg = r["diag"]; x = r["xd"]
    o = dict(cfg=cn, mode=c["mode"], scen=sc, win=w, days=H / 24, net_u=net, episodes=int(r["episodes"]), fills=int(r["fills"]),
             funding_u=r["funding"], fees_u=-r["fees"], slip_u=-r["cost"], chk=net - (r["price"] + r["funding"] - r["fees"]),
             traded_u=r["traded"], avg_cost_used_u=dg[15] / H, peak_cost_used_u=dg[12], avg_mtm_used_u=float(r["used"].mean()), peak_mtm_used_u=dg[13],
             mk_att=x[30], mk_elig=x[31], mk_pair_u=x[32], mk_defer_u=x[33], tk_next_u=x[34], gap_u=x[35], adv_u=x[36], hx_u=x[37], mk_entry_u=x[38], mk_exit_u=x[39],
             liq_resid_u=x[41], liq_cost_u=x[42])
    o["ann10"] = net / S / y * 100
    o["ann_pkc"] = net / o["peak_cost_used_u"] / y * 100 if o["peak_cost_used_u"] > 0 else np.nan
    o["ann_pkm"] = net / o["peak_mtm_used_u"] / y * 100 if o["peak_mtm_used_u"] > 0 else np.nan
    o["basis_u"] = net - o["funding_u"] - o["fees_u"] - o["slip_u"]
    if len(ep):
        dur = ep[:, 2] - ep[:, 1]; en = ep[:, 3] - ep[:, 6]; cp = np.bincount(ep[:, 0].astype(int), weights=en, minlength=N); top = np.sort(cp)[::-1][:5]
        o["ex5_ann"] = float(cp.sum() - top.sum()) / S / y * 100; o["avg_hold_h"] = float(dur.mean())
    return o
if __name__ == "__main__":
    names = list(CF) if len(sys.argv) < 3 or sys.argv[2] == "all" else sys.argv[2].split(",")
    jobs = [(c, s, w) for c in names for s in SC for w in WINS]
    with mp.get_context("fork").Pool(8) as p: res = p.map(job, jobs, chunksize=1)
    df = pd.DataFrame(res); df.to_csv(OUT + "exec_modes.csv", index=False)
    print(df[["cfg", "scen", "win", "ann10", "ann_pkc", "net_u", "funding_u", "fees_u", "slip_u", "basis_u", "chk", "episodes"]].round(1).to_string())
