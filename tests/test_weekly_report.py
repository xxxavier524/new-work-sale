"""T6 验收测试：CSV → 单量/退货率/估算净利/库存周转/G3-G4 距离。"""

import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import cost_calculator as cc
import weekly_report as wr


def make_orders(n_ok_a=10, n_ok_b=10, n_returned=1, day="2026-08-10"):
    rows = []
    i = 0
    for _ in range(n_ok_a):
        i += 1
        rows.append({"date": day, "order_id": f"o{i}", "sku": "SKU-A",
                     "qty": "1", "sale_aud": "49.95", "status": "delivered"})
    for _ in range(n_ok_b):
        i += 1
        rows.append({"date": day, "order_id": f"o{i}", "sku": "SKU-B",
                     "qty": "1", "sale_aud": "26.95", "status": "delivered"})
    for _ in range(n_returned):
        i += 1
        rows.append({"date": day, "order_id": f"o{i}", "sku": "SKU-A",
                     "qty": "1", "sale_aud": "49.95", "status": "returned"})
    return rows


class TestSummarize(unittest.TestCase):
    def setUp(self):
        self.cfg = cc.load_config(ROOT / "config" / "economics.yaml")
        self.econ = {r["id"]: r for r in cc.compute_all(self.cfg)["skus"]}

    def test_counts_and_net(self):
        n_o, n_u, sales, n_ret, net, per_sku = wr.summarize_orders(
            make_orders(10, 10, 1), self.econ)
        self.assertEqual(n_o, 21)
        self.assertEqual(n_u, 20)
        self.assertEqual(n_ret, 1)
        self.assertAlmostEqual(sales, 10 * 49.95 + 10 * 26.95, delta=0.01)
        # 净贡献 = 10×105.17 + 10×54.63 − 退货损失(38+40)
        a, b = self.econ["SKU-A"], self.econ["SKU-B"]
        expected = 10 * a["net_contribution"] + 10 * b["net_contribution"] \
            - (a["cost_cny"] + a["shipping_cny"])
        self.assertAlmostEqual(net, expected, delta=0.01)
        self.assertEqual(per_sku["SKU-A"]["returned"], 1)

    def test_window_filters_by_date(self):
        rows = [{"date": "2026-08-01"}, {"date": "2026-07-01"}]
        got = wr.window(rows, date(2026, 8, 10), 30)
        self.assertEqual(len(got), 1)


class TestReport(unittest.TestCase):
    def setUp(self):
        self.cfg = cc.load_config(ROOT / "config" / "economics.yaml")
        self.inventory = [{"sku": "SKU-A", "units_on_hand": "132"},
                          {"sku": "SKU-B", "units_on_hand": "760"}]

    def test_g3_pass_when_over_30_orders_low_returns(self):
        orders = make_orders(20, 15, 1)  # 36 单，退货率 2.8%
        rep = wr.build_report(orders, [], self.inventory, self.cfg, date(2026, 8, 10))
        self.assertIn("✅ G3 单量", rep)
        self.assertIn("✅ G3 退货率", rep)
        self.assertIn("库存周转", rep)

    def test_g3_fail_and_return_alarm(self):
        orders = make_orders(5, 5, 2)  # 12 单，退货率 16.7%
        rep = wr.build_report(orders, [], [], self.cfg, date(2026, 8, 10))
        self.assertIn("🔴 G3 单量", rep)
        self.assertIn("🔴 G3 退货率", rep)
        self.assertIn("退货率触发报警线", rep)

    def test_ad_spend_reduces_profit(self):
        orders = make_orders(20, 15, 0)
        ads = [{"date": "2026-08-09", "channel": "ebay", "spend_cny": "1000"}]
        rep_no = wr.build_report(orders, [], [], self.cfg, date(2026, 8, 10))
        rep_ad = wr.build_report(orders, ads, [], self.cfg, date(2026, 8, 10))
        self.assertIn("广告费 ¥1,000", rep_ad)
        self.assertNotEqual(rep_no, rep_ad)

    def test_zero_orders_no_crash(self):
        rep = wr.build_report([], [], self.inventory, self.cfg, date(2026, 8, 10))
        self.assertIn("单量 0", rep)
        self.assertIn("零动销", rep)

    def test_template_csvs_parse(self):
        tpl = ROOT / "data" / "templates"
        orders = wr.read_csv(tpl / "orders_template.csv")
        ads = wr.read_csv(tpl / "ads_template.csv")
        inv = wr.read_csv(tpl / "inventory_template.csv")
        rep = wr.build_report(orders, ads, inv, self.cfg, date(2026, 8, 7))
        self.assertIn("周报", rep)
        self.assertIn("SKU-A", rep)


if __name__ == "__main__":
    unittest.main()
