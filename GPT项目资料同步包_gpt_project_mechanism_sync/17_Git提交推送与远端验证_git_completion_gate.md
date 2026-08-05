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
- staged diff 发现 secret、本地路径或媒体。

## 回报字段

```text
git_sync_status:
  branch:
  files_staged:
  commit_sha:
  pushed:
  remote_head:
  remote_core_files_readback:
  unrelated_dirty_files:
  secret_scan:
  completed_allowed:
```

## 汾酒特别边界

Git 完成只证明协作文件进入远端仓库。它不证明用户已上传 GPT Project UI，也不证明供应链、平台、合规或业务上线成立。
