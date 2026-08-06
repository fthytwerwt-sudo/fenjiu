# P02-03｜业务线隔离、fixture 防护与合同测试报告

> **状态：remote_task_branch_code_readback_verified_pending_main_integration**
>
> **执行日期：** 2026-08-06
>
> **精确基线：** 远端 `main` `6d247b0613b517ff4474095abece2f64331a40a8`
>
> **远端任务分支代码提交：** `3341042c51a83d0eeac9abd91b1b01a3e07e2551`
>
> **范围边界：** 只完成 stdlib/local-only 的 isolation policy、repository grant、command 与 audit contract probes；没有 merge/push `main`，没有真实资料、production connection、外部 adapter、ORM/driver 或新依赖。

## 1. 实现结论

- `TruthConsumerCommand` 显式携带 scope、entity/version target、read time、action、actor、idempotency、policy ref 和完整 feature-flag snapshot；缺失或无效输入在 command 层 fail closed 并产生安全 denial audit。
- `IsolationPolicy` 只允许 `internal_truth_read`、固定 local `Sensitivity.INTERNAL` 与 11 个 external flags 全为 false；调用者不能自行扩大 sensitivity allowlist。
- `RepositoryReadGrant` 绑定 grant id、tenant/project/business-line/correlation scope、actor ref、target version、read time、policy ref、state/sensitivity/synthetic metadata；actor/field replacement、跨 target 复用和 metadata spoof 均被 signature/registry 拒绝。
- repository 只接受 sealed nominal `IsolationPolicy` 和 sealed audit recorder，并验证 grant 必须存在于该 policy instance 的 issuance registry；direct issuer、structural fake verifier 或 fake audit recorder 均不能获得 current truth。
- `_get_by_id_for_policy`、`_versions_for_contract_probe`、`_current_for_contract_probe` 已从 runtime repository object 移除；P02-02 history/current 观察能力只存在于 `tests/contracts/truth_repository_harness.py`。runtime 的 `policy_target()` 只返回 value-free policy metadata，不返回 payload/source/version object。
- guarded `current` 不再接受独立 `actor_ref`，再次验证 approved/current/fresh/no-successor 与 exact version/metadata，并在返回任何 `TruthVersion` 前以 `validated grant.actor_ref` 强制追加一条 `ALLOWED` audit；手工 bind real policy/grant 也不能替换 actor 或绕过 audit，consumer success 不重复记录。
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
| replace signed `grant.actor_ref` | `repository_read_grant_invalid` |
| pass legacy/current-call actor override | argument unavailable / `TypeError` |
| grant field tamper / cross-version reuse | `repository_read_grant_invalid` / `repository_grant_target_mismatch` |
| forged target sensitivity metadata | `repository_grant_target_metadata_mismatch` |
| fixture external action | `fixture_external_action_forbidden` |
| any external action on approved contract truth | `external_action_disabled` |
| candidate / expired / conflict / superseded / stale truth | `truth_not_current` |
| restricted truth in fixed local policy | `sensitivity_forbidden` |
| incomplete / enabled external flag snapshot | `feature_flag_snapshot_invalid` / `external_flags_must_remain_false` |
| unsafe actor / idempotency / policy ref | stable required-field denial code |

每个 command denial 均产生 `AuditPolicyResult.DENIED` event；允许路径产生 `ALLOWED` event。actor attribution 与 grant 的绑定只证明 local in-process contract integrity，不认证 actor 真伪，也不是 production authentication、RBAC、audit storage 或法定留存。

## 3. 验证证据

- `make regression`：通过；P02 `0001` + `0002` migrations 连续 replay 两次，16 类 SQL negative constraints 通过并清理 disposable database/Compose resources。
- Python suites：8 architecture + 14 regression + 8 local-runtime + 16 control-plane + 46 contracts，共 92 项通过。
- P00 default scan：通过；P00 `--all-files` scan：通过。
- GPT Project mechanism validation：通过，23 files、system prompt 3613 chars。
- `compileall`、`sh -n`、`git diff --check`：通过。
- Docker cleanup：本 worktree 派生 Compose project 的 containers、network、volumes 均为 0 残留。
- 审查闭环：前三轮独立 review 曾修复 direct grant forgery、mutable audit 与 structural fake verifier；控制器随后两次复现 runtime probe helper direct read 与 grant actor attribution 可被 read-time 参数替换，均判定 HIGH；中间独立 reviewer 还复现 real policy/grant 可绕过 consumer audit。依次移除 helpers、下沉 mandatory success audit、把 actor 加入 grant signature/validation 并删除 current actor 参数后，最终专项独立复审 0 findings，结论 `APPROVE`。

## 4. 远端回读

- task branch：`codex/P02-03-business-line-fixture-guards`。
- remote code commit：`3341042c51a83d0eeac9abd91b1b01a3e07e2551`。
- `core/contracts/access.py` remote SHA-256：`4c45c89a2feba71079e88076d627e2f11882617405e471bbb7b6d89a1055b9ee`。
- `core/security/isolation.py` remote SHA-256：`d37e895280394a1054179074ac8891953bae844ee243613a9b5b0db66342820f`。
- `core/application/truth_consumer.py` remote SHA-256：`ca035aff5e2cbaed87525ab3338acb107512578f7e2169bed0796bd5b4819a51`。
- `modules/truth_center/repository.py` remote SHA-256：`83a62543fb913fc25c0e9b8ff8adde8ee233a44c76016d91e65f300dcb8f225e`。
- `tests/contracts/test_isolation_policy.py` remote SHA-256：`ebf464f705233a50dfab329011fcce2c3eeeba5d9fa82c17e1bb2ad98c91b148`。
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
