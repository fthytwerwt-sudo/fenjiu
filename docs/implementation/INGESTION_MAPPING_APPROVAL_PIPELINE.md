# 通用资料导入、映射、审批与版本链

> **状态：PLANNED。** 这是 Phase 3 的受控资料入口设计；本轮不导入、复制或解析任何真实供应链文件。

## 1. 标准链路

```text
raw 原始文件登记 → hash/来源/业务线 → 私有隔离存储 → 文本/表格/OCR 提取
→ 字段候选 → 标准字段映射 → 单位/币种/日期/语言清洗 → 质量检查
→ 缺失报告 + 冲突报告 + AI 建议 → 人工批准/驳回/修改
→ approved 真值版本 → supersede 旧版 → 下游缓存/草稿刷新 → 审计
```

所有真实输入都经 `source_file` 私有存储 reference；文件正文、截图、附件、客户信息与供应链资料不进入 Git、同步包或测试 fixture。支持的候选入口：`XLSX/CSV`、`DOCX`、`PDF`、图片/截图、目录资料包、`JSON/API`、WhatsApp/邮件导出的文本记录。生产账号连接不属于 Phase 3；后两类仅设计离线、受控 export adapter。

## 2. adapter 与 mapping 结构

### 2.1 输入 adapter port

```text
Probe(source_file) -> FileProfile
Extract(source_file, extraction_options) -> ExtractionResult
Locate(field_candidate) -> sheet/row/cell | page/bbox | message/export record
```

每种文件类型一个 adapter，adapter 只能提取和定位，不能写 `approved_fact`。目录资料包先创建 manifest（每个成员的 hash、大小、MIME、相对 logical path），按成员分别提取；压缩包路径穿越、密码保护、超尺寸、未知 MIME、疑似恶意内容一律 quarantine。API adapter 还需保存 endpoint allowlist、auth reference（非密钥值）、cursor、response hash 与速率 policy。

### 2.2 可版本化 mapping config

```yaml
mapping_profile:
  id: supplier_product_v1
  business_line: fenjiu_nepal
  source_signature: sha256-of-header-layout-not-private-data
  target_contract: product_sku_price_inventory_v1
  fields:
    - target: sku.sku_code
      from: {sheet: Products, column: SKU, locator_required: true}
      transforms: [trim, unicode_normalize, upper]
      required: true
      approval: required
    - target: price.amount
      from: {sheet: Pricing, column: Wholesale Price}
      transforms: [decimal, currency_from_column_or_context]
      required: true
      approval: required
  validation_rules: [unique_sku, currency_known, date_iso8601, no_fixture_mix]
  ai_allowed: [suggest_source_column, translate_label, normalize_unit]
  ai_forbidden: [invent_missing_value, resolve_conflict, approve_price_or_inventory]
```

AI 可基于 profile、header、样本定位和已批准字段字典提出 mapping/transform/置信度解释；它不得虚构 SKU、价格、库存、币种、日期、资质、负责人、素材权利或缺失文本。任何目标字段无 source locator 时保持 `missing`，不以默认值填充。

## 3. 只加配置与新 adapter 的界线

| 情况 | 允许动作 |
|---|---|
| 同一类 XLSX/CSV/DOCX/PDF，字段名称/列序/语言/单位变化，现有 extractor 可定位 | 新增/版本化 mapping config，先跑 fixture contract、再人工审查。 |
| 新表单 layout、扫描质量、OCR 语言、复杂嵌套表格导致现有 extractor 无法给定位 | 新 extractor adapter；先用完全合成样本证明，不能在生产文件上边写边猜。 |
| 供应链给 JSON/API，字段合同已存在 | 新 API adapter config + response snapshot/idempotency contract。 |
| 需要登录、验证码、个人账号、WhatsApp/邮件生产同步 | `BLOCKED`；只允许对方导出后离线导入，直至独立授权与合规审查。 |

## 4. 清洗、质量、批准与幂等

| 环节 | 必须做 | 失败行为 |
|---|---|---|
| 登记 | SHA-256、uploader/渠道、received_at、scope、敏感级别、保存位置、MIME/size | quarantine；不调用解析器。 |
| 提取 | 文本/表格/OCR、page/sheet/row/cell/bbox、extractor version/confidence | `needs_review`；保留失败码，不猜补。 |
| 映射 | 显式 profile version、field locator、transform、目标合同 | 无法映射的字段进 missing report。 |
| 清洗 | Unicode、单位、币种、日期、语言原文/译文；保留原值与 normalized value | 多义/未知单位或币种为 `blocked`。 |
| 质量 | required、格式、范围、重复、有效期、跨线、source/version、素材/证件 hash | 创建 missing/conflict report；阻止 publish。 |
| 批准 | reviewer 修改/拒绝/批准，记录 evidence、policy、version、actor | 高风险字段永远不自动批准。 |
| 发布 | 创建新 `approved_fact` / `data_version`、触发下游 refresh event | 不覆盖旧值；失败时不部分成功。 |

同一 `file_hash + source scope + parser_version + mapping_profile_version` 创建同一个或可安全恢复的 `ingestion_job`；同 hash 的重跑不重复 candidate/approved facts。改变 parser/mapping/profile 必须产生新 job/version 并给出差异报告。job worker timeout、崩溃或 DLQ 时保留 checkpoint 和 idempotency key；恢复只从未提交阶段继续。

## 5. fixture 与正式资料的绝对隔离

- fixture 存放在 Git 可审查路径，必有 `is_synthetic=true`、`data_state=fixture`、假 hash/source 和 no-external-action policy。
- 正式资料只能存在私有对象存储或本机受控目录；数据库只保存 reference、hash、metadata、短摘要/经策略脱敏内容。
- 同一 mapping profile 可以处理二者，但正式发布 require `data_origin=real`、批准人、来源 evidence、敏感分类和环境 allowlist；fixture 不能被“更新”为 real。
- 测试报告、audit export 和 log 只输出 ID、hash 前缀、field names、计数与 policy result；不回显原文、价格或联系方式。

## 6. 下游刷新合同

批准产生 `TruthFactsChanged(scope, fact_type, subject, version, effective_window)`。客服未发送草稿、CRM 外联草稿、内容/视频任务与缓存必须验证所锁定 fact version；若新版使旧版本 `superseded/expired/conflict/blocked`，它们自动停止、转人工或标失效，绝不静默改写已发内容/历史记录。
