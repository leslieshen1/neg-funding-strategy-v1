"""唯一入口：复现头条（10M 本金，cons 保守成本，k_imp=4，0h 出场）的 IS / HO / FY 年化与笔数。
只需三个环境变量：NFB_DATA（数据目录，含 ds/ 与 calib/）、NFB_CAP_FILE（执行团队提供的逐币上限 CSV）、NFB_ROOT（输出根目录，默认当前目录）。
不打印任何逐币信息。"""
import os, sys
for k in ("NFB_DATA", "NFB_CAP_FILE"):
    if not os.environ.get(k): sys.exit(f"请先设置环境变量 {k}（见 README）")
ROOT = os.environ.get("NFB_ROOT", ".").rstrip("/")
os.environ["NFB_OUT"] = ROOT + "/out/"; os.environ["NFB_DAILY"] = ROOT + "/out/daily/"
os.makedirs(os.environ["NFB_DAILY"], exist_ok=True)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))
import engine_v12s, lib12s           # 带逐笔记账字段的引擎副本，必须先于其它模块导入
sys.argv = sys.argv[:1]
from v13lib import run_fix, ann_of
for win in ("IS", "HO", "FY"):
    r = run_fix("cons_c0", win)
    print(f"{win}: 年化 {ann_of(r):.2f}%  笔数 {len(r['ep'])}  净利 {r['cum'][-1]/1e4:.1f} 万U", flush=True)
