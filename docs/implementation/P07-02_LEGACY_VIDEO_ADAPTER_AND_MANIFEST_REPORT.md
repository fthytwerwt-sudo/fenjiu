# P07-02｜legacy video adapter 与 manifest 报告

> **状态：task_branch_validated；最终 commit / push / remote readback 以执行回报为准。**
>
> **状态回填边界：** `docs/project/*`、`docs/collaboration/COLLABORATION_STATUS.md`、`docs/collaboration/EXECUTION_HISTORY.md`、`docs/project/NEXT_ACTIONS.md` 与 `implementation_plan.yaml` 由 controller 在审查/集成后统一更新；本任务分支不回填这些全局状态文件。
>
> **执行日期：** 2026-08-09
>
> **精确工程基线：** 本地 `origin/main` `1033c7ab659df8a677a937b2b9bcb8f9b7141600`
>
> **任务分支：** `codex/p07-02-video-adapter-manifest`
>
> **范围边界：** 仅建立 stdlib、local-only、synthetic 的 provider-neutral `VideoPort`、versioned manifest、legacy adapter mapping、fake provider refs 和 manual QC refs。不调用供应商、模型、网络、FFmpeg 或 legacy 脚本；不读取 `.env*`；不生成、下载、导出、发布或覆盖媒体；不改变业务状态。

## 1. 结论

- 新增 `adapters/video/contracts.py`，定义 `VideoManifest`、`LegacyVideoAdapterSpec`、legacy probe baseline、provider/artifact/QC reference contracts 与 `VideoPort` protocol。
- 新增 `adapters/video/fake.py`，实现 zero-network `FakeVideoProvider`：`submit`、`poll`、`download_artifact_ref` 与 `create_qc_ref` 均只返回 reference，不写文件、不下载媒体、不产生外部调用。
- 更新 `adapters/video/__init__.py` 导出 P07-02 合同和 fake provider。
- 新增 `tests/contracts/test_legacy_video_adapter_manifest.py`，覆盖 manifest 版本锁、fake provider 流程、video-edit `no_auto_retry`、provider uncertainty manual review、legacy 未定位 baseline 和敏感/路径/外部 flag 拒绝。

## 2. Manifest 与 fake provider 合同

| 合同 | 已验证行为 |
|---|---|
| `VideoManifest` | 固定 `schema_version=video_manifest.v1`；锁定 `video_task_id`、fact/asset versions、policy version、manifest version、idempotency key、prompt hash、asset hashes 和 cost approval ref；不保存 prompt/text payload、真实 provider ID、路径或媒体。 |
| `LegacyVideoAdapterSpec` | 使用 provider-neutral refs 映射 legacy input/output；`video_edit` 必须 `no_auto_retry=true`，否则 fail closed。 |
| `FakeVideoProvider` | submit/poll/download/QC 全部 `external_call_count=0`；artifact 和 QC 仅为 refs/hash；QC 状态为 `manual_review_required`，不猜质量通过。 |
| provider uncertainty | 任一不确定 provider 状态进入 `manual_review_required`，`may_auto_retry=false`，不会重新提交。 |
| legacy baseline | 当前受控 Git 仍未定位 HappyHorse/DashScope/FFmpeg legacy 视频脚本；probe 记录为 `blocked_not_located`，不允许执行、读 env 或写 output。 |

## 3. Test-first evidence

- **RED**：新增 `tests/contracts/test_legacy_video_adapter_manifest.py` 后，首次运行 `python3 -m unittest tests.contracts.test_legacy_video_adapter_manifest` 失败于 `ImportError: cannot import name 'FakeVideoProvider' from 'adapters.video'`。
- **GREEN**：新增 P07-02 adapter contracts、fake provider 和导出后，P07-02 专项 5 项通过。
- **Scan repair**：P00 `--all-files` 首次发现测试负例里有本地绝对路径字面量；已改为运行时拼接，保留负向断言并使扫描通过。

## 4. Validation evidence

- `python3 -m unittest tests.contracts.test_legacy_video_adapter_manifest`：5 项通过。
- `python3 -m unittest tests.contracts.test_content_video_contracts tests.contracts.test_legacy_video_adapter_manifest`：13 项通过。
- `python3 -m unittest tests.contracts.test_audit_metrics_retry_dead_letter tests.contracts.test_action_policy_rbac_approvals`：16 项通过。
- `python3 -m unittest discover -s tests/architecture`：8 项通过。
- `python3 scripts/validate_regression_baseline.py --base-sha origin/main`：通过。
- `python3 scripts/validate_regression_baseline.py --base-sha origin/main --all-files`：通过。
- `python3 -m compileall -q -x '(^|/)\._' apps core observability modules adapters workflows tests`：通过。
- `python3 scripts/validate_gpt_project_mechanism_sync.py --no-report`：通过。
- `make regression`：通过；两轮 migration replay、negative constraints、architecture、regression、local-runtime、control-plane、contracts 与 ingestion tests 全部通过。
- 最终 diff、commit、push 和 remote readback 以本任务最终执行回报为准。

## 5. 工程治理检查

- `repository_hygiene_check（仓库卫生检查）`：新增内容仅为 stdlib contracts、fake provider、专项测试和报告；P00 default 与 `--all-files` 已通过，未发现 secret、token、cookie、本地绝对路径、媒体或 forbidden path。
- `configuration_validation（配置验证）`：未新增环境变量、配置文件、生产连接、真实账号、provider endpoint、model endpoint 或 SDK。
- `data_safety_check（数据安全检查）`：未读取或写入真实供应链、客户、价格、库存、资质、身份资料、海鲜资料、legacy 输出或媒体；所有 external flags 继续 false。
- `dependency_compatibility_check（依赖兼容检查）`：`not_applicable`；未新增或修改依赖。
- `failure_handling（失败处理）/ negative behavior test（负向行为测试）`：覆盖 `no_auto_retry`、provider uncertainty manual review、unknown legacy scripts、external flags、payload/path/credential-like refs 和 QC manual handoff。

## 6. 事实分级与剩余阻断

- **CONFIRMED（工程）**：P07-02 provider-neutral manifest、legacy mapping、fake provider refs、manual QC refs 和 `no_auto_retry` guard 已由专项测试和相邻回归验证。
- **CONFIRMED（工程边界）**：没有真实 provider/API/video call，没有 subprocess execution，没有 `.env*` 读取，没有 media file、output path、internal export、public publish 或业务状态升级。
- **BLOCKED（legacy 实体）**：HappyHorse/DashScope/FFmpeg legacy 视频脚本仍未在受控 Git 清单中定位；真实 wrapper 必须等授权位置、SHA-256、CLI `--help` 和 dry-safe input/output 行为回读。
- **BLOCKED（业务）**：真实 SKU、素材授权、平台酒类边界、价格、库存、主体/资质、账号、收款、履约、真实 content approval、provider cost approval、视频生成和公开发布仍未建立或未获书面证据。
- **不成立**：本任务不代表 Phase 7 完成，不代表视频可生成、可下载、可导出、可发布、平台允许、供应链已确认、销售或履约就绪。

## 7. P07-03 handoff

- P07-03 可消费 `VideoManifest.safe_summary()`、`ProviderRunRef.safe_summary()`、`VideoArtifactRef.safe_summary()` 与 `QualityControlRef.safe_summary()` 作为内部 QC/approval refs。
- P07-03 必须继续保持 `internal_export_allowed=false` 与 `public_publish_allowed=false`，直到另有明确任务卡、人工审批、业务闸门和 Phase 9 外部授权证据。
- provider uncertainty、legacy unlocated、QC unknown 或 fact/asset/policy 版本漂移时继续进入 manual review，不得自动换 provider、重投成本、重新提交或覆盖 artifact。
