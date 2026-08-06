# 执行历史｜EXECUTION_HISTORY

此处只记录真实仓库执行，不补写没有证据的业务动作。每个实质变更、生成、验证、commit/push 或新阻断点应新增条目。

## 2026-08-06｜P03-02 字段 mapping、清洗与数据质量（task branch）

- **目标**：只建立 stdlib/local-only/synthetic/value-free 的 versioned mapping profile、deterministic normalization fingerprint、missing/conflict/expiry/duplicate quality report 和 profile change replay/diff proof；不读取真实文件、不写 approved truth 或外部动作。
- **实际改动**：新增 `modules/ingestion/mapping.py` 与 10 项 mapping contract probes；只消费 P03-01 source/job/result/staging chain，candidate 保留 scope、source/job/result/staging IDs、locator、content hash、rule/profile lineage。strict profile schema 拒绝 implicit/generic mapping，unknown unit/currency/date/language、missing、conflict、duplicate、freshness、scope/lineage/signature 以 stable code fail closed。新增一个 synthetic mapping fixture，并以 `.gitignore` 精确 allowlist，其他 ingestion fixtures 继续被忽略。
- **审查与验证**：test-first 从缺少 `modules.ingestion.mapping` 的 ImportError 开始；fixture allowlist test 首次正确发现新 fixture 被忽略。自审发现 P00 all-files scan 将测试中的字面绝对路径检测样例视作违规，改为运行时构造后保持同一断言且两种扫描通过。focused mapping 10 项、ingestion 24 项、`make regression`（两次 migration replay、16 类 SQL negative、116 项 Python suites）、P00 default/all-files、mechanism validation、compile/shell/diff 均通过。
- **Git 证据**：基线为 `origin/main` `f92612bf03b5ac740e52d1d56e99f9959369b9fb`，状态回填基线 `535857f376765b16c056049e3c9ae86a348fee64`；任务代码提交 `a219463108ca3cf098920d57d17a6b7d8657b01f` 已 push，并从远端同名分支 readback。`main` 仍为 `535857f376765b16c056049e3c9ae86a348fee64`，尚待控制器集成。
- **状态边界**：仅为 task-branch local engineering `PARTIAL`；业务状态、business gates、真实资料、approved truth、生产 storage/database/auth/RBAC/RLS 与所有 external flags 均不变化。

## 2026-08-06｜P03-01 原始登记、隔离存储与 extraction ports

- **目标**：只建立 stdlib/local-only/synthetic 的 source registration、private relative/reference locator、hash/idempotency、quarantine、type-specific fake extraction 和 fixture staging；不读取真实供应链资料、不接 production、不写真值或外部动作。
- **实际改动**：新增 source/job/result/candidate/failure 合同、七类 fake ports、全批次原子 staging store、synthetic source profile 和 14 项 ingestion tests；workflow staging 仍保持 `data_state=fixture`。runtime 不暴露单条 result/candidate mutator，批量入口强制一对一完整性；unknown MIME、oversize/empty、storage/folder traversal、unlocated field、parse/OCR、cross-scope、replay mismatch、secret-like metadata、real/external flags 全部 stable-code fail closed。
- **审查与验证**：test-first 从缺失 adapter ImportError 开始；自审修复 partial write、failure rerun、lineage 与 fixture allowlist。独立 reviewer 第一轮发现 secret metadata retention HIGH 和 locator alias idempotency MEDIUM，修复后 `APPROVE`。控制器再发现 runtime 单条 staging atomicity bypass HIGH；本次移除单条 mutator、拒绝 partial/duplicate/mismatched batch，原 reviewer 专项只读复核为 0 findings / `APPROVE`。外置盘 AppleDouble sidecar 使 P03 静态 AST 审计误读非 UTF-8 元数据；控制器将源码枚举限为非 `._*`，未删除用户文件。最终 `make regression` 通过 106 项 Python tests、两次 migration replay与 16 类 SQL 负例；mechanism、compile/shell/diff、Docker cleanup 均通过。
- **Git 证据**：精确任务基线为远端 `main` `bce35a01fa7c13cce797069198ce71dcf29ea2dc`；任务分支修复提交 `e17196e06380827224a1463f01b53a9975382f22` 已 push。控制器按提交顺序集成并将 P03-01 工程代码 push/readback 至远端 `main` `f92612bf03b5ac740e52d1d56e99f9959369b9fb`；本地 `HEAD`、`origin/main` 与 `ls-remote` 一致，core-file SHA-256 已再次回读。本任务未生成 sync archive。
- **状态边界**：P03-01 已为远端 `main` 工程完成；P03-02 仅可从包含本次状态回填的最新远端 `main` 新建干净 worktree。业务状态、business gates、approved truth、production auth/RBAC/RLS、真实资料和所有 external flags 不变化。

## 2026-08-06｜P02-03 业务线隔离、fixture 防护与合同测试

- **目标**：只把 tenant/project/business-line、fixture production separation、sensitivity/flags、approved/fresh/no-conflict truth consumer 与 denial audit 锁进 local repository/command contracts；不实现真实资料、production connection 或外部 adapter。
- **实际改动**：新增 sealed policy-issued repository grant、fixed local sensitivity、scoped `TruthConsumerCommand`、exact current read 与 payload-free immutable audit；runtime probes 已移至 tests-only harness，guarded current 在返回 truth 前强制 success audit。最新修复把 `actor_ref` 纳入 policy issuance、grant field/signature/validation；repository 删除独立 actor 参数且只记录 validated grant actor。adversarial tests 覆盖 scope/fixture/state/sensitivity/flags、grant tamper/reuse/forgery、fake verifier/audit recorder、direct read/audit enforcement 与 actor attribution replacement。
- **审查与验证**：控制器和独立 reviewer 先后复现 runtime helper direct truth read、real-policy direct current audit bypass 与合法 grant 的 actor attribution replacement（均为 HIGH）。依次移除 helper、下沉 mandatory audit、绑定 actor 到 signed grant 后，最终 actor-binding 专项独立复审 0 findings / `APPROVE`。最终 `make regression` 通过 92 项 Python tests、两次 migration replay 和 16 类 SQL 负例；P00 default/all-files、mechanism validation、compile/shell/diff 与 Docker cleanup 通过。
- **Git 证据**：从远端 main `6d247b0613b517ff4474095abece2f64331a40a8` 新建干净 worktree；任务分支代码提交 `3341042c51a83d0eeac9abd91b1b01a3e07e2551` 已 push 并回读。控制器在 review 通过后逐笔集成六笔任务提交，并将 `main` push/readback 至 `451843601a1a610e50bfbd9794f437b5781f1401`；四份核心代码/测试文件从远端读取 SHA-256 一致。default branch 仍为旧协作分支，visibility 因 GitHub API 连接失败保持 `UNKNOWN/BLOCKED`。
- **状态边界**：Phase 2 engineering contracts 已在 `main`；P03-01 可在新干净 worktree 单卡开始。业务状态、业务闸门和所有 external flags 不变化；production auth/RBAC/RLS、真实资料与外部执行仍阻断。

## 2026-08-06｜P02-02 真值实体、版本与状态机

- **目标**：只以 value-free contract probes 建立 product/SKU/price/inventory/delivery/compliance/asset/approved_fact/forbidden expression 的 candidate/version/expiry/conflict/supersede 与 current-read 防护；不实现真实资料、parser、UI、adapter 或外部连接。
- **实际改动**：新增九类 truth entity enum、payload/source/version/parent/diff/effective-window/approval evidence 合同、append-only in-memory repository、明确状态图、`0002` PostgreSQL table/trigger/current view、27 项 truth contract tests 和扩展后的 migration negative suite。fixture/mock 不可提升，candidate/expired/blocked/conflict/superseded 不可作为 current truth；approved 必须同 scope 且 source/version/approval evidence 完整。
- **自审与验证**：自审统一 Python/SQL 的 `parent_version_id=data_version_id` 语义，并将 transition 和 update/delete 拒绝下沉到 PostgreSQL trigger。独立 code review 进一步发现 terminal root 可经 `conflict → approved` 绕过 staging ancestry，已在 Python repository、SQL CHECK/trigger 使用同一 root allowlist 修复，并新增四类非法 root 与 conflict-root child 负例。控制器和原 reviewer 二次复核后，完整 `make regression` 通过 73 项 Python tests、两次 migration replay 与 16 类 SQL 负例；P00 两种扫描、mechanism validation、diff/shell check 和 scoped Docker cleanup 均通过。P02-02 两笔工程提交已推送并从远端 `main` 回读为 `0ba7f0575fdfe2906455c5b6301ac71c8872e727`。
- **状态边界**：本条只完成 value-free local truth contract/state/read 防护；业务事实和所有外部 flags 不变化。RLS、authenticated approval/RBAC、production repository/connection、真实资料和远端 CI 仍未完成；P02-03 只能在新的干净 task worktree 中继续。

## 2026-08-06｜P02-01 scope contracts、migration 与 synthetic isolation 基线

- **目标**：只建立 local PostgreSQL schema、stdlib metadata contracts 与 synthetic fixture 防护，为后续 truth model 提供 scope/source/version/lineage 基础；不导入真实资料或开放外部能力。
- **实际改动**：新增 scope/source/version/state/sensitivity typed contracts、`0001_scope_contracts.sql`、synthetic-only metadata fixture、PostgreSQL compound FK/check constraints、migration replay/negative test 与 P02-01 报告。所有 scoped metadata 显式记录 tenant/project/business-line/source/version/state/sensitivity；schema 层拒绝跨业务线 lineage、synthetic→approved、fixture external execution 和任意 `external_execution_allowed=true`。
- **审查与验证**：P02-01 初审发现 database replay/negative constraints 未进入默认回归；已将 `make migration-test` 变为 Docker/Compose/daemon 缺失即非零失败的自包含隔离 PostgreSQL runner，并由 `make regression` 强制调用。控制器和独立复核均确认两次 migration replay、五类 SQL 负例、8 architecture、14 regression、8 local-runtime、16 control-plane、8 contracts（共 54 项 Python 测试）、P00 default/all-files scan 与 `git diff --check` 通过；临时 Compose containers/volumes 为零残留。P02-01 代码已推送并从远端 `main` 回读为 `b08722a703f37a0cfcce0c928fec8c01c4596357`。
- **状态边界**：仅完成 synthetic local schema/contract 防护；RLS、加密、retention、法域、真实 scope、ORM/driver、production connection、真实业务资料、审批和远端 CI 均未完成。SKU、价格、库存、资质、账号、收款、履约、合规、公开发布和销售没有新增确认，所有外部 flags 继续为 false。

## 2026-08-06｜P01-03 fail-closed config、readiness 与脱敏日志控制面

- **目标**：建立不读取环境/文件/secret reference 的 typed settings、不可提权 flags、liveness/readiness 以及不泄露文本/路径/secret 的基础 JSON log 合同。
- **实际改动**：新增 static `ControlPlaneSettings`、`FeatureFlagPort`、11 个敏感 action flag、`/live` / `/ready`、correlation-aware JSON logger 与 control-plane 测试。liveness 只报告 local control plane；因没有 broker/provider/real configuration，readiness 固定 `not_ready` / HTTP 503。日志只允许严格 identifier/code、数字和布尔值；其他自由文本及 URL/DSN/Cookie/secret/path 均 `[REDACTED]`。
- **审查与验证**：控制器和独立 code review 发现中性 metadata key 可泄露短文本，已以 allowlist 式字符串策略修复并补 2 项负向测试。最终在干净 task worktree 通过 8 项 architecture、14 项 regression、8 项 local-runtime、16 项 control-plane、P00 默认/全量扫描和 `git diff --check`；完整 local Docker lifecycle 保持 no-op / readiness reject，且容器清理完成。P01-03 四个任务提交已合入 `main`，代码远端回读为 `915d6116f114e3cea0d6bc8032fac2bdee4f3e15`。
- **状态边界**：本条只完成 local control plane，既不启用 broker/provider/远端 CI，也不确认 SKU、价格、库存、账号、资质、收款、履约、合规、公开发布或销售。所有业务外部 flags 继续为 false。

## 2026-08-06｜P01-02 local-only runtime、Make 入口与多 worktree Compose 隔离

- **目标**：只建立可复现的本地工程运行底座，不连接应用数据库、不读取 `.env`、不导入真实资料、不调用外部 HTTP 或任何业务外部动作。
- **实际改动**：新增固定镜像的 Docker Compose、stdlib-only API/admin loopback health endpoint、worker idle/health/no-op entrypoint、`.env.example` placeholder、Make 入口与 local-runtime 测试。Compose 无 host `ports`，代码挂载只读；`COMPOSE_PROJECT_NAME` 从 worktree 绝对路径派生，避免不同 Codex worktree 共享容器、网络或 volumes。
- **审查与验证**：控制器与独立审查先后收紧任意 healthcheck URL、嵌套 `.env.example` allowlist、Compose 静态 render 覆盖及固定 Compose project name。最终在干净 task worktree 通过 `make regression`（8 architecture、14 regression、8 local-runtime）、P00 默认/全量扫描、`git diff --check` 和完整 `make dev-up → health → migrate → load-fixtures → dev-down`；本地生命周期结束后无该 project 的残留容器。P01-02 三个任务提交已合入 `main`，代码远端回读为 `c2e9b1ce2f8109ec255e184d70331840a4da1651`。
- **已知阻断**：尝试提交仅做静态验证的 GitHub Actions workflow 时，被远端以当前凭据缺少 `workflow` scope 拒绝；因此远端 CI 未启用，本地静态验证不等于 GitHub CI。
- **状态边界**：所有业务外部 flags 继续为 false；Docker 拉取仅用于固定 local-runtime 镜像验证，不表示对外业务执行。P01-03 仍待新建干净 worktree 执行；SKU、价格、库存、资质、账号、收款、履约、平台合规和真实销售仍无新增确认。

## 2026-08-06｜P01-01 模块化单体 skeleton 与导入边界

- **目标**：只建立可 import、可测试的 Python skeleton，不实现产品、CRM、客服、数据库、网络或任何外部 adapter。
- **实际改动**：新增 apps/core/modules/adapters/workflows 的空包、模块 ownership README、typed scope/error/port 占位、synthetic-only fixture metadata、迁移占位与 architecture tests；`.gitignore` 仅放行 P01 必需源码及两份 fixture 文件。
- **审查与验证**：控制器发现并修复了 committed diff 尾部空白、相对导入可绕过 application/security 边界、fixtures allowlist 过宽及 AppleDouble 元数据导致边界测试解码失败四项问题。最终在干净 task worktree 通过 `compileall`、8 项 architecture tests、12 项 P00 回归以及两种 P00 扫描；控制器在外置盘根目录复验 8 项 architecture tests 与 12 项 P00 回归均通过，`main` 远端已回读。
- **状态边界**：外部动作默认全为 false；无新增依赖、ORM、数据库连接、模型、SDK、真实资料或业务状态。P01-02 后续已另行验证 local-only runtime；P01-03 仍待执行，不能把 skeleton 写成可运行销售系统。

## 2026-08-06｜P00-03 dry-safe 回归扫描与主工作区基线阻断

- **目标**：建立不联网、不读取 `.env*` 内容、不调用模型或真实渲染的敏感/路径/legacy 回归入口，并验证其 fail-closed 行为。
- **实际改动**：新增 `scripts/validate_regression_baseline.py`、12 项 stdlib 回归测试和 P00-03 报告；覆盖 `.env*` 路径级检测、ignored 非 ASCII 路径、AppleDouble、符号链接跳过、绝对路径、secret-like assignment、fixture 泄漏、Git 失败和过长路径的受控失败。
- **控制器验证**：任务分支测试、静态检查、默认/全量扫描与远端文件回读均完成；控制器在授权主工作区复验时，扫描器无 traceback，但正确发现 202 项默认带基线和 1,262 项全量既有 ignored 禁入路径。
- **状态边界**：扫描器实现本身为 **CONFIRMED**；外置盘根目录的工程基线为 **BLOCKED（局部）**，且任务规则禁止删除 AppleDouble、读取 `.env*` 或放宽扫描以伪造通过。控制器随后在干净 P00-03 task worktree 复验 12 项测试和两种扫描均通过，因此 Phase 0 可作为隔离工程路径完成；Phase 1 必须一任务一新 worktree。业务状态及外部行为没有变化。

## 2026-08-06｜P00-01 工程资产与禁区基线审计

- **目标**：只执行 `P00-01`，以当前仓库证据建立工程资产、legacy hash/CLI、禁区和 Phase 1 输入基线；不创建运行时代码，不调用模型/API，不读取密钥值，不改变业务事实。
- **实际读取**：AGENTS、PROJECT_ENTRY、业务/当前/事实源/范围/协作状态、GPT Project 机制包核心文件、AI Native Sales OS 总蓝图、架构与模块边界、P00-01 task card、受控 Git 文件清单和根目录脚本入口。
- **实际改动**：新增 `docs/implementation/P00-01_ENGINEERING_ASSET_BASELINE_REPORT.md`，追加本执行历史记录。
- **审计结果**：当前受控仓库主要为治理/状态/实施规划文档、GPT Project 机制包、同步包快照和两个根 Python 脚本；未发现 runtime 目录、migration、Docker/Make 入口或可运行服务。两个根脚本已记录 SHA-256 和安全 `--help` 入口；规划中 HappyHorse/DashScope/FFmpeg legacy 实体未在当前受控 Git 清单中定位，保持 `BLOCKED`，后续不得假设可运行。
- **禁区结果**：本轮未修改原始研究、DOCX/XLSX/PDF、媒体、`outputs/`、`.env*`、`research_channels.json` 或 `project_sync/latest/`；AppleDouble 和超过 10MB 文件检查无命中。
- **状态边界**：本条只表示 P00-01 在任务分支形成工程审计证据；不表示 Phase 0 已合入 main，不表示运行时系统、供应链资料、平台合规、账号权限、外部发布、报价、收款、订单、履约或销售成立。

## 2026-08-06｜AI Native Sales OS Phase 0–8 工程实施蓝图落库

- **目标**：把已有 GPT Project / GitHub / Codex 治理机制与运行时工程规划分层，形成从工程基线到真实供应链资料导入、fixture 替换、全链回归和受控运行的可下发路径；本轮不开发业务代码。
- **实际读取**：项目入口、业务/协作状态、事实源、范围、决策、风险、下一步、GPT Project 机制包/Manifest、未合并早期实施规划、HappyHorse/DashScope/FFmpeg 和研究/文档工具脚本，以及当前官方开源组件资料。
- **实际改动**：重组 `docs/implementation/` 为 Phase 0–8 总蓝图、分阶段执行图、数据/导入/工作流/CRM/客服/视频/真实资料 runbook、测试回滚矩阵、run-ready 模板、机器可读依赖图和 27 张独立 Codex 任务卡；旧粗粒度规划入口标为 SUPERSEDED，避免混用编号。
- **验证边界**：文档非空、任务卡字段、链接/路径、敏感/本地路径、业务线污染和 Git diff 检查须以本轮最终命令结果为准；Git commit/push/remote readback 在执行报告中单独回报。
- **状态边界**：规划落库只表示工程实施设计完成；不表示运行时系统、供应链资料、平台合规、账号权限、外部发布、报价、收款、订单、履约或销售已完成。

## 2026-08-06｜GPT Project 机制包语义一致性与来源追溯修正

- **目标**：消除 P0/P1/P2 两套定义，修正业务闸门误称为 P0 的表达，统一 blocked/Git 状态词，并让 `project_entry/AGENTS.md` 可由 Manifest 记录的 source commit 复现。
- **实际读取**：根 `AGENTS.md`、`PROJECT_ENTRY.md`、GPT Project 机制包核心文件、Manifest、验证脚本、验证报告和 AGENTS 机制对照审计。
- **第一阶段 source commit**：`28e6f92eb91548fc3f9ef3b79865cb4a591eb4d0`，用于生成 AGENTS 镜像。
- **实际改动**：统一来源优先级定义；将商品、价格、库存、资质、账号、收款、履约和酒类合规前置统一称为 `business_gates（业务闸门）`；新增语义一致性审计；升级 Manifest、验证脚本和验证报告以验证 AGENTS provenance。
- **状态边界**：`package_ready_for_manual_upload = true`；`user_uploaded_to_gpt_project_ui = false`。本条不表示用户已上传 GPT Project UI，也不表示供应链、平台、合规、上线、销售或履约成立。

## 2026-08-06｜GPT Project 配合机制同步包与 AGENTS 交叉审计

- **目标**：补齐汾酒 GPT Project 手动上传用配合机制包，并按 P0 补充要求交叉审计 `AGENTS.md`、`PROJECT_ENTRY.md` 与参考仓库机制。
- **实际读取**：当前汾酒 AGENTS、PROJECT_ENTRY、业务与协作状态、任务执行单；主参考仓库 `fthytwerwt-sudo/-` 根 AGENTS、完整 GPT Project 上传包和关键提交 `4b535ef`、`8a1350b`、`7402250`；补充参考 `fthytwerwt-sudo/lanxinse--` 根 AGENTS 与同名 GPT Project 机制包。
- **实际改动**：新增 `GPT项目资料同步包_gpt_project_mechanism_sync/` 23 文件；新增参考机制学习报告、AGENTS 机制对照审计、验证脚本和验证报告；更新 AGENTS、PROJECT_ENTRY、README、协作流程、任务模板、决策和协作状态。
- **验证结果**：`python3 -m py_compile scripts/validate_gpt_project_mechanism_sync.py` 通过；`python3 scripts/validate_gpt_project_mechanism_sync.py --write-manifest` 通过，文件数 23、系统提示词 3081 字符、Manifest 一致、AGENTS 镜像 SHA 一致、敏感信息/绝对路径/参考项目污染/媒体扫描通过。
- **状态边界**：`package_ready_for_manual_upload = true`；`user_uploaded_to_gpt_project_ui = false`。本条不表示供应链资料已回传、TikTok 酒类边界已确认、业务上线、销售或履约成立。

## 2026-08-05｜协作机制 V2：业务状态与协作状态分离

- **目标**：在不删除原始资料或虚构供应链交付的前提下，修正入口、当前范围、历史研究定位和协作收口状态。
- **实际读取**：用户确认的 TikTok 范围、双方职责、当前阶段与海鲜边界；现有入口、状态、事实源、决策、风险、下一步、模板、Git 历史摘要和 V2 任务要求。
- **审计事实**：旧临时分支有 6 个提交；历史 manifest 与多份历史生成脚本曾包含本机绝对路径/结构信息；高置信凭据规则在 Git 历史命中 0；本地 bundle 已验证可读且不进入仓库。
- **实际改动**：新增 BUSINESS_STATUS 和 COLLABORATION_STATUS；CURRENT_STATUS 改为总览路由；入口、决策、事实源、范围、待确认、风险、下一步和交接模板按当前 TikTok 与供应链启动范围更新。
- **未写为完成**：供应链尚未实际提供 SKU、价格、库存、主体/资质、账号、收款、仓储配送、售后或负责人确认；本条不宣称业务上线、合规许可或履约已完成。
- **待最终收口**：同步包脚本脱敏、干净 main、visibility、默认分支、旧远端分支清理、新同步包验证和远端回读，均以 COLLABORATION_STATUS 的最终证据为准。

## 2026-08-05｜建立跨会话协作与同步包机制

- **目标**：从参考仓库提炼可迁移协作机制，并为汾酒项目建立入口、事实分级、状态/决策体系和同步包自动化。
- **实际改动**：本轮建立的协作文件和同步包脚本见提交 diff；未移动或删除任何现有业务资料。
- **业务状态**：未新增当地许可、平台权限、SKU、库存、合作方确认、订单或销售结论。
- **说明**：该初始机制的部分同步包元数据和历史状态已在 V2 中被替代，具体以当前协作状态和最终远端回读为准。
