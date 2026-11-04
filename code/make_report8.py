"""Generate 第八轮 section (fixed forced-de-risk engine, v9 comparison, KuCoin variant) from aggregate CSVs. Aggregates only."""
import os, numpy as np, pandas as pd
H = os.path.dirname(os.path.abspath(__file__)) + "/../"; O = H + "out/"; KC = H + "kucoin/out/"
L = []
def P(s=""): L.append(s)
def f1(x): return f"{x:.1f}"
def wan(x): return f"{x/1e4:,.0f}"
def ann_avgc(d): return d.net_u / d.avg_cost_used_u / (d.days / 365) * 100
def tbl(hdr, rows): P("| " + " | ".join(hdr) + " |"); P("|" + "---|" * len(hdr)); [P("| " + " | ".join(map(str, r)) + " |") for r in rows]; P()
sc = pd.read_csv(O + "r7_scen.csv"); sc["avgc"] = ann_avgc(sc); lg = pd.read_csv(O + "r7_legacy_bound.csv"); lg["avgc"] = ann_avgc(lg)
nm = {"frozen_m2fb_c48": "**冻结:闸门 m=2 + X5/48h**", "newgate_c24": "闸门 m=2 + X5/24h", "oldgate_c24": "旧闸门 m=3 + X5/24h", "nogate_c24": "无闸门 + X5/24h"}
P("# 第八轮:强制降风险引擎修复 + v9 对比 + KuCoin 现货/Binance 永续变体")
P()
P("> **本节取代 §7.2、§7.3、§7.4b 与 §7.6 中的数字**(那些数字来自旧引擎 `derisk_force=1`,保留在 `out/legacy_derisk1/` 供审计)。§7.0 的预注册文字、§7.4 的 IS 选择过程、§7.1 的校准结果不变——**但要注意:冻结规则(m=2、X5/48h)是在旧引擎下用 IS 选出来的,修复引擎后没有重新选择**(重新选择会让 HO 不再是样本外)。")
P()
P("## 8.1 审计员发现的 bug 与修复(请先读这一节)")
P()
P("**bug 是什么**:旧引擎在小时内发现仓位超过成交量/OI 上限时,会**同小时全部砍回**(`derisk_force=1`),这一笔不受 pov 3% 预算约束(在冻结规则下,这类'超出 pov 预算的强制砍单'约占总成交额的 22.6%(IS)/ 26.3%(HO))。第七轮报告写的是'超出部分按外推平方根冲击额外计价',但代码里:")
P("- **30bp 情景**:这笔额外冲击**根本没有收**(只收了固定 30bp)。")
P("- **cal 情景**:整笔砍单本来就按平方根律计价,'超出部分的额外项'恒不超过整笔项,所以额外项是多余的——cal 情景里那句话碰巧近似成立,但 30bp 情景里不成立。")
P()
P("**修复(`derisk_force=2`,现在的默认)**:强制降风险**遵守 pov 3% 的同小时预算,超出的部分留到下一小时继续砍**;还没砍掉的部分就是'超出上限的残余敞口'(诊断量 `xd[52..61]`)。因此:")
P("- 强制减仓不再超过 pov 预算（退出成交未单独验证）(`forced_excess_over_pov = 0`);")
P("- 代价是**仓位会在上限之上多停留若干小时**(见 §8.2.3):这是新的风险,不是消失了。")
P("- 因此给出**两个边界**:**(a) 遵守 pov(新默认)**:成交现实,但残余敞口超上限;**(b) 旧的同小时全砍 + 超出部分按平方根额外计价(`legacy cut`,`bp30c` 情景 = bp30 + 平方根额外项)**:不超上限,但假设市场能接住大单。真实表现应落在两者之间或更差。")
P("- 验证:`NFB_DERISK=1` 能逐位复现旧数字(`out/legacy_derisk1/`);v9 的引擎在我们的引擎里复现与原 v9 逐日差 0.00。")
P()
P("## 8.2 修正后的第七轮结果(10M,taker,硬上限开,同小时,库存 A;**修复引擎,遵守 pov**)")
P()
P("### 8.2.1 主表(cal 成本;年化 % 的四个分母;金额单位万 U)")
P("分母:**10M** = 净利/10M/年数;**峰值成本占用**、**峰值市值占用** = 用于建仓/市值的资金峰值;**平均占用** = 净利/平均成本占用/年数(平均占用是被动闲置之外实际在用的钱,所以数字最大,但也最依赖'闸门多挑剔')。")
rows = []
for w in ("IS", "HO"):
    for c in nm:
        r = sc[(sc.cfg == c) & (sc.scen == "cal") & (sc.win == w)].iloc[0]
        rows.append([nm[c], w, f1(r.ann10), f1(r.ann_pkc), f1(r.ann_pkm), f1(r.avgc), wan(r.net_u), wan(r.funding_u), wan(r.fees_u), wan(r.slip_u), wan(r.basis_u), wan(r.traded_u), int(r.episodes), f1(r.avg_hold_h), f1(r.ex5_ann), f1(r.top5_share)])
tbl(["规则", "窗口", "年化(10M)", "年化(峰值成本占用)", "年化(峰值市值占用)", "年化(平均占用)", "净利", "funding", "手续费", "冲击+价差", "基差收敛", "成交额", "次数", "平均持有h", "去前5币年化", "前5币占比%"], rows)
P("(IS 246 天,HO 119 天,各自冷启动。)**和旧引擎相比**:冻结规则 IS 89.2→95.2、HO 48.1→57.1(cal)。变高**不是因为变好**:是因为强制砍单不再被收额外冲击,而仓位在上限之上多停了(§8.2.3)。旧引擎(同小时全砍)的数字见 §8.2.2。")
P()
P("### 8.2.2 两个边界:遵守 pov(新)vs 同小时全砍(旧,假设市场能接住大单)")
rows = []
for w in ("IS", "HO"):
    n = sc[(sc.cfg == "frozen_m2fb_c48") & (sc.win == w)].set_index("scen")
    l = lg[lg.win == w].set_index("scen")
    for lab, d, s in (("遵守 pov(新默认)cal", n, "cal"), ("同小时全砍 cal(旧;整笔平方根)", l, "cal"), ("遵守 pov bp30", n, "bp30"), ("同小时全砍 bp30(旧;**未额外收费**)", l, "bp30"), ("同小时全砍 bp30c(bp30 + 超出部分平方根 Y=1)", l, "bp30c")):
        r = d.loc[s]; rows.append([lab, w, f1(r.ann10), f1(r.ann_pkc), f1(r.avgc), wan(r.slip_u), wan(r.net_u)])
tbl(["口径(冻结规则)", "窗口", "年化(10M)", "年化(峰值成本占用)", "年化(平均占用)", "冲击+价差", "净利"], rows)
x = lg[(lg.scen == "bp30c")].set_index("win"); y = lg[(lg.scen == "bp30")].set_index("win")
P(f"- 旧口径下的同小时全砍成交额占总成交额:IS {f1(lg[(lg.scen=='cal')&(lg.win=='IS')].excess_share_traded.iloc[0])}%、HO {f1(lg[(lg.scen=='cal')&(lg.win=='HO')].excess_share_traded.iloc[0])}% 是'超出 pov 预算的部分'。")
P(f"- 补上缺失的额外收费(bp30c)后,旧口径 bp30 的年化下降:IS {f1(y.loc['IS'].ann10)}→{f1(x.loc['IS'].ann10)}(−{f1(y.loc['IS'].ann10-x.loc['IS'].ann10)}pp)、HO {f1(y.loc['HO'].ann10)}→{f1(x.loc['HO'].ann10)}(−{f1(y.loc['HO'].ann10-x.loc['HO'].ann10)}pp)。")
P("- **怎么读**:新默认(遵守 pov)的年化高于旧口径,但它多承担了超上限的残余敞口(§8.2.3);旧口径更保守地假设'可以瞬间砍掉,按平方根付费'。**两者之间没有哪一个是真实值**,请把 cal 下的区间当作 IS 89–95%、HO 48–57%(10M 口径)。")
P()
P("### 8.2.3 硬上限与残余敞口诊断(冻结规则,遵守 pov;cal 成本)")
hc = pd.read_csv(O + "r7_hardcap.csv"); hc = hc[hc.cfg == "frozen_c48"].set_index("win")
rows = []
for w in ("IS", "HO"):
    r = hc.loc[w]; rows.append([w, f"{r.volcap_pct:.2f}%", f"{r.oicap_pct:.2f}%", f"{r.max_vol_ratio:.1f}×", f"{r.max_oi_ratio:.1f}×", int(r.resid_hours), int(r.r_lt125), int(r.r_125_2), int(r.r_2_5), int(r.r_gt5), int(r.zero_cap_hours), f"{r.forced_excess_over_pov_u:.0f}"])
tbl(["窗口", "超成交量上限的币小时占比", "超 OI 上限占比", "最大超限(成交量)", "最大超限(OI)", "残余敞口币小时", "<1.25×", "1.25–2×", "2–5×", ">5×", "上限=0 的小时", "超出 pov 的强制成交额"], rows)
P("- 旧引擎的数字(同小时全砍,超限币小时 IS 0.28%、HO 0.71%)已作废:新口径下仓位**确实**在上限之上停留更久(IS 13.8%、HO 18.9% 的持仓币小时),最大 12–15 倍成交量上限,OI 最大 8.2 倍(HO)。**这是'obey pov'的代价,也是为什么要同时给出旧口径**。")
P()
P("### 8.2.4 成本情景(年化 % 10M,IS / HO;修复引擎,遵守 pov;成本只改实际成交,闸门不变)")
rows = []
for c in nm:
    row = [nm[c]]
    for s in ("cal", "sqrt1", "bp30", "book"):
        a = sc[(sc.cfg == c) & (sc.scen == s)].set_index("win"); row.append(f"{a.loc['IS'].ann10:.1f} / {a.loc['HO'].ann10:.1f}")
    rows.append(row)
tbl(["规则", "cal(主)", "sqrt y=1(保守)", "bp30(旧口径)", "book(乐观端)"], rows)
P("**同样没有重新选参。**'book'是乐观端、'cal/sqrt1'是主要估计;在 HO 上各规则之间的差都在 7 天块自助 CI 内(下表)。")
P()
P("### 8.2.5 7 天块自助 95% 置信区间(冻结规则 − 对照,日净利差折合 10M 年化 pp;5000 次)")
bt = pd.read_csv(O + "r7_bootstrap.csv"); rows = []
for s in ("cal", "bp30", "book"):
    for v in ("newgate_c24", "oldgate_c24", "nogate_c24"):
        a = bt[(bt.scen == s) & (bt.vs == v)].set_index("win"); rows.append([s, {"newgate_c24": "闸门 m=2 + X5/24h", "oldgate_c24": "旧闸门 m=3", "nogate_c24": "无闸门"}[v]] + [f"{a.loc[w].diff_ann_pp:+.1f} [{a.loc[w].lo:+.1f}, {a.loc[w].hi:+.1f}]" for w in ("IS", "HO")])
tbl(["成本情景", "对照", "IS 差 [95%CI]", "HO 差 [95%CI]"], rows)
P("→ **在修复引擎下,新闸门相对旧闸门的优势在 IS 只剩 +4.2pp [−0.2, +8.8](旧引擎 +4.6 [+1.3, +8.6]),CI 已经包含 0;相对无闸门仍显著(+7.8 [+3.2, +12.9])。HO 上所有差异的 CI 都包含 0。** 在 bp30 与 book 情景下,闸门的相对优势消失甚至反转(成本越低,挑剔的闸门越没有用)。48h vs 24h 出场的差(IS +0.2、HO +2.1)统计上不显著。")
P()
P("### 8.2.6 按持有时长的 PnL(冻结规则,cal,修复引擎;万 U)")
rows = []
for w in ("IS", "HO"):
    r = sc[(sc.cfg == "frozen_m2fb_c48") & (sc.scen == "cal") & (sc.win == w)].iloc[0]
    rows.append([w, f"{int(r.n_lt24)} 次 / {wan(r.net_lt24_u)}", f"{int(r.n_d24_72)} 次 / {wan(r.net_d24_72_u)}", f"{int(r.n_d72_168)} 次 / {wan(r.net_d72_168_u)}", f"{int(r.n_gt168)} 次 / {wan(r.net_gt168_u)}"])
tbl(["窗口", "<24h", "24–72h", "72–168h", ">168h"], rows)
P("几乎全部利润来自持有超过一周的仓位。")
P()
P("### 8.2.7 HO 的集中度(冻结规则,cal;逐日净利按月汇总;修复引擎)")
d = np.load(O + "r7_daily/v9cmp_FINAL_339__cal__HO.npy"); k = len(d) // 24 * 24; dd = d[:k].reshape(-1, 24).sum(1); s = pd.Series(dd, pd.date_range("2026-07-01", periods=len(dd)))
g = s.groupby(s.index.month).agg(["sum", "count"]); g["ann"] = g["sum"] / 10e6 / (g["count"] / 365) * 100; g["share"] = g["sum"] / s.sum() * 100
rows = [[f"2026-{m:02d}", int(r["count"]), wan(r["sum"]), f1(r.ann), f1(r.share)] for m, r in g.iterrows()]
tbl(["月份", "天数", "净利(万U)", "月内年化(10M,%)", "占 HO 净利%"], rows)
r = sc[(sc.cfg == "frozen_m2fb_c48") & (sc.scen == "cal") & (sc.win == "HO")].iloc[0]
P(f"**HO 严重集中**:9 月一个月就占 HO 净利的约 {f1(g.loc[9].share)}%(月内年化 {f1(g.loc[9].ann)}%),10 月(27 天)只有 {f1(g.loc[10].ann)}%;前 5 个币占净利 {f1(r.top5_share)}%,去掉前 5 币年化只剩 {f1(r.ex5_ann)}%(IS 去前 5 币 {f1(sc[(sc.cfg=='frozen_m2fb_c48')&(sc.scen=='cal')&(sc.win=='IS')].iloc[0].ex5_ann)}%)。**不要把 HO 的 57% 当作稳态收益**;一个更诚实的读法是'HO 去前 5 币 ≈ 20%,最近一个月 ≈ 25%'。(旧引擎下对应数字是 9 月 55%、10 月 ≈10%、前 5 66%、去前 5 16%,方向一致。)")
P()
P("## 8.3 对照 1:v9 与第七轮最终规则在同一设定下(同窗口、同分母、同 10M)")
P()
P("**v9 源码核对**(仓库 `neg-funding-backtest`@`dbe839a`,只读):入场=预估费率 < −10bp;等待 168h / 0.3% 后才允许出场;允许无限加仓;参与预算 = 前一小时成交额的 20%,24h 成交量上限 10%,OI 上限 10%;手续费现货 10bp / 永续 5bp;冲击固定 30bp;**没有闸门、没有 ADL 掩码、没有同小时 pov 3%**。**币池 267 个是事后挑选的**,**参数在同一窗口内调过,没有样本外**。因此 v9 的原数字不是样本外数字,我们这里只比'同一个环境下规则本身'的差别。")
P("- v9 的引擎已放进我们的引擎里复现(桥接步骤 S0):与 v9 原结果逐日净利差 **0.00**(IS 与 HO)。")
bg = pd.read_csv(O + "r7_v9bridge.csv"); bg["avgc"] = ann_avgc(bg)
labs = {"S0_v9like": "S0 v9 引擎(pov 20% 前一小时,无硬上限,30bp)", "S1_samehour": "S1 改为同小时 pov 20%", "S2_pov3": "S2 pov 3% 同小时", "S3_hardcap": "S3 硬上限(10% 成交量/OI;遵守 pov 后与 S2 相同)", "S4_adl": "S4 + ADL 掩码"}
P()
P("### 8.3.1 桥接阶梯:从 v9 到'第七轮环境 + v9 规则'(pool 267,bp30,年化%)")
rows = []
for st, lab in labs.items():
    r = [lab]
    for w in ("IS", "HO"):
        a = bg[(bg.step == st) & (bg.win == w)].iloc[0]; r += [f1(a.ann10), f1(a.ann_pkc), f1(a.ann_pkm), f1(a.avgc)]
    rows.append(r)
tbl(["步骤", "IS 10M", "IS 峰值成本", "IS 峰值市值", "IS 平均占用", "HO 10M", "HO 峰值成本", "HO 峰值市值", "HO 平均占用"], rows)
P("注:'S3 硬上限'在修复后与 S2 结果完全相同(强制降风险现在遵守 pov 预算,没有额外成交)。")
P()
P("### 8.3.2 同一环境下的规则对比(pool 267 / 339;年化%,四个分母)")
v = pd.read_csv(O + "r7_v9cmp.csv"); v["avgc"] = ann_avgc(v)
cn = {"REF_ADL": "v9 规则(入场 −10bp,等 168h/0.3%)", "REF_noADL": "v9 规则,无 ADL", "OLDGATE24": "旧闸门 m=3 + X5/24h", "NOGATE24": "无闸门 + X5/24h", "FINAL24": "m=2 闸门 + X5/24h", "FINAL": "**冻结:m=2 + X5/48h**"}
for scn in ("cal", "bp30"):
    P(f"**{scn} 成本**")
    rows = []
    for c, lab in cn.items():
        r = [lab]
        for pool in (267, 339):
            for w in ("IS", "HO"):
                a = v[(v.cfg == c) & (v.scen == scn) & (v.win == w) & (v.pool == pool)].iloc[0]; r.append(f"{a.ann10:.1f} / {a.ann_pkc:.1f} / {a.ann_pkm:.1f} / {a.avgc:.1f}")
        rows.append(r)
    tbl(["规则(年化:10M / 峰值成本 / 峰值市值 / 平均占用)", "267 IS", "267 HO", "339 IS", "339 HO"], rows)
v9n = pd.read_csv(H + "v9cmp/out/v9_10M.csv").set_index(["var", "win"])
P(f"v9 原引擎(其自己的选择与参数,30bp,本地复现):IS {f1(v9n.loc[('V9_real','IS')].ann10)}%、HO {f1(v9n.loc[('V9_real','HO')].ann10)}%(10M 分母,与峰值成本占用相同);峰值市值占用口径 IS {f1(v9n.loc[('V9_real','IS')].ann_pkm)}%、HO {f1(v9n.loc[('V9_real','HO')].ann_pkm)}%。")
P("(`V9_opt` 是 v9 在同窗口里调出来的参数,IS 135.5% / HO 108.5%;它是**在这两个窗口上调优的**,不应与冻结规则比较。)")
P()
P("### 8.3.3 7 天块自助(pool 267;日净利差折合 10M 年化 pp)")
vb = pd.read_csv(O + "r7_v9boot.csv"); rows = []
for _, r in vb.iterrows(): rows.append([r.win, r.scen, r["cmp"], f"{r.diff_ann_pp:+.1f} [{r.lo:+.1f}, {r.hi:+.1f}]"])
tbl(["窗口", "成本", "比较", "差 [95%CI]"], rows)
P("**读法(诚实版)**:")
P("1. v9 规则放进第七轮环境(同小时 pov、硬上限、ADL、cal 成本)后,IS 年化从 75.9%(v9 原引擎,30bp)变为 69.2%(cal)/ 82.4%(bp30);**bp30 下,第七轮环境比 v9 引擎略好(+6.5pp [+2.4, +10.5]),cal 下略差(−6.7pp)**——也就是说,**'v9 规则是否被第七轮环境改善'取决于成本假设,不是确定结论**。")
P("2. 冻结规则(m=2 闸门)相对 v9 规则(同一环境):IS 显著更好(cal +24.6pp [+17.9, +31.3];bp30 +21.1pp [+14.4, +28.1]);HO 也更好(cal +16.9pp [+4.6, +30.7];bp30 +11.6pp [+1.0, +22.2])。**但相对 v9 原引擎(30bp、pov 20%)**,HO 上差异 CI 很宽且含 0(cal −2.9pp [−30.4, +18.4];bp30 +6.0pp [−19.4, +26.1])。")
P("3. **v9 的选择与调参不同**:v9 的 267 币池是事后挑选的,参数在同窗口内调过;第七轮冻结规则的 m、conf_h 在 IS 选、HO 看一次;**但 HO 在前几轮已经看过**(见 §8.5),所以冻结规则也不是干净的样本外。两边都不能当作前瞻性证据。")
P("4. 分母:v9 规则占用资金大(平均成本占用:IS 约 950 万 U、HO 约 490 万 U),冻结规则占用小(IS 约 710 万、HO 约 330 万);按峰值成本占用算,冻结规则 HO 年化 ≈ 91%、v9 规则 ≈ 40%;按 10M 算分别 57% 与 40%(pool 339,cal)。**收益来自'少占钱、挑得准',但这在 HO 上同样高度集中(§8.2.7)。**")
P()
P("## 8.4 对照 2:KuCoin 现货 + Binance 永续变体(预注册 `kucoin/PREREG_kucoin.md`,写于看到任何 KuCoin 结果之前;其 §8 记录了之后的两处更正)")
P()
P("**更正与披露**:第一次 KuCoin 回测因我的数据构造 bug(引擎用的'现货小时 VWAP 价'错填成了成交量)无效,发现于'资金费收入≈0 而基差收益巨大',已修复并重跑,规则未改;KuCoin 的 K 线接口会为无成交小时返回'成交量 0、价格=上一收盘'的平线 K 线(6.6% 的 K 线),等于交易所替我们填充,已把这些小时当作不可成交(成交量 0、`sv`=NaN)。**硬检查:'无成交或无 K 线的小时里仓位数量发生变化'的次数 = 0**(FINAL 与 REF 在 IS 与 HO 均为 0)。")
P()
u = pd.read_csv(H + "kucoin/ds/dataset_meta.csv"); uk = u.kc_keep
P("### 8.4.1 币种集合(交集)与丢币数")
tbl(["项", "数量"], [["币安起始集合(339 币:267 币池 + 72 扩展)", 339], ["保留(KuCoin 有同名 USDT 现货对,价格比值通过检查,小时数≥200)", int(uk.sum())], ["丢弃:KuCoin 没有对应交易对", int((~uk).sum())], ["  其中 267 币池内丢弃 / 扩展丢弃", f"{int(((~uk)&(u.grp=='pool')).sum())} / {int(((~uk)&(u.grp=='ext')).sum())}"], ["丢弃:价格不一致 / 小时数不足 / 无重叠", "0 / 0 / 0"], ["现货费率:KuCoin VIP0 吃单 0.10% × 费率等级 × 交易对系数(317 币 ×1.0,1 币 ×2.0);永续仍为币安 5bp", "—"]])
P("KuCoin 现货成交额只有币安现货的约 2.6%(逐币中位数;总量约 13%),只有币安永续成交额的约 0.6%(逐币中位数)——**成交量/pov/冲击全部改用 `min(KuCoin 现货, Binance 永续)`**,这是 KuCoin 变体收益低的主因。无成交或无 K 线的小时:IS 约 15.3 万币小时(无行 4.4 万、成交量为 0 的平线 11 万)、HO 约 8.0 万币小时(全为平线)。没有任何填充。")
P()
P("### 8.4.2 主结果(10M;KuCoin 现货 + Binance 永续;修复引擎;pool 339;cal / bp30)")
km = pd.read_csv(KC + "kc_main.csv"); km["avgc"] = ann_avgc(km); kn = {"REF_ADL": "v9 规则(ADL,硬上限)", "FINAL": "**冻结:m=2 + X5/48h**", "NOGATE24": "无闸门 + X5/24h", "OLDGATE24": "旧闸门 m=3 + X5/24h"}
rows = []
for scn in ("cal", "bp30"):
    for c, lab in kn.items():
        for w in ("IS", "HO"):
            a = km[(km.cfg == c) & (km.scen == scn) & (km.win == w) & (km.pool == 339)].iloc[0]
            rows.append([scn, lab, w, f1(a.ann10), f1(a.ann_pkc), f1(a.ann_pkm), f1(a.avgc), wan(a.net_u), wan(a.funding_u), wan(a.basis_u), wan(a.fees_u), wan(a.slip_u), int(a.episodes), f1(a.volcap_pct), f1(a.ex5_ann), f1(a.top5_share)])
for w in ("IS", "HO"):
    a = km[(km.cfg == "V9_native_cfg") & (km.win == w) & (km.pool == 339)].iloc[0]
    rows.append(["bp30", "v9 引擎设定(pov 20%,无上限)", w, f1(a.ann10), f1(a.ann_pkc), f1(a.ann_pkm), f1(a.avgc), wan(a.net_u), wan(a.funding_u), wan(a.basis_u), wan(a.fees_u), wan(a.slip_u), int(a.episodes), f1(a.volcap_pct), f1(a.ex5_ann), f1(a.top5_share)])
tbl(["成本", "规则", "窗口", "年化(10M)", "年化(峰值成本)", "年化(峰值市值)", "年化(平均占用)", "净利", "funding", "基差", "手续费", "冲击+价差", "次数", "超成交量上限币小时%", "去前5币年化", "前5币占比%"], rows)
P("**对 267 币池的结果几乎相同**(见 `kucoin/out/kc_main.csv`)。")
P()
P("### 8.4.3 与币安现货版的对比(7 天块自助;同一冻结规则,日净利差折合 10M 年化 pp)")
kb = pd.read_csv(KC + "kc_boot.csv"); rows = []
for _, r in kb.iterrows():
    if r["scen"] == "cal" or r["item"] in ("KC V9 native cfg",): rows.append([r.win, r.scen, r["item"], f"{r.ann_pp:+.1f} [{r.lo:+.1f}, {r.hi:+.1f}]"])
tbl(["窗口", "成本", "项目", "年化 pp [95%CI]"], rows)
P("**结论**:KuCoin 版冻结规则 IS 19.6%、HO 3.6%(cal),比币安现货版(IS 95.2% / HO 57.1%)**低 76pp / 54pp,CI 都排除 0**。**差距主要不是价差,而是'能做多大'**:KuCoin 现货成交额太小,pov/成交量上限成为主约束(平均占用 IS 约 140 万 U、HO 约 15 万 U,对比币安版 710 万 / 330 万),所以按 10M 摊薄后年化很低;**按'峰值/平均占用'算会好看得多(HO 峰值成本分母 130%),但那是在一个很小的资金规模上的数字,不能外推到 10M。**")
P("KuCoin 版里闸门没有明显帮助:IS 冻结 − v9 规则 = +2.6pp [−0.9, +6.7](cal);HO −2.7pp [−4.9, −0.5](HO 上 KuCoin 可用容量极小,原因未单独检验)。")
P()
P("### 8.4.4 保证金与资金划转(冻结规则,cal,KuCoin 现货(卖出自有库存)+ Binance 永续多头 1 倍名义额;后处理,不改成交)")
mg = pd.read_csv(KC + "kc_margin.csv")
for var in ("raw", "glitch_filtered"):
    if var == "raw": P("**永续腿杠杆 L 与占用资金、假想爆仓(不追加保证金、维持保证金率 1%、按小时最低价)**")
    a = mg[mg.variant == var].set_index(["cfg", "win"])
    if var == "raw":
        rows = []
        for cfg in ("FINAL", "REF_ADL"):
            for w in ("IS", "HO"):
                r = a.loc[(cfg, w)]
                for Lv in (1, 2, 3, 5, 10):
                    rows.append([cfg, w, f"{Lv}×", f"{r[f'L{Lv}_margin_peak_pct']:.1f}% / {r[f'L{Lv}_margin_avg_pct']:.1f}%", int(r[f"L{Lv}_liq_events"]), f"{r[f'L{Lv}_liq_loss_pct']:.1f}%"])
        tbl(["规则", "窗口", "杠杆 L", "永续保证金占用 峰值 / 平均(占 10M)", "假想爆仓事件(币×回合)", "被扫仓位的浮亏合计(占 10M)"], rows)
        rows = []
        for cfg in ("FINAL", "REF_ADL"):
            for w in ("IS", "HO"):
                r = a.loc[(cfg, w)]
                rows.append([cfg, w, f"{r.peak_notional_pct:.1f}% / {r.avg_notional_pct:.1f}%", f"{r.peak_spotcash_kc_pct:.1f}% / {r.avg_spotcash_kc_pct:.1f}%", f"{r.dip_transfer_peak_pct:.1f}% / {r.dip_transfer_p95_pct:.1f}%", int(r.episodes), f"{r.ep_adv_p50:.0f}% / {r.ep_adv_p95:.0f}% / {r.ep_adv_max:.0f}%", int(r.ep_adv_gt50pct)])
        P("**下跌端:永续多头浮亏(需要从 KuCoin 现货款划到 Binance 补保证金)**")
        tbl(["规则", "窗口", "单腿名义额 峰值 / 平均(占 10M)", "KuCoin 现货卖出款 峰值 / 平均", "补保证金需求 峰值 / 95 分位", "回合数", "回合内永续最大回撤 中位 / 95 分位 / 最大", "回撤>50% 的回合数"], rows)
rows = []
for var in ("raw", "glitch_filtered"):
    a = mg[mg.variant == var].set_index(["cfg", "win"])
    for cfg in ("FINAL", "REF_ADL"):
        for w in ("IS", "HO"):
            r = a.loc[(cfg, w)]; rows.append([var, cfg, w, f"{r.rally_transfer_peak_pct:.1f}% / {r.rally_transfer_p95_pct:.1f}%", int(r.hours_rally_gt1pct), f"{r.ep_ral_p50:.0f}% / {r.ep_ral_p95:.0f}% / {r.ep_ral_max:.0f}%", int(r.ep_ral_gt50pct)])
P("**上涨端:卖出的现货(库存)浮亏 = 回补需要的额外资金,需从 Binance(永续盈利)划到 KuCoin**")
tbl(["数据", "规则", "窗口", "划转需求 峰值 / 95 分位(占 10M)", "需求>1% 的小时数", "回合内现货最大上冲 中位 / 95 分位 / 最大", "上冲>50% 的回合数"], rows)
P("**读法**:① 1× 永续(全额保证金)没有假想爆仓,但占用 = 单腿名义额(IS 峰值约 50% 的 10M);② 杠杆 ≥2× 时,在'不追加保证金'的假设下,IS 里 2× 就有 43 次、3× 156 次、5× 356 次回合被扫(HO 为 3 / 29 / 93),所以**这个策略要的是'随时能追加保证金的资金池',不是靠杠杆省钱**;③ 上涨端:个别币在一个回合内涨数倍(KuCoin 原始数据里还有 100 倍的错误最高价针,'毛刺过滤'版已封顶);IS 的回补划转需求峰值约 20%(过滤后 10.6%)的 10M,但 95 分位仅约 4.5%。**这些保证金/划转数字只对 KuCoin 现货腿是自有库存(不是借币做空)成立;如是借币做空,上涨端就是保证金缺口,KuCoin 的强平线另行核对。**")
P()
P("### 8.4.5 敏感性(只报告,不用于选择;冻结规则,pool 339,cal;10M 年化 IS / HO)")
ks = pd.read_csv(KC + "kc_sens.csv"); rows = []
base = km[(km.cfg == "FINAL") & (km.scen == "cal") & (km.pool == 339)].set_index("win")
rows.append(["基准", f"{base.loc['IS'].ann10:.1f} / {base.loc['HO'].ann10:.1f}"])
for t, lab in (("fee_x0.8_KCS", "现货费用 ×0.8(KCS 折扣)"), ("fee_x2_classB", "现货费用 ×2(假设 B 类)"), ("Y_x1.5", "冲击系数 Y ×1.5"), ("hs_s_x2", "现货半价差 ×2")):
    a = ks[(ks.tag == t) & (ks.cfg == "FINAL")].set_index("win"); rows.append([lab, f"{a.loc['IS'].ann10:.1f} / {a.loc['HO'].ann10:.1f}"])
tbl(["情景", "年化 IS / HO"], rows)
P("敏感性只改'实际成交成本',闸门掩码在改之前固定。结果对成本几乎不敏感,因为收益被'容量'而不是'费用'限制。")
P()
P("### 8.4.6 KuCoin 变体的限制")
P("- 校准系数 `Y_kyle`、有效半价差倍数 `hsm` 是币安永续的,套到 KuCoin 现货上;现货半价差是**2026-11 的 20 次快照中位数(静态)**,套用到全年;")
P("- 基差用 KuCoin 现货收盘 vs Binance 永续收盘(同一小时收盘对齐,没有同步到秒);KuCoin 薄币有价格毛刺(最大约 100 倍的错误高点),保证金表另给毛刺过滤版;")
P("- 币种交集的 318 币是**事后**(以现在 KuCoin 仍上市的交易对为准),有幸存者偏差;")
P("- 库存假设与币安版相同(同样数量的库存放在 KuCoin);KuCoin 的提币、转账时间与费用没有建模;")
P("- 现货侧 σ:`D.sigma()` 对缺失小时用全样本中位数填补,略微非因果(§8.5)。")
P()
P("## 8.5 披露:多重检验、HO 已被看过、其他已知限制(请在引用任何 HO 数字前读)")
P("1. **多重检验**:出场研究一共测试了约 100 个变体(§7.5 的 87 个出场组合 + 其他几个出场/闸门变体),**没有做多重检验校正**;被选组合(X5/48h)与 X5/24h 的差在统计上不显著(§8.2.5)。")
P("2. **HO 已被看过**:2026-07-01→10-28 这段从第四轮起就作为 holdout 用过(第四、五、六轮),第七轮是**再次使用**,所以它不是干净的样本外。第七轮的 m、conf_h 在 IS 选,但整个研究流程(信号族、成本口径、哪些东西值得做)受过 HO 的影响。")
P("3. **冻结规则在旧引擎下选出,修复引擎后没有重新选择**;修复后 IS/HO 数字改变,但所选组合保持。")
P("4. `D.sigma()` 用全样本中位数填补缺失小时(略微非因果);静态半价差(取自现在的快照,套用到全年);成交过的币清单(traded coins,用于校准抽样)是事后确定的;币池 267 是 v9 事后挑选的。")
P("5. 7 天块自助法是对时间相关性的近似,不是严格的样本外检验;5000 次重采样。")
P("6. 校准是币安公开数据代理,不是我们的成交;现货腿没有公开订单簿;小时数据无法模拟小时内拆单。")
P()
P("## 8.6 文件(第八轮)")
P("- 引擎/库:`code/engine_v12s.py`(`derisk_force=1/2`)、`code/lib12s.py`、`code/run_r7.py`(`NFB_DERISK` 环境变量)、`code/r7_legacy_bound.py`、`code/run_r7_v9cmp.py`、`code/r7_v9bridge.py`、`code/r7_v9boot.py`。")
P("- 输出:`out/r7_scen.csv`、`r7_hardcap.csv`、`r7_bootstrap.csv`、`r7_v9cmp.csv`、`r7_v9bridge.csv`、`r7_v9boot.csv`、`r7_legacy_bound.csv`;旧引擎结果 `out/legacy_derisk1/`。")
P("- KuCoin:`kucoin/PREREG_kucoin.md`、`kucoin/code/`(`dl_kucoin.py`、`snap_spread.py`、`build_kc_ds.py`、`run_kc.py`、`margin.py`、`kc_boot.py`)、`kucoin/out/kc_main.csv`、`kc_sens.csv`、`kc_fillcheck.csv`、`kc_margin.csv`、`kc_boot.csv`、`kc_universe.json`。")
open(O + "report8_section.md", "w").write("\n".join(L) + "\n"); print(len(L), "lines")
