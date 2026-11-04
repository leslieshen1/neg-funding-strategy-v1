import os as _os
import sys; sys.path.insert(0, (_os.environ.get("SIGNALS_ROOT", ".") + "/code"))
import numpy as np, pandas as pd, json
from run_signals import D, sum24, S, T, N
from run_adapt import A0, A_IS, A1
from lib12s import cap_vec
O = (_os.environ.get("SIGNALS_ROOT", ".") + "/out/"); R = O + "r11/"
RULES = ["_c0", "_cns", "_c12", "_c24", "", "_x2a", "_x2b"]          # simplicity / length order
LAB = {"_c0": "0h", "_cns": "next-settle(~9h)", "_c12": "12h", "_c24": "24h", "": "48h", "_x2a": "2stage-A", "_x2b": "2stage-B"}
KS = {"0": "_k0", "2": "_k2", "4": "", "6": "_k6"}; EVS = {"X5": "", "X8": "_e8"}
fx = lambda r, k, e: "cons" + r + KS[k] + EVS[e]
hr = lambda f, w="FY": np.load(R + f"S10M__{f}__{w}.npy")
def daily(x): k = len(x) // 24 * 24; return x[:k].reshape(-1, 24).sum(1)
def boot(d, blk=7, B=5000, seed=7):
    n = len(d); rng = np.random.default_rng(seed); nb = int(np.ceil(n / blk)); out = np.empty(B)
    for i in range(B):
        st = rng.integers(0, n, nb); idx = ((st[:, None] + np.arange(blk)[None, :]) % n).reshape(-1)[:n]; out[i] = d[idx].sum()
    f = 100.0 / S / (n / 365.0); return d.sum() * f, np.quantile(out, .025) * f, np.quantile(out, .975) * f
# 1) paired diff vs 0h
rows = []
for e in EVS:
    for k in KS:
        for w in ("IS", "HO", "FY"):
            ref = daily(hr(fx("_c0", k, e), w))
            for r in RULES:
                d = daily(hr(fx(r, k, e), w)); a = d.sum() * 100 / S / (len(d) / 365)
                dm, lo, hi = boot(d - ref) if r != "_c0" else (0, 0, 0)
                rows.append(dict(ev=e, k=k, win=w, rule=LAB[r], ann=a, d_vs0=dm, d_lo=lo, d_hi=hi))
B = pd.DataFrame(rows); B.to_csv(O + "r11_paired.csv", index=False)
# 2) walk-forward
def pick(anns):
    best = max(anns.values()); return next(r for r in RULES if anns[r] >= best - 2.0)
wf = []
for nseg in (4, 6):
    H = A1 - A0; edges = np.linspace(0, H, nseg + 1).astype(int)
    for e in EVS:
        for k in KS:
            P = {r: hr(fx(r, k, e)) for r in RULES}
            ann = lambda x, a, b: x[a:b].sum() * 100 / S / ((b - a) / 8760)
            for j in range(1, nseg):
                tr = {r: ann(P[r], 0, edges[j]) for r in RULES}; te = {r: ann(P[r], edges[j], edges[j + 1]) for r in RULES}
                ch = pick(tr); bt = max(te, key=te.get)
                wf.append(dict(nseg=nseg, ev=e, k=k, seg=j + 1, chosen=LAB[ch], test_best=LAB[bt], chosen_test=te[ch], c0_test=te["_c0"], c0_best=bt == "_c0", c0_beats_cns=te["_c0"] > te["_cns"], c0_beats_12=te["_c0"] > te["_c12"], c0_beats_48=te["_c0"] > te[""], **{"t_" + LAB[r]: te[r] for r in RULES}))
W = pd.DataFrame(wf); W.to_csv(O + "r11_walkforward.csv", index=False)
# 3) size buckets (per-coin FY net, by FY mean 24h volume tertile and mean OI tertile among tradeable coins)
cap = cap_vec(D, S); tr_ = cap > 0
vol = np.nanmean(np.where(D.dv[A0:A1] > 0, D.dv[A0:A1], np.nan), 0); oi = np.nanmean(D.oih[A0:A1] * np.where(D.arr[4][A0:A1] > 0, D.arr[4][A0:A1], np.nan), 0)
def tert(x):
    q = np.nanquantile(x[tr_], [1 / 3, 2 / 3]); g = np.where(x <= q[0], "S", np.where(x <= q[1], "M", "L")); g[~tr_] = "-"; g[~np.isfinite(x)] = "-"; return g
G = {"vol": tert(vol), "oi": tert(oi)}
br = []
for e in EVS:
    for k in KS:
        for r in RULES:
            pc = np.load(R + f"S10M__{fx(r, k, e)}__FY__coin.npy")
            for gn, g in G.items():
                for b in "SML": br.append(dict(ev=e, k=k, rule=LAB[r], by=gn, bucket=b, n_coins=int((g == b).sum()), net_wan=pc[g == b].sum() / 1e4))
BB = pd.DataFrame(br); BB.to_csv(O + "r11_buckets.csv", index=False)
# 4) event study: after the exit event, how often does it reverse within W, and funding collected over W (long perp: -rate)
ev = D.arr[6]; ivh = D.ivh()
ES = []
setl = ev != 0
for e in EVS:
    if e == "X5": cond = sum24 > 0
    else:
        last = np.full((T, N), np.nan); cur = np.full(N, np.nan)
        for t in range(T):
            m = setl[t]; cur[m] = ev[t, m]; last[t] = cur
        cond = last >= 0
    prev_neg = np.vstack([np.zeros((1, N), bool), ~cond[:-1]]); start = cond & prev_neg & np.isfinite(sum24)
    regime = np.vstack([np.zeros((24, N), bool), (sum24[:-24] < 0)])          # was in a negative-funding regime 24h earlier
    tt, nn = np.where(start[A0:A1] & regime[A0:A1] & tr_[None, :]); tt = tt + A0
    for t, n in zip(tt, nn):
        nxt = np.where(setl[t + 1:min(t + 25, T), n])[0]; wns = int(nxt[0]) + 1 if len(nxt) else 8
        for wl, W_ in (("next-settle", wns), ("12h", 12), ("24h", 24), ("48h", 48)):
            seg = slice(t + 1, min(t + 1 + W_, T)); rev = bool((~cond[seg, n]).any()); fund = -ev[seg, n].sum() * 1e4
            ES.append(dict(ev=e, W=wl, Wh=W_, vol=G["vol"][n], oi=G["oi"][n], rev=rev, fund_bp=fund))
E_ = pd.DataFrame(ES); E_.to_pickle(O + "r11_events.pkl")
def es(gcol):
    return E_.groupby(["ev", gcol, "W"]).agg(n=("rev", "size"), p_reverse=("rev", "mean"), mean_fund_bp=("fund_bp", "mean"), med_fund_bp=("fund_bp", "median")).reset_index()
pd.concat([es("vol").rename(columns={"vol": "bucket"}).assign(by="vol"), es("oi").rename(columns={"oi": "bucket"}).assign(by="oi"),
           E_.assign(all="ALL").groupby(["ev", "all", "W"]).agg(n=("rev", "size"), p_reverse=("rev", "mean"), mean_fund_bp=("fund_bp", "mean"), med_fund_bp=("fund_bp", "median")).reset_index().rename(columns={"all": "bucket"}).assign(by="all")]).to_csv(O + "r11_eventstudy.csv", index=False)
print("done")
