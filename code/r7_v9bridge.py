import os as _os
"""Engine-equivalence + bridge: our engine (v12s) running the v9 rule with v9-style execution knobs, step by step towards the round-7 environment. Aggregates only."""
import sys; sys.argv = ["x"]
sys.path.insert(0, (_os.environ.get("SIGNALS_ROOT", ".") + "/code"))
from run_r7_v9cmp import *
STEPS = [  # name, extra overrides, same_hour, adl, xobs
 ("S0_v9like", dict(pov=0.20, derisk_force=0), False, False, 0.0),
 ("S0b_v9like_xobs1", dict(pov=0.20, derisk_force=0), False, False, 1.0),
 ("S1_samehour", dict(pov=0.20, derisk_force=0), True, False, 1.0),
 ("S2_pov3", dict(pov=0.03, derisk_force=0), True, False, 1.0),
 ("S3_hardcap", dict(pov=0.03, derisk_force=DF), True, False, 1.0),
 ("S4_adl", dict(pov=0.03, derisk_force=DF), True, True, 1.0)]
def jb(a):
    nm, win, pool = a; _, ex_o, sh, adl, xo = [s for s in STEPS if s[0] == nm][0]
    pm = (P267 if pool == 267 else P339)[None, :]; ok = (~ADL_MASK if adl else np.ones((T, N), bool)) & pm
    ex = dict(FIXED); ex["x_obs"] = xo; ex.update(ex_o)
    r = run(D, S, ok_t=ok, extra=ex, imp=30, dl_stop=False, advmode=1.0, s24=sum24, hw=WINS[win], same_hour=sh, xa=None, **MODES["i"])
    o = metrics(r, save=f"v9bridge_{nm}_{pool}__bp30__{win}"); o.update(step=nm, win=win, pool=pool); return o
if __name__ == "__main__":
    jobs = [(s[0], w, 267) for s in STEPS for w in ("IS", "HO")]
    with mp.get_context("fork").Pool(8) as p: rows = p.map(jb, jobs, chunksize=1)
    df = pd.DataFrame(rows); df.to_csv(OUT + "r7_v9bridge.csv", index=False)
    print(df[["step", "win", "ann10", "ann_pkc", "ann_pkm", "episodes", "volcap_pct"]].round(1).to_string())
