"""Default entry threshold: 8h-normalized rate strictly below -0.001.

No market data. Equality at 1h, 4h and 8h must not pass.
"""

import math
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "repro" / "lib"))

from entry_threshold import (ENTRY_FAV_N, ENTRY_FAV_N_HISTORICAL,
                             passes_entry_rate, rate8_from_interval)


class TestEntryThreshold(unittest.TestCase):
    def test_default_is_strict_below_one_tenth_percent(self):
        self.assertEqual(ENTRY_FAV_N, 0.001)
        self.assertEqual(ENTRY_FAV_N_HISTORICAL, 0.0005)
        self.assertFalse(passes_entry_rate(-0.001))
        self.assertTrue(passes_entry_rate(math.nextafter(-0.001, -1.0)))
        self.assertFalse(passes_entry_rate(-0.0006))
        self.assertTrue(passes_entry_rate(-0.0006, ENTRY_FAV_N_HISTORICAL))
        self.assertFalse(passes_entry_rate(-0.0005, ENTRY_FAV_N_HISTORICAL))

    def test_interval_normalization_boundary(self):
        exact = {1: -0.000125, 4: -0.0005, 8: -0.001}
        for hours, raw in exact.items():
            rate8 = rate8_from_interval(raw, hours)
            self.assertEqual(rate8, -ENTRY_FAV_N)
            self.assertFalse(passes_entry_rate(rate8))
            deeper = rate8_from_interval(math.nextafter(raw, -1.0), hours)
            self.assertLess(deeper, -ENTRY_FAV_N)
            self.assertTrue(passes_entry_rate(deeper))

    def test_headline_wires_the_default_constant(self):
        signals = (ROOT / "repro" / "lib" / "run_signals.py").read_text()
        headline = (ROOT / "repro" / "run_headline.py").read_text()
        r7 = (ROOT / "repro" / "lib" / "run_r7.py").read_text()
        self.assertIn('"E7": dict(entry_fav_n=ENTRY_FAV_N, entry_basis_n=-0.003)', signals)
        self.assertIn('"E1": dict(entry_fav_n=ENTRY_FAV_N_HISTORICAL)', signals)
        self.assertIn("engine_extra(A.known_budget, A.fee_gate_match, A.open_residual, ENTRY_FAV_N)", headline)
        self.assertIn('BASEX = dict(ENTRY["E7"])', r7)

    def test_cli_smoke_without_private_data(self):
        env = os.environ.copy()
        env.pop("NFB_DATA", None)
        env.pop("NFB_CAP_FILE", None)
        help_run = subprocess.run([sys.executable, "repro/run_headline.py", "--help"], cwd=ROOT, env=env, capture_output=True, text=True)
        self.assertEqual(help_run.returncode, 0)
        self.assertIn("严格低于 -0.001", help_run.stdout)
        self.assertIn("0.0005", help_run.stdout)
        bare = subprocess.run([sys.executable, "repro/run_headline.py"], cwd=ROOT, env=env, capture_output=True, text=True)
        self.assertNotEqual(bare.returncode, 0)
        self.assertIn("NFB_DATA", bare.stderr + bare.stdout)


if __name__ == "__main__":
    unittest.main()
