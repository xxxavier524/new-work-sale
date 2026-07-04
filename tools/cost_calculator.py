#!/usr/bin/env python3
"""T1 落地成本计算器（docs/PROJECT_PLAN.md §5 / §9-T1）。

输入：config/economics.yaml（采购价/重量/售价/参数，全部可调）
输出：每 SKU 净利率、毛利红线闸门判定、保本单量、敏感性表（含三重悲观情形）

用法：
    python3 tools/cost_calculator.py
    python3 tools/cost_calculator.py --config config/economics.yaml
    python3 tools/cost_calculator.py --set fx_aud_cny=4.2 --set shipping_cny_per_kg=55

口径说明（与计划 §5.2 表格对齐）：
- 毛利率（红线口径）=（售价 − 采购 − 运费 − 包材）/ 售价，不含渠道费
- 单件净贡献 = 毛利 − 渠道费；净利率 = 净贡献 / 售价
- 拨备后净贡献 = 净贡献 − 退货拨备率 × 售价
- 保本单量 = 月固定成本 / 混合拨备后净贡献（按 mix 加权），向上取整
"""

import argparse
import copy
import math
import sys
from pathlib import Path

import yaml

DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "config" / "economics.yaml"


def load_config(path):
    with open(path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    for key in ("params", "skus"):
        if key not in cfg:
            raise ValueError(f"config 缺少 '{key}' 段")
    return cfg


def apply_overrides(cfg, overrides):
    """--set key=value 覆盖 params，参数改动即时生效（T1 验收项）。"""
    for item in overrides:
        key, _, raw = item.partition("=")
        key = key.strip()
        if not _ or key not in cfg["params"]:
            valid = ", ".join(cfg["params"])
            raise ValueError(f"无效覆盖 '{item}'，可用参数：{valid}")
        cfg["params"][key] = float(raw)
    return cfg


def compute_sku(sku, params):
    price_cny = sku["price_aud"] * params["fx_aud_cny"]
    shipping = sku.get("shipping_cny")
    if shipping is None:
        shipping = sku["weight_kg"] * params["shipping_cny_per_kg"]
    channel_fee = price_cny * params["channel_fee_rate"]
    gross = price_cny - sku["cost_cny"] - shipping - sku["packaging_cny"]
    net = gross - channel_fee
    net_after_returns = net - params["returns_provision"] * price_cny
    return {
        "id": sku["id"],
        "name": sku.get("name", sku["id"]),
        "price_aud": sku["price_aud"],
        "price_cny": price_cny,
        "cost_cny": sku["cost_cny"],
        "shipping_cny": shipping,
        "channel_fee": channel_fee,
        "packaging_cny": sku["packaging_cny"],
        "gross_profit": gross,
        "gross_margin": gross / price_cny,
        "net_contribution": net,
        "net_margin": net / price_cny,
        "net_after_returns": net_after_returns,
        "net_after_returns_margin": net_after_returns / price_cny,
        "gate_pass": gross / price_cny >= params["gross_margin_floor"],
        "mix": sku.get("mix", 0),
    }


def compute_all(cfg):
    params = cfg["params"]
    results = [compute_sku(s, params) for s in cfg["skus"]]
    mix_total = sum(r["mix"] for r in results)
    if mix_total > 0:
        blended_net = sum(r["net_after_returns"] * r["mix"] for r in results) / mix_total
        blended_price = sum(r["price_cny"] * r["mix"] for r in results) / mix_total
        blended_margin = blended_net / blended_price
        breakeven = math.ceil(params["fixed_cost_monthly"] / blended_net) if blended_net > 0 else None
    else:
        blended_net = blended_margin = breakeven = None
    return {
        "skus": results,
        "blended_net_after_returns": blended_net,
        "blended_net_margin": blended_margin,
        "breakeven_orders": breakeven,
    }


def scenario_configs(cfg):
    """基准 + 四个敏感性情形（§5.2）。返回 [(名称, 修改后的 cfg), ...]。"""
    sc = cfg.get("scenarios", {})
    aud = sc.get("aud_depreciation", 0.10)
    ship = sc.get("shipping_increase", 0.30)
    ret = sc.get("returns_stress", 0.12)

    def variant(fx_mult=1.0, ship_mult=1.0, returns=None):
        c = copy.deepcopy(cfg)
        c["params"]["fx_aud_cny"] *= fx_mult
        c["params"]["shipping_cny_per_kg"] *= ship_mult
        for s in c["skus"]:
            if s.get("shipping_cny") is not None:
                s["shipping_cny"] *= ship_mult
        if returns is not None:
            c["params"]["returns_provision"] = returns
        return c

    return [
        ("基准", cfg),
        (f"澳元贬 {aud:.0%}", variant(fx_mult=1 - aud)),
        (f"运费 +{ship:.0%}", variant(ship_mult=1 + ship)),
        (f"退货 {ret:.0%}", variant(returns=ret)),
        ("三重悲观叠加", variant(fx_mult=1 - aud, ship_mult=1 + ship, returns=ret)),
    ]


def render_report(cfg):
    params = cfg["params"]
    out = []
    out.append("# 落地成本模型报告（T1）")
    out.append("")
    out.append(f"参数：汇率 {params['fx_aud_cny']:.2f}｜渠道费 {params['channel_fee_rate']:.0%}｜"
               f"专线 ¥{params['shipping_cny_per_kg']:.0f}/kg｜退货拨备 {params['returns_provision']:.0%}｜"
               f"毛利红线 {params['gross_margin_floor']:.0%}｜固定成本 ¥{params['fixed_cost_monthly']:.0f}/月")
    out.append("")

    base = compute_all(cfg)
    out.append("## 每 SKU 落地成本（CNY）")
    out.append("")
    header = ["项目"] + [r["id"] for r in base["skus"]]
    rows = [
        ("售价", lambda r: f"A${r['price_aud']:.2f} ≈ ¥{r['price_cny']:.0f}"),
        ("采购", lambda r: f"{r['cost_cny']:.0f}"),
        ("运费", lambda r: f"{r['shipping_cny']:.0f}"),
        (f"渠道费 {params['channel_fee_rate']:.0%}", lambda r: f"{r['channel_fee']:.0f}"),
        ("包材杂项", lambda r: f"{r['packaging_cny']:.0f}"),
        ("毛利率（红线口径）", lambda r: f"{r['gross_margin']:.1%}"),
        ("单件净贡献", lambda r: f"{r['net_contribution']:.0f}（{r['net_margin']:.0%}）"),
        (f"拨备 {params['returns_provision']:.0%} 后净利率", lambda r: f"{r['net_after_returns_margin']:.1%}"),
        (f"红线闸门 ≥{params['gross_margin_floor']:.0%}", lambda r: "✅ 通过" if r["gate_pass"] else "❌ 不上架"),
    ]
    out.append("| " + " | ".join(header) + " |")
    out.append("|" + "---|" * len(header))
    for label, fn in rows:
        out.append("| " + " | ".join([label] + [fn(r) for r in base["skus"]]) + " |")
    out.append("")

    if base["breakeven_orders"] is not None:
        out.append(f"**盈亏平衡**：固定成本 ¥{params['fixed_cost_monthly']:.0f}/月 ÷ "
                   f"混合拨备后净贡献 ¥{base['blended_net_after_returns']:.0f}/单 → "
                   f"**约 {base['breakeven_orders']} 单/月保本**")
        out.append("")

    out.append("## 敏感性分析（混合净率，含退货拨备）")
    out.append("")
    ids = [r["id"] for r in base["skus"]]
    out.append("| 情形 | " + " | ".join(ids) + " | 混合净率 | 保本单量 |")
    out.append("|" + "---|" * (len(ids) + 3))
    worst_positive = True
    for name, c in scenario_configs(cfg):
        res = compute_all(c)
        cells = [f"{r['net_after_returns_margin']:.1%}" for r in res["skus"]]
        blended = f"{res['blended_net_margin']:.1%}" if res["blended_net_margin"] is not None else "—"
        be = str(res["breakeven_orders"]) if res["breakeven_orders"] else "亏损"
        out.append(f"| {name} | " + " | ".join(cells) + f" | {blended} | {be} |")
        if name == "三重悲观叠加" and res["blended_net_margin"] is not None:
            worst_positive = res["blended_net_margin"] > 0
    out.append("")
    out.append("三重悲观情形下混合净率" + ("仍为正 ✅（55% 红线的存在意义）" if worst_positive
               else "**为负 ❌ —— 触发模型失效条款，重估该 SKU 组合**"))
    out.append("")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description="T1 落地成本计算器")
    ap.add_argument("--config", default=str(DEFAULT_CONFIG), help="economics.yaml 路径")
    ap.add_argument("--set", action="append", default=[], metavar="KEY=VALUE",
                    help="覆盖 params 中任意参数，可多次使用（如 --set fx_aud_cny=4.2）")
    args = ap.parse_args(argv)
    cfg = apply_overrides(load_config(args.config), args.set)
    print(render_report(cfg))
    return 0


if __name__ == "__main__":
    sys.exit(main())
