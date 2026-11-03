import os as _os
"""Build the KuCoin-spot dataset (same array layout as the Binance one): spot arrays from KuCoin 1h candles, perp arrays unchanged. Missing hours = NaN (no ffill). Aggregates-only outputs."""
import os, numpy as np, pandas as pd, json
HERE = os.path.dirname(os.path.abspath(__file__)); K = os.path.join(HERE, ".."); RAW = K + "/raw"
BASE = os.environ.get("NFB_DS_DIR_BASE", _os.environ.get("V11_DS", "./upstream/v11_full/data/ds")); OUTD = K + "/ds"; os.makedirs(OUTD, exist_ok=True)
z = dict(np.load(BASE + "/dataset.npz")); m = pd.read_csv(BASE + "/dataset_meta.csv"); T, N = z["sc"].shape
sy = pd.read_csv(RAW + "/kucoin_symbols_usdt.csv").set_index("baseCurrency")
hs = pd.read_csv(K + "/out/kucoin_half_spread.csv").set_index("symbol").half_spread_med.to_dict() if os.path.exists(K + "/out/kucoin_half_spread.csv") else {}
T0 = int(pd.Timestamp("2025-10-01", tz="UTC").timestamp())
new = {k: np.full((T, N), np.nan) for k in ("sv", "sc", "sq", "so", "sh", "sl")}
keep = np.zeros(N, bool); rows = []; fsm = np.ones(N); tk = np.array(m.tick_s, float).copy(); hs_new = np.array(m.hs_s, float).copy()
hs_med = float(np.nanmedian([hs.get(s, np.nan) for s in sy.symbol if s in hs])) if hs else float(np.nanmedian(m.hs_s))
for i, r in m.iterrows():
    b = r.spot[:-4]
    if b not in sy.index: rows.append((r.fut, "no_kucoin_pair")); continue
    ks = sy.loc[b]; p = f"{RAW}/{ks.symbol}.csv"
    if not os.path.exists(p): rows.append((r.fut, "no_download")); continue
    d = pd.read_csv(p); idx = ((d.t - T0) // 3600).astype(int).to_numpy(); ok = (idx >= 0) & (idx < T); d = d[ok]; idx = idx[ok]
    if len(d) < 200: rows.append((r.fut, "lt200_hours")); continue
    bsc = z["sc"][idx, i]; fin = np.isfinite(bsc) & (bsc > 0) & (d.close.to_numpy() > 0)
    if fin.sum() < 100: rows.append((r.fut, "no_overlap")); continue
    ratio = float(np.median(bsc[fin] / d.close.to_numpy()[fin])); mult = float(r.mult)
    scale = None
    for f in ([1.0] if mult == 1 else [mult, 1.0]):   # Binance-equivalent price = KuCoin price x scale
        if 0.8 <= ratio / f <= 1.25: scale = f; break
    if scale is None: rows.append((r.fut, "price_mismatch")); continue
    keep[i] = True
    for k, col, mul in (("sc", "close", scale), ("so", "open", scale), ("sh", "high", scale), ("sl", "low", scale), ("sq", "quote_vol", 1.0)):
        new[k][idx, i] = d[col].to_numpy() * mul
    # sv = hourly VWAP price (engine uses it as the spot mid at fill) = quote_vol / base_vol; zero-volume candle -> NaN (no fill)
    bv = d.base_vol.to_numpy(); new["sv"][idx, i] = np.where(bv > 0, d.quote_vol.to_numpy() / np.where(bv > 0, bv, 1), np.nan) * scale
    fsm[i] = float(ks.feeCategory) * float(ks.takerFeeCoefficient); tk[i] = float(ks.priceIncrement) * scale
    hs_new[i] = hs.get(ks.symbol, hs_med); rows.append((r.fut, "kept"))
status = pd.DataFrame(rows, columns=["fut", "status"]).set_index("fut").status
for k in new:
    a = new[k]; a[:, ~keep] = np.nan; z[k] = a
# depth proxy from KuCoin spot volume (same formula as the Binance build)
K02, K1 = 0.26, 2.4
for i in range(N):
    if not keep[i]: z["d02"][:, i] = 0; z["d1"][:, i] = 0; continue
    mv = pd.Series(np.minimum(np.nan_to_num(z["sq"][:, i]), np.nan_to_num(z["fq"][:, i]))).where(lambda s: s > 0)
    base = np.nan_to_num(mv.rolling(24, min_periods=6).median().bfill().ffill().to_numpy())
    z["d02"][:, i] = K02 * base; z["d1"][:, i] = K1 * base
np.savez_compressed(OUTD + "/dataset.npz", **z)
m2 = m.copy(); m2["hs_s"] = hs_new; m2["tick_s"] = tk; m2["kc_keep"] = keep; m2["kc_status"] = [status.get(f, "?") for f in m.fut]; m2["fsm"] = fsm
m2.to_csv(OUTD + "/dataset_meta.csv", index=False)
print("kept", keep.sum(), "of", N); print(status.value_counts().to_dict())
cnt = status.groupby([m.set_index("fut").grp.reindex(status.index), status]).size().unstack(fill_value=0); print(cnt)
fin_b = np.isfinite(np.load(BASE + "/dataset.npz")["sc"]); fin_k = np.isfinite(z["sc"])
print("coin-hours: binance spot", int(fin_b[:, keep].sum()), "kucoin spot", int(fin_k[:, keep].sum()), "missing share on kept coins %.1f%%" % (100 * (1 - fin_k[:, keep].sum() / fin_b[:, keep].sum())))
print("fee multiplier of kept coins:", pd.Series(fsm[keep]).value_counts().to_dict())
json.dump(dict(kept=int(keep.sum()), total=N, status=status.value_counts().to_dict(), fee_mult=pd.Series(fsm[keep]).value_counts().astype(int).rename(lambda x: str(x)).to_dict()), open(K + "/out/kc_universe.json", "w"))
