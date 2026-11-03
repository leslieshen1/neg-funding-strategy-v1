import os as _os
"""v9-rule vs round-7-final under IDENTICAL settings in the round-7 engine (10M, inventory A, same pool/windows/cap file/costs/hard caps). Aggregates only."""
import sys; sys.argv = ["x"]
sys.path.insert(0, (_os.environ.get("SIGNALS_ROOT", ".") + "/code"))
from run_r7 import *
v9m = pd.read_csv(_os.environ.get("V9_DATA", "./upstream/v9/data") + "/dataset_meta.csv"); P267 = np.array([f in set(v9m.fut) for f in D.fut]); P339 = np.ones(N, bool)
print("pool267", P267.sum(), "pool339", P339.sum(), flush=True)
def run_any(kind, scen, win, pool):
    pm = (P267 if pool == 267 else P339)[None, :]
    if kind in ("REF_ADL", "REF_noADL"):
        ok = (~ADL_MASK if kind == "REF_ADL" else np.ones((T, N), bool)) & pm
        ex = dict(FIXED); ex["x_obs"] = 1.0; ex["derisk_force"] = DF
        if scen == "bp30": xa = None
        else: ex.update(sqrt_y=1.0, cutb_sqrt=1.0, use_xa=1.0, derisk_force=DF); xa = XA["cal"][0]
        return run(D, S, ok_t=ok, extra=ex, imp=30, dl_stop=False, advmode=1.0, s24=sum24, hw=WINS[win], same_hour=True, xa=xa, **MODES["i"])
    spec = {"FINAL": (("r7", 2.0), {"conf_h": 48.0}), "FINAL24": (("r7", 2.0), {"conf_h": 24.0}), "OLDGATE24": ("old", {"conf_h": 24.0}), "NOGATE24": ("none", {"conf_h": 24.0})}[kind]
    gk, exx = spec
    # run_cfg builds ok internally; replicate it with the pool mask
    ok = make_ok(gk, scen) & pm; ex = dict(BASEX); ex.update(exx)
    if scen == "bp30": ex["derisk_force"] = DF; xa = None
    else: ex.update(derisk_force=DF, sqrt_y=1.0, cutb_sqrt=1.0, use_xa=1.0); xa = XA[scen][0]
    return run(D, S, ok_t=ok, extra=ex, imp=30, dl_stop=False, advmode=1.0, s24=sum24, hw=WINS[win], same_hour=True, xa=xa, **MODES["i"])
def job2(a):
    kind, scen, win, pool = a
    r = run_any(kind, scen, win, pool); o = metrics(r, save=f"v9cmp_{kind}_{pool}__{scen}__{win}"); o.update(cfg=kind, scen=scen, win=win, pool=pool); return o
if __name__ == "__main__":
    jobs = [(k, s, w, p) for p in (267, 339) for k in ("REF_ADL", "REF_noADL", "OLDGATE24", "NOGATE24", "FINAL24", "FINAL") for s in ("bp30", "cal") for w in ("IS", "HO")]
    with mp.get_context("fork").Pool(8) as p: rows = p.map(job2, jobs, chunksize=1)
    df = pd.DataFrame(rows); df.to_csv(OUT + "r7_v9cmp.csv", index=False)
    print(df[["cfg", "pool", "scen", "win", "ann10", "ann_pkc", "ann_pkm", "episodes", "volcap_pct"]].round(1).to_string())
