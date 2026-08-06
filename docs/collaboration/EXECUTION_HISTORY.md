# 执行历史｜EXECUTION_HISTORY

此处只记录真实仓库执行，不补写没有证据的业务动作。每个实质变更、生成、验证、commit/push 或新阻断点应新增条目。

## 2026-08-06｜P01-01 模块化单体 skeleton 与导入边界

- **目标**：只建立可 import、可测试的 Python skeleton，不实现产品、CRM、客服、数据库、网络或任何外部 adapter。
- **实际改动**：新增 apps/core/modules/adapters/workflows 的空包、模块 ownership README、typed scope/error/port 占位、synthetic-only fixture metadata、迁移占位与 architecture tests；`.gitignore` 仅放行 P01 必需源码及两份 fixture 文件。
- **审查与验证**：控制器发现并修复了 committed diff 尾部空白、相对导入可绕过 application/security 边界、fixtures allowlist 过宽及 AppleDouble 元数据导致边界测试解码失败四项问题。最终在干净 task worktree 通过 `compileall`、8 项 architecture tests、12 项 P00 回归以及两种 P00 扫描；控制器在外置盘根目录复验 8 项 architecture tests 与 12 项 P00 回归均通过，`main` 远端已回读。
- **状态边界**：外部动作默认全为 false；无新增依赖、ORM、数据库、网络、模型、SDK、真实资料或业务状态。P01-02/P01-03 仍待执行，不能把 skeleton 写成可运行销售系统。

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
