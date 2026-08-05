# P07-03｜视频 QC、人工审批与内部导出

| 元数据 | 值 |
|---|---|
| task_id / phase | `P07-03` / `phase_07` |
| depends_on / can_run_in_parallel_with | `P07-02` / `P05-03`, `P06-03` |
| writes_to | content/video QC/workflow/admin/tests/docs |
| forbidden_paths | publish/social adapters, real media/model call, raw output archive, legacy scripts |
| estimated_risk / recommended_executor | high / Codex 5.6 Thinking + GPT review |

## Goal

完成 synthetic video 的 decode/format/subtitle/fact/source/QC、human approve/reject/revise 和 internal-export-only 流程。

## Context

技术 QC 不是内容/平台/业务批准；TikTok 酒类边界未核验时一律内部草稿/样片。

## Constraints

QC fails closed; `asset_origin=unknown` cannot export; publish flag/adapter absent and external publish count=0.

## 六层需求确认

- 目标层：内部质量闭环，不对外发布。
- 机制层：QC+human approval+current facts required; publish forbidden.
- 实现设计层：`primary_route=QC checks+approval state`；`fallback_route=manual QC queue`；`capability_status=synthetic`；`probe_required=bad artifact fixtures`。
- 流程层：artifact→QC→review→internal export/ref.
- 判断标准层：bad/missing/expired facts rejected, 0 publish.
- 反馈层：quality/rights/policy failure revision/manual hold.

## Impact check

logs do not store media, preserve manifest/hash/audit; no change legacy artifacts or business state.

## Must read

content plan, P07-01/02 outputs, P04 policy/audit, run-ready/runbook docs.

## Execution contract

- Capability status：synthetic internal QC/export only。
- Probe required：yes — bad-artifact/no-publish probe。

- Primary route：automated QC fakes, review workflow, internal export metadata.
- Fallback route：manual QC status with no artifact transfer.
- Allowed Codex autonomy：QC/workflow/tests/docs.
- Forbidden Codex guessing：platform permission, video quality, rights, approval identity.
- Required inputs：fake artifact/ref, fact/policy/asset locks.
- Required outputs：QC report, human decision, internal-only export reference.
- Execution entrypoints：video E2E / `make demo-run` synthetic.

## Execution steps

1. Implement technical and fact/policy QC checks.
2. Enforce approval/rejection/revision states.
3. Limit export to internal reference/storage; no publish port.
4. Test malformed, unknown asset, forbidden expression, expired fact.

## Validation commands

QC negative suite; assert external publish attempts=0; audit/redaction/legacy regression.

## Done when

content/video can run synthetic complete chain internally with human review and no external action.

## Blocked if

needs real video/provider, unknown rights need approval, or publish requested.

## Output 回报格式

QC/approval/no-publish proof, tests/Git, Phase 8 dependencies.

## Git completion

stage QC/workflow/tests/docs only; no media/output archives.
