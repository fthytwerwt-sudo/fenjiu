# P03-03｜审批、版本化发布与下游刷新报告

> **状态：task_branch_third_repair_remote_readback_verified_not_main**
>
> **执行日期：** 2026-08-06
>
> **精确基线：** `origin/main` / task worktree base `8637f827d62e5e5e48af96f4c1d1725fc0ff097d`
>
> **任务分支：** `codex/p03-03-approval-publish-refresh`
>
> **初始与第二轮复审结果：** 初始提交 `8f2914844894a0a6bd721d640b99678a89c82e4d` 被标记 `CHANGES_REQUIRED`；第二轮 repair 提交 `074807b21fc215e4d28d21e524200c5029d70643` 仍被 5.6 独立审查标记 `CHANGES_REQUIRED`，不得作为可接受完成态引用。
>
> **本轮 third repair commit / remote readback：** 不在本文件中构造自引用提交号；以最终执行回报中的 pushed commit、remote HEAD 与核心文件 SHA-256 为准。
>
> **范围边界：** 仅完成 stdlib、local-only、synthetic/value-free 的 approval request、human decision envelope、immutable simulated/internal publication record、supersede/revoke/successor 与 internal invalidation outbox fake。P03-03 不创建 P02 `TruthVersion`，不导入 `modules.truth_center`，不使用 `DataState.APPROVED`，不可被 P02 current-truth consumer 当成真值；没有真实 reviewer 身份、真实业务资料、真实 approved truth、production DB/auth/RBAC/RLS、process/DB crash proof 或外部动作。

## 1. 结论

- 第三轮 repair 将 registry/store/ledger/outbox/transaction log 的入口和返回值全部改为 defensive deep snapshot；公开返回对象被 `object.__setattr__` 原地篡改后，不能污染内部 canonical state。
- `CanonicalMappingCandidateGate` 每次 `assert_canonical()` 都重新验证 supplied candidate typed invariants、stored snapshot typed invariants、stored canonical fingerprint 与 supplied object equality；candidate/source/locator/profile/report drift 均 fail closed。
- `SyntheticReviewerCapabilityRegistry` 存储 grant snapshot，并为完整 scope、canonical actor、role、policy、evidence、issued/expiry window 与 safety flags 建立 grant fingerprint；公开 grant snapshot 的 actor drift 不再改变 decision/audit/publication actor。
- `InMemoryApprovalRequestStore` 为 request version 和 audit event 保存完整 state fingerprint；publisher 只从 store 内部 snapshot 读取 canonical current approved decision，并要求 supplied request 与 stored snapshot 完整一致。
- `SyntheticInternalPublicationLedger` 与 `InMemoryInvalidationOutbox` 不再暴露 public `snapshot` / `restore` / `recover` mutation surface；事务协调只使用私有 snapshot implementation，正常业务路径不能清空或替换 append-only history。
- `SyntheticPublicationTransactionLog` 纳入同一个 atomic transaction rollback 域。ledger/outbox/log 任一阶段失败，ledger、outbox、transaction log 都回到先前 snapshot；retry 产生 exactly one internal record/event/log result。
- `InternalInvalidationEvent.fingerprint` 现在绑定 full scope tenant/project/business/correlation、publication/ref、event type、destination、subject、target、version、occurred_at、superseded/revoked refs 与 safety flags；same-id poison event 会 fail closed，publisher 也验证 outbox append return 必须等于 expected event。
- `REVOKED_INTERNAL` 保持 append-only 历史；新的独立 approved request 可在当前 revoked head 上追加新的 `approved_internal` successor/event，不 mutation/deletion resurrect。

## 2. 六层实现设计摘要

- 目标层：修复第二轮遗漏的 mutable shared-reference、phantom transaction、public rollback、poison outbox 与 revoked successor 漏洞；仍只证明 synthetic/internal approval publish contract。
- 机制层：所有 canonical 对象、reviewer grant、request/audit、publication/event、transaction result 均以 snapshot + deterministic fingerprint 保护；reject/expire/conflict/revise/pending 绝不 publish。
- 实现设计层：`primary_route=defensive snapshots + canonical fingerprints + private transaction snapshots + internal invalidation outbox`；`fallback_route=stable denial code, no ledger/outbox/log write`；`capability_status=synthetic value-free local-only proof, not P02 current truth`；`blocked_if_missing=canonical P03 lineage, reviewer capability, request/audit integrity, atomic ledger/outbox/log commit`。
- 流程层：P03-01 registered/staged lineage -> P03-02 zero-finding mapped report -> canonical snapshot gate -> approval request snapshot -> synthetic reviewer decision snapshot -> internal publication transaction -> supersede/revoke/successor -> internal invalidation event。
- 判断标准层：先写红灯 regressions 并确认第二轮实现失败；修复后 P03 suite、ingestion/contracts/architecture、manual exploit probes、P00 scans、mechanism validation、compile/shell/diff、full regression 和 Docker cleanup 通过；业务状态不升级。
- 反馈层：失败回到 defensive snapshot、fingerprint integrity、transaction atomicity、append-only surface、event canonicalization、revoked successor 或 P02 boundary；不得把 synthetic fixture 改写成 real approved truth。

## 3. 第三轮 findings 修复映射

| Finding | 修复 |
|---|---|
| HIGH 1 shared object mutation bypasses gate | `register_profile()`、`register_report()`、`assert_canonical()` 均 deep snapshot；stored canonical candidate 和 returned candidate 分离；candidate source/locator/report nested mutation 被 `canonical_candidate_required` 拒绝且 ledger/outbox=0。 |
| HIGH 2 grant/request shared reference drift | grant/request/audit 均 snapshot + full fingerprint；公开 grant actor mutation 不再改变 canonical decision actor；公开 approved request subject mutation 以 `approval_request_not_canonical` 拒绝，publication record mutation 以 `internal_publication_not_found` 拒绝。 |
| HIGH 3 transaction log not rolled back | `_commit_transaction()` 同时 snapshot ledger/outbox/transaction log；log post-write failure 后三者全部恢复，retry 生成 exactly one record/event。 |
| HIGH 4 public restore clears append-only history | ledger/outbox public `snapshot`/`restore` 被封闭为 private implementation；store/ledger/outbox/transaction log public API 断言无 `snapshot`、`restore`、`recover`、`clear`、`replace`。 |
| HIGH 5 event fingerprint and outbox canonical return | event fingerprint 绑定 full scope/correlation/occurred_at/safety flags；same-id poison event 拒绝，publisher 验证 append return 与 expected event 完全一致，失败时 ledger/log rollback。 |
| MEDIUM revoke successor | `publish(..., supersedes=...)` 接受 current `InternalRevocationResult` / `REVOKED_INTERNAL` record；新独立 approval 可追加 successor，旧 approved result 在 revoke 后仍被 `superseded_publication_not_current` 拒绝。 |

第二轮已修复的 blocked/conflict report、copy-forged candidate、profile drift、fake request、exact self-approval、expiry、pre-log outbox failure、restart replay、P02 boundary/no-external-action regressions 保留并继续通过。

## 4. E2E 与 exploit 证据

- 红灯证据：第三轮新增 regression 在第二轮提交 `074807b...` 下失败：candidate mutation 未拒绝、profile returned object 污染 registry、grant actor 漂移为 `system_worker_alias`、log phantom retry ledger/outbox=0、public `snapshot/restore` 暴露、poison same-id event 被接受、revoked successor 被拒。
- 修复后 P03 suite：`python3 -m unittest tests.ingestion.test_approval_publish_and_refresh` 通过 23 项。
- Manual exploit probe：`H1.candidate_source_mutation=canonical_candidate_required`，`ledger=0 outbox=0`。
- Manual exploit probe：`H1.locator_mutation=canonical_candidate_required`，`ledger=0 outbox=0`。
- Manual exploit probe：`H1.profile_return_snapshot_ok`，mutating returned profile snapshot 不污染 canonical registry。
- Manual exploit probe：`H2.grant_mutation_actor=human_reviewer`，公开 grant mutation 不改变 canonical actor；`H2.request_subject_mutation=approval_request_not_canonical`，`ledger=0 outbox=0`。
- Manual exploit probe：`H3.log_post_write_failure=forced_log_post_write_failure` 后 `ledger=0 outbox=0`；retry 成功后 `ledger=1 outbox=1`。
- Manual exploit probe：`H4.public_mutating_restore_surface_present=False`。
- Manual exploit probe：`H5.poisoned_same_id_event=invalidation_event_idempotency_conflict`，`ledger=0 outbox=1`，即 pre-existing poison 保持但新 publish 无半写入。
- Manual exploit probe：`M.reuse_old_approved_after_revoke=superseded_publication_not_current`；revoked successor 追加成功，`ledger=3 outbox=3`。

## 5. 验证命令与结果

- `python3 -m unittest tests.ingestion.test_approval_publish_and_refresh`：通过，23 项。
- `python3 -m unittest discover -s tests/ingestion`：通过，49 项。
- `python3 -m unittest discover -s tests/contracts`：通过，46 项。
- `python3 -m unittest discover -s tests/architecture`：通过，8 项。
- Manual exploit probe（HIGH 1-5、revoke successor、legacy A-F 保留路径）：通过，稳定错误码与计数见第 4 节。
- `python3 scripts/validate_regression_baseline.py --base-sha 8637f827d62e5e5e48af96f4c1d1725fc0ff097d`：通过。
- `python3 scripts/validate_regression_baseline.py --base-sha 8637f827d62e5e5e48af96f4c1d1725fc0ff097d --all-files`：通过。
- `python3 scripts/validate_gpt_project_mechanism_sync.py --no-report`：通过，23 files，system prompt 3613 chars。
- `python3 -m compileall -q core modules adapters tests`：通过。
- `find scripts tests -type f -name '*.sh' -exec sh -n {} +`：通过。
- `git diff --check`：通过。
- `make regression`：通过；P02 `0001` + `0002` migrations 连续 replay 两次、16 类 SQL negative constraints 通过；8 architecture + 14 regression + 8 local-runtime + 16 control-plane + 46 contracts + 49 ingestion，共 141 项 Python tests 通过；隔离 Docker resources 已清理。
- Docker cleanup readback：Compose project `fenjiu-local-runtime-1735561601` containers=0、volumes=0、networks=0。

## 6. 实际改动文件

- `modules/ingestion/approval.py`：defensive snapshot/fingerprint integrity、private transaction snapshots、atomic ledger/outbox/log rollback、full event fingerprint、outbox canonical return validation、no public restore surface、revoked successor publish support。
- `tests/ingestion/test_approval_publish_and_refresh.py`：新增第三轮 exploit regressions，覆盖 candidate/profile/report/lineage mutation、grant/request/publication drift、transaction log post-write failure、public restore API、poison event、revoked successor，并保留旧 A-F regressions。
- `docs/implementation/P03-03_APPROVAL_PUBLISH_AND_REFRESH_REPORT.md`：记录第二轮 `074807b` 被拒、第三轮 repair 设计、红灯证据和验证结果。
- `docs/implementation/P03-03_APPROVAL_PUBLISH_AND_REFRESH_HANDOFF.md`：补第三轮 repair note 与 synthetic/internal/P02 边界。

## 7. 事实分级与剩余阻断

- **CONFIRMED（工程）**：P03-03 synthetic/value-free/local-only approval -> decision -> immutable internal publication -> supersede/revoke/successor -> internal invalidation contract 已通过专项、相邻套件、manual exploit probe、P00 scans、mechanism validation、compile/shell/diff、full regression 与 Docker cleanup。
- **CONFIRMED（边界）**：本模块只产生独立 immutable simulated/internal publication record，不创建或读取 P02 approved truth；P02 current-truth consumer 不能把该对象当作真值。
- **部分成立（角色能力）**：`SyntheticReviewerCapabilityRegistry` 只证明 local synthetic reviewer-capability contract，可用于测试职责分离、scope/policy/evidence/expiry；它不是真实认证、真实 reviewer identity、production RBAC 或人工审批系统。
- **部分成立（原子性）**：本卡证明的是单进程内存对象的 local atomic contract，不是 process crash、database crash、distributed transaction 或 production durability proof。
- **UNKNOWN / BLOCKED（业务）**：真实 reviewer 身份、真实 approval policy、SKU、价格、库存、资质、账号、收款、配送售后、TikTok 酒类边界仍未确认；外部发布、报价、收款、下单、履约仍关闭。
- **DEFER**：production DB、auth/RBAC/RLS、workflow runner、real approval identity、real supplier data onboarding、Phase 4 action policy。

## 8. Rollback 与 P04-01 安全入口

- Rollback：回退本任务分支 third repair commit 即可移除本轮 P03-03 approval module/report/test 改动；不会删除真实业务资料、真实 truth 或外部状态，因为本卡没有创建它们。
- P04-01 唯一安全入口：只可读取 P03-03 的 internal proof / invalidation contract 作为“synthetic local approval flow completed”工程信号；不得把它当作 P02 approved truth、真实业务事实、真实人工批准或外部执行授权。Phase 4 若要运行 workflow checkpoint/recovery，必须保持 external flags false，并在独立 action policy/RBAC 合同通过前只允许 internal dry-run。
