# P04-02｜RBAC、审批与 action policy

| 元数据 | 值 |
|---|---|
| task_id / phase | `P04-02` / `phase_04` |
| depends_on / can_run_in_parallel_with | `P04-01` / 无 |
| writes_to | `core/security/`、approval/admin application、tests/docs |
| forbidden_paths | external sending/publishing/payment adapters, real identities/data, legacy |
| estimated_risk / recommended_executor | high / Codex 5.6 Thinking + security review |

## Goal

实现 scoped roles、separation of duties、approval request/decision 和统一 ActionPolicy，使高风险动作默认不可执行。

## Context

external flags default false；reviewer 不能批准自己的风险生成；所有 policy decision 要可审计。

## Constraints

不创建真实用户/权限、不能使用 UI flag 代替 server policy、不为方便测试 bypass DNC/scope/approval。

## 六层需求确认

- 目标层：强制人工闸门。
- 机制层：role+scope+fact freshness+flag+evidence all required.
- 实现设计层：`primary_route=ActionPolicy service`；`fallback_route=deny all high-risk`；`capability_status=local`；`probe_required=negative RBAC`。
- 流程层：request→separate reviewer→decision→pre-execution recheck.
- 判断标准层：approve/reject/revise/expire all testable.
- 反馈层：ambiguous role/policy remains deny/block.

## Impact check

compatible with truth approvals, Leads DNC, CS handoff, video cost approval and all feature flags; no business authority inferred.

## Must read

`WORKFLOW_APPROVAL_AUDIT_DESIGN.md`、core data contracts、P04-01 output、runbook/test matrix。

## Execution contract

- Capability status：local RBAC/policy enforcement。
- Probe required：yes — negative role/flag/approval probe。

- Primary route：RBAC/scoped permissions/action policy/approval decisions and fakes.
- Fallback route：manual-only approval screen/command, still same policy.
- Allowed Codex autonomy：security/application/tests/docs.
- Forbidden Codex guessing：actual reviewers/owners, approval SLA, external authorization.
- Required inputs：roles/actions/flags/data states.
- Required outputs：enforced policy matrix and audit-ready decisions.
- Execution entrypoints：RBAC/approval test suite.

## Execution steps

1. Define roles/actions/scope contracts.
2. Implement decision state and self-approval denial.
3. Evaluate policy twice (request/execution) with flags/data freshness.
4. Test high-risk and cross-line denial.

## Validation commands

RBAC matrix tests; approval expiry/self-approve/flag denial; `make regression`.

## Done when

no route can approve/send/publish/quote/order without current policy, separate actor and evidence.

## Blocked if

role ownership depends on unprovided supplier/user data or policy lacks audit.

## Output 回报格式

roles/actions, denial proof, test/Git, P04-03 handoff.

## Git completion

stage security/approval/tests/docs only; no user/secret data.
