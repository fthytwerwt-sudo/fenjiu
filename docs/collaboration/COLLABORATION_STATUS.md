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
| Default branch | **CONFIRMED（远端读取）**：仍为旧临时分支；目标为干净 main |
| 最近验证远端 branch | **CONFIRMED（远端读取）**：main 已创建 |
| 最近验证远端 commit | **CONFIRMED（远端读取）**：010b24ab76cd7ee1425e2c2ee56e14caae6d06e9 |
| Pull requests | **UNKNOWN**：需要 GitHub API/CLI 认证后回读 |
| 旧临时分支 | **待清理**；必须在 main 成功成为默认分支后再删除 |

## 剩余机制收口

1. **高优先待办**：完成 GitHub CLI 登录，读取并将仓库 visibility 改为 Private。
2. 将 GitHub 默认分支切换为 main，随后删除旧临时远端分支，并回读全部远端状态。
3. 在包含本次状态回填的 main 上重新生成同步包，并完成解压、哈希和新会话接手验证。
4. 用户按需将 `GPT项目资料同步包_gpt_project_mechanism_sync/` 上传到 ChatGPT GPT Project，并用上传后验证清单测试新聊天框。

## 更新规则

只能以实际命令、GitHub/API 回读、脚本验证和可读取的产物更新本文。本文记录最近一次可写入的远端验证；包的 source_commit 表示生成基线，不尝试构造“文件同时记录自身提交”的不可能结构。每次新提交后，最终远端 HEAD 仍须由执行回报再次回读。
