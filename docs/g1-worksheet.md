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
