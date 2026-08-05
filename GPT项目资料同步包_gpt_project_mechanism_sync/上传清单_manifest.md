# GPT Project 配合机制上传清单

`package_ready_for_manual_upload = true`

`user_uploaded_to_gpt_project_ui = false`

## AGENTS 镜像来源

- `source_repository`: `fthytwerwt-sudo/fenjiu`
- `source_branch`: `main`
- `source_commit`: `34547dc895c5617dd3e1bfd7b8467e1021379842`
- `source_file`: `AGENTS.md`
- `source_sha256`: `658501d453e8e35ea269e536f53d88bae4e891bd8f239c3310ef0baa7b5183cf`
- `mirror_file`: `project_entry/AGENTS.md`
- `mirror_generated_at_utc`: `2026-08-05T16:44:47Z`

本清单由验证脚本根据实际文件生成。字符数和 SHA-256 以当前目录内容为准。

| 文件路径 | 中文用途 | 上传位置 | 字符数 | SHA-256 | 是否包含动态项目事实 | 敏感扫描 | 推荐读取顺序 |
|---|---|---|---:|---|---|---|---:|
| `00_GPT_Project上传说明_readme.md` | 说明上传方式、状态边界和禁止上传内容 | Project Knowledge | 2052 | `f0dea341dbba74d4881b3b143652620e0216a17054393226de3bef6852fd5a06` | 否 | 通过 | 1 |
| `上传清单_manifest.md` | 列出文件、用途、上传位置、字符数和哈希 | Project Knowledge | 5058 | `self-referential-see-validation-report` | 否 | 通过 | 2 |
| `01_汾酒项目系统提示词_fenjiu_project_system_prompt.md` | 复制到 Project Instructions 的汾酒专用系统提示词 | Project Instructions | 3081 | `3e2c4c17757c1be09a07f1b92889158ba7388697e8302caaabf5c7aa64704930` | 否 | 通过 | 3 |
| `02_项目身份与长期业务边界_project_identity_stable_scope.md` | 固定汾酒尼泊尔 TikTok 主线和业务边界 | Project Knowledge | 866 | `43197c6faf53a6b299fd4d9988ad9bb66c9abfe8d5be8d884a47587ea8866b5a` | 否 | 通过 | 4 |
| `03_三层架构与事实源边界_three_layer_source_boundary.md` | 区分 GPT Project、GitHub、Codex 和账号记忆 | Project Knowledge | 715 | `bd35ad5e723cd87ed7952f63ba6232d8b763b5241b836c6ac20fdba90340ae78` | 否 | 通过 | 5 |
| `04_P0-P1-P2锚点与抗漂移机制_anchor_priority_anti_drift.md` | 规定优先级和抗漂移检查 | Project Knowledge | 701 | `12b28f4de6e9475001dd94438eda55f77b80857a6c93b7eff3a2bc17fd92e273` | 否 | 通过 | 6 |
| `05_GitHub事实源读取机制_github_fact_source_protocol.md` | 规定何时回读 GitHub 当前事实源 | Project Knowledge | 909 | `221cfac2cf976738207f73933209c42e688de02a7f7deea05963e9b31b0c62cd` | 否 | 通过 | 7 |
| `06_Codex执行落库机制_codex_execution_to_repo_protocol.md` | 规定 Codex 执行、验证、提交和推送 | Project Knowledge | 769 | `faaf454ea62f8694a779b1e9328ac317171fa90c18bd4caee38d2eba6e1e2e86` | 否 | 通过 | 8 |
| `07_供应链启动与资料缺口判断机制_supplier_readiness_gap_protocol.md` | 判断商品、价格、库存、资质和履约缺口 | Project Knowledge | 660 | `d5c8aa9e0f8fea3974632fdd3d8d5b92c853c13489afa35dc26f3c550b388325` | 否 | 通过 | 9 |
| `08_TikTok主线与渠道边界_tiktok_channel_scope_protocol.md` | 限定 TikTok 主线和辅助渠道边界 | Project Knowledge | 630 | `4adc67a43cf5705151e8904c67132dfa0c847f7c320a347749ff63dc2ed3e96c` | 否 | 通过 | 10 |
| `09_酒类合规与外部执行闸门_alcohol_compliance_execution_gate.md` | 规定公开发布、投放、收款和履约的前置条件 | Project Knowledge | 491 | `defca3a5a6436e72f8865579c98c44120b6bd2c56c31415d6165aff61372aed7` | 否 | 通过 | 11 |
| `10_汾酒与海鲜业务线隔离机制_business_line_isolation.md` | 防止海鲜资料污染汾酒主线 | Project Knowledge | 436 | `9a23b14406282e2f21879035546793b18a1ca7db563b0f66314e76104bfc65db` | 否 | 通过 | 12 |
| `11_外部资料保真与执行桥接_external_evidence_bridge.md` | 把外部资料保真转为待验证输入或任务 | Project Knowledge | 626 | `8e55a632217f347853f96751786bcb983c9a6db69e3935479fe9d027497515ae` | 否 | 通过 | 13 |
| `12_方向型输入到可执行任务机制_direction_to_execution_protocol.md` | 把模糊输入转为可执行任务单 | Project Knowledge | 689 | `e0f425dafd67104e89e558e3049a31bc7c0b57951ac56a89b609d71ae78a69cd` | 否 | 通过 | 14 |
| `13_六层需求确认与实现设计闸门_six_layer_requirement_gate.md` | 定义目标、机制、实现设计、流程、标准和反馈六层 | Project Knowledge | 796 | `eddee82933b83c39d3797294f8872bc0271407b35527d542f85841046a0122e3` | 否 | 通过 | 15 |
| `14_Codex长期执行单模板_codex_task_template.md` | 提供长期复用的 Codex 下发模板 | Project Knowledge | 974 | `1e607483586496d98e50f5e584d1f3e82ea7fe79f2c01a1427ce6144a218e2f8` | 否 | 通过 | 16 |
| `15_Codex结果复审与完成度边界_codex_result_review.md` | 复审 Codex 结果和完成度边界 | Project Knowledge | 854 | `893a0c9156f63ccf395b54dfc6ada9edb6fa859226b78ef54c0fa81ca2abb771` | 否 | 通过 | 17 |
| `16_输出硬规则与中文语义对齐_output_hard_rules.md` | 规定中文状态词和禁止夸大表达 | Project Knowledge | 563 | `e089ef9083338182482e47fe98d661e4e12d837a6ee6eae1ab89198095b8a25d` | 否 | 通过 | 18 |
| `17_Git提交推送与远端验证_git_completion_gate.md` | 规定 commit、push 和 remote readback 闸门 | Project Knowledge | 718 | `dc7505e03744a2538a937995bc08bdd16b3e7df11f3011bde35dea7001a9069f` | 否 | 通过 | 19 |
| `18_AGENTS与GPTProject边界_agents_project_boundary.md` | 区分仓库 AGENTS 与 GPT Project 机制包 | Project Knowledge | 848 | `08de27c51d3b45ed56b5f4417b8e1073ed1cd4a74acfa248d4831ddb1c057e5e` | 否 | 通过 | 20 |
| `19_用户上传后验证清单_post_upload_validation_checklist.md` | 提供上传后测试问题和合格回答要点 | Project Knowledge | 1188 | `2a277568819a3aacc5a0a107425393657cc6264714f3b1e14cf04a65e8fdbe62` | 否 | 通过 | 21 |
| `20_同步包维护与更新机制_package_maintenance_protocol.md` | 规定后续何时更新机制包和如何更新 | Project Knowledge | 656 | `5815401c586292bcbc9d90346d62a893dfbfc2c23388d8b61ee3301632ce3083` | 否 | 通过 | 22 |
| `project_entry/AGENTS.md` | 根目录 AGENTS 的生成时只读镜像 | Project Knowledge | 4905 | `658501d453e8e35ea269e536f53d88bae4e891bd8f239c3310ef0baa7b5183cf` | 否 | 通过 | 23 |

## 上传建议

- `01_汾酒项目系统提示词_fenjiu_project_system_prompt.md`：复制到 Project Instructions。
- 其他 Markdown：上传为 Project Knowledge。
- 本清单也上传为 Knowledge，方便新聊天框核对读取顺序。
- `project_entry/AGENTS.md` 是生成时镜像；根目录当前 AGENTS 始终是权威版本。

## 禁止上传

不得上传密码、Token、API Key、Cookie、验证码、私人联系方式、实时价格、实时库存、本地配置、媒体文件、缓存或运行输出。
