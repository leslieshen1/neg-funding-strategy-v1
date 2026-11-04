import os as _os
"""Round 11: event-definition variants (X5 24h cumulative turns positive vs X8 single settlement >= 0) x exit candidates x k; FY hourly pnl + per-coin net. Aggregates only."""
import sys, os, time; ARGV = list(sys.argv); sys.path.insert(0, (_os.environ.get("SIGNALS_ROOT", ".") + "/code"))
import r10_run as R10
import r9_run as R9
from r9_run import *
_g = R9.getfix
def getfix11(name):
    t = name.split("_"); e8 = "e8" in t; f = _g("_".join(x for x in t if x != "e8"))
    if e8: f["xmode"] = 8.0
    return f
R9.getfix = getfix11
O11 = OUT + "r11/"; os.makedirs(O11, exist_ok=True)
def job(a):
    fix, win = a; t0 = time.time(); r = R9.run9(fix, win); o = RR.metrics(r, save=None)
    cum = np.concatenate([[0.0], r["cum"]]); np.save(O11 + f"S{int(S/1e6)}M__{fix}__{win}.npy", np.diff(cum))
    ep = r["ep"]; pc = np.zeros(D.N)
    if len(ep): np.add.at(pc, ep[:, 0].astype(int), ep[:, 3] - ep[:, 6])
    np.save(O11 + f"S{int(S/1e6)}M__{fix}__{win}__coin.npy", pc)
    return dict(fix=fix, win=win, ann=o["ann10"], net_u=o["net_u"], episodes=o["episodes"], ep_net_sum=float(pc.sum()), sec=time.time() - t0)
if __name__ == "__main__":
    fixes = ARGV[1].split(","); wins = ARGV[2].split(","); nw = int(ARGV[3]); tag = ARGV[4]
    with mp.get_context("fork").Pool(nw) as p: rows = p.map(job, [(f, w) for f in fixes for w in wins], chunksize=1)
    df = pd.DataFrame(rows); df.to_csv(OUT + f"r11_{tag}_S{int(S/1e6)}M.csv", index=False); print(df.round(2).to_string())
