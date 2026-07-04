#!/usr/bin/env python3
"""T6 周报 dashboard（docs/PROJECT_PLAN.md §9-T6）。

输入：订单/广告费/库存 CSV（模板见 data/templates/）
输出：markdown 周报 —— 单量、退货率、估算净利、库存周转天数、G3/G4 距离
验收：每周一 10 分钟内完成复盘。

用法：
    python3 tools/weekly_report.py --orders data/private/orders.csv \
        --ads data/private/ads.csv --inventory data/private/inventory.csv
    python3 tools/weekly_report.py --orders ... --as-of 2026-08-01

CSV 列定义（见模板）：
- orders.csv:    date, order_id, sku, qty, sale_aud, status   （status: delivered/shipped/returned）
- ads.csv:       date, channel, spend_cny
- inventory.csv: sku, units_on_hand
估算净利 = Σ(有效件数 × 该 SKU 单件净贡献[T1]) − 广告费 − 固定成本摊销 − 退货件损失(货+运)
"""

import argparse
import csv
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cost_calculator as cc

DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "config" / "economics.yaml"

# 闸门阈值（docs/PROJECT_PLAN.md §6）
G3_MIN_ORDERS_30D = 30      # 上架 30 天 ≥30 单
G3_MAX_RETURN_RATE = 0.08   # 退货率 <8%
G4_MIN_MONTHLY_NET = 3000   # 单 SKU 月净利 ≥¥3,000（本报告按全店与分 SKU 同时给出）
DAYS_PER_MONTH = 30.4


def read_csv(path):
    if path is None:
        return []
    with open(path, encoding="utf-8-sig", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def parse_date(s):
    return datetime.strptime(s.strip(), "%Y-%m-%d").date()


def window(rows, as_of, days):
    lo = as_of - timedelta(days=days - 1)
    return [r for r in rows if lo <= parse_date(r["date"]) <= as_of]


def summarize_orders(orders, econ_by_sku):
    """返回 (单量, 件数, 销售额AUD, 退货单量, 估算净贡献CNY, 分SKU统计)。"""
    n_orders = n_units = 0
    sales_aud = 0.0
    n_returned = 0
    net_cny = 0.0
    per_sku = {}
    for o in orders:
        sku = o["sku"].strip()
        qty = int(o["qty"])
        returned = o["status"].strip().lower() == "returned"
        econ = econ_by_sku.get(sku)
        s = per_sku.setdefault(sku, {"orders": 0, "units": 0, "returned": 0, "net_cny": 0.0})
        s["orders"] += 1
        n_orders += 1
        if returned:
            n_returned += 1
            s["returned"] += 1
            if econ:  # 退货损失：货值 + 去程运费（澳洲直发小件不召回，见 §4.1-C4 政策）
                loss = (econ["cost_cny"] + econ["shipping_cny"]) * qty
                net_cny -= loss
                s["net_cny"] -= loss
        else:
            n_units += qty
            sales_aud += float(o["sale_aud"])
            s["units"] += qty
            if econ:
                net_cny += econ["net_contribution"] * qty
                s["net_cny"] += econ["net_contribution"] * qty
    return n_orders, n_units, sales_aud, n_returned, net_cny, per_sku


def gate_line(label, value, target, ok, fmt="{:.0f}"):
    mark = "✅" if ok else "🔴"
    return f"- {mark} {label}：{fmt.format(value)} / 目标 {fmt.format(target)}"


def build_report(orders, ads, inventory, cfg, as_of):
    econ_by_sku = {r["id"]: r for r in cc.compute_all(cfg)["skus"]}
    fixed_monthly = cfg["params"]["fixed_cost_monthly"]
    fx = cfg["params"]["fx_aud_cny"]

    out = [f"# 周报（截至 {as_of.isoformat()}）", ""]

    for label, days in (("近 7 天", 7), ("近 30 天", 30)):
        w_orders = window(orders, as_of, days)
        w_ads = window(ads, as_of, days)
        n_o, n_u, sales, n_ret, net, per_sku = summarize_orders(w_orders, econ_by_sku)
        ad_spend = sum(float(a["spend_cny"]) for a in w_ads)
        fixed = fixed_monthly * days / DAYS_PER_MONTH
        est_profit = net - ad_spend - fixed
        ret_rate = n_ret / n_o if n_o else 0.0

        out.append(f"## {label}")
        out.append("")
        out.append(f"- 单量 {n_o}（退货 {n_ret}，退货率 {ret_rate:.1%}）｜有效件数 {n_u}")
        out.append(f"- 销售额 A${sales:,.0f} ≈ ¥{sales * fx:,.0f}")
        out.append(f"- 广告费 ¥{ad_spend:,.0f}｜固定成本摊销 ¥{fixed:,.0f}")
        out.append(f"- **估算净利 ¥{est_profit:,.0f}**")
        if per_sku:
            parts = [f"{sku} {s['orders']}单/净贡献¥{s['net_cny']:,.0f}" for sku, s in sorted(per_sku.items())]
            out.append(f"- 分 SKU：{'；'.join(parts)}")
        out.append("")

        if days == 30:
            out.append("## 闸门距离")
            out.append("")
            out.append(gate_line("G3 单量（30 天 ≥30 单）", n_o, G3_MIN_ORDERS_30D, n_o >= G3_MIN_ORDERS_30D))
            out.append(gate_line("G3 退货率（<8%）", ret_rate, G3_MAX_RETURN_RATE,
                                 ret_rate < G3_MAX_RETURN_RATE, fmt="{:.1%}"))
            if ret_rate >= G3_MAX_RETURN_RATE and n_o:
                out.append("  - ⚠ 退货率触发报警线：立即做差评/退货归因（§6 D61 周度动作提前）")
            out.append(gate_line("G4 月净利（≥¥3,000）", est_profit, G4_MIN_MONTHLY_NET,
                                 est_profit >= G4_MIN_MONTHLY_NET, fmt="¥{:,.0f}"))
            best_sku_net = max((s["net_cny"] for s in per_sku.values()), default=0.0)
            out.append(gate_line("G4 最佳单 SKU 月净贡献（≥¥3,000，未扣广告/固定）",
                                 best_sku_net, G4_MIN_MONTHLY_NET,
                                 best_sku_net >= G4_MIN_MONTHLY_NET, fmt="¥{:,.0f}"))
            out.append("")

            if inventory:
                out.append("## 库存周转")
                out.append("")
                out.append("| SKU | 在手 | 日均销量(30d) | 周转天数 | 状态 |")
                out.append("|---|---|---|---|---|")
                for row in inventory:
                    sku = row["sku"].strip()
                    on_hand = int(row["units_on_hand"])
                    daily = per_sku.get(sku, {}).get("units", 0) / days
                    if daily > 0:
                        turn = on_hand / daily
                        status = "🔴 >60 天，触发失效条款复查" if turn > 60 else ("⚠ 备货" if turn < 21 else "✅")
                        turn_s = f"{turn:.0f}"
                    else:
                        turn_s, status = "∞", "🔴 零动销"
                    out.append(f"| {sku} | {on_hand} | {daily:.2f} | {turn_s} | {status} |")
                out.append("")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description="T6 周报 dashboard")
    ap.add_argument("--orders", required=True, help="订单 CSV")
    ap.add_argument("--ads", help="广告费 CSV（可选）")
    ap.add_argument("--inventory", help="库存 CSV（可选）")
    ap.add_argument("--config", default=str(DEFAULT_CONFIG), help="economics.yaml 路径")
    ap.add_argument("--as-of", help="报告截止日 YYYY-MM-DD，默认今天")
    args = ap.parse_args(argv)

    as_of = parse_date(args.as_of) if args.as_of else date.today()
    cfg = cc.load_config(args.config)
    print(build_report(read_csv(args.orders), read_csv(args.ads),
                       read_csv(args.inventory), cfg, as_of))
    return 0


if __name__ == "__main__":
    sys.exit(main())
