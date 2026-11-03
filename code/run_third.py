import sys; sys.argv = ["x", "none"]
from run_signals import *
RULES = {"E7xX5": ("E7", "X5"), "E7xX3": ("E7", "X3"), "E2xX3": ("E2", "X3"), "E1xX1B": ("E1", "X1"), "REF": ("REF", "REF")}
def sp(rn, **kw):
    e, x = RULES[rn]; d = dict(e=e, x=x, imp=30, obs=1); d.update(kw); return d
if __name__ == "__main__":
    specs = []
    for rn in RULES:
        specs.append((f"base|{rn}", sp(rn)))
        specs.append((f"cool24|{rn}", sp(rn, extra=dict(cool_h=24.0))))
        for pv in (0.01, 0.03, 0.10, 0.20):
            specs.append((f"pov|fixed|{pv}|{rn}", sp(rn, extra=dict(pov=pv))))
            for y in (1.0, 2.0): specs.append((f"pov|sqrt{y}|{pv}|{rn}", sp(rn, extra=dict(pov=pv, sqrt_y=y))))
        for mm in ("ii_50", "ii_100", "iii_50", "iii_100"):
            for gs in (0, 1, 2):
                for hx in (0, 1):
                    for adv in (1.0, 0.0):
                        specs.append((f"mk|{mm}|gap{gs}|hxoff{hx}|adv{int(adv)}|{rn}", sp(rn, mm=mm, gap_sym=gs, advw=adv, extra=dict(hx_off=float(hx)))))
    df = pool(specs); df.to_csv(OUT + "third.csv", index=False); print(len(df))
