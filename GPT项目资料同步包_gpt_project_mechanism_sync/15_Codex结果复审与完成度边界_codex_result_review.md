# Codex 结果复审与完成度边界

## 复审原则

Codex 说完成后，GPT Project 仍要复审。复审不是不信任，而是把“文件生成”“仓库同步”“业务完成”分开。

## 必查项

| 检查项 | 合格标准 |
|---|---|
| 必读文件 | 按任务要求读取了 GitHub 当前事实源 |
| 范围 | 没有改禁止文件，没有扩到供应链业务事实 |
| 业务线 | 没有混入海鲜、旧 B2B、多平台或参考项目业务 |
| 动态事实 | 没有编造 SKU、价格、库存、资质、账号、收款、履约 |
| 验证 | 验证命令运行且结果可复述 |
| 安全 | 无 secret、私人联系方式、本地绝对路径、媒体、缓存 |
| Git | 明确路径 stage、commit、push、remote readback |
| 状态 | 没把机制完成写成业务上线或 GPT Project UI 已上传 |

## 完成度边界

- `file_generated`：本地文件存在。
- `validation_passed`：本地验证通过。
- `committed`：本轮相关文件已提交。
- `pushed`：提交已推到远端目标分支。
- `remote_readback_verified`：远端核心文件可回读。
- `package_ready_for_manual_upload`：同步包可交用户上传。
- `user_uploaded_to_gpt_project_ui`：只有用户在 ChatGPT UI 上传并确认后才可为 true。
- `business_ready`：只有业务证据满足时才可判断，不由机制包决定。

## 复审失败处理

发现缺文件、空文件、manifest 不一致、系统提示词过长、参考项目污染、secret、本地路径、push 失败或远端不可读时，按原因写 `blocked_push_failed`、`local_only_not_completed` 或 `BLOCKED`，并让 Codex 修复对应层级。只读任务无文件变化且已完成回读时，状态可写 `no_file_change_completed_readonly`。
