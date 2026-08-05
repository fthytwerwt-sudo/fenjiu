# P06-03｜客服 adapter、人工接管与 draft-only E2E

| 元数据 | 值 |
|---|---|
| task_id / phase | `P06-03` / `phase_06` |
| depends_on / can_run_in_parallel_with | `P06-02` / `P05-03`, `P07-03` |
| writes_to | `adapters/support/`、customer-service workflow/admin/tests/docs |
| forbidden_paths | production Chatwoot/WhatsApp/Meta/TikTok credentials, send endpoint, real conversations |
| estimated_risk / recommended_executor | high / Codex 5.6 Thinking + GPT review |

## Goal

用 fake support adapter 完成 receive→draft/handoff→human edit/approve/reject→audit 的 synthetic E2E，证明自动外发始终为 0。

## Context

Chatwoot 仅未来 `DEFER` inbox adapter；人工接管后自动化暂停，恢复需显式审计。

## Constraints

不调用/安装真实客服平台、不写 `SendApproved` production implementation、批准草稿不代表发出。

## 六层需求确认

- 目标层：人工工作流 simulation.
- 机制层：handoff pauses automation and real send flag false.
- 实现设计层：`primary_route=FakeSupportPort+admin case queue`；`fallback_route=manual case export`；`capability_status=synthetic`；`probe_required=E2E/replay`。
- 流程层：fake inbound→policy→draft/handoff→human decision→audit.
- 判断标准层：high-risk never becomes sendable; replay no duplicate case.
- 反馈层：adapter failure/human takeover holds conversation.

## Impact check

tests scope/DNC/fact expiry/PII/audit; future Chatwoot must map external IDs not control core state.

## Must read

customer service plan, open-source exit strategy, P06-01/02, P04 policy/audit.

## Execution contract

- Capability status：fake inbox/manual takeover; sending disabled。
- Probe required：yes — replay/handoff/zero-send probe。

- Primary route：fake adapter/webhook replay, handoff state/admin actions, no-send counter.
- Fallback route：manual-only queue.
- Allowed Codex autonomy：fake adapter/UI minimal/tests/docs.
- Forbidden Codex guessing：channel verification, auto-reply authorization, operator identity.
- Required inputs：synthetic messages, risk/fact policy.
- Required outputs：human takeover trace/audit and zero-send proof.
- Execution entrypoints：`make demo-run BUSINESS_LINE=fenjiu` synthetic mode and CS E2E.

## Execution steps

1. Build fake receive/replay adapter.
2. Build handoff/review/resume state with audit.
3. Enforce flags/policy before any hypothetical send.
4. Test reply, high-risk handoff, repeated message, fact invalidation.

## Validation commands

support E2E; assert `external_send_attempts=0`; DNC/PII/replay tests; `make regression`.

## Done when

customer-service module can internally operate on approved synthetic truth and safely hand all risky cases to humans.

## Blocked if

requires production account, real PII, or a nonzero send result.

## Output 回报格式

E2E correlations/handoff/no-send, tests/Git, Phase 8 dependencies.

## Git completion

stage fake adapter/workflow/tests/docs only; no channel secrets/data.
