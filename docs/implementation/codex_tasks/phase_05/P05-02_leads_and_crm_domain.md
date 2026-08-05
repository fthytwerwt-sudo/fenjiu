# P05-02｜Leads、CRM、DNC 与可替换导出

| 元数据 | 值 |
|---|---|
| task_id / phase | `P05-02` / `phase_05` |
| depends_on / can_run_in_parallel_with | `P05-01` / `P06-02`, `P07-02` |
| writes_to | `modules/leads/ modules/crm/`、migrations/contracts/tests |
| forbidden_paths | real contacts, Twenty/CRM service install, external sending, supplier data |
| estimated_risk / recommended_executor | medium / Codex 5.6 Thinking |

## Goal

建立 lead→review→organization/contact/opportunity/interaction/stage、source-aware dedupe 与 immutable DNC 的 scoped synthetic domain。

## Context

CRM 真值在本系统 PostgreSQL；Twenty 只是 future `DEFER` adapter/UI candidates，不能造成双真值。

## Constraints

仅 synthetic public business data；无 source/consent 时不建 contact；DNC/withdrawal 阻断草稿/发送、不可提示词绕过。

## 六层需求确认

- 目标层：CRM 内部数据模型，非销售动作。
- 机制层：lead approval before CRM; DNC overrides all.
- 实现设计层：`primary_route=own CRM domain+scoped export`；`fallback_route=CSV/manual review`；`capability_status=synthetic`；`probe_required=dedupe/DNC tests`。
- 流程层：snapshot→candidate→review→CRM→draft.
- 判断标准层：same source dedupe explainable, cross-line denied.
- 反馈层：ambiguous identity creates merge_candidate/manual review.

## Impact check

compatible with policy/audit, future Chatwoot/Twenty adapter, retention/PII minimization; no business status change.

## Must read

`LEADS_CRM_IMPLEMENTATION_PLAN.md`、core contracts、P05-01 source output、P04 policy/audit.

## Execution contract

- Capability status：synthetic CRM domain only。
- Probe required：yes — dedupe/DNC/export scope probe。

- Primary route：schemas/repositories/review/DNC/export tests.
- Fallback route：unresolved merge stays candidate, no silent merge.
- Allowed Codex autonomy：CRM domain/migrations/tests/export docs.
- Forbidden Codex guessing：contact validity, sales value, B2B authorization, consent.
- Required inputs：reviewed synthetic lead/evidence.
- Required outputs：scoped CRM entities/DNC/export.
- Execution entrypoints：CRM integration suite.

## Execution steps

1. Add lead fingerprint/scoring explanation/review.
2. Add CRM entities/stages/interactions and DNC command.
3. Add scoped JSON/CSV export without provider IDs as keys.
4. Test dedupe, DNC, cross line, deletion/retention intent.

## Validation commands

CRM/DNC/merge negative tests; export scope tests; `make regression`.

## Done when

synthetic public lead can enter CRM only after review; DNC cannot be bypassed; no real sender/provider.

## Blocked if

requires real contact/CRM credentials, or PII/retention policy cannot be applied.

## Output 回报格式

entities/exports/DNC proof, test/Git, P05-03 input.

## Git completion

stage CRM code/migrations/synthetic tests/docs; no contact data.
