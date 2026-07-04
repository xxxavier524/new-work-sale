# 跨境电商工具仓：澳洲双类目主线 + 俄罗斯备线

单一事实来源：**[docs/PROJECT_PLAN.md](docs/PROJECT_PLAN.md)**（先读它）。
本仓库承载计划 §9 的 Claude Code 任务清单产出：可复算的单位经济模型、周复盘工具、以及运营 SOP/模板。

## 快速开始

```bash
pip install -r requirements.txt   # 仅 PyYAML

# T1 落地成本计算器：净利率 / 55% 红线闸门 / 保本单量 / 敏感性表
python3 tools/cost_calculator.py
python3 tools/cost_calculator.py --set fx_aud_cny=4.2        # 参数即时覆盖
# 新增候选 SKU：编辑 config/economics.yaml 的 skus 段后重跑即可

# T2 差评挖掘：评论 CSV → 痛点榜单（或 --emit-llm-prompt 生成 LLM 聚类提示词）
python3 tools/review_miner.py --reviews data/templates/reviews_sample.csv

# T3 Listing：3 变体标题/五点/描述；--clean 输出可直接上架版
python3 tools/listing_generator.py --sku SKU-A --clean

# T4 落地页：从 config/listings.yaml 生成 web/*.html（含 JSON-LD）
python3 tools/landing_page.py

# T6 周报（真实数据放 data/private/，已 gitignore；模板见 data/templates/）
python3 tools/weekly_report.py --orders data/private/orders.csv \
    --ads data/private/ads.csv --inventory data/private/inventory.csv

# 测试
python3 -m unittest discover -s tests
```

## 任务清单状态（对应 PROJECT_PLAN §9）

| 任务 | 状态 | 位置 |
|---|---|---|
| T1 落地成本计算器 | ✅ | `tools/cost_calculator.py` + `config/economics.yaml`，§5.2 数字已复现（测试锁定）|
| T2 差评挖掘 pipeline | ✅ | `tools/review_miner.py`：词典聚类（复现 §4）+ LLM 提示词导出；样例见 `data/templates/reviews_sample.csv` |
| T3 Listing 生成器 | ✅ | `tools/listing_generator.py` + `config/listings.yaml`：3 变体，卖点溯源到痛点 id（校验强制）|
| T4 GEO 落地页 | ✅ | `tools/landing_page.py` → `web/*.html`：Product+FAQPage JSON-LD、对比页；上线前跑 Rich Results Test，配图待 G2 样品实拍 |
| T5 客服 SOP + 模板库 | ✅ | `docs/customer-service-sop.md`（10 场景英文模板 + 升级线）|
| T6 周报 dashboard | ✅ | `tools/weekly_report.py`（G3/G4 距离、退货报警、库存周转）|
| T7 政策监控清单 | ✅ | `docs/policy-watchlist.md`（四项硬指标 + 季度 checklist）|
| T8 EAC 避雷 + Ozon 材料 | ✅ 初版 | `docs/ozon-eac-checklist.md`（⚠ 启动备线前逐项复核）|
| T9 达人外联 CRM | ✅ | `crm/creators.csv` + `crm/outreach-templates.md` |

## 当前关键路径（人工，机器代替不了）

**G1 开闸判定**（PROJECT_PLAN §11「立即下一步」）：
按 **[docs/g1-worksheet.md](docs/g1-worksheet.md)** 完成 eBay AU sold 数据验证 + IP Australia 外观排雷（约 30 分钟），
结果回填底稿。自动化代查已尝试且被网络策略拦截（详见底稿 §D，含竞品定价补充情报）；
按 §6 卡点纪律，sold 数据必须人工取证，不得以搜索热度替代。成本模型侧 T1 已验证：SKU-A 毛利 63.8% / SKU-B 62.1%，均过 55% 红线；
G1 要求 ≥3 个 SKU 过线，第三候选 SKU 询价后加入 `config/economics.yaml` 复算。

## 纪律三条（不可协商，工具已内置）

1. **毛利红线 55% 以下不上架** —— T1 计算器每次运行输出闸门判定
2. **一期负面清单禁碰**（承重救援/带电/刀刃/铅坠/车灯/头盔）—— 见 PROJECT_PLAN §3
3. **G3 止损线无条件执行**（30 天 <30 单或退货 ≥8% → 清仓换 SKU）—— T6 周报每周输出距离

## 目录结构

```
config/economics.yaml     # 单位经济参数 + SKU 定义（全部可调）
config/listings.yaml      # Listing/落地页数据源（卖点强制溯源痛点 id）
tools/cost_calculator.py  # T1
tools/review_miner.py     # T2
tools/listing_generator.py# T3
tools/landing_page.py     # T4
tools/weekly_report.py    # T6
web/                      # T4 生成的静态落地页（改 listings.yaml 后重新生成）
data/painpoints.yaml      # §4 痛点档案 + T2 分类词典（机器可读）
data/templates/           # 周报/评论输入 CSV 模板
data/private/             # 真实运营数据（gitignore，不入库）
docs/                     # 计划原文 + G1 底稿 + SOP + 政策监控 + EAC 清单
crm/                      # 达人名单 + 外联模板
tests/                    # T1–T4/T6 验收测试
```
