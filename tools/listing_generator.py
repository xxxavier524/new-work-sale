#!/usr/bin/env python3
"""T3 Listing 生成器（docs/PROJECT_PLAN.md §9-T3）。

输入：config/listings.yaml（SKU 规格 + 卖点，每条 claim 溯源 painpoint id）
      + data/painpoints.yaml（校验溯源有效性）
输出：每 SKU 英文标题/五点/描述 × 3 变体（AB 测试用）
验收：每条卖点可溯源到具体痛点编号 —— annotated 模式输出 [C1] 标签；
      clean 模式输出可直接粘贴上架的纯文案。

用法：
    python3 tools/listing_generator.py                    # 全部 SKU，annotated
    python3 tools/listing_generator.py --sku SKU-A --clean
"""

import argparse
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LISTINGS = ROOT / "config" / "listings.yaml"
DEFAULT_PAINPOINTS = ROOT / "data" / "painpoints.yaml"

EBAY_TITLE_LIMIT = 80

# 三个 AB 变体的组稿角度
VARIANTS = [
    ("V1 pain-led", "痛点直击：按竞品差评频次排列卖点，首行即最高频痛点的反面"),
    ("V2 proof-led", "证据先行：每条卖点附带 proof，适合比价型买家"),
    ("V3 scenario-led", "场景带入：以使用场景开头，卖点融入场景叙述"),
]


def load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def valid_painpoint_ids(painpoints_path=DEFAULT_PAINPOINTS):
    data = load_yaml(painpoints_path)
    return {p["id"] for cat in data["categories"] for p in cat["painpoints"]}


def validate(listings, valid_ids):
    """所有 claim/faq/comparison 的 painpoint 溯源必须存在（T3 验收）。"""
    errors = []
    for sku in listings["skus"]:
        for c in sku["claims"]:
            if c.get("painpoint") not in valid_ids:
                errors.append(f"{sku['id']} claim '{c['bullet'][:30]}…' 溯源缺失或无效")
        for row in sku.get("comparison", {}).get("rows", []):
            pid = row.get("painpoint")
            if pid is not None and pid not in valid_ids:
                errors.append(f"{sku['id']} comparison '{row['feature']}' 溯源无效: {pid}")
        for f in sku.get("faq", []):
            if f.get("painpoint") not in valid_ids:
                errors.append(f"{sku['id']} faq '{f['q'][:30]}…' 溯源缺失或无效")
        for t in sku["title_variants"]:
            if len(t) > EBAY_TITLE_LIMIT:
                errors.append(f"{sku['id']} 标题超 {EBAY_TITLE_LIMIT} 字符（{len(t)}）：{t}")
    return errors


def bullet_line(claim, variant_idx, annotated):
    tag = f" [{claim['painpoint']}]" if annotated else ""
    if variant_idx == 1:  # proof-led
        return f"- {claim['bullet']} — {claim['proof']}{tag}"
    return f"- {claim['bullet']}{tag}"


def description(sku, policy, variant_idx, annotated):
    parts = []
    if variant_idx == 2:  # scenario-led
        parts.append(sku["scenario_hook"])
    parts.append(f"{sku['tagline']} {sku['product_name']} — {sku['fitment']}.")
    for c in sku["claims"]:
        tag = f" [{c['painpoint']}]" if annotated else ""
        parts.append(f"{c['bullet']}: {c['proof']}.{tag}")
    parts.append(policy)
    return "\n\n".join(parts)


def render_sku(sku, policy, annotated=True):
    out = [f"# {sku['id']}｜{sku['product_name']}（A${sku['price_aud']}）", ""]
    if annotated:
        out.append("> annotated 模式：[Cx]/[Jx] 为卖点溯源标签（data/painpoints.yaml），上架前用 --clean 重新生成")
        out.append("")
    for i, (vname, vdesc) in enumerate(VARIANTS):
        title = sku["title_variants"][i]
        out.append(f"## {vname}（{vdesc}）")
        out.append("")
        out.append(f"**标题**（{len(title)}/{EBAY_TITLE_LIMIT} 字符）：`{title}`")
        out.append("")
        out.append("**五点卖点：**")
        claims = sku["claims"]
        if i == 0:  # pain-led：保持 yaml 顺序（已按差评频次排列）
            ordered = claims
        elif i == 1:
            ordered = claims
        else:       # scenario-led：功能性卖点靠前，服务政策殿后
            ordered = sorted(claims, key=lambda c: c["painpoint"].startswith("C4"))
        for c in ordered[:5]:
            out.append(bullet_line(c, i, annotated))
        out.append("")
        out.append("**描述：**")
        out.append("")
        out.append(description(sku, policy, i, annotated))
        out.append("")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description="T3 Listing 生成器")
    ap.add_argument("--listings", default=str(DEFAULT_LISTINGS))
    ap.add_argument("--painpoints", default=str(DEFAULT_PAINPOINTS))
    ap.add_argument("--sku", help="只生成指定 SKU")
    ap.add_argument("--clean", action="store_true", help="输出无溯源标签的上架版")
    args = ap.parse_args(argv)

    listings = load_yaml(args.listings)
    errors = validate(listings, valid_painpoint_ids(args.painpoints))
    if errors:
        print("溯源校验失败（T3 验收不通过）：", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    for sku in listings["skus"]:
        if args.sku and sku["id"] != args.sku:
            continue
        print(render_sku(sku, listings["store_policy"], annotated=not args.clean))
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
