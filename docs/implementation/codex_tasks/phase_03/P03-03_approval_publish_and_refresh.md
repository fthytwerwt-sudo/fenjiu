# P03-03｜审批、版本化发布与下游刷新

| 元数据 | 值 |
|---|---|
| task_id / phase | `P03-03` / `phase_03` |
| depends_on / can_run_in_parallel_with | `P03-02` / 无 |
| writes_to | truth/ingestion application services、approval contracts、tests/docs |
| forbidden_paths | 自动外发/发布、真实数据、CRM/support/video implementation、legacy |
| estimated_risk / recommended_executor | high / Codex 5.6 Thinking + GPT review |

## Goal

实现 candidate→approval request→human decision→approved truth/data version→supersede/refresh 的 synthetic 闭环。

## Context

价格、库存、配送、资质、素材权利和任何 conflict 必须人工批准；publish 不代表销售授权。

## Constraints

禁止自动批准、overwrite/delete history、self-approval；下游只收到 internal invalidation event，不外部同步。

## 六层需求确认

- 目标层：真值发布控制，不开放模块执行。
- 机制层：reviewer/role/evidence/version/policy mandatory。
- 实现设计层：`primary_route=approval state machine+immutable version`；`fallback_route=staging only`；`capability_status=synthetic`；`probe_required=E2E`。
- 流程层：mapping candidate→review→approved→TruthFactsChanged→draft/cache invalidation。
- 判断标准层：reject/expire/conflict can't publish; replay no duplicates。
- 反馈层：误批准用 revoke/supersede, never delete.

## Impact check

与 Phase 4 action policy、P05/06/07 only-read approved truth 相容；不写业务 status/Phase 9 state。

## Must read

`CORE_DATA_CONTRACTS.md`、`INGESTION_MAPPING_APPROVAL_PIPELINE.md`、`WORKFLOW_APPROVAL_AUDIT_DESIGN.md`、P03-01/02 output。

## Execution contract

- Capability status：synthetic approved-truth publication only。
- Probe required：yes — approval/invalidation E2E probe。

- Primary route：approval request/decision service, truth publisher, event/outbox fake, invalidation tests.
- Fallback route：无法安全 publish stays staging/review.
- Allowed Codex autonomy：application services/tests/synthetic E2E.
- Forbidden Codex guessing：reviewer identity, approval policy exceptions, real facts.
- Required inputs：quality-passed candidate with evidence.
- Required outputs：approved versions/audit/event and negative cases.
- Execution entrypoints：synthetic ingest-to-approved E2E, `make regression`。

## Execution steps

1. 定义 request/decision/expiry/revise states。
2. enforce separation of duties and evidence.
3. publish immutable version, supersede old, emit refresh event.
4. test conflict, expired, reject, rerun, cross-scope, fixture.

## Validation commands

approval E2E；state/idempotency/cross-line tests；audit and no-external-action scan。

## Done when

合成供应链表可受控变成 approved synthetic truth；错误/冲突不外溢，Phase 4 可依赖。

## Blocked if

approval/audit cannot be atomic, reviewer role unclear, or real data is required.

## Output 回报格式

E2E correlation, approvals, failure paths, Git/rollback, Phase 4 entry.

## Git completion

only stage services/contracts/tests/docs; commit/push/readback according to branch rule.
