# P07-01｜内容/视频合同与 approved-fact lock

| 元数据 | 值 |
|---|---|
| task_id / phase | `P07-01` / `phase_07` |
| status | `PLANNED` |
| depends_on / can_run_in_parallel_with | Phase 04 / `P05-01`, `P06-01` |
| writes_to | `modules/content_video/`、contracts/migrations/tests/fixtures |
| forbidden_paths | legacy script implementation, real assets/video calls, `.env*`, external publish |
| estimated_risk / recommended_executor | medium / Codex 5.6 Thinking |

## Goal

建立 content_task/video_task、fact/asset rights lock、forbidden expression policy、synthetic brief 与 review/QC states。

## Context

真实 SKU/素材未到；内部样片必须 `synthetic` 标记，不能模拟真实商品、价格、库存或授权。

## Constraints

不调用模型/视频 API、不改 HappyHorse/FFmpeg、未批准 facts/assets/平台边界必 fail closed。

## 六层需求确认

- 目标层：内容生产数据合同，不是发布。
- 机制层：task locks fact/policy/asset versions; expiry invalidates.
- 实现设计层：`primary_route=content/video entities+fact checker`；`fallback_route=manual brief`；`capability_status=synthetic`；`probe_required=policy fixtures`。
- 流程层：brief→fact check→review→provider future→QC.
- 判断标准层：missing/unapproved/forbidden content cannot submit/export.
- 反馈层：unknown asset origin stays blocked.

## Impact check

inherits truth/scope/approval/audit; must not write `approved_fact`, publish, or alter legacy output paths.

## Must read

`CONTENT_VIDEO_SERVICEIZATION_PLAN.md`、core data contracts、P04 policy/audit, Phase 0 legacy baseline.

## Execution contract

- Capability status：synthetic internal content task only。
- Probe required：yes — fact/asset/policy negative probe。

- Primary route：contracts/state machines/fact checker/synthetic fixtures.
- Fallback route：no provider means internal manual-only brief.
- Allowed Codex autonomy：content/video domain/tests/docs.
- Forbidden Codex guessing：product claims, assets rights, platform alcohol policy, model capability/cost.
- Required inputs：approved synthetic facts/assets/policy vectors.
- Required outputs：locked task/check result/review states.
- Execution entrypoints：content policy suite.

## Execution steps

1. Create scoped content/video entities/state transitions.
2. Lock fact/asset/policy versions and source labels.
3. Implement fact/forbidden checker and invalidation.
4. Test AI-generated vs supplier-authorized vs unknown assets.

## Validation commands

content fixture policy tests; fact expiry/asset rights tests; no-video-call scan.

## Done when

only valid synthetic internal briefs reach review; no task can claim or publish unapproved facts.

## Blocked if

needs real assets/SKU/platform permission or fact checker cannot trace versions.

## Output 回报格式

states/fact locks/fail cases, tests/Git, P07-02 input.

## Git completion

stage domain/contracts/tests/docs only; leave legacy untouched.
