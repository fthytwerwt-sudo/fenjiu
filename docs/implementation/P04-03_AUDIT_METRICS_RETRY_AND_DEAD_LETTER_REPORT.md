# P04-03｜审计、指标、重试与死信队列报告

> **状态：task_branch_local_validated_with_spec_review_high_fix；最终 commit / push / remote readback 以执行回报为准。**
>
> **执行日期：** 2026-08-09
>
> **精确工程基线：** `origin/main` `78d998ce2972e2a09a00db136dc1a43169d33416`
>
> **任务分支：** `codex/p04-03-audit-metrics-retry-dlq`
>
> **范围边界：** 仅建立 stdlib、local-only、synthetic/value-free 的 append-only audit（追加式审计）、retry classification（重试分类）、dead-letter visibility（死信可见性）、metrics/log redaction（指标/日志脱敏）与 correlation tracing（关联追踪）合同。不接入真实监控 SaaS、broker、云端、生产数据库、真实身份/资料或外部 action adapter。

## 1. 结论

- 新增 `core/security/audit.py`：提供 `InMemoryAuditLog`、`AuditEvent` 与 `AuditRequiredCommandExecutor`。审计事件由 sink 内部生成 sequence（序列）、previous/chain hash（链式哈希）与 event ref；事件 frozen（不可变），无 public update/delete。
- 审查 HIGH 修复：`AuditRequiredCommandExecutor` 现在只接受 staged effect（暂存效果）合同；`command_started` 审计成功后，mutation 只能准备 effect，必须等 `command_succeeded` 审计写入成功后才 `commit()`。若 success audit 写入失败，执行 `rollback()` 并抛 `audit_persistence_required`，不留下可见 mutation。
- 新增 `core/application/retry.py`：提供 `RetryClassifier`、`RetryDecision`、`LocalDeadLetterQueue`。自动重试仅限 internal transient（内部瞬时失败）；external side effect（外部副作用）、unknown side effect（未知副作用）和 broker unavailable（broker 不可用）进入 manual/pending 状态。
- 新增 `observability/metrics.py`：提供本地 append-only metric samples（指标样本）、固定 metric names（指标名）和 label redaction（标签脱敏）；不定义告警阈值、保留期或外部 endpoint。
- 扩展 `core/application/__init__.py`、`core/security/__init__.py`、`observability/__init__.py` 的导出，不修改 P04-02 action policy（动作策略）边界，不开启任何外部执行。

## 2. Audit 证明

| 场景 | 已验证行为 |
|---|---|
| append-only sequence | 两条审计事件 sequence 为 `1, 2`，第二条 `previous_chain_hash` 等于第一条 `chain_hash` |
| tamper visibility | `verify_chain()` 可重算链式哈希；事件 dataclass frozen，测试验证直接改 actor 会失败 |
| no ordinary mutation | `InMemoryAuditLog` 不暴露 `update` / `delete` |
| sensitive rejection | metadata key/value 含 raw content、contact、secret-like value 或 local path pattern 时 fail closed，记录数不变化 |
| mutating command audit gate | `AuditRequiredCommandExecutor` 在 start audit 写入失败时不调用 mutation callback，稳定返回 `audit_persistence_required` |
| success audit atomicity | started 审计成功、effect 已准备、success 审计失败时，rollback 被调用，commit 不可见 |

审计事件只保留 actor/command/correlation/scope/policy/version/time/result/hash/safe metadata；不记录 raw content（原始内容）、PII（个人资料）、secret（密钥）、token（访问令牌）、cookie（身份凭证）或 local absolute path（本地绝对路径）。本地 synthetic 合同不假装能回滚任意已执行副作用；调用方必须返回可 `commit` / `rollback` 的 staged effect。

## 3. Retry / DLQ 证明

| failure effect | attempt 状态 | 稳定结果 |
|---|---|---|
| `internal_transient` | 未到上限 | `auto_retry` + `retry_scheduled` |
| `internal_transient` | 到达上限 | `no_retry` + `dead_lettered` |
| `internal_permanent` | 任意合法 attempt | `no_retry` + `dead_lettered` |
| `external_side_effect` | 任意合法 attempt | `manual_review` + `manual_queue`，不可自动 retry |
| `unknown_side_effect` | 任意合法 attempt | `manual_review` + `manual_queue`，不可自动 retry |
| `broker_unavailable` | 任意合法 attempt | `manual_review` + `pending_manual`，审计引用不丢失 |

`LocalDeadLetterQueue` 只保留 `source_ref`、`checkpoint_ref`、`correlation_id`、`error_code`、`reason_code` 和 attempts；不会保存 payload、正文、路径、secret 或外部请求内容。

## 4. Metrics / Logs 证明

- `record_retry_metrics()` 记录 `retry_decision_total`，并按状态追加 `dead_letter_total` 或 `manual_queue_depth`；label 仅保留 safe identifier（安全标识符）、code（代码）、count/bool（计数/布尔）类值。
- metrics label 出现本地路径样式值时输出 `redacted_identifier`，不泄露原值。
- 现有 `JsonLogEvent` 继续保留 correlation_id，并对 bearer-like detail（类似凭证详情）输出 `[REDACTED]`。
- P04-03 专项测试验证 metrics/log rendered summary 不出现合成敏感值或本地路径片段。

## 5. Test-first evidence

- **RED**：新增 `tests/contracts/test_audit_metrics_retry_dead_letter.py` 后，首次运行 `python3 -m unittest tests.contracts.test_audit_metrics_retry_dead_letter` 失败于 `ModuleNotFoundError: No module named 'core.application.retry'`。
- **GREEN**：新增 audit/retry/metrics 最小实现后，P04-03 专项 6 项通过。
- **Safety repair**：P00 `--all-files` 首次发现新测试文件含可匹配的 `local_absolute_path` 合成样本；已将样本拆为安全字符串拼接，保留测试语义后 P00 `--all-files` 通过。
- **Spec review HIGH RED**：新增 `test_staged_mutation_is_not_committed_when_success_audit_fails` 后，P04-03 专项先失败，`prepared` 未出现 `rolled_back`，证明 success audit 失败后 staged effect 未回滚。
- **Spec review HIGH GREEN**：加入 `AuditStagedEffect` 与 staged commit/rollback 协议后，started 审计成功、success 审计失败时 rollback 被调用，commit 列表保持空，P04-03 专项 7 项通过。

## 6. Validation evidence

- `python3 -m unittest tests.contracts.test_audit_metrics_retry_dead_letter`：7 项通过。
- `python3 -m unittest discover -s tests/workflows`：11 项通过。
- `python3 -m unittest tests.contracts.test_action_policy_rbac_approvals`：7 项通过。
- `python3 -m unittest tests.control_plane.test_config_flags_health_observability`：16 项通过。
- `python3 -m unittest discover -s tests/contracts`：60 项通过。
- `python3 -m unittest discover -s tests/architecture`：8 项通过。
- `python3 -m unittest tests.ingestion.test_approval_publish_and_refresh`：9 项通过。
- `make regression`：通过；两轮 migration replay、16 类 SQL negative constraints、8 architecture、14 regression、8 local-runtime、16 control-plane、60 contracts、35 ingestion tests 全部通过。
- `python3 -m compileall -q -x '(^|/)\._' apps core observability modules adapters workflows tests`：通过。
- `git diff --check`：通过。
- `python3 scripts/validate_gpt_project_mechanism_sync.py --no-report`：通过。
- `python3 scripts/validate_regression_baseline.py --base-sha 78d998ce2972e2a09a00db136dc1a43169d33416`：通过。
- `python3 scripts/validate_regression_baseline.py --base-sha 78d998ce2972e2a09a00db136dc1a43169d33416 --all-files`：通过。

## 7. 工程治理检查

- `repository_hygiene_check（仓库卫生检查）`：新增代码、测试和报告仅包含 synthetic/value-free 标识符与相对路径；最终 P00 default 与 `--all-files` 扫描通过。
- `configuration_validation（配置验证）`：未新增配置、环境变量、生产连接、真实账号、真实 broker 或监控 endpoint。
- `data_safety_check（数据安全检查）`：未读取、复制、记录或提交真实供应链资料、个人信息、海鲜业务事实、raw content、PII、secret、token、cookie 或 local absolute path。
- `dependency_compatibility_check（依赖兼容检查）`：`not_applicable`；未新增或修改依赖。
- `failure_handling（失败处理）/ negative behavior test（负向行为测试）`：覆盖 audit persistence failure、success audit failure rollback、敏感 metadata 拒绝、external/unknown/manual retry、broker unavailable pending/manual、DLQ 安全摘要、metrics/log redaction。

## 8. 事实分级与剩余阻断

- **CONFIRMED（工程）**：P04-03 local audit / retry / DLQ / metrics / redaction contract 已由专项与回归测试验证。
- **CONFIRMED（工程边界）**：所有实现保持 stdlib/local-only/synthetic/value-free；无外部 adapter、无生产数据库、无真实身份/RBAC、无真实资料、无外部监控 SaaS。
- **BLOCKED（业务）**：真实 SKU、价格、库存、主体/资质、账号、收款、履约、TikTok 酒类边界、真实 auth/RBAC/RLS、生产审计/队列和任何外部执行仍未建立或未获书面证据。
- **不成立**：本工程合同不代表 Phase 4 全部完成、业务上线、真实报价、支付、订单、退款、库存写回、公开发布或履约能力。

## 9. P05/P06/P07 输入

- 后续模块可使用 `InMemoryAuditLog.record()` 记录 command intent/result，命令在 audit sink 不可写时必须 fail closed。
- 后续 worker/queue 可使用 `RetryClassifier.classify()` 统一区分 auto retry、DLQ、manual queue 与 broker unavailable pending/manual。
- 后续 observability 可使用固定 metric names 与 redacted labels；告警阈值、保留期和外部监控 endpoint 必须由后续明确配置任务决定。
