import os as _os
"""Download KuCoin spot hourly candles (public endpoint, no key) for the coins whose base ticker exists as an USDT pair on KuCoin today.
Output raw/<KUCOIN_SYMBOL>.csv with columns t(unix s, open time), open, close, high, low, base_vol, quote_vol. Hours with no candle are simply absent (no fill)."""
import os, time, requests, pandas as pd, numpy as np
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__)); RAW = os.path.join(HERE, "..", "raw")
DS = os.environ.get("NFB_DS_DIR", _os.environ.get("V11_DS", "./upstream/v11_full/data/ds"))
T0 = int(pd.Timestamp("2025-10-01", tz="UTC").timestamp()); T1 = int(pd.Timestamp("2026-10-28", tz="UTC").timestamp())
def get(sym, a, b):
    for k in range(6):
        try:
            r = requests.get("https://api.kucoin.com/api/v1/market/candles", params=dict(type="1hour", symbol=sym, startAt=a, endAt=b), timeout=30)
            if r.status_code == 200 and r.json().get("code") == "200000": return r.json()["data"]
        except Exception: pass
        time.sleep(1.5 * (k + 1))
    raise RuntimeError(sym)
def one(sym):
    p = os.path.join(RAW, sym + ".csv")
    if os.path.exists(p): return sym, "cached"
    rows = []; a = T0
    while a < T1:
        b = min(a + 1400 * 3600, T1); rows += get(sym, a, b); a = b
    d = pd.DataFrame(rows, columns=["t", "open", "close", "high", "low", "base_vol", "quote_vol"]).astype(float).drop_duplicates("t").sort_values("t")
    d.to_csv(p, index=False); return sym, len(d)
if __name__ == "__main__":
    m = pd.read_csv(DS + "/dataset_meta.csv"); s = pd.read_csv(os.path.join(RAW, "kucoin_symbols_usdt.csv"))
    ks = dict(zip(s.baseCurrency, s.symbol)); syms = sorted({ks[x[:-4]] for x in m.spot if x[:-4] in ks})
    print(len(syms), "symbols"); n = 0
    with ThreadPoolExecutor(4) as ex:
        for sym, k in ex.map(one, syms):
            n += 1
            if n % 40 == 0: print(n, sym, k, flush=True)
