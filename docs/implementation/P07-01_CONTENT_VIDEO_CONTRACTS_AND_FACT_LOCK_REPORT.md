# P07-01｜内容/视频合同与 approved-fact lock 报告

> **状态：task_branch_local_validated；最终 commit / push / remote readback 以执行回报为准。**
>
> **执行日期：** 2026-08-09
>
> **精确工程基线：** `origin/main` `eda64feb9945e1f9f2eaa688b1152f87b8182bf5`
>
> **base preservation fix：** 2026-08-09 质量审查发现 `c713e6d` 基于旧 `eda64fe`，相对当前 `origin/main` 会回退已接受的 P05-01 source-policy/crawl/leads 文件。已在本任务分支非破坏性 merge 当前 `origin/main` `914a76146f47734d2989b4d4ce71c5fdaeedd988`，保留 P05-01 全部文件，仅在 `.gitignore` 同时保留 P05 leads fixture allowlist 与 P07 content_video fixture allowlist。
>
> **任务分支：** `codex/p07-01-content-video-fact-lock`
>
> **范围边界：** 仅建立 stdlib、local-only、synthetic 的 content/video 合同、fact/asset/policy version lock、forbidden expression policy、synthetic brief 与 review/QC state。不调用模型、视频 API、HappyHorse、DashScope、FFmpeg 或 legacy 脚本；不写 P02 `approved_fact`；不导出、不发布、不改变业务状态。

## 1. 结论

- 新增 `modules/content_video/contracts.py`，定义 `ContentTask`、`FactVersionLock`、`AssetRightsVersionLock`、`ForbiddenExpressionPolicy`、`PolicyVersionLock`、`SyntheticBrief`、`ContentReviewRecord`、`VideoTask` 与 `ContentPolicySuite`。
- `ContentPolicySuite.submit_for_review()` 只有在 synthetic brief、approved synthetic fact lock、authorized asset rights lock、approved policy lock、current version recheck 和 forbidden-token check 全部通过时，才生成 `review_pending`。
- `VideoTask.from_review()` 只生成 `qc_pending` 的内部 QC handoff；`provider_call_requested`、`internal_export_allowed`、`public_publish_allowed` 均固定 false，任一被设为 true 都 fail closed。
- 新增 `fixtures/content_video/synthetic_policy_vectors.json`，仅含 synthetic AI-generated、supplier-authorized、unknown asset origin vectors 和 forbidden-token policy；不含真实 SKU、素材、价格、库存、资质或客户资料。
- `.gitignore` 仅精确放行上述 content/video synthetic fixture，不放开其他 fixture、媒体或 provider 输出路径。

## 2. Lock 与状态合同

| 合同 | 已验证行为 |
|---|---|
| fact lock | 缺失、非 approved、非 fixture synthetic、过期或 current version 不一致均拒绝；不写入 P02 current truth 或 `approved_fact`。 |
| asset rights lock | `ai_generated` 与 `supplier_authorized` 在 rights authorized 且版本未失效时可进入 review；`unknown` 或过期均拒绝。 |
| policy lock | policy boundary unknown、policy expired、forbidden policy 版本漂移或 current policy version 漂移均拒绝。 |
| forbidden expression | synthetic brief tokens 与 denied policy tokens 相交时返回 `forbidden_expression_detected`。 |
| review/QC state | valid task 到 `review_pending`；video handoff 只到 `qc_pending`，无 provider call、无 internal export、无 public publish。 |

## 3. Test-first evidence

- **RED**：新增 `tests/contracts/test_content_video_contracts.py` 后，首次运行 `python3 -m unittest tests.contracts.test_content_video_contracts` 失败于 `ModuleNotFoundError: No module named 'modules.content_video.contracts'`。
- **GREEN**：新增 content/video 合同实现和导出后，P07-01 专项 8 项通过。
- **Regression scope**：`tests/contracts` 从 62 项扩展到 70 项，完整合同 suite 通过。
- **Base preservation RED**：质量审查指出旧基线分支相对当前 `origin/main` 会删除 P05-01 `.gitignore` leads fixture allowlist、architecture guard、`adapters/crawl/fake.py`、`modules/leads/source_policy.py` 与 P05 tests。
- **Base preservation GREEN**：本分支非破坏性 merge `origin/main` 后，最终 diff relative `origin/main` 只保留 P07-01 允许范围，不再删除或改写 leads/crawl/P05 文件。

## 4. Validation evidence

- `python3 -m unittest tests.contracts.test_content_video_contracts`：8 项通过。
- `python3 -m unittest tests.contracts.test_action_policy_rbac_approvals`：7 项通过。
- `python3 -m unittest tests.contracts.test_audit_metrics_retry_dead_letter`：9 项通过。
- `python3 -m unittest discover -s tests/workflows`：11 项通过。
- `python3 -m unittest discover -s tests/architecture`：8 项通过。
- `python3 -m unittest discover -s tests/contracts`：70 项通过。
- `python3 -m compileall -q -x '(^|/)\._' apps core observability modules adapters workflows tests`：通过。
- `python3 scripts/validate_regression_baseline.py --base-sha eda64feb9945e1f9f2eaa688b1152f87b8182bf5`：通过。
- `python3 scripts/validate_regression_baseline.py --base-sha eda64feb9945e1f9f2eaa688b1152f87b8182bf5 --all-files`：通过。
- `python3 scripts/validate_gpt_project_mechanism_sync.py --no-report`：通过。
- `git diff --check`：通过。
- no-video-call/no-export scan：对 `modules/content_video`、P07-01 tests 和 fixture 扫描 HappyHorse、DashScope、FFmpeg、subprocess、requests、httpx、openai 与强制开启外部能力的模式，无命中。
- `make regression`：通过；两轮 migration replay、16 类 SQL negative constraints、8 architecture、14 regression、8 local-runtime、16 control-plane、70 contracts、35 ingestion tests 全部通过；隔离 Docker containers/volumes 回查为空。

## 5. 工程治理检查

- `repository_hygiene_check（仓库卫生检查）`：新增内容仅为 stdlib 合同、synthetic fixture、专项测试和报告；P00 default 与 `--all-files` 均通过，未发现 secret、token、cookie、本地绝对路径、媒体或 forbidden path。
- `configuration_validation（配置验证）`：未新增环境变量、配置文件、生产连接、真实账号、provider endpoint 或外部服务。
- `data_safety_check（数据安全检查）`：未读取或写入真实供应链、客户、价格、库存、资质、身份资料、海鲜资料或 legacy 输出；fixture 明确 `is_synthetic=true` 且 external flags 为 false。
- `dependency_compatibility_check（依赖兼容检查）`：`not_applicable`；未新增或修改依赖。
- `failure_handling（失败处理）/ negative behavior test（负向行为测试）`：覆盖 missing/unapproved/expired fact、asset rights unknown、forbidden expression、policy/asset/fact version invalidation、unknown policy、expired policy、unknown synthetic asset vector、no-video-call 和 no-export。

## 6. 事实分级与剩余阻断

- **CONFIRMED（工程）**：P07-01 content/video synthetic contracts、version locks、forbidden policy、review/QC state 和 fail-closed checks 已由专项与回归测试验证。
- **CONFIRMED（工程边界）**：没有模型/API/video provider 调用，没有 HappyHorse/DashScope/FFmpeg/legacy 修改，没有 external publish、internal export、P02 `approved_fact` 写入或业务状态升级。
- **BLOCKED（业务）**：真实 SKU、素材授权、平台酒类边界、价格、库存、主体/资质、账号、收款、履约、真实 content approval、provider cost approval、视频生成和公开发布仍未建立或未获书面证据。
- **不成立**：本任务不代表内容可发布、视频可生成、平台允许、供应链已确认、真实素材可用、销售或履约就绪。

## 7. P07-02 handoff

- 可复用输入：`ContentReviewRecord` 的 `locked_fact_versions`、`locked_asset_versions`、`policy_version` 与 `content_task_id`；`VideoTask` 的 `qc_pending` 状态可作为 fake provider manifest 的上游安全输入。
- P07-02 必须继续保持 `provider_call_requested=false` 直到 fake `VideoPort` 与 legacy hash/CLI/dry-safe wrapper 证明完成；不得直接调用 HappyHorse、DashScope、FFmpeg 或真实 provider。
- P07-02 应继续使用 synthetic fixture，并验证 legacy hash/CLI 未变、manifest 不含 payload、provider ID 不进入 truth、edit no-retry 语义保留、失败进入 manual review。
