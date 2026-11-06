"""Run the unchanged book and each accounting switch in its own process.

Nothing here is a new backtest result. Set NFB_DATA, NFB_CAP_FILE and optionally
NFB_S before starting. Each variant writes only the json path you pass.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FLAGS = {
    "base": ["--no-known-budget", "--no-fee-gate-match", "--no-open-residual"],
    "A": ["--known-budget", "--no-fee-gate-match", "--no-open-residual"],
    "B": ["--no-known-budget", "--fee-gate-match", "--no-open-residual"],
    "C": ["--no-known-budget", "--no-fee-gate-match", "--open-residual"],
    "ABC": ["--known-budget", "--fee-gate-match", "--open-residual"],
}


def main():
    ap = argparse.ArgumentParser(description="Compare base, A, B, C and ABC without sharing process state.")
    ap.add_argument("--variants", default="base,A,B,C,ABC")
    ap.add_argument("--windows", default="IS,HO,FY")
    ap.add_argument("--fee", default="vip3", choices=["vip0", "vip3"])
    ap.add_argument("--out", default="abc_compare.json")
    args = ap.parse_args()
    missing = [k for k in ("NFB_DATA", "NFB_CAP_FILE") if not os.environ.get(k)]
    if missing:
        sys.exit("设好 " + " 和 ".join(missing) + " 后再跑。这里不生成收益数字。")
    out = {}
    for name in args.variants.split(","):
        if name not in FLAGS:
            sys.exit(f"未知对照 {name}")
        dest = Path(args.out).with_name(Path(args.out).stem + f"_{name}.json")
        cmd = [sys.executable, str(ROOT / "repro" / "run_headline.py"), "--fee", args.fee,
               "--windows", args.windows, "--json", str(dest), *FLAGS[name]]
        proc = subprocess.run(cmd, cwd=ROOT)
        if proc.returncode != 0:
            sys.exit(f"{name} 退出码 {proc.returncode}")
        out[name] = json.loads(dest.read_text())
    Path(args.out).write_text(json.dumps(out, indent=1, default=str))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
