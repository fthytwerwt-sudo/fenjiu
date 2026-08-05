# P03-01｜原始登记、隔离存储与 extraction ports

| 元数据 | 值 |
|---|---|
| task_id / phase | `P03-01` / `phase_03` |
| status | `PLANNED` |
| depends_on / can_run_in_parallel_with | Phase 02 / 无 |
| writes_to | `modules/ingestion/`、`adapters/storage/`、contracts/tests/fixtures |
| forbidden_paths | 真实供应链包、原始 DOCX/XLSX/PDF、生产聊天/API、Git/sync archive |
| estimated_risk / recommended_executor | high / Codex 5.6 Thinking |

## Goal

实现 `source_file`、quarantine、private storage reference、hash/idempotency 和 XLSX/CSV/DOCX/PDF/image/folder/JSON export 的 fake extraction ports。

## Context

真实资料尚未到；每个 extracted field 必须保留 page/sheet/row/cell/bbox 或 export record locator。

## Constraints

仅 synthetic fixtures；不把文件正文写进数据库/Git/log；不接生产 WhatsApp/email/API；不自动批准。

## 六层需求确认

- 目标层：登记/提取候选，不写真值。
- 机制层：unknown MIME/oversize/path traversal/quarantine fail closed。
- 实现设计层：`primary_route=SourceFile+ExtractorPort+fake`；`fallback_route=manual metadata entry`；`capability_status=synthetic`；`probe_required=fixture extraction`。
- 流程层：register→hash→extract→locate→staging。
- 判断标准层：同 input hash/version 幂等、locators 可回读。
- 反馈层：parse/OCR failure 留错误码，不猜文本。

## Impact check

不更改 legacy DOCX/XLSX/视频；storage locator 只允许 private relative/reference，不产生本机绝对路径。

## Must read

`INGESTION_MAPPING_APPROVAL_PIPELINE.md`、`CORE_DATA_CONTRACTS.md`、`P02-03`、`REAL_SUPPLIER_DATA_ONBOARDING_RUNBOOK.md`。

## Execution contract

- Capability status：synthetic ingestion/extraction only。
- Probe required：yes — fixture extraction/quarantine probe。

- Primary route：port + type-specific fakes + file profile + quarantine tests。
- Fallback route：unsupported source marked blocked/manual, no ad-hoc parser。
- Allowed Codex autonomy：ingestion contracts/adapters/tests/fixtures。
- Forbidden Codex guessing：file content, security clearance, source owner, field values。
- Required inputs：synthetic input pack, data contracts.
- Required outputs：source/job/extraction records with locators.
- Execution entrypoints：`make load-fixtures`, ingestion unit/integration tests。

## Execution steps

1. Register/hashing/classification/quarantine contracts。
2. Build fake extractors and locators for each supported source class。
3. Enforce idempotency/parser version and failure retention。
4. Test no path/body/secret leakage。

## Validation commands

ingestion fixture tests；hash rerun test；quarantine/path traversal tests；`make regression`。

## Done when

合成资料包可安全产出 staged extraction，任何不支持/不安全输入不进入 mapping。

## Blocked if

需读取真实私有文件、无 locator、或无法保证 private storage boundary。

## Output 回报格式

source types、fixtures、fail paths、scan、Git、P03-02 input。

## Git completion

只 stage code/tests/synthetic fixtures；不 stage source files/dumps/attachments。
