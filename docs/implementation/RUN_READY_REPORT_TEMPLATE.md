# Run-ready 报告模板

> 仅当 Phase 8 完成后生成。报告只能基于实际 run、测试、审批与来源证据填写；空项写 `UNKNOWN` / `BLOCKED`，不能补猜。

```markdown
# Run-ready Report｜<business_line>｜<report_id>

## 结论
- technical_ready: true | false | blocked
- data_ready: true | false | blocked
- business_external_ready: false（除非 Phase 9 独立证据逐项列明）
- external_execution_allowed policy flag: false（状态字段与策略字段不得互相代替）
- 结论范围：内部受控运行 / 仅指定模块 / 不含外部执行

## 资料入场与真值
- receiving package / source hashes / received dates / owners:
- ingestion jobs / parser + mapping versions:
- missing / conflict / expired counts and owners:
- reviewer approvals / rejected/revised decisions:
- approved fact version set and effective windows:
- fixture isolation proof:

## 模块就绪
| module | allowed internal capability | forced-off capability | fact/policy version | evidence |
|---|---|---|---|---|
| ingestion | | | | |
| CRM / leads | | | | |
| customer service | | | | |
| content / video | | | | |
| workflow / audit | | | | |

## 回归与安全
- unit / contract / integration / E2E / legacy regression commands and results:
- negative tests: fixture leakage / cross-line / expired fact / DNC / high-risk handoff / zero external actions:
- logs / secret / local-path scan:
- RBAC / approval / audit / retry / dead-letter evidence:
- rollback drill and feature-flag state:

## 外部上线闸门（必须逐项独立）
- local entity, licences, brand authorisation:
- TikTok alcohol content/ads/live/link rules:
- account owner/admin rights:
- price/inventory/fulfilment/refund/settlement:
- payment/order path:
- user explicit authorisation:
- unresolved items: BLOCKED

## Git 与复现
- branch / commit / remote HEAD / key-file readback:
- environment versions / compose image digests / SBOM:
- execution correlation IDs and private evidence location references:
- unrelated worktree changes:

## 下一步
- owner / action / completion evidence / stop condition:
```

当 `technical_ready=true`、`data_ready=true`、`business_external_ready=false` 且 `external_execution_allowed=false` 时，报告标题和结论必须明确“内部受控运行”，不得写“已上线”“可销售”“已获许可”或“已开始履约”。
