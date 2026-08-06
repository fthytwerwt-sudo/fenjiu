# 协作机制状态｜COLLABORATION_STATUS

- **最近更新**：2026-08-06
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
- **最近本地 bundle 验证日期**：2026-08-05；V2 build、`--verify`、ZIP 解压、SHA-256、路径/秘密扫描均通过。
- **CONFIRMED**：V2 脱敏脚本已完成重新生成与验证；最终包仍须在本文件本次回填提交后再次生成，确保新会话读到同一状态。
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
| Visibility | **BLOCKED / 未确认**：GitHub CLI 认证读取超时，尚无法读取或改为 Private |
| Default branch | **CONFIRMED（远端读取）**：仍为 `chore/project-collaboration-system`；`main` 尚非 default branch |
| 最近验证远端 branch | **CONFIRMED（远端读取）**：main 已创建 |
| 最近验证远端代码 commit | **CONFIRMED（远端读取）**：`main` 的 P03-01 工程代码为 `f92612bf03b5ac740e52d1d56e99f9959369b9fb` |
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
- **PARTIAL（P03-02 / task branch only）**：当前 `codex/p03-02-mapping-quality` 已本地完成 strict synthetic mapping profile、deterministic value-free normalization fingerprint、quality report 与 profile replay/diff proof；focused suite、ingestion suite、`make regression`、P00 default/all-files、mechanism validation、compile/shell/diff 均已通过。状态仍为 `task_branch_partial_pending_commit_push_readback`，不得写为 `main` 集成、真实资料处理、approved truth 或外部业务能力。
- **边界**：该工程阻断不改变 BUSINESS_STATUS；公开发布、报价、收款、订单、履约及任何外部业务动作仍为关闭状态。

## 剩余机制收口

1. **高优先待办**：完成 GitHub CLI 登录，读取并将仓库 visibility 改为 Private。
2. 将 GitHub 默认分支切换为 main，随后删除旧临时远端分支，并回读全部远端状态。
3. 在包含本次状态回填的 main 上重新生成同步包，并完成解压、哈希和新会话接手验证。
4. 用户按需将 `GPT项目资料同步包_gpt_project_mechanism_sync/` 上传到 ChatGPT GPT Project，并用上传后验证清单测试新聊天框。

## 更新规则

只能以实际命令、GitHub/API 回读、脚本验证和可读取的产物更新本文。本文记录最近一次可写入的远端验证；包的 source_commit 表示生成基线，不尝试构造“文件同时记录自身提交”的不可能结构。每次新提交后，最终远端 HEAD 仍须由执行回报再次回读。
