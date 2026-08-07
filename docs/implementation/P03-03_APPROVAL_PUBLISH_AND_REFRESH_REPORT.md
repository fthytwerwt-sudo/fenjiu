# P03-03｜审批、版本化发布与下游刷新报告

> **状态：task_branch_validated_pending_git_completion**
>
> **执行日期：** 2026-08-08
>
> **精确工程基线：** `origin/main` `697c6dbd5430a0c132a08f380f8ff56e77851eb3`
>
> **任务分支：** `codex/p03-03-approval-publish-refresh-v2`
>
> **范围边界：** 仅完成 stdlib、local-only、synthetic/value-free 的 approval request、human decision、isolated approved synthetic truth version、supersede/revoke 与 internal refresh event 合同。本报告不证明真实供应链资料、P02 current truth、外部发布、CRM/support/video 实现、供应链确认、合规许可或业务外部执行成立。

## 1. 结论

- 新增 `modules/ingestion/approval.py`，实现 `SyntheticApprovalPublisher`（合成审批发布器）和不可变 synthetic approval/version/refresh/audit contracts。
- P03-03 的 `ApprovedSyntheticTruthVersion`（已批准合成真值版本）保持 `data_state=fixture`、`is_synthetic=true`、`external_execution_allowed=false`、`business_external_ready=false`；它不复用、不导入、不写入 P02 `modules/truth_center` current-read path。
- 成功链路为：P03-02 `MappedCandidate` + `MappingReport` → `ReviewRequestCommand` → `HumanDecisionCommand` → immutable approved synthetic version → `TruthFactsChanged` internal invalidation event。
- 支持 `approve`、`reject`、`revise`、`supersede` 和 `revoke`；每个决定记录 actor reference、时间、policy/evidence reference、correlation、P03-02 mapping report/profile fingerprint 和 source/job/result/staging lineage。
- `TruthFactsChanged` 只枚举未来消费者 `customer_service`、`content_video`、`crm`，语义仅为 internal invalidation，不实现或调用这些模块。

## 2. Fail-closed 合同

| 场景 | 稳定行为 |
|---|---|
| 缺 P03-02 source/evidence lineage | `mapping_evidence_required`，不创建 request/version/refresh |
| P03-02 quality 未通过 | `quality_not_passed`，不发布 |
| request 过期 | `approval_request_expired`，不追加 decision/version/refresh |
| 跨 business line/scope | `cross_scope_forbidden` |
| 高风险 self approval | `self_approval_forbidden` |
| 已存在 current version 但未走 supersede | `publication_supersede_required` |
| requested version 与 current chain 冲突 | `version_conflict` |
| 同 idempotency key 不同 payload | `idempotency_conflict` |
| terminal request 再决策 | `duplicate_decision` |
| sensitive actor/idempotency/correlation metadata | `sensitive_metadata_forbidden` |

失败路径在提交前完成所有校验，失败后 `snapshot_counts()` 不变化，避免半成品 request decision、version 或 refresh 记录。

## 3. 下游读取与隔离

- `current(scope, fact_type, subject_ref)` 只返回当前有效的 `SyntheticTruthStatus.APPROVED` synthetic version。
- P03-02 candidate、pending request、rejected/revised/expired/conflict 路径、superseded version 和 revoked version 均不能通过 downstream read 读取。
- `supersede` 与 `revoke` 不删除、不覆写历史 version；旧版状态由 append-only status overlay 和 refresh invalidation 记录表达。
- P02 SQL negative constraints 仍证明 synthetic fixture 不能成为 P02 `DataState.APPROVED`；P03-03 没有削弱该限制。

## 4. Test-first 与验证证据

- **RED**：首次运行 `python3 -m unittest tests.ingestion.test_approval_publish_and_refresh` 因 `ModuleNotFoundError: No module named 'modules.ingestion.approval'` 失败。
- **GREEN**：新增最小 implementation 后，P03-03 专项测试通过；自审新增 audit sequence/idempotency conflict 回归，先复现失败，再修复通过。
- `python3 -m unittest tests.ingestion.test_approval_publish_and_refresh`：7 项通过。
- `python3 -m unittest discover -s tests/ingestion`：33 项通过。
- `make regression`：通过；P02 migrations replay 两次、16 类 SQL negative constraints 通过，8 architecture + 14 regression + 8 local-runtime + 16 control-plane + 46 contracts + 33 ingestion tests 通过，隔离 Docker resources 已清理。
- `python3 -m compileall -q core modules adapters tests`：通过。
- `git diff --check`：通过。
- `python3 scripts/validate_regression_baseline.py --base-sha 697c6dbd5430a0c132a08f380f8ff56e77851eb3`：通过。
- `python3 scripts/validate_regression_baseline.py --base-sha 697c6dbd5430a0c132a08f380f8ff56e77851eb3 --all-files`：通过。
- `python3 scripts/validate_gpt_project_mechanism_sync.py --no-report`：通过。

## 5. 事实分级与剩余阻断

- **CONFIRMED（工程）**：P03-03 synthetic approval/publish/refresh contract 在任务分支本地验证通过；P03-02 candidate 只有通过人工 decision 后才形成隔离 synthetic approved version。
- **CONFIRMED（工程边界）**：所有 external flags 保持 false；没有新增依赖、网络、数据库、CRM/support/video 实现、真实资料读取或外部执行接口。
- **PARTIAL（Git 完成）**：本文写入时 commit/push/remote readback 尚未完成；以最终执行回报为准。
- **BLOCKED / UNKNOWN（业务）**：真实 SKU、价格、库存、主体/资质、账号、收款、履约、TikTok 酒类边界、真实 approval actor/RBAC/RLS、production database 和任何外部业务动作仍未建立或未获书面证据。
