# P00-01｜工程资产与禁区基线审计报告

> **状态：completed_on_task_branch**
> **执行日期：2026-08-06**
> **任务卡：** `docs/implementation/codex_tasks/phase_00/P00-01_engineering_asset_baseline.md`
> **基线提交：** `16e68d97b4ebe1bb4206fbfd531fcefe9bc75f08`
> **范围边界：** 本报告只记录静态工程资产、禁区和 Phase 1 输入；不创建运行时代码，不调用模型/API，不读取密钥值，不改变业务状态。

## 1. 结论

| 项目 | 状态 | 证据与边界 |
|---|---|---|
| 仓库与远端 | 已确认 | 当前任务从指定基线创建独立分支；远端为 `https://github.com/fthytwerwt-sudo/fenjiu.git`。 |
| 运行时工程 | 已确认未实施 | 当前受控 Git 清单未发现 `apps/`、`core/`、`modules/`、`adapters/`、`migrations/`、`tests/`、`docker-compose.yml` 或 `Makefile`。 |
| 文档规划资产 | 已确认可复用 | `docs/implementation/` 已包含 Phase 0-8 蓝图、架构边界、数据合同、导入审批、工作流、CRM、客服、视频和任务卡。 |
| 本地同步/机制脚本 | 已确认可复用 | 仅发现两个根目录 Python 脚本；`--help` 可安全回读，不触发外部调用。 |
| HappyHorse / DashScope / FFmpeg legacy 实体 | 待验证 | 当前受控 Git 清单没有这些 legacy 脚本实体；仅在规划文档中被引用。后续必须在授权位置定位实体后再记录 hash/CLI。 |
| 原始资料、媒体、`.env*`、`research_channels.json` | 已确认未命中当前可见工作树 | 静态路径检查未发现 DOCX/XLSX/PDF/媒体、`.env*` 或 `research_channels.json` 可见文件；仍保持 forbidden。 |
| AppleDouble `._*` | 已确认未命中 | `find . -name '._*' -print` 无输出。 |
| 大文件 | 已确认未命中 | `find . -type f -size +10M -print` 无输出。 |

## 2. 资产矩阵

| 资产 | 分类 | 成熟度 | Phase 1 处理 | 禁止事项 |
|---|---|---|---|---|
| `AGENTS.md`、`PROJECT_ENTRY.md`、`docs/project/*.md` | 可复用控制平面 | 已确认 | 作为所有 Phase 的事实读取入口 | 不把技术完成写成业务完成。 |
| `docs/collaboration/*.md` | 可复用协作记录 | 已确认 | 继续记录执行历史和 Git 收口证据 | 不替代供应链、平台或合规确认。 |
| `GPT项目资料同步包_gpt_project_mechanism_sync/` | GPT Project 机制包 | 已确认 | 仅作机制参考；事实仍回读 GitHub 当前文件 | 不写入动态价格、库存、账号或密钥。 |
| `project_sync/latest/` | 项目事实交接快照 | 已确认但本任务禁改 | 本任务不读取其动态事实、不更新、不 stage | 不作为运行时输入，不在本任务中修改。 |
| `docs/implementation/*.md` | 实施规划资产 | 已确认 | P00-02/P00-03/P01 使用的设计输入 | 不当作已实施系统。 |
| `docs/implementation/codex_tasks/**` | 任务卡 | 已确认 | 一次一张卡推进 | 不跨卡顺手实现。 |
| `scripts/build_project_sync_pack.py` | 包装后可复用工具 | 已确认 | 保留为协作同步工具，不进入业务 runtime | 不复制到 API/worker，不读取秘密。 |
| `scripts/validate_gpt_project_mechanism_sync.py` | 包装后可复用工具 | 已确认 | 保留为机制包验证工具 | 不作为业务合规或销售验证。 |
| HappyHorse / DashScope 视频脚本 | 包装后复用候选 | 待验证 | Phase 7 先定位实体、记录 hash/CLI，再封装 fake/manifest port | 本任务不调用真实模型、不读取 `.env`。 |
| FFmpeg 后处理脚本 | 包装后复用候选 | 待验证 | Phase 7 先确认实体、输入输出和 dry-safe 命令 | 不覆盖历史输出，不发布。 |
| `build_research_channels.py` / `research_channels.json` | 研究参考或 forbidden 输入 | 待验证 / forbidden | 只能作为 future fixture 字段参考；JSON 不进 CRM | 不导入私人联系人，不自动采集。 |
| DOCX/XLSX/PDF/媒体/outputs | 不进 runtime | 当前未命中可见文件 | 只在后续授权任务中作为私有受控输入引用 | 不移动、不改名、不提交、不打包。 |

## 3. Legacy hash 与 CLI 基线

| 文件 | SHA-256 | CLI 基线 | 状态 |
|---|---|---|---|
| `scripts/build_project_sync_pack.py` | `3db48ced864b80949b67bc6b5b940795269f80461ba2688d5b9d5aac8c2ae605` | `--help` 显示 `--verify`，本地同步包生成/验证入口 | 已确认 |
| `scripts/validate_gpt_project_mechanism_sync.py` | `504c7ed887623f2dc8d9629910a244e68f09ba48252e6537a8572e474c7f313e` | `--help` 显示 `--write-manifest`、`--no-report` | 已确认 |
| `generate_happyhorse_shots.py` | UNKNOWN | 未在当前受控 Git 清单中定位 | BLOCKED：需后续授权位置 |
| `generate_happyhorse_video_edit_once.py` | UNKNOWN | 未在当前受控 Git 清单中定位 | BLOCKED：需后续授权位置 |
| `prepare_video_assets.py`、`assemble_final_video.py`、`build_video_execution_report.py` | UNKNOWN | 未在当前受控 Git 清单中定位 | BLOCKED：需后续授权位置 |
| `build_research_channels.py` | UNKNOWN | 未在当前受控 Git 清单中定位 | BLOCKED：不得读取或导入 `research_channels.json` |

## 4. 依赖与技术债

| 项目 | 发现 | Phase 1 影响 |
|---|---|---|
| Python 脚本依赖 | 两个根脚本均以标准库为主，未发现根目录 `requirements.txt`、`pyproject.toml` 或锁文件 | Phase 1 可独立创建 runtime 依赖，不应把协作脚本变成 runtime 依赖。 |
| runtime 目录 | 当前不存在 `apps/`、`core/`、`modules/`、`adapters/`、`fixtures/`、`migrations/`、`tests/` | P01-01 应从空骨架开始，并用 scope/feature flag/health check 证明最小可启动。 |
| 同步包 allowlist | `scripts/build_project_sync_pack.py` 使用严格 allowlist，且对本机路径、秘密、媒体、AppleDouble、`research_channels.json` 分类排除 | Phase 1 不应扩展同步包 allowlist；如需扩展，必须独立验证。 |
| legacy 实体缺位 | 规划文档引用多个视频/研究脚本，但当前受控 Git 未跟踪这些实体 | Phase 7 不能假设已可运行，必须重新定位、hash、CLI、fake provider 和 manifest contract。 |

## 5. 禁区与扫描结果

| 检查 | 命令摘要 | 结果 |
|---|---|---|
| 受控文件清单 | `rg --files`、`git ls-files` | 已回读；当前仓库主要为 Markdown、2 个根 Python 脚本、1 个 YAML、同步包文件。 |
| AppleDouble | `find . -name '._*' -print` | 无命中。 |
| 大文件 | `find . -type f -size +10M -print` | 无命中。 |
| 可见 forbidden 类型 | `find` 按 DOCX/XLSX/PDF/媒体/`.env*`/`research_channels.json` 查找 | 无命中。 |
| Git 受控 forbidden 类型 | `git ls-files` 按 forbidden 模式过滤 | 命中 `project_sync/latest/` 已跟踪快照；本任务未修改、未 stage。 |
| 本机绝对路径 | 对 `docs/implementation`、`scripts`、入口和机制包扫描 | 无命中。 |
| 高置信秘密模式 | 对 `docs/implementation`、`scripts`、入口和机制包扫描 | 无命中。 |
| 业务线污染 | 对新增报告和执行历史做业务线术语复核 | 仅记录隔离边界，不引入海鲜产品、客户、价格、资质或履约结论。 |

## 6. Phase 1 入口冻结

P01-01 可使用本报告作为输入，但只能创建空工程骨架和测试护栏：

1. 保持 `external_execution_allowed=false`、`business_external_ready=false` 的默认业务边界。
2. 新建 runtime 目录时不得迁移原始资料、媒体、`.env*`、`research_channels.json` 或同步包快照。
3. 不把现有协作同步脚本导入业务 runtime。
4. legacy 视频链只可通过后续 Phase 7 的 fake provider / manifest wrapper 进入，不可在 Phase 1 运行真实模型或 FFmpeg 输出。
5. 任一真实供应链资料接入必须等 Phase 8，并以私有受控路径、hash、MIME、人工审批和业务线 scope 为前置。

## 7. 阻断项

| 阻断 | 状态 | 解除条件 |
|---|---|---|
| legacy 视频/研究脚本实体未定位 | BLOCKED | 后续任务在授权位置回读实体、记录 SHA-256、CLI、输入输出和 dry-safe 行为。 |
| 真实供应链资料 | BLOCKED | 供应链提供当前书面 SKU、价格、库存、资质、账号、收款、履约和负责人证据。 |
| 外部业务执行 | BLOCKED | Phase 9 书面证据、feature flag、平台/合规边界和用户授权同时满足。 |
