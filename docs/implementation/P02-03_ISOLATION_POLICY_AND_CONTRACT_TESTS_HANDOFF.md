# P02-03｜业务线隔离、fixture 防护与合同测试执行交接

## Goal｜目标

- 仅执行 `P02-03`：把 tenant/project/business-line scope、fixture production separation、sensitivity、feature-policy denial 和 denial audit 锁进 repository/command 合同与 regression tests。
- 下游 truth consumer 只有在 scope 完整且精确一致、目标 version 为 approved/fresh/no-conflict current head、sensitivity 明确允许、policy snapshot 完整且全部外部 flags 为 false 时，才可获得 local internal read。
- 本轮不实现真实资料导入、外部执行、UI、CRM、客服、视频或 production isolation。

## Context｜上下文

- 目标仓库：`fthytwerwt-sudo/fenjiu`。
- 精确基线：远端 `main` `6d247b0613b517ff4474095abece2f64331a40a8`；已由 `git fetch`、`git rev-parse origin/main` 和 `git ls-remote` 一致确认。
- 工作区：从上述基线新建的干净独立 worktree；分支 `codex/P02-03-business-line-fixture-guards`。
- P02-01 已建立 compound scope/source/version schema 与 fixture external false 约束；P02-02 已建立 append-only truth version、approval/effective-window current read 与 invalid-root 防护。
- 当前工程能力仅为 stdlib/local-only/synthetic contract probes；业务闸门与所有 external flags 保持关闭。

## Constraints｜边界

- 允许修改：`core/security/`、`core/application/` 的 local command contract、truth repository contract、synthetic fixtures、tests、本任务 handoff/report，以及实际受影响的工程状态/决策/风险/执行历史。
- 禁止修改或新增：真实数据、`.env*`、任何 external send/publish adapter、legacy、真实服务账户、wildcard default scope、UI、ingestion、CRM、support、video、ORM/driver、新依赖、production connection。
- 不得提供可把 fixture/mock 转成 real/approved 或打开外部 action 的 command/config surface。
- 不得猜测 tenant role/owner、真实 scope、法律留存、真实 data classification、SKU/价格/库存/资质等业务值。
- Git 只 stage 本任务明确路径；禁止 `git add .`；不得 merge 或 push `main`；commit 使用 Lore trailers。

## Impact check｜影响面

- 业务状态：不变化；SKU、价格、库存、主体/资质、账号、收款、履约、TikTok 酒类边界继续 `UNKNOWN/BLOCKED`。
- 工程状态：只增加 local contract enforcement 和 adversarial evidence，不声明 production isolation、authenticated RBAC/RLS 或业务可用。
- Phase 3：只提供 staging command/read guard 的依赖合同；不实现 ingestion parser、mapping 或 approval publish。
- GPT Project 机制包：不修改机制定义；运行现有 validation 防止漂移。
- 业务线污染：测试只使用 value-free synthetic UUID/identifier/hash；不写入汾酒或海鲜真实业务值。

## Must read｜必读

1. 根 `AGENTS.md`、GPT Project 机制包强制文件、`PROJECT_ENTRY.md`。
2. `BUSINESS_STATUS.md`、`CURRENT_STATUS.md`、`SOURCE_OF_TRUTH.md`、`SCOPE_AND_BOUNDARIES.md`、`RISKS_AND_BLOCKERS.md`、`COLLABORATION_STATUS.md`。
3. P02-03 task card、`CORE_DATA_CONTRACTS.md`、`TEST_ACCEPTANCE_ROLLBACK_MATRIX.md`、`WORKFLOW_APPROVAL_AUDIT_DESIGN.md`。
4. P02-01/P02-02 task cards、contracts、migrations、tests、handoff/reports，以及当前 `DECISIONS.md`、`EXECUTION_HISTORY.md`。

## 六层需求确认

- 目标层：执行 local hard isolation 和 denial evidence，不开放业务能力。
- 机制层：command 必须携带完整 scope/version/correlation/idempotency/actor/policy/flag context；policy 从目标 metadata 检查固定 local sensitivity allowlist，调用者不能自行扩大；缺失、跨 scope、fixture external、非 current truth 或 policy 不完整全部 fail closed 并记录 audit result。
- 实现设计层：`primary_route=application command -> isolation policy -> repository grant/current read -> append-only audit`；`fallback_route=deny all unscoped/unsupported/external`；`capability_status=local synthetic isolation contract`；`probe_required=adversarial tenant/project/business-line/unscoped/fixture/state/sensitivity/policy tests`；`allowed_codex_autonomy=security/application/repository/tests/docs`；`forbidden_codex_guessing=real scope,roles,retention,classifications,business values`；`required_inputs=P02-01 scope metadata + P02-02 truth version/current read`；`required_outputs=stable codes,repository grant,denial audit,regression evidence`；`execution_entrypoints=contract suite + make regression`；`validation_commands` 见下；`blocked_if_missing=complete scope/current truth/audit denial guarantee`。
- 流程层：command receives scope/context → policy checks fixture/action/flags/sensitivity → repository validates grant and current truth → result is appended to audit → caller receives truth or stable denial。
- 判断标准层：技术通过要求所有 adversarial path 被拒并有安全 audit；这不等于业务、合规、真实资料或 production 通过。
- 反馈层：失败分别回 scope propagation、repository grant/current truth、fixture/action policy、sensitivity、audit append-only、migration regression 或 Git/readback；不放宽 guard 以绕过失败。

## Execution steps｜执行步骤

1. 先增加 P02-03 adversarial contract tests，覆盖 cross tenant/project/business line、unscoped/wildcard、direct repository bypass、fixture external action、candidate/expired/conflict/superseded/stale truth、sensitivity 与 policy snapshot denial、denial audit。
2. 建立 stdlib-only isolation policy、immutable repository read grant、append-only audit contract 和 local truth-consumer command handler。
3. 收紧 repository current read，只接受 policy-issued、scope/version/correlation/actor 精确绑定的 grant；audit actor 只能来自 validated grant；保持 P02-02 append-only/state semantics。
4. 运行 focused tests、完整 regression（含 P02 migrations）、P00 default/all-files、mechanism validation、diff/path/shell 检查和 Docker cleanup。
5. 自审后交由独立 code review；修复后复跑受影响与完整验证。
6. 更新报告和必要工程状态；path-limited Lore commit，push 本任务分支并回读远端 branch/default/visibility/core files。

## Validation commands｜验证

- `python3 -m unittest discover -s tests/contracts`
- `make regression`
- `python3 scripts/validate_regression_baseline.py --base-sha 6d247b0613b517ff4474095abece2f64331a40a8`
- `python3 scripts/validate_regression_baseline.py --base-sha 6d247b0613b517ff4474095abece2f64331a40a8 --all-files`
- `python3 scripts/validate_gpt_project_mechanism_sync.py --no-report`
- `git diff --check`、task-path diff/status、forbidden path/pattern 与 shell syntax checks。
- worktree-derived Compose project 的 containers/network/volumes cleanup 回读。

## Done when｜完成标准

- cross tenant/project/business line、unscoped/wildcard、fixture external、unsupported external action、candidate/expired/conflict/superseded/stale、sensitivity/policy mismatch 全部 fail closed。
- denial 产生稳定 error code 和不含 payload/secret/path 的 append-only audit event；success 也记录 policy result。
- repository current consumer read 不能绕过 policy grant，grant 不能跨 scope/version/actor 重用或替换 audit attribution。
- `make regression` 含 P02 migration replay/negative suite 通过；P00 两种扫描、mechanism validation、diff/shell/Docker cleanup 通过。
- 独立 code review 无未解决 blocker；任务分支 Lore commit/push、remote HEAD/core-file readback 完成；worktree clean。

## Blocked if｜阻断条件

- 任一 cross-scope、fixture external、非 current truth、sensitivity/policy bypass 可通。
- 任一 denial 无法记录安全 audit result，或 audit 可被普通 update/delete。
- 实现需要真实资料/账户、wildcard scope、production connection、外部 adapter、ORM/driver/新依赖或放宽 external flag。
- migration regression、P00 scan、mechanism validation、独立 review、push 或 remote readback 失败且无安全的范围内修复。
