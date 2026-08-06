# 架构与模块边界

> **状态：RECOMMENDED，未实施。** 本文是 [Phase 0–8 总蓝图](AI_NATIVE_SALES_OS_MASTER_PLAN.md) 的工程蓝图；不改变当前汾酒业务范围或外部执行禁令。

## 1. 建议的第一版形态

采用一个部署单元中的 **模块化单体（modular monolith）**：一个 Python/FastAPI API、一个或多个同代码库 worker、同一个 PostgreSQL、一个队列/缓存服务，以及只做审批与审计的极简 admin。模块之间经 domain service 和 versioned contract 通信，而不是互相读表或调用第三方 SDK。

这不是“永远不拆服务”。满足以下任一证据后才评估拆分：视频 worker 的资源/失败域显著不同；采集工作需要独立的网络隔离；或独立模块已有稳定 API、独立部署需求和可测契约。否则，微服务只会增加部署、可观察性和 Codex 维护成本。

## 2. 目标目录蓝图（实施时创建；本轮不创建代码目录）

```text
apps/
  api/                 # FastAPI: 认证、查询、命令、webhook 接收
  worker/              # 队列 consumer；不暴露业务 HTTP API
  admin/               # 极简审批、审计、导入复核界面；可先 server-rendered
core/
  domain/              # 聚合、policy、状态机、领域事件；零第三方 adapter 导入
  application/         # use cases / command handlers / ports；唯一可调用 adapter port 的内层入口
  contracts/           # Pydantic/JSON Schema、事件版本、错误码
  security/            # tenant scope、RBAC、审计上下文、secret references
modules/
  truth_center/        # 资料、标准化、approved facts、版本、合规素材
  ingestion/           # 文件登记、提取、映射、review、批准
  leads/               # 公共来源快照、提取、去重、评分、审核
  crm/                 # 组织、联系人、机会、互动、拒绝联系、任务
  customer_service/    # 会话、意图、检索、草稿、handoff、policy
  content_video/       # content/video task、事实检查、QC、批准、legacy video port
adapters/
  storage/ database/ queue/ ai/ crawl/ crm/ support/ video/
workflows/             # LangGraph 或等价编排的薄层，仅调用 application ports
schemas/contracts/     # 可导出的 JSON Schema 与跨模块 contract fixtures
fixtures/              # synthetic-only，按 tenant/project/business_line 隔离
migrations/            # 可回放 DB migration；不得含真实数据
tests/                 # unit / contract / integration / e2e / regression
observability/         # logging、metrics、tracing、dashboard 定义
docs/implementation/   # 本计划、ADR、runbook、任务包
docker-compose.yml     # local-only dependencies，禁止承载生产密钥
Makefile               # 唯一、易理解的本地操作入口
```

### Phase 1 文件级入口冻结

P01-01 创建 skeleton 时只能建立空实现、README/module docstring、最小 import/test 护栏和 feature flag/config 占位，不接数据库、模型、网络、真实资料或 provider SDK。首批文件级入口如下：

| 路径 | owner | Phase 1 最小内容 | 禁止内容 |
|---|---|---|---|
| `apps/api/` | delivery/API | FastAPI app factory、health route、correlation/scope middleware 占位 | 真实 auth provider、webhook URL、外部发送或业务写入。 |
| `apps/worker/` | delivery/worker | worker bootstrap、queue fake consumer、idempotency shell | 真实 broker 账号、模型调用、外部采集、发布或支付。 |
| `apps/admin/` | delivery/admin | approval/audit 占位路由或静态 shell | 把 fixture 升级为 approved、真实用户/账号管理。 |
| `core/domain/` | domain | policy、状态枚举、领域事件占位 | provider SDK、数据库 session、HTTP client。 |
| `core/application/` | application | command/query handler、port interfaces、feature-flag checks | 直接读取 adapter 私有状态或绕过 approval。 |
| `core/contracts/` | contracts | scope、error、event、schema version 的最小 contract | 真实 SKU、价格、库存、客户或账号数据。 |
| `core/security/` | security | scope context、RBAC/action-policy 占位 | 真实密钥、cookie、生产身份。 |
| `modules/*/` | module owner | 每模块 README/docstring、空 service/repository contract | 跨模块直接读私表、真实资料导入。 |
| `adapters/*/` | adapter owner | fake/in-memory adapter skeleton 和 provider capability registry | 未核验 SDK、真实 token、真实 API 调用。 |
| `workflows/` | orchestration | thin runner interface，调用 application ports | 把 workflow DSL 当事实源或审批源。 |
| `fixtures/` | test data | `is_synthetic=true` 的最小 fixture metadata | 从真实资料复制或缺 synthetic 标记。 |
| `migrations/` | data platform | 空 migration 入口和命名规则 | 真实数据、生产连接串、不可回放 DDL。 |
| `tests/` | verification | architecture/import/flag negative tests | 需要外部网络、真实密钥或真实业务数据。 |

## 3. 依赖方向与禁止项

```mermaid
flowchart LR
  UI["apps/api + apps/admin"] --> APP["core/application"]
  WORKER["apps/worker + workflows"] --> APP
  APP --> DOMAIN["core/domain + modules"]
  APP --> PORTS["core/contracts / ports"]
  ADAPTERS["adapters"] --> PORTS
  DOMAIN --> CONTRACTS["core/contracts"]
  FIXTURES["fixtures"] --> CONTRACTS
```

禁止：

- `core/domain` / `modules` 导入 LangGraph、Crawl4AI、CRM、客服、视频或模型 SDK。
- 一个模块直接读另一个模块的私有表；跨模块只经 application query/command 或事件 contract。
- 外部 webhook 直接写 `approved`、`price`、`inventory`、`crm_stage` 或 `sent` 状态。
- AI 输出直接成为 `approved_fact`、外发消息、公开内容、正式报价、退款/订单决定。
- fixture 从真实资料复制，或在缺 `fixture` 标记时被 worker 加载。

### 单向依赖判定表

| From | May import/call | Must not import/call |
|---|---|---|
| `apps/*` | `core/application`、`core/contracts`、delivery middleware | provider SDK、模块私有 repository、真实 secret。 |
| `workflows` | `core/application` ports、workflow state contracts | `adapters/*` provider implementation、domain private mutation。 |
| `core/application` | `core/domain`、`core/contracts`、port protocols | provider SDK、HTTP crawler/client、video SDK、CRM/support SDK。 |
| `core/domain` / `modules` | `core/contracts`、领域 policy、同模块私有类型 | `adapters`、`apps`、`workflows`、外部 SDK、环境变量读取。 |
| `adapters` | port protocols、contracts、provider-specific client | 写入 approved truth、保存唯一业务真值、绕过 application policy。 |
| `fixtures` | exported contracts/schema | production settings、真实资料、未脱敏联系人。 |

## 4. 模块边界与 ownership

| 模块 | 拥有的数据与命令 | 允许读取 | 禁止做的事 |
|---|---|---|---|
| `truth_center` | source file 引用、事实候选、批准事实、版本、合规文件、素材、禁用表达 | 原始/提取数据、人工批准上下文 | 直接对外发布、接收 CRM 变更、替外部系统作真值 |
| `ingestion` | ingestion job、提取结果、mapping rule、review queue | 文件元数据、解析器、字段合同 | 覆盖原始文件、自动批准冲突字段 |
| `leads` | source snapshot、lead candidate、指纹、评分、审核结论 | 公开来源和允许的 truth facts | 私有数据采集、自动联系、绕过 robots/条款 |
| `crm` | organization、contact、opportunity、interaction、stage、do-not-contact | 已审核 leads、批准后的消息结果 | 覆盖 lead 来源、读取未授权客服文本、修改价格库存 |
| `customer_service` | conversation、message、intent、draft reply、handoff case | approved facts、forbidden expressions、已批准 FAQ | 自动承诺、改真值、绕过人工手动接管 |
| `content_video` | content/video task、script draft、fact check、QC、approval | approved facts、授权素材、legacy video port | 修改原视频脚本、发布内容、把未确认 SKU 写入成片 |
| `adapters` | provider-specific identifiers、sync cursor、retry metadata | ports/contracts | 存放核心业务状态或成为唯一真值 |

## 5. 多业务线隔离

所有可业务化实体必须拥有不可为空的 `(tenant_id, project_id, business_line_id)`：

- `tenant`：数据责任、账号边界和加密/导出授权边界；第一版可以只有内部 tenant，仍要保留字段。
- `project`：一个可审计的目标/环境，如“Fenjiu Nepal preparation”或“Seafood discovery fixture”。
- `business_line`：`fenjiu_nepal` 与 `seafood_nepal` 等；从创建、查询、worker payload 到审计事件均强制传递。

实施建议：PostgreSQL 复合外键/唯一约束、repository 自动 scope、测试中跨线读取必须失败。绝不以页面筛选或提示词代替隔离。真实业务线的运行开关单独配置，默认均为 `disabled`；fixture 不可提升为生产开关。

## 6. Legacy 资产的接入边界

P00-01 的受控 Git 审计未定位 HappyHorse / DashScope / FFmpeg legacy 实体；下表中的路径只是规划引用和未来 port 名称，不是当前可运行事实。除 `scripts/build_project_sync_pack.py` 与 `scripts/validate_gpt_project_mechanism_sync.py` 外，legacy 视频/研究脚本继续为 `DEFER/BLOCKED`，直到授权位置、SHA-256、CLI、输入输出和 dry-safe 行为被回读。

| 规划引用 | 状态 | 新系统中的位置 | 不能做什么 |
|---|---|---|---|
| `generate_happyhorse_shots.py`、`generate_happyhorse_video_edit_once.py` | `DEFER/BLOCKED` | `adapters/video/happyhorse_legacy_port` 的受控 subprocess/manifest adapter | 未定位前不得实现真实 wrapper；不得复制 API 实现；不把 `.env` 或请求响应写入数据库日志。 |
| `assemble_final_video.py`、`prepare_video_assets.py` | `DEFER/BLOCKED` | 由 content/video worker 调用的 post-process port | 未定位前只保留 `PostProcessPort` fake；不重写 FFmpeg/字幕流程；不直接发布/覆盖原输出。 |
| `build_video_execution_report.py` | `DEFER/BLOCKED` | QC/report reference port | 未定位前不得把 report 字段写成 contract truth；业务真值不从 report 倒灌。 |
| `build_research_channels.py` | `DEFER/BLOCKED` | `fixtures/research_channel_fixture` 的来源/字段参考 | 不作为 crawler，不导入真实联系人到 CRM；`research_channels.json` 保持 forbidden。 |
| `seafood_project_data.py` | `DEFER/BLOCKED` | 研究规则、FAQ、字段候选的审计输入 | 不能批量迁移商品、价格、联系人或“首批测试”结论到汾酒。 |
| DOCX/XLSX 生成脚本 | `DEFER/NEEDS_VERIFY` | 资料样本与格式回归样本 | 不成为 API/worker 的运行时依赖；原始 DOCX/XLSX/PDF 不入 Git/runtime。 |

## 6A. Optional adapter ports 与退出规则

这些 port 允许 Phase 1 先建 interface/fake，不允许选择未核验依赖版本或真实 provider：

| Capability | Port | Default status | Exit / fallback rule |
|---|---|---|---|
| workflow | `WorkflowPort.run/pause/resume/recover` | `planned_fake_only` | 简易 in-process runner 必须跑同一 contract；LangGraph 等组件未重验版本/许可/恢复语义前保持 `NEEDS_VERIFY`。 |
| crawl | `CrawlPort.fetch_snapshot/extract_public_fields` | `planned_fake_only` | CSV/manual import fallback 必须保留；任何 robots/条款/频率/地区合规不明时禁用真实 crawl。 |
| CRM | `CrmPort.export_interaction/import_stage/map_external_id` | `planned_fake_only` | PostgreSQL 内部 CRM domain 是真值；第三方 CRM 关闭后 scoped export 仍可读。 |
| support | `SupportPort.receive/draft/send_approved/handoff` | `planned_fake_only` | 默认 manual-only；无 approved fact、无授权账号或高风险意图时不发送并转人工。 |
| video | `VideoPort.submit/poll/fetch/run_qc` | `planned_fake_only` | fake provider 是 Phase 1/7 默认；legacy 实体未定位或 hash/CLI 不可验证时不得调用真实 HappyHorse/DashScope/FFmpeg。 |

## 7. 配置、队列、观察性与密钥

- **配置：** 类型化 settings 只读取环境变量/secret reference；仓库只保留 `.env.example` 占位符，禁止密钥值、Cookie、真实 webhook URL。
- **队列：** 所有异步 job 有 idempotency key、attempt count、safe retry policy、dead-letter 状态与业务线 scope；失败不能重复外发或重复创建事实。
- **日志：** JSON log 至少含 `correlation_id`、scope IDs、actor type、command、result、policy decision；不得记录消息全文、密钥、身份证明或私有附件。
- **审计：** 数据变更和批准是 append-only audit event；常规管理员不能删除。更正采用 superseding version，不覆盖历史。
- **本地外置盘：** 开发 compose 的 volume 需相对路径；AppleDouble `._*`、`.DS_Store`、`outputs/`、媒体和临时 PDF/DOCX 继续被 Git 排除。同步包 allowlist 只有在规划完成并通过敏感扫描后才可单独扩展。

## 8. 统一开发入口与环境合同

实施 Phase 1 时创建 `.env.example`，它只能包含键名、类型/用途和明显占位符，不能复制本机 `.env`。建议入口固定为：

```text
make bootstrap                    # 建虚拟环境/锁定依赖；不下载业务资料
make dev-up                       # 启动 local PostgreSQL、broker、API、worker/admin
make dev-down                     # 正常停止本地依赖
make migrate                      # 只针对当前 local database 执行 migration
make load-fixtures                # 只加载 is_synthetic=true 的资料
make ingest FILE=<private-path> BUSINESS_LINE=<slug>
make inspect-ingestion JOB_ID=<id>
make approve-ingestion JOB_ID=<id>
make regression
make demo-run BUSINESS_LINE=<slug>
make run-ready-report BUSINESS_LINE=<slug>
```

`bootstrap`、`dev-up`、`migrate` 不能隐式执行 `ingest`、外部 adapter、模型调用或网络采集；`ingest` 只允许私有受控文件路径，调用前检查业务线、文件哈希、MIME/大小、data classification 和 feature flag。任何真实配置应以 secret manager reference 或环境变量在运行时注入。

## 9. Legacy 兼容与迁移策略

| 资产 | Phase 0 基线 | 未来位置 | 本轮和实施阶段禁止事项 |
|---|---|---|---|
| `generate_happyhorse_shots.py`、`generate_happyhorse_video_edit_once.py` | `DEFER/BLOCKED`：P00-01 未定位 | `adapters/video/happyhorse_legacy_port`，仅在定位和 hash/CLI 通过后受控 subprocess 包装 | 本轮不改；后续不复制 API 逻辑、不读取/记录密钥、不调用真实模型作测试。 |
| `prepare_video_assets.py`、`assemble_final_video.py`、`build_video_execution_report.py` | `DEFER/BLOCKED`：P00-01 未定位 | `content_video` 后处理 port，未定位前仅 fake/manifest contract | 不迁移历史输出、不覆盖原文件、不将输出当 approved 商品事实。 |
| `build_research_channels.py` 与 `research_channels.json` | `DEFER/BLOCKED` / forbidden | synthetic public-source fixture / CSV fallback 参考 | JSON 与联系人不进 runtime/CRM，除非未来逐条来源审查与人工导入。 |
| DOCX/XLSX 与供应链生成脚本 | `DEFER/NEEDS_VERIFY` | ingestion parser fixture 和 regression source | 原始 DOCX/XLSX/PDF 不被移动、改名、写回或打包。 |
| `seafood_project_data.py`、海鲜 FAQ/CRM 文档 | `DEFER/BLOCKED` | 独立 `seafood` fixture 合同输入 | 不把商品、价格、客户、合规或业务结论带入 `fenjiu`。 |

实施任务如需把旧工具放入 `legacy_tools/`，必须先在独立任务中证明原路径兼容、调用方引用已迁移且 hash/CLI 回归通过；本规划不授权移动。同步包默认仍不打包整个 `docs/implementation/` 或任何 task card，因为它的严格 allowlist 面向最小项目事实交接。若未来需要纳入，只增加入口型、无敏感、低体积的索引文件，并单独运行同步包验证。

## 10. 实施前的架构验收

进入 Phase 1 前，必须证明：目录 skeleton 能在空数据库启动；modules 依赖图无反向 adapter；任一 fixture 不能以 production mode 运行；两个业务线不能跨读；worker 重试是幂等的；审计事件不能因为错误分支缺失。具体测试见 [测试与回滚策略](TEST_AND_ROLLBACK_STRATEGY.md)。
