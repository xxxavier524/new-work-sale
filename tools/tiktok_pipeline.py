#!/usr/bin/env python3
"""营销模块 M1：TikTok 全 AI 内容工作流（策略见 docs/tiktok-playbook.md）。

三个子命令：
  brief    批量生成视频简报：钩子+分镜脚本+Seedance 提示词+文案标签+合规清单
  calendar 生成 30 天发布日历 CSV
  report   读发布数据 CSV → 周报：漏斗指标、$200 目标进度、支柱加减产建议

用法：
    python3 tools/tiktok_pipeline.py brief --count 7
    python3 tools/tiktok_pipeline.py brief --count 7 --emit-llm-prompt
    python3 tools/tiktok_pipeline.py calendar --days 30 --start 2026-08-01
    python3 tools/tiktok_pipeline.py report --stats data/private/tiktok_stats.csv

生成是确定性的（同参数同输出），便于团队协作与回归测试；
需要更高文案质感时用 --emit-llm-prompt 让 Claude 精修（AI 脚本属平台豁免范围）。
"""

import argparse
import csv
import io
import sys
from datetime import date, timedelta
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cost_calculator as cc

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TIKTOK = ROOT / "config" / "tiktok.yaml"
DEFAULT_ECON = ROOT / "config" / "economics.yaml"


def load(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


# ---------- brief ----------

def pillar_rotation(cfg):
    """按 weight 展开支柱轮换序列，如 [P1,P1,P1,P2,P2,P3,P3,P3,P4,P4]。"""
    seq = []
    for p in cfg["pillars"]:
        seq.extend([p] * p["weight"])
    return seq


def pick(items, i):
    return items[i % len(items)]


def make_brief(cfg, econ_by_sku, n):
    """第 n 条（从 0 起）视频简报，确定性轮换。

    occ = 本支柱第几次出现（0 起）——用它轮换钩子与镜头，
    避免同支柱连续几条撞同一钩子/同一首镜头。
    """
    seq = pillar_rotation(cfg)
    pillar = pick(seq, n)
    occ = sum(1 for j in range(n) if pick(seq, j)["id"] == pillar["id"])
    hooks = [h for h in cfg["hooks"] if h["pillar"] == pillar["id"]]
    hook = pick(hooks, occ)
    structure = pick(cfg["structures"], n)
    cta = pick(cfg["ctas"], n)
    shots = [s for s in cfg["seedance"]["shot_bank"] if s["pillar"] == pillar["id"]]
    shots = shots[occ % len(shots):] + shots[:occ % len(shots)] if shots else []
    tags = cfg["hashtags"]["base"] + cfg["hashtags"].get(pillar["id"], [])
    econ = econ_by_sku.get(pillar["sku"])
    return {
        "id": f"VID-{n + 1:03d}",
        "pillar": pillar,
        "hook": hook,
        "structure": structure,
        "cta": cta,
        "shots": shots,
        "hashtags": tags,
        "econ": econ,
    }


def render_brief(b, cfg):
    sd = cfg["seedance"]
    out = [f"### {b['id']}｜{b['pillar']['name']}（{b['pillar']['sku']}）"
           f"｜结构 {b['structure']['name']}", ""]
    out.append(f"**钩子（0–2s 台词）**：{b['hook']['text']}  ·（溯源 {b['hook']['source']}）")
    out.append("")
    out.append("**分镜：**")
    ai_shot_i = 0
    for beat in b["structure"]["beats"]:
        role = beat["role"]
        if role in ("solve", "reveal", "process"):
            out.append(f"- `{beat['t']}` {role}：**［实拍位］** 产品特写用样品实拍"
                       f"（清单见 config/tiktok.yaml real_footage_checklist）——{beat['note']}")
        elif role == "cta":
            out.append(f"- `{beat['t']}` cta：口播「{b['cta']['text']}」+ 文字条")
        else:
            shot = b["shots"][ai_shot_i % len(b["shots"])] if b["shots"] else None
            ai_shot_i += 1
            if shot:
                out.append(f"- `{beat['t']}` {role}：Seedance 生成（{shot['id']}）——{beat['note']}")
                out.append(f"  - prompt: `{shot['prompt']}, {sd['base_style']}`")
                out.append(f"  - negative: `{sd['negative']}`")
    out.append("")
    out.append(f"**文案**：{b['hook']['text']} {' '.join(b['hashtags'][:6])}")
    out.append("")
    out.append(f"**发布检查**：☐ AIGC 标签开 ☐ 实拍位已替换非 AI 素材 "
               f"☐ {'商业披露开（含折扣码）' if b['cta']['mode'] == 'discount' else '无需商业披露'} "
               f"☐ 封面帧=钩子画面")
    out.append("")
    return "\n".join(out)


def llm_polish_prompt(briefs, cfg):
    blocks = []
    for b in briefs:
        blocks.append(f"{b['id']}｜pillar={b['pillar']['name']}｜hook=\"{b['hook']['text']}\""
                      f"｜structure={b['structure']['name']}｜cta=\"{b['cta']['text']}\"")
    joined = "\n".join(blocks)
    return f"""你是澳洲户外垂类 TikTok 编剧。把下面每条视频简报扩写成 15–27 秒口播脚本（EN-AU 口语，
澳式表达，短句，每句一行标注秒数）。规则：
1. 钩子台词保持原文不改（已 AB 设计）
2. 产品卖点只能用 config/listings.yaml 中溯源过的 claim，不得新增功能宣称
3. 不写 "waterproof"（只能 water-resistant）；不承诺渔获量
4. CTA 保持原文
5. 每条输出后附 caption（钩子改写 + 已给 hashtag）

简报列表：
{joined}
"""


# ---------- calendar ----------

def make_calendar(cfg, days, start):
    rows = []
    for i in range(days):
        d = start + timedelta(days=i)
        b_pillar = pick(pillar_rotation(cfg), i)
        rows.append({
            "date": d.isoformat(),
            "video_id": f"VID-{i + 1:03d}",
            "pillar": b_pillar["id"],
            "sku": b_pillar["sku"],
            "post_time_aest": cfg["params"]["post_time_local"],
            "status": "planned",
        })
    return rows


# ---------- report ----------

def order_profit_cny(econ, discount):
    """归因单利润（CNY）= 单件净贡献 − 折扣让利。"""
    return econ["net_contribution"] - discount * econ["price_cny"]


def build_report(stats, cfg, econ_by_sku):
    p = cfg["params"]
    pillar_sku = {pl["id"]: pl["sku"] for pl in cfg["pillars"]}
    pillar_name = {pl["id"]: pl["name"] for pl in cfg["pillars"]}
    def zero():
        return {"videos": 0, "views": 0, "likes": 0, "comments": 0, "shares": 0,
                "clicks": 0, "orders": 0, "profit_cny": 0.0}

    tot = zero()
    per_pillar = {}
    for r in stats:
        pid = r["pillar"].strip()
        sku = pillar_sku.get(pid)
        econ = econ_by_sku.get(sku)
        orders = int(r.get("orders") or 0)
        profit = orders * order_profit_cny(econ, p["attribution_discount"]) if econ else 0.0
        s = per_pillar.setdefault(pid, zero())
        for tgt in (tot, s):
            tgt["videos"] += 1
            tgt["views"] += int(r.get("views") or 0)
            tgt["likes"] += int(r.get("likes") or 0)
            tgt["comments"] += int(r.get("comments") or 0)
            tgt["shares"] += int(r.get("shares") or 0)
            tgt["clicks"] += int(r.get("link_clicks") or 0)
            tgt["orders"] += orders
            tgt["profit_cny"] += profit

    cost_cny = tot["videos"] * p["video_cost_cny"]
    net_cny = tot["profit_cny"] - cost_cny
    net_usd = net_cny / p["fx_cny_usd"]
    goal = p["profit_goal_usd"]

    def rate(a, b):
        return a / b if b else 0.0

    out = ["# TikTok 周报（M1）", ""]
    out.append(f"- 已发布 {tot['videos']} 条｜播放 {tot['views']:,}｜"
               f"互动率 {rate(tot['likes'] + tot['comments'] + tot['shares'], tot['views']):.2%}｜"
               f"链接点击率 {rate(tot['clicks'], tot['views']):.2%}")
    out.append(f"- 归因订单 {tot['orders']} 单｜归因利润 ¥{tot['profit_cny']:,.0f}｜"
               f"内容成本 ¥{cost_cny:,.0f}（{tot['videos']} × ¥{p['video_cost_cny']}）")
    out.append(f"- **净利润 ${net_usd:,.0f} / 目标 ${goal}"
               f"（{rate(net_usd, goal):.0%}）** "
               + ("✅ 目标达成——去续 Max 20x 吧" if net_usd >= goal else
                  f"，还差 ${goal - net_usd:,.0f}"))
    out.append("")
    out.append("## 分支柱表现")
    out.append("")
    out.append("| 支柱 | 条数 | 播放 | 互动率 | 点击率 | 订单 | 利润(¥) | 建议 |")
    out.append("|---|---|---|---|---|---|---|---|")
    for pid, s in sorted(per_pillar.items()):
        eng = rate(s["likes"] + s["comments"] + s["shares"], s["views"])
        ctr = rate(s["clicks"], s["views"])
        if s["videos"] >= 6 and eng < 0.02 and s["orders"] == 0:
            advice = "🔴 杀停：换钩子库重做或砍支柱"
        elif s["orders"] > 0 and ctr >= 0.01:
            advice = "🟢 加产：weight +1，钩子做变体"
        else:
            advice = "🟡 续跑观察"
        out.append(f"| {pid} {pillar_name.get(pid, '')} | {s['videos']} | {s['views']:,} | "
                   f"{eng:.2%} | {ctr:.2%} | {s['orders']} | {s['profit_cny']:,.0f} | {advice} |")
    out.append("")
    out.append("数据来源：TikTok Analytics 手动导出 + 订单表 TIKTOK10 折扣码归因；"
               "口径注意：bio 链接点击到 eBay 后无法全程追踪，折扣码归因是下限估计。")
    return "\n".join(out)


# ---------- main ----------

def main(argv=None):
    ap = argparse.ArgumentParser(description="M1 TikTok 内容工作流")
    sub = ap.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("brief", help="批量生成视频简报")
    b.add_argument("--count", type=int, default=7)
    b.add_argument("--start-id", type=int, default=1, help="起始编号（续批用）")
    b.add_argument("--emit-llm-prompt", action="store_true")

    c = sub.add_parser("calendar", help="发布日历 CSV")
    c.add_argument("--days", type=int, default=30)
    c.add_argument("--start", default=None, help="YYYY-MM-DD，默认明天")

    r = sub.add_parser("report", help="数据周报")
    r.add_argument("--stats", required=True)

    ap.add_argument("--config", default=str(DEFAULT_TIKTOK))
    ap.add_argument("--economics", default=str(DEFAULT_ECON))
    args = ap.parse_args(argv)

    cfg = load(args.config)
    econ_by_sku = {s["id"]: s for s in cc.compute_all(cc.load_config(args.economics))["skus"]}

    if args.cmd == "brief":
        briefs = [make_brief(cfg, econ_by_sku, args.start_id - 1 + i)
                  for i in range(args.count)]
        if args.emit_llm_prompt:
            print(llm_polish_prompt(briefs, cfg))
        else:
            print(f"# 视频简报批次（{briefs[0]['id']}–{briefs[-1]['id']}）\n")
            for br in briefs:
                print(render_brief(br, cfg))
    elif args.cmd == "calendar":
        start = (date.fromisoformat(args.start) if args.start
                 else date.today() + timedelta(days=1))
        rows = make_calendar(cfg, args.days, start)
        w = csv.DictWriter(sys.stdout, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    elif args.cmd == "report":
        with open(args.stats, encoding="utf-8-sig", newline="") as f:
            stats = [dict(row) for row in csv.DictReader(f)]
        print(build_report(stats, cfg, econ_by_sku))
    return 0


if __name__ == "__main__":
    sys.exit(main())
