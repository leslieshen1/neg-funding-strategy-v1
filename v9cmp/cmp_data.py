import os as _os
import numpy as np, pandas as pd
a=np.load(_os.environ.get("V9_DATA", "./upstream/v9/data") + "/dataset.npz"); b=np.load(_os.environ.get("V11_DS", "./upstream/v11_full/data/ds") + "/dataset.npz")
ma=pd.read_csv(_os.environ.get("V9_DATA", "./upstream/v9/data") + "/dataset_meta.csv"); mb=pd.read_csv(_os.environ.get("V11_DS", "./upstream/v11_full/data/ds") + "/dataset_meta.csv")
print(a.files); print(b.files); print({k:a[k].shape for k in a.files[:4]},{k:b[k].shape for k in b.files[:4]})
ia={f:i for i,f in enumerate(ma.fut)}; ib={f:i for i,f in enumerate(mb.fut)}
com=[f for f in ia if f in ib]; print("v9 pool",len(ia),"ours",len(ib),"common",len(com))
T=min(a["sc"].shape[0],b["sc"].shape[0])
for k in ["sc","fc","sq","fq","ev","r8","oih"]:
    if k in a.files and k in b.files:
        x=a[k][:T][:,[ia[f] for f in com]].astype(float); y=b[k][:T][:,[ib[f] for f in com]].astype(float)
        m=np.isfinite(x)&np.isfinite(y)&(x!=0)&(y!=0)
        rel=np.abs(x-y)[m]/np.abs(y[m]); print(k,"overlap",m.mean().round(4),"max rel",rel.max(),"frac>1e-6",(rel>1e-6).mean())
