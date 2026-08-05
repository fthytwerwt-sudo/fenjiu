# P05-03｜外联草稿、人工批准与零发送证明

| 元数据 | 值 |
|---|---|
| task_id / phase | `P05-03` / `phase_05` |
| status | `PLANNED` |
| depends_on / can_run_in_parallel_with | `P05-02` / `P06-03`, `P07-03` |
| writes_to | CRM application/workflow/policy/tests/docs |
| forbidden_paths | send/email/WhatsApp/social adapters, real contacts, automatic B2B activation, legacy |
| estimated_risk / recommended_executor | high / Codex 5.6 Thinking + GPT review |

## Goal

实现 only-approved-fact 的外联草稿、fact lock、DNC/policy/approval gate 和 scoped export；保持发送实现不存在/关闭。

## Context

汾酒主线不启用旧 B2B 自动外联；这项能力只做内部草稿与人工编辑。

## Constraints

批准草稿不等于发送；无 price/inventory truth 只能写需确认；sent count must be zero.

## 六层需求确认

- 目标层：draft-only CRM workflow.
- 机制层：DNC/expired/conflict/no authorization hard deny.
- 实现设计层：`primary_route=draft+approval no SendPort`；`fallback_route=manual template export`；`capability_status=internal`；`probe_required=zero-send E2E`。
- 流程层：CRM→fact policy→draft→review→manual record future.
- 判断标准层：all variants leave no send action.
- 反馈层：policy error expires draft/manual handoff.

## Impact check

check DNC, consent, business-line scope, fact version expiry, audit and no provider endpoints.

## Must read

`LEADS_CRM_IMPLEMENTATION_PLAN.md`、customer service plan policy sections、P04 action policy、P05-02 output.

## Execution contract

- Capability status：internal draft-only; sending disabled。
- Probe required：yes — zero-send E2E probe。

- Primary route：draft entity/template/fact refs/approval/invalidation and tests.
- Fallback route：render editable offline draft only.
- Allowed Codex autonomy：draft workflow/tests/docs.
- Forbidden Codex guessing：recipient, message claim, price/stock, outreach authorization.
- Required inputs：reviewed CRM entity, approved synthetic facts, policy.
- Required outputs：draft with fact version/policy and 0-send proof.
- Execution entrypoints：outreach synthetic E2E.

## Execution steps

1. Verify scope/DNC/contact evidence.
2. Generate editable draft from approved facts only.
3. Require review, invalidate on policy/fact change.
4. Test DNC/missing/expired/high risk and no SendPort.

## Validation commands

synthetic lead→CRM→draft E2E; assert `external_send_attempts=0`; policy/audit tests.

## Done when

draft is reproducible and auditable; no code path can send to a real or fake external recipient.

## Blocked if

task asks to contact/send, facts lack approval, DNC/consent missing.

## Output 回报格式

fact locks, DNC/no-send proofs, tests/Git, Phase 8 dependencies.

## Git completion

stage draft/policy/tests/docs only; no contacts or send configs.
