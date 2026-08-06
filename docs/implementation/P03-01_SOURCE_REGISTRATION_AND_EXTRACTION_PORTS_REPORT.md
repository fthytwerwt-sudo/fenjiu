# P03-01｜原始登记、隔离存储与 extraction ports 报告

> **状态：remote_main_code_readback_verified**
>
> **执行日期：** 2026-08-06
>
> **精确基线：** 远端 `main` `bce35a01fa7c13cce797069198ce71dcf29ea2dc`
>
> **任务分支修复提交：** `e17196e06380827224a1463f01b53a9975382f22`
>
> **控制器远端 main 工程代码提交：** `f92612bf03b5ac740e52d1d56e99f9959369b9fb`
>
> **范围边界：** 只完成 stdlib/local-only/synthetic-only 的登记、hash、quarantine、fake extraction、locator 与 fixture staging contract；没有读取真实供应链文件，没有接 production storage/database/auth/RBAC/RLS，没有写 approved truth，也没有打开任何 external flag。

## 1. 结论

- `SourceFileRecord` 只保存完整 scope、private relative/reference locator、locator version、SHA-256、size、allowlisted MIME、synthetic marker、classification 与 quarantine metadata；不保存文件正文或真实本机绝对路径。
- `IngestionJobRecord` 以 `source_file + parser_version + mapping_profile_version` 幂等；input signature 同时绑定 extractor version、字段 hash 和 locator。parser 版本改变会产生新 job；同版本不同输出会以 `extraction_replay_mismatch` fail closed。
- `ExtractionResultRecord` 与 `StagingCandidateRecord` 只保存 field name、content hash、source/job/result lineage 和 traceable locator，不保存 extracted value。candidate 的 `workflow_state=staged`，但 `data_state` 永远保持 `fixture`，因此不能进入 P02 approved/current truth。
- 七类 fake ports 已建立：`XLSX`、`CSV`、`DOCX`、`PDF`、image、folder manifest 与 JSON export。fake 只回放 value-free synthetic descriptors，不读取真实文件、不实现 ZIP/XML/PDF/OCR parser、不调用外部程序或网络。
- 全批次先验证 locator 与 lineage，再原子写 result/candidate；任一字段失败时该批次为 0 staging write。runtime store 不再暴露单条 `append_result` / `append_candidate`，唯一 staging 写入入口强制 result/candidate 一对一、无重复且 lineage 一致；半批次以 `staging_batch_atomicity_required` fail closed。

## 2. Locator 与 source type

| Source kind | synthetic MIME | 必须保存的 locator |
|---|---|---|
| `xlsx` | OpenXML spreadsheet MIME | `sheet + row + cell` |
| `csv` | `text/csv` | `row + cell` |
| `docx` | OpenXML word-processing MIME | `page + bbox` |
| `pdf` | `application/pdf` | `page + bbox` |
| `image` | `image/png` / `image/jpeg` | `page + bbox` |
| `folder` | `application/x.synthetic-folder-manifest` | safe `member_relative_path + export_record` |
| `json_export` | `application/json` | `export_record` |

fixture allowlist 只新增 `fixtures/ingestion/synthetic_source_profiles.json`；`fixtures/ingestion/` 中其他文件仍被 `.gitignore` 拒绝。fixture 只有 source type、MIME、private locator 和 locator metadata，不含商品、价格、库存、资质、联系人、正文或凭据。

## 3. Fail-closed 与失败留存

| 路径 | 稳定结果 |
|---|---|
| unknown/invalid MIME | `unsupported_mime` → quarantine/manual |
| oversize / empty | `source_oversize` / `source_empty` → quarantine |
| absolute/private path traversal 或 folder member traversal | `storage_locator_unsafe` / `field_locator_invalid` → blocked/manual |
| 缺 field locator | `field_locator_required` → blocked/manual，0 partial staging |
| fake parse / OCR failure | `parse_failed` / `ocr_failed` → blocked/manual，保留 source/job/failure code，不猜文本 |
| cross tenant/project/business line | `cross_scope_forbidden` |
| same job 不同 extraction signature | `extraction_replay_mismatch` |
| secret-like correlation/locator/MIME/version/actor/idempotency/field metadata | `sensitive_metadata_forbidden`，不保留未经验证 scope/source/job 或原字符串 |
| real marker 或 external/business flag | `synthetic_input_required` / `external_execution_forbidden` / `business_external_ready_forbidden` |

同 scope/hash/storage-locator-version 的 private locator alias 返回 canonical existing source；MIME、source kind 或 size 不一致仍为 `source_registration_conflict`。失败记录只含安全 scope（通过验证时）、IDs、stage、稳定 code、input SHA-256 和时间，不含 body、raw text、value、secret 或 absolute path。

## 4. Test-first、自审与独立复审

- 首个 ingestion 测试运行按预期因 `fake_extractor_registry` 尚不存在而 ImportError；之后才实现 contracts/ports/store/pipeline/fakes。
- 自审发现并修复：多字段 partial staging、失败重跑 timestamp conflict、folder member traversal、extractor-version replay、store direct cross-scope append、fixture allowlist 过宽和 batch append failure retention。
- 独立 reviewer 第一轮为 `REQUEST CHANGES`：1 个 HIGH（secret-like `received_by/idempotency_key` 可原样留存）与 1 个 MEDIUM（同 hash 的 locator alias 被误判冲突）。修复并补回归后，原 reviewer 只读复现两条路径，最终 0 findings / `APPROVE`。
- 控制器随后发现 1 个 HIGH：已导出的 runtime store 仍公开单条 result/candidate mutator，且 batch 入口本身可接受半批次。本次 test-first 复现公共绕过，移除单条 mutator，并在批量入口写入前强制一对一完整性。原独立 reviewer 专项复核、独立复现 partial/duplicate 路径后为 0 findings / `APPROVE`。

## 5. 验证证据

- `make regression`：通过；P02 `0001` + `0002` migrations 连续 replay 两次，16 类 SQL negative constraints 通过，isolated PostgreSQL database/containers/network/volumes 已清理。
- Python suites：8 architecture + 14 regression + 8 local-runtime + 16 control-plane + 46 contracts + 14 ingestion，共 106 项通过。
- P00 default scan：通过；P00 `--all-files` scan：通过。
- GPT Project mechanism validation：通过，23 files、system prompt 3613 chars。
- `compileall`、全部 shell syntax、`git diff --check`：通过。
- Docker cleanup：worktree-derived Compose project `fenjiu-local-runtime-539997260` 的 containers、network、volumes 均为 0 残留。
- 禁止能力静态合同：P03-01 implementation 没有 file read、network、subprocess、database/ORM/client import；测试只读取已提交的 synthetic metadata fixture。

## 6. Git 与远端回读

- task branch：`codex/p03-01-ingestion-ports`；任务分支修复提交为 `e17196e06380827224a1463f01b53a9975382f22`。
- 控制器已依次集成任务提交和 AppleDouble 静态审计兼容性修复，并将 `main` 工程代码 push/readback 至 `f92612bf03b5ac740e52d1d56e99f9959369b9fb`；本地 `HEAD`、`origin/main` 和 `git ls-remote` 一致。
- `modules/ingestion/store.py` remote SHA-256：`2d9dd42fabdcd9952c8187f7ca8b3fcf4c8f975c8b5fe5c5b6aaf9c750b8dea8`。
- `modules/ingestion/pipeline.py` remote SHA-256：`e97e0d06236c84d7dcc7568c2726e6c8b87eba52fe187ae41b4ccdd8b09b56dd`。
- `modules/ingestion/contracts.py` remote SHA-256：`57ac6039f37388dc8d244e3833f4b09a2d9c82d6cd522158bc1af5915a880ed4`。
- `adapters/storage/fake_extractors.py` remote SHA-256：`6b0f89c8f0b348cefb93efe5bd436027ee219ff78cc41b4b99b2db8006233014`。
- `tests/ingestion/test_source_registration_and_extraction.py` remote SHA-256：`6388db73a3200894201a0feacb0b32f9354f4f46e4ed0dcc89190956c7922907`。该静态审计只忽略外置盘 `._*` AppleDouble sidecar，不忽略普通源码。
- P03-01 工程代码已合入、推送并回读 `main`；本报告状态回填后不生成或修改 sync archive。

## 7. 事实分级、剩余阻断与 P03-02 输入

- **CONFIRMED（工程）**：synthetic source registration/extraction、quarantine、locator、idempotency、failure retention、测试、独立 review、controller integration、`main` code commit/push 与远端 core-file readback 已完成。
- **部分成立（Phase 3）**：P03-01 只完成 synthetic/local engineering contract；P03-02 可在本次状态回填也被远端回读后，从新的精确 `main` 创建干净 worktree，仍不得引入真实资料或提升 approved truth。
- **BLOCKED / DEFER**：真实 source storage、真实 XLSX/CSV/DOCX/PDF/image/folder/JSON parsing、OCR、database adapter/driver、authenticated actor/RBAC、RLS、encryption、retention/legal region、production connection、approved publish 与所有外部动作。
- **P03-02 输入**：可复用 `SourceFileRecord`、`IngestionJobRecord`、`ExtractionResultRecord`、`StagingCandidateRecord`、`FieldLocator`、source/job/result IDs、content hash 与 parser/extractor/mapping profile version；P03-02 仍只能新增 synthetic versioned mapping、normalizer 与 missing/conflict/expiry/duplicate quality reports，必须保留 source+locator+rule lineage，未知字段/单位/币种/日期转 manual/blocked，不得补值或批准。

业务状态、SKU、价格、库存、主体/资质、账号、收款、履约、TikTok 酒类边界及所有 external flags 没有变化。
