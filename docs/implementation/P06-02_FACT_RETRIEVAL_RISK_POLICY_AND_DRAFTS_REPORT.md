# P06-02｜Approved fact retrieval、risk policy 与 draft/handoff 报告

> **状态：task_branch_local_validated；最终 commit / push / remote readback 以执行回报为准。**
>
> **执行日期：** 2026-08-09
>
> **精确工程基线：** `origin/main` `1033c7ab659df8a677a937b2b9bcb8f9b7141600`
>
> **任务分支：** `codex/p06-02-fact-risk-drafts`
>
> **范围边界：** 仅建立 stdlib、local-only、synthetic/value-free 的 approved fact reference、read-only fact query、risk-first policy、fake model draft、forbidden-expression check、hash-only reviewable draft 与 manual handoff evidence。不接真实渠道、真实模型、发送器、真实客户资料、真实供应链资料、approval/truth 写入或任何外部执行。

## 1. 结论

- 新增 `modules/customer_service/drafts.py`：定义 `ApprovedFactRef`、`InMemoryApprovedFactQuery`、`ForbiddenExpressionPolicy`、`FakeDraftModel`、`SupportDraftPipeline`、`DraftReviewRecord` 与 `ManualHandoffRecord`。
- P06-02 固定 `risk first（风险优先）`：价格、库存、配送、酒类购买、报价、退款、投诉、质量、账期、独家、订单、支付和 unknown intent 在 fact query / model 之前直接 `handoff_required`。
- 低风险 synthetic FAQ 只有在 fresh approved synthetic fact、有效 forbidden-expression policy 和 fake model 均通过时才生成 `draft_ready`；草稿仍为 reviewable draft，不可发送。
- `DraftReviewRecord` 仅保存 original/translation/prompt/output hash、versioned refs、fact locks、policy/model/template refs；不保存原始客户文本、原始 prompt 或原始 output。
- `ManualHandoffRecord` 记录 reason code、hash refs、policy/model/fact-query refs；所有 `external_execution_allowed`、`send_allowed`、`truth_write_allowed`、`approval_write_allowed` 均为 false。
- `modules/customer_service/__init__.py` 仅导出新合同类型；未新增 provider config、SDK、网络、sender 或生产连接。

## 2. 风险矩阵

| 输入/状态 | 稳定结果 |
|---|---|
| `faq_general` 等低风险白名单 + fresh approved synthetic fact + 有效 policy + fake model OK | `draft_ready`，仅可人工审查，不可发送 |
| price / inventory / delivery | `handoff_required: risk_policy_manual_required` |
| alcohol_purchase / quote / refund / complaint / quality / credit_terms / exclusive / order / payment / unknown | `handoff_required: risk_policy_manual_required` |
| 缺 approved fact | `handoff_required: approved_fact_missing` |
| expired / revoked / conflict / blocked / superseded fact | 对应 `approved_fact_*` handoff |
| fact retrieval failure | `handoff_required: fact_retrieval_failed` |
| policy owner / policy vector 缺失或过期 | `handoff_required: policy_owner_missing` |
| fake model failure / missing output | `handoff_required: model_generation_failed` 或 `model_output_missing` |
| forbidden expression 命中 | `handoff_required: forbidden_expression_detected` |
| cross scope fact/policy | fail closed: `cross_scope_forbidden` |
| 任一外部执行、truth write、approval write 或 send 许可尝试 | fail closed: `external_execution_forbidden` |

## 3. Fact lock 与 handoff 证据

- `DraftFactLock` 只接受 `approval_state=approved`、`data_state=fixture`、`external_execution_allowed=false` 的 synthetic approved fact reference。
- `fact_version_set_hash` 由 fact version IDs 与 value hashes 派生；草稿 safe summary 暴露 hash/ref，不暴露原始 fact value。
- P06-02 专项测试断言低风险草稿的 safe summary 不包含原始 question、translation、fake model output、raw prompt/output 字段。
- P06-02 专项测试断言 business gate intents 在 fact query 和 model 前就转人工，`fact_query.call_count == 0` 且 `model.call_count == 0`。
- P06-02 专项测试覆盖 missing / expired / revoked / conflict fact、retrieval failure、model failure、forbidden expression、policy missing、cross scope 和 external capability attempt。

## 4. RED → GREEN 证据

- **RED**：先新增 `tests/contracts/test_customer_service_fact_retrieval_risk_policy_and_drafts.py`，首次运行 P06-02 专项失败于 `ModuleNotFoundError: No module named 'modules.customer_service.drafts'`。
- **GREEN**：新增最小 `drafts.py` 和导出后，P06-02 专项 5 项通过。
- **测试修正**：初始 hash-only 断言误把合法 `original_text_hash` / `prompt_hash` 字段名当成违规；已收窄为禁止原文、原 output 和原 prompt 字段，保留 hash 字段。

## 5. Validation evidence

- `python3 -m unittest tests.contracts.test_customer_service_fact_retrieval_risk_policy_and_drafts`：5 项通过。
- `python3 -m unittest tests.contracts.test_customer_service_conversation_contracts tests.contracts.test_customer_service_fact_retrieval_risk_policy_and_drafts tests.ingestion.test_approval_publish_and_refresh tests.contracts.test_action_policy_rbac_approvals tests.contracts.test_audit_metrics_retry_dead_letter`：36 项通过。
- `python3 -m unittest discover -s tests/contracts`：89 项通过。
- `python3 -m unittest discover -s tests/ingestion`：35 项通过。
- `make regression`：通过；migration replay 两次、P02/P06 negative constraints、compileall、8 architecture、14 regression、8 local-runtime、16 control-plane、89 contracts、35 ingestion tests 全部通过并清理隔离 Docker resources。
- `python3 -m compileall -q -x '(^|/)\._' apps core observability modules adapters workflows tests`：通过。
- `python3 scripts/validate_gpt_project_mechanism_sync.py --no-report`：通过。
- `git diff --check`：通过。
- `python3 scripts/validate_regression_baseline.py --base-sha 1033c7ab659df8a677a937b2b9bcb8f9b7141600`：通过。
- `python3 scripts/validate_regression_baseline.py --base-sha 1033c7ab659df8a677a937b2b9bcb8f9b7141600 --all-files`：通过。

## 6. 工程治理检查

- `repository_hygiene_check（仓库卫生检查）`：P00 default 与 `--all-files` 扫描通过；变更限定在 P06-02 合同、测试和本报告。变更文件人工检索未发现本地绝对路径、真实客户/供应链资料、汾酒与海鲜业务线污染或真实外部资料。
- `configuration_validation（配置验证）`：未新增配置文件、环境变量、provider key、模型 key、channel adapter、sender、生产连接或 feature flag 默认值变更。
- `data_safety_check（数据安全检查）`：实现和测试只使用 synthetic refs、hashes、UUID、policy/model/template version refs；不读取 `.env` 内容，不保存原始客户文本、prompt/output、真实 SKU、价格、库存、资质、账号、收款、订单或履约资料。
- `dependency_compatibility_check（依赖兼容检查）`：`not_applicable`；未新增或修改依赖文件。

## 7. 事实分级与剩余阻断

- **CONFIRMED（工程）**：P06-02 local synthetic approved-fact retrieval、risk-first policy、fake model draft、forbidden-expression check、hash-only fact lock 与 manual handoff contracts 已由专项和完整回归验证。
- **CONFIRMED（工程边界）**：模型只是假模型；AI 不能写 truth、approval 或 send；所有 external execution flags 保持 false。
- **BLOCKED（业务）**：真实 SKU、价格、库存、主体/资质、账号、收款、履约、TikTok 酒类边界、真实 auth/RBAC/RLS、真实 customer consent/retention policy、生产审计/队列、真实模型/渠道/发送器和任何外部业务动作仍未建立或未获书面证据。
- **不成立**：本任务不代表 Phase 6 完成、客服上线、自动回复可发送、真实模型可调用、真实客户数据可入库、报价/订单/付款/退款/履约可执行。

## 8. P06-03 handoff

- P06-03 只能消费 `DraftOutcome` 的 hash/ref/fact-lock/handoff evidence，不能读取 raw prompt/output，也不能接真实 sender。
- 若 P06-03 需要 adapter 或人工接管 UI，必须继续保持 `external_execution_allowed=false`，并以 fake adapter / synthetic fixtures 先锁定 no-send、handoff takeover 和 audit/redaction regression。
