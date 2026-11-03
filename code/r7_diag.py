import os as _os
import sys; sys.path.insert(0, (_os.environ.get("SIGNALS_ROOT", ".") + "/code"))
import run_r7 as R, numpy as np, pandas as pd
rows = []
for w in ("IS", "HO"):
    for nm, c in (("frozen_c48", 48.0), ("newgate_c24", 24.0)):
        r = R.run_cfg(("r7", 2.0), dict(conf_h=c), "cal", w); xd = r["xd"]; dg = r["diag"]
        rows.append(dict(win=w, cfg=nm, forced_cut_notional_u=float(xd[44]), forced_excess_over_pov_u=float(xd[45]), traded_u=r["traded"], volcap_hours=dg[0], oicap_hours=dg[1], held_hours=dg[11],
                         max_vol_ratio=dg[2], max_oi_ratio=dg[3], cap_over_hours_capital=dg[18], is_derisk_notional_u=dg[16], trim_hours=xd[52], resid_hours=xd[55], zero_cap_hours=xd[57], max_over_cap_ratio=xd[54], r_lt125=xd[58], r_125_2=xd[59], r_2_5=xd[60], r_gt5=xd[61], resid_u_hours=xd[53]))
df = pd.DataFrame(rows); df["volcap_pct"] = 100 * df.volcap_hours / df.held_hours; df["oicap_pct"] = 100 * df.oicap_hours / df.held_hours
df["forced_excess_share_of_traded_pct"] = 100 * df.forced_excess_over_pov_u / df.traded_u
df.to_csv(R.OUT + "r7_hardcap.csv", index=False); print(df.round(3).T.to_string())
