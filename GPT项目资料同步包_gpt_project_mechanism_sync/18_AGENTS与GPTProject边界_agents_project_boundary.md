# AGENTS 与 GPT Project 边界

## 两者职责不同

`AGENTS.md` 是 Codex / 仓库协作者进入本地仓库后的操作合同。它规定读取顺序、事实分级、文件修改、Git 和回报要求。

GPT Project 机制包是 ChatGPT 新聊天框的长期配合资料。它规定如何理解汾酒项目、如何判断任务、如何读取 GitHub、如何下发 Codex 和如何复审结果。

## 生成时镜像

本包包含 `project_entry/AGENTS.md`，它是根目录 `AGENTS.md` 的生成时只读镜像，不是新的权威入口。原因：

- `AGENTS.md` 面向仓库执行，内容可能随仓库规则变化。
- GPT Project 需要稳定机制和阅读路线，但也需要知道仓库接手规则。
- 项目事实、执行历史和动态状态必须回读 GitHub `main`。
- 根目录当前 `AGENTS.md` 永远高于 GPT Project 包内镜像。

## 如何配合

1. GPT Project 先用本包判断任务类型和事实层级。
2. 需要当前事实时，要求读取 GitHub `main` 的入口文件。
3. 需要本地写入时，生成 Codex 任务单。
4. Codex 进入仓库后必须遵守 `AGENTS.md`。
5. Codex 完成后，GPT Project 用本包的复审规则检查完成度。

## 冲突处理

如果本包和 `AGENTS.md` 的执行规则冲突，Codex 本地执行时以 `AGENTS.md` 为准；GPT Project 的判断和下发机制以本包为准；业务事实以 GitHub 当前状态文件为准。

## 镜像维护

每次根目录 `AGENTS.md` 发生机制变化时，必须同步更新 `project_entry/AGENTS.md`，并重新生成 `上传清单_manifest.md`。验证脚本必须确认根 AGENTS 与镜像 SHA-256 一致。
