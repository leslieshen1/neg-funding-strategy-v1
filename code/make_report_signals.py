import os as _os
import pandas as pd, numpy as np
O = (_os.environ.get("SIGNALS_ROOT", ".") + "/out/")
g = pd.read_csv(O + "grid2.csv"); ex = pd.read_csv(O + "ex5_2.csv"); ks = pd.read_csv(O + "ksens.csv"); ke = pd.read_csv(O + "ksens_e1.csv"); mk = pd.read_csv(O + "maker2.csv")
W = lambda v: f"{v/1e4:,.0f}"; P = lambda v: f"{v:.1f}"
L = []; a = L.append
def sel(obs, imp=30): return g[(g.obs == obs) & (g.imp == imp)]
B = sel(1); Bc = B[B.e != "REF"].sort_values("is_ann", ascending=False).reset_index(drop=True); A = sel(0); Ac = A[A.e != "REF"].sort_values("is_ann", ascending=False).reset_index(drop=True)
ref = B[B.e == "REF"].iloc[0]
def full(imp, e, x, obs): r = g[(g.obs == obs) & (g.imp == imp) & (g.e == e) & (g.x == x)]; return r.iloc[0]
w = Bc.iloc[0]; wA = Ac.iloc[0]
a("\n---\n\n# 结果(以下在所有预先登记之后生成;数字单位:年化=占 10M 本金的年化 %;U=USDT,表中净收益/费用用「万 U」)\n")
a("## 5. 一句话结论\n")
a(f"- **样本内(2025-10-28~2026-06-30)冠军(B 版,49 组合里,30bp,IS 年化最高)= {w.e} × {w.x}**:样本内 {P(w.is_ann)}%,**样本外(7~10 月){P(w.ho_ann)}%**,全年 {P(w.ann)}%,净收益 {W(w.net_u)} 万 U,{int(w.episodes)} 笔。")
a(f"- A 版(出场触发含自身冲击,原来 35 个组合)的 IS 冠军 = {wA.e} × {wA.x}:样本内 {P(wA.is_ann)}%,样本外 {P(wA.ho_ann)}%,全年 {P(wA.ann)}%。")
e1x1a = full(30, 'E1', 'X1', 0); e1x1b = full(30, 'E1', 'X1', 1)
a(f"- 原纯净版 E1×X1:A 版全年 {P(e1x1a.ann)}%(样本内 {P(e1x1a.is_ann)}% / 样本外 {P(e1x1a.ho_ann)}%);**只把出场触发改成市场已结算费率(B 版)就变成 {P(e1x1b.ann)}%**(样本内 {P(e1x1b.is_ann)}% / 样本外 {P(e1x1b.ho_ann)}%)。也就是说,\"-0.05% 进、>=0 出\"的大部分问题**不是入场阈值,而是 A 版里自身冲击项让出场过早**(下面第 8 节)。")
a(f"- 样本内第一名在样本外仍为正且排第 {int(Bc.ho_ann.rank(ascending=False).iloc[0])}/49;49 个组合样本外全部为正(最差 {P(Bc.ho_ann.min())}%),样本内排名和样本外排名的相关系数(Spearman)= {Bc.is_ann.rank().corr(Bc.ho_ann.rank()):.2f}。")
a(f"- 对照 v11 调参规则(不在 49 个里):全年 {P(ref.ann)}%,样本内 {P(ref.is_ann)}%,样本外 {P(ref.ho_ann)}%。样本内比它高的组合有 {(Bc.is_ann>ref.is_ann).sum()} 个,样本外比它高的有 {(Bc.ho_ann>ref.ho_ann).sum()} 个。")
a("- **最重要的限制**:这些数都建立在 k_imp(自身冲击系数)和每腿 20/30/50bp 冲击这两个没标定的假设上(第 9 节);币清单是今天的快照;入场阈值族是看过第一年结果后才提的;挂单(maker)不可信,需要实盘试验(第 11 节)。\n")

def table(df, cols_fmt, head):
    a("| " + " | ".join(head) + " |"); a("|" + "---|" * len(head))
    for i, r in df.iterrows(): a("| " + " | ".join(f(r, i) for f in cols_fmt) + " |")
def row_fmt(obs, df):
    def get(r, imp): 
        t = g[(g.obs == obs) & (g.imp == imp) & (g.e == r.e) & (g.x == r.x)]; return t.iloc[0].ann
    fs = [lambda r, i: str(i + 1), lambda r, i: f"{r.e}×{r.x}", lambda r, i: P(r.is_ann), lambda r, i: P(r.ho_ann), lambda r, i: P(r.ann),
          lambda r, i: P(r.Q1_ann), lambda r, i: P(r.Q2_ann), lambda r, i: P(r.Q3_ann), lambda r, i: P(r.Q4_ann), lambda r, i: W(r.net_u), lambda r, i: str(int(r.episodes)),
          lambda r, i: W(r.fees_impact_u), lambda r, i: ("-" if np.isnan(r.exit_negfund_share) else P(r.exit_negfund_share)), lambda r, i: P(r.reentry24_share),
          lambda r, i: P(get(r, 20)), lambda r, i: P(get(r, 50))]
    return fs
HEAD = ["IS排名", "组合", "样本内年化%", "**样本外年化%**", "全年年化%", "Q1", "Q2", "Q3", "Q4", "净收益(万U)", "笔数", "费用+冲击(万U)", "出场时市场费率为负占比%", "24h内再进场占比%", "全年@20bp", "全年@50bp"]
a("## 6. 主表 B 版:出场触发只看市场已结算费率,7 入场 × 7 出场 = 49 组合(30bp,吃单,按样本内年化排序)\n")
a("Q1~Q4 = 从 2025-10-28 起每约 91 天一季(Q1→2026-01-27,Q2→04-28,Q3→07-28,Q4→10-28);样本内=前 246 天,样本外=后 119 天。**样本外列是单独的 4 个月,噪声很大。**\n")
table(Bc, row_fmt(1, Bc), HEAD)
a("\n**参考行(不在预登记 49 个里):v11 调参规则**\n")
rr = ref; a("| 规则 | 样本内 | 样本外 | 全年 | Q1 | Q2 | Q3 | Q4 | 净收益(万U) | 笔数 | 费用+冲击(万U) | 全年@20bp | 全年@50bp |\n|---|---|---|---|---|---|---|---|---|---|---|---|---|")
a(f"| 进场<-0.10% + 等待≤168h/0.3% | {P(rr.is_ann)} | {P(rr.ho_ann)} | {P(rr.ann)} | {P(rr.Q1_ann)} | {P(rr.Q2_ann)} | {P(rr.Q3_ann)} | {P(rr.Q4_ann)} | {W(rr.net_u)} | {int(rr.episodes)} | {W(rr.fees_impact_u)} | {P(full(20,'REF','REF',1).ann)} | {P(full(50,'REF','REF',1).ann)} |")
a("\n(调参规则的出场用\"费率<0 才继续等\"的逻辑,A/B 两版完全相同:自身冲击只会把负费率往 0 推,不会把正费率变负。)\n")
a("入场信号、出场信号的平均表现(49 个组合,30bp,B 版):\n")
m1 = Bc.groupby("x")[["is_ann", "ho_ann", "ann"]].mean().round(1); m2 = Bc.groupby("e")[["is_ann", "ho_ann", "ann"]].mean().round(1)
a("| 出场 | 样本内均值 | 样本外均值 | 全年均值 |\n|---|---|---|---|"); 
for k, r in m1.iterrows(): a(f"| {k} | {r.is_ann} | {r.ho_ann} | {r.ann} |")
a("\n| 入场 | 样本内均值 | 样本外均值 | 全年均值 |\n|---|---|---|---|")
for k, r in m2.iterrows(): a(f"| {k} | {r.is_ann} | {r.ho_ann} | {r.ann} |")
a("\n读法:出场\"越有耐心\"(X2~X5)越好,\"费率一回到 0 就走\"(X1)和\"带缓冲就走\"(X6)、\"预期收入低于成本就走\"(X7)都差——因为每次进出要付约 1.5%(30bp 档,来回),X7 在预期收入刚好不够时频繁进出(各入场下 2 千~3.6 万笔,约 92%~96% 的出场发生在市场费率仍为负时),亏在成本上。入场方面,E7(永续折价>0.3%)和 E2(<-0.10%)平均最好,E5(缩短周期)最差,因为交易太少(约 250~400 笔)。\n")

a("## 7. A 版(原 35 组合,出场触发含自身冲击 k=4;30bp,按样本内年化排序)——保留,供对照\n")
table(Ac, row_fmt(0, Ac), HEAD)
a("")

a("## 8. 出场:自身冲击 vs 市场费率,再进场与持有时长\n")
x1 = A[(A.x == "X1") & (A.e != "REF")]
a(f"- A 版 X1:出场发生时市场已结算费率仍为负的比例 {P(x1.exit_negfund_share.min())}%~{P(x1.exit_negfund_share.max())}%(E1×X1 = {P(e1x1a.exit_negfund_share)}%,与独立复核的 57.6% 一致)。B 版 X1 按定义为 0%。")
a(f"- 24 小时内同一个币再次进场的比例:E1×X1 A 版 {P(e1x1a.reentry24_share)}% → B 版 {P(e1x1b.reentry24_share)}%;B 版冠军 {P(w.reentry24_share)}%;调参规则 {P(ref.reentry24_share)}%。比例高 = 反复进出,每次都付一次来回成本。")
a("\n持有时长分档(30bp,B 版;笔数 / 该档净收益万U;净收益 = 价差+资金费−手续费−冲击,逐笔):\n")
a("| 组合 | <24h | 24~72h | 72~168h | >168h | 平均持有(小时) |\n|---|---|---|---|---|---|")
def hs(r, name): a(f"| {name} | " + " | ".join(f"{int(r['n_'+k])} / {W(r['net_'+k+'_u'])}" for k in ("lt24", "d24_72", "d72_168", "gt168")) + f" | {r.avg_hold_h:.0f} |")
for i in range(3): hs(Bc.iloc[i], f"{Bc.e[i]}×{Bc.x[i]}")
hs(e1x1b, "E1×X1 (B)"); hs(e1x1a, "E1×X1 (A)"); hs(ref, "v11 调参规则")
a("\n读法:几乎所有利润来自**持有超过 1 周的少数笔**;持有不到 3 天的笔数不少,但合计净收益为负或接近 0。这也是\"耐心出场\"赢的原因。\n")

a("## 9. 自身冲击 k 的敏感性(30bp,吃单;k = 我们每占 1% OI,资金费率被抬高 k bp/8h;全年年化% / 样本外年化%)\n")
a("| 组合 | 出场触发 | k=0 | k=2 | **k=4(基准)** | k=8 |\n|---|---|---|---|---|---|")
def krow(df, e, x, obs, nm):
    t = df[(df.e == e) & (df.x == x) & (df.obs == obs)].set_index("k"); 
    a(f"| {nm} | {'市场费率(B)' if obs else '含自身冲击(A)'} | " + " | ".join(f"{t.loc[k].ann:.1f} / {t.loc[k].ho_ann:.1f}" for k in (0, 2, 4, 8)) + " |")
for e, x in [("E1", "X1"), ("E1", "X2"), ("E1", "X4")]:
    for o in (0, 1): krow(ke, e, x, o, f"{e}×{x}")
for i in range(5):
    for o in (1, 0): krow(ks, Bc.e[i], Bc.x[i], o, f"{Bc.e[i]}×{Bc.x[i]}")
for o in (1,): krow(ks, "REF", "REF", o, "v11 调参规则")
a("\n读法:① k 越大越差,k 没标定,**年化从 k=0 到 k=8 差一倍**;② **A 版的 E1×X1 在 k=8 翻成负(−10.4%)**,B 版不翻——复核指出的\"符号被 k 决定\"只对 A 版成立;③ 排名前 5 的组合和调参规则在 k=0~8 全部为正,但幅度差很大。k 需要用真实 OI/资金费对仓位的反应来标定。\n")

a("## 10. 剔除利润最多的 5 个币(30bp;币按全年净收益事后排名,是压力测试不是选币)\n")
a("| 组合 | 出场触发 | 全年 | 剔除后全年 | 样本内 | 剔除后样本内 | 样本外 | 剔除后样本外 | 前5币占利润% |\n|---|---|---|---|---|---|---|---|---|")
for _, r in ex.iterrows():
    nm = r["name"].split("|"); a(f"| {nm[0]}×{nm[1]} | {'A' if r['name'].endswith('obs0') else 'B'} | {P(r.ann)} | {P(r.ex5_ann)} | {P(r.is_ann)} | {P(r.ex5_is_ann)} | {P(r.ho_ann)} | {P(r.ex5_ho_ann)} | {P(r.top5_share)} |")
a("\n(B 版前 5 名 + v11 调参规则 + A 版前 5 名。剔除后全部仍为正,利润集中度约 30%,剔除后年化约降 1/4~1/3。)\n")

a("## 11. 挂单(maker)——只做提示,**不可信,需要实盘小额试验**(30bp,B 版出场,ADL 开)\n")
a("跳空(gap)改为双向计价(对我们有利的一侧也记账)。对象:B 版冠军与 v11 调参规则。全年年化% / 样本内 / 样本外:\n")
a("| 组合 | 模式 | 成交率 | gap单向(旧) | **gap双向(新)** | 对冲腿极值额外成本(万U) | 逆选择成本(万U) |\n|---|---|---|---|---|---|---|")
for e, x in [(Bc.e[0], Bc.x[0]), ("REF", "REF")]:
    for mm, lab, fr in (("ii_50", "永续maker+现货taker", "50%"), ("ii_100", "永续maker+现货taker", "100%"), ("iii_50", "双maker", "50%"), ("iii_100", "双maker", "100%")):
        t = mk[(mk.e == e) & (mk.mm == mm)].set_index("gap_sym")
        f = lambda r: f"{r.ann:.1f} / {r.is_ann:.1f} / {r.ho_ann:.1f}"
        a(f"| {e}×{x} | {lab} | {fr} | {f(t.loc[0])} | {f(t.loc[1])} | {W(t.loc[1].hedge_extreme_u)} | {W(t.loc[1].adverse_u)} |")
t0 = mk[(mk.e == Bc.e[0]) & (mk.mm == "i")].iloc[0]; a(f"\n吃单基准:{Bc.e[0]}×{Bc.x[0]} {t0.ann:.1f}%;v11 调参规则 {P(ref.ann)}%。")
a("\n**模型有问题的信号**:成交率 100% 比 50% 更差(例如冠军 永续maker 50% → 100% 反而大幅下降)。成交率越高应该越好,方向反了,说明挂单行主要在测\"对冲腿按整小时最高/最低价成交\"和\"逆选择叠加\"这两个悲观假设,不是真实的挂单经济学。gap 改双向后 50% 的数明显回升(冠军 +30、调参规则 +22 个百分点),100% 几乎不变(因为 100% 时没有下一小时补单)。结论:**挂单结果不能用来下结论,必须小额实盘试验**(用真实成交价/成交率标定)。\n")

a("## 12. 稳健性小结\n")
b20 = g[(g.obs == 1) & (g.imp == 20) & (g.e != 'REF')]; b50 = g[(g.obs == 1) & (g.imp == 50) & (g.e != 'REF')]
a(f"- 冲击成本:B 版 49 个组合全年为正的个数:20bp {int((b20.ann>0).sum())}/49,30bp {int((Bc.ann>0).sum())}/49,50bp {int((b50.ann>0).sum())}/49。冠军 {w.e}×{w.x}:20bp {P(full(20,w.e,w.x,1).ann)}% / 30bp {P(w.ann)}% / 50bp {P(full(50,w.e,w.x,1).ann)}%。")
a(f"- 样本内前 5 名在样本外:{', '.join(f'{Bc.e[i]}×{Bc.x[i]} {P(Bc.ho_ann[i])}%(第{int(Bc.ho_ann.rank(ascending=False)[i])}名)' for i in range(5))}。")
a(f"- 收益构成(冠军,30bp):资金费 {W(w.funding_u)} 万U,价差 {W(w.price_u)} 万U,手续费 {W(w.fees_u)},冲击 {W(w.impact_u)}(万U)。价差项在几乎所有组合里都为正(含 E1×X1),E7 入场还会吃到永续折价收敛;这部分不是资金费,来源未单独拆解。窗口末尚未平仓部分按引擎口径清算(约 {W(w.residual_end_u)} 万U 名义)。")

a("\n## 13. 注意事项(请务必看)\n")
for s in [
 "**样本外只有 4 个月**,样本外各组合年化(约 50~70%)普遍低于样本内(约 80~100%);另外 Q3(2026-04-28~07-28)全线明显偏弱(49 个组合均值 16%,其余季度 64~106%),它横跨样本内外切分点;单独看样本外噪声很大;不能当作\"已证明\"。",
 "**49 个里挑最好**有赢家诅咒:样本内冠军的样本外表现只能当参考。好在样本内/样本外排名相关性较高,且前几名都是同一族(E7/E2 × 耐心出场)。",
 "**币清单是今天的库存快照**(事后选出来的可借币),**前 5 币的排名也是事后的**;剔除前 5 不等于真正的无事后诸葛。",
 "**阈值族是用户看过第一年结果后提的**,第 1~3 节的 A 版已先跑过再收到复核意见,第二轮(B 版、X6/X7、k、maker)是之后补的并在运行前登记——不是完全干净的预登记。B 版作为\"主线\"是按复核意见定的,不是按结果挑的。",
 "**成本和资金费几乎同量级**:全年费用+冲击中位约 400 万 U(范围 80~1040 万 U),与净收益同量级,结论对 20/30/50bp 和 k 都敏感。",
 "**一次连续模拟**:样本内/样本外切分点处的持仓会跨过去;窗口首尾月不完整;窗口末持仓按引擎口径清算。",
 "没有预测资金费率的历史数据,所以没有使用(没有用别的东西顶替);X7 的\"预期剩余收入\"只用过去 24 小时已结算费率,假设再持有 168 小时,是一个粗糙的估计。",
 "出场时序:信号读取与 v12 纯净版一致(第 t 小时用截至 t 小时已结算的费率,下单在 t 小时内成交),未在真实盘口验证;ADL 过滤为代理指标。",
 "隐私:没有输出任何逐币库存数量/可借额度,没有使用或输出 API key;文件里只有汇总数字。"]: a("- " + s)
a("\n## 14. 文件\n- `code/engine_v12s.py`(引擎副本:新增出场信号 X2–X7、出场触发读市场费率、gap 双向开关、出场诊断计数;v10/v11/v12 原文件未改)、`code/lib12s.py`、`code/run_signals.py`、`code/run_k_pure.py`、`code/make_report_signals.py`\n- `out/grid2.csv`(A/B 全部组合×3 档冲击)、`out/ex5_2.csv`、`out/ksens.csv`、`out/ksens_e1.csv`、`out/maker2.csv`;`out/grid_signals.csv`、`out/ex5_signals.csv` 为第一轮 A 版原始结果(与 grid2 的 A 版一致)。")
open((_os.environ.get("SIGNALS_ROOT", ".") + "/REPORT_signals.md"), "a").write("\n".join(L) + "\n")
