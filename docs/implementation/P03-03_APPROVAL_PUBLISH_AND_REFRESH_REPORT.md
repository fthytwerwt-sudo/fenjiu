# P03-03｜审批、版本化发布与下游刷新报告

> **状态：task_branch_pushed_remote_readback_verified; controller_review_pending**
>
> **执行日期：** 2026-08-08
>
> **精确工程基线：** `origin/main` `697c6dbd5430a0c132a08f380f8ff56e77851eb3`
>
> **任务分支：** `codex/p03-03-approval-publish-refresh-v2`
>
> **范围边界：** 仅完成 stdlib（标准库）、local-only（本地限定）、synthetic/value-free（合成且不含真实值）的 approval request（审批请求）、human decision（人工决定）、isolated approved synthetic truth version（隔离的已批准合成真值版本）、supersede/revoke（替代/撤销）与 internal refresh event（内部刷新事件）合同。本报告不证明真实供应链资料、P02 current truth（P02 当前真值读取）、外部发布、CRM/support/video（客户管理/客服/内容视频）实现、供应链确认、合规许可或业务外部执行成立。

## 1. 结论

- 新增 `modules/ingestion/approval.py`，实现 `SyntheticApprovalPublisher`（合成审批发布器）和不可变 synthetic approval/version/refresh/audit contracts。
- P03-03 的 `ApprovedSyntheticTruthVersion`（已批准合成真值版本）保持 `data_state=fixture`、`is_synthetic=true`、`external_execution_allowed=false`、`business_external_ready=false`；它不复用、不导入、不写入 P02 `modules/truth_center` current-read path。
- 成功链路为：P03-02 `MappedCandidate` + `MappingReport` → `ReviewRequestCommand` → `HumanDecisionCommand` → immutable approved synthetic version → `TruthFactsChanged` internal invalidation event。
- 支持 `approve`、`reject`、`revise`、`supersede` 和 `revoke`；每个决定记录 actor reference、时间、policy/evidence reference、correlation、P03-02 mapping report/profile fingerprint 和 source/job/result/staging lineage。
- `TruthFactsChanged` 只枚举未来消费者 `customer_service`、`content_video`、`crm`，语义仅为 internal invalidation，不实现或调用这些模块。
- 控制器 follow-up 修复新增 correlation integrity（关联链完整性）、expiry state（过期状态）与 logical scope key（逻辑业务范围键）：request/decision/revoke 每条写入链自身的 `correlation_id` 必须与所属 record correlation 一致；version/refresh/audit 保留原始 correlation；current read（当前读取）使用 tenant/project/business_line 组成的业务范围键，避免把一次性 correlation 当成业务真值 series key（系列键）。过期 request 进入 `EXPIRED` 并追加审计，不产生 decision/version/refresh。

## 2. Fail-closed 合同

| 场景 | 稳定行为 |
|---|---|
| 缺 P03-02 source/evidence lineage | `mapping_evidence_required`，不创建 request/version/refresh |
| P03-02 quality 未通过 | `quality_not_passed`，不发布 |
| request 过期 | `approval_request_expired`，不追加 decision/version/refresh |
| request correlation 与 scope correlation 不一致 | `correlation_mismatch`，不创建 request/audit |
| decision correlation 与 request correlation 不一致 | `correlation_mismatch`，不创建 decision/version/refresh/audit |
| revoke correlation 与 version correlation 不一致 | `correlation_mismatch`，不撤销、不刷新、不审计 |
| current read 使用新的合法 correlation | 仍可读取同一 tenant/project/business_line 的当前 approved synthetic version，不改写 version/refresh/audit correlation |
| current read 改变 tenant/project/business_line 任一项 | 返回 `None`，不跨业务范围读取 |
| 跨 business line/scope | `cross_scope_forbidden` |
| 高风险 self approval | `self_approval_forbidden` |
| 已存在 current version 但未走 supersede | `publication_supersede_required` |
| requested version 与 current chain 冲突 | `version_conflict` |
| 同 idempotency key 不同 payload | `idempotency_conflict` |
| terminal request 再决策 | `duplicate_decision` |
| sensitive actor/idempotency/correlation metadata | `sensitive_metadata_forbidden` |

除合法 expiry state/audit 转换外，失败路径在提交前完成所有校验，失败后 `snapshot_counts()` 不变化，避免半成品 request、decision、version 或 refresh 记录。expiry（过期）转换只改变 request state 为 `EXPIRED` 并追加 `approval_request_expired` audit event，不产生 decision/version/refresh。

## 3. 下游读取与隔离

- `current(scope, fact_type, subject_ref)` 只返回当前有效的 `SyntheticTruthStatus.APPROVED` synthetic version。
- P03-03 private `_LogicalScopeKey`（私有逻辑业务范围键）仅由 `tenant_id`、`project_id`、`business_line_id` 组成，只用于 `_current_by_key` 的写入、current read、revoke deletion（撤销删除当前索引）和 supersede/current lookup（替代/当前查找）；不修改 core `ScopeRef`、P02 `truth_center` 或其他 Phase。
- `ScopeRef.correlation_id` 仍作为 request/decision/revoke/version/refresh/audit 的追踪 correlation（关联追踪 ID）保留并校验；它不再参与 current read 的业务 series key。
- P03-02 candidate、pending request、rejected/revised/expired/conflict 路径、superseded version 和 revoked version 均不能通过 downstream read 读取。
- `supersede` 与 `revoke` 不删除、不覆写历史 version；旧版状态由 append-only status overlay 和 refresh invalidation 记录表达。
- P02 SQL negative constraints 仍证明 synthetic fixture 不能成为 P02 `DataState.APPROVED`；P03-03 没有削弱该限制。

## 4. Test-first 与验证证据

- **RED**：首次运行 `python3 -m unittest tests.ingestion.test_approval_publish_and_refresh` 因 `ModuleNotFoundError: No module named 'modules.ingestion.approval'` 失败。
- **GREEN**：新增最小 implementation 后，P03-03 专项测试通过；自审新增 audit sequence/idempotency conflict 回归，先复现失败，再修复通过。
- **Controller follow-up RED**：新增 correlation mismatch 与 expiry state tests 后，专项测试先失败于 `AttributeError: EXPIRED` 与 `ApprovalBoundaryError not raised`。
- **Controller follow-up GREEN**：加入 `ApprovalRequestState.EXPIRED`、`correlation_mismatch` guards 和 append-only expiry audit 后，专项测试通过。
- **Controller current-read RED**：新增 logical scope key 回归后，专项测试先失败于同 tenant/project/business_line、不同合法 correlation 的 `current()` 返回 `None`。
- **Controller current-read GREEN**：加入 private `_LogicalScopeKey` 后，`current()` 不再把一次性 correlation 当成业务范围 key，且 version/refresh/audit correlation 未被改写。
- `python3 -m unittest tests.ingestion.test_approval_publish_and_refresh`：9 项通过。
- `python3 -m unittest discover -s tests/ingestion`：35 项通过。
- `make regression`：通过；P02 migrations replay 两次、16 类 SQL negative constraints 通过，8 architecture + 14 regression + 8 local-runtime + 16 control-plane + 46 contracts + 35 ingestion tests 通过，隔离 Docker resources 已清理。
- `python3 -m compileall -q core modules adapters tests`：通过。
- `git diff --check`：通过。
- `python3 scripts/validate_regression_baseline.py --base-sha 697c6dbd5430a0c132a08f380f8ff56e77851eb3`：通过。
- `python3 scripts/validate_regression_baseline.py --base-sha 697c6dbd5430a0c132a08f380f8ff56e77851eb3 --all-files`：通过。
- `python3 scripts/validate_gpt_project_mechanism_sync.py --no-report`：通过。

## 5. 事实分级与剩余阻断

- **CONFIRMED（工程）**：P03-03 synthetic approval/publish/refresh contract 在任务分支本地验证通过；P03-02 candidate 只有通过人工 decision 后才形成隔离 synthetic approved version；correlation integrity、expiry state 与 logical scope key follow-up 本地专项验证通过。
- **CONFIRMED（工程边界）**：所有 external flags 保持 false；没有新增依赖、网络、数据库、CRM/support/video 实现、真实资料读取或外部执行接口。
- **PARTIAL（Git 完成）**：main integration（main 集成）尚未完成，仍等待 controller review（控制器审查）与集成决策。
- **BLOCKED / UNKNOWN（业务）**：真实 SKU、价格、库存、主体/资质、账号、收款、履约、TikTok 酒类边界、真实 approval actor/RBAC/RLS、production database 和任何外部业务动作仍未建立或未获书面证据。
