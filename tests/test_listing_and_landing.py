"""T3/T4 验收测试：卖点溯源、标题长度、JSON-LD 结构。"""

import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import landing_page as lp
import listing_generator as lg


class TestListingGenerator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.listings = lg.load_yaml(ROOT / "config" / "listings.yaml")
        cls.valid_ids = lg.valid_painpoint_ids()

    def test_traceability_validation_passes(self):
        # T3 核心验收：每条卖点可溯源到具体痛点编号
        self.assertEqual(lg.validate(self.listings, self.valid_ids), [])

    def test_validation_catches_bad_painpoint(self):
        import copy
        broken = copy.deepcopy(self.listings)
        broken["skus"][0]["claims"][0]["painpoint"] = "X9"
        errors = lg.validate(broken, self.valid_ids)
        self.assertTrue(any("溯源" in e for e in errors))

    def test_titles_within_ebay_limit(self):
        for sku in self.listings["skus"]:
            self.assertEqual(len(sku["title_variants"]), 3)
            for t in sku["title_variants"]:
                self.assertLessEqual(len(t), lg.EBAY_TITLE_LIMIT, t)

    def test_three_variants_rendered_with_tags(self):
        out = lg.render_sku(self.listings["skus"][0], self.listings["store_policy"])
        for v in ("V1 pain-led", "V2 proof-led", "V3 scenario-led"):
            self.assertIn(v, out)
        self.assertIn("[C1]", out)                     # annotated 溯源标签
        self.assertIn("Metal hardware. No plastic clips.", out)  # §3 规定的首行

    def test_clean_mode_strips_tags(self):
        out = lg.render_sku(self.listings["skus"][0], self.listings["store_policy"],
                            annotated=False)
        self.assertNotRegex(out, r"\[[CJ]\d\]")

    def test_five_bullets_per_variant(self):
        out = lg.render_sku(self.listings["skus"][1], self.listings["store_policy"])
        for block in out.split("## ")[1:]:
            bullets = [l for l in block.splitlines() if l.startswith("- ")]
            self.assertEqual(len(bullets), 5)


class TestLandingPage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.listings = lp.load_listings(ROOT / "config" / "listings.yaml")
        cls.pages = {s["id"]: lp.render_page(s, cls.listings)
                     for s in cls.listings["skus"]}

    def extract_jsonld(self, page):
        blocks = re.findall(
            r'<script type="application/ld\+json">\s*(.*?)\s*</script>',
            page, re.DOTALL)
        return [json.loads(b) for b in blocks]

    def test_product_jsonld_required_fields(self):
        for sku_id, page in self.pages.items():
            product = next(b for b in self.extract_jsonld(page)
                           if b["@type"] == "Product")
            self.assertEqual(product["sku"], sku_id)
            offer = product["offers"]
            self.assertEqual(offer["priceCurrency"], "AUD")
            self.assertEqual(offer["availability"], "https://schema.org/InStock")
            float(offer["price"])  # 数字格式可解析

    def test_faq_jsonld_matches_config(self):
        for sku in self.listings["skus"]:
            faq = next(b for b in self.extract_jsonld(self.pages[sku["id"]])
                       if b["@type"] == "FAQPage")
            self.assertEqual(len(faq["mainEntity"]), len(sku["faq"]))

    def test_comparison_table_present(self):
        self.assertIn("Adventure Kings-style organiser", self.pages["SKU-A"])
        self.assertIn("A$80+ for 5 premium singles", self.pages["SKU-B"])

    def test_no_external_resources(self):
        # GEO 页自包含：无外链脚本/样式/字体
        for page in self.pages.values():
            self.assertNotRegex(page, r'<(script|link)[^>]+(src|href)="http')

    def test_files_written(self):
        with tempfile.TemporaryDirectory() as d:
            lp.main(["--out-dir", d])
            files = sorted(p.name for p in Path(d).iterdir())
            self.assertEqual(files, ["sku-a.html", "sku-b.html"])


if __name__ == "__main__":
    unittest.main()
