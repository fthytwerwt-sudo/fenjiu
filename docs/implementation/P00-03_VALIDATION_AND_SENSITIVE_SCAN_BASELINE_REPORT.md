# P00-03｜验证、敏感扫描与 legacy 回归基线报告

> **状态：PARTIAL — 扫描器已实现；授权主工作区基线闸门为 BLOCKED**
> **执行日期：2026-08-06**
> **任务卡：** `docs/implementation/codex_tasks/phase_00/P00-03_validation_and_sensitive_scan_baseline.md`
> **基线提交：** `4349aa221435ca2586c34ae5c727855faa0d0bfd`
> **范围边界：** 本报告只记录 dry-safe 静态验证入口、负例测试和 legacy 基线；不创建 runtime、不调用模型/API、不读取 `.env`、不渲染视频/DOCX/XLSX、不改变业务状态。

## 1. 结论

| 项目 | 状态 | 证据与边界 |
|---|---|---|
| 可重复扫描入口 | 已确认 | 新增 `python3 scripts/validate_regression_baseline.py --base-sha 4349aa221435ca2586c34ae5c727855faa0d0bfd`。 |
| 负例测试 | 已确认 | 新增 stdlib `unittest`，覆盖 forbidden path、`.env.local`、ignored `.env`、非 ASCII ignored `.env*`、symlink 外部文件、overlong path metadata failure、AppleDouble、本机绝对路径、高置信 secret、fixture real-data 标记、无效 base SHA fail-closed 和敏感值不回显。 |
| secret 输出策略 | 已确认 | 命中时只输出类别、路径和固定描述，不输出匹配值。 |
| `.env*` 内容安全 | 已确认 | basename 以 `.env` 开头的路径一律 forbidden；ignored `.env*` 通过 Git ignored 状态按路径发现，且在 `read_text_safely` 前跳过内容扫描。 |
| symlink 安全 | 已确认 | `--all-files` 不收集 symlink entries；内容读取前拒绝 symlink，且 resolved path 必须仍在 root 内。 |
| path metadata fail-closed | 已确认 | 不可访问、畸形或过长路径会输出 `path_scan_failed` 和泛化路径标签，不抛 traceback，不读取候选内容。 |
| Git fail-closed | 已确认 | 指定 `--base-sha` 时，必需的 `git status` / `git diff` / `git ls-files` 失败会输出 `git_scan_failed` 并非零退出。 |
| 授权主工作区基线 | **BLOCKED** | 控制器在授权主工作区复验时，带基线默认模式命中 202 项、`--all-files` 命中 1,262 项既有 ignored 禁入路径，类别为 `appledouble` 和 `forbidden_ignored_path`；无 traceback，且未读取 `.env*` 内容。按任务约束不得删除 `._*` 或放宽规则。 |
| legacy hash/CLI baseline | 已确认 | 仅覆盖 P00-01 定位到的两个根同步/验证脚本；HappyHorse / DashScope / FFmpeg / research legacy 实体继续 `DEFER/BLOCKED`。 |
| 外部行为 | 已确认关闭 | 未联网、未调用模型、未运行真实视频/DOCX/XLSX 渲染、未读取 `.env*`、未改 legacy 业务脚本。 |
| 业务状态 | 未改变 | 仍为汾酒尼泊尔 TikTok 销售准备；外部发布、报价、收款、订单和履约保持 `BLOCKED`。 |

## 2. 扫描入口

```text
python3 scripts/validate_regression_baseline.py --base-sha 4349aa221435ca2586c34ae5c727855faa0d0bfd
```

默认行为：

1. 读取 Git tracked files 做内容扫描；不递归读取 ignored `.env*`。
2. 跳过 `project_sync/latest/` 内容扫描，避免把交接快照当 runtime 输入。
3. 对可见路径检测 forbidden path、basename `.env*`、AppleDouble、`.DS_Store`、大文件和媒体/文档扩展。
4. 对文本文件检测本机绝对路径、高置信 secret-like assignment 和 fixture real-data 标记；`.env*`、`.git`、`.omx`、symlink 和 `project_sync/latest/` 不进入内容读取。
5. 若提供 `--base-sha`，额外用 NUL 分隔的 raw Git records 检查 ignored forbidden paths 与相对基线变更路径，防止 ignored `.env*`、非 ASCII ignored path 或本轮 forbidden 改动被遗漏；Git 命令失败时 fail-closed。
6. 对 P00-01 定位到的两个根脚本验证 SHA-256 和 `--help` token。

命中时退出码为 `1`；通过时退出码为 `0`。

> 控制器复验说明：任务 worktree 中的自身回归测试和干净路径验证通过；授权主工作区含既有 ignored AppleDouble、`.env*` 与其他禁入路径，因此上述入口在该工作区正确返回非零。这是待人工处理的环境基线闸门，不是可忽略的“通过”结果，也不允许由本任务删除或读取这些文件。

## 3. Legacy baseline

| 文件 | SHA-256 | CLI baseline | 状态 |
|---|---|---|---|
| `scripts/build_project_sync_pack.py` | `3db48ced864b80949b67bc6b5b940795269f80461ba2688d5b9d5aac8c2ae605` | `--help` 包含 `--verify` | 已确认 |
| `scripts/validate_gpt_project_mechanism_sync.py` | `504c7ed887623f2dc8d9629910a244e68f09ba48252e6537a8572e474c7f313e` | `--help` 包含 `--write-manifest`、`--no-report` | 已确认 |
| HappyHorse / DashScope / FFmpeg / research legacy | `UNKNOWN` | 未在当前受控 Git 清单中定位 | `DEFER/BLOCKED` |

## 4. 跳过项与原因

| 项目 | 处理 | 原因 |
|---|---|---|
| `.env*` | 不读取内容；路径命中即失败 | 避免读取或回显真实密钥。 |
| `project_sync/latest/` | 默认跳过内容扫描 | P00-03 禁止改该目录；该快照不作为 runtime 输入。 |
| DOCX/XLSX/PDF/媒体 | 路径命中即失败，不渲染 | 防止真实资料、媒体或派生产物进入 Git/runtime。 |
| legacy 视频链 | 不调用 | 当前未定位实体，继续 `DEFER/BLOCKED`。 |
| AppleDouble | 路径命中即失败，不删除 | 本任务禁止删除 AppleDouble。 |

## 5. 验证命令

```text
python3 -m unittest discover -s tests/regression
python3 scripts/validate_regression_baseline.py --base-sha 4349aa221435ca2586c34ae5c727855faa0d0bfd
python3 scripts/validate_regression_baseline.py --base-sha 4349aa221435ca2586c34ae5c727855faa0d0bfd --all-files
python3 scripts/validate_gpt_project_mechanism_sync.py --no-report
git check-ignore .env '._x'
git diff --check
```

## 6. 后续使用

后续任务在修改前后都应运行同一扫描入口。若命中 `high_confidence_secret`、`local_absolute_path`、`fixture_leak`、`forbidden_changed_path` 或 `legacy_hash_mismatch`，应停止提交并转人工复核；不要在日志或报告中复制敏感值。
