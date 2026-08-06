# 执行报告模板

    ## 结论
    - 状态：completed / local_only_not_completed / blocked_push_failed / no_file_change_completed_readonly / BLOCKED
    - 本轮实现了什么：

    ## 业务与协作状态
    - 业务事实是否变化：
    - 协作/Git/同步包事实是否变化：
    - 不得把后者写成前者已完成：

    ## 事实分级
    - CONFIRMED：
    - INFERRED：
    - UNKNOWN：
    - BLOCKED：
    - SUPERSEDED：

    ## 实际修改
    - 文件：用途：

    ## 验证
    - 命令：结果：
    - 未测试项及原因：

    ## 工程治理检查
    - repository_hygiene_check（仓库卫生检查）：检查密钥、访问令牌、身份凭证、本地绝对路径、私有数据和禁止提交内容。
    - configuration_boundary_status（配置边界状态）：确认配置未带入生产信息、真实账号或敏感连接信息。
    - data_safety_check（数据安全检查）：确认真实业务资料、个人信息和业务线边界未被误读、误写或误提交。
    - dependency_compatibility_check（依赖兼容检查）：仅在依赖变化时，记录兼容性、许可证和维护风险；无依赖变化时写 `not_applicable（不适用）`。
    - failure_handling_check（失败处理检查）：说明错误输入、权限不足、缺失资料或恢复失败时是否安全停止。

    ## Git
    - 分支：
    - Commit：
    - 推送/远端回读：

    ## 下一步与需要确认项
    -

不得以计划代替实际执行，不得以文件存在代替供应链、平台、合规或合作方确认。
