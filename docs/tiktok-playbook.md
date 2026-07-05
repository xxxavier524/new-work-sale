# 营销模块 M1：TikTok 全 AI 内容工作流作战手册

> 调研日期：2026-07-05。定位：主计划 §6 D31–60 冷启动的**自有内容渠道**，与达人寄样（T9）并行。
> MVP 目标：**净利润 $200**（≈¥1,440 ≈ 混合 18–20 单），嵌套在 G3「30 天 ≥30 单」之内——
> TikTok 贡献 20 单，两个目标同时达成。原则：低启动成本（月增量预算 <¥300）、先跑通再优化。

## 0. 调研结论（架构依据，来源见文末）

| 事实 | 对策 |
|---|---|
| **TikTok Shop 未开澳洲**，官方明确短期不开 | 漏斗只能走：自然流量 → 主页 bio 链接 → eBay listing / Shopify 页（T4 已建）。零平台入驻成本，反而契合 MVP |
| TikTok 2026 AIGC 政策：真实感 AI 画面必须开 AIGC 标签；**商品展示不得 AI 捏造**；禁 AI 人脸/人声假背书；AI 写脚本豁免 | AI 只做场景/情绪/失败演示 B-roll；产品本体一律样品实拍；不做 AI 数字人口播 |
| Seedance 成本：即梦年费会员 ≈¥4.6/条 15s；火山 API ≈¥15/条；Atlas $0.022/s | MVP 用**即梦会员**批量生成；跑通后需要 API 自动化再上火山 |
| 归因：bio 链接跳 eBay 后链路断裂 | 折扣码 TIKTOK10 归因（下限口径）+ 评论区/私信问询计数（辅助）|

## 1. 方法论（饼干哥哥式全 AI 工作流的本地化）

参考其公开方法论核心：**选题库 → 爆款结构模板 → AI 批量生成 → 发布 → 数据回流选题**。
本仓库的实现比通用教程多一层护城河：**选题库不是抓热点，而是 T2 差评挖掘的痛点档案**——
每个钩子溯源到真实差评（C1 塑料扣、J1 锈、J2 沉姿……），内容天然带转化意图，
而不是泛流量。对应关系：

```
data/painpoints.yaml（选题库）
   → config/tiktok.yaml（钩子库/结构模板/Seedance 提示词库）
      → tools/tiktok_pipeline.py brief（批量出简报：脚本+分镜+提示词+文案）
         → 即梦生成 B-roll + 实拍位插入 → 剪映合成 → 发布
            → tools/tiktok_pipeline.py report（数据回流 → 支柱加减产）
```

## 2. 账号与漏斗

- **账号**：新号，人设「中国工厂直连澳洲玩家的小店主理人」不出镜（免 AI 人脸问题），
  简介：AU stock · metal hardware · tank-tested jigs · ships 7–15 days。
- **发布环境 ⚠**：TikTok 在中国大陆不可用。需要海外网络环境 + 海外 Apple ID/Google 账号，
  且**账号注册地/代理 IP 决定初始流量池**——必须稳定澳洲 IP 或至少英语区环境，
  频繁切换 IP 会限流。这是整个模块最大的运营卡点（见 §7 人工清单）。
- **漏斗**：视频 → bio 链接（先 eBay listing，Shopify 页作备用）→ 下单。
  折扣码 TIKTOK10（10% off，已计入归因利润口径）。
- **发布节奏**：日更 1 条，澳东 18:30（悉尼下班刷手机窗口）；周产 7 条 ≈ 成本 ¥32。

## 3. 内容体系（详见 config/tiktok.yaml）

4 支柱 × 3 结构 × 10 钩子轮换，pipeline 确定性生成不撞车：

| 支柱 | 内容 | 赌的是什么 |
|---|---|---|
| P1 pain-demo | 竞品失败画面（塑料扣断裂慢镜头）→ 金属对策 | 差评共鸣 = 最强转化钩子 |
| P2 satisfying-rig | MOLLE 上装/收纳 ASMR | organization 品类天然流量池 |
| P3 squid-science | 沉速/沉姿科普（为什么便宜木虾钓不到）| 「涨知识」分享率高，且直击 J2 差异化 |
| P4 session-story | 夜钓叙事/出车故事 | 情绪与人设，养号用 |

**每条视频的固定纪律**（pipeline 已内置在发布检查清单）：
1. AI 画面 → AIGC 标签必开；2. 产品特写必是实拍位；3. 带折扣码 → 商业披露必开；
4. 只用 listings.yaml 溯源过的卖点，禁 waterproof、禁渔获承诺。

## 4. $200 经济账（MVP 口径）

| 项 | 数值 |
|---|---|
| 归因单利润（折扣码后）| SKU-A ¥81.7/单 ≈ $11.3；SKU-B ¥42.0/单 ≈ $5.8 |
| **达标所需订单** | 纯 A：18 单｜纯 B：35 单｜**混合（A:B=1:1）：约 24 单** |
| 内容成本（30 天日更）| 30 × ¥4.6 ≈ ¥138 ≈ $19 |
| 其他增量成本 | $0（剪映免费、发布免费、bio 链接免费）|
| 转化假设校验 | 需 bio 点击→下单转化 3% 时，24 单 ≈ 800 次点击 ≈ 播放 8 万（CTR 1%）——30 条日更下即人均 2,700 播放/条，中位数可达 |

**结论：目标不需要爆款**。30 条里只要 2–3 条进 5 万+ 流量池，剩下的稳定长尾即可。
若 30 天后 <$100：转化问题（换钩子/换 CTA）；若播放长期 <500/条：账号环境或垂类标签问题（先修账号再谈内容）。

## 5. 30 天 MVP 冲刺（与主计划 D31–60 对齐）

| 周 | 动作 | 产出/判定 |
|---|---|---|
| W0（样品到手前）| 注册养号：每天刷 30min 目标垂类+点赞评论（喂标签）；跑 `brief --count 7` 生成首批简报；即梦把 AI B-roll 全部生成入库 | 账号有 50+ 垂类互动；素材库 20+ 条 B-roll |
| W1 | 样品到手 → **1 天拍完 real_footage_checklist 全部 7 组实拍**；剪映合成，日更开始 | 7 条上线；观察初始流量池（>500 播放/条 = 账号正常）|
| W2 | 日更继续；评论区全回（养权重）；'RIG' 评论钩子开始收私信名单 | 14 条累计；首单出现 → 折扣码归因验证跑通 |
| W3 | 跑 `report`；按支柱建议加减产（杀停规则：6 条后互动 <2% 且 0 单）| 数据驱动的第一次调整 |
| W4 | 复制赢家：最佳钩子做 3 变体；最佳视频投 $30 Promote 测付费放大（可选，预算内）| 30 天复盘：$ 进度 / 杀停 / 放大决策 |

## 6. 风险与诚实条款

- **账号被限流/封禁**（新号+代理环境是高危组合）：备用号同步养；素材库与简报可复用，损失仅账号权重
- **AI 素材同质化**：即梦提示词库每 2 周换血一次（把表现最差的 shot 换成新场景）
- **视频火了但没货**（G2 延迟）：置顶评论改「link waitlist」，把流量存进私信名单——流量不等库存
- **模块失效条款**：60 天 0 单且 CTR 持续 <0.5% → 停更，预算转投达人寄样（T9 渠道优先级更高）

## 7. 与主计划的资源边界

本模块**不动用**主预算表（§7）的任何一项；增量成本 = 即梦会员 ¥79/月 + 可选 Promote $30，
全部计入「达人寄样 + 小额投流 ¥8,000」池内，占用 <5%。周投入 ≈3h（拍摄一次性 4h 另计），
在 12h/周约束内与主线并行成立。

## 信息来源

- TikTok Shop 澳洲未开：[contentgrip](https://www.contentgrip.com/tiktok-shop-australia-delay/)、[marketing-interactive](https://www.marketing-interactive.com/tiktok-shop-is-booming-globally-so-why-is-australia-still-waiting)
- AIGC 政策：[TikTok Newsroom](https://newsroom.tiktok.com/en-us/new-labels-for-disclosing-ai-generated-content)、[TikTok Seller University](https://seller-us.tiktok.com/university/essay?knowledge_id=491489038501663)、[auditsocials 2026 解读](https://www.auditsocials.com/blog/tiktok-ai-content-disclosure-rules-2026)
- Seedance 价格：[火山引擎](https://www.volcengine.com/article/42193)、[实在智能对比](https://www.ai-indeed.com/encyclopedia/20215.html)、[Atlas Cloud](https://www.atlascloud.ai/blog/case-studies/seedance-2.0-pricing-full-cost-breakdown-2026)
- 全 AI 内容工作流生态：[awesome-ai-media-cn](https://github.com/JuneYaooo/awesome-ai-media-cn)（150+ 开源工具索引）
