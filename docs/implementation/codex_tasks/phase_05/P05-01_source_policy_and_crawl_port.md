# P05-01｜公开来源 policy 与 crawl port

| 元数据 | 值 |
|---|---|
| task_id / phase | `P05-01` / `phase_05` |
| status | `PLANNED` |
| depends_on / can_run_in_parallel_with | Phase 04 / `P06-01`, `P07-01` |
| writes_to | `modules/leads/`、`adapters/crawl/`、contracts/tests/fixtures |
| forbidden_paths | real website crawl, login/CAPTCHA bypass, `research_channels.json`, private contacts, external send |
| estimated_risk / recommended_executor | medium / Codex 5.6 Thinking |

## Goal

实现 source policy、snapshot、robots/terms/frequency gate 和 fake CrawlPort；默认不访问真实网址。

## Context

汾酒旧自动找客不在正式外部范围，Phase 5 是共享/内部 draft-only 能力。

## Constraints

每域一 policy/adapter；无 policy/robots/terms/owner 即拒绝；不得把公开页面或研究 JSON 当可联系授权。

## 六层需求确认

- 目标层：公开来源候选，不找客/外联。
- 机制层：blocked source has audit/no bypass.
- 实现设计层：`primary_route=SourcePolicy+CrawlPort fake`；`fallback_route=CSV/manual import`；`capability_status=synthetic`；`probe_required=no real crawl`。
- 流程层：policy approve→snapshot→extract candidate→review.
- 判断标准层：forbidden/no-policy source zero fetch.
- 反馈层：real source needs separate authorization/probe.

## Impact check

isolates business lines, protects personal data, preserves snapshots/hash and stops future Crawl4AI from owning data.

## Must read

`LEADS_CRM_IMPLEMENTATION_PLAN.md`、open-source strategy、P04 policy/audit output、data contracts。

## Execution contract

- Capability status：synthetic source/crawl port only。
- Probe required：yes — zero-network policy/snapshot probe。

- Primary route：policy model, fake fetch/snapshot, source evidence tests.
- Fallback route：structured CSV/manual candidate with same evidence contract.
- Allowed Codex autonomy：lead/crawl ports/fake/tests.
- Forbidden Codex guessing：site permission, robots terms, contact legitimacy, source facts.
- Required inputs：synthetic HTML/CSV fixtures, policy schema.
- Required outputs：source policy/snapshot/denial paths.
- Execution entrypoints：leads contract suite.

## Execution steps

1. Define policy/owner/allowlist/rate/retention fields.
2. Implement fake snapshot/hash/evidence locator.
3. Deny blocked/no-policy/login/private conditions.
4. Test source isolation/audit/export.

## Validation commands

policy/robots denial fixture tests; no-network test; audit/redaction scan.

## Done when

no real crawl occurs; approved synthetic source produces a traceable snapshot suitable for P05-02.

## Blocked if

real crawl/contacts are requested, policy cannot be approved, or source contains private data.

## Output 回报格式

policy fields, fetch count=0 external, tests/Git, P05-02 input.

## Git completion

stage ports/fakes/tests/docs only; no scraped content/lead data.
