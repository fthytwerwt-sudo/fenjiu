# P02-02｜真值实体、版本与状态机执行交接

## Goal｜目标

- 仅实现 `product`、`sku`、`price`、`inventory`、`delivery_rule`、`compliance_document`、`content_asset`、`approved_fact`、`forbidden_expression` 的 synthetic-only 合同、不可变版本链、状态转换和 current-truth read model。
- `approved` truth 必须同时具备同 scope 的 source、version 与 approval evidence；`candidate`/`fixture`、`expired`、`conflict`、`superseded` 均不得作为 current truth 返回。
- 本轮不实现 P02-03、UI、ingestion parser、CRM/support/video adapter、真实业务资料或外部连接。

## Context｜上下文

- 基线：远端 `main` `43ec53fc4441f22fd2492324c2d0d3a3da460f6b`，当前为该提交创建的干净独立 worktree 和任务分支。
- P02-01 已提供 stdlib scope/source/version metadata 合同、synthetic fixture 隔离与 local PostgreSQL migration regression。
- 本轮只证明 local contract/state/read-model 防护，不代表 SKU、价格、库存、资质、素材权利或其他业务闸门成立。

## Constraints｜边界

- 允许修改：`modules/truth_center/`、必要的 `core/contracts/` exports、编号 migration、合同/migration 测试、本任务 handoff/report 和受影响的工程状态路由。
- 禁止修改：真实业务文件、ingestion parser、UI、CRM/support/video adapters、production connection、ORM/driver、依赖和 lockfile。
- 禁止猜测：SKU normalization、币种、价格默认值、库存值、资质日期、商品事实或素材权利。
- fixture/mock 不得转成 approved/real；任何 synthetic probe 永久 `external_execution_allowed=false`，全部外部业务 flags 保持 false。
- Git：只暂存本任务路径，不使用 `git add .`，不 merge 或 push `main`，提交遵循 Lore trailers。

## Impact check｜影响面

- 业务状态：不变化；现有 `business_gates` 继续 `BLOCKED`。
- 工程状态：仅在代码、测试、扫描、commit、push 与远端核心文件回读全部通过后记录 P02-02 工程完成。
- 同步包/GPT Project 机制：不修改机制定义；只运行现有 mechanism validation，避免误改静态包。
- 业务线隔离：所有 read/transition/version 操作要求完整 compound scope；跨 tenant/project/business line fail closed。

## Must read｜必读

1. 根 `AGENTS.md` 与 GPT Project 机制包强制文件。
2. `PROJECT_ENTRY.md`、`BUSINESS_STATUS.md`、`CURRENT_STATUS.md`、`SOURCE_OF_TRUTH.md`、`SCOPE_AND_BOUNDARIES.md`、`COLLABORATION_STATUS.md`、`RISKS_AND_BLOCKERS.md`。
3. P02-02 task card、`CORE_DATA_CONTRACTS.md`、`INGESTION_MAPPING_APPROVAL_PIPELINE.md`、`WORKFLOW_APPROVAL_AUDIT_DESIGN.md`。
4. P02-01 contracts、migration、tests 与 `P02-01_SCOPE_CONTRACTS_AND_MIGRATIONS_REPORT.md`。

## 六层需求确认

- 目标层：建立真值合同与 current read 安全边界，不确认任何业务值。
- 机制层：candidate 只可形成新 version；future approval evidence 完整后才可形成 approved version；conflict 不按 latest-wins；历史不覆盖/不删除。
- 实现设计层：`primary_route=immutable truth version + guarded transition + scoped read model`；`fallback_route=fixture/candidate staging only`；`capability_status=local synthetic contract`；`probe_required=state transition/read model/cross-scope/invalid-state tests`；`allowed_codex_autonomy=truth module,migration,tests,report`；`forbidden_codex_guessing=business values and normalization/defaults`；`required_inputs=P02-01 base contracts`；`required_outputs=entities,state chart,version/evidence guards,positive/negative synthetic probes`；`execution_entrypoints=truth contract suite and make regression`；`validation_commands` 见下；`blocked_if_missing=P02-01 lineage or approval/audit guarantee`。
- 流程层：synthetic candidate → future human approval evidence contract → immutable approved version → scoped current read；失效、冲突、supersede 立即不可读。
- 判断标准层：技术通过不替代业务通过；current read 只返回 approved/fresh/no-conflict/same-scope 且 evidence 完整的版本。
- 反馈层：失败按 scope、lineage、approval evidence、state transition、freshness、Git/环境分别回退，不补猜业务字段。

## Execution steps｜执行步骤

1. 建立 entity kind、candidate payload、approval evidence、version/diff 与状态转换合同。
2. 建立 append-only in-memory contract repository/read model，拒绝 overwrite/delete、重复 version、跨 scope 与不合法转换。
3. 如需 schema 防护，新增 replay-safe 纯 SQL migration，只建合同表/约束，不插入业务行。
4. 添加状态转换、current read、cross-scope、invalid-state 和 migration 负向测试。
5. 更新 P02-02 报告与必要状态路由，保持业务状态不变。
6. 执行完整验证、自我审查、path-limited commit/push 和远端回读。

## Validation commands｜验证命令

- `python3 -m unittest discover -s tests/contracts`
- `make regression`
- `python3 scripts/validate_regression_baseline.py --base-sha 43ec53fc4441f22fd2492324c2d0d3a3da460f6b`
- `python3 scripts/validate_regression_baseline.py --base-sha 43ec53fc4441f22fd2492324c2d0d3a3da460f6b --all-files`
- `python3 scripts/validate_gpt_project_mechanism_sync.py --no-report`
- `git diff --check`、本任务 diff/status/path scan、Docker Compose project cleanup 核验。

## Done when｜完成标准

- 所有目标 entity kind 共用明确 scope/source/version/approval/expiry/conflict/supersede 合同。
- candidate/fixture/expired/conflict/superseded 与 evidence 不完整记录不可作为 current truth 读取。
- `make regression` 含 P02-01 migration replay/negative constraints 全部通过，P00 两种扫描和 mechanism validation 通过。
- 本任务分支已 Lore commit、push，远端 branch HEAD 与核心文件已回读；最终 worktree clean。

## Blocked if｜阻断条件

- 基线、worktree、remote 或 P02-01 contracts 不满足任务卡要求。
- 无法在不放宽 fixture 隔离、scope lineage 或 approval evidence 的情况下实现状态转换/read model。
- 验证、敏感扫描、push 或远端核心文件回读失败且无安全替代方案。

## Output｜回报格式

- 实际修改与简化、验证命令/结果、未测试项。
- `CONFIRMED` / `INFERRED` / `UNKNOWN` / `BLOCKED` 事实分级。
- 分支、commit、push、远端 HEAD/core-file readback、剩余阻断与 P02-03 依赖。
