# T9 达人外联：邮件模板 + 跟进规则

> 对应 PROJECT_PLAN §6 D31–60（30 个创作者寄样，回复率按 20% 预期 → 预计 6 个上线）。
> 名单记录在 `creators.csv`，status 取值：`待联系 / 已联系 / 已回复 / 寄样中 / 内容已上线 / 婉拒 / 失联`。

## 选人标准

- 4WD 线：YouTube 中腰部（1–10 万订阅）优先——头部要价高、尾部没水花；视频里出现 Hilux/Ranger 的加分
- 钓鱼线：FB 群活跃版主 + Instagram egi/squid 标签高频发帖者；地域偏 QLD/VIC/SA 沿海
- 排除：纯折扣号、无真实出镜、评论区死寂的

## 首封邮件（YouTube / 邮箱）

Subject: **Free {product} for your {truck model} — no strings, keep it either way**

> G'day {name},
>
> I run a small AU store making {one-line product}. Watched your {specific video title} — the bit about {specific detail} is exactly the problem we built this for.
>
> I'd love to send you one, free, no obligations: if you rate it, a mention or honest review would be brilliant; if you don't, bin it or give it to a mate and no hard feelings. Not asking for a script — honest opinion only, good or bad.
>
> One detail you might appreciate: {SKU-A: all-metal hardware, no plastic clips — we built it after reading a few hundred reviews of the big brands' broken buckles / SKU-B: every batch is tank-tested and the actual sink rate is printed on the pack}.
>
> If you're keen, just reply with a postal address. Cheers,
> {your name} — {store name}

## Instagram/FB DM 版（≤500 字符）

> G'day {name}! Small AU brand here — we make {product one-liner}. Loved your {recent post}. Keen to send you one free, zero strings: like it → a mention's appreciated; don't → no worries at all. Honest takes only. DM me a postal address if interested. Cheers!

## 跟进节奏

| 时点 | 动作 |
|---|---|
| D0 | 首封发出，`creators.csv` status → 已联系 |
| D7 | 无回复 → 跟进一句话（"Bumping this in case it got buried — offer stands!"）|
| D14 | 仍无回复 → status → 失联，不再打扰 |
| 回复后 24h 内 | 寄样 + 填 tracking_no，status → 寄样中 |
| 签收后 D10 | 轻提醒一次（只提醒一次）："Hope it arrived safe! No rush — curious what you reckon when you've had a run with it." |
| 内容上线 | 填 content_url/date，status → 内容已上线；评论区互动 + 求授权二次使用素材 |

## 红线

- 不付费买「好评脚本」；只送样求 honest review（合规 + 可信度）
- 同一创作者两条产品线间隔 ≥30 天再谈第二次寄样
- 所有寄样含手写感谢卡 + 一页产品故事（差评痛点→我们的对策）
