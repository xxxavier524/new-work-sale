#!/usr/bin/env python3
"""T2 差评挖掘 pipeline（docs/PROJECT_PLAN.md §9-T2）。

输入：评论 CSV（人工从评价页导出，⚠ 注意目标站 robots/ToS —— 手动导出 + 本地分析）
    列：source, product, rating, date, text   （product 取 4wd / squid，留空则全类目匹配）
输出：痛点榜单（频次 × severity 加权排名）+ 样例引用 + 未归类评论（新痛点候选）
验收：对 §4 的人工聚类结果可复现（词典来自 data/painpoints.yaml 的 keywords 字段）

用法：
    python3 tools/review_miner.py --reviews data/templates/reviews_sample.csv
    python3 tools/review_miner.py --reviews my.csv --emit-llm-prompt   # 生成 LLM 聚类提示词

词典模式为离线基线；语义级聚类用 --emit-llm-prompt 把评论打包成提示词，
粘贴给 Claude 得到 JSON 榜单（新痛点发现能力强于词典）。
"""

import argparse
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PAINPOINTS = ROOT / "data" / "painpoints.yaml"

SEVERITY_WEIGHT = {"high": 3, "medium": 2, "low": 1}
# 类目名 → product 列取值
CATEGORY_KEY = {"4WD 软装": "4wd", "木虾/Squid jig": "squid"}


def load_painpoints(path=DEFAULT_PAINPOINTS):
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    points = []
    for cat in data["categories"]:
        for p in cat["painpoints"]:
            points.append({
                "id": p["id"],
                "title": p["title"],
                "severity": p.get("severity", "medium"),
                "counter": p.get("counter", ""),
                "category": CATEGORY_KEY.get(cat["name"], ""),
                "patterns": [re.compile(r"\b" + re.escape(k.lower()) + r"\b")
                             for k in p.get("keywords", [])],
            })
    return points


def read_reviews(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return [dict(r) for r in csv.DictReader(f)]


def classify(reviews, painpoints):
    """返回 (hits: id->[review], unmatched: [review])。一条评论可命中多个痛点。"""
    hits = defaultdict(list)
    unmatched = []
    for r in reviews:
        text = (r.get("text") or "").lower()
        product = (r.get("product") or "").strip().lower()
        matched = False
        for p in painpoints:
            if p["category"] and product and p["category"] != product:
                continue
            if any(pat.search(text) for pat in p["patterns"]):
                hits[p["id"]].append(r)
                matched = True
        if not matched:
            unmatched.append(r)
    return hits, unmatched


def rank(hits, painpoints):
    rows = []
    for p in painpoints:
        n = len(hits.get(p["id"], []))
        if n:
            rows.append({**p, "count": n,
                         "score": n * SEVERITY_WEIGHT[p["severity"]]})
    return sorted(rows, key=lambda r: (-r["score"], -r["count"], r["id"]))


def render(hits, unmatched, ranked, total):
    out = ["# 痛点榜单（T2 词典模式）", ""]
    out.append(f"输入评论 {total} 条｜命中 {total - len(unmatched)} 条｜未归类 {len(unmatched)} 条")
    out.append("")
    out.append("| 排名 | ID | 痛点 | 命中数 | severity | 加权分 | 我方对策 |")
    out.append("|---|---|---|---|---|---|---|")
    for i, r in enumerate(ranked, 1):
        out.append(f"| {i} | {r['id']} | {r['title']} | {r['count']} | "
                   f"{r['severity']} | {r['score']} | {r['counter']} |")
    out.append("")
    out.append("## 样例引用（每痛点前 2 条）")
    out.append("")
    for r in ranked:
        out.append(f"**{r['id']} {r['title']}**")
        for rev in hits[r["id"]][:2]:
            text = (rev.get("text") or "").strip().replace("\n", " ")
            out.append(f"- 「{text[:120]}」（{rev.get('source', '?')}，评分 {rev.get('rating', '?')}）")
        out.append("")
    if unmatched:
        out.append("## 未归类评论（新痛点候选，建议跑一次 LLM 聚类）")
        out.append("")
        for rev in unmatched[:10]:
            text = (rev.get("text") or "").strip().replace("\n", " ")
            out.append(f"- 「{text[:120]}」")
        out.append("")
    return "\n".join(out)


def llm_prompt(reviews, painpoints):
    """生成可直接粘贴给 Claude 的聚类提示词（语义模式）。"""
    known = "\n".join(f"- {p['id']}: {p['title']} (severity={p['severity']})"
                      for p in painpoints)
    lines = "\n".join(f"{i}. [{r.get('product','?')}|rating {r.get('rating','?')}] "
                      f"{(r.get('text') or '').strip()}"
                      for i, r in enumerate(reviews, 1))
    return f"""你是差评聚类分析器。已知痛点分类（来自人工研究）：
{known}

任务：把下面每条评论归入上述分类（可多选）；无法归类的提出新痛点（id 用 NEW-1, NEW-2…）。
输出 JSON：{{"assignments": [{{"review": 序号, "painpoints": ["C1"]}}],
"new_painpoints": [{{"id": "NEW-1", "title": "...", "evidence": "...", "severity": "high|medium|low"}}],
"ranking": [{{"id": "C1", "count": N, "severity_weighted_score": N}}]}}

评论列表：
{lines}
"""


def main(argv=None):
    ap = argparse.ArgumentParser(description="T2 差评挖掘 pipeline")
    ap.add_argument("--reviews", required=True, help="评论 CSV 路径")
    ap.add_argument("--painpoints", default=str(DEFAULT_PAINPOINTS))
    ap.add_argument("--emit-llm-prompt", action="store_true",
                    help="不做词典聚类，输出 LLM 聚类提示词")
    args = ap.parse_args(argv)

    painpoints = load_painpoints(args.painpoints)
    reviews = read_reviews(args.reviews)
    if args.emit_llm_prompt:
        print(llm_prompt(reviews, painpoints))
        return 0
    hits, unmatched = classify(reviews, painpoints)
    ranked = rank(hits, painpoints)
    print(render(hits, unmatched, ranked, len(reviews)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
