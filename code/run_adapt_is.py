import os as _os
import sys; sys.path.insert(0, (_os.environ.get("SIGNALS_ROOT", ".") + "/code"))
from run_adapt import *
HW_IS = (A0, A_IS)
def job(a):
    m, conf = a
    r = arun(m, conf, HW_IS); o = summ_win(r, HW_IS); o.update(m=m, conf=conf)
    return o
if __name__ == "__main__":
    grid = [(m, c) for m in (0, 0.5, 1, 1.5, 2, 3) for c in (1, 6, 12, 24)]
    with mp.get_context("fork").Pool(8) as p: res = p.map(job, grid)
    df = pd.DataFrame(res).drop(columns=["funding_u"], errors="ignore")
    df.to_csv(OUT + "adapt_is_grid.csv", index=False)
    print(df[["m","conf","ann","ex5_ann","top5_share","episodes","avg_hold_h","avg_cost_used_u"]].round(2).to_string())
