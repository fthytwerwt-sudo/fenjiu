# 项目同步包说明｜Project Sync Pack

## 作用

同步包将新会话接手所需的入口、状态、目标、边界、决策、风险、下一步、事实源、模板、执行历史、Git 状态和文件索引整理为轻量包。它不是业务原始资料的全量备份，也不证明业务/合规状态已经成立。

## 一条命令生成

在仓库根目录运行：

```bash
python3 scripts/build_project_sync_pack.py
```

可使用以下检查命令验证已生成包：

```bash
python3 scripts/build_project_sync_pack.py --verify
```

## 生成位置

- 最新、可直接阅读的目录：`project_sync/latest/`
- 当前 manifest 指针：`project_sync/PROJECT_SYNC_MANIFEST.json`
- 不覆盖历史的 ZIP：`dist/fenjiu_project_sync_pack_YYYYMMDD_HHMMSS.zip`

脚本使用 Python 标准库，自动记录当前分支、commit、工作区状态和生成时间。ZIP 默认被 `.gitignore` 排除；`project_sync/latest/` 可以随着项目状态进入版本控制。

## 何时生成

- 完成重要任务、生成重要资料或修改机制后；
- 修改目标、边界、决定、风险、下一步或事实源后；
- 切换聊天框、电脑、执行 Agent 或交接给合作方前；
- commit/push 后需要给新会话当前 Git 状态时。

## 默认排除

`.git`、`.env`、密钥/Token/Cookie/密码类文件、线索库、媒体、图片、视频、渲染、QA、缓存、临时/构建产物、虚拟环境与超出 1 MiB 限制的文件。脚本还会扫描同步包 allowlist；发现疑似秘密会失败退出，而不是打包。

## 交给新 ChatGPT / Codex 的 Prompt

```text
请先阅读同步包中的 PROJECT_SYNC_README.md、AGENTS.md、PROJECT_ENTRY.md、CURRENT_STATUS.md 和 SOURCE_OF_TRUTH.md。在开始执行前，先说明你理解的项目目标、当前阶段、任务边界、已确认事实、未知项和本轮完成标准。不要把未知项当成事实，也不要修改任务范围外的文件；未经明确授权，不外发、不发布、不投放、不下单。
```
