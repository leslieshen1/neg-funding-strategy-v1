import os as _os
import pandas as pd, numpy as np
OUT = (_os.environ.get("SIGNALS_ROOT", ".") + "/out/"); REP = (_os.environ.get("SIGNALS_ROOT", ".") + "/REPORT_signals.md")
d = pd.read_csv(OUT + "third.csv").set_index("name")
R = ["E7xX5", "E7xX3", "E2xX3", "E1xX1B", "REF"]; LB = {"E7xX5": "E7×X5(冠军)", "E7xX3": "E7×X3", "E2xX3": "E2×X3", "E1xX1B": "E1×X1(B)", "REF": "v11 调参规则"}
w = lambda v: f"{v/1e4:,.0f}"; f1 = lambda v: f"{v:.1f}"
def tab(h, rows): return "| " + " | ".join(h) + " |\n|" + "|".join(["---"] * len(h)) + "|\n" + "\n".join("| " + " | ".join(map(str, r)) + " |" for r in rows) + "\n"
L = []; A = L.append
A("\n---\n\n# 结果:第三轮(审查官回应)\n")
A("口径:B 版(x_obs=1)、30bp、taker、ADL 开、k=4、pov 3%、窗口 2025-10-28→2026-10-28(365 天),分母固定 1000 万 U。引擎改动仅为新增开关(cool_h / hx_off / gap_sym=2),默认值下复现旧结果(E1×X1 A 版 13.073%、E7×X3 A 版 91.122%、本表基线与第二轮一致)。金额单位:万 U。\n")
# 1
A("## 15. 同币 24h 再入场冷却 + 立即再入场计数\n")
rows = []
for r in R:
    b = d.loc[f"base|{r}"]; c = d.loc[f"cool24|{r}"]
    rows.append([LB[r], f1(b.ann), f1(c.ann), f"{c.ann-b.ann:+.1f}", f1(b.is_ann), f1(c.is_ann), f1(b.ho_ann), f1(c.ho_ann), int(b.episodes), int(c.episodes),
                 f"{int(b.reentry2_n)} ({b.reentry2_share:.1f}%)", f"{int(b.reentry8_n)} ({b.reentry8_share:.1f}%)", f"{int(b.reentry_lt24_n)} ({b.reentry_lt24_share:.1f}%)"])
A(tab(["规则", "基线年化%", "冷却24h年化%", "差", "基线IS", "冷却IS", "基线HO", "冷却HO", "基线episodes", "冷却episodes", "基线≤2h再入", "≤8h", "<24h"], rows))
A("说明:再入场 = 同一币上次平完到下次开仓的间隔(括号为占全部 episodes 的比例);冷却版按定义 <24h 再入场为 0(间隔恰为 24h 的另计,E7×X5 为 103 个)。\n")
# 2
A("## 16. pov 敏感性(1/3/10/20%)× 冲击模型\n")
A("固定 30bp = 每腿每笔固定 30bp;平方根律 = y·σ_日·√(Q/ADV)(y=1、2;σ、ADV 用 t-1 前已知值,另加半点差)。注意:平方根律的 y 没有校准,只是量级敏感性;pov 越大,单笔 Q 越大,平方根冲击越高。年化 %(1000 万分母):\n")
rows = []
for r in R:
    for mdl, key in (("固定30bp", "fixed"), ("√律 y=1", "sqrt1.0"), ("√律 y=2", "sqrt2.0")):
        rows.append([LB[r], mdl] + [f1(d.loc[f"pov|{key}|{pv}|{r}"].ann) for pv in (0.01, 0.03, 0.1, 0.2)])
A(tab(["规则", "冲击模型", "pov 1%", "pov 3%(基线)", "pov 10%", "pov 20%"], rows))
c = d.loc[[f"pov|{k}|{pv}|E7xX5" for k in ("fixed", "sqrt1.0", "sqrt2.0") for pv in (0.03, 0.2)]]
A("冠军 E7×X5 的冲击+点差(万 U):" + ";".join(f"{n.split('|')[1]} pov{float(n.split('|')[2])*100:.0f}% {w(v)}" for n, v in c.impact_u.items()) + "。\n")
# 3
A("## 17. maker:逐假设拆分(年化 %,50%/100% 成交)\n")
A("三个悲观/未校准假设:**A** 次小时 gap 成本(原口径=单边取正;另列对称有符号、关闭)、**B** 对冲腿按整小时最差价成交(关=对冲腿按普通 taker 价)、**C** 逆选(只影响模式 iii;模式 ii 恒为 0)。每行在其余假设保持原口径(A=单边、B=开、C=开)的基础上只改一项,最后几行为组合。\n")
def mk(r, mm, gs, hx, adv): return d.loc[f"mk|{mm}|gap{gs}|hxoff{hx}|adv{adv}|{r}"].ann
for r in R:
    A(f"**{LB[r]}**(taker 基线 {f1(d.loc['base|'+r].ann)})\n")
    rows = []
    for nm, gs, hx, adv in (("原口径(A单边+B开+C开)", 0, 0, 1), ("仅 A 改为对称有符号", 1, 0, 1), ("仅去 A(gap 关)", 2, 0, 1), ("仅去 B(对冲按 taker 价)", 0, 1, 1), ("仅去 C(逆选关)", 0, 0, 0),
                            ("去 A+B", 2, 1, 1), ("去 A+C", 2, 0, 0), ("去 B+C", 0, 1, 0), ("去 A+B+C", 2, 1, 0)):
        rows.append([nm] + [f1(mk(r, mm, gs, hx, adv)) for mm in ("ii_50", "ii_100", "iii_50", "iii_100")])
    A(tab(["假设组合", "ii_50", "ii_100", "iii_50", "iii_100"], rows))
e = [mk("E7xX5", mm, g, h, a) for mm in ("ii_50", "ii_100", "iii_50", "iii_100") for g in (0, 1, 2) for h in (0, 1) for a in (1, 0)]
A(f"**结论(预先写定,数据未改变它):无盘口/逐笔数据,不能证明 maker 更好,也不能证明更差,需要校准。** 冠军 E7×X5 在 4 种模式 × 12 种假设组合(共 48 个数)下 maker 年化跨度 {min(e):.1f}% ~ {max(e):.1f}%(taker 基线 {f1(d.loc['base|E7xX5'].ann)}%),符号和相对 taker 的优劣都随假设翻转;任何单个 maker 数字都不能当估计值。需要校准的三件事:限价单真实成交率与成交时点、成交后对冲腿的反应时间与滑点(取代'整小时最差价'假设)、逆选幅度(成交后价格漂移)。成交率 50%→100% 的非单调(100% 反而更差)在 B 打开时存在;去掉 B(模式 ii)或去掉 B+C(模式 iii)后消失(100% 变好),说明它是'对冲腿按整小时最差价'与逆选假设的产物。\n")
# 4
A("## 18. PnL 分解(万 U;恒等式:funding + 冲击点差 + 手续费 + 基差收敛 + 其他 = 净利)\n")
rows = []
for r in R:
    b = d.loc[f"base|{r}"]
    chk = b.funding_u + b.impact_u + b.fees_u + b.basis_u + b.other_liq_u - b.net_u
    rows.append([LB[r], w(b.funding_u), w(b.impact_u), w(b.fees_u), w(b.basis_u), w(b.other_liq_u), w(b.net_u), f"{chk:.0f}", f"{b.funding_u/S_:.1f}" if False else f1(b.funding_u / 1e7 * 100), f1(b.basis_u / 1e7 * 100), f1(b.ann)])
A(tab(["规则", "funding", "冲击+点差", "手续费", "基差收敛", "其他", "净利", "校验(U)", "funding 年化pp", "基差年化pp", "净年化%"], rows))
A(f"口径:funding = 已结算资金费(持仓期间收到/支付);冲击+点差 = 每笔成交相对小时中价的价差成本(含固定冲击与半点差);手续费 = 现货 10bp + 永续 5bp;**基差收敛 = 中价口径的价格盈亏**(= 成交价盈亏 + 冲击点差,再扣掉'其他'),即永续相对现货的价差(入场时永续折价)在持仓/平仓期间的变化(以小时 VWAP 作中价);其他 = 退市交割强平和窗口末残仓清算的中价盈亏(很小)。funding − 冲击点差 − 手续费(不含基差)在 B 版五条规则下均为正(冠军 {(d.loc['base|E7xX5'].funding_u+d.loc['base|E7xX5'].impact_u+d.loc['base|E7xX5'].fees_u)/1e4:,.0f} 万),与审查官对 v12 原始 A 版('纯费率'为 −162 万、净利全靠基差)不同(规则与退出口径已不同);本表中基差收敛贡献 19~28 个百分点。基差项对 VWAP 取价与成交量假设同样敏感,本回测无法独立验证,是'基差收敛是否真实可得'的主要不确定项。\n")
# 5
A("## 19. 资金占用与月度(含不完整月标注)\n")
rows = []
for r in R:
    b = d.loc[f"base|{r}"]
    rows.append([LB[r], f"{b.avg_cost_used_u/1e4:,.0f} ({b.avg_cost_used_u/1e5:.0f}%)", f"{b.avg_used_is_u/1e4:,.0f}", f"{b.avg_used_ho_u/1e4:,.0f}", f"{b.peak_cost_used_u/1e4:,.0f}", f"{b.peak_mtm_used_u/1e4:,.0f}", f"{b.hrs_mtm_gt_S_pct:.1f}%", f1(b.ann), f1(b.ann_on_avg_used)])
A(tab(["规则", "平均占用(成本,万U/占1000万)", "IS 平均占用(市值)", "HO 平均占用(市值)", "峰值(成本)", "峰值(市值)", "市值>1000万的小时", "年化%(分母1000万)", "年化%(分母=平均成本占用,仅参考)"], rows))
A("占用 = 单腿名义(现货腿);成本口径峰值被 1000 万上限卡住,市值口径(按收盘价重估单腿名义)峰值可达 1.4~1.5 倍,因为引擎只对成本口径设 1000 万上限、未对市值做减仓。按平均占用的年化只用于说明资金效率,不是可承诺收益(闲置资金的机会成本、峰值保证金需求都未计入)。\n")
mc = [c for c in d.columns if c.startswith("M20")]
lab = {"M2025-10_u": "2025-10(仅 4 天,10/28–10/31)†", "M2026-10_u": "2026-10(仅 27 天,10/1–10/27)†"}
rows = [[lab.get(c, c[1:8])] + [w(d.loc[f"base|{r}", c]) for r in R] for c in mc]
tot = lambda r: (d.loc[f"base|{r}", mc[0]] + d.loc[f"base|{r}", mc[-1]])
rows.append(["两个 10 月合并(31 天,按 1 个月)"] + [w(tot(r)) for r in R])
A(tab(["月份(万U净利)"] + [LB[r] for r in R], rows))
pos = [int(((d.loc[f"base|{r}", mc[1:-1]] > 0).sum() + (tot(r) > 0))) for r in R]
A(f"† 首末月不完整,不能按月年化;合并后共 12 个月。盈利月数(合并后 /12):" + "、".join(f"{LB[r]} {p}" for r, p in zip(R, pos)) + "。冠军去掉最好的 2026-02 后净利仍有 " + f"{(d.loc['base|E7xX5'].net_u - d.loc['base|E7xX5','M2026-02_u'])/1e4:,.0f} 万(相当于 1000 万分母下全年 {(d.loc['base|E7xX5'].net_u - d.loc['base|E7xX5','M2026-02_u'])/1e7*100:.1f}%;只是把该月利润扣掉,未重新回测)。\n")
# summary
b = d.loc["base|E7xX5"]; cc = d.loc["cool24|E7xX5"]
A("## 20. 小结(不改选择)\n")
A(f"1. **冷却**:24h 冷却对 5 条规则的年化影响为 {min(d.loc['cool24|'+r].ann-d.loc['base|'+r].ann for r in R):+.1f} ~ {max(d.loc['cool24|'+r].ann-d.loc['base|'+r].ann for r in R):+.1f} 个百分点,冠军 {f1(b.ann)}→{f1(cc.ann)};冷却没有救回弱规则(E1×X1(B) 再入场 <24h 占 {d.loc['base|E1xX1B'].reentry_lt24_share:.0f}%,冷却后仍 {f1(d.loc['cool24|E1xX1B'].ann)}),说明冠军的收益并非来自'平完又立刻重进'的偶然。")
A(f"2. **pov/冲击**:固定 30bp 下冠军在 pov 1/3/10/20% 为 {f1(d.loc['pov|fixed|0.01|E7xX5'].ann)}/{f1(d.loc['pov|fixed|0.03|E7xX5'].ann)}/{f1(d.loc['pov|fixed|0.1|E7xX5'].ann)}/{f1(d.loc['pov|fixed|0.2|E7xX5'].ann)}%,变化温和(与审查官对 v12 原始 A 版 E1×X1 的 +33.8→−174.3 形成对比:B 版+E7/X5 的冠军不再靠'必亏短 episode'堆量);但换成平方根律(y=1)后 pov 3% 为 {f1(d.loc['pov|sqrt1.0|0.03|E7xX5'].ann)}%、pov 10% 为 {f1(d.loc['pov|sqrt1.0|0.1|E7xX5'].ann)}%,y=2 时 pov 3% 为 {f1(d.loc['pov|sqrt2.0|0.03|E7xX5'].ann)}%。**结论:冲击模型(随规模变化与否)比规则选择更重要,固定 30bp 的好结果依赖'小单、固定成本'假设**;REF 在 √律下衰减较慢(pov 10%、y=1 为 {f1(d.loc['pov|sqrt1.0|0.1|REF'].ann)}% vs 冠军 {f1(d.loc['pov|sqrt1.0|0.1|E7xX5'].ann)}%),可能因其 episodes 少一半(1242 vs 2678)、成交笔数少,未单独验证。")
A("3. **maker**:不能证明,需要校准(见第 17 节)。")
A(f"4. **分解**:冠军净利 {w(b.net_u)} 万 = funding {w(b.funding_u)} − 冲击点差 {abs(b.impact_u)/1e4:,.0f} − 手续费 {abs(b.fees_u)/1e4:,.0f} + 基差收敛 {w(b.basis_u)} + 其他 {w(b.other_liq_u)};基差收敛占净利 {b.basis_u/b.net_u*100:.0f}%,不是可忽略项。")
A(f"5. **资金**:冠军平均成本占用仅 {b.avg_cost_used_u/1e4:,.0f} 万({b.avg_cost_used_u/1e5:.0f}%),holdout 平均市值占用只有 {b.avg_used_ho_u/1e4:,.0f} 万;1000 万分母下的年化是'平均用六成资金'的结果。")
open(REP, "a").write("\n".join(L) + "\n")
print("\n".join(L))
