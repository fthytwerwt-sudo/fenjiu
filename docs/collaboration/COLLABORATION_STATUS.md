# 协作机制状态｜COLLABORATION_STATUS

- **最近更新**：2026-08-05
- **用途**：记录仓库协作、脱敏、Git 与同步包状态；不替代 BUSINESS_STATUS 中的业务事实。

## 入口与协作规则

| 项目 | 状态 | 说明 |
|---|---|---|
| AGENTS 规则 | **CONFIRMED** | 已要求先读业务状态，再读总览、事实源、范围和协作状态；禁止把机制完成写成业务完成 |
| PROJECT_ENTRY | **CONFIRMED** | 已以 TikTok、供应链启动阶段、双方职责、P0 输入、历史研究降级和海鲜隔离作为首屏信息 |
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
- **同步包版本**：**待验证**；V2 修正后必须重新生成，不能将历史 bundle 误称为 V2 最终包。
- **同步包脚本版本**：**待验证**；以最终安全 main 上的构建脚本 source_commit 为准，不在文档中预写最终 commit。
- **最近本地 bundle 验证日期**：2026-08-05；该验证证明历史 bundle 可读，不替代 V2 重新生成、verify、解压和跨机器可用性检查。
- **待验证**：V2 脱敏脚本修改完成后，须重新生成并验证同步包；该包必须包含 BUSINESS_STATUS 和本文。
- **规则**：manifest 的 source_commit 是生成时的 Git 基线，不是随后提交 project_sync/latest 的 commit；不得构造自我引用版本。
- **规则**：包和 manifest 只可记录跨机器可用的信息；不得包含本机绝对路径、真实排除文件清单、秘密、私人联系资料或本地 ZIP 绝对路径。

## GitHub 收口状态

| 字段 | 当前状态 |
|---|---|
| Repository | fthytwerwt-sudo/fenjiu |
| Visibility | **待最终远端回读**；不得提前写为 Private |
| Default branch | **待最终远端回读**；目标为干净 main |
| 最近验证远端 branch | **待最终远端回读** |
| 最近验证远端 commit | **待最终远端回读** |
| Pull requests | **待最终远端回读** |
| 旧临时分支 | **待清理**；必须在 main 成功成为默认分支后再删除 |

## 剩余机制收口

1. 完成同步包脚本的绝对路径、排除清单和跨机器元数据修正。
2. 在本地备份存在且当前安全内容经扫描后，建立干净 main。
3. 将仓库 visibility 改为 Private；若权限不足，保留为 P0 阻断并记录用户最小操作。
4. 推送 main、设置默认分支、删除旧临时远端分支，并回读全部远端状态。
5. 在干净 main 上重新生成、verify、解压和模拟新会话接手同步包。

## 更新规则

只能以实际命令、GitHub/API 回读、脚本验证和可读取的产物更新本文。最终 main commit、远端 branch、visibility、默认分支和 PR 状态由最终收口执行者回填。
