# P06-02｜Approved truth 检索、风险 policy 与答复草稿

| 元数据 | 值 |
|---|---|
| task_id / phase | `P06-02` / `phase_06` |
| depends_on / can_run_in_parallel_with | `P06-01` / `P05-02`, `P07-02` |
| writes_to | customer-service application/policy/AI port/fakes/tests |
| forbidden_paths | real LLM API, model key, send adapter, unapproved truth, legacy |
| estimated_risk / recommended_executor | high / Codex 5.6 Thinking |

## Goal

建立只读 approved fact retrieval、intent/risk classification、forbidden expression check、多语言 draft 和强制 handoff，全部使用 fake model。

## Context

价格/库存/配送只能在 fresh approved truth 中被引用；酒类购买、报价、退款、投诉、质量、账期、独家、订单/支付和未知事实均转人工。

## Constraints

AI cannot write truth/approval/send; no approved fact means no guessed answer; prompt/output stored as hashes/versioned reference, not raw secrets.

## 六层需求确认

- 目标层：draft safety, not automatic response.
- 机制层：risk first; policy over model; fact/policy change invalidates draft.
- 实现设计层：`primary_route=FactQueryPort+RiskPolicy+FakeModel`；`fallback_route=manual handoff template`；`capability_status=synthetic`；`probe_required=adversarial suite`。
- 流程层：message→intent/risk→truth→draft/handoff.
- 判断标准层：high-risk/missing/expired all handoff.
- 反馈层：model/retrieval error manual-only.

## Impact check

checks fact data state/scope/freshness, DNC and P04 flags; it must not modify CRM or content truth.

## Must read

customer service plan, `CORE_DATA_CONTRACTS.md`, `WORKFLOW_APPROVAL_AUDIT_DESIGN.md`, P06-01, P03-03.

## Execution contract

- Capability status：fake-model draft/handoff only。
- Probe required：yes — adversarial risk/fact-expiry probe。

- Primary route：intent/risk policy, approved-only query, fake model and draft/handoff contracts.
- Fallback route：no model/retrieval→handoff.
- Allowed Codex autonomy：policy/ports/fakes/tests.
- Forbidden Codex guessing：facts, translations, price/stock, permitted automatic replies.
- Required inputs：synthetic approved fact set/conversations/policy vector.
- Required outputs：draft fact locks and handoff evidence.
- Execution entrypoints：CS adversarial E2E.

## Execution steps

1. Implement intent/risk taxonomy and facts query filter.
2. Build draft with locale/original/translation/fact/policy/model refs.
3. Enforce handoff on all listed high-risk/missing paths.
4. Test fact expiry/revocation/model failure.

## Validation commands

adversarial CS suite; assert zero sends and no truth writes; audit/redaction scan.

## Done when

normal synthetic FAQ produces only reviewable draft; every risky/unknown path produces handoff.

## Blocked if

approved truth contract unavailable, need real model/channel, or policy lacks owner.

## Output 回报格式

intent matrix/fact lock/handoff proof, tests/Git, P06-03 handoff.

## Git completion

stage policy/fakes/tests/docs; no provider config/model calls.
