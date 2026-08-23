# 项目上下文｜PROJECT_CONTEXT

本文件由同步包脚本生成，汇总最小必要上下文；完整规则仍以同包原文件为准。

## 项目入口

# 项目统一入口｜PROJECT_ENTRY

本文件是新 ChatGPT、Codex、Work 或人工协作者的业务优先导航；它不替代原始资料，也不把模板当作合作方已确认。

## 30 秒定位

- **当前正式范围**：汾酒仅做尼泊尔 TikTok 线上销售准备。TikTok 是当前主销售与内容渠道。
- **当前阶段**：供应链启动资料收集与首批 TikTok 商品上线准备，不是已经公开销售或履约。
- **用户负责**：线上账号运营、TikTok 内容制作与发布、商品展示和上架、客户沟通、订单转化，以及销售数据和市场反馈。
- **供应链负责**：当地合法销售与品牌/产品资质、SKU/规格/价格/库存、账号主体认证支持、当地收款、仓储配送、退换货、质量、售后和财务结算；这些均为确认的责任边界，不表示资料已交付。
- **当前最重要任务**：取得商品单、真实价格与规则、库存/补货、账号和认证支持、资质授权、收款、配送售后及明确负责人；资料齐备后再决定首批可上架 SKU。
- **不自动恢复的旧范围**：B2B 经销商开发、多平台独立运营、Facebook/Instagram 独立营销、YouTube/Viber、90 天试销、自动找客或自动外联。
- **海鲜资料线**：独立业务线；可共享有限协作机制，不能直接用于汾酒事实或决策。

## 必读顺序

1. 用户本轮明确输入，也就是 `P0（用户本轮明确输入）`。
2. [AGENTS.md](AGENTS.md)
3. [GPT Project 配合机制包](GPT项目资料同步包_gpt_project_mechanism_sync/00_GPT_Project上传说明_readme.md)
4. 本文件
5. [业务状态](docs/project/BUSINESS_STATUS.md)
6. [总览状态](docs/project/CURRENT_STATUS.md)
7. [事实源地图](docs/project/SOURCE_OF_TRUTH.md)
8. [范围与边界](docs/project/SCOPE_AND_BOUNDARIES.md)
9. [协作机制状态](docs/collaboration/COLLABORATION_STATUS.md)
10. 与当前任务直接相关的原始资料；不要用派生产物替代原始资料。

## 先分清可继续与不可进入的动作

- **可继续准备**：内部资料整理、供应链启动表、商品字段/上架资料设计、事实核验、合规与平台问题清单、受控草稿。
- **业务闸门阻断外部执行**：未取得当前书面证据前，不得公开发布、投放、收款、下单、承诺交期或开展真实履约。关键 `business_gates（业务闸门）` 包括 SKU、价格、库存、主体和资质、账号权限、收款、配送售后，以及 TikTok 酒类内容/广告边界；缺失时状态为 `BLOCKED`。

## 状态和交接

- 业务事实以 [BUSINESS_STATUS.md](docs/project/BUSINESS_STATUS.md) 为准。
- 协作与仓库收口事实以 [COLLABORATION_STATUS.md](docs/collaboration/COLLABORATION_STATUS.md) 为准。
- 当前摘要以 [CURRENT_STATUS.md](docs/project/CURRENT_STATUS.md) 为准；它只路由，不替代两份详细状态。
- 重要任务完成后更新状态、决策、风险、下一步和 [执行历史](docs/collaboration/EXECUTION_HISTORY.md)。

生成交接包：

    python3 scripts/build_project_sync_pack.py

把 project_sync/latest 或本地 ZIP 与 [同步包说明](docs/sync/README.md) 一并交给新会话。新会话必须先复述当前范围、阶段、职责、事实分级、阻断和完成标准，再执行。

GPT Project 配合机制包位于 `GPT项目资料同步包_gpt_project_mechanism_sync/`，用于用户手动上传到 ChatGPT GPT Project。它和 `project_sync/latest/` 不同：前者保存长期配合机制，后者保存 GitHub 项目事实交接快照。包已生成不等于用户已上传 GPT Project UI。

## 业务状态

# 业务项目状态｜BUSINESS_STATUS

- **最近更新**：2026-08-05
- **业务线**：汾酒尼泊尔主线
- **状态来源**：用户明确确认，2026-08-05；以及当前仓库原始资料存在性审计。

## 当前业务阶段

**CONFIRMED**：供应链启动资料收集与首批 TikTok 商品上线准备。

这表示可继续做内部资料、字段、清单和证据准备；不表示供应链已经交付资料，也不表示已可对外销售。

## 当前正式业务范围

- **CONFIRMED**：汾酒当前只做尼泊尔 TikTok 线上销售；TikTok 是主销售和内容渠道。
- **CONFIRMED**：WhatsApp Business、TikTok Business Center/广告账户、Facebook Page、Meta Business Manager、Instagram、官方网站、企业邮箱和当地收款账户可作为认证、广告、客服、询盘、收款或基础设施使用。
- **CONFIRMED**：上述辅助资产不自动成为独立营销主渠道。
- **SUPERSEDED**：旧研究中的 B2B 经销商开发、多平台独立运营、Facebook/Instagram 独立营销、YouTube、Viber、完整 90 天试销、自动找客和自动外联，仅在当前执行范围层面被替代；原始研究仍保留为历史背景，重新启用须由用户明确确认。

## 双方职责边界

| 角色 | CONFIRMED 的责任边界 | 不能据此推断 |
|---|---|---|
| 用户 | 线上账号运营、TikTok 内容制作与发布、商品线上展示和上架、客户沟通、订单转化、销售数据和市场反馈 | 已获平台权限、已完成发布或已成交 |
| 供应链 | 当地合法销售主体、进口/销售/品牌资质、产品合法可售、SKU/规格/价格/最低价/库存/补货、品牌素材、账号主体认证支持、当地收款、仓储发货配送、退换货、质量、售后和财务结算 | 任一资料已经提供、确认或可执行 |

## 当前已完成的内部准备

- **CONFIRMED**：汾酒市场、执行与文化/合规研究源文件存在。
- **CONFIRMED**：供应链启动文件/模板存在，商品、价格、库存、账号、资质和履约字段已被设计。
- **CONFIRMED**：当前范围、职责和资料收集优先级已被用户明确确认并写入项目状态。

## 正在进行

- **CONFIRMED**：整理和维护可交给供应链填写的启动资料入口。
- **UNKNOWN**：供应链是否已填写、回传或确认任何商品、价格、库存、账号、资质、收款或履约资料。
- **BLOCKED**：没有上述实际书面资料时，不能决定首批可上架 SKU，也不能进入真实外部销售。

## P0 待补输入

1. 真实 SKU、规格、商品图片/品牌素材、价格、价格有效期、最低销售价、库存和补货周期。
2. 当地销售/进口主体、产品合法可售、品牌授权与相关资质。
3. 账号主体、管理员权限和认证支持。
4. 当地收款主体、仓储、发货、配送、退换货、质量、售后和财务结算责任人。
5. TikTok 当前酒类内容、广告、账号和转化边界的书面核验。
6. 以上资料基础上确定的首批可上架 SKU。

## 可继续与必须停止的动作

- **可继续**：内部资料整理、供应链启动清单、商品信息收集、合规/平台问题核验、草稿和人工审核。
- **BLOCKED**：公开发布、广告投放、真实报价、收款、下单、发货、承诺交期、真实售后，直至对应 P0 输入和授权以当前书面证据解除。

## 海鲜资料线

**CONFIRMED**：尼泊尔海鲜为独立业务线，可有 B2B 与 B2C 范围。两条业务线可复用有限协作机制，但产品、客户、价格、资质、履约和业务结论不得互推；没有明确任务时，Agent 默认只处理汾酒主线。

## 更新规则

任何实际资料回传、责任确认或范围变化，都须附来源、日期、确认人和事实分级，并同步更新 OPEN_QUESTIONS、RISKS_AND_BLOCKERS、NEXT_ACTIONS 与必要的决策记录。

## 当前总览

# 当前项目总览｜CURRENT_STATUS

- **最近更新**：2026-08-23
- **用途**：本页只提供业务与协作的短摘要和路由；详细事实以链接文件为准。

## 业务状态摘要

- **CONFIRMED**：汾酒当前正式范围为尼泊尔 TikTok 线上销售准备，阶段为供应链启动资料收集与首批商品上线准备。
- **UNKNOWN**：供应链尚未在当前资料中实际提供 SKU、价格、库存、补货、主体/资质、品牌授权、账号权限、收款、仓储配送、售后及负责人确认。
- **当前最重要任务**：先补齐商品单、价格规则和库存，再确认首批可上架 SKU，并补齐账号、资质、收款和履约资料。
- **P0 阻断**：在上述资料及 TikTok 当前酒类内容/广告边界获得书面确认前，不能进入公开发布、广告、真实销售、收款、订单或履约。
- **已确认（内部规范层）**：已形成汾酒/海鲜独立的《尼泊尔精准客户获取标准与 Codex 输入规范》；它只定义未来客户发现、评分和 CRM 准入标准，不恢复自动找客/自动外联，也不解除任何业务闸门。
- **已确认（来源研究层）**：双业务线 Source Catalog（真实获客来源目录）已形成并提供 machine-readable（机器可读）YAML；状态为 `source_catalog_ready`，但真实企业发现、联系人处理、CRM 和外联均尚未开始或未获授权。

详情：[BUSINESS_STATUS.md](BUSINESS_STATUS.md)｜[OPEN_QUESTIONS.md](OPEN_QUESTIONS.md)｜[RISKS_AND_BLOCKERS.md](RISKS_AND_BLOCKERS.md)｜[NEXT_ACTIONS.md](NEXT_ACTIONS.md)

## 协作机制状态摘要

- **CONFIRMED**：固定入口、事实分级、任务交接、执行记录和同步包机制已建立。
- **CONFIRMED**：GPT Project 配合机制包已在仓库内生成并通过本地验证；包内 AGENTS 镜像与根 AGENTS SHA-256 一致。
- **部分成立**：远端 `main`、任务集成和同步包验证已持续回读；远端默认分支仍不是 `main`，GitHub API 的 visibility（可见性）仍未获认证回读。二者均不能由本文件编辑或本地 commit（提交）替代。
- **最近远端验证**：Phase 5–7 的最后五张任务卡已由 `origin/main` 回读至 `ae84e183be38da62d17c8567569f75206ddb35f1`；同步包将在本次状态回填后重新生成并验证。

## 工程规划状态摘要

- **CONFIRMED（规划层）**：`docs/implementation/` 已形成 AI Native Sales OS 的 Phase 0–8 分阶段蓝图、机器可读依赖图和每阶段 3 张 Codex 任务卡；该规划承接 GPT Project / GitHub / Codex 治理机制，不替代它。
- **部分成立**：本摘要不表示已创建可连接数据库的业务服务、队列、CRM、客服、视频服务或真实资料导入；技术实施仍须按 `docs/implementation/CODEX_EXECUTION_INDEX.md` 一次一张任务卡推进。
- **CONFIRMED（工程 Phase 0）**：P00-01、P00-02 与 P00-03 已完成远端回读；P00-03 在干净独立 task worktree 通过 12 项回归和两种扫描模式。外置盘根目录存在既有 ignored 禁入路径，故不得在该根目录运行 P00 default/`--all-files` 扫描；`make regression` 的 compile step 已显式跳过 AppleDouble metadata，但后续任务仍须在新建、干净的独立 task worktree 中启动。
- **CONFIRMED（工程 Phase 1）**：P01-01 至 P01-03 已在 `main` 远端回读：模块化单体 skeleton、synthetic-only fixture metadata、local-only Docker Compose / Make、静态 typed settings / FeatureFlagPort、liveness/readiness 与 JSON 脱敏日志合同均已建立。所有敏感 flags 默认 false，broker/provider/real configuration 不存在时 `/ready` 返回 HTTP 503；日志只保留结构化安全码并 fail-closed 脱敏自由文本、URL、DSN、Cookie、secret 和绝对路径。当前通过 8 项 architecture、14 项 regression、8 项 local-runtime 与 16 项 control-plane 测试；未接入应用数据库连接、外部网络、模型、SDK 或真实业务资料。GitHub Actions workflow 因当前凭据缺少 `workflow` scope 未写入远端；Phase 2 仍须在新建干净 task worktree 中逐卡推进。
- **CONFIRMED（工程 Phase 2 / P02-01）**：`main` 的 P02-01 代码已远端回读至 `b08722a703f37a0cfcce0c928fec8c01c4596357`：stdlib scope/source/version metadata contracts、local PostgreSQL schema migration 与 compound scope/lineage constraints 已建立。默认 `make regression` fail-closed 地执行隔离 PostgreSQL migration replay（两次）与五类负向约束，再运行既有测试；本轮总计 54 项 Python 测试通过，临时容器与 volumes 已清理。
- **CONFIRMED（工程 Phase 2 / P02-02）**：`main` 的 P02-02 代码已远端回读至 `0ba7f0575fdfe2906455c5b6301ac71c8872e727`：九类 value-free truth contracts、append-only parent/version chain、approval/effective-window current read、PostgreSQL trigger/view 已建立。review 发现 terminal root 可绕过 staging ancestry 后，已在 Python 与 SQL 双层限制 root 只能为 synthetic fixture/mock 或 non-synthetic staging；完整回归通过 73 项 Python 测试、两次 migration replay 与 16 类 SQL 负例。它只证明 local contract/state/read 防护，未接入 production database、真实 tenant/SKU/价格/库存、认证审批/RBAC、RLS 或任何外部动作；P02-03 isolation/audit 证据见下一项。
- **CONFIRMED（工程 Phase 2 / P02-03）**：控制器已将审查后的 P02-03 六笔提交安全集成，并将 `main` 推送、回读至 `451843601a1a610e50bfbd9794f437b5781f1401`。runtime probes 只存在于 tests-only harness；guarded current truth 必须通过 sealed policy grant、强制 audit，且 audit actor 只能来自包含 actor signature binding 的 validated grant。控制器与独立 reviewer 发现的 direct helper、unaudited direct read 和 actor attribution replacement HIGH 均已修复，最终专项独立复审 `APPROVE`；集成后 `main` 回归通过 92 项 Python tests、两次 migration replay 与 16 类 SQL 负例。该 runtime contract 不是 actor authentication/RBAC；P03-01 可在新的干净 task worktree 单卡启动，但 production database、真实 tenant/SKU/价格/库存、认证审批/RBAC、RLS 或任何外部动作仍未建立。
- **CONFIRMED（工程 Phase 3 / P03-01）**：控制器已将任务分支的 P03-01 提交安全集成，并从 `origin/main` 回读工程代码至 `f92612bf03b5ac740e52d1d56e99f9959369b9fb`。该代码仅实现 stdlib/local-only/synthetic source registration、private relative/reference locator、hash/job/result/candidate idempotency、quarantine、七类 fake extraction ports 与 fixture staging；runtime 单条 mutator 已移除，批量入口强制 result/candidate 一对一且在任何可见写入前 fail closed。控制器完整回归通过 106 项 Python tests、两次 migration replay 和 16 类 SQL 负例，mechanism validation 与 Docker cleanup 通过；独立专项复审为 0 findings / `APPROVE`。P03 AST 静态审计只跳过外置盘 `._*` AppleDouble 元数据，不跳过普通源码。真实 parser/OCR/storage/database/auth/RBAC/RLS/approved publish 与 external actions 均未建立。
- **CONFIRMED（工程 Phase 3 / P03-02）**：控制器已将修复后的 P03-02 安全集成，并从 `origin/main` 回读至 `355483121580c0205a43e59078eba8c29d719d93`。初始分支的 forged profile provenance HIGH 和 quarantine/non-`STAGED` lifecycle MEDIUM 均已由 profile fingerprint/report/replay binding 与 P03-01 lifecycle enum guard 修复；最终独立复审 `APPROVE`。控制器完整回归通过 118 项 Python tests、两次 migration replay 和 16 类 SQL 负例，mechanism validation 与 Docker cleanup 通过。它只提供 synthetic/value-free mapping fingerprint、quality 和 replay proof，不读取或保存真实值，不创建 approved truth，也不改变任何 external flag 或 business gate。
- **CONFIRMED（工程 Phase 3 / P03-03）**：控制器已将三笔已审查任务提交快进集成，并从 `origin/main` 回读至 `5d2c429bd253344ce3c2a3a30a31315f4a81f177`。P03-03 仅建立 stdlib/local-only/synthetic 的 candidate→review→human decision→isolated approved synthetic version→supersede/revoke→internal refresh 合同；其记录固定为 `DataState.FIXTURE`，不接入 P02 current truth。关联链完整性、过期审计状态与业务范围 current-read 索引均有独立回归；客户管理、客服和内容视频仅收到未来内部失效通知的合同枚举，未实现模块或外部动作。控制器复验 9 项专项、35 项 ingestion、完整 `make regression`（两次 migration replay、16 类 SQL negative constraints）、机制验证和排除 AppleDouble 元数据的编译检查均通过；两轮最终只读审查为 `APPROVE` 与无阻断评论。
- **CONFIRMED（工程 Phase 4 / P04-01）**：控制器已将三笔已审查任务提交快进集成，并从 `origin/main` 回读至 `d2805b293cbb71f7c5898ad0c611d863fb87e4b7`。P04-01 仅建立 stdlib/local-only 的 simple workflow runner（简易工作流运行器）、安全 checkpoint（检查点）、幂等恢复、暂停/批准/恢复、超时重试/死信队列和人工队列合同；可选 LangGraph probe（探测）因未安装而保持 deferred（暂缓），未新增依赖。审查先后发现 terminal approval replay（终态批准回放）和 public store write bypass（公开存储写入绕过）三项 HIGH，均已以 fail-closed（默认拒绝）状态守卫、受限写面和专项回归修复；11 项工作流专项、8 项架构、完整 `make regression`、机制验证与任务干净 worktree 的两种 P00 检查均通过。它不认证 actor（操作者）、不实现 RBAC（基于角色的权限控制）、不接外部 provider（服务提供方）或生产队列，也不改变任何外部动作开关。
- **CONFIRMED（工程 Phase 4 / P04-02）**：控制器已将已审查任务提交快进集成，并从 `origin/main` 回读至 `fd727fd0a74068edfa5511a18f878c312c062b6c`。P04-02 仅建立 stdlib/local-only/synthetic 的角色、动作策略与追加式审批合同；高风险复核必须精确绑定已批准请求的 `subject_version`（事实版本），同一幂等键的任一审批语义变化均拒绝，不执行外部动作。两轮审查发现并修复 subject-version 漂移与幂等语义复用；7 项策略专项、11 项工作流、8 项架构、完整 `make regression`、机制验证、排除 AppleDouble 元数据的编译和 diff 均通过。它不认证真实身份、不授予真实权限、不连接生产审计/队列，也不改变任何外部动作开关。
- **CONFIRMED（工程 Phase 4 / P04-03；Phase 4 工程完成）**：控制器已将三轮审查后的任务提交快进集成，并从 `origin/main` 回读至 `6cf2033b0376add9fabb6487d818d00f8a4805d1`。P04-03 建立 local-only 的追加式审计、重试分类、死信/人工队列可见性与脱敏指标/日志合同；审计成功记录失败会回滚暂存效果，提交失败会追加 `command_commit_failed`（提交失败）并标为人工处理，绝不静默写成成功。9 项专项、P04-02 的 7 项策略、P04-01 的 11 项工作流、8 项架构、完整 `make regression`、机制验证、排除 AppleDouble 元数据的编译和 diff 均通过。Phase 5、Phase 6 与 Phase 7 的首卡已解锁，但这不代表真实身份、生产审计/队列、真实供应链资料或外部动作已就绪。
- **CONFIRMED（工程 Phase 5 / P05-01）**：控制器已将审查后的任务提交快进集成，并从 `origin/main` 回读至 `f034857d5ec5715c2677e06d8add6338f65f50e1`。P05-01 仅建立 local-only 的来源政策、合成 snapshot（快照）/hash（哈希）/evidence（证据）与 fake CrawlPort（模拟抓取端口）；无 policy/owner/robots/terms、登录/私有来源、跨业务线或任一联系字段都拒绝，`external_fetch_count=0`。审查发现 public contact field（公开联系字段）越界后，已在政策、抓取、evidence 和 candidate 四层 fail closed（默认拒绝）修复；8 项专项、70 项合同、完整 `make regression`、机制验证与干净 worktree 两种 P00 检查均通过。它不抓取真实网站、不建立 lead/contact/CRM、不外联；P05-02 只能消费合成 snapshot/evidence/hash，不能抬升为可联系事实。
- **CONFIRMED（工程 Phase 5 / P05-02）**：控制器已在保留 P06/P07 合同的前提下集成并从 `origin/main` 回读至 `35d6e1f12ad6ed2e4bfa86a2c9f70463f9dcacb9`。P05-02 只建立 local synthetic 的 lead（线索）、CRM（客户管理）、DNC（拒绝联系）与受控导出合同：未审查来源、缺少同意、跨范围、模糊重复或任意外部开关都停止，导出只保留内部哈希与引用。并行任务导致的迁移碰撞已改为 P02 `0001/0002`、P06 `0003`、P05 `0004`；双次 migration replay（迁移重放）已精确断言四项均按序且只登记一次。91 项合同、35 项导入、完整 `make regression`、机制验证、编译和 diff 均通过。它不建立真实联系人、外联、发送、真实 CRM 或任何外部动作；P05-03 只能在新干净 task worktree（任务工作目录）继续。
- **CONFIRMED（工程 Phase 6 / P06-01）**：控制器已在保留 P05-01 的前提下集成并从 `origin/main` 回读至 `f02360d7e386f61b6b39cf2d8f3051e59fe21bc4`。P06-01 只建立 local-only 的会话、消息、意图、答复草稿、人工转交与 unknown scope（未知范围）隔离合同；已知范围的外部标识只保存 opaque reference（不透明引用），未知范围不生成可见会话或转交。6 项客服专项、84 项合同、35 项导入、完整 `make regression`、双次 migration replay（迁移重放）与负向约束、机制验证、编译和 diff（差异）均通过。它不接入渠道、模型、发送器、真实客户数据或外部动作；P06-02 只能生成合成、可审查的草稿或人工转交。
- **CONFIRMED（工程 Phase 7 / P07-01）**：控制器已在保留 P06 隐私合同的前提下集成并从 `origin/main` 回读至 `f02360d7e386f61b6b39cf2d8f3051e59fe21bc4`。P07-01 只建立合成 content brief（内容简报）、asset（素材）与 policy lock（政策锁）合同；事实、素材和策略任一缺失、过期、撤销、跨范围或带外部开关时均停止。8 项内容视频专项、84 项合同、35 项导入、完整 `make regression`、迁移重放、机制验证、编译和 diff 均通过。它不调用生成服务、不输出媒体、不导出或发布内容；P07-02 仅可接入模拟适配器与 manifest（清单）合同。
- **CONFIRMED（工程 Phase 5 complete）**：P05-03 已审查、集成并由远端 `main` 回读至 `37b19ed4bffff3b9d7a0341c6e756f71ce6ff6e4`。它只增加 synthetic（合成）outreach draft（外联草稿）/review（复核）/internal export（内部导出）合同；DNC（拒绝联系）、同意、来源、范围、事实锁和外部开关任一不满足均转人工，`external_send_attempts=0`。Phase 5 的 P05-01 至 P05-03 工程合同已完成，不建立真实联系人、外联或发送。
- **CONFIRMED（工程 Phase 6 complete）**：P06-02 已随 `aa5f2b6a4233dee70a3611b15d3593053319d98b` 集成，P06-03 已审查、集成并回读至 `bbc742d22bc0f19f6b2cbe8b7be7abc058b7f197`。P06-03 仅建立 receive-only fake inbox（只接收模拟收件箱）、合成 case（案例）与审计式人工接管/恢复；不含发送端、真实客户、渠道或模型。Phase 6 的 P06-01 至 P06-03 工程合同已完成。
- **CONFIRMED（工程 Phase 7 complete）**：P07-02 已随 `73b1a01cad82e01077b452a8486dc8211b567229` 集成，P07-03 已审查、集成并回读至 `ae84e183be38da62d17c8567569f75206ddb35f1`。它只允许基于 synthetic（合成）素材引用的 QC（质量检查）、人工决定和 internal export reference（内部导出引用）；`external_publish_attempts=0`，不调用视频服务、不写媒体、不发布。Phase 7 的 P07-01 至 P07-03 工程合同已完成。
- **BLOCKED（工程 Phase 8）**：P08-01 的依赖已经解锁，但任务卡要求当前、获授权的真实供应链资料包及其来源/范围/版本证据。当前仍缺 SKU（商品编号）、价格、库存、资质、授权及履约资料，故状态为 `BLOCKED / real_supplier_data_missing（阻断 / 缺少真实供应链资料）`；不得以合成 fixture（测试模拟数据）替代，也不得启动外部动作。
- **BLOCKED（外部业务）**：该规划不解除 SKU、价格、库存、主体/资质、账号、收款、履约或 TikTok 酒类边界的业务闸门；公开发布、报价、收款、下单和履约仍保持停止。

详情：[COLLABORATION_STATUS.md](../collaboration/COLLABORATION_STATUS.md)｜[SOURCE_OF_TRUTH.md](SOURCE_OF_TRUTH.md)

## 范围提醒

旧 B2B、多平台与 90 天研究已作为历史输入保留，且仅在当前执行范围层面被替代；海鲜资料线独立，不自动进入汾酒任务。

## 事实源地图

# 事实源地图｜SOURCE_OF_TRUTH

发生冲突时按下表读取。派生产物、截图、口头转述、聊天摘要和旧同步包不能覆盖排名更高且较新的原始来源。

| 信息类型 | 当前事实源 | 状态与说明 |
|---|---|---|
| 当前正式业务范围、阶段、职责、未知与业务阻断 | docs/project/BUSINESS_STATUS.md | **CONFIRMED** 的范围和职责来自用户明确确认（2026-08-05）；供应链实际交付仍须原始书面证据 |
| 项目总览与路由 | docs/project/CURRENT_STATUS.md | 短摘要；不替代业务或协作详细状态 |
| 协作、Git、同步包与远端回读 | docs/collaboration/COLLABORATION_STATUS.md | 远端 branch、commit、默认分支和 visibility 仅以最终回读为准 |
| 协作规则与阅读顺序 | AGENTS.md、PROJECT_ENTRY.md | **CONFIRMED** 的仓库规则和导航 |
| 当前执行范围 | docs/project/PROJECT_GOAL.md、SCOPE_AND_BOUNDARIES.md | **CONFIRMED**；旧研究不覆盖当前范围 |
| 已采用的业务与机制取舍 | docs/project/DECISIONS.md | **CONFIRMED**；每条决定须保留来源、日期、影响和状态 |
| 待补业务输入、阻断与顺序 | OPEN_QUESTIONS.md、RISKS_AND_BLOCKERS.md、NEXT_ACTIONS.md | **UNKNOWN/BLOCKED**；收到书面证据后再更新 |
| 汾酒市场、渠道和合规研究 | research_root.json、research_execution.json、research_culture_compliance.json | 资料存在为 **CONFIRMED**；涉及 B2B、多平台、90 天方案的内容为 **SUPERSEDED**（仅当前执行范围层面被替代），保留为历史市场背景，须由用户重新确认才可恢复 |
| 汾酒供应链启动模板 | 任务相关的汾酒供应链原始文件 | 模板和字段存在为 **CONFIRMED**；未签署、未回执或未回传的字段不得写为已确认 |
| 尼泊尔海鲜业务资料 | 海鲜原始资料线与对应供应链文件 | 独立资料线；不得自动用于汾酒结论 |
| 未来客户发现、评分与 CRM 准入标准 | `docs/implementation/NEPAL_CUSTOMER_TARGETING_SPECIFICATION.md` | **CONFIRMED（内部规范）**：定义两条业务线各自的产品-客户匹配、城市/关键词、字段、评分、来源/DNC 与 CRM 准入规则；不代表真实获客、联系人处理、发送、供应链资料或合规已获授权。 |
| 真实客户来源目录与机器配置 | `docs/implementation/FENJIU_SOURCE_CATALOG.md`、`docs/implementation/SEAFOOD_SOURCE_CATALOG.md`、`docs/implementation/source_catalogs/` | **CONFIRMED（来源研究）**：逐项记录来源 owner、入口、条款/访问证据、字段和 use decision（使用裁决）；只允许目录标明的最小企业发现动作，不代表联系人、CRM、外联、产品事实或合规已就绪。 |
| 生成逻辑 | 根目录生成脚本与 scripts | 脚本存在/运行结果不等于业务事实 |
| P01 local-only runtime 与 control plane 验证 | `docker-compose.yml`、`Makefile`、`apps/*/local_runtime.py`、`core/security/`、`observability/`、`tests/local_runtime/`、`tests/control_plane/`、`docs/implementation/P01-02_LOCAL_RUNTIME_AND_MAKE_ENTRYPOINTS_REPORT.md`、`docs/implementation/P01-03_CONFIG_FLAGS_HEALTH_AND_OBSERVABILITY_REPORT.md` | **CONFIRMED（工程）**：`main` 代码已远端回读；仅证明 local-only runtime、disabled flags、not-ready control plane 和日志脱敏边界，不代表数据库接入、远端 CI、供应链、合规或业务执行成立 |
| P02-01 scope contracts 与 migration 防护 | `core/contracts/`、`migrations/0001_scope_contracts.sql`、`fixtures/synthetic_metadata.json`、`tests/contracts/`、`tests/migrations/`、`docs/implementation/P02-01_SCOPE_CONTRACTS_AND_MIGRATIONS_REPORT.md` | **CONFIRMED（工程）**：`main` P02-01 代码已远端回读至 `b08722a703f37a0cfcce0c928fec8c01c4596357`；仅证明 synthetic local metadata、scope/lineage database constraints 和隔离 migration regression，不代表 production database、真实 scope、真实业务数据、审批、供应链、合规或外部业务执行成立 |
| P02-02 truth contracts、version/state 与 current read 防护 | `modules/truth_center/`、`migrations/0002_truth_entities_versions_and_states.sql`、`tests/contracts/test_truth_contracts.py`、`tests/migrations/`、`docs/implementation/P02-02_TRUTH_ENTITIES_VERSIONS_STATES_REPORT.md` | **CONFIRMED（工程）**：`main` P02-02 代码已远端回读至 `0ba7f0575fdfe2906455c5b6301ac71c8872e727`；仅证明 value-free local contracts、append-only migration/trigger/view 与 fail-closed current read。它不代表真实业务资料、人工身份/RBAC、production isolation、合规或外部执行成立 |
| P02-03 isolation policy、fixture/consumer denial 与 audit contract | `core/contracts/access.py`、`core/security/isolation.py`、`core/application/truth_consumer.py`、`modules/truth_center/repository.py`、`tests/contracts/test_isolation_policy.py`、`tests/contracts/truth_repository_harness.py`、`docs/implementation/P02-03_ISOLATION_POLICY_AND_CONTRACT_TESTS_REPORT.md` | **CONFIRMED（工程）**：控制器已安全集成并从远端 `main` `451843601a1a610e50bfbd9794f437b5781f1401` 回读；guarded current read 在返回 truth 前强制 audit，actor attribution 由 signed grant 固定。只证明 local capability attribution integrity，不认证 actor 真伪，也不代表 production auth/RBAC/RLS、真实资料或外部执行成立 |
| P03-01 source registration、private locator、quarantine 与 fake extraction | `modules/ingestion/`、`adapters/storage/`、`fixtures/ingestion/synthetic_source_profiles.json`、`tests/ingestion/`、`docs/implementation/P03-01_SOURCE_REGISTRATION_AND_EXTRACTION_PORTS_REPORT.md` | **CONFIRMED（工程）**：控制器已将任务分支修复安全集成，并从远端 `main` `f92612bf03b5ac740e52d1d56e99f9959369b9fb` 回读。只证明 value-free synthetic fake ports、hash/idempotency、safe locator、failure retention 与 fixture workflow staging；不代表真实 parser/OCR/storage/database、approved truth、生产权限或外部执行成立 |
| P03-02 mapping、normalization fingerprint、quality 与 replay proof | `modules/ingestion/mapping.py`、`fixtures/ingestion/synthetic_mapping_profiles.json`、`tests/ingestion/test_mapping_normalization_and_quality.py`、`docs/implementation/P03-02_MAPPING_NORMALIZATION_AND_QUALITY_REPORT.md` | **CONFIRMED（工程）**：控制器已将 profile/replay provenance 和 lifecycle repair 安全集成，并从远端 `main` `355483121580c0205a43e59078eba8c29d719d93` 回读；最终独立 review `APPROVE`。只证明 synthetic value-free mapping/quality contract，不代表真实 mapping、approved truth、供应链、合规或外部执行成立 |
| P03-03 审批、隔离的合成真值发布与内部刷新 | `modules/ingestion/approval.py`、`tests/ingestion/test_approval_publish_and_refresh.py`、`docs/implementation/P03-03_APPROVAL_PUBLISH_AND_REFRESH_REPORT.md` | **CONFIRMED（工程）**：控制器已将三笔任务提交集成，并从远端 `main` `5d2c429bd253344ce3c2a3a30a31315f4a81f177` 回读。只证明合成 candidate 的人工决定、不可变隔离版本、supersede/revoke、过期审计与内部失效通知合同；记录保持 `DataState.FIXTURE`，不写入 P02 current truth，不代表真实审批、真实 approved fact、供应链、合规或任何外部执行成立 |
| P04-01 工作流状态、检查点与恢复 | `workflows/runner.py`、`core/application/interfaces.py`、`tests/workflows/test_workflow_state_checkpoint_recovery.py`、`docs/implementation/P04-01_WORKFLOW_STATE_CHECKPOINT_AND_RECOVERY_REPORT.md` | **CONFIRMED（工程）**：控制器已将三笔任务提交集成，并从远端 `main` `d2805b293cbb71f7c5898ad0c611d863fb87e4b7` 回读。只证明 local simple runner（本地简易运行器）的安全检查点、幂等恢复、重试/死信与人工队列合同；公开存储写入、终态回流和未记录审批事件均被回归拒绝。它不代表真实身份、RBAC（基于角色的权限控制）、生产队列/工作流框架、真实 provider（服务提供方）、业务真值或外部执行成立 |
| P04-02 角色、审批与动作策略 | `core/security/action_policy.py`、`tests/contracts/test_action_policy_rbac_approvals.py`、`docs/implementation/P04-02_RBAC_APPROVALS_AND_ACTION_POLICY_REPORT.md` | **CONFIRMED（工程）**：控制器已将任务提交集成，并从远端 `main` `fd727fd0a74068edfa5511a18f878c312c062b6c` 回读。只证明 local synthetic 的最小角色/动作矩阵、追加式审批决定和执行前复核；审批精确绑定版本，幂等键覆盖证据、数据状态、时效、开关、DNC/同意和环境等审批语义。它不代表真实身份认证、真实授权、生产审批/审计/队列、业务资料或任何外部执行成立 |
| P04-03 审计、指标、重试与死信合同 | `core/security/audit.py`、`core/application/retry.py`、`observability/metrics.py`、`tests/contracts/test_audit_metrics_retry_dead_letter.py`、`docs/implementation/P04-03_AUDIT_METRICS_RETRY_AND_DEAD_LETTER_REPORT.md` | **CONFIRMED（工程）**：控制器已将审查后的任务提交集成，并从远端 `main` `6cf2033b0376add9fabb6487d818d00f8a4805d1` 回读。只证明 local-only 的追加式审计、可安全重试/不可重试/人工处理分类、死信可见性与安全指标/日志；审计或提交失败时均以回滚或追加失败/人工处理事件收口。它不代表生产审计库、broker、外部监控、真实 identity/RBAC、业务资料或任何外部执行成立 |
| P05-01 来源政策、合成快照与模拟抓取 | `modules/leads/source_policy.py`、`adapters/crawl/fake.py`、`fixtures/leads/synthetic_public_sources.json`、`tests/contracts/test_source_policy_and_crawl_port.py`、`docs/implementation/P05-01_SOURCE_POLICY_AND_CRAWL_PORT_REPORT.md` | **CONFIRMED（工程）**：控制器已将审查后的任务提交集成，并从远端 `main` `f034857d5ec5715c2677e06d8add6338f65f50e1` 回读。只证明 local synthetic 的来源政策、快照/哈希/证据引用和 zero-network fake port；联系字段在 policy/fetch/evidence/candidate 四层被拒绝，公开页面不构成 contact/CRM/outreach（联系/客户管理/外联）授权。它不代表真实网站访问、联系人、线索、外联、供应链或任何外部执行成立 |
| P05-02 合成线索、CRM、DNC 与受控导出 | `core/contracts/leads_crm.py`、`modules/leads/domain.py`、`modules/crm/domain.py`、`migrations/0004_leads_crm_dnc_export.sql`、`tests/contracts/test_leads_crm_domain.py`、`docs/implementation/P05-02_LEADS_CRM_DNC_EXPORT_REPORT.md` | **CONFIRMED（工程）**：控制器已保留 P06/P07 合同并从远端 `main` `35d6e1f12ad6ed2e4bfa86a2c9f70463f9dcacb9` 回读。只证明 local synthetic 的审查线索→CRM、DNC、同意/来源、可解释去重/人工合并与只含内部引用的导出；迁移序列 `0001/0002/0003/0004` 在双次重放中精确验证。它不代表真实联系人、客户、外联、发送、生产 CRM 或任何外部执行成立 |
| P06-01 会话、消息、隐私与人工转交合同 | `modules/customer_service/contracts.py`、`migrations/0003_support_conversations_messages_privacy.sql`、`tests/contracts/test_customer_service_conversation_contracts.py`、`docs/implementation/P06-01_CONVERSATION_CONTRACTS_AND_PRIVACY_REPORT.md` | **CONFIRMED（工程）**：控制器已保留 P05-01 并从远端 `main` `f02360d7e386f61b6b39cf2d8f3051e59fe21bc4` 回读。只证明 local synthetic 的会话、消息、意图、草稿、人工转交与未知范围隔离；外部标识均转换为不透明引用，未知范围不生成 scoped record（范围记录）。它不代表真实客户、渠道、身份、模型、发送、生产存储或任何外部执行成立 |
| P07-01 内容、素材与政策事实锁 | `modules/content_video/contracts.py`、`fixtures/content_video/synthetic_policy_vectors.json`、`tests/contracts/test_content_video_contracts.py`、`docs/implementation/P07-01_CONTENT_VIDEO_CONTRACTS_AND_FACT_LOCK_REPORT.md` | **CONFIRMED（工程）**：控制器已在保留 P06 隐私合同的前提下从远端 `main` `f02360d7e386f61b6b39cf2d8f3051e59fe21bc4` 回读。只证明 local synthetic 的 content brief、asset 与 policy lock；缺失、过期、撤销、跨范围或任何外部开关均被停止。它不代表真实内容素材、视频生成、供应商调用、导出、发布或任何外部执行成立 |
| 派生产物 | outputs、交付物、qa、渲染和媒体 | 仅作结果或质量线索；必须回读源数据与脚本 |
| 本地私有配置和线索 | 本地受控资料 | 不进入 Git 或同步包；不能当作对外联系授权或共享事实源 |

## 更新规则

1. 新事实须有来源、日期、责任人和事实分级。
2. 原始资料与状态冲突时，记录冲突并暂停升级，不静默挑选。
3. 新决定替代旧决定时，在 DECISIONS 中标记 SUPERSEDED，并保留原始资料。
4. 法律、平台、价格、库存、主体、账号和联系方式均应在执行前重新核验，不可仅依赖历史研究。

## 范围与边界

# 范围与边界｜SCOPE_AND_BOUNDARIES

## 当前在范围内

- 汾酒尼泊尔 TikTok 线上销售准备；
- 供应链启动资料收集、商品字段核验、首批 SKU 决策输入与上线前准备；
- 用户的账号运营、内容、商品展示、客户沟通、订单转化和数据反馈准备；
- 供应链的主体/资质、产品、账号认证支持、收款与履约资料收集和书面确认；
- 事实分级、状态、决策、风险、交接和同步包机制维护；
- 海鲜资料线的独立保存与明确任务下的独立处理。

## 当前不在范围内

- 自动恢复旧研究中的汾酒 B2B 经销商开发、多平台独立运营、Facebook/Instagram 独立营销、YouTube、Viber、完整 90 天试销、自动找客或自动外联；
- 将 WhatsApp Business、Meta、Instagram、网站等辅助资产自动扩大为独立主营销渠道；
- 未经明确授权和书面前置条件的外发、发布、投放、真实报价、下单、收款、发货或售后；
- 将海鲜产品、客户、价格、资质、履约或结论用于汾酒，或反向推导；
- 将研究、模板、文档、提交或测试通过描述为当地许可、供应链确认、上线、销售或履约。

## 不可擅自修改

- 原始研究 JSON、原始 DOCX/XLSX/PDF、视频、素材与供应链原始资料；如需更正，应建立可追溯的新版本，不覆盖原件。
- 本地私有配置、凭据、线索、私人联系方式、缓存、媒体、渲染和 QA 材料的安全边界。
- 已确认的业务范围、职责和事实源；变更须有新的用户确认或书面证据。

## 许可与执行闸门

内部资料准备可继续。任何公开酒类内容、广告、商品展示、导流、订单、付款、配送或个人数据处理，必须同时满足：当地合法性、当前平台规则、主体/品牌/产品授权、年龄与地域限制、账号与数据归属、收款履约责任、用户授权和可审计证据。任一缺失即 **BLOCKED**。

## 协作机制状态

# 协作机制状态｜COLLABORATION_STATUS

- **最近更新**：2026-08-10
- **用途**：记录仓库协作、脱敏、Git 与同步包状态；不替代 BUSINESS_STATUS 中的业务事实。

## 入口与协作规则

| 项目 | 状态 | 说明 |
|---|---|---|
| AGENTS 规则 | **CONFIRMED** | 已要求先读业务状态，再读总览、事实源、范围和协作状态；禁止把机制完成写成业务完成 |
| PROJECT_ENTRY | **CONFIRMED** | 已以 TikTok、供应链启动阶段、双方职责、用户本轮输入来源优先级、历史研究降级和海鲜隔离作为首屏信息 |
| 业务/协作状态分离 | **CONFIRMED** | BUSINESS_STATUS 记录业务，CURRENT_STATUS 仅作路由，本文记录协作与远端状态 |
| 交接模板与执行历史 | **CONFIRMED** | 已要求新会话先复述范围、事实分级、阻断和完成标准 |

## 安全与历史迁移审计

- **CONFIRMED**：旧临时分支历史共有 6 个提交；历史 manifest 与多份历史生成脚本曾暴露本机绝对路径和不必要的本地结构信息。
- **CONFIRMED**：使用高置信凭据规则检查 Git 历史，命中数为 0；这不等于无需继续保护或轮换可能只存在于本地的真实凭据。
- **CONFIRMED**：.env 与 .env.example 处于忽略状态，未作为受控 Git 内容。
- **CONFIRMED**：历史修复前的本地 Git bundle 已验证可读，并保留在仓库外；它不进入 Git 或同步包。
- **待验证**：完成干净 main、删除旧远端分支、设置默认分支和最终远端回读前，不得把历史清理或仓库安全收口写为完成。

## 同步包状态

- **CONFIRMED**：allowlist、敏感扫描、SHA-256、ZIP 完整性、AppleDouble/.DS_Store 清理、latest 原子替换和 verify 路径是保留机制。
- **同步包版本**：**CONFIRMED**；V2 Manifest schema 为 2，来源分支为 main，包含 BUSINESS_STATUS 和本文。
- **同步包脚本版本**：**CONFIRMED**；以构建时 Manifest 的 `source_git.source_commit` 为准；该字段只表示生成基线，不预写随后提交的自身 commit。
- **最近本地 bundle 验证日期**：2026-08-10；V2 build、`--verify`、ZIP 解压、SHA-256、路径/秘密扫描均通过。
- **CONFIRMED**：本文件本次回填后已重新生成并验证同步包；Manifest（清单）记录的 `source_commit` 是生成基线，不是随后提交同步包目录的 commit（提交）。
- **规则**：manifest 的 source_commit 是生成时的 Git 基线，不是随后提交 project_sync/latest 的 commit；不得构造自我引用版本。
- **规则**：包和 manifest 只可记录跨机器可用的信息；不得包含本机绝对路径、真实排除文件清单、秘密、私人联系资料或本地 ZIP 绝对路径。

## GPT Project 配合机制包状态

- **CONFIRMED**：`GPT项目资料同步包_gpt_project_mechanism_sync/` 已创建为 GPT Project 手动上传包；它与 `project_sync/latest/` 分工不同，不能互相替代。
- **CONFIRMED**：包内包含上传说明、Manifest、汾酒项目系统提示词、项目身份、三层/四层事实源边界、P0/P1/P2 来源优先级、GitHub 事实读取、Codex 执行落库、供应链业务闸门缺口、TikTok 主线、酒类合规、海鲜隔离、外部资料桥接、六层需求确认、Codex 任务模板、结果复审、Git 完成闸门和维护机制。
- **CONFIRMED**：`project_entry/AGENTS.md` 必须由 Manifest 记录的 source commit 中 `AGENTS.md` 生成；验证脚本会回读历史 commit、比较 source SHA、mirror SHA 和镜像内容。
- **CONFIRMED**：`scripts/validate_gpt_project_mechanism_sync.py --write-manifest` 已升级为语义一致性、业务闸门术语、blocked/Git 状态词和 AGENTS provenance 验证；具体 SHA 和结果以验证报告为准。
- **状态边界**：`package_ready_for_manual_upload = true`；`user_uploaded_to_gpt_project_ui = false`。本包生成、验证、commit 或 push 不代表用户已上传 GPT Project UI，也不代表供应链、平台、合规、上线、销售或履约成立。

## GitHub 收口状态

| 字段 | 当前状态 |
|---|---|
| Repository | fthytwerwt-sudo/fenjiu |
| Visibility | **UNKNOWN / 未认证回读**：GitHub CLI 认证读取超时；匿名 Git 引用读取可用，但不能据此推断 Private（私有）或 Public（公开）状态 |
| Default branch | **CONFIRMED（远端读取）**：仍为 `chore/project-collaboration-system`；`main` 尚非 default branch |
| 最近验证远端 branch | **CONFIRMED（远端读取）**：main 已创建 |
| 最近验证远端代码 commit | **CONFIRMED（远端读取）**：`main` 的 Phase 5–7 工程代码为 `ae84e183be38da62d17c8567569f75206ddb35f1` |
| Pull requests | **UNKNOWN**：需要 GitHub API/CLI 认证后回读 |
| 旧临时分支 | **待清理**；必须在 main 成功成为默认分支后再删除 |

## AI Native Sales OS 执行状态

- **部分成立**：P00-01 工程资产审计与 P00-02 架构冻结已在 `main` 远端回读。
- **CONFIRMED（隔离执行）**：P00-03 dry-safe 扫描器与 12 项回归测试已在控制器审查后集成并推送 `main`；干净 P00-03 task worktree 的两种扫描均通过，Phase 0 可写为工程完成。
- **PARTIAL（本地环境）**：外置盘根目录仍发现既有 ignored 禁入路径（AppleDouble、`.env*` 等）；该目录不得执行回归。Phase 1 及以后必须每张任务卡新建干净 task worktree，扫描失败即停止该任务分支。
- **CONFIRMED（P01-01）**：`main` 已远端回读模块化单体空 skeleton 与 metadata-safe architecture guard；外部 adapter、网络、数据库、模型、环境变量与真实业务资料均未接入。导入护栏覆盖 core/domain 与 modules 到 application/security 的直接及相对反向导入，跳过 AppleDouble 等文件系统元数据但不跳过普通源码，fixtures 默认仅放行 synthetic metadata。
- **CONFIRMED（P01-02）**：`main` 已远端回读 local-only Docker Compose / Make runtime 入口。固定镜像、named volumes、无 host `ports`、只读代码挂载、固定 loopback healthcheck 和 safe no-op migration/fixture 均已验证；Make 会从 worktree 绝对路径派生 Compose project name，避免多聊天框/临时 worktree 共享容器、网络和 volumes。控制器最终在干净 task worktree 通过 8 项 architecture、14 项 regression、8 项 local-runtime 测试、P00 两种扫描及完整 `dev-up → health → migrate → load-fixtures → dev-down` 生命周期，未留下该 project 的容器。GitHub Actions workflow 仍因当前凭据缺少 `workflow` scope 而未写入远端，不能表述为远端 CI 已启用。
- **CONFIRMED（P01-03）**：`main` 已远端回读静态 settings、只读 FeatureFlagPort、liveness/readiness 和 correlation-aware JSON log 合同。11 个敏感 action flag 永久默认关闭且 unknown/invalid 输入 fail-closed；`/live` 健康不泄露配置，`/ready` 因 broker/provider/real configuration 缺失而返回 HTTP 503。日志仅保留安全 identifier/code、数字和布尔值，自由文本、URL/DSN、message/file/Cookie/secret/绝对路径一律脱敏。控制器在干净 worktree 复验 `make regression`（8 architecture、14 regression、8 local-runtime、16 control-plane）与 P00 两种扫描通过；P01-03 不解除业务或远端 CI 阻断。
- **CONFIRMED（P02-01）**：`main` 已远端回读 scope/source/version contracts、synthetic fixture metadata、PostgreSQL schema migration 和 compound scope/lineage constraints。独立 code review 发现 migration replay/negative constraints 未纳入默认回归，已修复并二次复核：`make regression` 现在要求 Docker/Compose/daemon，启动 worktree 派生的隔离 PostgreSQL、完成两次 migration replay、五类 SQL 负例和 54 项 Python 测试后清理容器、network 与 volumes；不可用时非零失败而不跳过。该成果只证明 local synthetic schema 防护，不启用 production database、真实资料、审批、外部网络或业务外部动作。
- **CONFIRMED（P02-02）**：`main` 已远端回读九类 value-free truth contracts、source/version/approval evidence、parent/diff/effective window、append-only state machine、scoped current read 与 PostgreSQL constraints/triggers/view。review 发现 terminal root 可经 `conflict → approved` 绕过 staging ancestry，已在 Python repository、SQL CHECK 与 insert trigger 使用同一 root allowlist 修复；73 项 Python tests、两次 migration replay、16 类 SQL 负例、P00 两种扫描、mechanism validation 与 Docker cleanup 均由控制器复验通过。它不启用真实资料、认证审批、RLS、production database 或业务外部动作。
- **CONFIRMED（P02-03 / Phase 2）**：控制器已将 P02-03 六笔审查后提交安全集成并从远端 `main` `451843601a1a610e50bfbd9794f437b5781f1401` 回读 sealed policy grant、tests-only lifecycle probe、mandatory audit 与 signed actor attribution contracts。控制器和独立 reviewer 复现的 runtime direct read、audit bypass 与 actor replacement HIGH 均已修复并补精确回归；最终 actor-binding 专项独立复审 `APPROVE`。集成后 `make regression` 通过 92 项 Python tests、两次 migration replay、16 类 SQL 负例与 Docker cleanup；P00 两种扫描只在干净 task worktree 通过。该 local capability 不认证 actor/RBAC；P03-01 可开始，但真实资料、production isolation 与所有外部业务动作仍阻断。
- **CONFIRMED（P03-01 / Phase 3 engineering）**：控制器已从任务分支 `codex/p03-01-ingestion-ports` 安全集成 P03-01，并从远端 `main` `f92612bf03b5ac740e52d1d56e99f9959369b9fb` 回读。synthetic-only source/hash/private locator/quarantine、七类 fake extraction 与 fixture staging 均保持 value-free；runtime 单条 staging mutator 已移除，全批次入口在写入前强制 result/candidate 一对一、无重复与 lineage/scope 一致。控制器 `make regression` 通过 106 项 Python tests、两次 migration replay 与 16 类 SQL 负例，mechanism validation 与 Docker cleanup 通过；独立专项复审为 0 findings / `APPROVE`。P03 static audit 仅过滤外置盘 AppleDouble `._*` sidecar，普通源码仍被审计。P03-02 可从含本次状态回填的最新远端 `main` 新建干净 worktree。
- **CONFIRMED（P03-02 / Phase 3 engineering）**：控制器已将 `codex/p03-02-mapping-quality` 修复后提交安全集成，并从远端 `main` `355483121580c0205a43e59078eba8c29d719d93` 回读。初始 same ID/version forged profile provenance HIGH 与 quarantine/non-`STAGED` lifecycle MEDIUM 均由 profile/report/replay full fingerprint binding 和 P03-01 lifecycle enum guard 修复；最终独立复审 `APPROVE`。控制器完整 `make regression` 通过 118 项 Python tests、两次 migration replay、16 类 SQL 负例、mechanism validation 与 Docker cleanup；P03-02 仅提供 synthetic value-free mapping/quality/replay contract，绝不代表真实资料清洗、approved truth 或外部业务能力。P03-03 可从含本次状态回填的最新远端 `main` 新建干净 worktree。
- **CONFIRMED（P03-03 / Phase 3 engineering）**：控制器已将 `codex/p03-03-approval-publish-refresh-v2` 的三笔已审查提交快进集成，并从远端 `main` `5d2c429bd253344ce3c2a3a30a31315f4a81f177` 回读。P03-03 固定 candidate→review→human decision→isolated approved synthetic version→supersede/revoke→internal invalidation 合同；每条写入链的 correlation 完整性、过期审计状态和不含 correlation 的业务范围 current-read 索引均有回归。版本保持 `DataState.FIXTURE`，所有外部 flags 为 false，未接入 P02 current truth、真实审批/RBAC、CRM/客服/内容视频模块或外部动作。控制器复验专项 9 项、ingestion 35 项、完整 `make regression`、机制验证和 AppleDouble 排除编译检查；两轮最终只读审查没有阻断项。
- **CONFIRMED（P04-01 / Phase 4 engineering）**：控制器已将 `codex/p04-01-workflow-state` 的三笔已审查提交快进集成，并从远端 `main` `d2805b293cbb71f7c5898ad0c611d863fb87e4b7` 回读。P04-01 固定 local simple workflow runner（本地简易工作流运行器）为主路线和回退路线；checkpoint（检查点）只保存安全引用/哈希/元数据，超时进入 retry/DLQ（重试/死信队列），未知效果进入 manual queue（人工队列）。两轮审查发现的 terminal replay（终态回放）与 public store write bypass（公开存储写入绕过）均已用 fail-closed 守卫和回归修复；控制器复验 11 项工作流、8 项架构、完整 `make regression`、机制验证及干净 task worktree 的两种 P00 检查通过。未新增依赖、真实 provider（服务提供方）、业务资料、真实审批/RBAC 或外部动作。
- **CONFIRMED（P04-02 / Phase 4 engineering）**：控制器已将 `codex/p04-02-rbac-approvals` 的已审查提交快进集成，并从远端 `main` `fd727fd0a74068edfa5511a18f878c312c062b6c` 回读。P04-02 固定 local synthetic 的角色/动作策略、追加式审批决定和执行前复核；两轮审查发现并修复了 subject-version（事实版本）漂移与不完整幂等语义指纹，所有外部动作仍策略拒绝且不执行。控制器复验 7 项策略、11 项工作流、8 项架构、完整 `make regression`、机制验证、排除 AppleDouble 元数据的编译和 diff；未新增依赖、真实角色、业务资料、生产审计/队列或外部动作。P04-03 可从含本次状态回填的最新远端 `main` 新建干净 worktree。
- **CONFIRMED（P04-03 / Phase 4 engineering complete）**：控制器已将 `codex/p04-03-audit-metrics-retry-dlq` 的审查后提交快进集成，并从远端 `main` `6cf2033b0376add9fabb6487d818d00f8a4805d1` 回读。P04-03 固定 local-only 的 append-only audit（追加式审计）、retry/DLQ/manual（重试/死信/人工）分类和脱敏指标/日志；三轮审查先后修复 success-audit failure（成功审计失败）未回滚、commit failure（提交失败）伪装成功及 rollback failure（回滚失败）未人工标记的问题。控制器复验 9 项审计专项、7 项策略、11 项工作流、8 项架构、完整 `make regression`、机制验证、排除 AppleDouble 元数据的编译和 diff；未新增依赖、真实角色、业务资料、生产审计/队列/监控或外部动作。P05-01、P06-01 和 P07-01 可从含本次状态回填的最新远端 `main` 并行新建干净 worktree。
- **CONFIRMED（P05-01 / Phase 5 engineering）**：控制器已将 `codex/p05-01-source-policy-crawl-port` 的审查后提交快进集成，并从远端 `main` `f034857d5ec5715c2677e06d8add6338f65f50e1` 回读。P05-01 固定 local-only source policy（来源政策）、snapshot/evidence/hash（快照/证据/哈希）和 zero-network fake CrawlPort（零网络模拟抓取端口）；规格审查发现联系字段可被公开来源政策允许后，已在 policy、fetch、evidence 和 candidate 四层 fail closed 修复，外部 fetch 仍为零。控制器复验 8 项来源专项、9 项审计、7 项策略、11 项工作流、8 项架构、完整 `make regression`、机制验证、排除 AppleDouble 元数据的编译和 diff；未新增依赖、真实访问、contact/CRM/outreach（联系/客户管理/外联）或外部动作。P05-02 可从含本次状态回填的最新远端 `main` 新建干净 worktree。
- **CONFIRMED（P05-02 / Phase 5 engineering）**：控制器已将 `codex/p05-02-leads-crm-domain` 经一次修复与最终规格/质量复审后快进集成，并从远端 `main` `35d6e1f12ad6ed2e4bfa86a2c9f70463f9dcacb9` 回读。P05-02 固定 synthetic lead/CRM/DNC/export（合成线索/客户管理/拒绝联系/导出）合同：来源/同意不足、未审查、跨范围、DNC、模糊重复和外部开关均拒绝；导出不含 provider identifier（服务提供方标识）。并行 P06 的迁移冲突已以 P05 `0004` 修正，并在双次重放中精确核对 `0001/0002/0003/0004` 各一次且有序。控制器复验 91 项合同、35 项导入、完整 `make regression`、机制验证、编译和 diff；P05-03 可在新干净 worktree 中继续。
- **CONFIRMED（P06-01 / Phase 6 engineering）**：控制器已将 `codex/p06-01-conversation-contracts` 经规格与质量复审后集成，并从远端 `main` `f02360d7e386f61b6b39cf2d8f3051e59fe21bc4` 回读。P06-01 固定 local-only 的会话、消息、意图、草稿、人工转交与 unknown scope（未知范围）隔离；known scope（已知范围）的外部标识均转换为 opaque reference（不透明引用），未知范围不会创建 scoped conversation/message/handoff（范围会话/消息/转交）。控制器复验 6 项客服专项、8 项内容视频、84 项合同、35 项导入、完整 `make regression`、双次迁移重放与负向约束、机制验证、编译和 diff。未接入真实客户/渠道/模型/发送或外部动作；P06-02 可在新干净 worktree 中继续。
- **CONFIRMED（P07-01 / Phase 7 engineering）**：控制器已将 `codex/p07-01-content-video-fact-lock` 经规格与质量复审后以保留 P06 隐私合同的合并方式集成，并从远端 `main` `f02360d7e386f61b6b39cf2d8f3051e59fe21bc4` 回读。P07-01 固定 local synthetic 的内容简报、素材与政策事实锁，缺失/过期/撤销/跨范围/外部开关均停止；不调用生成服务、不写媒体、不导出或发布。控制器复验 8 项内容视频、6 项客服、84 项合同、35 项导入、完整 `make regression`、迁移重放、机制验证、编译和 diff；P07-02 可在新干净 worktree 中继续。
- **CONFIRMED（P05-03 / Phase 5 complete）**：`codex/p05-03-draft-zero-send` 已经最终审查、快进集成并从 `origin/main` 回读至 `37b19ed4bffff3b9d7a0341c6e756f71ce6ff6e4`。P05-03 只提供 synthetic（合成）草稿、人工决定与内部导出证明；无发送器、无端点、无收件人，`external_send_attempts=0`。来源/同意、DNC（拒绝联系）、范围、冲突、过期和高风险均 fail closed（默认拒绝）至人工处理。Phase 5 三张任务卡工程完成。
- **CONFIRMED（P06-02/P06-03 / Phase 6 complete）**：P06-02 已在 `aa5f2b6a4233dee70a3611b15d3593053319d98b` 集成；`codex/p06-03-support-adapter-takeover` 已审查、快进集成并回读至 `bbc742d22bc0f19f6b2cbe8b7be7abc058b7f197`。P06-03 仅增加 receive-only fake inbox（只接收模拟收件箱）、合成 case（案例）、审计式人工接管与显式恢复；无 provider（服务提供方）发送面，`external_send_attempts=0`。Phase 6 三张任务卡工程完成。
- **CONFIRMED（P07-02/P07-03 / Phase 7 complete）**：P07-02 已在 `73b1a01cad82e01077b452a8486dc8211b567229` 集成；`codex/p07-03-qc-approval-internal-export` 已审查、快进集成并由 `origin/main` 回读至 `ae84e183be38da62d17c8567569f75206ddb35f1`。P07-03 只处理 synthetic（合成）素材引用的 QC（质量检查）、人审决定和 internal export reference（内部导出引用）；无视频服务、媒体写入或公开发布，`external_publish_attempts=0`。Phase 7 三张任务卡工程完成。
- **BLOCKED（P08-01）**：Phase 8 的工程依赖已解锁，但 task card（任务卡）要求当前、获授权的真实供应链资料包及来源/范围/版本证据。当前仍缺真实商品、价格、库存、授权、资质和履约资料，故为 `BLOCKED / real_supplier_data_missing（阻断 / 缺少真实供应链资料）`；不得以 synthetic fixture（合成测试数据）替代。
- **边界**：该工程阻断不改变 BUSINESS_STATUS；公开发布、报价、收款、订单、履约及任何外部业务动作仍为关闭状态。

## 剩余机制收口

1. **业务闸门**：等待供应链提供 P08-01 所需的当前、获授权真实资料包；在此之前不启动真实导入或外部动作。
2. **仓库治理**：具备管理权限的责任人应认证回读 visibility（可见性）、决定是否将默认分支切换为 `main`，再按决定回读和清理旧临时远端分支。
3. **远端 CI**：具备 `workflow` scope 的授权凭据可单独写入并回读 GitHub Actions；本地 `make regression` 不替代远端 CI。
4. 用户按需将 `GPT项目资料同步包_gpt_project_mechanism_sync/` 上传到 ChatGPT GPT Project，并用上传后验证清单测试新聊天框。

## 更新规则

只能以实际命令、GitHub/API 回读、脚本验证和可读取的产物更新本文。本文记录最近一次可写入的远端验证；包的 source_commit 表示生成基线，不尝试构造“文件同时记录自身提交”的不可能结构。每次新提交后，最终远端 HEAD 仍须由执行回报再次回读。
