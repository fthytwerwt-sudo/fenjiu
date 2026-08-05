# Codex 执行落库机制

## Codex 的位置

Codex 是本地执行落库层，负责读取事实源、生成文件、运行验证、写报告、commit、push 和远端回读。Codex 不负责替用户外发、发布、收款、下单或承诺履约。

## 下发前置

给 Codex 的任务必须包含：

- `Goal`：本轮真实目标。
- `Context`：当前项目、分支、事实源、业务线。
- `Constraints`：可改与不可改、隐私、合规、Git 边界。
- `Impact check`：是否影响状态、决策、风险、同步包或执行历史。
- `Must read`：明确路径。
- `Execution steps`：按依赖顺序。
- `Validation commands`：能证明完成的命令。
- `Done when`：完成标准。
- `Blocked if`：阻断条件。
- `Output`：回报格式。

## 写入规则

1. 只改任务范围内文件。
2. 不删除或覆盖原始业务资料。
3. 不提交 `.env`、凭据、私人联系方式、媒体、缓存、运行输出。
4. 不把海鲜事实写进汾酒主线。
5. 不把参考仓库业务内容复制进汾酒。
6. 业务状态和协作机制状态分开写。

## 验证规则

Codex 完成前必须按任务运行相关验证。机制包类任务至少检查非空文件、manifest、哈希、敏感信息、本地绝对路径、参考项目污染和用户上传状态。

## Git 规则

只 stage 本轮相关路径，禁止 `git add .`。提交后必须 push 到目标分支，并用远端回读证明核心文件存在。push 失败或 remote HEAD 无法验证时，状态只能是 `partial_completed` 或 `blocked`，不能写完成。
