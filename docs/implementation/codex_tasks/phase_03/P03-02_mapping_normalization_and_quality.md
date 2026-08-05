# P03-02｜字段 mapping、清洗与数据质量

| 元数据 | 值 |
|---|---|
| task_id / phase | `P03-02` / `phase_03` |
| status | `PLANNED` |
| depends_on / can_run_in_parallel_with | `P03-01` / 无 |
| writes_to | mapping service/contracts/quality rules/tests/fixtures |
| forbidden_paths | approved write path、真实供应链资料、外部 adapters、legacy |
| estimated_risk / recommended_executor | high / Codex 5.6 Thinking |

## Goal

实现 versioned mapping profile、AI suggestion boundary、单位/币种/日期/语言规范化、missing/conflict/expiry/duplicate quality reports。

## Context

mapping 是配置优先；未知字段/单位/币种/日期和低置信 OCR 保持 missing/blocked，绝不以默认值补齐。

## Constraints

AI 仅可建议 source column/transform/翻译；不得 invent、resolve conflict、approve price/inventory/compliance；所有原值/normalized value/locator 保留。

## 六层需求确认

- 目标层：候选数据质量，不升级 business facts。
- 机制层：mapping profile version + source signature + deterministic replay。
- 实现设计层：`primary_route=config mappings+normalizers`；`fallback_route=manual mapping review`；`capability_status=synthetic`；`probe_required=replay/diff`。
- 流程层：extract→map→normalize→quality→review queue。
- 判断标准层：same profile yields same output；conflict/missing explicit。
- 反馈层：new layout→new adapter task，不临时 hardcode。

## Impact check

检查 contract fields、source locator、privacy、business-line scope；不让 rules 混淆海鲜/汾酒字段或复用事实。

## Must read

`INGESTION_MAPPING_APPROVAL_PIPELINE.md`、`CORE_DATA_CONTRACTS.md`、P03-01 输出、`TEST_ACCEPTANCE_ROLLBACK_MATRIX.md`。

## Execution contract

- Capability status：synthetic mapping/quality only。
- Probe required：yes — deterministic replay/diff probe。

- Primary route：YAML/JSON mapping profile schema、normalizers、quality rule engine、synthetic profiles。
- Fallback route：profile missing→manual review, no implicit map。
- Allowed Codex autonomy：mapping code/tests/docs。
- Forbidden Codex guessing：formal prices/currencies/sku defaults/effective dates.
- Required inputs：extraction result/locators, target contract.
- Required outputs：mapping candidates, quality/missing/conflict reports.
- Execution entrypoints：mapping test runner / `make regression`。

## Execution steps

1. 定义 mapping config/version validation。
2. 实现 deterministic normalizers and evidence preservation。
3. 实现 quality/duplicate/freshness/cross-scope rules。
4. 对 profile change 输出 diff/replay report。

## Validation commands

mapping replay tests；invalid profile/unknown unit/currency/conflict tests；sensitive scan。

## Done when

任何候选都可追到 source+locator+rule，且没有 mapping 能自动批准或默填关键字段。

## Blocked if

target contract 未冻结、mapping requires real content、or conflict cannot be represented.

## Output 回报格式

profiles/rules, replay proof, blocked cases, Git and P03-03 readiness.

## Git completion

stage mapping code/schema/tests/docs only; no real config/data.
