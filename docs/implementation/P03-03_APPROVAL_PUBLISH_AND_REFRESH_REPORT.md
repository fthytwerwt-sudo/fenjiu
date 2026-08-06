# P03-03｜审批、版本化发布与下游刷新报告

> **状态：task_branch_fifth_repair_remote_readback_verified_not_main**
>
> **执行日期：** 2026-08-06
>
> **精确基线：** `origin/main` / task worktree base `8637f827d62e5e5e48af96f4c1d1725fc0ff097d`
>
> **任务分支：** `codex/p03-03-approval-publish-refresh`
>
> **历轮复审结果：** 初始提交 `8f2914844894a0a6bd721d640b99678a89c82e4d`、第二轮 repair `074807b21fc215e4d28d21e524200c5029d70643`、第三轮 repair `918cc8954988f6f723891d2c7989366cee9e692f`、第四轮 repair `c87ec0a817a158900bd8b245f045822139c3175a` 均被 5.6 只读复审标记 `CHANGES_REQUIRED`，不得作为可接受完成态引用。
>
> **本轮 fifth repair commit / remote readback：** 不在本文件中构造自引用提交号；以最终执行回报中的 pushed commit、remote HEAD 与核心文件 SHA-256 为准。
>
> **范围边界：** 仅完成 stdlib、local-only、synthetic/value-free 的 approval request、human decision envelope、immutable simulated/internal publication record、supersede/revoke/successor 与 internal invalidation outbox fake。P03-03 不创建 P02 `TruthVersion`，不导入 `modules.truth_center`，不使用 `DataState.APPROVED`，不可被 P02 current-truth consumer 当成真值；没有真实 reviewer 身份、真实业务资料、真实 approved truth、production DB/auth/RBAC/RLS、process/DB crash proof 或外部动作。

## 1. 结论

- 第五轮 repair 在第四轮基础上继续封闭 authority storage：ledger/outbox/transaction-log 的权威状态只存在于闭包内，公开导出的实例没有 `__dict__`、没有 public/private append/commit/get/snapshot/restore 方法、没有可变 state map，类方法默认参数和模块 helper 也不再泄露写 capability。
- `publish()`/`revoke()` 对精确同 key 的已提交 transaction 先做 full validation replay，再进入当前 expiry/grant/current-head freshness 检查；已提交重放在 request/grant 过期后仍返回原完全等值 result，新操作仍按 `approval_request_expired_at_publish` 或 `reviewer_capability_expired` fail closed。
- committed-result validation 现在绑定 request/candidate id、payload/source lineage、locator/profile/rule、scope/subject/target/version、publication timestamps、record/event full semantic equality；root replay 也强制 `version_no=1`，不能只靠 transaction fingerprint。
- 第四轮 repair 已移除 public write surfaces：`SyntheticInternalPublicationLedger.append_batch()`、`InMemoryInvalidationOutbox.append()`、`SyntheticPublicationTransactionLog.commit()` 不再作为公开写入口存在，外部调用者不能直接制造 publication/event 或预置 transaction result。
- transaction log replay 现在必须回读 ledger/outbox 中已落地的 canonical records/event；只有 log、没有 ledger/outbox 的 phantom result 以 `publication_transaction_incomplete` fail closed。
- `publish(..., supersedes=revocation_result)` 要求新的独立 canonical request、decision 和 audit；revoke 后复用原 request/decision 会以 `revoked_successor_requires_new_approval` 拒绝。
- 普通 supersede 与 revoke-successor 的同 key 重放先查询并验证已提交 transaction，再做 current-head lifecycle check；合法 replay 返回原完全等值 result，不再误报 `superseded_publication_not_current`。
- 第三轮 repair 已将 registry/store/ledger/outbox/transaction log 的入口和返回值改为 defensive deep snapshot；公开返回对象被 `object.__setattr__` 原地篡改后，不能污染内部 canonical state。
- `CanonicalMappingCandidateGate` 每次 `assert_canonical()` 都重新验证 supplied candidate typed invariants、stored snapshot typed invariants、stored canonical fingerprint 与 supplied object equality；candidate/source/locator/profile/report drift 均 fail closed。
- `SyntheticReviewerCapabilityRegistry` 存储 grant snapshot，并为完整 scope、canonical actor、role、policy、evidence、issued/expiry window 与 safety flags 建立 grant fingerprint；公开 grant snapshot 的 actor drift 不再改变 decision/audit/publication actor。
- `InMemoryApprovalRequestStore` 为 request version 和 audit event 保存完整 state fingerprint；publisher 只从 store 内部 snapshot 读取 canonical current approved decision，并要求 supplied request 与 stored snapshot 完整一致。
- `SyntheticInternalPublicationLedger` 与 `InMemoryInvalidationOutbox` 不再暴露 public `snapshot` / `restore` / `recover` / `append` mutation surface；事务协调只使用私有 snapshot implementation，正常业务路径不能清空、替换或注入 append-only history。
- `SyntheticPublicationTransactionLog` 纳入同一个 atomic transaction rollback 域。ledger/outbox/log 任一阶段失败，ledger、outbox、transaction log 都回到先前 snapshot；retry 产生 exactly one internal record/event/log result。
- `InternalInvalidationEvent.fingerprint` 现在绑定 full scope tenant/project/business/correlation、publication/ref、event type、destination、subject、target、version、occurred_at、superseded/revoked refs 与 safety flags；same-id poison event 会 fail closed，publisher 也验证 outbox append return 必须等于 expected event。
- `REVOKED_INTERNAL` 保持 append-only 历史；新的独立 approved request 可在当前 revoked head 上追加新的 `approved_internal` successor/event，不 mutation/deletion resurrect。

## 2. 六层实现设计摘要

- 目标层：修复第四轮遗漏的 underscore/private-method 可调用、mutable map 可写、helper 默认参数泄露、partial replay validation 与 expiry-before-replay 幂等漏洞；仍只证明 synthetic/internal approval publish contract。
- 机制层：所有 canonical 对象、reviewer grant、request/audit、publication/event、transaction result 均以 snapshot + deterministic fingerprint 保护；公开导出对象只提供读面，不能持有或取得 authoritative write store；reject/expire/conflict/revise/pending 绝不 publish。
- 实现设计层：`primary_route=defensive snapshots + canonical fingerprints + closure-owned publication state + full committed-result validation + atomic ledger/outbox/log transaction + internal invalidation outbox`；`fallback_route=stable denial code, no ledger/outbox/log write`；`capability_status=synthetic value-free local-only proof, not P02 current truth`；`blocked_if_missing=canonical P03 lineage, reviewer capability, request/audit integrity, atomic ledger/outbox/log commit`。
- 流程层：P03-01 registered/staged lineage -> P03-02 zero-finding mapped report -> canonical snapshot gate -> approval request snapshot -> synthetic reviewer decision snapshot -> internal publication transaction -> supersede/revoke/successor -> internal invalidation event。
- 判断标准层：先写第五轮红灯 regressions 并确认第四轮实现失败；修复后 P03 suite、ingestion/contracts/architecture、manual exploit probes、P00 scans、mechanism validation、compile/shell/diff、full regression 和 Docker cleanup 通过；业务状态不升级。
- 反馈层：失败回到 authority storage 封装、full committed-result validation、committed replay ordering、revoke successor independence、defensive snapshot、fingerprint integrity、transaction atomicity、event canonicalization 或 P02 boundary；不得把 synthetic fixture 改写成 real approved truth。

## 3. 第三、四、五轮 findings 修复映射

### 第五轮

| Finding | 修复 |
|---|---|
| HIGH 1 underscore 不是安全边界，导出的 ledger/outbox/log 仍可调 private write 方法或写内部 map | 权威 ledger/outbox/transaction-log state 迁入闭包持有的 `WeakKeyDictionary`；公开实例使用 `__slots__` 且没有 `__dict__`、没有 public/private append/commit/get/snapshot/restore 方法、没有 `_records_by_id/_events_by_id/_results_by_key` 等 mutable map；模块级 helper 与类方法默认参数均不暴露写 capability。 |
| HIGH 2 partial replay validation 可接受自洽 poison transaction | committed publication/revoke replay 必须重新验证 stored ledger/outbox/log 三方一致，并绑定 request/candidate id、payload/source lineage、locator/profile/rule、scope/subject/target/version、publication timestamps 和完整 event semantic equality；root replay 强制 `version_no=1`。 |
| HIGH 3 committed replay 在 expiry/grant 过期后被 freshness 先拦截 | `publish()`/`revoke()` 对精确同 key 的已提交 transaction 先做 full validation replay，再做当前 freshness/lifecycle 检查；新操作仍严格执行 request expiry、grant expiry 和 current-head rules，预置/篡改 key 不能绕过。 |

### 第四轮

| Finding | 修复 |
|---|---|
| HIGH 1 public write surfaces bypass approval chain | `append_batch()`、`append()`、`commit()` 从 public API 移除并改为 private transaction-only methods；publisher replay 验证 transaction log result 必须已在 ledger/outbox 完整落地，phantom log 以 `publication_transaction_incomplete` 拒绝。 |
| HIGH 2 original decision reused after revoke | revoked successor 必须使用新的 canonical request 和新的 decision/audit；复用 revoked record 上的原 `request_id` 或 `decision_id` 以 `revoked_successor_requires_new_approval` 拒绝，ledger/outbox 保持原 revoke 后 2/2。 |
| HIGH 3 supersede/revoke-successor replay idempotency | `publish()` 在 current-head lifecycle check 前先查询并验证 committed transaction；普通 supersede 和 revoke-successor 重放返回原完全等值 result，不产生 branch 或重复 event。 |

### 第三轮

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

- 红灯证据：第五轮新增 regression 在第四轮提交 `c87ec0a817a158900bd8b245f045822139c3175a` 下失败：类方法默认参数仍暴露 `_publication_state_accessors` helper，已提交 publish/supersede/revoke replay 在 expiry/grant 过期后被 freshness 先拦截。
- 修复后 P03 suite：`python3 -m unittest tests.ingestion.test_approval_publish_and_refresh` 通过 29 项。
- Manual exploit probe：`H1_public_storage_encapsulation=pass raw_commit_error=publication_storage_uninstalled ledger=0 outbox=0`；公开 ledger/outbox/transaction-log handle 无 `__dict__`、无 append/commit/get/snapshot/restore、无 mutable map，模块 helper 与类方法默认参数不暴露写 capability，publisher raw commit 也不是可用写入口。
- Manual exploit probe：`H2_public_read_mutation_is_defensive=pass replay_equal=True`；修改 `outbox.safe_summary()` 返回 dict 不污染 canonical event/result。
- Manual exploit probe：`H3_publish_replay_after_expiry=pass late_new_error=approval_request_expired_at_publish`；root/supersede exact replay 在 request expiry 后返回原结果，新 publish 仍拒绝。
- Manual exploit probe：`H3_revoke_replay_after_grant_expiry=pass late_new_error=reviewer_capability_expired`；exact revoke replay 在 grant expiry 后返回原结果，新 revoke 仍拒绝。
- 第四轮红灯证据：第四轮新增 regression 在第三轮提交 `918cc895...` 下失败：public `append_batch/append/commit` 存在且可注入、transaction-log-only phantom result 被 publisher 返回、revoke 后复用原 request/decision 可生成 version 3、普通 supersede replay 和 revoke-successor replay 均误报 `superseded_publication_not_current`。
- 第四轮修复证据：public write surfaces 不再存在，phantom log 以 `publication_transaction_incomplete` fail closed，revoke 后复用原 request/decision 以 `revoked_successor_requires_new_approval` fail closed，普通 supersede 与 revoke-successor replay 返回原完全等值 result。
- 第三轮红灯证据：第三轮新增 regression 在第二轮提交 `074807b...` 下失败：candidate mutation 未拒绝、profile returned object 污染 registry、grant actor 漂移为 `system_worker_alias`、log phantom retry ledger/outbox=0、public `snapshot/restore` 暴露、poison same-id event 被接受、revoked successor 被拒。
- Manual exploit probe：`H1.candidate_source_mutation=canonical_candidate_required`，`ledger=0 outbox=0`。
- Manual exploit probe：`H1.locator_mutation=canonical_candidate_required`，`ledger=0 outbox=0`。
- Manual exploit probe：`H1.profile_return_snapshot_ok`，mutating returned profile snapshot 不污染 canonical registry。
- Manual exploit probe：`H2.grant_mutation_actor=human_reviewer`，公开 grant mutation 不改变 canonical actor；`H2.request_subject_mutation=approval_request_not_canonical`，`ledger=0 outbox=0`。
- Manual exploit probe：`H3.log_post_write_failure=forced_log_post_write_failure` 后 `ledger=0 outbox=0`；retry 成功后 `ledger=1 outbox=1`。
- Manual exploit probe：`H4.public_mutating_restore_surface_present=False`。
- Manual exploit probe：`H5.poisoned_same_id_event=invalidation_event_idempotency_conflict`，`ledger=0 outbox=1`，即 pre-existing poison 保持但新 publish 无半写入。
- Manual exploit probe：independent revoked successor 追加成功，`ledger=3 outbox=3`。

## 5. 验证命令与结果

- `python3 -m unittest tests.ingestion.test_approval_publish_and_refresh`：通过，29 项。
- `python3 -m unittest discover -s tests/ingestion`：通过，55 项。
- `python3 -m unittest discover -s tests/contracts`：通过，46 项。
- `python3 -m unittest discover -s tests/architecture`：通过，8 项。
- Manual exploit probe（第五轮 HIGH 1-3、第四轮 HIGH 1-3、第三轮 HIGH 1-5、revoke successor、legacy A-F 保留路径）：通过，稳定错误码与计数见第 4 节。
- `python3 scripts/validate_regression_baseline.py --base-sha 8637f827d62e5e5e48af96f4c1d1725fc0ff097d`：通过。
- `python3 scripts/validate_regression_baseline.py --base-sha 8637f827d62e5e5e48af96f4c1d1725fc0ff097d --all-files`：通过。
- `python3 scripts/validate_gpt_project_mechanism_sync.py --no-report`：通过，23 files，system prompt 3613 chars。
- `python3 -m compileall -q core modules adapters tests`：通过。
- `find scripts tests -type f -name '*.sh' -exec sh -n {} +`：通过。
- `git diff --check`：通过。
- `make regression`：通过；P02 `0001` + `0002` migrations 连续 replay 两次、16 类 SQL negative constraints 通过；8 architecture + 14 regression + 8 local-runtime + 16 control-plane + 46 contracts + 55 ingestion，共 147 项 Python tests 通过；隔离 Docker resources 已清理。
- Docker cleanup readback：Compose project `fenjiu-local-runtime-1735561601` containers=0、volumes=0、networks=0。

## 6. 实际改动文件

- `modules/ingestion/approval.py`：将 authority ledger/outbox/log state 封闭在闭包持有的 read-surface 背后，增加 full committed-result semantic validation，修复 expiry/grant 后 exact replay 顺序，同时保留 revoke successor independence、defensive snapshot/fingerprint integrity、atomic rollback、full event fingerprint、outbox canonical return validation。
- `tests/ingestion/test_approval_publish_and_refresh.py`：新增第五轮 exploit regressions，覆盖 helper/default capability 泄露、module helper 暴露、已提交 publish/supersede/revoke expiry replay、新操作 freshness 拒绝；保留第四轮、第三轮和旧 A-F regressions。
- `docs/implementation/P03-03_APPROVAL_PUBLISH_AND_REFRESH_REPORT.md`：记录第四轮 `c87ec0a...` 被拒、第五轮 repair 设计、红灯证据和验证结果。
- `docs/implementation/P03-03_APPROVAL_PUBLISH_AND_REFRESH_HANDOFF.md`：补第五轮 repair note 与 synthetic/internal/P02 边界。

## 7. 事实分级与剩余阻断

- **CONFIRMED（工程）**：P03-03 synthetic/value-free/local-only approval -> decision -> immutable internal publication -> supersede/revoke/successor -> internal invalidation contract 已通过专项、相邻套件、manual exploit probe、P00 scans、mechanism validation、compile/shell/diff、full regression 与 Docker cleanup；第五轮 storage encapsulation/full replay validation/expiry replay ordering regressions 已覆盖，第四轮 public write/phantom/revoke-reuse/replay regressions 保持不回归。
- **CONFIRMED（边界）**：本模块只产生独立 immutable simulated/internal publication record，不创建或读取 P02 approved truth；P02 current-truth consumer 不能把该对象当作真值。
- **部分成立（角色能力）**：`SyntheticReviewerCapabilityRegistry` 只证明 local synthetic reviewer-capability contract，可用于测试职责分离、scope/policy/evidence/expiry；它不是真实认证、真实 reviewer identity、production RBAC 或人工审批系统。
- **部分成立（原子性）**：本卡证明的是单进程内存对象的 local atomic contract，不是 process crash、database crash、distributed transaction 或 production durability proof。
- **UNKNOWN / BLOCKED（业务）**：真实 reviewer 身份、真实 approval policy、SKU、价格、库存、资质、账号、收款、配送售后、TikTok 酒类边界仍未确认；外部发布、报价、收款、下单、履约仍关闭。
- **DEFER**：production DB、auth/RBAC/RLS、workflow runner、real approval identity、real supplier data onboarding、Phase 4 action policy。

## 8. Rollback 与 P04-01 安全入口

- Rollback：回退本任务分支 fifth repair commit 即可移除本轮 P03-03 approval module/report/test 改动；不会删除真实业务资料、真实 truth 或外部状态，因为本卡没有创建它们。
- P04-01 唯一安全入口：只可读取 P03-03 的 internal proof / invalidation contract 作为“synthetic local approval flow completed”工程信号；不得把它当作 P02 approved truth、真实业务事实、真实人工批准或外部执行授权。Phase 4 若要运行 workflow checkpoint/recovery，必须保持 external flags false，并在独立 action policy/RBAC 合同通过前只允许 internal dry-run。
