import os as _os
"""Conservative bound: legacy same-hour forced cut-backs (derisk_force=1) with the excess charged extrapolated sqrt also in the fixed-30bp scenario (bp30c), plus cal (sqrt already charged on whole cut). Aggregates only."""
import os; os.environ["NFB_DERISK"] = "1"
import sys; sys.path.insert(0, (_os.environ.get("SIGNALS_ROOT", ".") + "/code"))
import run_r7 as R, pandas as pd
R.OUT7 = R.OUT + "legacy_derisk1/r7_daily/"
def job(a):
    scen, win = a; r = R.run_cfg(("r7", 2.0), dict(conf_h=48.0), scen, win); o = R.metrics(r); xd = r["xd"]
    o.update(cfg="FINAL_legacycut", scen=scen, win=win, legacy_cut_u=xd[44], legacy_excess_u=xd[45], excess_share_traded=100 * xd[45] / r["traded"]); return o
if __name__ == "__main__":
    with R.mp.get_context("fork").Pool(4) as p: rows = p.map(job, [(s, w) for s in ("bp30", "bp30c", "cal") for w in ("IS", "HO")])
    df = pd.DataFrame(rows); df.to_csv(R.OUT + "r7_legacy_bound.csv", index=False); print(df[["scen", "win", "ann10", "ann_pkc", "volcap_pct", "excess_share_traded"]].round(2).to_string())
