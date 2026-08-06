# Git 提交推送与远端验证闸门

## 触发条件

只要 Codex 创建或修改仓库文件，就触发 Git 完成闸门。

## 必做步骤

1. 查看 `git status --short --branch`。
2. 检查 diff，确认只包含本轮相关文件。
3. 只 stage 明确路径，禁止 `git add .`。
4. 运行相关验证和 staged diff 检查。
5. commit，提交信息说明为什么改。
6. push 到本轮目标分支。
7. 用远端 HEAD 或远端文件回读验证。
8. 最终检查 git status。

## 不能写 completed 的情况

- 只有本地文件，没有 commit。
- commit 了但没 push。
- push 到错误分支。
- remote HEAD 无法验证。
- 远端核心文件无法回读。
- 混入 unrelated dirty files。
- `repository hygiene check（仓库卫生检查）` 发现 `secret（密钥）`、本地路径或媒体。

## 正式状态键

- `blocked_push_failed`：push 失败或远端拒绝。
- `local_only_not_completed`：本地文件或 commit 存在，但未完成 push 和远端回读。
- `no_file_change_completed_readonly`：只读核验任务无文件变化，且已完成必要回读。

不要使用模糊的部分完成或本地-only 类表述作为正式完成状态；如需自然语言解释，必须同时给出上述正式状态键。

## 回报字段

```text
git_sync_status: # Git 同步状态
  branch: # 分支
  files_staged: # 已暂存文件
  commit_sha: # 提交 SHA
  pushed: # 是否已推送
  remote_head: # 远端提交指针
  remote_core_files_readback: # 远端核心文件回读
  unrelated_dirty_files: # 无关脏文件
  repository_hygiene_check: # 仓库卫生检查：密钥、身份凭证、本地路径和禁止提交内容
  configuration_boundary_status: # 配置边界状态：配置未带入生产信息、真实账号或敏感连接
  data_safety_check: # 数据安全检查：真实业务资料和业务线边界未被误提交
  dependency_compatibility_check: # 依赖兼容检查：仅在依赖变化时记录兼容性、许可证和维护风险
  completed_allowed: # 是否允许写 completed
```

## 汾酒特别边界

Git 完成只证明协作文件进入远端仓库。它不证明用户已上传 GPT Project UI，也不证明供应链、平台、合规或业务上线成立。
