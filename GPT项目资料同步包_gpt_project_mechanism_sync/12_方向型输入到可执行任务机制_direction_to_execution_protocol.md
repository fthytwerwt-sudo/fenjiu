# 方向型输入到可执行任务机制

## 方向型输入

用户可能说：“把这个弄好”“按之前机制补齐”“让 Codex 直接做”“项目资料同步一下”“这个不对”。这些不是完整执行单，GPT Project 必须先补成可执行任务。

## 转换步骤

1. 判断真实任务类型：业务事实、机制同步、文档导出、仓库落库、供应链缺口、外部执行。
2. 锁定本轮不做什么，避免范围扩大。
3. 建立六层需求确认。
4. 明确需要读取的 GitHub 文件。
5. 明确产物路径和禁止路径。
6. 列出验证命令和失败条件。
7. 要求 Codex path-limited stage、commit、push、remote readback。

## 最小可执行任务单

```text
Goal:
Context:
Constraints:
Impact check:
Must read:
Primary route:
Fallback route:
Required outputs:
Validation:
Done when:
Blocked if:
Git completion:
```

## 不得省略的边界

- 不猜供应链已经给资料。
- 不猜价格、库存、账号、资质和履约。
- 不把海鲜资料混入汾酒。
- 不把项目机制完成写成业务完成。
- 不把 GPT Project 包已生成写成用户已上传。

## 用户要求直接执行时

如果风险低且边界清楚，可以直接给 Codex 执行；如果涉及外部发布、收款、订单、个人数据、账号权限或合规结论，必须先阻断并说明缺少什么证据。
