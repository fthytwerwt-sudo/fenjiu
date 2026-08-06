# P03-02｜字段 mapping、清洗与数据质量执行交接

## Goal｜目标

- 只完成 local-only、stdlib、synthetic/value-free 的 versioned mapping profile、deterministic normalization fingerprint、quality reports 和 profile change replay/diff proof。
- 不读取真实文件、不保存原值、不写 approved truth、不执行 approval/publish/外部动作。

## Context｜上下文

- **基线**：`origin/main` `f92612bf03b5ac740e52d1d56e99f9959369b9fb`；当前 task branch `codex/p03-02-mapping-quality`。
- **输入合同**：P03-01 的 `SourceFileRecord`、`IngestionJobRecord`、`ExtractionResultRecord`、`StagingCandidateRecord` 与 `FieldLocator`，全部 synthetic/fixture-only。
- **当前状态**：初始代码提交 `a219463108ca3cf098920d57d17a6b7d8657b01f` 已被控制器标记 HIGH/not accepted，独立 reviewer 另发现 P03-01 lifecycle MEDIUM；profile-report provenance 与 lifecycle repair 代码提交 `969a2114c83350a606c917f4c9b8e11c72ca56f0` 已 push/readback，状态为 `task_branch_repair_remote_readback_verified_not_main`，未集成 `main`。

## Constraints｜边界

- 保持 `data_state=fixture`、`is_synthetic=true`、`external_execution_allowed=false`、`business_external_ready=false`。
- profile 缺失、source signature 不同、未知 field/attribute、scope/lineage 失败、冲突、过期或重复必须转 quality/manual；不得补值、选值或批准。
- mapping 前 source 必须为 P03-01 `SourceDisposition.REGISTERED`，ingestion job 与 staging candidate 必须为 P03-01 `IngestionWorkflowState.STAGED`；quarantine 或未 staging 只能产生 `lineage_invalid` / 零 candidate。
- 禁止引入依赖、parser/OCR、database/storage/auth/RBAC/approval、真实资料、网络或外部 adapter。

## Verification｜验证入口

- `python3 -m unittest tests.ingestion.test_mapping_normalization_and_quality`
- `python3 -m unittest discover -s tests/ingestion`
- `make regression`
- `python3 scripts/validate_regression_baseline.py --base-sha f92612bf03b5ac740e52d1d56e99f9959369b9fb`
- `python3 scripts/validate_regression_baseline.py --base-sha f92612bf03b5ac740e52d1d56e99f9959369b9fb --all-files`
- `python3 scripts/validate_gpt_project_mechanism_sync.py --no-report`

## Controller handoff｜控制器交接

1. 先复核 task-branch repair diff，特别检查 `MappingReport.profile_fingerprint` 由 engine 构造，registry 同时绑定 registered prior/current report/传入 profile，且 `MappingEvidence.validate()` 在 mapping 前以实际 P03-01 enum 拒绝 quarantine/non-`STAGED` lifecycle；不得出现 direct persistence、truth promotion、raw-value/path/secret leak 或 implicit mapping。
2. 回读 task branch 的 commit、push、remote HEAD 和 `mapping.py`/fixture/test/report hashes；不得把 task-branch 完成写成 `main` 或业务就绪。
3. 如集成，P03-03 仍需单独建立人工 approval/publish/refresh contract；本卡只提供 candidate/report/replay proof，不能作为真实值处理或批准入口。

## Blocked if｜阻断条件

- 控制器审查发现任何 mapping 旁路、scope/lineage 遗漏、实际值泄露、profile 静默覆盖或 fixture promotion。
- 下一步需要真实资料、新依赖、production storage/database、authenticated approval、实际业务或外部动作。
