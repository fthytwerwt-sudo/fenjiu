# P03-03｜审批、版本化发布与下游刷新报告

> **状态：task_branch_repair_remote_readback_verified_not_main**
>
> **执行日期：** 2026-08-06
>
> **精确基线：** `origin/main` / task worktree base `8637f827d62e5e5e48af96f4c1d1725fc0ff097d`
>
> **任务分支：** `codex/p03-03-approval-publish-refresh`
>
> **初始分支复审结果：** `CHANGES_REQUIRED`。初始提交 `8f2914844894a0a6bd721d640b99678a89c82e4d` 被拒，原因包括 quality/mapping provenance 可伪造、publisher 可绕过 canonical decision/audit、publish 未复查 expiry、ledger/outbox 非原子、缺 revoke contract，以及 P02 boundary assertion 不充分。
>
> **本轮 repair commit / remote readback：** 不在本文件中构造自引用提交号；以最终执行回报中的 pushed commit、remote HEAD 与核心文件 SHA-256 为准。
>
> **范围边界：** 仅完成 stdlib、local-only、synthetic/value-free 的 approval request、human decision envelope、immutable simulated/internal publication record、supersede/revoke 与 internal invalidation outbox fake。P03-03 不创建 P02 `TruthVersion`，不导入 `modules.truth_center`，不使用 `DataState.APPROVED`，不可被 P02 current-truth consumer 当成真值；没有真实 reviewer 身份、真实业务资料、真实 approved truth、production DB/auth/RBAC/RLS 或外部动作。

## 1. 结论

- `CanonicalMappingCandidateGate` 现在是 request 入口的 fail-closed 本地权威链：只接受已登记 canonical mapping profile、零 findings、`report.state=MAPPED` 的 canonical `MappingReport` candidate；并从 `InMemoryIngestionStore` 回读实际存在且 registered/staged 的 source/job/result/staging records 后重放 P03-02 report。
- request creation 只接受 gate 返回的 `CanonicalMappedCandidate`，绑定 report run/profile fingerprint、candidate fingerprint、scope、source/job/result/staging lineage、locator、rule/profile lineage 与 synthetic/no-external markers；replaced object、blocked report、mapping conflict、cross-scope、profile/report drift 全部拒绝。
- `SyntheticReviewerCapabilityRegistry` 是明确的 synthetic local reviewer-capability registry，不是 production auth/RBAC。grant 绑定 canonical actor、role=`data_reviewer`、scope、policy、evidence、issued/expiry window；decision 必须引用未过期且匹配 scope/policy/role 的 grant。
- publisher 不再信任任意 `state=APPROVED` object；它必须通过 `InMemoryApprovalRequestStore.assert_publishable_request()` 回读 canonical current decision、decision audit、request version、reviewer grant、policy/evidence，并在 publish 时再次检查 request 未过期。
- `SyntheticInternalPublicationLedger` 只写独立 immutable internal publication proof：`approved_internal`、`superseded_internal`、`revoked_internal`。更正只追加 supersede/revoke，不 overwrite/delete。
- `SyntheticPublicationTransactionLog` 与 ledger/outbox snapshot/restore 形成本地 atomic publication transaction：ledger + internal outbox + idempotency result 全成功或全不变；同一 shared transaction state 下跨 publisher 新实例重跑返回原 publication/event。

## 2. 六层实现设计摘要

- 目标层：修复 P03-03 synthetic approval/publish/refresh contract，使它能证明受控内部发布闭环，但不做真实审批、真实资料导入、P02 approved truth 或外部执行。
- 机制层：request、decision、expiry、revise、publish、supersede、revoke 均强制 evidence、policy、scope、actor capability、version、audit 与 idempotency；reject/expire/conflict/revise/pending 绝不能 publish。
- 实现设计层：`primary_route=CanonicalMappingCandidateGate + ApprovalRequestStore + SyntheticReviewerCapabilityRegistry + SyntheticInternalPublicationLedger + SyntheticPublicationTransactionLog + internal invalidation outbox`；`fallback_route=staging/review only with stable denial code`；`capability_status=synthetic value-free local-only proof, not P02 current truth`；`blocked_if_missing=quality-passed canonical lineage, registered profile, non-self reviewer grant, evidence, policy, scope match, atomic ledger/outbox commit`。
- 流程层：P03-01 registered/staged lineage -> P03-02 mapped zero-finding report -> canonical candidate gate -> approval request -> synthetic local human decision capability -> internal publication proof -> supersede/revoke -> internal invalidation event。
- 判断标准层：专项 E2E、A-F exploit regressions、P02 import/API boundary、ingestion/contracts/architecture、P00 scans、mechanism validation、compile/shell/diff 与 full regression 通过；业务状态不升级。
- 反馈层：任何失败回到 canonical chain、reviewer capability、request store, transaction atomicity、P02 boundary 或 Git readback；不得放宽 P02 guards 或把 synthetic fixture 伪装为 real approved truth。

## 3. 复审 findings 修复映射

| Finding | 修复 |
|---|---|
| HIGH A quality/mapping provenance 可伪造 | request 入口改为 `CanonicalMappingCandidateGate`。必须先登记 canonical profile fingerprint；report 必须 `MAPPED` 且 zero findings；gate 从 `InMemoryIngestionStore` 回读 registered source、staged job/result/candidate 后用 P03-02 engine replay；forged/replaced candidate、blocked/conflict report、cross-scope、profile/report drift 均 fail closed。 |
| HIGH B publisher 可绕过 decision/audit/职责分离 | `SyntheticApprovalPublisher` 依赖 request store 的 canonical current request 与 decision audit；fake approved request 被拒。decision 必须引用 `SyntheticReviewerCapabilityRegistry` 的未过期 `data_reviewer` grant；self-approval 用 canonical actor identity 判断。 |
| HIGH C expiration | `assert_publishable_request()` 在 publish 时再次检查 `now <= expires_at`，稳定错误码为 `approval_request_expired_at_publish`。 |
| HIGH D ledger/outbox 非原子 | `_commit_transaction()` 先 snapshot ledger/outbox，再 append batch + outbox + transaction log；异常时 restore，保证失败后 0 new record / 0 new event。shared `SyntheticPublicationTransactionLog` 支持 publisher 新实例重跑返回原结果。 |
| MEDIUM E revoke | 增加 append-only `revoked_internal` record 与 internal invalidation event；revoke 需要 reviewer grant、policy、evidence、idempotency，不删除历史、不外部同步。 |
| MEDIUM F P02 boundary test | 增加 AST import/API assertion：approval module 不导入 `modules.truth_center`、不引用 `TruthVersion`、不产生 `DataState.APPROVED`；并用真实 P02 contract harness 证明 internal publication object 不能进入 current-truth path。 |

## 4. E2E 与 exploit 证据

- Approval E2E correlation：`correlation_id=synthetic_correlation`；approve 后生成 `approved_internal` publication proof 与 `TruthFactsChanged` event；record 保留 source/job/result/staging IDs、locator fingerprint、rule/profile lineage；`p02_current_truth_readable=false`、`external_execution_allowed=false`、`business_external_ready=false`。
- P02 boundary：`TruthRepositoryContractHarness.probe_current(...APPROVED_FACT...)` 对 P03 internal publication 返回 `None`；直接 append internal publication object 返回 `truth_version_required`，证明它不是 P02 truth contract object。
- Reject/expired/revise/conflict/pending：均返回 `approval_request_not_publishable`，publication/event 计数保持 0。
- Manual exploit probe：`A.blocked_report=canonical_mapping_report_required`、`A.forged_candidate=canonical_candidate_required`、`A.forged_profile=mapping_profile_fingerprint_mismatch`。
- Manual exploit probe：`B.fake_approved_publish=approval_request_not_canonical`、`B.self_approval=self_approval_forbidden`。
- Manual exploit probe：`C.late_publish=approval_request_expired_at_publish`。
- Manual exploit probe：`D.forced_outbox_failure=forced_outbox_failure` 后 `ledger=0`、`failing_outbox=0`；重试成功后 `ledger=1`、`outbox=1`。
- Manual exploit probe：restart idempotency `same=True`，共享 transaction state 下 publisher 新实例不重复 publication/event。
- Manual exploit probe：revoke replay `same=True`、state=`revoked_internal`，ledger/outbox 只追加内部记录与内部 event。

## 5. 验证命令与结果

- `python3 -m unittest tests.ingestion.test_approval_publish_and_refresh`：通过，16 项。
- `python3 -m unittest discover -s tests/ingestion`：通过，42 项。
- `python3 -m unittest discover -s tests/contracts`：通过，46 项。
- `python3 -m unittest discover -s tests/architecture`：通过，8 项。
- Manual exploit probe（A-D、restart idempotency、revoke）：通过，稳定错误码与计数见第 4 节。
- `python3 scripts/validate_regression_baseline.py --base-sha 8637f827d62e5e5e48af96f4c1d1725fc0ff097d`：通过。
- `python3 scripts/validate_regression_baseline.py --base-sha 8637f827d62e5e5e48af96f4c1d1725fc0ff097d --all-files`：通过。
- `python3 scripts/validate_gpt_project_mechanism_sync.py --no-report`：通过，23 files，system prompt 3613 chars。
- `python3 -m compileall -q core modules adapters tests`：通过。
- `find scripts tests -type f -name '*.sh' -exec sh -n {} +`：通过。
- `git diff --check`：通过。
- `make regression`：通过；P02 `0001` + `0002` migrations 连续 replay 两次、16 类 SQL negative constraints 通过；8 architecture + 14 regression + 8 local-runtime + 16 control-plane + 46 contracts + 42 ingestion，共 134 项 Python tests 通过；隔离 Docker resources 已清理。
- Docker cleanup readback：Compose project `fenjiu-local-runtime-1735561601` containers=0、volumes=0、networks=0。

## 6. 实际改动文件

- `modules/ingestion/approval.py`：新增/重做 canonical candidate gate、synthetic reviewer capability registry、approval request/audit state machine、internal publication ledger/outbox、shared transaction log、supersede/revoke 与 atomic commit。
- `tests/ingestion/test_approval_publish_and_refresh.py`：扩展 approval/invalidation E2E、A-F regression/exploit tests、transaction failure injection、restart idempotency、revoke、P02 AST/API boundary、value leakage/no-external-action 负例。
- `docs/implementation/P03-03_APPROVAL_PUBLISH_AND_REFRESH_REPORT.md`：记录初始分支被拒、repair 设计、证据与验证结果。
- `docs/implementation/P03-03_APPROVAL_PUBLISH_AND_REFRESH_HANDOFF.md`：保持 P03-03 synthetic/internal 边界与 repair handoff。

## 7. 事实分级与剩余阻断

- **CONFIRMED（工程）**：P03-03 synthetic/value-free/local-only approval -> decision -> immutable internal publication -> supersede/revoke -> internal invalidation contract 已通过专项、相邻套件、manual exploit probe、P00 scans、mechanism validation、compile/shell/diff、full regression 与 Docker cleanup。
- **CONFIRMED（边界）**：本模块只产生独立 immutable simulated/internal publication record，不创建或读取 P02 approved truth；P02 current-truth consumer 不能把该对象当作真值。
- **部分成立（角色能力）**：`SyntheticReviewerCapabilityRegistry` 只证明 local synthetic reviewer-capability contract，可用于测试职责分离、scope/policy/evidence/expiry；它不是真实认证、真实 reviewer identity、production RBAC 或人工审批系统。
- **UNKNOWN / BLOCKED（业务）**：真实 reviewer 身份、真实 approval policy、SKU、价格、库存、资质、账号、收款、配送售后、TikTok 酒类边界仍未确认；外部发布、报价、收款、下单、履约仍关闭。
- **DEFER**：production DB、auth/RBAC/RLS、workflow runner、real approval identity、real supplier data onboarding、Phase 4 action policy。

## 8. Rollback 与 P04-01 安全入口

- Rollback：回退本任务分支 repair commit 即可移除 P03-03 approval module/report/test 改动；不会删除真实业务资料、真实 truth 或外部状态，因为本卡没有创建它们。
- P04-01 唯一安全入口：只可读取 P03-03 的 internal proof / invalidation contract 作为“synthetic local approval flow completed”工程信号；不得把它当作 P02 approved truth、真实业务事实、真实人工批准或外部执行授权。Phase 4 若要运行 workflow checkpoint/recovery，必须保持 external flags false，并在独立 action policy/RBAC 合同通过前只允许 internal dry-run。
