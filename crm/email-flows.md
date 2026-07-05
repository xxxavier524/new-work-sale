# 复购邮件流（T6 配套 / PROJECT_PLAN §6 D61–90「邮件流复购」）

> 渔具是消耗品逻辑（木虾会挂底丢失、会被咬坏）→ 复购主战场在 SKU-B；
> SKU-A 走「同人群第二类目」交叉销售。触发以发货/签收日为锚。
> 渠道注意：eBay 站内消息不允许导流外部；本邮件流用于 Shopify 独立站订单
> 与已订阅买家。eBay 订单只能用合规的订单消息（模板 1 的站内版）。

## Flow 1｜签收 +2 天：使用 tips（不卖货，建信任）

Subject: **Get the most out of your {product} — 60-second setup**

> G'day {name},
>
> Your {product} should be with you now — here's the 60-second version of getting it right:
>
> {SKU-B: Start with the 2.5 at your local jetty an hour either side of tide change. Count the sink — the rate printed on your pack is measured, not marketing. Slow two-lift, long pause. After the session: fresh-water rinse, jigs into the drain wallet, leave it open overnight.}
> {SKU-A: Mount the panel before you load the pockets — straps cinch easier empty. Heavy stuff low, grab-first stuff (med kit, gloves) at the top.}
>
> Any issue at all — a clip, a crown, anything — reply to this email and a replacement ships within 24h. You keep the original. That's the policy.
>
> Tight lines / happy touring,
> {store name}

## Flow 2｜签收 +30 天：复购提醒（SKU-B 主打）

Subject: **Down a jig or two yet?**

> G'day {name},
>
> A month of squidding usually costs a jig or two — snags happen to everyone.
>
> Restock singles in your proven size, or grab a second kit so the wallet's never empty: {restock_link}. Returning customers get {10}% off with code **BACKAGAIN** — works store-wide, including the seat organiser your 4WD's been eyeing: {cross_sell_link}.
>
> New colours drop as batches pass tank-testing — sink rates printed as always.
>
> {store name}

## Flow 3｜签收 +45 天：评价请求（只发给无客诉记录的订单）

Subject: **One line from you = a lot for a small store**

> G'day {name},
>
> If the {product} has earned its keep, a short honest review helps other {squidders/tourers} skip the junk tier we built this against: {review_link}.
>
> If it *hasn't* earned its keep — reply to this email instead and I'll fix it first. Replacement or refund, no return postage.
>
> Cheers,
> {store name}

## 执行规则

| 规则 | 说明 |
|---|---|
| 客诉在途不触发 | 有未关闭工单的订单跳过 Flow 2/3（先解决再营销）|
| Flow 3 分流 | 差体验流量导向客服而非评价页（差评拦截）|
| 频控 | 任意 30 天内最多 2 封营销邮件；退订链接必带（Spam Act 2003 合规）|
| 数据回流 | 邮件带 UTM，转化记入周报 CSV 的 channel 列 |
