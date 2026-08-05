# 客服 AI、会话状态与人工接管计划

> **状态：PLANNED / draft-only。** Phase 6 不接生产 WhatsApp、TikTok、Meta 或邮箱账号；将来接入也必须遵守 approved truth、人工接管和渠道授权。

## 1. 标准流程

```text
消息进入 → scope/客户识别 → 幂等与敏感分类 → intent/risk → 查询 approved truth
→ 生成草稿 → 事实/合规检查 → draft-only 或人工审批 → 人工接管
→ conversation/message/result/feedback/audit 入库
```

消息 adapter 首先验证签名（未来）、external message ID、scope 映射与 DNC/consent；未知 scope 隔离并报警。`conversation`、`message` 是不可变记录；AI 的 intent、译文、摘要、reply 均为版本化 candidate/draft。

## 2. 答复 policy

| 情况 | 系统结论 |
|---|---|
| approved、未过期的规格/一般 FAQ，且 channel/intent 在低风险白名单 | 可生成 `draft_reply`，默认仍需人工审核。 |
| 价格/有效期、库存更新时间、配送范围/时效、订单状态 | 只在具体 approved fact 存在、freshness 通过时生成草稿；否则转人工。 |
| 酒类购买/年龄、报价、退款、投诉、质量、账期、独家、支付、订单、法律/资质、个人数据、大额询盘 | 强制 `handoff_case`；不产生可发送承诺。 |
| 无 approved truth、事实 expired/conflict/blocked、模型低置信、禁语命中 | 回复“需要确认”的人工队列信息；禁止猜测。 |

多语言必须同时保留原文、译文、locale、translation/model version 和批准版本；事实引用以 approved fact version IDs 而非聊天记忆或上传文件全文表示。事实/政策更新后，未发送草稿自动 `superseded`。

## 3. 人工接管与数据回流

人工接管暂停该 conversation 的任何自动化，直到明确恢复并审计。处理结果包括 `resolved/needs_supplier_confirmation/complaint/escalated/no_reply`，不会自动更新产品/价格/库存真值。真实对话数据到达后，Codex 的周期任务只能在受控导出上做：PII 最小化/脱敏、意图混淆矩阵、未答问题聚类、FAQ candidate、policy regression fixtures；FAQ 的每次更新仍走 source/version/approval。不得把私人聊天直接训练、导出或填入 Git。

## 4. Chatwoot 的位置

Chatwoot 可在真实咨询量、渠道权限、PII 留存与人工工作台需求均出现后作为 `support_inbox_adapter` 评估。先完成 fake webhook、message replay、DNC、handoff、export、关闭 adapter 的 contract；只同步必要 conversation metadata 和经批准草稿，不让 Chatwoot 的 automation 直接查询未批准资料、发送高风险答复或成为 source of truth。
