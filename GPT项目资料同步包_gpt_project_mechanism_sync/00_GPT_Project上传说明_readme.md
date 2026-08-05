# GPT Project 上传说明

## 文件定位

`已确认`：本目录是汾酒尼泊尔项目给 ChatGPT GPT Project 手动上传的配合机制同步包。

它的用途是让新聊天框先理解“如何配合、如何判断、如何读取事实、如何下发 Codex”，不是保存实时业务事实。业务事实仍以 GitHub `main` 当前文件为准。

## 与 GitHub 项目事实交接包的区别

| 包 | 路径 | 主要用途 | 能不能替代对方 |
|---|---|---|---|
| GitHub 项目事实交接包 | `project_sync/latest/` | 保存当前业务状态、协作状态、事实源、风险和 Git 状态快照 | 不能替代 GPT Project 机制包 |
| GPT Project 配合机制同步包 | `GPT项目资料同步包_gpt_project_mechanism_sync/` | 教 GPT Project 长期怎样理解汾酒项目、分层判断、下发 Codex 和复审结果 | 不能替代 GitHub 当前事实源 |

`project_sync/latest/` 是给新会话或 Codex 快速接手项目事实的交接包；本目录是给 GPT Project 上传的长期协作机制包。两者不能混用。

## 当前状态

```text
package_ready_for_manual_upload = true
user_uploaded_to_gpt_project_ui = false
gpt_project_ui_effective_status = not_claimed
```

本目录生成和通过验证，只说明本地上传包已准备好；不表示用户已在 ChatGPT UI 上传，也不表示新聊天已经生效。

## 推荐上传方式

1. 将 `01_汾酒项目系统提示词_fenjiu_project_system_prompt.md` 的正文复制到 GPT Project 的 Project Instructions。
2. 将本目录内其余 Markdown 文件上传为 Project Knowledge。
3. `上传清单_manifest.md` 也建议上传，便于 GPT Project 知道文件顺序、用途和边界。
4. `project_entry/AGENTS.md` 是根目录 `AGENTS.md` 的生成时只读镜像，建议作为 Knowledge 上传，方便 GPT Project 理解仓库接手规则；若它与 GitHub `main` 当前根 AGENTS 冲突，以 GitHub 当前文件为准。
5. 上传后用 `19_用户上传后验证清单_post_upload_validation_checklist.md` 的测试问题验证新聊天是否理解项目。

## 推荐阅读顺序

1. `01_汾酒项目系统提示词_fenjiu_project_system_prompt.md`
2. `02_项目身份与长期业务边界_project_identity_stable_scope.md`
3. `03_三层架构与事实源边界_three_layer_source_boundary.md`
4. `04_P0-P1-P2锚点与抗漂移机制_anchor_priority_anti_drift.md`
5. `05_GitHub事实源读取机制_github_fact_source_protocol.md`
6. `06_Codex执行落库机制_codex_execution_to_repo_protocol.md`
7. 遇到具体任务时，再按 manifest 的读取顺序补读对应机制文件。

## 术语边界

- `P0 = 用户本轮明确输入`
- `P1 = GitHub main 当前事实、当前书面证据和当前验证证据`
- `P2 = 历史聊天、账号记忆、旧项目机制、外部资料和通用建议`
- `business_gates（业务闸门）`：商品、价格、库存、资质、账号、收款、履约和酒类合规前置。
- `hard_constraints（硬约束）`：不得违反的安全、事实源、业务线、合规和 Git 远端边界。

P0/P1/P2 只表示来源优先级，不表示业务重要程度、风险级别或供应链缺口等级。业务闸门缺少当前书面证据时，状态统一为 `BLOCKED`。

## 禁止上传内容

不得把以下内容加入 GPT Project Knowledge：

- 密码、Token、API Key、Cookie、验证码、账号恢复信息。
- 私人手机号、真实客户联系方式、未审核线索。
- 实时价格、库存、账号权限、收款信息、订单或履约记录。
- 本地绝对路径、`.env`、缓存、临时输出、视频、图片、音频、ZIP。
- 参考仓库的业务身份、素材、模型、API 状态、执行日志或完成结论。

## 一句话口径

GPT Project 保存配合机制；GitHub `main` 保存项目事实；Codex 负责本地执行、验证、落库、commit、push 和远端回读；用户负责最终业务授权和 GPT Project UI 手动上传。

## AGENTS 镜像状态

`project_entry/AGENTS.md` 记录生成时的仓库接手入口快照。Manifest 会记录该镜像的字符数和 SHA-256；验证脚本会检查它与根目录 `AGENTS.md` 内容一致。更新根 AGENTS 后，必须同步更新该镜像、Manifest 和验证报告。
