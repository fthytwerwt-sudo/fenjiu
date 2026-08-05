# 分阶段路线、验收与停止条件

> **状态：RECOMMENDED / 无时间承诺。** 这是按“可运行闭环”而非“模块堆砌”划分的路线。每阶段的细任务、前置和并行关系见 [Codex 执行包](CODEX_EXECUTION_PACK.md)，测试细则见 [测试与回滚策略](TEST_AND_ROLLBACK_STRATEGY.md)。

## 0. 全阶段共同完成定义

一个 Phase 只有同时满足以下条件才可标 `phase_complete`：

1. 任务范围内代码/文档/contract 已审查，且没有遗留 mock 冒充事实；
2. 对应单元、contract、集成/端到端测试通过，失败路径也有证据；
3. 任何新增外部 adapter 都有退出/替换说明与 fake adapter contract test；
4. fixture、业务线隔离、审批/禁令、审计、幂等/重试均有自动验证；
5. 无 `.env`、Token、Cookie、私人联系方式、真实客户数据、媒体/大产物或本机绝对路径进入暂存；
6. 本阶段没有把内部技术通过写成供应链、合规、公开销售、客户接触或业务成果；
7. Git 仅 stage 明确路径、commit 使用 Lore trailers，push/远端回读由任务授权和实际结果决定。

若任一条件失败，只能是 `partial_completed` 或 `BLOCKED`，不得带入下阶段。

## Phase 0｜仓库整理与工程底座

| 项目 | 内容 |
|---|---|
| 目标 | 建立一个不会污染现有 DOCX/XLSX/视频生成链的可运行工程骨架，并锁定当前遗产工具行为。 |
| 前置 | 当前 repo/remote/branch 核验；工作树无无法解释的改动；不读取 `.env`。 |
| 任务 | 新建工程目录与 Python 工具链；local compose（PostgreSQL、队列）；typed config 仅占位；基础 lint/test；遗产视频与文档脚本的只读回归清单/manifest；敏感/AppleDouble/产物忽略与扫描。 |
| 文件范围 | `apps/`, `core/`, `modules/`, `adapters/`, `fixtures/`, `tests/`, `docker-compose.yml`, 工程配置、`docs/implementation/`；不得改原始业务资料、视频脚本、生成脚本或同步快照。 |
| 测试 | 空服务启动；最小 health check；import boundary test；`git check-ignore`；legacy manifest/CLI help 或 dry-run 只读测试。 |
| 验收 | 新骨架可在空数据下运行；现有 HappyHorse/FFmpeg/DOCX/XLSX 工具仍可被定位且未改；无秘密/真实资料进入 Git。 |
| 停止条件 | repo/默认分支/远端异常；遗产脚本需改动才能通过；发现 secrets/真实联系资料即停写、隔离报告。 |
| 回退 | 删除新增工程目录或回滚单个文档/配置提交；不触碰遗产资产。 |
| 建议角色 | `planner` 定义准则 → `executor` 骨架 → `test-engineer` 测试 → `verifier` 完成证据。 |

## Phase 1｜真值中心、导入器、审批与审计

| 项目 | 内容 |
|---|---|
| 目标 | 用 synthetic 文件建立 `raw → extract → normalize → review → approved fact` 闭环；人工批准、版本、来源和审计不可缺失。 |
| 前置 | Phase 0 完成；核心 schema/contract 已评审。 |
| 任务 | scope/RBAC 基础、migrations、source file registry、ingestion jobs、parser port、mapping/rule、事实候选/冲突、approval queue、append-only audit、fixture guard。 |
| 文件范围 | `modules/truth_center`, `modules/ingestion`, `core/contracts`, `migrations`, `fixtures`, `tests`；只新增，不改供应链原文件。 |
| 测试 | 同文件幂等；字段定位；冲突/过期；禁止无来源批准；approval replay；跨业务线隔离；fixture 不可变成 external action。 |
| 验收 | synthetic spreadsheet 通过人工批准形成 scoped/versioned approved facts；没有有效 source/approval 的价格、库存、配送、合规事实无法被读取。 |
| 停止条件 | 数据合同无法表达来源/版本/审批；审计有缺口；fixture 与真实数据无法隔离。 |
| 回退 | 禁用 importer/worker；事务回滚并保留 source/audit；用 migration down 仅在演练过且无真实数据时执行。 |
| 建议角色 | `architect` contract review → `executor` 实现 → `security-reviewer` scope/RBAC → `test-engineer` 失败路径。 |

## Phase 2｜线索采集、CRM 与外联草稿

| 项目 | 内容 |
|---|---|
| 目标 | 从 synthetic public snapshot 到审核组织、CRM timeline 和“可批准但不可发送”的外联草稿闭环。 |
| 前置 | Phase 1；source policy 和 DNC contract 定义完成。 |
| 任务 | source policy、crawl port fake、snapshot、lead extraction/dedupe/scoring、review、organization/contact/opportunity/interaction、stage policy、DNC、outreach draft/approval。 |
| 文件范围 | `modules/leads`, `modules/crm`, `adapters/crawl`, `workflows/outreach`, contracts/tests；不接真实 crawler、不导入旧 `research_channels.json` 的联系人。 |
| 测试 | robots/terms blocked；重复/同名人工合并；DNC 绝对阻断；跨线 lead/CRM 读写失败；草稿使用过期事实失败；无发送 adapter。 |
| 验收 | 一条 synthetic source 可得到审核后的 synthetic organization、机会和草稿；只有人工记录后才出现 sent interaction。 |
| 停止条件 | 采集策略不清、需要绕过访问控制、引入真实联系人、或发送路径被实现。 |
| 回退 | 关闭 crawl adapter 与 workflow；保留 snapshot/audit；撤销草稿批准，绝不删除 DNC。 |
| 建议角色 | `executor` leads/CRM 分 slice；`security-reviewer` 公开数据/个人数据边界；`verifier` 发送禁令。 |

## Phase 3｜客服 AI 与人工接管

| 项目 | 内容 |
|---|---|
| 目标 | 以 synthetic conversation 验证“可答事实 → 草稿；高风险/无事实 → 人工接管”，默认 `draft_only`。 |
| 前置 | Phase 1；approved fact 和 forbidden expression policy 可用。 |
| 任务 | conversation/message storage、intent port、policy engine、approved-fact retrieval、draft reply、handoff queue、审计/权限、fake webhook adapter。 |
| 文件范围 | `modules/customer_service`, `adapters/support`, `workflows/customer_service`, contracts/tests；不接 WhatsApp/Meta/TikTok 或生产模型账号。 |
| 测试 | fixture guard；webhook replay；敏感/高风险意图转人工；事实过期后草稿失效；人工接管暂停/恢复；无自动发送。 |
| 验收 | 每个 synthetic 客服案例可追到事实版本/政策/审批；高风险不产生可发送回复。 |
| 停止条件 | 无法保证事实可追溯、DNC/隐私策略未定义、或拟接真实消息账号。 |
| 回退 | 将全局模式锁到 `manual_only`；暂停 worker，保留会话/audit，撤销未发送草稿。 |
| 建议角色 | `architect` policy design → `executor` 实现 → `security-reviewer` PII/权限 → `test-engineer` adversarial cases。 |

## Phase 4｜现有视频链服务化与内容工作流

| 项目 | 内容 |
|---|---|
| 目标 | 将现有视频脚本封装为可审计 job adapter，使内容从 approved facts 到 QC/人工审批可模拟运行，而非重写 HappyHorse/FFmpeg。 |
| 前置 | Phase 1；Phase 0 的 legacy 回归基线。 |
| 任务 | content/video contracts、fact/forbidden-expression checker、legacy manifest translator、job state adapter、provider fake、QC importer、content/video approval、成本/重试 policy。 |
| 文件范围 | `modules/content_video`, `adapters/video`, `workflows/content_video`, `fixtures/video`, tests/docs；禁止修改 `generate_happyhorse_*`, `assemble_final_video.py`、既有 outputs。 |
| 测试 | legacy manifest success/failure/resume；single-batch no-retry；事实不完整/过期阻断；synthetic video 不能发布；QC 未过不能 approved。 |
| 验收 | fixture 能生成 content task→video job→QC→人工 review 的全审计链；旧视频工具链回归不变。 |
| 停止条件 | 需要迁移/覆盖旧 outputs、需要读取真实 key、或重写遗产脚本。 |
| 回退 | 拔掉 video adapter，旧脚本独立保留；撤销 content approval。 |
| 建议角色 | `executor` adapter；`vision`/人工复核 QC 标准；`verifier` 遗产回归。 |

## Phase 5｜真实供应链资料替换 Fixture 与回归

| 项目 | 内容 |
|---|---|
| 目标 | 在供应链提供书面资料后，以清洗/映射/审批/回归替换 fixture；证明系统可适配真实格式而非重开发。 |
| 前置 | P1-P4 模拟闭环通过；供应链资料、业务线、保留/访问授权和字段责任人均书面明确。 |
| 任务 | 私有资料登记、file classification、field mapping、差异/冲突报告、人工 approval、fixture-vs-real suite、CRM/客服/内容草稿失效与再生成、导出/审计包。 |
| 文件范围 | 私有运行存储与 mapping config；可提交的仅 schema、匿名 fixture、映射规则模板与测试。不得把真实文件、价格、库存或图片进 Git。 |
| 测试 | 每种实际格式可定位字段；冲突/缺失/过期；全链路内容与草稿不再引用 fixture；升级/降级和回滚演练。 |
| 验收 | 每条可用事实可追至书面来源、有效期和批准人；仍不等于可外发/公开销售。 |
| 停止条件 | 没有书面资料/使用授权、商业事实冲突无法裁决、资料含未处理 PII/secret、合规缺口。 |
| 回退 | 撤销批准事实版本、恢复 fixture-only mode、关闭所有外部 adapters；不删除原文件或审计。 |
| 建议角色 | `analyst` 资料盘点 → `executor` mapping → `verifier` data reconciliation → 业务负责人批准。 |

## Phase 6｜生产渠道、支付、库存与订单的受控接入

| 项目 | 内容 |
|---|---|
| 状态 | **BLOCKED：不排期，不因前序技术完成自动开启。** |
| 目标 | 仅在单渠道/单动作逐项获得授权后，建立可停止、可审计、可回滚的生产 adapter。 |
| 前置证据 | 当前平台/当地合规书面核验；主体/品牌授权；已批准真实 SKU/价格/库存/配送；账号/数据归属；收款、售后、退款责任；用户明确外部执行授权；演练环境与 owner。 |
| 任务 | 按 channel/action 单独启动：webhook/消息、发布、支付、库存、订单各一包；权限最小化、sandbox、allowlist、审批、dead-letter、监控、kill switch、人工演练。 |
| 验收 | 在 sandbox/小范围受控环境证明不可重复、可撤销、可审计、人工可以立即暂停；生产首件单独由用户批准。 |
| 停止条件 | 任一前置证据或回滚演练缺失；无法控制外部副作用；政策/合规不清；无法隔离业务线/PII。 |
| 回退 | 关闭 adapter credentials/feature flag，停止消费队列，保留审计与未完成 approval；对外补救由业务负责人决定。 |
| 建议角色 | `security-reviewer`、`architect`、`executor`、`test-engineer`、业务/合规负责人；不得只由 Codex 决定上线。 |

## Phase Gate 表

| 从 | 到 | 必须证明 | 绝不可作为证明 |
|---|---|---|---|
| 0 | 1 | 运行 skeleton、忽略/扫描、legacy baseline | 目录存在、mock 页面截图 |
| 1 | 2/3/4 | 来源-版本-审批-审计的 fixture 闭环 | 研究 JSON、未审核 mock data |
| 2 | 5 | lead/CRM/DNC/草稿均不外发 | 名单数量、草稿内容好看 |
| 3 | 5 | 高风险转人工、无自动发送 | 模型回复看似正确 |
| 4 | 5 | legacy adapter 不改旧工具且 QC 可追溯 | 成片可播放 |
| 5 | 6 | 真实资料已清洗批准且全链路不再读 fixture | 文件已上传、系统测试通过 |
| 6 | 外部执行 | 逐渠道/逐动作的书面授权与回滚演练 | 任何前置 Phase 完成 |
