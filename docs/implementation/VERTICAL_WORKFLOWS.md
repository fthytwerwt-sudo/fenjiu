# 五条纵向工作流与 Fixture 模拟闭环

> **状态：RECOMMENDED / 未实现。** 每条流程以 [核心数据合同](CORE_DATA_CONTRACTS.md) 为唯一数据语言，以 [架构边界](ARCHITECTURE_AND_MODULE_BOUNDARIES.md) 的 ports/adapters 设计为前提。外部账号、真实资料、自动发送和发布均不属于本轮或当前默认能力。

## 统一工作流约定

- 每次运行生成 `correlation_id`、scope IDs、actor、input hash、policy decision、job attempt 与审计事件。
- worker 只能处理有 idempotency key 的命令；可重试任务与不可重试外部动作分开。
- AI 输出永远是 `candidate`/`draft`，除非由具备权限的人通过 `approval_request` 产生 `approved` 版本。
- 任一 dependency 为 `fixture`、`expired`、`conflict`、`blocked` 时，外部动作一律失败关闭；系统可输出内部草稿/缺失报告。
- 人工审批的默认 SLA 不在系统内假设；过期请求必须失效而非继续执行。

## 1. 供应链资料导入 → 真值中心

| 项目 | 设计 |
|---|---|
| 输入 | 受控上传的 Excel、CSV、DOCX、PDF、图片或文件夹清单；可选人工字段说明。真实文件保留在私有存储，不进 Git。 |
| 输出 | 原始文件记录、提取结果、字段映射建议、缺失/冲突报告、待审核候选、批准事实版本。 |
| 完成状态 | `approved_fact` 已有来源定位、版本、有效期、scope、审批记录；不代表可公开销售。 |

### 步骤

1. API/admin 创建 `source_file`，计算 hash，依据 MIME/大小/病毒扫描策略设为 `quarantined` 或 `processable`；记录业务线与敏感级别。
2. 创建幂等 `ingestion_job`；parser adapter 只读取私有文件副本，生成 `extraction_result`，并保留页/Sheet/行定位。
3. mapping service 根据 file signature 建议 `mapping_rule`，写 `normalization_candidate`：单位、货币、日期、SKU、图片链接、合规文件等分开处理。
4. validation 对必填字段、范围、重复、同 scope 冲突、有效期、文件 hash 和 fixture/真实混用执行检查。
5. 自动通过的低风险字段仍为 `ready_for_approval`；价格、库存、配送、合规、品牌/产品身份及任一冲突字段创建 `approval_request`。
6. 审核人接受、修改或拒绝；接受后创建不可变 `data_version` 和 `approved_fact`，原候选保留来源与 decision。
7. 发布 `TruthFactsChanged` 内部事件；客服/内容草稿缓存失效，不触发对外同步。

### 失败与回退

| 情况 | 系统行为 | 回退/人工动作 |
|---|---|---|
| 文件不支持、损坏或疑似敏感 | `source_file=rejected/quarantined`，无提取 | 人工确认文件安全/补格式 adapter |
| OCR/表格置信度低 | `needs_review`，不得猜测补值 | 人工标记列/页，建立新 mapping rule |
| 价格/库存与有效 `approved_fact` 冲突 | 对应字段 `conflict`，下游草稿失效 | 审核人选择证据，生成 superseding version |
| job 中断或重试 | 同 hash + parser version 返回同一 job/结果 | 恢复 job；不重复创建事实 |
| 审批过期 | 候选保持 staging，审批请求 expired | 重新申请并复核来源是否仍有效 |

### 必留日志

source hash、parser/mapping 版本、字段定位、validation、人工 decision、产出的 version ID、失败码；日志不写文件正文、附件或秘密。

## 2. 公开名单采集 → 线索审核入库

| 项目 | 设计 |
|---|---|
| 输入 | 已批准的采集 source policy、公开 URL/目录、业务线范围、速率/robots/条款策略；或现有人工转录 fixture。 |
| 输出 | `source_snapshot`、结构化 lead candidate、指纹/去重结果、评分理由、审核队列；仅审核通过后可创建 CRM organization。 |
| 当前边界 | 这是公开资料发现，不是绕过限制的“万能爬虫”；不得收集非公开个人数据、登录墙数据或自动联系。 |

### 步骤

1. 人工批准 source policy：域名、目的、允许路径、频率、robots/条款检查、保留期、业务线和人工 owner。
2. crawl adapter 获取并 hash 内容；写 `source_snapshot`，包括时间、URL、policy/robots 结果和失败原因。被拒绝、限流或策略不明直接 `blocked`。
3. extractor 只产出公开业务字段与证据定位；每个 candidate 至少含名称、类别、城市/地区（可空）、来源链接和 snapshot 引用。
4. lead service 生成 source-aware fingerprint、计算重复候选、评分和解释；不得将模型置信度当作真实性。
5. 低证据 candidate 进入 `reviewed` 而非 CRM；高优先对象要求两处独立公开来源或人工证明。
6. 人工接受后创建/合并 `organization`，可选创建最小 `contact`；没有合法/公开依据的个人联系资料不得写入。
7. 写 `audit_event`，并创建默认 `do_not_contact` 检查；不创建发送任务。

### 失败与回退

- URL 失效、robots 禁止、条款/许可不明：保留失败记录和旧 snapshot，停采该源，不绕过。
- 同名/同域冲突：标记 `merge_candidate`，人工决定；不静默合并。
- 明确拒绝联系或撤回：创建 `do_not_contact`，阻断所有草稿/发送 adapter，保留最小证据。
- Crawl4AI 或其他工具更换：源策略与 snapshot contract 不变，只替换 adapter，并重跑契约测试。

## 3. 外联草稿 → CRM 跟进

| 项目 | 设计 |
|---|---|
| 输入 | 已审核 organization/contact、允许业务线、批准事实、品牌/合规 policy、CRM 阶段、明确的人工触达授权。 |
| 输出 | 仅内部 `draft_reply`/`outreach_draft`、关联 opportunity、建议下一步、人工审批请求与 interaction 模板。 |
| 明确禁止 | 自动群发、自动首次触达、自动短信/邮件/WhatsApp 发送、真实报价、以未批准库存/价格作承诺。 |

### 步骤

1. CRM 读取目标 scope 和 `do_not_contact`；无合法联系人、无授权、跨线或 DNC 命中时拒绝创建草稿。
2. workflow 从 `approved_fact` 读取允许表达；对 business_line、产品类别、禁用表达、真实业务范围做事实/合规检查。
3. 生成可编辑草稿，附 used fact version IDs、风险旗标、建议的 CRM stage 与下一步；没有价格/库存时只生成“待确认”型草稿。
4. 对所有 outbound draft 创建 `approval_request`；批准不等于自动发送，只允许用户/指定人员手动发送或在未来已授权 adapter 内一键确认。
5. 收到人工记录的真实发送/回复后才写 `interaction` 并更新 opportunity。无回复仅生成内部提醒；时间到期不会自动重发。
6. 拒绝、退订、投诉或无联系方式触发 DNC/hand-off，不使用模型“优化”规避拒绝。

### 日志与回退

保存草稿版本、事实版本、policy、批准和人为记录的发送证据；撤销批准、事实过期或业务边界变更时草稿立即 `expired`，新草稿必须再走审批。

## 4. 客服 AI 答复 → 人工接管

| 项目 | 设计 |
|---|---|
| 输入 | 将来接入的授权消息 adapter；本阶段可用 synthetic conversation fixture；approved facts、FAQ policy、禁语、人审规则。 |
| 输出 | intent、风险旗标、可发送/只能草稿的 reply、handoff case、会话/审计记录。 |
| 默认策略 | `draft_only`。即使未来开放低风险自动答复，也只能针对明确白名单 intent、批准事实和已授权渠道。 |

### 步骤

1. adapter 验证 webhook/消息签名、tenant/project/business_line 映射、去重 external message ID；未知 scope 隔离并报警。
2. 创建 `conversation`、不可变 `message`；AI 只提取 intent/entities/risk flags，不能执行动作。
3. policy engine 评估：消息包含价格、库存、配送承诺、酒类/年龄、退款、投诉、食品安全、账期、独家、大额订单、个人数据或低置信时，强制 `handoff_case`。
4. 若在允许 intent 白名单内，检索未过期 `approved_fact`，生成 `draft_reply`，保存 facts/policy/model version；若没有事实，只能说明“需要确认”，不得臆测。
5. 人工在 admin 修订、批准或拒绝草稿；只有未来 “channel enabled + approved action + no fixture + explicit user authorization” 同时成立时，adapter 才可发送。
6. 实际发送/转人工/解决均写 audit + message state；事实版本改变自动使相关未发送草稿失效。

### 失败与回退

- 模型/检索不可用：创建 `handoff_case`，发送能力保持禁用；不使用知识缓存猜测。
- webhook 重放：以 external message ID 幂等，不重复草稿/不重复外发。
- 人工接管后：自动答复暂停到手动恢复；每次恢复留审计。
- 发现个人/敏感信息：按留存策略最小化保存与访问控制，不能回写到公开 leads。

## 5. 内容与视频生产

| 项目 | 设计 |
|---|---|
| 输入 | approved product facts/素材、选题 brief、禁语/合规 policy、现有 HappyHorse/FFmpeg legacy adapter、人工成本/执行批准。 |
| 输出 | content task、脚本草稿、事实检查、video task manifest、QC、待人工审核文件引用；不等于发布。 |
| 遗产边界 | 复用现有 DashScope 任务状态、下载、重试和 FFmpeg/字幕合成；不重写，也不把已有 outputs 作为当前真实商品事实。 |

### 步骤

1. 创建 `content_task`，锁定已批准 fact version、授权素材与业务线；若当前没有真实商品资料，可只用标记为 fixture 的通用内部演示 brief。
2. 模型生成 script/storyboard draft，事实/合规 checker 比对 forbidden expressions、事实缺失、SKU/价格/库存/功效/许可声明。未通过者不能发起视频。
3. 人工批准内容 brief 和成本/模型调用；video adapter 将 approved manifest 转译为 legacy script 所需 input，不复制密钥也不改变原文件。
4. worker 提交/轮询/下载/重试；按 provider task ID 与 idempotency key 恢复。视频编辑一次性模式必须尊重其“不自动重试”契约。
5. 复用 FFmpeg 合成、字幕、probe/QC，写技术结果、素材 hash、脚本/事实版本；QC 未过、人工未验收则 `needs_review`。
6. 人工决定接受/拒绝/需修订；`approved` 的输出仍仅代表“可进入后续受控发布审批”，发布 adapter 在 Phase 6 前不存在。

### 回退

provider 失败/额度缺失/生成质量不合格时保留 manifest、状态和 QC，标记 failed/needs_review；不自动换模型、重投预算或公开替代内容。因事实过期而失效时，保留老稿作历史，不复用作新宣传。

## 6. 端到端 Fixture 模拟闭环

此闭环是 Phase 1-4 集成验证，不接生产账号、不调用真实客户/供应链/支付/发布。

```text
synthetic supplier spreadsheet
  -> ingestion + mapping + human approval
  -> approved synthetic facts
  -> synthetic public-source snapshot -> reviewed synthetic organization
  -> outbound draft (approval required; no send)
  -> synthetic inbound question -> draft reply / forced handoff
  -> content draft -> fact policy -> legacy video dry-run/manifest fixture -> QC record
  -> audit export + cross-business isolation checks
```

验收必须同时证明：

1. 全链路每条记录有正确 scope、source、version、data_state 与 audit event；
2. fixture 不能跨 business line、不能调用 send/publish/payment/order adapter；
3. 过期价格、库存冲突、DNC、客服高风险问题与视频事实不完整都准确阻断/转人工；
4. 重跑同一输入不产生重复事实、线索、机会或视频提交；
5. 删除/替换测试 fixture 后，不会留下隐式真实数据或无来源 approved fact。
