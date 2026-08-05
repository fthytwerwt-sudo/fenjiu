# Codex 长期执行单模板

本模板用于把 GPT Project 的判断转成 Codex 可执行、可验证、可提交的任务。使用时必须替换为本轮真实路径和事实源。

固定来源优先级定义：

```text
P0 = 用户本轮明确输入
P1 = GitHub main 当前事实、当前书面证据和当前验证证据
P2 = 历史聊天、账号记忆、旧项目机制、外部资料和通用建议
```

```text
# Goal｜目标
本轮任务类型：
本轮真实目标：
本轮不做：
最终产物：

# Context｜上下文
目标仓库：
当前分支：
当前项目事实源：
业务线：
当前阶段：
P0（用户本轮明确输入）：
P1（GitHub main 当前事实、当前书面证据和当前验证证据）：
P2（历史聊天、账号记忆、旧项目机制、外部资料和通用建议）：
hard_constraints（硬约束）：
business_gates（业务闸门）：
blocked_conditions（阻断条件）：

# Constraints｜边界
允许修改：
禁止修改：
禁止上传：
隐私与合规：
Git 约束：

# Impact check｜影响面
是否影响业务状态：
是否影响协作状态：
是否影响同步包：
是否影响执行历史：
是否可能混入海鲜、旧 B2B、多平台或参考项目事实：
是否可能写入动态价格、库存、账号、资质或履约：

# Must read｜必读
1.
2.
3.

# 六层需求确认
目标层：
机制层：
实现设计层：
流程层：
判断标准层：
反馈层：

# Execution steps｜执行
1. 确认 cwd、repo root、branch、remote、git status。
2. `git pull --ff-only`。
3. 读取必读文件。
4. 执行本轮产物生成或修改。
5. 运行验证命令。
6. 扫描 secret、本地绝对路径、媒体、参考项目污染。
7. path-limited stage，禁止 `git add .`。
8. commit。
9. push。
10. remote HEAD 和核心文件回读。

# Validation｜验证
命令：
预期：
失败处理：

# Done when｜完成标准
- 产物存在且非空。
- 验证通过。
- 未混入禁止内容。
- commit / push / remote readback 完成。
- 最终 git status clean 或只剩明确无关改动。

# Blocked if｜阻断
- 必读文件不可读。
- 事实源冲突无法裁决。
- 验证失败。
- 发现 secret 或本地绝对路径。
- push 或 remote readback 失败。

# Output｜回报
主结论：
修改文件：
验证结果：
事实分级：
Git 结果：
未验证项：
用户下一步：
```
