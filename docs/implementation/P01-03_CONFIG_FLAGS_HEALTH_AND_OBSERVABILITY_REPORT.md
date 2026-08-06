# P01-03｜配置、默认关闭 flags、健康检查与基础日志报告

> **状态：followup_fix_verified_locally_pending_remote_readback**
> **执行日期：2026-08-06**
> **任务卡：** `docs/implementation/codex_tasks/phase_01/P01-03_config_flags_health_and_observability.md`
> **基线提交：** `0c4a699d0cf20cad9090581230e70649e0d7665d`
> **范围边界：** 本报告只记录 stdlib-only 的 local control plane；不读取环境变量、文件配置或 secret reference 值，不连接 broker/provider，不新增 HTTP 外部能力、数据库连接、业务写入或外部动作。

## 1. Settings 与 feature flags

- `ControlPlaneSettings` 是类型化静态合同，不包含环境、文件或 secret reference loader。
- unknown/invalid 配置只保留稳定状态码，不保留原始值，且 readiness 始终为 `false`。
- `FeatureFlagPort` 与 `FailClosedFeatureFlags` 无 override/config 入口；fixture、prompt、unknown flag 均返回 `false`。
- 敏感动作包括 send、publish、quote、refund、order、payment、inventory writeback、real crawl、real video、external execution 与 business external ready，全部默认关闭。

## 2. Liveness 与 readiness

- `/health` 保留为 liveness 兼容入口，`/live` 为显式 liveness；本地进程可返回 healthy。
- `/ready` 在缺 broker/provider/real configuration 时返回 `not_ready` 与 HTTP 503，不伪装业务 ready。
- payload 只包含 component、check、status、boolean 健康结果、capability status 与稳定 reason code；不包含 scope、flag/config 值、secret 或路径。
- Docker 仍只使用固定 loopback liveness healthcheck，不接受任意 URL。

## 3. JSON log 与脱敏

- `JsonLogEvent` 强制携带 `correlation_id`、component、event 和 result，输出单行 JSON。
- message/file/content/payload/API key/Cookie/authorization/token/password/secret/path 类 metadata 键值全部保守脱敏。
- metadata 的任意字符串值默认 fail-closed：只允许完整匹配严格 safe identifier/code 格式的 ASCII 字符串；其余自由文本、URL、endpoint、DSN、多行或过长字符串统一输出 `[REDACTED]`。
- `url`、`uri`、`endpoint`、`dsn` 也属于敏感键 token；原有本机绝对路径、Windows 绝对路径和 authorization/cookie/token 特征拒绝仍保留。
- numeric、boolean 以及 `flag_disabled`、`provider_unavailable` 等安全 policy/status code 仍保持结构化可用。
- 未知对象不调用 `repr`，避免意外输出内容。

## 4. 技术与业务边界

本任务只建立安全默认、健康合同和日志脱敏基础。它不解除 SKU、价格、库存、主体/资质、账号、收款、履约或 TikTok 酒类边界的业务闸门；公开发布、报价、收款、下单、退款和履约仍为关闭。

## 5. 本地验证证据

- control-plane 目标测试：16 项通过，覆盖 typed settings、invalid/unknown fail-closed、feature flag 拒绝、HTTP liveness/readiness、secret/path 脱敏，以及中性键自由文本、URL/endpoint/DSN 不泄露负例。
- `make regression`：8 项 architecture、14 项 scanner regression、8 项 local-runtime 与 16 项 control-plane 全部通过。
- P00 scanner：对指定 base SHA 的 default 与 `--all-files` 模式在修改前、修改后均通过。
- Docker 生命周期：isolated `dev-up`、liveness、migration no-op、fixture no-op 与 `dev-down` 通过；API/admin/worker readiness 均按预期拒绝，未留下该 project 容器。
- `git diff --check`：通过。

原 P01-03 实现提交已完成 push 和 remote readback。本次日志 fail-closed 跟进修复已完成本地验证，须在新 Lore commit push 且远程核心文件回读一致后才可写为 task branch 跟进完成。无论该技术状态如何，都不表示已合并 `main`、已开启远程 CI 或已具备外部业务条件。
