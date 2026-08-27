# GPT Project 配合机制上传清单

`package_ready_for_manual_upload = true`

`user_uploaded_to_gpt_project_ui = false`

## AGENTS 镜像来源

- `source_repository`: `fthytwerwt-sudo/fenjiu`
- `source_branch`: `main`
- `source_commit`: `8e03083be90f9d7e355787596a35598eb629a5e8`
- `source_file`: `AGENTS.md`
- `source_sha256`: `a8e2adf50c22dff6c45f8ceb68222b16db14bcd17f1fb9e9c9a2cd55971599af`
- `mirror_file`: `project_entry/AGENTS.md`
- `mirror_sha256`: `a8e2adf50c22dff6c45f8ceb68222b16db14bcd17f1fb9e9c9a2cd55971599af`
- `mirror_generated_at_utc`: `2026-08-27T18:29:46Z`

本清单由验证脚本根据实际文件生成。字符数和 SHA-256 以当前目录内容为准。

| 文件路径 | 中文用途 | 上传位置 | 字符数 | SHA-256 | 是否包含动态项目事实 | 敏感扫描 | 推荐读取顺序 |
|---|---|---|---:|---|---|---|---:|
| `00_GPT_Project上传说明_readme.md` | 说明上传方式、状态边界和禁止上传内容 | Project Knowledge | 2338 | `0673b982f5a3b739e101081a7c38f581bc7a2ee53bcd8c84d24886087bfb7770` | 否 | 通过 | 1 |
| `上传清单_manifest.md` | 列出文件、用途、上传位置、字符数和哈希 | Project Knowledge | 5158 | `self-referential-see-validation-report` | 否 | 通过 | 2 |
| `01_汾酒项目系统提示词_fenjiu_project_system_prompt.md` | 复制到 Project Instructions 的汾酒专用系统提示词 | Project Instructions | 4861 | `188b3d29e02f292bbcc87a7014c08070249cf998e2f82d305514c8d4ef435767` | 否 | 通过 | 3 |
| `02_项目身份与长期业务边界_project_identity_stable_scope.md` | 固定汾酒尼泊尔 TikTok 主线和业务边界 | Project Knowledge | 1280 | `f3a35d65bece333bb917bba91cbfa3d657c7155b73349cb2920698dc166c9ee3` | 否 | 通过 | 4 |
| `03_三层架构与事实源边界_three_layer_source_boundary.md` | 区分 GPT Project、GitHub、Codex 和账号记忆 | Project Knowledge | 715 | `bd35ad5e723cd87ed7952f63ba6232d8b763b5241b836c6ac20fdba90340ae78` | 否 | 通过 | 5 |
| `04_P0-P1-P2锚点与抗漂移机制_anchor_priority_anti_drift.md` | 规定来源优先级和抗漂移检查 | Project Knowledge | 1017 | `01f47a9ad1d7f1f037adbf9b117264905233a11fbb30b11470e5149c2afe22b9` | 否 | 通过 | 6 |
| `05_GitHub事实源读取机制_github_fact_source_protocol.md` | 规定何时回读 GitHub 当前事实源 | Project Knowledge | 909 | `221cfac2cf976738207f73933209c42e688de02a7f7deea05963e9b31b0c62cd` | 否 | 通过 | 7 |
| `06_Codex执行落库机制_codex_execution_to_repo_protocol.md` | 规定 Codex 执行、验证、提交和推送 | Project Knowledge | 1006 | `04cbb85b9f47d8180508d3b5df36c6f4e76187ef6b8e57815892da342576f232` | 否 | 通过 | 8 |
| `07_供应链启动与资料缺口判断机制_supplier_readiness_gap_protocol.md` | 判断商品、价格、库存、资质和履约业务闸门缺口 | Project Knowledge | 687 | `b37ce083f2b3bb2b5606730294c9223b847db323aeebdbc956280c5793a2cfef` | 否 | 通过 | 9 |
| `08_TikTok主线与渠道边界_tiktok_channel_scope_protocol.md` | 限定 TikTok 主线和辅助渠道边界 | Project Knowledge | 1019 | `d31df0405904c0673ef7c38738915db939a4fd090af062ef6e0a19c676fdb567` | 否 | 通过 | 10 |
| `09_酒类合规与外部执行闸门_alcohol_compliance_execution_gate.md` | 规定公开发布、投放、收款和履约的前置条件 | Project Knowledge | 553 | `15628d23b101b582e33ce027c3167a7aed75ef77b9c31ad4048ed97e5019e052` | 否 | 通过 | 11 |
| `10_汾酒与海鲜业务线隔离机制_business_line_isolation.md` | 防止海鲜资料污染汾酒主线 | Project Knowledge | 436 | `9a23b14406282e2f21879035546793b18a1ca7db563b0f66314e76104bfc65db` | 否 | 通过 | 12 |
| `11_外部资料保真与执行桥接_external_evidence_bridge.md` | 把外部资料保真转为待验证输入或任务 | Project Knowledge | 626 | `8e55a632217f347853f96751786bcb983c9a6db69e3935479fe9d027497515ae` | 否 | 通过 | 13 |
| `12_方向型输入到可执行任务机制_direction_to_execution_protocol.md` | 把模糊输入转为可执行任务单 | Project Knowledge | 689 | `e0f425dafd67104e89e558e3049a31bc7c0b57951ac56a89b609d71ae78a69cd` | 否 | 通过 | 14 |
| `13_六层需求确认与实现设计闸门_six_layer_requirement_gate.md` | 定义目标、机制、实现设计、流程、标准和反馈六层 | Project Knowledge | 805 | `e332342a5b264775e7edb926c2a699b94c7c87b3910e5d07a7c16126ff485bee` | 否 | 通过 | 15 |
| `14_Codex长期执行单模板_codex_task_template.md` | 提供长期复用的 Codex 下发模板 | Project Knowledge | 1740 | `689984af34ceec59564afc250542f8accf9c6d857183d228950dab2fbaeee9bb` | 否 | 通过 | 16 |
| `15_Codex结果复审与完成度边界_codex_result_review.md` | 复审 Codex 结果和完成度边界 | Project Knowledge | 1012 | `3be34f6d71faacd9bba571bbe4d62ab769ece6ef15dc578f43cc0dea6d41d657` | 否 | 通过 | 17 |
| `16_输出硬规则与中文语义对齐_output_hard_rules.md` | 规定中文状态词和禁止夸大表达 | Project Knowledge | 1212 | `b974ebc2b9e806b21ef70b82be50faae2b80668dc43216ce01d8d59c3159dba2` | 否 | 通过 | 18 |
| `17_Git提交推送与远端验证_git_completion_gate.md` | 规定 commit、push 和 remote readback 闸门 | Project Knowledge | 1279 | `82b1da4b770d4e21fe41ba51edc9206e9d147bbd9261230965d996fc19da3f34` | 否 | 通过 | 19 |
| `18_AGENTS与GPTProject边界_agents_project_boundary.md` | 区分仓库 AGENTS 与 GPT Project 机制包 | Project Knowledge | 848 | `08de27c51d3b45ed56b5f4417b8e1073ed1cd4a74acfa248d4831ddb1c057e5e` | 否 | 通过 | 20 |
| `19_用户上传后验证清单_post_upload_validation_checklist.md` | 提供上传后测试问题和合格回答要点 | Project Knowledge | 1451 | `a458d57dce35fda4d216b48eb6c5df998ffb159e8a0600c78c22b35f799e5209` | 否 | 通过 | 21 |
| `20_同步包维护与更新机制_package_maintenance_protocol.md` | 规定后续何时更新机制包和如何更新 | Project Knowledge | 767 | `020ccf8042da60c0fd5e32fe23218f4f92cbab826a0698b8b823c8dc11e1598f` | 否 | 通过 | 22 |
| `project_entry/AGENTS.md` | 根目录 AGENTS 的生成时只读镜像 | Project Knowledge | 5297 | `a8e2adf50c22dff6c45f8ceb68222b16db14bcd17f1fb9e9c9a2cd55971599af` | 否 | 通过 | 23 |

## 上传建议

- `01_汾酒项目系统提示词_fenjiu_project_system_prompt.md`：复制到 Project Instructions。
- 其他 Markdown：上传为 Project Knowledge。
- 本清单也上传为 Knowledge，方便新聊天框核对读取顺序。
- `project_entry/AGENTS.md` 是生成时镜像；根目录当前 AGENTS 始终是权威版本。

## 禁止上传

不得上传密码、Token、API Key、Cookie、验证码、私人联系方式、实时价格、实时库存、本地配置、媒体文件、缓存或运行输出。
