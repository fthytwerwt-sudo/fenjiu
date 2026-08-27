# 同步包维护与更新机制

## 何时需要更新

以下情况触发 GPT Project 机制包更新：

- 项目长期协作方式变化。
- 项目北极星、渠道边界、AI 优先级或 Codex 判断规则变化（例如 Sales-First 重规划）。
- GitHub 事实源读取顺序变化。
- Codex 任务单格式或 Git 闭环要求变化。
- 新增重要业务线隔离规则。
- 用户反馈新聊天仍误解项目。
- 发现旧 B2B、多平台、海鲜或参考项目污染。

## 不需要更新的情况

以下动态事实不应直接写入机制包：

- 新价格、新库存、新 SKU。
- 账号权限、收款路径、订单、发货、售后。
- 某次供应链回复或某次平台规则截图。
- 一次执行日志或临时验证结果。

这些应写入 GitHub 当前事实、状态、风险、决策或执行历史，而不是长期 GPT Project 机制包。

## 更新流程

1. 读取 GitHub 当前事实源和本机制包。
2. 判断是机制变化还是业务事实变化。
3. 只修改机制相关文件。
4. 若根 `AGENTS.md` 改动，同步更新 `project_entry/AGENTS.md` 镜像。
5. 重新生成 manifest。
6. 运行验证脚本。
7. 更新验证报告和必要执行历史。
8. path-limited commit、push、remote readback。
9. 告诉用户需要手动重新上传 GPT Project UI。

## 版本边界

`package_ready_for_manual_upload = true` 只说明本地包可以上传。`user_uploaded_to_gpt_project_ui = false` 必须保持，直到用户明确完成 UI 上传并测试通过。
