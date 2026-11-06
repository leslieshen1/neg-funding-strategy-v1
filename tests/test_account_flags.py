"""Accounting switches. No market file.

The engine case is one coin and a handful of hours.
"""

import os
import subprocess
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "repro" / "lib"))

from fee_gate import configure, reset, roundtrip
from headline_flags import engine_extra
from known_budget import prior_oi_row, shrink_to_realized
import engine_v12s as E


def _book(T, N):
    z = np.zeros((T, N))
    ones = np.ones((T, N))
    return ones * 10, ones * 10, z, ones * 10, ones * 10, z, z, z, z, ones * 1e12, ones * 1e12


def _run(fill_cap, f_prior, res_mode, sq):
    T, N = sq.shape
    sv, sc, _sq, fv, fc, fq, ev, r8, r8s, d02, d1 = _book(T, N)
    fq = sq.copy()
    r8[:, :] = -0.01
    P = E.mkp(entry_fav_n=0.001, entry_basis_n=1.0, xmode=0.0, exit_fav_n=-1e9, wait_max_n=0,
              derisk=0.0, f_hardcap=0.0, vol_frac=0.0, f_exitpov=1.0, wind_down_h=0.0,
              f_prior=f_prior, fill_cap=fill_cap, res_mode=res_mode, acct_book=1.0, f_budget=1.0,
              f_exitlag=1.0, capital=1e7, pov=0.5, add_n=0.0, impact=0.0, spread_mult=0.0,
              fee_s=0.001, fee_f=0.001, sqrt_y=0.0, k_imp=0.0, exec_mode=0.0, dfrac=1.0, xmax=1.0,
              f_markfund=0.0, f_coin=0.0)
    H = T
    used = np.zeros(H); cum = np.zeros(H); comp = np.zeros((H, 6)); ep = np.zeros((20, 11))
    diag = np.zeros(32); pos = np.zeros((H, N)); xd = np.zeros(64); acct = np.zeros((H, 4))
    E.sim(0, T, sv, sc, sq, fv, fc, fq, ev, r8, r8s, d02, d1, np.ones((T, N)), np.ones((T, N)) * 1e18,
          np.zeros(N), np.zeros(N), np.zeros(N), np.zeros(N), np.ones((T, N), np.uint8), np.zeros((T, N), np.uint8),
          np.ones(N) * 1e7, np.zeros(N), np.ones((T, N)) * 10, np.zeros(N), np.ones((T, N)), np.zeros((T, N)),
          np.ones((T, N)), np.zeros((T, N)), P, used, cum, ep, comp, diag, pos,
          sv, sv, sv, fv, fv, fv, np.zeros(N), np.zeros(N), np.full(N, 1e9), np.full(N, 1e9), xd,
          np.zeros((T, N)), np.ones((T, N)), np.ones((3, T, N)), np.ones(N), acct)
    return pos, cum, comp, diag, acct


class TestAccountFlags(unittest.TestCase):
    def test_future_oi_does_not_change_past_cap(self):
        oih = np.arange(6, dtype=float)[:, None] * 10
        past = prior_oi_row(oih)[:3].copy()
        oih[3:] = 999
        self.assertTrue(np.allclose(prior_oi_row(oih)[:3], past, equal_nan=True))
        self.assertTrue(np.isnan(prior_oi_row(oih)[0, 0]))

    def test_current_volume_only_shrinks(self):
        self.assertEqual(shrink_to_realized(50, 10, True), 10)
        self.assertEqual(shrink_to_realized(50, 80, True), 50)
        self.assertEqual(shrink_to_realized(50, 10, False), 50)

    def test_engine_prefix_fill_cap_and_open_book(self):
        sq = np.array([100, 10000, 100, 100, 100, 100], float)[:, None]
        pos, cum, comp, diag, acct = _run(1, 1, 3, sq)
        later = sq.copy(); later[3:] = 1
        pos2, cum2, _, _, _acct2 = _run(1, 1, 3, later)
        self.assertTrue(np.allclose(pos[:2], pos2[:2]))
        self.assertTrue(np.allclose(cum[:2], cum2[:2]))
        self.assertGreater(pos[-1, 0], 0)
        self.assertEqual(diag[28], 1)
        self.assertEqual(diag[24], 0)
        marked = acct[-1, 0] - acct[-1, 3] + acct[-1, 1] + acct[-1, 2]
        self.assertAlmostEqual(marked, cum[-1], places=6)
        wide = _run(0, 0, 3, sq)
        self.assertGreater(wide[0][1, 0], pos[1, 0])
        flat = _run(1, 1, 2, sq)
        self.assertEqual(flat[3][24], 1)
        self.assertEqual(flat[3][28], 0)
        self.assertNotAlmostEqual(flat[1][-1], cum[-1], places=6)

    def test_delivery_partial_derisk_and_funding_stay_in_balance(self):
        T, N = 24, 2
        px = np.zeros((T, N))
        px[:, 0] = 20.0
        for t in range(T):
            px[t, 1] = 80.0 - t
        sq = np.full((T, N), 1.0e6)
        sq[9:, 0] = 100.0
        ev = np.zeros((T, N)); ivh = np.zeros((T, N))
        ev[8, 1] = -0.004; ivh[8, 1] = 8
        ev[16, 1] = -0.003; ivh[16, 1] = 8
        r8 = np.full((T, N), -0.02)
        s24 = np.zeros((T, N)); s24[6:, 1] = 0.01
        P = E.mkp(entry_fav_n=0.001, entry_basis_n=1.0, xmode=5.0, x_obs=1.0, conf_h=1.0, exit_fav_n=-1e9,
                  derisk=1.0, derisk_force=2.0, f_hardcap=1.0, vol_frac=0.02, f_exitpov=1.0, wind_down_h=0.0,
                  f_prior=1.0, res_mode=3.0, acct_book=1.0, f_budget=1.0, f_exitlag=1.0, capital=1e7, pov=0.5,
                  add_n=1.0, impact=0.001, spread_mult=1.0, fee_s=0.0006, fee_f=0.00032, k_imp=4.0, fx_fund=2.0,
                  f_markfund=1.0, sqrt_y=0.0)
        cum = np.zeros(T); comp = np.zeros((T, 6)); ep = np.zeros((40, 11)); diag = np.zeros(32)
        pos = np.zeros((T, N)); xd = np.zeros(64); acct = np.zeros((T, 4)); used = np.zeros(T)
        E.sim(0, T, px, px, sq, px, px, sq, ev, r8, np.zeros((T, N)), np.full((T, N), 1e12), np.full((T, N), 1e12),
              np.full((T, N), 1e5), np.full((T, N), 5e4), np.array([1e-4, 2e-4]), np.array([1e-4, 2e-4]),
              np.ones(N), np.ones(N), np.ones((T, N), np.uint8), np.zeros((T, N), np.uint8), np.full(N, 1e7), np.zeros(N),
              px, np.zeros(N), np.full((T, N), 1e6), ivh, np.full((T, N), 0.03), np.zeros((T, N)), P, used, cum, ep, comp, diag, pos,
              px, px, px, px, px, px, np.full(N, 0.01), np.full(N, 0.01), np.array([10.0, 1e9]), np.array([14.0, 1e9]),
              xd, s24, np.ones((T, N)), np.ones((3, T, N)), np.ones(N), acct)
        gap = acct[:, 0] - acct[:, 3] + acct[:, 1] + acct[:, 2] - cum
        self.assertLess(np.max(np.abs(gap)), 1e-6)
        self.assertEqual(pos[-1, 0], 0.0)
        self.assertGreater(pos[10, 0], 0.0)
        self.assertGreater(pos[-1, 1], 0.0)
        self.assertGreater(diag[28], 0.0)

    def test_vip3_gate_fee_and_flag_isolation(self):
        self.assertEqual(roundtrip(), 0.0030)
        configure(True, 0.0006, 0.00032)
        self.assertAlmostEqual(roundtrip(), 0.00184)
        reset()
        self.assertEqual(roundtrip(), 0.0030)
        on = engine_extra(True, True, True, 0.001)
        off = engine_extra(False, False, False, 0.001)
        self.assertEqual(on["fill_cap"], 1)
        self.assertFalse(on["same_hour"])
        self.assertEqual(on["res_mode"], 3)
        self.assertTrue(off["same_hour"])
        self.assertEqual(off["res_mode"], 2)
        self.assertFalse(off["fee_gate_match"])
        self.assertEqual(on["entry_fav_n"], 0.001)

    def test_cli_wires_the_three_switches(self):
        env = os.environ.copy()
        env.pop("NFB_DATA", None)
        env.pop("NFB_CAP_FILE", None)
        help_run = subprocess.run([sys.executable, "repro/run_headline.py", "--help"], cwd=ROOT, env=env, capture_output=True, text=True)
        self.assertEqual(help_run.returncode, 0, help_run.stderr)
        self.assertIn("--known-budget", help_run.stdout)
        self.assertIn("--fee-gate-match", help_run.stdout)
        self.assertIn("--open-residual", help_run.stdout)
        self.assertIn("严格低于 -0.001", help_run.stdout)
        bare = subprocess.run([sys.executable, "repro/run_headline.py", "--no-known-budget", "--no-fee-gate-match", "--no-open-residual"], cwd=ROOT, env=env, capture_output=True, text=True)
        self.assertNotEqual(bare.returncode, 0)
        self.assertIn("NFB_DATA", bare.stdout + bare.stderr)


if __name__ == "__main__":
    unittest.main()
