# P02-02｜真值实体、版本与状态机

| 元数据 | 值 |
|---|---|
| task_id / phase | `P02-02` / `phase_02` |
| status | `PLANNED` |
| depends_on / can_run_in_parallel_with | `P02-01` / 无 |
| writes_to | `modules/truth_center/`、contracts/migrations/tests |
| forbidden_paths | ingestion parser、CRM/support/video adapters、真实资料、legacy |
| estimated_risk / recommended_executor | high / Codex 5.6 Thinking |

## Goal

实现 product/SKU/price/inventory/delivery/compliance/asset/approved_fact/forbidden expression 的候选、版本、expiry/conflict/supersede 合同。

## Context

approved truth 必有 source/version/approval evidence；价格/库存/资质未经批准或过期不得被读取。

## Constraints

AI 不能直接写 approved；禁止 overwrite/delete history；不创建真实 business values、不实现 UI/ingestion。

## 六层需求确认

- 目标层：建立 truth model，非业务确认。
- 机制层：candidate→approved only via future approval command；conflict never latest-wins。
- 实现设计层：`primary_route=immutable data_version+read model`；`fallback_route=staging-only`；`capability_status=local`；`probe_required=state transition tests`。
- 流程层：future ingestion candidate→review→versioned truth→consumer invalidation。
- 判断标准层：expired/conflict/superseded not queryable as current truth。
- 反馈层：未知 effective window/field semantics stay blocked.

## Impact check

需求与 Phase 3 mapping、Phase 6 retrieval、Phase 7 fact lock 一致；不让 old DOCX/JSON 成为真值。

## Must read

`CORE_DATA_CONTRACTS.md`、`INGESTION_MAPPING_APPROVAL_PIPELINE.md`、`WORKFLOW_APPROVAL_AUDIT_DESIGN.md`、P02-01 contracts。

## Execution contract

- Capability status：synthetic truth model only。
- Probe required：yes — state transition and read-model probe。

- Primary route：entity schemas/repositories/state transitions/version diff/read query.
- Fallback route：没有 approved flow 时只创建 staging contract/fakes.
- Allowed Codex autonomy：truth module/migrations/tests。
- Forbidden Codex guessing：SKU normalization, price currency/default, compliance dates, product facts.
- Required inputs：P02-01 base contract.
- Required outputs：entity contracts, state chart, positive/negative fixtures.
- Execution entrypoints：migration and truth contract suite。

## Execution steps

1. 以 scoped base model 建领域实体。
2. 建 data version/parent/diff and state guards。
3. 让 read APIs 返回 only current approved/fresh/no-conflict facts。
4. 测试 supersede/revoke/expiry/conflict。

## Validation commands

truth unit/integration tests；cross scope and invalid-state tests；`make regression`。

## Done when

synthetic truth 具完整 lineage；不可能从 fixture/candidate 无审批读出价格/库存/资质。

## Blocked if

core contract 缺失、状态转移不能保证 audit/approval、或触及真实资料。

## Output 回报格式

schemas/states/tests/known gaps、Git/rollback、P02-03 dependency。

## Git completion

path-limited stage truth/contracts/migrations/tests，push/readback 后报告。
