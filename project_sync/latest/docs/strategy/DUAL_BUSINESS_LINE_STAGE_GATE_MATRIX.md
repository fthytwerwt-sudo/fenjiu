# Dual Business Line Stage Gate Matrix｜汾酒与海鲜双业务线阶段闸门

> **用途：** 一页判断两条线“现在在哪、只做什么、不做什么、谁提供输入、何时才解锁下一步”。
> **总规则：** 每条线每个阶段只赢一个主要结果。阶段完成、文件存在、AI 生成、播放量或 Git 成功都不是业务完成。

## 1. 当前定位

| 业务线 | Current stage | Why | 今天只做 | 需要谁提供什么 | Current blocked | Next unlock |
|---|---|---|---|---|---|---|
| `fenjiu_nepal` | `FJ-1 Sellable Offer Ready` | 20 年/30 年仅有产品线名与公开研究候选；本地具体 SKU、价格、库存、许可、账号、收款与履约未获当前书面证据。 | 锁定一个实物 SKU 的 Offer 证据包、禁止表达与人工 owner。 | 供应链：实际 SKU/标签/图片权利、价格/有效期、库存、授权/许可、账号、收款、仓配/售后。 | 公开内容、广告、报价、交易、订单、履约。 | 所有业务闸门 `READY` 且用户具体授权后，FJ-2。 |
| `seafood_nepal` | `SF-1 Seafood Offer & Cold-Chain Ready` | 第一批次货品单只证明产品候选/表内数量重量，食品、冷链、价格、库存和履约未获证据。 | 为一个 `SM-*` 候选 SKU 锁定产品/标签/批次、冷链、食品、商业与履约资料。 | 供应链：产品规格/标签/过敏原/批次、库存/价格/MOQ、食品/进口、温控/配送、支付/售后。 | 报价、样品、接单、配送、B2B/B2C 发布。 | 一个 SKU 的全证据 Offer 后，SF-2 B2B 人工采购闭环。 |

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

## 3. Seafood Stage Gates

| Stage | 主要目标 | 只做什么 | NOT NOW | Output / Funnel / Decision | Stop line | Next unlock |
|---|---|---|---|---|---|---|
| SF-0 | 路线隔离 | 确定 B2B-first、B2C-second | 不两线同时启动 | 决策记录 / 无 / 选择可验证路线 | 业务线混淆 | SF-1 |
| SF-1 | 一个食品/冷链 Offer | 一个 SKU 的标签、批次、食品、冷链、价格、履约证据 | 不报价/样品/配送/发布 | READY 字段 / 无 / `food-cold-chain-ready?` | 任一食品/冷链事实缺失 | SF-2 |
| SF-2 | B2B 手工采购闭环 | 一个客户类型、一个产品、一个 owner、一个采购路径 | 不批量 B2B/B2C | 有效采购记录 / qualified procurement conversation / 是否存在采购匹配 | 冷链/食品/授权失效 | SF-3、SF-5 |
| SF-3 | B2B 渠道验证 | 一个来源或信任触点 | 不增加来源/消费者投放 | 已记录触点 / 采购对话 / Keep-Improve-Stop | 无合格对话/数据依据不全 | SF-4 |
| SF-4 | 规格内容学习 | 测一个规格/菜单/收货变量 | 不把知识内容当供货证据 | 内容卡 / B2B inquiry / 哪种信息促进对话 | 只有观看无对话 | SF-6、SF-7、SF-8 |
| SF-5 | B2B 跟进稳定 | owner、next action、样品/报价前核验 | 不接复杂 CRM | 已跟进动作 / stage aging / 是否需工具 | 无真实负担 | SF-6、SF-8 |
| SF-6 | B2C 最小履约闭环 | 一个零售 SKU、一个渠道、一个入口 | 不同时扩 B2B 和 B2C | 已批准产品资料 / qualified household inquiry / 是否安全履约 | 温控、投诉、支付、配送失效 | SF-7 |
| SF-7 | 增量渠道/客群 | 一个第二渠道或第二段 | 不多个平台并发 | 独立内容/渠道记录 / 增量询盘 / 是否继续 | 无增量或交接压力 | SF-9 |
| SF-8 | AI 净收益 | 一个已测量的重复人工任务 | 不自动作食品/商业判断 | 节省时间 / QC / 是否保留 | 无净收益/事实风险 | SF-9 |
| SF-9 | 稳定规模化 | 扩一 SKU/区域/渠道 | 不越过食品/冷链能力 | 稳定事实与 SOP / 履约/复购 / scale decision | 质量/食品/冷链异常 | 回 SF-1 或对应阶段 |

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
| AI scripts / visuals | FJ-3 或 SF-3 | 人工脚本时间、QC 通过/修改率与下游内容数据 | 只作内部草稿；不扩模型/预算。 |
| AI reply | FJ-5 / SF-5 | 合法真实询盘、人工首响/采纳率、DNC/升级规则 | `DEFER`，不自动答复。 |
| CRM | FJ-5 / SF-5 | 多次需跟进客户、owner、next action、处理依据 | 使用最小人工表。 |
| AI research | FJ-6 / SF-3 | 已批准来源、人工研究时间、有效公司率 | 不抓取、不建真实联系人库。 |
| Automation | FJ-9 / SF-9 | 稳定流程、异常回退、清晰净收益、安全审核 | 保持人工。 |
