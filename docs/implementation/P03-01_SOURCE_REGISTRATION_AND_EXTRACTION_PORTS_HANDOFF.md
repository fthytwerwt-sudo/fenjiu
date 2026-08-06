# P03-01｜原始登记、隔离存储与 extraction ports 执行交接

## Goal｜目标

- 只执行 `P03-01`：以 stdlib、local-only、synthetic fixture 建立 `source_file` 登记、private relative/reference storage locator、SHA-256 hash/idempotency、quarantine 与 type-specific fake extraction ports。
- 支持 synthetic `XLSX`、`CSV`、`DOCX`、`PDF`、image、folder manifest 与 JSON export；每个 extracted field 必须带可回读的 `page/sheet/row/cell/bbox/export_record` locator。
- 固定 `register → hash → extract → locate → staging`；只产生候选/暂存记录，绝不写 `approved` current truth。
- 本轮不读取或导入任何真实供应链资料，不实现 mapping/normalization/approval publish、UI、CRM、support、video、external adapter 或 production connection。

## Context｜上下文

- 目标仓库：`fthytwerwt-sudo/fenjiu`。
- 精确基线：远端 `main` `bce35a01fa7c13cce797069198ce71dcf29ea2dc`；本任务开始时本地 `HEAD` 与 `git ls-remote origin refs/heads/main` 一致。
- 工作区：从精确基线创建的干净独立 worktree；任务分支 `codex/p03-01-ingestion-ports`。
- P02-01/02/03 已建立 stdlib scope/source/version、append-only truth、isolation policy、sealed read grant 与 audit contract；P03-01 只能向 synthetic staging 边界提供候选，不能绕过 P02 current-truth guard。
- 当前业务资料和业务闸门没有变化；所有 external flags、`external_execution_allowed`、`business_external_ready` 继续为 false。

## Constraints｜边界

- 允许修改：`modules/ingestion/`、`adapters/storage/`、synthetic fixture metadata、合同/集成测试、本任务 handoff/report，以及实际受影响的工程状态、风险与执行历史。
- 禁止读取、复制、导入或修改：真实供应链包、原始 DOCX/XLSX/PDF/image、`.env*`、真实聊天/API/WhatsApp/email、legacy、outputs、Git/sync archive。
- 禁止新增：external network、production connection、external send/publish、UI/CRM/support/video、ORM/driver/new dependency。
- 数据最小化：数据库/记录/Git/log 不保存文件正文、真实本机绝对路径、secret；storage locator 仅允许规范化 private relative path 或 opaque reference。
- 安全失败：unknown MIME、oversize、path traversal、body/path/secret leakage、parse/OCR failure、缺 locator 均 fail closed，保留稳定错误码并进入 `blocked/manual` 或 quarantine，不猜文本。
- Python 私有命名不声称 auth/RBAC；production auth/RBAC/RLS、encryption、retention/legal region 继续 `DEFER`。
- Git：只 stage 本任务明确路径，禁止 `git add .`；不得 merge 或 push `main`；提交使用 Lore trailers。

## Impact check｜影响面

- 业务状态：不变化；SKU、价格、库存、主体/资质、账号、收款、履约和 TikTok 酒类边界继续 `UNKNOWN/BLOCKED`。
- 工程状态：仅在代码、test-first 证据、全量回归、扫描、独立复审、commit、push 与远端 core-file 回读全部通过后记录 P03-01 工程完成。
- 真值边界：P03-01 只创建 `fixture/staging/blocked` 候选，不创建 `approved_fact`，不向 P02 current truth repository 写入任何记录。
- 同步包/GPT Project 机制：不修改、不生成 Git/sync archive；只运行既有 mechanism validation 防漂移。
- 业务线隔离：所有 register/job/result 操作显式携带完整 scope；跨 tenant/project/business line fail closed。

## Must read｜必读

1. 根 `AGENTS.md`、GPT Project 机制包强制文件与 `PROJECT_ENTRY.md`。
2. `BUSINESS_STATUS.md`、`CURRENT_STATUS.md`、`SOURCE_OF_TRUTH.md`、`SCOPE_AND_BOUNDARIES.md`、`RISKS_AND_BLOCKERS.md`、`COLLABORATION_STATUS.md`。
3. P03-01 task card、`INGESTION_MAPPING_APPROVAL_PIPELINE.md`、`CORE_DATA_CONTRACTS.md`、`TEST_ACCEPTANCE_ROLLBACK_MATRIX.md`、`REAL_SUPPLIER_DATA_ONBOARDING_RUNBOOK.md`。
4. P02-01/02/03 task cards、contracts、tests、handoffs/reports、migrations 与 current validation entrypoints。

## 六层需求确认

- 目标层：建立 value-free synthetic source registration/extraction/staging contract，不导入真实资料，不发布真值。
- 机制层：完整 scope + safe locator + allowlisted MIME/size + content hash + type port + required field locator；任何缺失、跨 scope、不安全输入或 extractor failure 均 fail closed 并保留安全 failure record。
- 实现设计层：`primary_route=SourceFileRegistry + PrivateStorageLocator + ExtractorPort registry + type-specific fakes + StagingRepository`；`fallback_route=quarantine or blocked/manual metadata-only record`；`capability_status=stdlib local-only synthetic`；`probe_required=synthetic type fixture, rerun/parser version, cross-scope, quarantine and leakage probes`；`allowed_codex_autonomy=ingestion/storage contracts, fakes, tests, fixture metadata, report`；`forbidden_codex_guessing=file content, owner, clearance, field values, missing text`；`required_inputs=value-free synthetic payload bytes + scope + private locator + declared MIME`；`required_outputs=source/job/extraction/staging records with stable IDs, hashes, locators and failure codes`；`execution_entrypoints=ingestion contract suite + make regression`；`validation_commands` 见下；`blocked_if_missing=safe locator, supported MIME, bounded size, complete scope or field locator`。
- 流程层：register validates metadata → hash immutable bytes → quarantine or select fake extractor → extract only synthetic candidate descriptors → validate locators → append staging candidate/failure record；人工 fallback 只保留 metadata/error，不猜正文。
- 判断标准层：同 scope/hash/storage-locator-version 幂等；同 source/parser/mapping profile 幂等；parser version 变化产生新 job；全部类型 locator 可回读；unsafe/failed inputs 不进入 mapping/current truth；技术通过不等于业务、数据或外部执行通过。
- 反馈层：失败分别回 scope、locator、MIME/size、hash/idempotency、extractor/locator、staging retention 或 Git/环境；不得放宽 guard 或读取真实资料来绕过。

## Execution steps｜执行步骤

1. 先写失败测试，覆盖全部 synthetic 类型、hash rerun/idempotency/parser version、cross-scope、unsafe MIME/oversize/path traversal、unlocated field、quarantine/manual fallback、failed extraction retention 与 no body/absolute path/secret leak。
2. 建立 immutable stdlib contracts、stable error codes、scope/locator validation、source/job/result/staging in-memory repositories。
3. 建立 type-specific fake ports；fake 只消费测试提供的 value-free descriptor，不实现真实 ZIP/XML/PDF/OCR parser，不接外部程序或网络。
4. 建立 pipeline service，强制 `register → hash → extract → locate → staging`、跨 scope 拒绝、幂等和 failure retention。
5. 运行 focused tests、完整 regression（含 P02 migrations）、P00 default/all-files、mechanism validation、compile/shell/diff/path/leakage 检查与 Docker cleanup。
6. 自审后执行独立只读 code review；修复全部 blocker 并重跑受影响与完整验证。
7. 更新 P03-01 报告和必要工程状态；path-limited Lore commit，push 本任务分支并回读远端 branch/default/visibility/core files。

## Validation commands｜验证

- `python3 -m unittest discover -s tests/ingestion`
- `python3 -m unittest discover -s tests/contracts`
- `make regression`
- `python3 scripts/validate_regression_baseline.py --base-sha bce35a01fa7c13cce797069198ce71dcf29ea2dc`
- `python3 scripts/validate_regression_baseline.py --base-sha bce35a01fa7c13cce797069198ce71dcf29ea2dc --all-files`
- `python3 scripts/validate_gpt_project_mechanism_sync.py --no-report`
- `python3 -m compileall -q core modules adapters tests`
- `find scripts tests -type f -name '*.sh' -exec sh -n {} +`
- `git diff --check`、task-path diff/status、forbidden path/pattern/leakage scan。
- worktree-derived Compose project 的 containers/network/volumes cleanup 回读。

## Done when｜完成标准

- 七类 synthetic source 均可得到带 required locator 的 staging candidates；folder member locator 仍是 private relative/reference，不暴露 absolute path。
- hash/source/job/result rerun 幂等且 parser version 变化生成新 job；跨 scope 不能重用 source/job/staging。
- unknown MIME、oversize、path traversal、缺 locator、parse/OCR failure 全部 fail closed，保留稳定错误码和 metadata-only failure record，不产生猜测候选。
- repository records、exceptions、safe summaries、test fixtures 与 Git diff 不含正文、真实绝对路径或 secret；不创建 approved current truth。
- `make regression` 含 P02 migration replay/negative suite通过；P00 两种扫描、mechanism validation、compile/shell/diff/Docker cleanup 通过。
- 独立只读 code review 无未解决 blocker；本任务分支 Lore commit/push、remote HEAD/core-file readback 完成；worktree clean。

## Blocked if｜阻断条件

- 实现或验证需要读取真实供应链文件、`.env*`、生产聊天/API、external network 或 production connection。
- 无法保证 private relative/reference locator、bounded input、字段 locator、scope/idempotency 或 failure-retention 边界。
- 任一 unsafe/failed input 可进入 mapping/current truth，或记录/log/Git 出现正文、绝对路径、secret。
- 实现需要 ORM/driver/new dependency、真实 auth/RBAC/RLS 假设或打开 external flag。
- migration regression、P00 scan、mechanism validation、独立 review、push 或 remote readback 失败且无安全的范围内修复。

## Output｜回报格式

- 实际 source types、fixtures、fail paths、改动与简化、验证命令/结果、未测试项。
- `CONFIRMED` / `INFERRED` / `UNKNOWN` / `BLOCKED` 事实分级。
- 分支、commit、push、remote HEAD/core-file readback、剩余阻断与 P03-02 输入。
