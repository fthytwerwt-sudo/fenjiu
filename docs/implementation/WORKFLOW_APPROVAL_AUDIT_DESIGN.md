# 工作流、人工闸门、权限、审计与可观察性设计

> **状态：PLANNED。** Phase 4 先建立统一控制面，再允许 Leads、客服或视频模块运行。LangGraph 是可选的 workflow adapter，不是业务状态或审批真值。

## 1. workflow state machine

```text
created → validated → queued → running → waiting_for_approval
  ├─ approve → executing → succeeded
  ├─ reject  → rejected
  ├─ revise  → created (new revision)
  ├─ timeout → expired
  └─ error   → retry_scheduled → running | dead_lettered
```

每个 run 的必填字段：`workflow_run_id`、scope、`correlation_id`、command type、input hash、policy version、idempotency key、attempt、checkpoint ref、actor、created/updated time 和 terminal result。checkpoint 只保存恢复所需状态，业务事实与 audit 仍写 PostgreSQL。外部副作用前后均须有 deterministic idempotency key；resume 不能再发送/再提交/再创建事实。

## 2. 动作等级与 feature flags

| 等级 | 示例 | 系统行为 | 默认 |
|---|---|---|---|
| `automatic_internal` | hash、OCR、normalization、fixture 测试、草稿建议 | 可自动运行，仍记录 audit 和失败。 | enabled only in local/test |
| `human_approval_required` | publishing truth、CRM merge、内容/视频成本调用、低风险回复草稿应用 | 创建 `approval_request`；批准后仍检查 flag、scope、最新事实。 | enabled for request, not execution |
| `forbidden` | 自动公开发布、自动外联、正式报价、退款、下单、支付、库存写回 | policy 硬拒绝并审计；无执行 adapter。 | disabled |

flags 至少包含：`external_send_enabled`、`content_publish_enabled`、`price_quote_enabled`、`refund_enabled`、`order_enabled`、`payment_enabled`、`inventory_write_enabled`、`real_crawl_enabled`、`real_video_provider_enabled`。所有值默认 `false`，且 fixture 永远不能覆盖。

## 3. RBAC 与 action policy

| 角色 | 可做 | 不能做 |
|---|---|---|
| `system_worker` | 处理允许的内动作、写 run/audit | 批准、跨 scope、直接外发。 |
| `data_reviewer` | 修改 mapping、批准/拒绝 data candidate | 批准自己的高风险生成结果或改 audit。 |
| `content_reviewer` | 审批内容/视频内部导出 | 改价格/库存/合规真值。 |
| `support_agent` | 人工接管、编辑/批准回复草稿 | 自行解除 policy/feature flag。 |
| `project_owner` | 授权 scope、配置安全 flags、最终内部 run-ready 签收 | 不能把外部合规证据缺口自动视为解除。 |
| `auditor` | 只读 audit/export | 编辑业务记录或删除日志。 |

`ActionPolicy.evaluate()` 必须同时检查 actor role、scope、data state、approval state、fact freshness、DNC/consent、flag、environment 与 required evidence。任何不满足返回稳定错误码与 `audit_event`。审批者不能批准自己的高风险 action；所有决定产生 append-only `approval_decision`。

## 4. 重试、超时、死信与告警

- 可安全重试：提取、normalization、snapshot fetch、内部 QC；限定 attempt、指数退避、总时间与 state checksum。
- 需 approval 才能重试：产生费用的视频 provider、外部同步、任何可能触达第三方的 adapter。
- 禁止自动重试：发送、发布、报价、支付、退款、下单、库存回写；必须人工创建新 command。
- timeout 将 run 标为 `expired` 或 `dead_lettered`，保留 payload hash、错误码和 checkpoint；不丢弃审计。
- metrics 合同：queue depth、retry/DLQ count、pending/expired approvals、policy denials、data state distribution、adapter latency/error、model tokens/cost/result category。告警阈值由运行环境配置，但指标名和 correlation link 在 Phase 4 固定。

## 5. 审计与日志

`audit_event` 是 append-only：`sequence`、时间、actor、scope、command、target ref、before/after version hash、policy result、approval ref、correlation id、external reference hash、error code。普通日志仅写结构化 metadata；不得写 API key、Cookie、Token、完整私人消息、原文件正文、敏感附件或本机绝对路径。

模型调用额外记录：provider/model alias（不含 key）、prompt/template version、approved fact version set、output class、token/cost bucket、latency、safety/policy outcome。对话/资料全文采用 reference 或脱敏摘要，访问需要相应 scope。

## 6. LangGraph / fallback 选择

Phase 4 的 probe 比较两个 runner：简单数据库 state machine 与 LangGraph adapter。只有当需要多步 checkpoint、interrupt/resume 且两者可以用同一 contract suite 证明时才引入 LangGraph。失败或退出时保留 `workflow_run`、approval、audit 和 domain state，用 fallback runner 从 checkpoint 恢复；不得让图框架专有 memory 格式成为唯一恢复来源。
