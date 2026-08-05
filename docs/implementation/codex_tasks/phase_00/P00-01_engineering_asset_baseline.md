# P00-01｜工程资产与禁区基线审计

| 元数据 | 值 |
|---|---|
| task_id / phase | `P00-01` / `phase_00` |
| status | `PLANNED` |
| depends_on / can_run_in_parallel_with | 无 / 无 |
| writes_to | `docs/implementation/`, `docs/collaboration/EXECUTION_HISTORY.md`（如有真实结果） |
| forbidden_paths | 原始研究、DOCX/XLSX/PDF、媒体、`outputs/`、`.env*`、`research_channels.json`、`project_sync/latest/` |
| estimated_risk / recommended_executor | low / Codex 5.6 Thinking + GPT review |

## Goal

以当前 GitHub/main 与本地文件为证据，建立可复现资产成熟度、legacy hash/CLI、依赖/技术债和禁区清单；不创建运行时代码。

## Context

汾酒业务仍处供应链资料准备；现有 HappyHorse/DashScope/FFmpeg、文档与研究工具可作为候选，不能当运行时系统或业务真值。

## Constraints

只读审计和文档/报告写入；不读取密钥值、不调用模型/API、不移动/删除文件、不把海鲜事实写入汾酒。AppleDouble `._*` 只能报告/忽略，不能批量删除。

## 六层需求确认

- 目标层：资产事实，不是系统实现。
- 机制层：仅 evidence-backed 分类；无法判断写 `UNKNOWN`。
- 实现设计层：`primary_route=rg+hash+CLI-help`；`fallback_route=文件元数据`；`capability_status=read-only`；`probe_required=no network`。
- 流程层：Codex 审计→GPT review→后续任务引用。
- 判断标准层：每项有路径/分类/理由；业务状态不升级。
- 反馈层：发现 secret、路径泄露或不明资料即停止并报告。

## Impact check

检查 `.gitignore`、同步包 allowlist、legacy 调用方、`._*`、敏感/大文件和海鲜资料线，不修改它们。

## Must read

`AGENTS.md`、`PROJECT_ENTRY.md`、`docs/project/{BUSINESS_STATUS,CURRENT_STATUS,SOURCE_OF_TRUTH,SCOPE_AND_BOUNDARIES}.md`、本计划总览和 `ARCHITECTURE_AND_MODULE_BOUNDARIES.md`。

## Execution contract

- Capability status：read-only audit; no runtime capability。
- Probe required：yes — static asset/legacy safety probe only。

- Primary route：`rg --files`、`git ls-files`、hash/`--help` 或安全 import、现有规划对照。
- Fallback route：不能安全执行的脚本仅记录静态接口和阻断。
- Allowed Codex autonomy：新增审计报告、更新实施规划索引。
- Forbidden Codex guessing：脚本可生产使用、外部 API 可用、供应链字段含义、真实账号/密钥。
- Required inputs：当前仓库、上述文件、现有脚本。
- Required outputs：资产矩阵、分类、技术债、legacy baseline、明确 Phase 1 入口。
- Execution entrypoints：`git status --short --branch`、`rg --files`、安全 `--help`。

## Execution steps

1. 核验 cwd/repo/branch/remote/status/HEAD。
2. 分类为可复用、包装后复用、研究参考、不进 runtime、待删除但本轮不删。
3. 记录 legacy hash/CLI 或安全阻断、依赖/环境、敏感与 AppleDouble 风险。
4. 链接 Phase 1 所需目录和禁区，不写业务状态为完成。

## Validation commands

`git status --short --branch`；`rg --files`；对新增 Markdown 做非空、绝对路径、敏感词与链接检查。不得执行联网或读取 `.env` 的命令。

## Done when

资产矩阵可回读、每项分类有依据、Phase 1 输入完整、无原始文件/业务事实被改。

## Blocked if

仓库/remote 不可核验、发现疑似 secret/私人资料、或唯一验证需要真实密钥/API。

## Output 回报格式

已确认/部分成立/UNKNOWN/BLOCKED；资产表；改动与验证；legacy 影响；Git 状态；下一张 `P00-02`。

## Git completion

独立分支、path-limited stage、禁止 `git add .`；commit/push/remote readback 或如实 `local_only_not_completed`。
