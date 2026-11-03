import sys; sys.argv = ["x", "none"]
from run_signals import *
if __name__ == "__main__":
    specs = [(f"{e}|{x}|30|k{k}|obs{o}", dict(e=e, x=x, imp=30, obs=o, k=k)) for k in (0, 2, 4, 8) for e, x in (("E1", "X1"), ("E1", "X2"), ("E1", "X4")) for o in (0, 1)]
    pool(specs).to_csv(OUT + "ksens_e1.csv", index=False)
