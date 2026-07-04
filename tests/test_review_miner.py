"""T2 验收测试：对 §4 人工聚类结果可复现（样例数据上 9 痛点全命中、C1 居首）。"""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import review_miner as rm

SAMPLE = ROOT / "data" / "templates" / "reviews_sample.csv"


class TestClassification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.painpoints = rm.load_painpoints()
        cls.reviews = rm.read_reviews(SAMPLE)
        cls.hits, cls.unmatched = rm.classify(cls.reviews, cls.painpoints)
        cls.ranked = rm.rank(cls.hits, cls.painpoints)

    def test_all_nine_painpoints_detected(self):
        self.assertEqual({r["id"] for r in self.ranked},
                         {"C1", "C2", "C3", "C4", "C5", "J1", "J2", "J3", "J4"})

    def test_c1_ranks_first(self):
        # §4.1：C1 五金件是最高频痛点
        self.assertEqual(self.ranked[0]["id"], "C1")

    def test_j1_tops_squid_category(self):
        squid = [r for r in self.ranked if r["id"].startswith("J")]
        self.assertEqual(squid[0]["id"], "J1")  # §4.2：锈与散架最高频

    def test_category_scoping(self):
        # squid 评论不得命中 4WD 痛点（如 C1），反之亦然
        for pid, revs in self.hits.items():
            expect = "4wd" if pid.startswith("C") else "squid"
            for rev in revs:
                self.assertEqual(rev["product"], expect, f"{pid} 命中了错误类目")

    def test_unmatched_bucket_collects_new_candidates(self):
        self.assertGreaterEqual(len(self.unmatched), 1)
        for rev in self.unmatched:
            self.assertNotIn("buckle", rev["text"].lower())

    def test_score_is_count_times_severity(self):
        for r in self.ranked:
            self.assertEqual(r["score"], r["count"] * rm.SEVERITY_WEIGHT[r["severity"]])

    def test_render_contains_ranking_and_counters(self):
        out = rm.render(self.hits, self.unmatched, self.ranked, len(self.reviews))
        self.assertIn("C1", out)
        self.assertIn("金属扣具", out)   # 对策列
        self.assertIn("未归类评论", out)

    def test_llm_prompt_contains_reviews_and_schema(self):
        prompt = rm.llm_prompt(self.reviews, self.painpoints)
        self.assertIn("new_painpoints", prompt)
        self.assertIn("C1", prompt)
        self.assertIn("rusted to bits", prompt)


if __name__ == "__main__":
    unittest.main()
