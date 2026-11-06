"""The fee gate must see the same VIP rates the fill uses.

run_headline writes v13lib._ns['MKO']. Re-executing lib12s binds a second MKO,
and reading the original one leaves the gate without spot/perpetual fees.
Missing NFB_DATA is a different failure from that configuration error.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
VIP3 = dict(fee_s=0.0006, fee_s_mk=0.0004, fee_f=0.00032, fee_f_mk=0.00012)


def _hours():
    start = pd.Timestamp("2025-10-01", tz="UTC")
    end = pd.Timestamp("2026-10-28", tz="UTC")
    return int((end - start).total_seconds() // 3600)


def _fixture(root: Path):
    T = _hours()
    price = 10.0 + 0.05 * np.sin(np.arange(T) * 0.7)[:, None]
    vol = np.full((T, 1), 1.0e6)
    zero = np.zeros((T, 1))
    depth = np.full((T, 1), 1.0e9)
    ds = root / "ds"
    cal = root / "calib"
    ds.mkdir()
    cal.mkdir()
    np.savez(ds / "dataset.npz", sv=price, sc=price, sq=vol, fv=price, fc=price, fq=vol,
             ev=zero, r8=zero, r8s=zero, d02=depth, d1=depth, oi=depth, oih=depth, mk=price,
             so=price, sh=price + 0.1, sl=price - 0.1, fo=price, fh=price + 0.1, fl=price - 0.1)
    pd.DataFrame(dict(fut=["TESTUSDT"], spot=["TESTUSDT"], hs_s=[0.0001], hs_f=[0.0001],
                      r2=[1.2], r5=[1.5], tick_s=[0.01], tick_f=[0.01], dl_exit=[1.0e9],
                      dl_fin=[1.0e9], delisted=[False], grp=["pool"])).to_csv(ds / "dataset_meta.csv", index=False)
    pd.DataFrame(dict(sym=["TESTUSDT"], date=["2025-10-02"], y_kyle=[1.0], hs=[0.0001])).to_csv(cal / "ag.csv", index=False)
    levels = {f"{side}{level:g}": [1.0e6 * (i + 1)] for i, level in enumerate((0.2, 1, 2, 3, 4, 5)) for side in ("bid", "ask")}
    pd.DataFrame(dict(sym=["TESTUSDT"], date=["2025-10-02"], **levels)).to_csv(cal / "bd.csv", index=False)
    cap = root / "caps.csv"
    pd.DataFrame(dict(fut_symbol=["TESTUSDT"], cap_usdt=[1.0e7], cap_qty_token=[1.0e6])).to_csv(cap, index=False)
    return cap


def _run(args, env):
    return subprocess.run([sys.executable, "repro/run_headline.py", *args], cwd=ROOT, env=env, capture_output=True, text=True)


class TestFeeWiring(unittest.TestCase):
    def test_missing_data_is_not_the_fee_error(self):
        env = os.environ.copy()
        env.pop("NFB_DATA", None)
        env.pop("NFB_CAP_FILE", None)
        proc = _run(["--fee", "vip3", "--fee-gate-match", "--windows", "IS"], env)
        text = proc.stdout + proc.stderr
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("NFB_DATA", text)
        self.assertNotIn("fee-gate match is on", text)

    def test_real_cli_configures_vip3_for_gate_and_fills(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cap = _fixture(root)
            env = os.environ.copy()
            env.update(NFB_DATA=str(root), NFB_CAP_FILE=str(cap), NFB_S="10000000", NFB_DERISK="2", NFB_ROOT=str(root / "out"))
            cases = {
                "B": ["--no-known-budget", "--fee-gate-match", "--no-open-residual"],
                "ABC": [],
            }
            for name, flags in cases.items():
                dest = root / f"{name}.json"
                proc = _run(["--fee", "vip3", "--windows", "IS", "--json", str(dest), *flags], env)
                text = proc.stdout + proc.stderr
                self.assertNotIn("fee-gate match is on", text, name)
                self.assertNotIn("selected spot and perpetual fees are missing", text, name)
                self.assertEqual(proc.returncode, 0, f"{name} is a fee-configuration failure:\n{text[-2000:]}")
                got = json.loads(dest.read_text())["engine_params"]
                self.assertEqual(got["fee_s"], VIP3["fee_s"])
                self.assertEqual(got["fee_f"], VIP3["fee_f"])
                self.assertEqual(got["fee_s_mk"], VIP3["fee_s_mk"])
                self.assertEqual(got["fee_f_mk"], VIP3["fee_f_mk"])


if __name__ == "__main__":
    unittest.main()
