# GPT Project 机制语义一致性审计

- **审计日期**：2026-08-06
- **目标仓库**：`fthytwerwt-sudo/fenjiu`
- **目标分支**：`main`
- **任务类型**：`mechanism_consistency_fix` + `provenance_repair` + `validation_upgrade`
- **结论**：本轮将 P0/P1/P2 收敛为唯一来源优先级定义；商品、价格、库存、资质、账号、收款、履约和酒类合规前置统一称为 `business_gates（业务闸门）`；绝对禁止违反的边界统一称为 `hard_constraints（硬约束）`。

## 唯一标准定义

| 术语 | 唯一正确表达 | 用途 | 不得表示 |
|---|---|---|---|
| P0 | `P0 = 用户本轮明确输入` | 用户本轮目标、纠正、禁止项、验收标准和本轮明确红线 | 业务重要程度、风险级别、供应链缺口等级 |
| P1 | `P1 = GitHub main 当前事实、当前书面证据和当前验证证据` | 当前仓库事实、供应链书面证据、验证/Git/远端回读证据 | 执行效率或文档质量等级 |
| P2 | `P2 = 历史聊天、账号记忆、旧项目机制、外部资料和通用建议` | 背景、候选机制、待验证参考 | 当前汾酒业务事实 |
| hard_constraints | `hard_constraints（硬约束）` | 不得违反的安全、事实源、业务线、合规和 Git 远端边界 | 供应链资料缺口 |
| business_gates | `business_gates（业务闸门）` | 外部执行前必须满足的 SKU、价格、库存、资质、账号、收款、履约和酒类合规条件 | P0/P1/P2 来源等级 |

## 冲突清单

| 文件 | 当前表达 | 问题 | 唯一正确表达 | 是否修改 |
|---|---|---|---|---|
| `AGENTS.md` | P0 定义包含目标、纠正、验收和红线，但未明说不得表示缺口等级 | 容易被后续文件解释为风险/业务等级 | P0/P1/P2 只表示来源和冲突优先级；业务条件称 `business_gates` | 是 |
| `PROJECT_ENTRY.md` | “P0 阻断外部执行” | 把业务前置条件误命名为 P0 | “业务闸门阻断外部执行”，缺失时 `BLOCKED` | 是 |
| `01_汾酒项目系统提示词_fenjiu_project_system_prompt.md` | P0 = 安全、合规、商品价格库存、账号收款履约等 | P0 被用成风险和业务条件集合 | P0/P1/P2 来源优先级；另设 `hard_constraints`、`business_gates`、`blocked_conditions` | 是 |
| `04_P0-P1-P2锚点与抗漂移机制_anchor_priority_anti_drift.md` | P0 = 不能绕过的安全和事实锚点；P1 = 协作和工程锚点 | 存在第二套 P0/P1/P2 定义 | 整体重写为 P0 用户输入、P1 当前事实证据、P2 历史参考 | 是 |
| `07_供应链启动与资料缺口判断机制_supplier_readiness_gap_protocol.md` | “P0 缺口” | 供应链资料缺口不属于来源优先级 | `business_gate_gaps（业务闸门缺口）` | 是 |
| `09_酒类合规与外部执行闸门_alcohol_compliance_execution_gate.md` | “P0 条件阻断” | 酒类前置证据不属于 P0 | 业务闸门和当前书面证据缺口，状态 `BLOCKED` | 是 |
| `13_六层需求确认与实现设计闸门_six_layer_requirement_gate.md` | `blocked_need_requirement_design` | blocked 状态词与根 AGENTS 不一致 | `blocked_need_implementation_design_layer` | 是 |
| `14_Codex长期执行单模板_codex_task_template.md` | P0/P1/P2 空字段混在 Context 中 | 未区分来源优先级、硬约束和业务闸门 | 分列 P0/P1/P2、`hard_constraints`、`business_gates`、`blocked_conditions` | 是 |
| `15_Codex结果复审与完成度边界_codex_result_review.md` | `partial_completed` | Git 未完成状态词不统一 | `blocked_push_failed`、`local_only_not_completed`、`no_file_change_completed_readonly` | 是 |
| `16_输出硬规则与中文语义对齐_output_hard_rules.md` | “P0 证据齐全” | 把业务证据称为 P0 | “相关业务闸门均有当前书面证据并通过核验” | 是 |
| `17_Git提交推送与远端验证_git_completion_gate.md` | 未列明正式 Git 未完成状态键 | 容易继续使用模糊状态 | 增加三个正式状态键 | 是 |
| `19_用户上传后验证清单_post_upload_validation_checklist.md` | “价格和库存是 P0 阻断”、local-only/partial | 上传后测试会强化错误定义 | 价格和库存属于业务硬闸门；Git 状态使用正式状态键；新增 P0/P1/P2 定义测试 | 是 |
| `上传清单_manifest.md` | `source_commit` 指向旧提交，但 `source_sha256` 为当前 AGENTS SHA | 来源 commit 无法复现镜像 | 第二阶段用第一阶段 commit 的 `git show <source_commit>:AGENTS.md` 生成镜像和 manifest | 待第二阶段 |
| `scripts/validate_gpt_project_mechanism_sync.py` | 只检查关键词存在和镜像当前哈希 | 无法检测两套 P0 定义或来源 commit 不真实 | 增加语义、禁止旧称、状态词和 provenance 检查 | 待第二阶段 |
| `docs/collaboration/GPT_Project同步包验证报告_gpt_project_package_validation_report.md` | “关键词齐全/未发现阻断”式结论 | 把关键词存在误写成机制无冲突 | 第二阶段报告输出语义一致性和来源验证字段 | 待第二阶段 |

## 影响面记录

- 当前目录：`/Volumes/WD_BLACK/汾酒尼泊尔`
- Git 仓库根目录：`/Volumes/WD_BLACK/汾酒尼泊尔`
- 目标分支：`main`
- 目标远端：`https://github.com/fthytwerwt-sudo/fenjiu.git`
- 执行前 HEAD：`c1a3babac6a76e1bc40a315f05f0623e6e0b9bf6`
- GPT Project 包文件数量：23
- 执行前根 AGENTS SHA-256：`658501d453e8e35ea269e536f53d88bae4e891bd8f239c3310ef0baa7b5183cf`
- 执行前镜像 AGENTS SHA-256：`658501d453e8e35ea269e536f53d88bae4e891bd8f239c3310ef0baa7b5183cf`
- 执行前 Manifest `source_commit`：`34547dc895c5617dd3e1bfd7b8467e1021379842`
- 该 commit 中 `AGENTS.md` SHA-256：`bb1ff8d631cf8d9ad1216469132f366dd6954800bce5c6a47c54f0218e6d9c62`
- 结论：执行前 Manifest `source_commit` 无法复现当前镜像，需要第二阶段修复。

## 工作区边界

执行前发现既有未跟踪目录 `docs/implementation/`。该目录属于非本轮改动，本轮不读取、不修改、不暂存；最终状态中若仍出现，只作为无关既有改动报告。
