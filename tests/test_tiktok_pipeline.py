"""M1 验收测试：简报轮换不重复、合规位强制、周报口径正确、$200 进度。"""

import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import cost_calculator as cc
import tiktok_pipeline as tp


def load_all():
    cfg = tp.load(ROOT / "config" / "tiktok.yaml")
    econ = {s["id"]: s for s in
            cc.compute_all(cc.load_config(ROOT / "config" / "economics.yaml"))["skus"]}
    return cfg, econ


class TestBriefs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg, cls.econ = load_all()
        cls.briefs = [tp.make_brief(cls.cfg, cls.econ, i) for i in range(10)]

    def test_pillar_rotation_follows_weights(self):
        # weight 3/2/3/2 → 一轮 10 条中 P1×3 P2×2 P3×3 P4×2
        ids = [b["pillar"]["id"] for b in self.briefs]
        self.assertEqual(ids.count("P1"), 3)
        self.assertEqual(ids.count("P2"), 2)
        self.assertEqual(ids.count("P3"), 3)
        self.assertEqual(ids.count("P4"), 2)

    def test_same_pillar_rotates_hooks(self):
        p1_hooks = [b["hook"]["id"] for b in self.briefs if b["pillar"]["id"] == "P1"]
        self.assertEqual(len(p1_hooks), len(set(p1_hooks)), "同支柱钩子不应重复")

    def test_hooks_traceable_to_painpoints(self):
        import review_miner as rm
        valid = {p["id"] for p in rm.load_painpoints()}
        for h in self.cfg["hooks"]:
            self.assertIn(h["source"], valid, f"钩子 {h['id']} 溯源无效")

    def test_render_forces_real_footage_and_aigc_label(self):
        for b in self.briefs:
            out = tp.render_brief(b, self.cfg)
            self.assertIn("AIGC 标签", out)
            # solve/reveal/process 任一存在时必须出现实拍位
            roles = {beat["role"] for beat in b["structure"]["beats"]}
            if roles & {"solve", "reveal", "process"}:
                self.assertIn("实拍位", out)

    def test_discount_cta_triggers_disclosure(self):
        for b in self.briefs:
            out = tp.render_brief(b, self.cfg)
            if b["cta"]["mode"] == "discount":
                self.assertIn("商业披露开", out)

    def test_deterministic(self):
        again = [tp.make_brief(self.cfg, self.econ, i) for i in range(10)]
        for a, b in zip(self.briefs, again):
            self.assertEqual(a["hook"]["id"], b["hook"]["id"])
            self.assertEqual(a["structure"]["id"], b["structure"]["id"])


class TestCalendarAndReport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg, cls.econ = load_all()

    def test_calendar_days_and_fields(self):
        rows = tp.make_calendar(self.cfg, 30, date(2026, 8, 1))
        self.assertEqual(len(rows), 30)
        self.assertEqual(rows[0]["date"], "2026-08-01")
        self.assertEqual(rows[0]["sku"], "SKU-A")

    def test_report_math_matches_template(self):
        import csv
        with open(ROOT / "data" / "templates" / "tiktok_stats_template.csv",
                  encoding="utf-8-sig", newline="") as f:
            stats = [dict(r) for r in csv.DictReader(f)]
        rep = tp.build_report(stats, self.cfg, self.econ)
        self.assertIn("已发布 7 条", rep)
        self.assertIn("归因订单 7 单", rep)
        # 手算：P1 4 单×(105.17−23.48) + P3 3 单×(54.63−12.67) ≈ ¥453
        self.assertIn("¥453", rep)
        self.assertIn("$200", rep)

    def test_per_pillar_counts_isolated(self):
        # 回归：分支柱统计曾把累计值当初始值（dict(tot) bug）
        import csv
        with open(ROOT / "data" / "templates" / "tiktok_stats_template.csv",
                  encoding="utf-8-sig", newline="") as f:
            stats = [dict(r) for r in csv.DictReader(f)]
        rep = tp.build_report(stats, self.cfg, self.econ)
        self.assertIn("| P2 satisfying-rig | 2 |", rep)

    def test_goal_reached_message(self):
        stats = [{"video_id": "V", "date": "2026-08-01", "pillar": "P1",
                  "views": "100000", "likes": "5000", "comments": "300",
                  "shares": "200", "link_clicks": "1500",
                  "orders": "20", "revenue_aud": "999"}]
        rep = tp.build_report(stats, self.cfg, self.econ)
        self.assertIn("✅ 目标达成", rep)

    def test_kill_rule_triggers(self):
        stats = [{"video_id": f"V{i}", "date": "2026-08-01", "pillar": "P2",
                  "views": "1000", "likes": "5", "comments": "1", "shares": "0",
                  "link_clicks": "1", "orders": "0", "revenue_aud": "0"}
                 for i in range(6)]
        rep = tp.build_report(stats, self.cfg, self.econ)
        self.assertIn("🔴 杀停", rep)

    def test_llm_prompt_contains_guardrails(self):
        briefs = [tp.make_brief(self.cfg, self.econ, i) for i in range(3)]
        prompt = tp.llm_polish_prompt(briefs, self.cfg)
        self.assertIn("water-resistant", prompt)   # 禁 waterproof 宣称
        self.assertIn("VID-001", prompt)


if __name__ == "__main__":
    unittest.main()
