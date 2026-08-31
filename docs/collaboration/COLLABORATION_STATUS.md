# 协作机制状态｜COLLABORATION_STATUS

- **最近更新**：2026-08-31
- **用途**：记录仓库协作、脱敏、Git 与同步包状态；不替代 BUSINESS_STATUS 中的业务事实。

## 入口与协作规则

| 项目 | 状态 | 说明 |
|---|---|---|
| AGENTS 规则 | **CONFIRMED** | 已要求先读业务状态，再读总览、事实源、范围和协作状态；禁止把机制完成写成业务完成 |
| PROJECT_ENTRY | **CONFIRMED** | 已以 TikTok、供应链启动阶段、双方职责、用户本轮输入来源优先级、历史研究降级和海鲜隔离作为首屏信息 |
| 业务/协作状态分离 | **CONFIRMED** | BUSINESS_STATUS 记录业务，CURRENT_STATUS 仅作路由，本文记录协作与远端状态 |
| 交接模板与执行历史 | **CONFIRMED** | 已要求新会话先复述范围、事实分级、阻断和完成标准 |
| Sales-First 规划入口 | **CONFIRMED（规划）** | `docs/strategy/` 已将业务北极星从系统完成度改为可售 Offer、受控触点、人工销售、订单交接和反馈；不表示已可执行外部销售 |
| Video Orchestrator | **PARTIAL / AIDGE_PROBE_REQUIRED** | capability-first application/runtime/CLI/presets 与 8 类 provider adapter 已通过回归；Aidge/OSS 本地配置已就绪，OSS Bucket/北京地域/put/sign/get/delete 已验证，Aidge credentials/endpoint 已被只读查询预检接受。`aidge:VideoGeneration` 仍未物理验证，本轮没有 Aidge 付费调用或媒体提交。代码复审误触发 1 次 MiniMax TTS，已单独记录且不作为新能力证据。 |
| 双业务线执行化手册 | **CONFIRMED（内部规划）** | 已增加汾酒/海鲜独立执行与内容手册、阶段/KPI 矩阵；AI 视频仅为内部 iPhone Natural Look 草稿，不解除产品、平台或外部动作闸门。 |
| 海鲜 Online Acquisition 职责重构 | **CONFIRMED（P0 / 内部规划）** | 海鲜现为 Supplier SF-S1 + User SF-U0–U8；新增线上获客与 Lead Handoff/Feedback 合同。旧 SF-2 已 SUPERSEDED，未启动真实发现、发送、发布或销售。 |

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
- **最近本地 bundle 验证日期**：2026-08-29；Sales-First allowlist 已纳入 16 份战略文件（新增 Seafood Online Acquisition Playbook 与 Lead Handoff Contract），build、`--verify`、ZIP 解压、SHA-256、路径/秘密扫描均通过；最终重建基线为 `788ea3a90b402d03a9374f7dcb29e3e3b3239888`，文件数为 48。最终提交后 source commit 与提交本身不同是正常的非自引用边界。
- **CONFIRMED**：本文件本次回填后已重新生成并验证同步包；Manifest（清单）记录的 `source_commit` 是生成基线，不是随后提交同步包目录的 commit（提交）。
- **规则**：manifest 的 source_commit 是生成时的 Git 基线，不是随后提交 project_sync/latest 的 commit；不得构造自我引用版本。
- **规则**：包和 manifest 只可记录跨机器可用的信息；不得包含本机绝对路径、真实排除文件清单、秘密、私人联系资料或本地 ZIP 绝对路径。

## GPT Project 配合机制包状态

- **CONFIRMED**：`GPT项目资料同步包_gpt_project_mechanism_sync/` 已创建为 GPT Project 手动上传包；它与 `project_sync/latest/` 分工不同，不能互相替代。
- **CONFIRMED**：包内包含上传说明、Manifest、汾酒项目系统提示词、项目身份、三层/四层事实源边界、P0/P1/P2 来源优先级、GitHub 事实读取、Codex 执行落库、供应链业务闸门缺口、Sales-First 渠道边界、酒类合规、海鲜隔离、外部资料桥接、六层需求确认、Codex 任务模板、结果复审、Git 完成闸门和维护机制。
- **CONFIRMED**：`project_entry/AGENTS.md` 必须由 Manifest 记录的 source commit 中 `AGENTS.md` 生成；验证脚本会回读历史 commit、比较 source SHA、mirror SHA 和镜像内容。
- **CONFIRMED**：`scripts/validate_gpt_project_mechanism_sync.py --write-manifest` 已升级为语义一致性、业务闸门术语、blocked/Git 状态词和 AGENTS provenance 验证；具体 SHA 和结果以验证报告为准。
- **CONFIRMED（2026-08-28）**：Sales-First 机制包已重新生成 Manifest 并通过验证；23 个文件、system prompt 4,714 字符，根 AGENTS、镜像和 Manifest source commit `8e03083be90f9d7e355787596a35598eb629a5e8` 一致。此状态不表示用户已重新上传 GPT Project UI。
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
5. **Sales-First 包同步**：本轮完成 Manifest、AGENTS 镜像、机制验证、Git commit/push/remote readback 前，不得声明 GPT Project UI 已更新；状态始终保持 `user_uploaded_to_gpt_project_ui = false`。

## 更新规则

只能以实际命令、GitHub/API 回读、脚本验证和可读取的产物更新本文。本文记录最近一次可写入的远端验证；包的 source_commit 表示生成基线，不尝试构造“文件同时记录自身提交”的不可能结构。每次新提交后，最终远端 HEAD 仍须由执行回报再次回读。
