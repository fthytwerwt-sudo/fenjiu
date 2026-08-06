# P03-03｜审批、版本化发布与下游刷新报告

> **状态：task_branch_local_validation_passed_pending_remote_readback**
>
> **执行日期：** 2026-08-06
>
> **精确基线：** `origin/main` / local `HEAD` `8637f827d62e5e5e48af96f4c1d1725fc0ff097d`
>
> **任务分支：** `codex/p03-03-approval-publish-refresh`
>
> **范围边界：** 仅完成 stdlib、local-only、synthetic/value-free 的 approval request、human decision、immutable internal publication proof、supersede 与 internal invalidation outbox fake。P03-03 不创建 P02 `approved` truth，不导入 `modules.truth_center`，不使用 `DataState.APPROVED`，不可被 P02 current-truth consumer 当成真值；没有真实 reviewer 身份、真实业务资料、真实 approved truth、production DB/RBAC/RLS 或外部动作。

## 1. 结论

- 新增 `modules/ingestion/approval.py`，只消费 P03-02 quality-passed `MappedCandidate`；candidate 必须为 `MappingRunState.MAPPED`、`DataState.FIXTURE`、`is_synthetic=true`、`external_execution_allowed=false`、`business_external_ready=false`。
- `InMemoryApprovalRequestStore` 建立 request/decision append-only 版本：`pending -> approved/rejected/expired/revision_requested/conflict`；强制 evidence、policy、scope、actor、expiry、idempotency 与 audit；approve 自己的 request 会 fail closed。
- `SyntheticInternalPublicationLedger` 建立独立 internal publication proof：`approved_internal -> superseded_internal -> approved_internal`，只追加不覆盖/删除；它是 P03 本地合同证明，不是 P02 truth record。
- `InMemoryInvalidationOutbox` 只写 `TruthFactsChanged` internal invalidation event，destination 固定为 `internal_invalidation_outbox`；没有 external sync adapter。
- publish 只接受 approved request；pending/reject/expire/revise/conflict 均返回 `approval_request_not_publishable` 且不产生 publication/event。重跑同一 request/decision/publish 返回同一对象，不重复 request version、publication record 或 event。

## 2. 六层实现设计摘要

- 目标层：完成 synthetic approval/publish/refresh proof，不做真实资料、真实审批或外部执行。
- 机制层：request、decision、publication、supersede、event 全部绑定 scope、actor、policy、evidence、version 与 idempotency；reject/expire/conflict/revise/pending 不可 publish。
- 实现设计层：`primary_route=ApprovalRequestStore + SyntheticInternalPublicationLedger + InMemoryInvalidationOutbox`；`fallback_route=staging/review only with stable denial code`；`capability_status=synthetic value-free local-only proof, not P02 current truth`；`blocked_if_missing=quality-passed lineage, non-self reviewer, evidence, policy, scope match, atomic append/event`。
- 流程层：P03-02 mapped candidate -> approval request -> human decision envelope -> internal approved publication proof -> optional supersede -> internal invalidation event。
- 判断标准层：专项 E2E、负例、P02 boundary static assertion、ingestion/contracts/architecture/regression 全部通过才可提交；业务状态不升级。
- 反馈层：任何失败回到 candidate quality、scope/lineage、approval state、idempotency、append-only ledger、internal outbox 或 Git 验证，不放宽 P02 guards。

## 3. E2E 与负例证据

- `approval_to_immutable_internal_publication_and_invalidation_e2e`：pending request 不可 publish；approve 后生成 `approved_internal` publication proof 与 1 条 `TruthFactsChanged` internal invalidation event；记录保留 candidate payload hash、source/job/result/staging IDs、locator fingerprint、rule/profile lineage；safe summary 不回显 source hash。
- 安全 E2E correlation：`correlation_id=synthetic_correlation`；`request_id=99ad53e6-7f1b-50cd-9bf9-69c727522c88`；`decision_id=61e61f0e-d8ca-5160-8d63-8bfe901fc7f9`；`publication_id=18314648-aa2e-5c76-b5ce-3aed00b0fbfb`；`event_id=5286610e-5b93-57f4-b3a5-483e5279cc9d`；`request_versions=2`；`audit_events=2`；`publication_records=1`；`outbox_events=1`。
- `internal_publication_is_not_p02_current_truth`：P03 publication 成功后，P02 `TruthRepositoryContractHarness.probe_current(..., TruthEntityKind.APPROVED_FACT, ...)` 仍返回 `None`，且 `p02_current_truth_readable=false`。
- `rerun_does_not_duplicate_approval_request_publication_or_event`：同 request/decision/publish 重跑后 request versions = 2、publication records = 1、event = 1。
- `reject_expire_revise_conflict_and_pending_requests_never_publish`：reject、expire、revise、conflict 与 pending 全部不可 publish，publication/event 均为 0。
- `self_approval_expired_decision_and_policy_mismatch_fail_closed`：自我 approve、过期 approve、policy mismatch 分别 fail closed。
- `non_quality_cross_scope_or_real_like_candidates_are_rejected`：blocked/manual candidate、cross scope、external_execution_allowed forged candidate 均被拒绝。
- `supersede_appends_new_versions_and_refresh_event_without_external_sync`：replacement 会追加 `superseded_internal` + 新 `approved_internal`，并产生第二条 internal invalidation event；不外部同步。
- `approval_module_never_imports_or_emits_p02_approved_truth`：静态断言 approval module 不导入 `modules.truth_center`、不出现 `TruthVersion`、不使用 `DataState.APPROVED`。

## 4. 验证状态

- `python3 -m unittest tests.ingestion.test_approval_publish_and_refresh`：通过，9 项。
- `python3 -m unittest discover -s tests/ingestion`：通过，35 项。
- `python3 -m unittest discover -s tests/contracts`：通过，46 项。
- `python3 -m unittest discover -s tests/architecture`：通过，8 项。
- `make regression`：通过；P02 `0001` + `0002` migrations 连续 replay 两次、16 类 SQL negative constraints 通过；8 architecture + 14 regression + 8 local-runtime + 16 control-plane + 46 contracts + 35 ingestion，共 127 项 Python 测试通过；隔离 Docker resources 已清理。
- `python3 scripts/validate_regression_baseline.py --base-sha 8637f827d62e5e5e48af96f4c1d1725fc0ff097d`：通过。
- `python3 scripts/validate_regression_baseline.py --base-sha 8637f827d62e5e5e48af96f4c1d1725fc0ff097d --all-files`：通过。
- `python3 scripts/validate_gpt_project_mechanism_sync.py --no-report`：通过，23 files，system prompt 3613 chars。
- `python3 -m compileall -q core modules adapters tests`：通过。
- `find scripts tests -type f -name '*.sh' -exec sh -n {} +`：通过。
- `git diff --check`：通过。
- 静态边界扫描：`modules/ingestion/approval.py` 未命中 `modules.truth_center`、`TruthVersion`、`DataState.APPROVED`、外部 HTTP/SDK 或 external action flag；仅命中普通说明字符串 `approved requests`。
- Docker cleanup：`fenjiu-local-runtime-1735561601` containers、volumes、networks 均为 0 残留。
- remote push/readback 待提交后回填至最终执行回报。

## 5. 事实分级与剩余阻断

- **CONFIRMED（工程，本地）**：P03-03 synthetic approval/internal publication/invalidation 合同已通过专项、ingestion、contracts、architecture、完整 regression、P00 两种扫描、mechanism validation、compile/shell/diff 和 Docker cleanup 验证。
- **CONFIRMED（边界）**：P03-03 不创建 P02 approved truth；internal publication proof 不可作为 P02 current truth。
- **UNKNOWN / BLOCKED（业务）**：真实 reviewer 身份、真实 approval policy、SKU、价格、库存、资质、账号、收款、配送售后、TikTok 酒类边界仍未确认；外部发布、报价、收款、下单、履约仍关闭。
- **DEFER**：production DB、auth/RBAC/RLS、workflow runner、real approval identity、real supplier data onboarding、Phase 4 action policy。

## 6. P04-01 唯一安全入口

P04-01 只能从本卡的 internal proof / invalidation contract 读取“是否存在受控审批完成的本地模拟发布记录”这一工程信号；不得把它当作 P02 approved truth、真实业务事实或外部执行授权。Phase 4 若要运行 workflow checkpoint/recovery，必须继续保持 external flags false，并在独立 action policy/RBAC 合同通过前只允许 internal dry-run。
