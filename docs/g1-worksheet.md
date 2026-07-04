# G1 工作底稿：eBay AU sold 数据验证 + IP 排雷

> 对应 PROJECT_PLAN §4.3 / §11「立即下一步」。人工执行，约 30 分钟。
> 结果回填本文件后提交，并同步更新 PROJECT_PLAN §4.3 的 checkbox。

## A. eBay AU 成交数据验证（每个关键词 ~5 分钟）

操作步骤（桌面浏览器）：

1. 打开 ebay.com.au，搜索关键词
2. 左侧筛选栏勾选 **Show only → Sold items**（如无此项，先勾 Completed items 再勾 Sold）
3. 排序改为 **Ended recently**
4. 记录总结果页数（每页 60 条）→ 近 90 天成交条数 ≈ 页数 × 60
5. 抽看前 3 页：记录 A$40–60 价格带是否有真实成交（注意区分 A$15 以下垃圾档）
6. 记录头部卖家（成交最多的 2–3 家）的月销估算：其近 30 天 sold 数

### 填写区

| # | 关键词 | 总成交条数(90d) | 估算月销 | A$40–60 带有成交? | 头部竞品月销 | 备注 |
|---|---|---|---|---|---|---|
| 1 | hilux seat organiser | | | | | |
| 2 | molle panel hilux | | | | | |
| 3 | ranger seat organiser | | | | | |
| 4 | squid jig set | | | | | |
| 5 | squid jig kit | | | | | |

第二梯队关键词（G1 不达标时重跑）：awning organiser / rod holder storage / 4wd canvas storage

## B. IP Australia 外观设计排雷（每 SKU 上架前必查）

1. 打开 IP Australia → Australian Design Search（designs.ipaustralia.gov.au）
2. 逐个检索关键词，看已注册外观是否与我方产品形态实质近似

| # | 关键词 | 命中数 | 有实质近似? | 风险判断 | 备注 |
|---|---|---|---|---|---|
| 1 | seat organiser | | | | |
| 2 | seat storage vehicle | | | | |
| 3 | squid jig | | | | |
| 4 | lure case / tackle wallet | | | | |

## C. G1 判定

**通过线（两条同时满足）**：
- [ ] 目标关键词头部竞品月销 > 100 件
- [ ] A$40–60 价格带有真实成交（而非只有 A$15 垃圾档在动）

**成本模型侧（已由 T1 计算器验证 ✅）**：SKU-A 毛利 63.8%、SKU-B 62.1%，均 ≥55% 红线。
第三个 SKU 落地成本模型待补（G1 要求 ≥3 个 SKU 过线）——把候选 SKU 参数加进
`config/economics.yaml` 跑 `python3 tools/cost_calculator.py` 即得。

**判定结果**（填写）：
- G1 状态：☐ 开闸 / ☐ 不达标 → 换第二梯队关键词重跑
- 判定日期：
- 决策备注：

---

## D. 网络情报补充（2026-07-04，Claude 代查）

> ⚠ **非 G1 依据**。以下来自网页搜索，不是 sold 数据——按计划 §6 卡点纪律
> 「不得用搜索热度代替成交数据」，A/B 两节仍须人工在 eBay/IP Australia 完成。
> （已尝试自动化访问 eBay AU 与 IP Australia：被执行环境网络策略拦截，无法代查。）

**4WD 软装侧：**
- eBay AU 存在通用款 Hilux 座椅收纳在售，约 A$33、显示 15 sold —— 印证低价通用档有动销
- MSA 4X4（本土高端软装品牌，A$100+ 档）有 seat organiser 产品线 —— 印证「Kings 之上」档位存在且有品牌占位；我方 A$49.95 卡位仍在两者之间的空档
- MOLLE panel 类目在售价带宽 A$10–146 —— 与「金属五金层」差异化定位兼容

**木虾侧（对计划 §4.2 竞争事实的更新）：**
- Rui 单只价已上移：官方渠道约 A$24.99/只，Anaconda 零售 A$14.99/只（3 只 A$36 会员价）
  —— 计划里记录的 A$11.99 已过时，**中间档价格上移对 SKU-B A$39.95 套装更有利**
- Rui 官方 10 只装促销 A$109.90（合 ~A$11/只）—— 系统套装（5 只+wallet A$39.95）
  仍避开其单只/多只战场，wallet 与校准沉速差异化不变

来源：ebay.com.au 商品页、eging.com.au、anacondastores.com（经搜索引擎摘要，未逐页核验）
