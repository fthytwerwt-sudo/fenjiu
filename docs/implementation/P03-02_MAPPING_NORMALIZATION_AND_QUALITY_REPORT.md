# P03-02｜字段 mapping、清洗与数据质量报告

> **状态：task_branch_partial_pending_commit_push_readback**
>
> **执行日期：** 2026-08-06
>
> **精确工程基线：** `origin/main` `f92612bf03b5ac740e52d1d56e99f9959369b9fb`，状态回填基线 `535857f376765b16c056049e3c9ae86a348fee64`
>
> **范围边界：** 仅完成 stdlib、local-only、synthetic/value-free 的 P03-02 mapping/quality contract。任务分支尚未集成 `main`；本报告不证明真实供应链资料、approved truth、业务资料就绪或任何外部执行。

## 1. 结论

- 新增严格的 versioned JSON-style `MappingProfile`、`TargetContract` 与显式 `MappingRule`。profile 必须同时给出完整 scope、version、source signature、冻结 target allowlist 和非空规则；未知字段或缺 profile 一律产生 `blocked_manual` report，绝不隐式 mapping。
- `SyntheticMappingEngine` 只消费 P03-01 的 `source_file → ingestion_job → extraction_result → staging_candidate` 链。每个 mapped candidate 保留 scope、source/job/result/staging IDs、`FieldLocator`、source content hash、normalization fingerprint、rule/profile lineage；不保存原值、正文、价格、联系人、绝对路径或 secret。
- deterministic normalizer 是 value-free contract：用既有 content hash、顺序固定的 transform IDs 和 unit/currency/date/language 的 known/unknown control status 得出稳定 fingerprint。它不声称已解析真实文本或真实单位/币种/日期/语言。
- quality engine 以稳定 fail-closed codes 报告 `required_missing`、unknown unit/currency/date/language、`mapping_conflict`、`duplicate_candidate`、`expired_or_stale`、cross-scope、lineage 和 source-signature failures。所有 finding 仅引用 candidate IDs，不自动选择冲突值。
- `MappingProfileRegistry` 拒绝同 version 静默覆盖，也拒绝不带 replay/diff proof 的 profile version change；`diff_replays` 输出仅含安全 fingerprints/semantic keys 的 append-only 证明。

## 2. 实际改动

- `modules/ingestion/mapping.py`：纯内存 mapping profile/parser、normalization fingerprint、quality reports、replay diff 与 append-only profile registry；无文件读取、网络、数据库、approval 或 truth write surface。
- `fixtures/ingestion/synthetic_mapping_profiles.json`：三个 synthetic profile（基础、version-change、required-gap），仅含 opaque IDs/hashes/descriptors；全部 external/business flags 为 false。
- `.gitignore`、`fixtures/README.md`、`tests/architecture/test_import_boundaries.py`：精确 allowlist 该一个 mapping fixture，其他 ingestion fixture 仍被忽略。
- `tests/ingestion/test_mapping_normalization_and_quality.py`：10 项 contract probes，覆盖 profile schema、lineage、manual fallback、unknown normalization attributes、missing/conflict/duplicate/freshness、scope/lineage/signature failures、replay/diff 和 value leakage。

## 3. Test-first、自审与验证

- **Test-first evidence**：首次运行 mapping suite 在 `modules.ingestion.mapping` 尚不存在时因 `ModuleNotFoundError` 失败；随后实现最小 contract 再通过。
- **Fixture allowlist evidence**：新增 allowlist assertion 首次失败（mapping fixture 被忽略），随后只放行该固定 synthetic path。
- **自审修复**：P00 `--all-files` 首次发现测试中用于断言的字面绝对路径模式；已改为运行时构造标记，同一断言保留，后续两种 P00 扫描均通过。
- `python3 -m unittest tests.ingestion.test_mapping_normalization_and_quality`：10 项通过。
- `python3 -m unittest discover -s tests/ingestion`：24 项通过（包含 P03-01 回归）。
- `make regression`：通过；P02 migrations 连续 replay 两次、16 类 SQL negative constraints 通过，8 architecture + 14 regression + 8 local-runtime + 16 control-plane + 46 contracts + 24 ingestion tests 通过，隔离 Docker resources 已清理。
- `python3 scripts/validate_regression_baseline.py --base-sha f92612bf03b5ac740e52d1d56e99f9959369b9fb` 与 `--all-files`：均通过。
- `python3 scripts/validate_gpt_project_mechanism_sync.py --no-report`：通过（23 files，system prompt 3613 chars）。
- `python3 -m compileall -q core modules adapters tests`、shell syntax、`git diff --check`：通过。

## 4. 显式 bypass review

| 检查项 | 结果 | 证据 |
|---|---|---|
| direct map/quality write | 无 | engine 只返回 immutable report；无 storage/database/approved import path |
| missing lineage 或 scope | 拒绝 | evidence 逐链比对 source/job/result/candidate IDs、scope、hash、locator；失败不生成 candidate |
| output/value leakage | 未发现 | reports 仅保留 IDs、hashes、locator、codes；fixture/value-free probe 和 P00 scans 通过 |
| generic profile acceptance | 拒绝 | exact schema keys、source signature、non-empty frozen target contract、unique rule/source validation |
| duplicate/replay drift | 拒绝 | stable sorting、content fingerprint grouping、same-version conflict 和 change-diff proof tests |
| truth/external promotion | 拒绝 | candidate data state 固定 `fixture`，`external_execution_allowed=false`、`business_external_ready=false`；没有 approval/publish route |

## 5. 事实分级、剩余阻断与控制器交接

- **CONFIRMED（任务分支本地工程）**：上述 mapping/quality/replay contracts 与验证已在 `codex/p03-02-mapping-quality` 工作树完成，尚待该分支 commit/push/readback 与控制器审查。
- **PARTIAL（Phase 3）**：P03-02 只处理 synthetic value-free capability；它没有接入 P03-01 runtime storage，也没有创建新的 ingestion job 或任何真实 candidate。
- **UNKNOWN / BLOCKED**：真实 profile/source signature、真实值解析/normalization、真实单位/币种/日期/语言、人工 mapping review、approval、truth publish、数据库、auth/RBAC/RLS、供应链业务闸门与所有外部动作。
- **控制器 handoff**：审查 task-branch diff；只在确认 task commit/push/remote readback 后决定是否集成。后续 P03-03 必须把真实/approved publish 继续隔离在人工审批与 P02 truth guards 之后，不能把本模块的 synthetic fingerprint 当作真实数据清洗或业务就绪。
