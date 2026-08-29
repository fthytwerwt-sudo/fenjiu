# Dual Business Line Stage Gate Matrix｜汾酒与海鲜双业务线阶段闸门

> **用途：** 一页判断两条线“现在在哪、只做什么、不做什么、谁提供输入、何时才解锁下一步”。
> **总规则：** 每条线每个阶段只赢一个主要结果。阶段完成、文件存在、AI 生成、播放量或 Git 成功都不是业务完成。

## 1. 当前定位

| 业务线 | Current stage | Why | 今天只做 | 需要谁提供什么 | Current blocked | Next unlock |
|---|---|---|---|---|---|---|
| `fenjiu_nepal` | `FJ-1 Sellable Offer Ready` | 20 年/30 年仅有产品线名与公开研究候选；本地具体 SKU、价格、库存、许可、账号、收款与履约未获当前书面证据。 | 锁定一个实物 SKU 的 Offer 证据包、禁止表达与人工 owner。 | 供应链：实际 SKU/标签/图片权利、价格/有效期、库存、授权/许可、账号、收款、仓配/售后。 | 公开内容、广告、报价、交易、订单、履约。 | 所有业务闸门 `READY` 且用户具体授权后，FJ-2。 |
| `seafood_nepal` | `Supplier SF-S1` 与 `User SF-U1` 并行 | 供应链正在推进本地准备但未证明 READY；用户职责已修正为 Online Acquisition，不承担当地报价/样品/成交/履约。 | 供应链补本地 business gates；用户把 1 个 SKU 转成 Online Offer Pack。 | 供应链：商品/食品/冷链/销售/履约；用户：pack 缺口、ICP/Route 内部准备。 | 真实发现、联系、发布、广告、报价、订单、履约。 | `ONLINE_ACQUISITION_READY` Product Pack 后，用户进入 SF-U2；供应链继续 SF-S1。 |

## 2. Fenjiu Stage Gates

| Stage | 主要目标 | 只做什么 | NOT NOW | Output / Funnel / Decision | Stop line | Next unlock |
|---|---|---|---|---|---|---|
| FJ-0 | 战略重置 | 固定 Sales-First、角色、指标、停止线 | 不开发系统/多平台 | 文档一致 / 无 / `planning_ready` | 事实源冲突 | FJ-1 |
| FJ-1 | 一个可审计 Offer | 收集 SKU、价格、库存、合规、履约证据 | 不拍销售承诺、不发布/报价 | READY 字段数 / 无 / `business_ready?` | 任一关键字段未知 | FJ-2 |
| FJ-2 | 一个人工销售闭环 | 一个 Offer、入口、owner、CTA、事实复核 | 不多平台/自动回复/付款 API | 已记录互动 / inquiry→conversation / `manual loop viable?` | 事实/授权/owner 失效 | FJ-3、FJ-5 |
| FJ-3 | 验证一个渠道 | 只改变一个内容/受众/CTA 变量 | 不扩渠道/买量 | 可归因发布 / qualified inquiry / Keep-Improve-Stop | 无合格询盘或归因缺失 | FJ-4 |
| FJ-4 | 内容到询盘学习 | 对比一个内容变量 | 不建视频工厂 | 有内容记录 / conversation / 哪类内容继续 | 只有虚荣指标 | FJ-7、FJ-8 |
| FJ-5 | 人工跟进稳定 | stage、owner、next action、DNC | 不接复杂 CRM | 到期动作 / missed follow-up / 是否工程化 | 无真实负担/无依据 | FJ-6、FJ-8 |
| FJ-6 | B2B 精准试点 | 小样本、公司核验、单次批准接触 | 不抓取/猜邮箱/批量外联 | 公司审核 / qualified conversation / B2B 是否有价值 | 来源/处理依据/Offer 缺失 | FJ-7、FJ-8 |
| FJ-7 | 第二渠道增量 | 仅启用一个第二渠道 | 不全平台铺开 | 增量触点 / 增量合格询盘 / 是否继续 | 无增量/政策不明 | FJ-9 |
| FJ-8 | AI 辅助净收益 | 一个有 baseline 的重复任务 | 不自动销售/报价/发送 | 人工分钟数 / 质量/漏项 / Keep-Improve-Stop | 无净收益/风险升高 | FJ-9 |
| FJ-9 | 稳定规模化 | 扩一个已证实变量 | 不让规模掩盖履约问题 | 稳定 SOP / order-handoff / scale decision | 合规、质量、履约失稳 | 重新回对应阶段 |

## 3. Seafood Dual Workstream Stage Gates

### Supplier Workstream

| Stage | 主要目标 | 供应链动作 | 用户动作 | Stop line | Output |
|---|---|---|---|---|---|
| SF-S1 | 商品、食品/进口、价格/库存、冷链与当地销售/履约准备 | 提供当前书面事实、当地 owner；负责报价、样品、谈判、收款、订单、配送、售后和结果反馈 | 只检查 Online Offer Pack 与 Lead 接收/反馈接口，不代执行本地动作 | 任一事实缺失、冲突、过期；“正在做”不能标 READY | Online Offer Pack inputs + supplier owner + outcome feedback |

### User Online Acquisition Workstream

| Stage | 主要目标 | 只做什么 | NOT NOW | Output / Funnel / Decision | Stop line | Next unlock |
|---|---|---|---|---|---|---|
| SF-U0 | 职责和接口清楚 | 固定 User Acquisition / Supplier Local Sales | 不获客/开发/发布 | role doc / 无 / boundary clear | 仍把本地销售交给用户 | SF-U1 |
| SF-U1 | 1 个 Online Offer Pack | 检查 1 SKU 的事实、素材权、接受状态和 supplier owner | 不要求 20 SKU、不找客户 | ready pack / 无 / safe for lead gen? | 身份/规格/权利/owner/询盘接受缺失 | SF-U2 |
| SF-U2 | 1 Product + 1 ICP + 1 Region + 1 Route | 锁 First ICP、Primary/Fallback、sample/window/cost | 不多 ICP/多 Route | test brief / 无 / authorizable? | 无 supplier owner 或 Route 边界 | SF-U3 |
| SF-U3 | First Route 产生可判定基线；获授权后产生 Qualified Lead | Search/Web 单路线内部基线；获授权后人工联系 | 不并行内容/Ads/自动发送 | verified/qualified accounts / qualified lead / Route K-I-S | 来源/处理/DNC/授权缺失或样本不匹配 | 未授权：留在 SF-U3 waiting_authorization；已授权且 ≥1 Qualified Lead：SF-U4 |
| SF-U4 | Qualified Lead 稳定交接 | qualification、handoff、Supplier Accept | 用户不报价/样品/谈判 | handoff/ack / supplier accepted / stable? | 无 owner、ACK、basis 或隐私边界 | SF-U5 |
| SF-U5 | 获客连接销售结果 | 关联 accepted/offered/won/lost/fulfilled 和成本 | 不用 views/公司数代替价值 | attribution / offer/order outcome / best ICP+Route | feedback incomplete | SF-U6 / SF-U7 |
| SF-U6 | 第二 Route 增量 | 只增加 Content 或另一个 Route | 不全平台并发 | independent route / incremental accepted leads / K-I-S | 无增量、无法归因、supplier capacity 不稳 | SF-U7 / SF-U8 |
| SF-U7 | AI 对一个瓶颈有净收益 | 一个任务 before/after + 人工审核 | 不自动联系/报价/库存 | time/review / quality / AI K-I-S | 错误升高或无净收益 | SF-U8 |
| SF-U8 | 稳定流程自动化与扩张 | 自动化一个低风险步骤，保留回退 | 不全自动获客/销售 | automation / accepted outcome / scale/rollback | ICP/Offer/handoff/feedback 任一不稳 | 回对应阶段 |

## 4. Channel Expansion Contract

新的渠道只有满足下列至少一项理由并通过前一渠道完整周期后才可进入：

1. 当前渠道已证实有效，新增渠道解决清晰的覆盖缺口。
2. 当前渠道无法覆盖一个已定义的新客群，且新渠道能被单独归因。
3. 当前渠道被明确 Stop，需要以更低成本测试一个替代假设。
4. 人工销售闭环已经稳定，新增变量不会破坏归因或履约。

每次扩展必须写：`existing channel result`、`new audience`、`one hypothesis`、`entry condition`、`measurement window`、`Stop line`、`owner`、`authorization ref`。如果只因为“平台存在/别人也在用”，结论为 `DEFER`。

## 5. AI / CRM / Automation Gate

`Manual → measure → find bottleneck → AI assist → compare → Keep/Improve/Stop → automation`

| 能力 | 最早可评估 | 必须已有的人工事实 | 不满足时 |
|---|---|---|---|
| AI scripts / visuals | FJ-3 或 SF-U7 | 人工脚本时间、QC 通过/修改率与下游 Lead 数据 | 只作内部草稿；不扩模型/预算。 |
| AI reply | FJ-5 或 SF-U7 | 合法真实 Lead、人工首响/采纳率、DNC/升级规则 | `DEFER`，不自动答复。 |
| CRM | FJ-5 或 SF-U5 | 多次需跟进 Lead、owner、next action、处理依据 | 使用最小人工记录。 |
| AI research | FJ-6 或 SF-U7 | 已批准来源、人工研究时间、qualified-account/lead 率 | 不抓取联系人、不建真实联系人库。 |
| Automation | FJ-9 或 SF-U8 | 稳定 ICP/Offer/Route/handoff/feedback、异常回退、净收益 | 保持人工。 |
