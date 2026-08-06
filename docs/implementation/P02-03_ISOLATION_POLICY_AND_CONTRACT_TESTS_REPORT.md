# P02-03｜业务线隔离、fixture 防护与合同测试报告

> **状态：remote_task_branch_code_readback_verified_pending_main_integration**
>
> **执行日期：** 2026-08-06
>
> **精确基线：** 远端 `main` `6d247b0613b517ff4474095abece2f64331a40a8`
>
> **远端任务分支代码提交：** `ec1b07ed97788b9d1fe4f36526b371694b58b881`
>
> **范围边界：** 只完成 stdlib/local-only 的 isolation policy、repository grant、command 与 audit contract probes；没有 merge/push `main`，没有真实资料、production connection、外部 adapter、ORM/driver 或新依赖。

## 1. 实现结论

- `TruthConsumerCommand` 显式携带 scope、entity/version target、read time、action、actor、idempotency、policy ref 和完整 feature-flag snapshot；缺失或无效输入在 command 层 fail closed 并产生安全 denial audit。
- `IsolationPolicy` 只允许 `internal_truth_read`、固定 local `Sensitivity.INTERNAL` 与 11 个 external flags 全为 false；调用者不能自行扩大 sensitivity allowlist。
- `RepositoryReadGrant` 绑定 grant id、tenant/project/business-line/correlation scope、target version、read time、policy ref、state/sensitivity/synthetic metadata；普通 field replacement、跨 target 复用和 metadata spoof 均被拒绝。
- repository 只接受 sealed nominal `IsolationPolicy` 和 sealed audit recorder，并验证 grant 必须存在于该 policy instance 的 issuance registry；direct issuer、structural fake verifier 或 fake audit recorder 均不能获得 current truth。
- `_get_by_id_for_policy`、`_versions_for_contract_probe`、`_current_for_contract_probe` 已从 runtime repository object 移除；P02-02 history/current 观察能力只存在于 `tests/contracts/truth_repository_harness.py`。runtime 的 `policy_target()` 只返回 value-free policy metadata，不返回 payload/source/version object。
- guarded `current` 再次验证 approved/current/fresh/no-successor 与 exact version/metadata，并在返回任何 `TruthVersion` 前强制追加一条 `ALLOWED` audit；手工 bind real policy/grant 也不能绕过 audit，consumer success 不重复记录。
- denial/success audit 只保存 reference、安全 identifier、scope、policy result、error code、state/sensitivity 和 external-attempt marker，不保存 truth payload、正文、URL、secret 或本机路径。
- local audit storage 使用 `__slots__`、name-mangled immutable tuple replacement 与 frozen event；普通 clear、field mutation、update/delete surface 均失败。

## 2. adversarial cases 与稳定拒绝码

| 攻击/错误路径 | 结果 |
|---|---|
| cross tenant / project / business line | `cross_scope_forbidden` |
| unscoped / wildcard scope | `scope_required` |
| direct repository current without grant | `repository_read_grant_required` |
| direct issuer forged grant | `repository_read_grant_not_issued` |
| structural fake verifier binding | `repository_grant_verifier_required` |
| runtime probe/read helper direct call | method unavailable / `AttributeError` |
| fake audit recorder binding | `repository_audit_recorder_required` |
| direct real-policy grant current read | truth 仅在 `ALLOWED` audit append 后返回 |
| grant field tamper / cross-version reuse | `repository_read_grant_invalid` / `repository_grant_target_mismatch` |
| forged target sensitivity metadata | `repository_grant_target_metadata_mismatch` |
| fixture external action | `fixture_external_action_forbidden` |
| any external action on approved contract truth | `external_action_disabled` |
| candidate / expired / conflict / superseded / stale truth | `truth_not_current` |
| restricted truth in fixed local policy | `sensitivity_forbidden` |
| incomplete / enabled external flag snapshot | `feature_flag_snapshot_invalid` / `external_flags_must_remain_false` |
| unsafe actor / idempotency / policy ref | stable required-field denial code |

每个 command denial 均产生 `AuditPolicyResult.DENIED` event；允许路径产生 `ALLOWED` event。上述 audit 只证明 local contract，不是 production audit storage、身份认证或法定留存。

## 3. 验证证据

- `make regression`：通过；P02 `0001` + `0002` migrations 连续 replay 两次，16 类 SQL negative constraints 通过并清理 disposable database/Compose resources。
- Python suites：8 architecture + 14 regression + 8 local-runtime + 16 control-plane + 45 contracts，共 91 项通过。
- P00 default scan：通过；P00 `--all-files` scan：通过。
- GPT Project mechanism validation：通过，23 files、system prompt 3613 chars。
- `compileall`、`sh -n`、`git diff --check`：通过。
- Docker cleanup：本 worktree 派生 Compose project 的 containers、network、volumes 均为 0 残留。
- 审查闭环：前三轮独立 review 曾修复 direct grant forgery、mutable audit 与 structural fake verifier；控制器随后复现 runtime probe helper 可直接返回 approved truth，判定 1 个 HIGH。移除 helpers 后，独立 reviewer 又复现 real policy/grant 可绕过 consumer audit，判定 1 个 HIGH；将 mandatory success audit 下沉到 guarded repository read 并补精确 exploit regression 后，最终独立复审 0 findings，结论 `APPROVE`。

## 4. 远端回读

- task branch：`codex/P02-03-business-line-fixture-guards`。
- remote code commit：`ec1b07ed97788b9d1fe4f36526b371694b58b881`。
- `core/contracts/access.py` remote SHA-256：`78040cc83f6c40befb33f9bb8fd0c0732a322a1f2a0a16546b43d1ac89e44c05`。
- `core/security/isolation.py` remote SHA-256：`6e2a0cf9661205864fc719c2e3a93a1c582e58fe4b5949f016464c336766fced`。
- `core/application/truth_consumer.py` remote SHA-256：`134cd8efa39cae270d662e5aa6ce342a35fe440494a1285b5946c5646a3b45f4`。
- `modules/truth_center/repository.py` remote SHA-256：`4165417ee01a1541abbb536c2ec5fb3da6470975bef45d0861b3de3dff81980c`。
- `tests/contracts/test_isolation_policy.py` remote SHA-256：`867bc0810d87caff98316720d6644e95eda1644a0615f6d9e220ffc0cd3ae3f5`。
- `tests/contracts/truth_repository_harness.py` remote SHA-256：`336ad8bff88dc516e23d61a835d2f01babd1fafcb645ef8f1cb5a4000c9354dd`。
- remote `main` 仍为精确基线 `6d247b0613b517ff4474095abece2f64331a40a8`；本任务没有 merge/push `main`。
- remote default branch 仍为 `chore/project-collaboration-system`；visibility 因 GitHub API 连接失败保持 `UNKNOWN/BLOCKED`。

## 5. 边界、回退与 Phase 3 依赖

- **CONFIRMED（task branch engineering）**：P02-03 local isolation/fixture/policy/audit contracts、adversarial tests、代码 commit/push/core-file readback 已完成。
- **PARTIAL（Phase 2 integration）**：代码尚未集成并从远端 `main` 回读，因此不能写 Phase 2 已在 main 完成，也不能启动依赖 `Phase 02` 的 P03-01。
- **DEFER / 未实现**：authenticated actor/RBAC、RLS、encryption、retention/legal region、production repository/driver/connection、真实 tenant/scope、真实 data classification、真实资料和外部执行。
- **Phase 3 进入条件**：先由控制器审查并将本任务安全集成到 `main`，从新的远端 main 回读本报告列出的 core contracts/tests，再在新建干净 worktree 单独执行 P03-01；P03-01 仍只能 synthetic source registration/extraction、quarantine、relative/reference locator 和 staging output，不能读取真实供应链包或绕过 current-truth consumer policy。
- 回退采用单独 revert/forward fix 本任务提交；不删除 audit/history，不使用 destructive reset，不提供 production down migration。
- 所有业务 external flags 与 `business_external_ready` 保持 false；业务状态和 `business_gates` 没有变化。
