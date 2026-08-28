# 当前项目总览｜CURRENT_STATUS

- **最近更新**：2026-08-28
- **用途**：本页只提供业务与协作的短摘要和路由；详细事实以链接文件为准。

## 业务状态摘要

- **CONFIRMED**：用户本轮 P0 已将当前方向改为 Sales-First：业务目标是经由最小、可核验的销售闭环验证询盘、人工销售、订单和履约交接；AI 系统完成度不再是北极星。
- **UNKNOWN**：供应链尚未在当前资料中实际提供 SKU、价格、库存、补货、主体/资质、品牌授权、账号权限、收款、仓储配送、售后及负责人确认。
- **当前最重要任务**：完成 `SR-1 Sellable Offer Ready`：先补齐商品单、价格规则、库存、主体/资质、账号、收款与履约资料，并据此确认一个最小 Offer、询盘入口、人工销售 owner 和交接方式。
- **BLOCKED / business_gates**：在上述资料与指定渠道当前酒类政策获得书面确认前，不能进入公开发布、广告、真实销售、收款、订单或履约。
- **已确认（内部规范层）**：已形成汾酒/海鲜独立的《尼泊尔精准客户获取标准与 Codex 输入规范》；它只定义未来客户发现、评分和 CRM 准入标准，不恢复自动找客/自动外联，也不解除任何业务闸门。
- **已确认（来源研究层）**：双业务线 Source Catalog 已形成并提供 machine-readable（机器可读）YAML；真实企业发现、联系人处理、CRM 和外联均尚未开始或未获授权，且仅是 SR-6 后置 B2B 小样本的输入。
- **CONFIRMED（执行设计层）**：汾酒 `FJ-1` 与海鲜 `SF-1` 的独立执行/内容手册、双线阶段闸门与 KPI 已形成。它们把内容脚本、AI iPhone 质感、渠道/询盘/跟进与决策阈值写成可执行草稿，但不解除任何外部业务闸门。
- **部分成立（海鲜货品来源）**：用户提供的 2026 年货品单已作为 `SM-01` 至 `SM-20` 的候选产品登记；表内数据不升级为本地可售库存、食品/冷链、价格或履约事实。

详情：[SALES_FIRST_MASTER_PLAN.md](../strategy/SALES_FIRST_MASTER_PLAN.md)｜[SALES_EXECUTION_PHASES.md](../strategy/SALES_EXECUTION_PHASES.md)｜[BUSINESS_STATUS.md](BUSINESS_STATUS.md)｜[OPEN_QUESTIONS.md](OPEN_QUESTIONS.md)｜[RISKS_AND_BLOCKERS.md](RISKS_AND_BLOCKERS.md)｜[NEXT_ACTIONS.md](NEXT_ACTIONS.md)

## 协作机制状态摘要

- **CONFIRMED**：固定入口、事实分级、任务交接、执行记录和同步包机制已建立。
- **CONFIRMED**：GPT Project 配合机制包已在仓库内生成并通过本地验证；包内 AGENTS 镜像与根 AGENTS SHA-256 一致。
- **部分成立**：远端 `main`、任务集成和同步包验证已持续回读；远端默认分支仍不是 `main`，GitHub API 的 visibility（可见性）仍未获认证回读。二者均不能由本文件编辑或本地 commit（提交）替代。
- **最近远端验证**：Phase 5–7 的最后五张任务卡已由 `origin/main` 回读至 `ae84e183be38da62d17c8567569f75206ddb35f1`；同步包将在本次状态回填后重新生成并验证。

## 工程规划状态摘要

- **CONFIRMED（工程历史层）**：`docs/implementation/` 保留 AI Native Sales OS 的 Phase 0–8 技术蓝图、依赖图和任务卡；自 2026-08-28 起它们不再是业务优先队列，销售顺序以 `docs/strategy/SALES_EXECUTION_PHASES.md` 为准。
- **部分成立**：本摘要不表示已创建可连接数据库的业务服务、队列、CRM、客服、视频服务或真实资料导入；任何未来技术实施必须先由 Sales-First 阶段证明其必要性，再按独立任务卡推进。
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
