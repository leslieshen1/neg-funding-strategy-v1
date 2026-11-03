"""Snapshot KuCoin spot best bid/ask (public allTickers) n times; per-symbol median half-spread = proxy for hs_s. Taken NOW (Nov 2026) and applied to the whole past: disclosed limitation."""
import requests, time, pandas as pd, numpy as np, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); n = int(sys.argv[1]) if len(sys.argv) > 1 else 30; rows = []
for i in range(n):
    d = None
    for _try in range(5):
        try:
            d = requests.get("https://api.kucoin.com/api/v1/market/allTickers", timeout=30).json().get("data")
        except Exception: d = None
        if d: break
        time.sleep(10)
    if not d: continue
    for x in d["ticker"]:
        try:
            b, a = float(x["buy"]), float(x["sell"])
            if b > 0 and a > b: rows.append((x["symbol"], (a - b) / (a + b)))
        except Exception: pass
    time.sleep(15)
df = pd.DataFrame(rows, columns=["symbol", "hs"]); g = df.groupby("symbol").hs.agg(["median", "count"]).reset_index(); g.columns = ["symbol", "half_spread_med", "n_snap"]
g.to_csv(os.path.join(HERE, "..", "out", "kucoin_half_spread.csv"), index=False); print(len(g), g.half_spread_med.median())
