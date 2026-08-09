# P06-03｜support adapter、human takeover 与 draft-only E2E 报告

> **状态：task_branch_local_validated；最终 commit / push / remote readback 以执行回报为准。**
>
> **执行日期：** 2026-08-10
>
> **精确工程基线：** `origin/main` `37b19ed4bffff3b9d7a0341c6e756f71ce6ff6e4`
>
> **任务分支：** `codex/p06-03-support-adapter-takeover`
>
> **范围边界：** 仅建立 stdlib、local-only、synthetic/value-free 的 fake support receive adapter、draft-only review case、manual handoff、human approve/reject/revise/resume 审计与 zero-send proof。不接 Chatwoot、WhatsApp、Meta、TikTok、真实模型、真实客户数据、真实发送器、provider endpoint、SendApproved 或任何外部执行。

## 1. 结论

- 新增 `adapters/support/fake.py`，提供 receive-only `FakeSupportPort` 与 `SupportInboundEnvelope`；原始外部 conversation/message ID 只作为 synthetic 输入，进入 P06-01 前转换为 opaque refs。
- 新增 `modules/customer_service/takeover.py`，定义 `SupportReviewCase`、`SupportCaseQueue`、`HumanDecision`、`SupportZeroSendProof` 与 case state；所有 case 固定 `external_send_attempts=0` 且 `external_execution_allowed=false`。
- 新增 `core/application/support_takeover.py`，把 P06-03 case opening、人工 decision、explicit resume 与 fact invalidation 记录到 P04 append-only audit log。
- P04 `ActionPolicy` 新增 `approve_support_draft` internal action，仅允许 support agent 在 fixture synthetic draft 上走 approval flow；批准结果为 `human_approved_internal`，不代表发送许可。
- 新增 `apps/admin/support_cases.py` 与 `workflows/support.py` 的最小 facade，只暴露 safe summaries 和人工决策入口，不暴露 raw body、prompt、output、sender 或 provider endpoint。
- 新增 `tests/contracts/test_support_adapter_takeover_e2e.py`，覆盖 fake receive、幂等回放、DNC/PII/high-risk/manual handoff、fact invalidation、人工 approve/reject/revise/resume、zero-send 与无 sender surface。

## 2. 行为合同

| 场景 | 稳定结果 |
|---|---|
| synthetic inbound + scoped conversation + low-risk FAQ + fresh approved fact | 生成 `draft_only` review case；automation paused；等待人工处理 |
| replayed inbound / replayed case opening | 返回同一 receipt/case；不重复审计；不发送 |
| DNC 命中 | `manual_handoff.reason_code=dnc_blocked` |
| PII / private contact detected | `manual_handoff.reason_code=privacy_review_required` |
| price / inventory / delivery 等业务闸门 intent | `manual_handoff.reason_code=risk_policy_manual_required` |
| high risk conversation | `manual_handoff.reason_code=high_risk` |
| missing / expired / revoked / conflict fact | 对应 `approved_fact_*` manual handoff |
| approved draft | `human_approved_internal`；仍然 internal only；`external_send_attempts=0` |
| rejected / revised draft | 记录 human decision audit；不生成发送任务 |
| explicit resume | 只记录 `support_resume_recorded` audit；automation 仍 paused；不自动外发 |
| policy/fact version invalidation | case 置为 `invalidated`；automation paused；后续 approve fail closed |
| SendApproved / sender / provider endpoint | 公共表面不存在；zero-send proof 固定为 false/0 |

## 3. RED → GREEN 证据

- **RED**：先新增 P06-03 合同测试后，首次运行 `python3 -m unittest tests.contracts.test_support_adapter_takeover_e2e` 失败于 `ImportError: cannot import name 'FakeSupportPort' from 'adapters.support'`。
- **GREEN**：新增 fake adapter、takeover queue、application workflow、policy action 与 exports 后，P06-03 专项 6 项通过。
- **测试修正**：将 case 幂等 fingerprint 从完整 receipt/outcome summary 收敛为 stable conversation/message + draft/handoff fields，避免 replay 状态或审计时间改变幂等结果。

## 4. 已验证

- `python3 -m unittest tests.contracts.test_support_adapter_takeover_e2e`：6 项通过。
- `python3 -m unittest tests.contracts.test_customer_service_conversation_contracts tests.contracts.test_customer_service_fact_retrieval_risk_policy_and_drafts tests.contracts.test_outreach_draft_zero_send tests.contracts.test_legacy_video_adapter_manifest`：24 项通过。
- `python3 -m unittest tests.contracts.test_action_policy_rbac_approvals tests.contracts.test_audit_metrics_retry_dead_letter`：16 项通过。
- `python3 -m unittest discover -s tests/contracts`：115 项通过。
- `python3 -m unittest discover -s tests/architecture`：8 项通过。
- `python3 -m compileall -q -x '(^|/)\._' apps core observability modules adapters workflows tests`：通过。
- `git diff --check`：通过。
- `python3 scripts/validate_regression_baseline.py --base-sha 37b19ed4bffff3b9d7a0341c6e756f71ce6ff6e4`：通过。
- `python3 scripts/validate_regression_baseline.py --base-sha 37b19ed4bffff3b9d7a0341c6e756f71ce6ff6e4 --all-files`：通过。
- `python3 scripts/validate_gpt_project_mechanism_sync.py --no-report`：通过。
- `make compose-config`：通过。
- `make migration-test`：通过；两轮 migration replay 和 P02/P05/P06 negative constraints 通过。
- `make regression`：通过；compose config、migration replay、compileall、8 architecture、16 regression、8 local-runtime、16 control-plane、115 contracts、35 ingestion tests 全部通过。
- remote branch / commit / key files readback 以最终执行回报为准。

## 5. 工程治理检查

- `repository_hygiene_check（仓库卫生检查）`：P00 default 与 `--all-files` 均通过；P06-03 变更仅使用 synthetic refs、hashes、UUID、policy/action identifiers。
- `configuration_validation（配置验证）`：`make compose-config` 通过；未新增配置文件、环境变量、provider key、channel adapter、sender、生产连接或 feature flag 默认值变更。
- `data_safety_check（数据安全检查）`：P00 扫描通过；变更路径定向检索未发现真实客户资料、真实供应链资料、本地绝对路径、凭据、Chatwoot/WhatsApp/Meta/TikTok provider 调用、SendApproved 或发送器实现。测试里的 `sender` / `provider_endpoint` 仅为 forbidden surface 断言。
- `dependency_compatibility_check（依赖兼容检查）`：`not_applicable`；未新增或修改依赖文件。

## 6. 事实分级与剩余阻断

- **CONFIRMED（工程）**：P06-03 local synthetic receive-only support adapter、draft-only case queue、manual handoff、human decision audit、explicit resume audit 与 zero-send proof 已由专项和相邻合同测试验证。
- **CONFIRMED（工程边界）**：无 Chatwoot / WhatsApp / Meta / TikTok / 模型 / 网络 / 真实客户数据调用；无 SendApproved、sender 或 provider endpoint；所有 external send attempts 为 0。
- **BLOCKED（业务）**：真实 SKU、价格、库存、主体/资质、账号、收款、履约、TikTok 酒类边界、真实 auth/RBAC/RLS、真实 customer consent/retention policy、生产审计/队列、真实客服渠道/发送器和任何外部业务动作仍未建立或未获书面证据。
- **不成立**：本任务不代表 Phase 6 完成、客服上线、自动回复可发送、真实模型可调用、真实客户数据可入库、报价/订单/付款/退款/履约可执行。
