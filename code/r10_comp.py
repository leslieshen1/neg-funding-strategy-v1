import os as _os
"""Round 10: companion numbers for cons + 0h (and 8h comparison). Aggregates only. Writes out/r10_comp_tables.md"""
import numpy as np, pandas as pd, json
from r10_boot import boot
O = (_os.environ.get("SIGNALS_ROOT", ".") + "/out/")
runs = pd.concat([pd.read_csv(O + f"r10_{t}_S{S}M.csv") for t in "abcdke" for S in (10, 20)]).drop_duplicates(["fix", "win", "S"])
b9 = pd.read_csv(O + "r9b_all_runs.csv")
bs = pd.read_csv(O + "r10_bootstrap2.csv")
def R(S, fix, w, c="ann"): return runs[(runs.S == S * 1e6) & (runs.fix == fix) & (runs.win == w)].iloc[0][c] if len(runs[(runs.S == S * 1e6) & (runs.fix == fix) & (runs.win == w)]) else np.nan
print(runs.S.unique()[:4])
def B(S, fix, w, ref=None):
    q = bs[(bs.S == S) & (bs.fix == fix) & (bs.win == w)]
    if ref: q = q[q.ref == ref]
    return q.iloc[0] if len(q) else None
def ci(r): return f"[{r.lo:.0f}, {r.hi:.0f}]"
def dff(r): return f"{r.d:+.1f} [{r.dlo:+.1f}, {r.dhi:+.1f}]"
def dl(S, f, w):
    x = np.load(O + f"r10_daily/S{S}M__{f}__{w}.npy"); k = len(x) // 24 * 24; return x[:k].reshape(-1, 24).sum(1)
def dl9(S, f, w):
    x = np.load(O + f"r9_daily/S{S}M__{f}__{w}.npy"); k = len(x) // 24 * 24; return x[:k].reshape(-1, 24).sum(1)
out = []; J = {}
def P(s=""): out.append(s)
# 1. headline
P("### 9d.4 头条(cons + 0h)\n"); P("| 本金 | IS 年化(净利万U) | HO 年化(净利) | FY 年化(净利)[95%区间] | FY 笔数 | 平均持仓(h) | 平均占用(万U) |"); P("|---|---|---|---|---|---|---|")
for S in (10, 20):
    r = {w: B(S, "cons_c0", w) for w in ("IS", "HO", "FY")}
    P(f"| {S}M | {r['IS'].ann:.1f}% ({r['IS'].net_wan:.0f}) [{r['IS'].lo:.0f}, {r['IS'].hi:.0f}] | {r['HO'].ann:.1f}% ({r['HO'].net_wan:.0f}) [{r['HO'].lo:.0f}, {r['HO'].hi:.0f}] | **{r['FY'].ann:.1f}% ({r['FY'].net_wan:.0f})** {ci(r['FY'])} | {int(R(S,'cons_c0','FY','episodes'))} | {R(S,'cons_c0','FY','avg_hold_h'):.0f} | {R(S,'cons_c0','FY','avg_cost_used_u')/1e4:.0f} |")
    J[f"head{S}"] = {w: [r[w].ann, r[w].net_wan, r[w].lo, r[w].hi] for w in r}
P("\n收益分解(FY,万U,10M):\n"); P("| 规则 | 资金费 | 基差 | 手续费 | 冲击 | 净利 |\n|---|---|---|---|---|---|")
for fx, n in (("cons", "48h"), ("cons_c0", "0h")):
    P(f"| {n} | {R(10,fx,'FY','funding_u')/1e4:+.0f} | {R(10,fx,'FY','basis_u')/1e4:+.0f} | {R(10,fx,'FY','fees_u')/1e4:+.0f} | {R(10,fx,'FY','slip_u')/1e4:+.0f} | {R(10,fx,'FY','net_u')/1e4:.0f} |")
# 2. k sensitivity
P("\n### 9d.5 k_imp 敏感性(cons + 0h;年化 %,区间为 FY 的 95% 自助法区间)\n")
ks = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
def fk(k): return "cons_c0" + ("" if k == 4 else f"_k{k}")
P("| 本金 / 窗口 | " + " | ".join(f"k={k}" for k in ks) + " |"); P("|---|" + "---|" * len(ks))
for S in (10, 20):
    for w in ("FY", "HO", "IS"):
        P(f"| {S}M {w} | " + " | ".join(f"{B(S,fk(k),w).ann:.1f}" for k in ks) + " |")
    P(f"| {S}M FY 区间 | " + " | ".join(ci(B(S, fk(k), 'FY')) for k in ks) + " |")
be = {}
for S in (10, 20):
    for w in ("FY", "HO"):
        y = [B(S, fk(k), w).ann for k in ks]; z = None
        for i in range(len(ks) - 1):
            if y[i] > 0 >= y[i + 1]: z = ks[i] + (y[i] - 0) / (y[i] - y[i + 1]) * (ks[i + 1] - ks[i]); break
        be[f"{S}{w}"] = z
P("\n盈亏平衡 k(线性插值,年化=0):" + ";".join(f"{S}M {w}: " + (f"{be[f'{S}{w}']:.1f}" if be[f'{S}{w}'] else ">12") for S in (10, 20) for w in ("FY", "HO")))
y10 = [B(10, fk(k), "FY").ann for k in ks]; P("相邻 k 的 10M FY 年化斜率(pp/单位 k):" + ", ".join(f"{ks[i]}→{ks[i+1]}: {y10[i]-y10[i+1]:.1f}" for i in range(len(ks) - 1)))
J["be"] = be; J["k"] = {f"{S}{w}": [B(S, fk(k), w).ann for k in ks] for S in (10, 20) for w in ("FY", "HO", "IS")}
# 3. variants
P("\n### 9d.6 其他检验(cons + 0h;年化 %,括号 = 对 0h 基准的配对差 pp [95%区间])\n")
P("| 本金 | 变体 | IS | HO | FY | FY 净利(万U) |\n|---|---|---|---|---|---|")
def row(S, fx, name, ref):
    cs = []
    for w in ("IS", "HO", "FY"):
        r = B(S, fx, w, ref); cs.append(f"{r.ann:.1f}" + (f" ({dff(r)})" if ref else ""))
    P(f"| {S}M | {name} | {' | '.join(cs)} | {B(S,fx,'FY',ref).net_wan:.0f} |")
for S in (10, 20):
    row(S, "cons_c0", "基准 cons+0h", None)
    row(S, "consM_c0", "市值上限(consM)", "cons_c0")
    row(S, "consI_c0", "冲击感知仓位 imp_size, k=4", "cons_c0")
    row(S, "cons_c0_dS", "现货腿晚 1 小时", "cons_c0")
    row(S, "cons_c0_dP", "永续腿晚 1 小时", "cons_c0")
    row(S, "allC_c0", "乐观上界 allC(不对 e≥0 小时计自身冲击)", "cons_c0")
P(f"\nimp_size k=2:10M FY {B(10,'consI_c0_k2','FY','cons_c0_k2').ann:.1f}%(对 cons_c0_k2 配对 {dff(B(10,'consI_c0_k2','FY','cons_c0_k2'))}),20M FY {B(20,'consI_c0_k2','FY','cons_c0_k2').ann:.1f}%({dff(B(20,'consI_c0_k2','FY','cons_c0_k2'))})")
P("\n**峰值市价占用 / 本金**:" + "; ".join(f"{S}M cons+0h {R(S,'cons_c0','FY','peak_mtm_u')/S/1e6:.2f}×,consM+0h {R(S,'consM_c0','FY','peak_mtm_u')/S/1e6:.2f}×" for S in (10, 20)) + "(48h:1.21× / 1.07×)")
P("\nconsM 触发裁减名义额(FY,万U):" + "; ".join(f"{S}M {R(S,'consM_c0','FY','mtm_trim_u')/1e4:.0f}" for S in (10, 20)))
# residual
P("\n### 9d.7 窗口末残余仓位与平仓成本倍数(cons + 0h)\n")
P("| 倍数 | HO 净利(万U) | HO 比 ×3 少 | FY 净利(10M,万U) | FY 比 ×3 少 | FY 残余成本(千U) |\n|---|---|---|---|---|---|")
for m, fx in ((1, "cons_c0_r1"), (3, "cons_c0"), (5, "cons_c0_r5"), (10, "cons_c0_r10")):
    ho = R(10, fx, "HO", "net_u"); fy = R(10, fx, "FY", "net_u"); ho3 = R(10, "cons_c0", "HO", "net_u"); fy3 = R(10, "cons_c0", "FY", "net_u")
    P(f"| ×{m} | {ho/1e4:.1f} | {(1-ho/ho3)*100:.1f}% | {fy/1e4:.1f} | {(1-fy/fy3)*100:.1f}% | {R(10,fx,'FY','resid_cost_u')/1e3:.0f} |")
for S in (10, 20):
    P(f"\n{S}M FY 窗口末残余名义额 {R(S,'cons_c0','FY','resid_u')/1e4:.0f} 万U(48h:{R(S,'cons','FY','resid_u')/1e4:.0f});按 pov 分批平完平均 {R(S,'cons_c0_u1','FY','unwind_wavg_h')/24:.1f} 天、最长 {R(S,'cons_c0_u1','FY','unwind_max_h')/24:.0f} 天(48h:{R(S,'cons_u1','FY','unwind_wavg_h')/24:.1f} / {R(S,'cons_u1','FY','unwind_max_h')/24:.0f})")
J["resid"] = {S: [R(S, "cons_c0", "FY", "resid_u") / 1e4, R(S, "cons_c0_u1", "FY", "unwind_wavg_h") / 24, R(S, "cons_c0_u1", "FY", "unwind_max_h") / 24] for S in (10, 20)}
# concentration
P("\n### 9d.8 集中度(事后排名)与月份占比(cons + 0h)\n")
P("| 本金 | 窗口 | 前5币占净利 | 去掉前5币后年化 | 48h 对照:前5占 / 去前5年化 |\n|---|---|---|---|---|")
for S in (10, 20):
    for w in ("FY", "HO"):
        P(f"| {S}M | {w} | {R(S,'cons_c0',w,'top5_share'):.1f}% | {R(S,'cons_c0',w,'ex5_ann'):.1f}% | {R(S,'cons',w,'top5_share'):.1f}% / {R(S,'cons',w,'ex5_ann'):.1f}% |")
J["conc"] = {f"{S}{w}": [R(S, "cons_c0", w, "top5_share"), R(S, "cons_c0", w, "ex5_ann")] for S in (10, 20) for w in ("FY", "HO")}
def monthly(S, fx, w, start):
    d = dl(S, fx, w); idx = pd.date_range(start, periods=len(d), freq="D"); s = pd.Series(d, index=idx).groupby(idx.to_period("M")).sum(); return (s / s.sum() * 100)
for S, fx in ((10, "cons_c0"), (10, "cons")):
    for w, st in (("HO", "2026-07-01"), ("FY", "2025-10-28")):
        m = monthly(S, fx, w, st); P(f"\n{S}M {'0h' if fx=='cons_c0' else '48h'} {w} 月份占净利比:" + ",".join(f"{str(i)[2:]} {v:.1f}%" for i, v in m.items()))
        J[f"month_{fx}_{w}"] = {str(i): v for i, v in m.items()}
for fx in ("cons", "cons_c0"):
    d = dl(10, fx, "FY"); c = np.cumsum(d); dd = (np.maximum.accumulate(np.concatenate([[0], c]))[1:] - c).max()
    P(f"\n{'0h' if fx=='cons_c0' else '48h'} 10M FY 日度累计净利最大回撤 {dd/1e4:.1f} 万U,最差单日 {d.min()/1e4:.1f} 万U")
# capacity
P("\n### 9d.9 容量:10M vs 20M(净利,万U;配对差 = 20M − 10M,7 天块自助法)\n")
P("| 配置 | 10M FY 净利 | 20M FY 净利 | 差(20M−10M)[95%区间] | 10M HO | 20M HO |\n|---|---|---|---|---|---|")
for nm, fx in (("cons + 0h,k=4", "cons_c0"), ("cons + 0h,k=0", "cons_c0_k0"), ("乐观 allC + 0h,k=4", "allC_c0"), ("乐观 allC + 0h,k=0", "allC_c0_k0"), ("cons + 48h,k=4", "cons"), ("cons + 48h,k=0", "cons_k0")):
    d10 = dl(10, fx, "FY"); d20 = dl(20, fx, "FY"); n = len(d10); m, lo, hi, _ = boot(d20 - d10, 100 * 365 / (n * 1e6)); f = 1.0
    P(f"| {nm} | {d10.sum()/1e4:.0f} | {d20.sum()/1e4:.0f} | {(d20-d10).sum()/1e4:+.0f} [{lo*f/1e4:+.0f}, {hi*f/1e4:+.0f}] | {R(10,fx,'HO','net_u')/1e4:.0f} | {R(20,fx,'HO','net_u')/1e4:.0f} |")
# own impact on pending hours
P("\n### 9d.10 0h 的优势有多少依赖“出场条件已触发后仍持仓的小时也计自身冲击”(保守假设)\n")
P("| 配置(10M) | IS | HO | FY |\n|---|---|---|---|")
for nm, f9, f10 in (("cons 48h", "cons", None), ("cons 0h", None, "cons_c0"), ("allC 48h(不对 e≥0 小时计自身冲击)", "allC", None), ("allC 0h", None, "allC_c0")):
    P(f"| {nm} | " + " | ".join(f"{(R(10, f9, w) if f9 and f9 in set(runs.fix) else float(b9[(b9.S==10)&(b9.fix==f9)&(b9.win==w)].ann.iloc[0])) if f9 else R(10, f10, w):.1f}" for w in ("IS", "HO", "FY")) + " |")
for w in ("IS", "HO", "FY"):
    a = dl(10, "allC_c0", w) - dl9(10, "allC", w); c = dl(10, "cons_c0", w) - dl9(10, "cons", w)
    ma, la, ha, _ = boot(a, 10); mc, lc, hc, _ = boot(c, 10)
    P(f"\n{w}:0h − 48h(cons){mc:+.1f} [{lc:+.1f}, {hc:+.1f}] pp;0h − 48h(allC){ma:+.1f} [{la:+.1f}, {ha:+.1f}] pp")
    J[f"own_{w}"] = [mc, ma]
# rank table by k
P("\n### 9d.2 各 k 下的 IS 排名(10M,cons;年化 %;排名只看 IS)\n")
names = [("c48", "cons", "48h(参照)"), ("c24", "cons_c24", "24h"), ("c12", "cons_c12", "12h"), ("c8", "cons_c8", "8h(事后加入)"), ("c0", "cons_c0", "0h"), ("x2a", "cons_x2a", "两段式 A"), ("x2b", "cons_x2b", "两段式 B")]
def fx(base, k): return base + ("" if k == 4 else f"_k{k}")
P("| 规则 | " + " | ".join(f"k={k}: IS(名次)/HO/FY" for k in (0, 2, 4, 6)) + " |"); P("|---|---|---|---|---|")
rk = {}
for k in (0, 2, 4, 6):
    v = {n: R(10, fx(b, k), "IS") for _, b, n in names}; order = sorted(v, key=lambda n: -v[n]); rk[k] = {n: order.index(n) + 1 for n in v}
for _, b, n in names:
    P(f"| {n} | " + " | ".join(f"{R(10,fx(b,k),'IS'):.1f} (#{rk[k][n]}) / {R(10,fx(b,k),'HO'):.1f} / {R(10,fx(b,k),'FY'):.1f}" for k in (0, 2, 4, 6)) + " |")
# 8h and 0h pairs
P("\n### 9d.3 8h(一个资金费周期)对比(10M,配对差 pp [95%区间];括号外为年化)\n")
P("| k | 窗口 | 8h 年化 | 8h − 0h | 8h − 48h |\n|---|---|---|---|---|")
for S, ks_ in ((10, (0, 2, 4, 6)), (20, (0, 2, 4, 6))):
    for k in ks_:
        for w in ("IS", "HO", "FY"):
            r0 = B(S, fx("cons_c8", k), w, fx("cons_c0", k)); r48 = B(S, fx("cons_c8", k), w, fx("cons", k))
            P(f"| {S}M k={k} | {w} | {r0.ann:.1f} {ci(r0)} | {dff(r0)} | {dff(r48)} |")
open(O + "r10_comp_tables.md", "w").write("\n".join(out)); json.dump(J, open(O + "r10_comp.json", "w"), default=float)
print("\n".join(out))
