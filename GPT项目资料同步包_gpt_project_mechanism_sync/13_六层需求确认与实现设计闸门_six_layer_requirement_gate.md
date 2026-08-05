# 六层需求确认与实现设计闸门

## 触发条件

以下情况必须先过六层，不直接下发 Codex：

- 用户需求混杂或方向型。
- 涉及机制修复、同步包、Git 落库或外部资料桥接。
- 会改变长期协作口径。
- 会影响商品、价格、库存、资质、账号、收款或履约判断。
- 用户反馈“不对”“不是这个”“继续补齐”但未说明层级。

## 六层定义

### 1. 目标层

本轮真正达成什么；本轮不解决什么；是否属于汾酒 TikTok 主线、海鲜独立线、协作机制或工具任务。

### 2. 机制层

触发条件、禁止条件、降级条件、能力状态、不可猜测事项和阻断线。

### 3. 实现设计层

必须写清：

```text
primary_route:
fallback_route:
capability_status:
probe_required:
allowed_codex_autonomy:
forbidden_codex_guessing:
required_inputs:
required_outputs:
execution_entrypoints:
validation_commands:
blocked_if_missing:
```

### 4. 流程层

GPT 判断什么，Codex 执行什么，用户确认什么；哪些步骤依赖前置验证。

### 5. 判断标准层

技术通过、内容通过、业务通过、Git 通过、用户使用通过分别是什么。不能用技术通过替代业务通过。

### 6. 反馈层

失败后回到目标层、机制层、实现设计层、流程层、事实源层、合规层还是用户授权层。

## 停止线

缺实现设计层、缺事实源、缺验证命令、缺阻断条件、需要外部执行但缺授权时，输出 `blocked_need_implementation_design_layer`，不要让 Codex 猜。
