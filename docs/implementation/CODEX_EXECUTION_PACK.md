# Codex 分阶段执行包

> **使用状态：READY FOR REVIEW，不等于获准开始开发。** 本包将 [总计划](AI_NATIVE_SALES_OS_MASTER_PLAN.md) 转成可复制的阶段执行单与小任务卡。除非用户在具体任务中明确授权，Codex 不得 push、接生产账号、外发、发布、投放、下单、收款或使用真实客户/供应链数据。

## 使用规则

1. 一次只下发一张 Phase prompt 或一张前置已完成的任务卡；禁止把全包一次交给一个执行者。
2. 每次先以当前 GitHub/本地事实为准：读取 `AGENTS.md`、`PROJECT_ENTRY.md`、`docs/project/{BUSINESS_STATUS,SOURCE_OF_TRUTH,SCOPE_AND_BOUNDARIES}.md`、本计划相关页、分支/remote/status。
3. 未确认事实固定标记 `已确认 / 部分成立 / 待验证 / 推测`；不要将 fixture 或规划升级为业务事实。
4. 未指明 push 时，默认：在独立分支工作、只 stage 明确路径、可以本地 commit（如任务需要）但不 push；报告 remote readback 为未执行。
5. 所有实现任务都继承 [测试与回滚策略](TEST_AND_ROLLBACK_STRATEGY.md)；所有数据契约继承 [核心数据合同](CORE_DATA_CONTRACTS.md)。

## 第一批建议下发顺序

1. **P0-T1：工程骨架与依赖边界**。
2. **P0-T2：安全、fixture 与 AppleDouble/产物护栏**。
3. **P0-T3：遗产视频/DOCX/XLSX 回归基线**（可与 T2 并行；都完成后才 T4）。
4. **P0-T4：本地 compose、healthcheck 与最小 CI 测试**。
5. **P1-T1：scope、数据合同与 migration 基线**。

### 并行图例

- `→`：严格前置；`∥`：可并行但共享 contract 必须先冻结。
- 任务卡列出 `parallel`/`exclusive`。并行任务不得写同一文件；若需共同 schema，先由前置卡产生审核通过的合同。

---

## Phase 0 Prompt｜仓库整理与工程底座

```text
# Goal｜目标
在不触碰现有视频、DOCX/XLSX、研究和同步包的前提下，建立可测试的模块化单体工程骨架与遗产回归基线。本轮不实现业务功能。

# Context｜上下文
仓库：/Volumes/WD_BLACK/汾酒尼泊尔
基线：以当前 remote/main 与项目事实文件为准；远端默认分支可能与本地 main 不同，必须再次核验。
业务状态：供应链和外部执行仍 BLOCKED；所有示例均为 synthetic fixture。
设计依据：docs/implementation/AI_NATIVE_SALES_OS_MASTER_PLAN.md、ARCHITECTURE_AND_MODULE_BOUNDARIES.md、TEST_AND_ROLLBACK_STRATEGY.md。

# Constraints｜边界
允许：新增工程 skeleton、测试、配置占位、docs、ignore/扫描规则。
禁止：改动或移动 generate_happyhorse_*、assemble_final_video.py、DOCX/XLSX 脚本、原始资料、outputs、project_sync；读取 .env；新增生产账号/网络调用/真实数据。
不得新增不必要依赖；不做微服务；不 push，除非本任务明确追加授权。

# Impact check｜影响面检查
确认新增路径是否被 .gitignore 过滤、是否会被同步包误收录、是否碰到 AppleDouble/媒体/真实研究资料；确认现有脚本 CLI/manifest 可保持只读回归。

# Execution steps｜执行步骤
先确认仓库/branch/remote/status及必读事实；按任务卡顺序新增骨架和测试；运行最小验证、敏感扫描、diff审查；只 stage 本任务路径。

# Done when｜完成标准
P0-T1~T4 全部满足且测试通过：新骨架可启动、fixture guard有效、legacy回归基线存在、无秘密/真实资料/产物进入Git；业务状态文件不被误写为已开发。

# Blocked if｜阻断条件
工作树有不明重要改动；remote/默认分支无法核验；必须读取密钥或改遗产脚本；扫描发现真实秘密/私人数据。

# Output｜回报格式
Result；关键事实和分支；修改文件；任务完成/未完成；测试和失败分支；legacy影响；敏感扫描；git diff/stage/commit/push/readback；剩余风险和下一张可下发卡。
```

| 卡 | Goal / 文件范围 | 依赖与并行 | Done when / Blocked if |
|---|---|---|---|
| P0-T1 | 新建 `apps/{api,worker,admin}`、`core/{domain,application,contracts,security}`、`modules`、`adapters`、`workflows`、`fixtures`、`migrations`、`tests` 的最小 package skeleton 和 dependency-boundary test。 | 无；`exclusive`（定义目录/包名） | 禁止反向 import 的测试可跑；**阻断：**需改旧脚本或目录与现有 ignore 冲突。 |
| P0-T2 | 新增 synthetic fixture 标识、secret/PII/AppleDouble/media 预提交扫描与 `git check-ignore` 测试；必要时仅扩展 `.gitignore`。 | P0-T1 →；与 P0-T3 `∥` | fixture 不能被标作 production；`._*`/`.DS_Store`/`.env`/outputs 被排除；**阻断：**发现秘密值需停止并报告不回显。 |
| P0-T3 | 新建 `tests/regression/legacy`：记录视频/DOCX/XLSX/同步包脚本的路径、CLI help/manifest/hash 只读基线。 | 无；与 P0-T2 `∥` | 不调用真实模型/API且能证明原脚本未改；**阻断：**唯一测试方式需读取 `.env` 或重跑视频生成。 |
| P0-T4 | 新增 local-only `docker-compose.yml`、healthcheck、typed config placeholders、最小 lint/test 命令和 CI 文档。 | P0-T1/T2/T3 →；`exclusive` | 空服务可启动/关闭，未暴露生产端口/密钥；**阻断：**需要新云资源或生产凭据。 |

---

## Phase 1 Prompt｜真值中心、导入器、审批与审计

```text
# Goal｜目标
以严格 synthetic fixture 建立来源文件→提取→映射→候选→人工批准→版本化事实→审计的最小闭环。

# Context｜上下文
前置：Phase 0 已验收。数据定义以 CORE_DATA_CONTRACTS.md 为准；业务线必须隔离，真实供应链资料尚未到达。

# Constraints｜边界
允许：schema、migration、repository、fake parser、admin review 最小接口、测试与synthetic fixtures。
禁止：真实文件导入、真实价格/库存/SKU、自动批准、adapter生产写入、客服/内容直接读候选事实。

# Impact check｜影响面检查
检查 migrations 可回放；contract/version/approval/audit 是否会影响下游；确认 project_sync 未自动收录工程数据。

# Execution steps｜执行步骤
先冻结合同，再建 scope/migration，再实现导入与批准，最后跑 synthetic E2E/negative tests；每次变更只影响指定模块。

# Done when｜完成标准
同一 synthetic 文件幂等导入；无来源/版本/审批的字段无法 approved；冲突/过期/跨线/fixture外发全部失败关闭并有 audit。

# Blocked if｜阻断条件
数据合同存在未裁决冲突；审计无法 append-only；需要真实文件/密钥；approval 不能区分角色和scope。

# Output｜回报格式
同 P0，另加 migration plan、contract version、synthetic E2E correlation与每个拒绝路径的证据。
```

| 卡 | Goal / 文件范围 | 依赖与并行 | Done when / Blocked if |
|---|---|---|---|
| P1-T1 | 定义 scope、状态枚举、base entity 与 JSON/Pydantic contracts；valid/invalid fixtures。`core/contracts`, `fixtures/contracts`, `tests/contracts`。 | P0 →；`exclusive` | 三元 scope/source/version/state 缺任一即失败；**阻断：**业务线模型不明确。 |
| P1-T2 | 建 database schema/migrations：tenant/project/business_line、source/data version/audit/approval。 | P1-T1 →；`exclusive` | 临时库 up/down/upgrade 测试；审计不可普通更新；**阻断：**migration 会影响现有资料/表。 |
| P1-T3 | fake parser + ingestion job + extraction result + mapping/normalization candidate。 | P1-T1/T2 →；与 P1-T4 可 `∥` | 同 hash 幂等、行/页定位、低置信需 review；**阻断：**parser 对真实文件硬编码。 |
| P1-T4 | approval state machine + `approved_fact` read model + conflict/expired handling。 | P1-T1/T2 →；与 P1-T3 可 `∥` | 价格/库存/配送无 approval 不可读；拒绝/过期不 resume；**阻断：**任何自动批准路径。 |
| P1-T5 | 汇合 synthetic supply spreadsheet E2E、audit export、跨线/fixture guard。 | P1-T3/T4 →；`exclusive` | 全链路通过且失败路径有 audit；**阻断：**任一步少 source/version/approval。 |

---

## Phase 2 Prompt｜公开线索、CRM 与外联草稿

```text
# Goal｜目标
在无真实爬虫和无发送路径的条件下，用 synthetic public source 完成 snapshot→线索审核→CRM→外联草稿/批准的内部闭环。

# Context｜上下文
前置：Phase 1。现有 build_research_channels.py 是人工转录研究生成工具，不是运行时crawler；旧 JSON 不能被导入真实联系人。

# Constraints｜边界
只实现 port/fake/synthetic HTML；遵守 source policy、robots/terms、DNC；禁止私有数据、登录绕过、自动群发、真实联系人和发送adapter。

# Impact check｜影响面检查
确认 lead/CRM 只接 approved scope；DNC 由任何草稿/未来发送路径强制读取；导出不泄露个人资料。

# Execution steps｜执行步骤
先定义 source policy/snapshot 与去重contracts，后建CRM，再建草稿；最后测试“从未发送”的完整时间线。

# Done when｜完成标准
一条 synthetic snapshot 经人工审核才能建组织；DNC、跨线、过期事实和未授权联系人全拒绝；外联只有草稿/批准，0自动发送。

# Blocked if｜阻断条件
采集许可/数据边界不明确，或任务要求真实网页/联系人/外发。

# Output｜回报格式
同 P0，另列 source policy、snapshot证据、DNC negative test和明确的“外发次数=0”。
```

| 卡 | Goal / 文件范围 | 依赖与并行 | Done when / Blocked if |
|---|---|---|---|
| P2-T1 | source policy、snapshot、crawl port/fake 与 robots/terms failure contract。 | P1 →；`exclusive` | 禁止源不抓取且保留失败审计；**阻断：**需连真实网站。 |
| P2-T2 | lead candidate、指纹/去重、评分解释、人工审核队列。 | P2-T1 →；与 P2-T3 `∥` | 同名不静默合并，高证据要求可测；**阻断：**评分不可解释。 |
| P2-T3 | CRM organization/contact/opportunity/interaction/stage/DNC 领域模型。 | P1 →；与 P2-T2 `∥` | 跨线失败，DNC不可删除/绕过；**阻断：**需导入真实联系人。 |
| P2-T4 | outreach draft workflow，引用 approved facts和approval，不含发送adapter。 | P2-T2/T3 →；`exclusive` | 审批也不发出消息；事实过期/DNC必拒绝；**阻断：**被要求自动触达。 |
| P2-T5 | synthetic lead→CRM→draft E2E及审计/导出测试。 | P2-T4 →；`exclusive` | 完整时间线、0 sending actions；**阻断：**任何真实数据混入fixture。 |

---

## Phase 3 Prompt｜客服 AI 与人工接管

```text
# Goal｜目标
用 synthetic conversations 构建 draft-only 客服：意图/风险识别、approved fact检索、回复草稿和强制人工接管。

# Context｜上下文
前置：Phase 1。现有FAQ/人工转接是规则素材，尚非消息服务；客服绝不改真值。

# Constraints｜边界
只接 fake webhook与fake model；默认draft_only；禁止真实WhatsApp/Meta/TikTok、自动发送、价格/库存/退款/酒类等自动承诺。

# Impact check｜影响面检查
核验会话的scope/PII、webhook去重、事实过期、DNC与人工接管状态；日志不得存明文敏感内容。

# Execution steps｜执行步骤
先构建会话contract与policy，再模型port/retrieval/draft，最后fake webhook和human queue E2E。

# Done when｜完成标准
普通批准事实只生成可审核草稿；高风险/不确定/过期/DNC全部handoff；无自动发送且审计可追溯。

# Blocked if｜阻断条件
真实消息账号、PII留存规则不明、无approved fact契约或无法保证人工接管优先。

# Output｜回报格式
同 P0，另列每种高风险intent、hand-off proof、发送次数=0、事实版本失效证据。
```

| 卡 | Goal / 文件范围 | 依赖与并行 | Done when / Blocked if |
|---|---|---|---|
| P3-T1 | conversation/message/intent/draft/handoff contracts及隐私最小化存储。 | P1 →；`exclusive` | replay/idempotency和scope测试通过；**阻断：**真实消息字段必须落库。 |
| P3-T2 | policy engine：风险分类、禁语、事实可用性、`draft_only`。 | P3-T1 →；与 P3-T3 `∥` | 高风险无法生成sendable action；**阻断：**policy无法版本化。 |
| P3-T3 | AI/retrieval ports with fake adapters，严格只读 approved facts。 | P1/P3-T1 →；与 P3-T2 `∥` | expired/conflict不返回，provider替换contract通过；**阻断：**模型输出成真值。 |
| P3-T4 | fake webhook、handoff queue/admin review 状态机。 | P3-T1/T2/T3 →；`exclusive` | handoff暂停/恢复可审计；**阻断：**出现send endpoint。 |
| P3-T5 | synthetic customer-service E2E adversarial suite。 | P3-T4 →；`exclusive` | 价格/退款/酒类/食品安全/低置信全转人工；**阻断：**任一自动外发。 |

---

## Phase 4 Prompt｜现有视频链服务化与内容工作流

```text
# Goal｜目标
以 adapter/manifest 的方式将现有 HappyHorse/FFmpeg 工具链纳入内容任务、事实检查、QC和人工审批；绝不重写遗产脚本。

# Context｜上下文
前置：Phase 0的legacy baseline与Phase 1 approved facts。既有脚本能提交、轮询、重试、下载、合成、字幕和QC，但不是服务。

# Constraints｜边界
只用 fake provider/fixture manifest；不可读取DASHSCOPE_API_KEY、调用模型、覆盖outputs、改生成或合成脚本、发布内容。

# Impact check｜影响面检查
确认新wrapper不会改变原CLI/manifest/output语义；事实/禁语/素材权利检查在提交前失败关闭；single-batch no-retry尊重旧契约。

# Execution steps｜执行步骤
先定义content/video contracts和facts checker，后建legacy port与fake provider/QC import，最后做fixture workflow和regression。

# Done when｜完成标准
synthetic content从事实版本到QC/人工review完整可追溯；事实缺失/质量失败不能approved；旧脚本未修改。

# Blocked if｜阻断条件
需真实API key/视频生成、迁移旧outputs、改动legacy脚本或要求发布。

# Output｜回报格式
同 P0，另列legacy diff=none、provider calls=fake only、QC状态、人工发布状态=not implemented。
```

| 卡 | Goal / 文件范围 | 依赖与并行 | Done when / Blocked if |
|---|---|---|---|
| P4-T1 | content/video contracts、fact-version lock、forbidden expression及assets-rights checker。 | P1 →；`exclusive` | 未确认SKU/价格/素材必阻断；**阻断：**需读真实产品素材。 |
| P4-T2 | HappyHorse legacy port/manifest translator/fake provider；不改原脚本。 | P0/P4-T1 →；`exclusive` | success/fail/resume/no-retry contract通过；**阻断：**需调用真实API。 |
| P4-T3 | FFmpeg/QC legacy port、QC importer及approval state。 | P0/P4-T1 →；与 P4-T2 `∥` | QC fail不能approved；**阻断：**需覆盖旧outputs。 |
| P4-T4 | fixture content→video→QC→review E2E和legacy regression。 | P4-T2/T3 →；`exclusive` | 输出可审计但不可发布；**阻断：**旧hash/CLI基线变化。 |

---

## Phase 5 Prompt｜真实供应链资料替换 Fixture 与全链路回归

```text
# Goal｜目标
仅在书面供应链资料、数据授权和负责人到位后，把fixture替换为私有受控真实资料；以映射、审批和回归完成，而不重开发。

# Context｜上下文
前置：P1-P4模拟闭环。业务和外部执行状态仍以docs/project事实源为准；真实资料不能进Git。

# Constraints｜边界
先只读盘点/分类；真实文件留私有存储；不自动把数据批准、外发、报价、发布或接生产渠道。

# Impact check｜影响面检查
检查资料来源/日期/确认人、schema差异、PII/秘密、保留策略、业务线、mapping rule影响和下游draft失效。

# Execution steps｜执行步骤
先建立资料清单与访问边界，再做单格式mapping、人工approval、替换测试，最后跑全链路回归和差异报告。

# Done when｜完成标准
每条读取的真实事实可追到私有来源/批准/版本/有效期；所有生产/外部actions仍disabled；不含真实资料的回归报告通过。

# Blocked if｜阻断条件
无书面资料/授权/负责人、冲突不能裁决、发现未处理PII/secret或想把真数据提交Git。

# Output｜回报格式
Result；资料类别/数量而非内容；mapping coverage；冲突/缺失；approved/blocked counts；回归；数据留存；git（不应有真实文件）；下一步授权需求。
```

| 卡 | Goal / 文件范围 | 依赖与并行 | Done when / Blocked if |
|---|---|---|---|
| P5-T1 | 只读资料盘点、分类、访问/保留与业务线归属清单。 | 用户提供书面资料 →；`exclusive` | 不回显内容/密钥且有owner；**阻断：**资料/授权不明。 |
| P5-T2 | 单一格式 mapping adapter/rule 与私有样本验证。 | P5-T1 →；可按格式 `∥` | 字段定位/错误报告可用；**阻断：**规则被硬编码成未经确认值。 |
| P5-T3 | 人工approval/reconciliation：真实事实替换fixture、冲突/过期处理。 | P5-T2 →；`exclusive` | approved facts可溯源，fixture不泄漏；**阻断：**价格/库存/合规无书面确认。 |
| P5-T4 | 全链路回归：CRM/客服/内容草稿事实换版、失效和审计。 | P5-T3 →；`exclusive` | 所有草稿引用当前版本、0外部动作；**阻断：**下游仍读fixture。 |

---

## Phase 6 Prompt｜生产渠道、支付、库存与订单（当前 BLOCKED）

```text
# Goal｜目标
仅对一个被明确授权的外部动作/渠道，做受控生产adapter的设计、sandbox演练或最小接入；不假设其他渠道已授权。

# Context｜上下文
当前默认BLOCKED。前置必须有最新书面平台/当地合规、主体/品牌、真实商品/价格/库存/履约、账户归属、数据与收款责任、用户外部执行授权、owner和kill switch。

# Constraints｜边界
一次只处理一个adapter和一个动作；最小权限；feature flag关闭默认；先sandbox；禁止自动群发/发布/报价/退款/下单。

# Impact check｜影响面检查
审计可达性、PII/支付边界、幂等/retry、撤销、webhook、库存一致性、事故owner、外部不可逆性和回滚演练。

# Execution steps｜执行步骤
核对书面前置→建立port/fake→sandbox→人工批准流程→故障/kill-switch演练→仅在用户逐次授权后决定生产首件。

# Done when｜完成标准
本阶段仅在具体adapter的sandbox和回滚演练通过后完成；任何生产首件另需用户批准，技术通过不代表业务上线。

# Blocked if｜阻断条件
任一书面前置、合规、授权、owner、rollback或审计缺失；无法隔离scope；出现不可控外部副作用。

# Output｜回报格式
逐条前置证据状态；adapter范围；sandbox结果；失败/回滚演练；生产动作数；审计；剩余BLOCKED；不得将此报告写成上线。
```

| 卡 | Goal / 文件范围 | 依赖与并行 | Done when / Blocked if |
|---|---|---|---|
| P6-T1 | 针对一个渠道/动作完成授权与证据 checklist，不写接入代码。 | P5 + 书面证据 →；`exclusive` | 所有前置confirmed或保持BLOCKED；**阻断：**任何缺证据。 |
| P6-T2 | 建单一 adapter port、fake/sandbox client、feature flag、kill switch。 | P6-T1 →；`exclusive` | 无凭据/无生产调用即可测试；**阻断：**只提供生产账号。 |
| P6-T3 | approval/audit/idempotency/dead-letter/rollback 演练。 | P6-T2 →；`exclusive` | 重复/失败/撤销均可证明；**阻断：**无测试环境或owner。 |
| P6-T4 | 用户明确批准的单一生产首件（可选、单独任务）。 | P6-T3 + 明确授权 →；`exclusive` | 仅报告真实证据与外部结果；**阻断：**用户未明确批准。 |

## 不可并行的总清单

- P1-T1 → P1-T2；P1-T5 必须等待 P1-T3/T4。
- 任何 leads/CRM/customer service/content/video 代码不得在 P1 的 approved fact、audit、scope contract 前进入真实逻辑。
- 每个 Phase 的 E2E 与 phase gate 在所有子卡完成后执行；不能边写边宣布已过 Phase。
- Phase 5 必须等待资料与授权，Phase 6 必须逐 action 等待书面证据和用户明确授权。
