"""T1 验收测试：§5.2 表格数字可复现；三重悲观一键复算；参数改动即时生效。"""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import cost_calculator as cc


def load():
    return cc.load_config(ROOT / "config" / "economics.yaml")


class TestBaseline(unittest.TestCase):
    """对齐 docs/PROJECT_PLAN.md §5.2 首批 SKU 测算表。"""

    def setUp(self):
        self.cfg = load()
        self.res = cc.compute_all(self.cfg)
        self.by_id = {r["id"]: r for r in self.res["skus"]}

    def test_sku_a_matches_plan(self):
        a = self.by_id["SKU-A"]
        self.assertAlmostEqual(a["price_cny"], 234.77, delta=0.01)
        self.assertAlmostEqual(a["net_contribution"], 105, delta=1)   # 计划：≈105
        self.assertAlmostEqual(a["net_margin"], 0.45, delta=0.01)     # 计划：45%
        self.assertAlmostEqual(a["net_after_returns_margin"], 0.40, delta=0.01)  # 计划：≈40%

    def test_sku_b_matches_plan(self):
        b = self.by_id["SKU-B"]
        self.assertAlmostEqual(b["net_contribution"], 55, delta=1)    # 计划：≈55
        self.assertAlmostEqual(b["net_margin"], 0.43, delta=0.01)     # 计划：43%
        self.assertAlmostEqual(b["net_after_returns_margin"], 0.38, delta=0.01)  # 计划：≈38%

    def test_gross_margin_gate_passes_floor(self):
        for r in self.res["skus"]:
            self.assertGreaterEqual(r["gross_margin"], 0.55)
            self.assertTrue(r["gate_pass"])

    def test_breakeven_matches_plan(self):
        self.assertEqual(self.res["breakeven_orders"], 13)            # 计划：约 13 单/月

    def test_gate_fails_below_floor(self):
        cfg = load()
        cfg["skus"][0]["cost_cny"] = 120  # 抬高采购价压穿红线
        r = cc.compute_sku(cfg["skus"][0], cfg["params"])
        self.assertFalse(r["gate_pass"])


class TestSensitivity(unittest.TestCase):
    """三重悲观情形一键复算，且方向正确。"""

    def setUp(self):
        self.cfg = load()
        self.scenarios = dict(
            (name, cc.compute_all(c)) for name, c in cc.scenario_configs(self.cfg)
        )

    def test_all_five_scenarios_present(self):
        self.assertEqual(len(self.scenarios), 5)
        self.assertIn("三重悲观叠加", self.scenarios)

    def test_each_stress_lowers_margin(self):
        base = self.scenarios["基准"]["blended_net_margin"]
        for name, res in self.scenarios.items():
            if name != "基准":
                self.assertLess(res["blended_net_margin"], base, name)

    def test_triple_pessimistic_still_positive(self):
        triple = self.scenarios["三重悲观叠加"]["blended_net_margin"]
        self.assertGreater(triple, 0)          # 计划：三重叠加仍为正
        self.assertLess(triple, 0.30)          # 且显著低于基准 ~39%

    def test_explicit_shipping_scales_with_scenario(self):
        # SKU-A 用显式 shipping_cny=40，运费 +30% 情形下应变为 52
        for name, c in cc.scenario_configs(self.cfg):
            if name.startswith("运费"):
                self.assertAlmostEqual(c["skus"][0]["shipping_cny"], 52, delta=0.01)


class TestOverrides(unittest.TestCase):
    """--set 参数改动即时生效（T1 验收项）。"""

    def test_fx_override_changes_result(self):
        cfg = cc.apply_overrides(load(), ["fx_aud_cny=4.2"])
        res = cc.compute_all(cfg)
        a = res["skus"][0]
        self.assertAlmostEqual(a["price_cny"], 49.95 * 4.2, delta=0.01)
        self.assertLess(a["net_margin"], 0.45)

    def test_invalid_key_rejected(self):
        with self.assertRaises(ValueError):
            cc.apply_overrides(load(), ["not_a_param=1"])

    def test_weight_based_shipping_fallback(self):
        cfg = load()
        del cfg["skus"][0]["shipping_cny"]
        r = cc.compute_sku(cfg["skus"][0], cfg["params"])
        self.assertAlmostEqual(r["shipping_cny"], 0.8 * 45, delta=0.01)


if __name__ == "__main__":
    unittest.main()
