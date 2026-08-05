# P06-01｜会话合同、幂等与隐私最小化

| 元数据 | 值 |
|---|---|
| task_id / phase | `P06-01` / `phase_06` |
| depends_on / can_run_in_parallel_with | Phase 04 / `P05-01`, `P07-01` |
| writes_to | `modules/customer_service/`、contracts/migrations/tests |
| forbidden_paths | real WhatsApp/TikTok/Meta/email adapters, raw chats/PII, `.env*`, legacy |
| estimated_risk / recommended_executor | high / Codex 5.6 Thinking |

## Goal

实现 scoped conversation/message/intent/draft/handoff data contracts、external message idempotency 和 privacy/retention references，使用 synthetic conversations。

## Context

真实消息渠道尚无授权；数据最小化、DNC、business line identification 和 human handoff 先于 AI reply。

## Constraints

不保存不必要全文/附件；不接 webhook；不实现自动发送；unknown scope quarantine。

## 六层需求确认

- 目标层：会话数据基础，非客服上线。
- 机制层：external ID replay idempotent and scope mandatory.
- 实现设计层：`primary_route=conversation/message immutable records`；`fallback_route=synthetic file import`；`capability_status=synthetic`；`probe_required=replay/PII tests`。
- 流程层：receive fake→scope→record→policy future.
- 判断标准层：duplicate creates no new reply/audit side effect.
- 反馈层：unknown scope/sensitive data creates hold/handoff.

## Impact check

aligns with CRM DNC/truth fact refs/audit retention; not export chats to Git, sync package or model training.

## Must read

`CUSTOMER_SERVICE_AI_IMPLEMENTATION_PLAN.md`、core data contracts、P04 policy/audit, P02 isolation.

## Execution contract

- Capability status：synthetic conversation store only。
- Probe required：yes — replay/scope/PII minimization probe。

- Primary route：entities/migrations/repositories/synthetic fixtures/replay tests.
- Fallback route：manual case record without message body.
- Allowed Codex autonomy：CS contracts/tests/docs.
- Forbidden Codex guessing：customer identity/consent/retention duration/channel permissions.
- Required inputs：synthetic message vectors, scope contract.
- Required outputs：idempotent privacy-minimised conversation store.
- Execution entrypoints：CS contract/integration suite.

## Execution steps

1. Define immutable conversation/message and external IDs.
2. Add scope/consent/redaction references and handoff fields.
3. Add replay/unknown scope/DNC/PII-negative tests.
4. Verify no channel adapter/send endpoint exists.

## Validation commands

message replay tests; PII/log scan; cross-line/DNC tests; `make regression`.

## Done when

synthetic inbound messages are safely recorded or quarantined with no external output.

## Blocked if

real chat data/credentials required, scope/consent unavailable, or privacy policy conflicts.

## Output 回报格式

contracts/privacy proof/known gaps, tests/Git, P06-02 handoff.

## Git completion

stage modules/migrations/synthetic tests/docs only; never stage chats/contacts.
