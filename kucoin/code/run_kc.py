import os as _os
"""KuCoin spot + Binance perp variant: frozen round-7 rule + v9 rule, same engine (fixed forced-de-risk), same denominators/windows. Aggregates only."""
import os, sys
KC = (_os.environ.get("SIGNALS_ROOT", ".") + "/kucoin/")
os.environ["NFB_DS_DIR"] = KC + "ds"; os.environ.setdefault("NFB_DERISK", "2")
sys.path.insert(0, (_os.environ.get("SIGNALS_ROOT", ".") + "/code")); sys.path.insert(0, KC + "code")
import run_r7 as RR
os.makedirs(KC + "out/daily", exist_ok=True); RR.OUT7 = KC + "out/daily/"
from run_r7 import *
import run_r7_v9cmp as VC, r7_v9bridge as BR
import numpy as np, pandas as pd, multiprocessing as mp
from margin import margin_stats, ffill0
meta = pd.read_csv(KC + "ds/dataset_meta.csv"); KEEP = meta.kc_keep.to_numpy()
RR.D.fsm = meta.fsm.to_numpy(float).copy(); assert np.isfinite(RR.D.fsm).all() and (RR.D.fsm >= 1).all()
OKS = {}
for gk in (("r7", 2.0), "old", "none"): OKS[gk] = VC.make_ok(gk, "cal")                    # gates fixed BEFORE any sensitivity mutation (realised-cost sensitivities only)
VC.make_ok = lambda gk, scen: OKS[gk]
x = XA["cal"][0].copy(); x[0] = x[0] * 1.5; XA["calY15"] = (x, None, None)
def rows_for(tag, jobs, n=8):
    with mp.get_context("fork").Pool(n) as p: rows = p.map(VC.job2, jobs, chunksize=1)
    df = pd.DataFrame(rows); df["tag"] = tag; return df
if __name__ == "__main__":
    out = []
    SKIP = os.environ.get('KC_SKIP_MAIN') == '1'
    if not SKIP:
        # main grid, pools 339(=all KuCoin-listed of the 339) and 267
        jobs = [(k, s, w, p) for p in (267, 339) for k in ("REF_ADL", "FINAL", "NOGATE24", "OLDGATE24") for s in ("bp30", "cal") for w in ("IS", "HO")]
        out.append(rows_for("main", jobs))
        # v9 native config on KuCoin data
        with mp.get_context("fork").Pool(4) as p: v9 = p.map(BR.jb, [("S0_v9like", w, pl) for w in ("IS", "HO") for pl in (267, 339)])
        d9 = pd.DataFrame(v9); d9["cfg"] = "V9_native_cfg"; d9["scen"] = "bp30"; d9["tag"] = "main"; d9["pool"] = d9["pool"]; out.append(d9)
        pd.concat(out).to_csv(KC + "out/kc_main.csv", index=False); print("main done", flush=True)
    # sensitivities (pool 339, FINAL, cal): realised cost only
    SKS = os.environ.get('KC_SKIP_SENS') == '1'
    sens = []; base_fsm = RR.D.fsm.copy(); base_hs = RR.D.hs_s.copy()
    for nm, fm, hm, sc in (("fee_x0.8_KCS", 0.8, 1.0, "cal"), ("fee_x2_classB", 2.0, 1.0, "cal"), ("Y_x1.5", 1.0, 1.0, "calY15"), ("hs_s_x2", 1.0, 2.0, "cal")):
        RR.D.fsm = base_fsm * fm; RR.D.hs_s = base_hs * hm
        df = rows_for(nm, [("FINAL", sc, w, 339) for w in ("IS", "HO")] + ([("REF_ADL", "cal", w, 339) for w in ("IS", "HO")] if sc == "cal" else [])); sens.append(df)
    RR.D.fsm = base_fsm; RR.D.hs_s = base_hs
    pd.concat(sens).to_csv(KC + "out/kc_sens.csv", index=False); print("sens done", flush=True)
    # fill check + margin on FINAL / REF cal, pool 339
    mrows = []; fchk = []
    z = np.load(KC + "ds/dataset.npz"); fcP = z["fc"]; flP = z["fl"]; scP = z["sc"]; shP = z["sh"]; svP = z["sv"]
    for kind in ("FINAL", "REF_ADL"):
        for w in ("IS", "HO"):
            r = VC.run_any(kind, "cal", w, 339); h0, h1 = RR.WINS[w]; pos = r["pos"]
            miss = ~(svP[h0:h1] > 0); SF = ffill0(scP[h0:h1]); qq = np.abs(pos) / np.where(np.isfinite(SF) & (SF > 0), SF, np.inf)   # pos = qty x last spot close -> recover qty
            qprev = np.vstack([np.zeros((1, qq.shape[1])), qq[:-1]]); d = np.abs(qq - qprev) > 1e-9 * np.maximum(qq, qprev) + 1e-12
            fchk.append(dict(cfg=kind, win=w, fills_in_missing_kucoin_hours=int((d & miss).sum()), coin_hours_no_trade_or_absent=int((miss & KEEP[None, :]).sum()), coin_hours_absent_candle=int((~np.isfinite(scP[h0:h1]) & KEEP[None, :]).sum()), pos_changes=int(d.sum())))
            fhP = z["fh"][h0:h1]; shF = np.minimum(shP[h0:h1], 1.2 * np.fmax(np.fmax(fhP, fcP[h0:h1]), 0))   # glitch filter: spot high capped at 1.2x the Binance perp high (KuCoin has a few bad highs, e.g. 100x wicks)
            shF = np.where(np.isfinite(shF), shF, shP[h0:h1])
            for var, shx in (("raw", shP[h0:h1]), ("glitch_filtered", shF)):
                m = margin_stats(pos, scP[h0:h1], shx, fcP[h0:h1], flP[h0:h1], S); m.update(cfg=kind, win=w, variant=var); mrows.append(m)
    pd.DataFrame(fchk).to_csv(KC + "out/kc_fillcheck.csv", index=False); pd.DataFrame(mrows).to_csv(KC + "out/kc_margin.csv", index=False); print(pd.DataFrame(fchk)); print("margin done", flush=True)
