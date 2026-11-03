"""Post-processing margin / transfer analysis for spot(KuCoin)+perp(Binance long) positions. Does not change fills. Aggregates only.
pos: (H,N) single-leg notional at hour close (engine output); spot sc (KuCoin), perp fc / fl (Binance). Missing KuCoin hours -> price carried only to VALUE the existing position."""
import numpy as np
def ffill0(a):
    a = a.copy(); 
    for t in range(1, len(a)): m = ~np.isfinite(a[t]); a[t, m] = a[t - 1, m]
    return a
def margin_stats(pos, sc, sh, fc, fl, S, Ls=(1, 2, 3, 5, 10), mmr=0.01):
    H, N = pos.shape; sc = ffill0(sc); sh = np.fmax(ffill0(sh), sc); fc = np.nan_to_num(ffill0(fc), nan=0.0); fl = np.nan_to_num(np.fmin(ffill0(fl), fc), nan=0.0); sc = np.nan_to_num(sc, nan=0.0); sh = np.nan_to_num(sh, nan=0.0)
    q = np.where(sc > 0, np.abs(pos) / np.where(sc > 0, sc, 1), 0.0)
    qp = np.zeros(N); epf = np.zeros(N); eps = np.zeros(N)
    liq = {L: np.zeros(N, bool) for L in Ls}; nliq = {L: 0 for L in Ls}; nep = 0
    adv = np.zeros(N); ral = np.zeros(N); epd_adv = []; epd_ral = []
    out_dip = np.zeros(H); out_ral = np.zeros(H); out_notional = np.zeros(H); out_cash_s = np.zeros(H); out_perploss_close = np.zeros(H); out_spotloss_close = np.zeros(H)
    out_liq_loss = {L: 0.0 for L in Ls}
    for t in range(H):
        # intrahour extremes on the position held INTO the hour
        h = qp > 0
        if h.any():
            pl = qp * (fl[t] - epf)                  # perp unrealized at the hour low
            ss = qp * (eps - sh[t])                  # spot-short unrealized at the hour high
            out_dip[t] = np.maximum(0, -pl)[h].sum(); out_ral[t] = np.maximum(0, -ss)[h].sum()
            adv = np.where(h, np.maximum(adv, (epf - fl[t]) / np.where(epf > 0, epf, 1)), adv); ral = np.where(h, np.maximum(ral, (sh[t] - eps) / np.where(eps > 0, eps, 1)), ral)
            for L in Ls:
                eq = qp * epf / L + pl; hit = h & (eq <= mmr * qp * fl[t]) & ~liq[L]
                if hit.any(): nliq[L] += int(hit.sum()); liq[L] |= hit; out_liq_loss[L] += float(np.maximum(0, -pl)[hit].sum())
        qn = q[t]; add = qn > qp * 1.0000001
        ne_ = add & (qp == 0); nep += int(ne_.sum())
        w = add & (qn > 0)
        epf = np.where(w, (epf * qp + fc[t] * (qn - qp)) / np.where(qn > 0, qn, 1), epf); eps = np.where(w, (eps * qp + sc[t] * (qn - qp)) / np.where(qn > 0, qn, 1), eps)
        z = qn <= 0
        if z.any():
            for a_, b_ in ((adv, epd_adv), (ral, epd_ral)):
                b_.extend(a_[z & (qp > 0)].tolist())
            adv[z] = 0; ral[z] = 0; epf[z] = 0; eps[z] = 0
            for L in Ls: liq[L][z] = False
        qp = qn
        out_notional[t] = (qp * fc[t]).sum(); out_cash_s[t] = (qp * eps).sum()
        out_perploss_close[t] = np.maximum(0, -(qp * (fc[t] - epf))).sum(); out_spotloss_close[t] = np.maximum(0, -(qp * (eps - sc[t]))).sum()
    r = dict(peak_notional_pct=out_notional.max() / S * 100, avg_notional_pct=out_notional.mean() / S * 100, episodes=nep,
             peak_spotcash_kc_pct=out_cash_s.max() / S * 100, avg_spotcash_kc_pct=out_cash_s.mean() / S * 100,
             dip_transfer_peak_pct=out_dip.max() / S * 100, dip_transfer_p95_pct=np.percentile(out_dip, 95) / S * 100,
             rally_transfer_peak_pct=out_ral.max() / S * 100, rally_transfer_p95_pct=np.percentile(out_ral, 95) / S * 100,
             dip_close_peak_pct=out_perploss_close.max() / S * 100, rally_close_peak_pct=out_spotloss_close.max() / S * 100,
             hours_rally_gt1pct=int((out_ral > 0.01 * S).sum()), hours_dip_gt1pct=int((out_dip > 0.01 * S).sum()))
    for nm, e in (("adv", epd_adv), ("ral", epd_ral)):
        e = np.array(e) if len(e) else np.zeros(1)
        r[f"ep_{nm}_p50"] = np.percentile(e, 50) * 100; r[f"ep_{nm}_p95"] = np.percentile(e, 95) * 100; r[f"ep_{nm}_max"] = e.max() * 100; r[f"ep_{nm}_gt20pct"] = int((e > 0.20).sum()); r[f"ep_{nm}_gt50pct"] = int((e > 0.50).sum()); r["n_ep_closed"] = len(e)
    for L in Ls:
        r[f"L{L}_margin_peak_pct"] = r["peak_notional_pct"] / L; r[f"L{L}_margin_avg_pct"] = r["avg_notional_pct"] / L; r[f"L{L}_liq_events"] = nliq[L]; r[f"L{L}_liq_loss_pct"] = out_liq_loss[L] / S * 100
    return r
