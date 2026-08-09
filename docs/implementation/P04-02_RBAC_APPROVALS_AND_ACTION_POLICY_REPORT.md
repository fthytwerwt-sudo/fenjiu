# P04-02｜RBAC、approval 与 ActionPolicy 报告

> **状态：task_branch_local_validated；最终 commit / push / remote readback 以执行回报为准。**
>
> **执行日期：** 2026-08-09
>
> **精确工程基线：** `origin/main` `1cb06920908a42e7dc0be3d882838e856efd89fe`
>
> **任务分支：** `codex/p04-02-rbac-approvals`
>
> **范围边界：** 仅建立 stdlib、local-only、synthetic/value-free 的 scoped RBAC、ActionPolicy、approval request/decision 与 pre-execution recheck 合同。不创建真实用户、真实权限、真实审核者、生产账号、外部 adapter、业务真值或任何外部执行能力。

## 1. 结论

- 新增 `core/security/action_policy.py`，定义 `ActorRole`、`ActionName`、`PolicyPhase`、`ApprovalState`、`ApprovalAction`、`Environment`、`PolicyActor`、`PolicyRequest`、`PolicyDecision`、`ActionPolicy` 与 `ActionApprovalService`。
- `ActionPolicy.evaluate()` 同时检查 actor role、scope、data state、approval state、fact freshness、DNC/consent、feature flag、environment 与 required evidence；任一不满足返回稳定、无敏感值 `error_code` 与 audit-ready `PolicyDecision`。
- 高风险流程固定为：`request -> separate reviewer -> decision -> pre_execution_recheck`。审批 request、decision 与 audit event 均为 append-only tuple 输出；无 `update`、`delete` 或 `approve_without_policy` 公共绕过面。
- `ActionApprovalService` 支持 `approve`、`reject`、`revise`、`expire`；同一 reviewer 不可 approve 自己创建的高风险 request，终态 request 不可再用新 decision 变更。
- `forbidden` 外部动作统一 hard deny：`external_send`、`content_publish`、`price_quote`、`payment`、`order`、`refund`、`inventory_write` 均返回 `external_action_forbidden`，并标记 `external_execution_attempted=True` 供审计。
- P04-01 workflow metadata 可作为 `PolicyRequest` 输入来源，但本实现不改 `workflows/runner.py`，不扩大 workflow store 公共写面，也不让 ActionPolicy 成为 approval truth 或 store 绕过。
- Spec review fix：`pre_execution_recheck()` 现在强制 execution `subject_version` 等于已批准 request 的 `subject_version`；不一致返回 audit-ready denial `approval_subject_version_mismatch`，且 `external_execution_attempted=False`。
- Spec review fix：`request_approval()` 的 idempotency fingerprint 现在覆盖影响审批语义的 `PolicyRequest` 输入，包括 required evidence、data state、fact freshness/TTL、feature flag snapshot、DNC、consent、environment、actor、phase、approval state 以及原有 scope/correlation/action/target/policy/version/creator/expires_at；同 key 任一差异稳定 `idempotency_conflict`。

## 2. Roles / Actions 最小矩阵

| role | direct allowed action | 明确不能做 |
|---|---|---|
| `system_worker` | `run_internal_workflow` | approve/reject/revise/expire 高风险 request；外发、发布、报价、支付、订单、退款、库存写回 |
| `data_reviewer` | `approve_data_candidate` | 批准自己的高风险生成结果；跨 scope；改 audit |
| `content_reviewer` | `export_content_internal` | 改价格、库存、合规真值；公开发布 |
| `support_agent` | `apply_support_draft` | 绕过 DNC/consent/feature flag；自行解除外部发送策略 |
| `project_owner` | `configure_safe_flag` | 把缺失合规/业务证据自动视为解除；执行 forbidden 外部动作 |
| `auditor` | `read_audit` | 编辑业务记录、approval decision 或 audit |

## 3. Policy matrix 与稳定 denial proofs

| 场景 | 稳定结果 |
|---|---|
| unknown role | `actor_role_unknown` |
| actor scope 与 request scope 不一致 | `cross_scope_forbidden` |
| role 无 action 权限 | `role_not_permitted` |
| 缺 evidence | `required_evidence_missing` |
| 非 approved data 执行需 approved action | `data_state_not_approved` |
| fact freshness 过期 | `fact_stale` |
| DNC 命中 | `dnc_blocked` |
| consent 缺失 | `consent_required` |
| required feature flag 为 false | `feature_flag_disabled` |
| 非 local/test environment | `environment_forbidden` |
| forbidden 外部动作 | `external_action_forbidden` |
| self approval | `self_approval_forbidden` |
| terminal request 再 decision | `duplicate_decision` |
| pending request 执行前复核 | `approval_not_approved` |
| approved request 的 execution subject version 变化 | `approval_subject_version_mismatch` |
| 同 idempotency key 改审批语义输入 | `idempotency_conflict` |

## 4. Approval flow

1. `request_approval()`：只接受 `PolicyPhase.REQUEST`、`ApprovalState.PENDING`、同 scope、当前 evidence、当前 freshness 和 local/test 环境；通过后追加 request 与 audit event。
2. `decide()`：只允许非 creator 的具权 reviewer 对 pending request 追加 `approve/reject/revise` decision；`revise` 必须带 `revision_ref`。
3. `expire()`：只允许到期 request 追加 `expire` decision，并将 request state 标为 `expired`。
4. `pre_execution_recheck()`：只对 approved request 运行；执行前重新检查 data state、freshness、DNC/consent、feature flag、environment 与 evidence。批准后事实或 flag 变化会 fail closed。

## 5. Test-first evidence

- **RED**：新增 `tests/contracts/test_action_policy_rbac_approvals.py` 后，首次运行 `python3 -m unittest tests.contracts.test_action_policy_rbac_approvals` 失败于 `ModuleNotFoundError: No module named 'core.security.action_policy'`。
- **GREEN**：新增最小 ActionPolicy / approval service 后，P04-02 专项 6 项通过。
- **Refine**：补 `PolicyRequest.phase`、过期测试时钟基准、unknown action 安全返回、decision idempotency 重放与默认 UTC 时钟后，专项保持通过。
- **Spec review RED**：新增 subject-version recheck 与 request idempotency semantic fingerprint tests 后，专项先失败：version=1 approval 在 execution 传 version=2 仍 allowed；同 key 改 evidence/freshness/flag 等语义字段返回旧 request 或先返回非幂等错误。
- **Spec review GREEN**：加入 `approval_subject_version_mismatch` denial 与完整 request semantic fingerprint 后，P04-02 专项 7 项通过。

## 6. Validation evidence

- `python3 -m unittest tests.contracts.test_action_policy_rbac_approvals`：7 项通过。
- `python3 -m unittest discover -s tests/workflows`：11 项通过。
- `python3 -m unittest discover -s tests/architecture`：8 项通过。
- `python3 -m unittest discover -s tests/contracts`：53 项通过。
- `make regression`：通过；两轮 migration replay、16 类 SQL negative constraints、8 architecture、14 regression、8 local-runtime、16 control-plane、53 contracts、35 ingestion tests 全部通过。
- `python3 -m compileall -q -x '(^|/)\._' apps core observability modules adapters workflows tests`：通过。
- `git diff --check`：通过。
- `python3 scripts/validate_gpt_project_mechanism_sync.py --no-report`：通过。
- `python3 scripts/validate_regression_baseline.py --base-sha 1cb06920908a42e7dc0be3d882838e856efd89fe`：通过。
- `python3 scripts/validate_regression_baseline.py --base-sha 1cb06920908a42e7dc0be3d882838e856efd89fe --all-files`：通过。

## 7. 工程治理检查

- `repository_hygiene_check（仓库卫生检查）`：当前新增代码和测试只包含 synthetic/value-free 标识符；未写入 secret、token、cookie、私有联系方式、本地绝对路径、真实 SKU、价格、库存或业务资料。
- `configuration_validation（配置验证）`：未新增配置、环境变量、生产连接、真实账号或外部 provider。
- `data_safety_check（数据安全检查）`：未读取或提交真实供应链资料、个人信息或海鲜业务事实；业务线 scope 仍由 `ScopeRef` 明确注入。
- `dependency_compatibility_check（依赖兼容检查）`：`not_applicable`；未新增或修改依赖。
- `failure_handling（失败处理）/ negative behavior test（负向行为测试）`：覆盖 unknown role、cross scope、role denied、missing evidence、stale fact、approval 后 fact/flag/subject version 变化复核、request idempotency semantic drift、DNC/consent、flag false、non-local env、self approval、terminal duplicate、pending execution 和 forbidden external actions。

## 8. 事实分级与剩余阻断

- **CONFIRMED（工程）**：P04-02 local RBAC/action-policy/approval contract 已由专项和回归测试验证。
- **CONFIRMED（工程边界）**：所有记录仍为 synthetic/value-free；无外部 adapter、无真实用户权限、无真实审批者、无生产连接、无外部动作。
- **BLOCKED（业务）**：真实 SKU、价格、库存、主体/资质、账号、收款、履约、TikTok 酒类边界、真实 RBAC/auth/RLS 与任何外部执行仍未建立或未获书面证据。
- **不成立**：本工程合同不代表真实角色/RBAC、业务授权、平台许可、供应链确认、上线、销售、报价、支付、订单、退款或库存写回能力。
