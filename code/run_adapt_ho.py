import os as _os
import sys; sys.path.insert(0, (_os.environ.get("SIGNALS_ROOT", ".") + "/code"))
from run_adapt import *
HW = (A_IS, A1)
RULESH = {"primary_m3_c24": (3, 24), "literal_m2_c1": (2, 1), "confonly_m0_c24": (0, 24), "fixed_m0_c1": (0, 1)}
SC = {"imp30": dict(imp=30), "imp20": dict(imp=20), "imp50": dict(imp=50), "sqrt1": dict(imp=30, extra=dict(sqrt_y=1.0)), "sqrt2": dict(imp=30, extra=dict(sqrt_y=2.0))}
def job(a):
    rn, sc = a; m, c = RULESH[rn]; kw = dict(SC[sc])
    r = arun(m, c, HW, **kw); o = summ_win(r, HW); o.update(rule=rn, scen=sc, m=m, conf=c); return o
if __name__ == "__main__":
    jobs = [(rn, sc) for rn in RULESH for sc in SC]
    with mp.get_context("fork").Pool(8) as p: res = p.map(job, jobs)
    df = pd.DataFrame(res).drop(columns=["funding_u"], errors="ignore"); df.to_csv(OUT + "adapt_holdout.csv", index=False)
    print(df[["rule","scen","ann","ex5_ann","top5_share","episodes","avg_hold_h"]].round(2).to_string())
