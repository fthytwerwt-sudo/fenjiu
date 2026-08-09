# P06-01｜Conversation contracts、idempotency 与 privacy minimization 报告

> **状态：task_branch_local_validated；最终 commit / push / remote readback 以执行回报为准。**
>
> **执行日期：** 2026-08-09
>
> **精确工程基线：** `origin/main` `eda64feb9945e1f9f2eaa688b1152f87b8182bf5`
>
> **任务分支：** `codex/p06-01-conversation-contracts`
>
> **范围边界：** 仅建立 stdlib、local-only、synthetic/value-free 的客服会话、消息、意图、draft-only 回复引用、handoff 与隐私最小化合同。不接入 WhatsApp/TikTok/Meta/email、webhook、channel adapter、真实客户资料、真实供应链资料、生产存储或发送 endpoint。

## 1. 结论

- 新增 `modules/customer_service/contracts.py`：定义 scoped `ConversationRecord`、`MessageRecord`、`IntentRecord`、`DraftReplyRecord`、`HandoffCase`、`InboundMessageCommand` 与 `InMemoryConversationStore`。
- inbound message body 仅作为输入计算 `content_hash`；持久记录只保存 hash、opaque `content_ref`、retention/consent/redaction refs、scope、policy version 和安全状态，不保存 raw body、attachment 或真实客户资料。
- external message replay 以 scope/channel/external message ID 和完整输入 fingerprint 幂等；相同 replay 返回旧 receipt，不新增 message、draft 或 audit event；同 ID 改 payload / scope 稳定拒绝。
- unknown scope 创建 quarantine/handoff，不创建 scoped conversation/message；已知 scope 必须使用 `ScopeRef`，同一 external conversation 不能跨 business line 复用。
- DNC、personal data、high-risk intent 都进入 handoff，不生成 draft；absolute path、secret-like payload 和未标记 personal data 在写入前 fail closed。
- 新增 `migrations/0003_support_conversations_messages_privacy.sql`：建立 `support_conversations`、`support_messages`、`support_intents`、`support_draft_replies`、`support_handoff_cases` 五张 synthetic-only append-only 表。
- `modules/customer_service` 仍无 webhook、channel adapter 或 outbound delivery surface。

## 2. RED → GREEN 证据

- **RED（Python）**：新增 `tests/contracts/test_customer_service_conversation_contracts.py` 后，首次运行 `python3 -m unittest tests.contracts.test_customer_service_conversation_contracts` 失败于 `ImportError: cannot import name 'contracts' from 'modules.customer_service'`。
- **GREEN（Python）**：新增最小客服合同、store 与导出后，P06-01 专项 6 项通过。
- **RED（migration）**：先更新 migration regression 期望 support tables 与 `0003` 版本；运行 `make migration-test` 失败于缺少 P06 support schema。
- **GREEN（migration）**：新增 `0003` 后，migration replay 两次、support 负向约束与既有 truth/scope 负例全部通过。
- **Safety repair**：P00 `--all-files` 发现测试中的合成本地路径片段；已拆分测试字符串，保留负向语义后扫描通过。

## 3. Validation evidence

- `python3 -m unittest tests.contracts.test_customer_service_conversation_contracts`：6 项通过。
- `python3 -m unittest tests.contracts.test_action_policy_rbac_approvals`：7 项通过。
- `python3 -m unittest tests.contracts.test_audit_metrics_retry_dead_letter`：9 项通过。
- `python3 -m unittest discover -s tests/workflows`：11 项通过。
- `python3 -m unittest discover -s tests/contracts`：68 项通过。
- `python3 -m unittest discover -s tests/architecture`：8 项通过。
- `make migration-test`：通过；P02/P06 migrations replay 两次，support 与 truth/scope negative constraints 通过并清理 Docker resources。
- `make regression`：通过；migration replay、compileall、8 architecture、14 regression、8 local-runtime、16 control-plane、68 contracts、35 ingestion tests 全部通过。
- `python3 -m compileall -q -x '(^|/)\._' apps core observability modules adapters workflows tests`：通过。
- `git diff --check`：通过。
- `python3 scripts/validate_gpt_project_mechanism_sync.py --no-report`：通过。
- `python3 scripts/validate_regression_baseline.py --base-sha eda64feb9945e1f9f2eaa688b1152f87b8182bf5`：通过。
- `python3 scripts/validate_regression_baseline.py --base-sha eda64feb9945e1f9f2eaa688b1152f87b8182bf5 --all-files`：通过。

## 4. 工程治理检查

- `repository_hygiene_check（仓库卫生检查）`：新增代码、测试、migration 和报告仅包含 synthetic/value-free 标识符、hash、opaque ref 与相对仓库路径；P00 default 与 `--all-files` 扫描通过。
- `configuration_validation（配置验证）`：未新增配置、环境变量、生产连接、真实账号、channel adapter、webhook、send endpoint 或外部 service。
- `data_safety_check（数据安全检查）`：未读取、复制、提交真实供应链资料、客户资料、价格、库存、资质、联系方式、raw chats、attachments 或海鲜业务事实；对 absolute path、secret-like payload、未标记 PII 均 fail closed。
- `dependency_compatibility_check（依赖兼容检查）`：`not_applicable`；未新增或修改依赖。
- `failure_handling（失败处理）/ negative behavior test（负向行为测试）`：覆盖 replay no side effect、idempotency drift、scope missing、cross-line reuse、unknown scope quarantine、DNC handoff、privacy handoff、unsafe payload rejection、no adapter/send surface、SQL duplicate external ID、cross-scope FK、opaque ref、external execution disabled 与 append-only triggers。

## 5. 事实分级与剩余阻断

- **CONFIRMED（工程）**：P06-01 local synthetic conversation/message/intent/draft/handoff contracts、external message idempotency、privacy minimization 与 migration constraints 已由专项、migration 和完整回归验证。
- **CONFIRMED（工程边界）**：实现不存 raw chat body/attachment，不接外部服务，不发送消息，不写 approved truth，不改变 P04 policy/audit 边界。
- **BLOCKED（业务）**：真实 SKU、价格、库存、主体/资质、账号、收款、履约、TikTok 酒类边界、真实 auth/RBAC/RLS、真实 customer consent/retention policy、生产审计/队列和任何外部执行仍未建立或未获书面证据。
- **不成立**：本任务不代表客服上线、自动回复可发送、真实模型可调用、真实渠道可接入、真实客户数据可入库、报价/订单/付款/退款/履约可执行。

## 6. P06-02 handoff

- P06-02 可复用 `InboundMessageCommand`、`InMemoryConversationStore` 与 support tables 作为 synthetic inbound conversation 基础。
- P06-02 的 draft 只能生成 `DraftReplyRecord.draft_ref` 和 fact/policy/model references；不得保存 raw prompt、raw output、真实 customer text 或发送内容。
- P06-02 必须先读 `CUSTOMER_SERVICE_AI_IMPLEMENTATION_PLAN.md`、`CORE_DATA_CONTRACTS.md`、`WORKFLOW_APPROVAL_AUDIT_DESIGN.md`、本报告、`modules/customer_service/contracts.py`、P03-03 与 P04 policy/audit 报告。
- P06-02 必须保持 `primary_route=FactQueryPort+RiskPolicy+FakeModel`、`fallback_route=manual handoff template`、`capability_status=synthetic`；无 approved/fresh truth、DNC、missing consent、high-risk intent、model/retrieval error、policy conflict 均 handoff。
- P06-02 禁止接 real LLM API、model key、send adapter、unapproved truth、真实客户数据、生产连接或 legacy channel code；验收必须包含 assert zero sends、no truth writes、fact expiry/revocation、model failure、forbidden expression 和 audit/redaction scan。
