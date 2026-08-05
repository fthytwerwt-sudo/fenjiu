# 内容与视频生产链服务化计划

> **状态：PLANNED。** Phase 7 复用现有 HappyHorse / DashScope / FFmpeg 工具链的行为，不重写、不移动、不在本轮调用真实模型；任何内容在平台和酒类边界未确认时仅为内部草稿/样片。

## 1. 标准流程

```text
content task → lock approved product facts + asset rights → topic/script → forbidden-expression/fact check
→ storyboard/prompt → approval → video provider adapter → download/resume/retry → subtitles/voice/FFmpeg
→ automated QC → human approval → internal export
```

`content_task` 必锁定业务线、brief、fact version set、素材 rights version、policy version、目标 locale 和 data origin。未确认商品时可使用明确 synthetic 的通用内部演示 brief；必须水印/metadata 标明 `synthetic`，不能模拟真实 SKU、价格、库存、授权或客户评价。

## 2. legacy 复用清单与边界

| 现有文件 | 可复用能力 | 新包装边界 |
|---|---|---|
| `generate_happyhorse_shots.py` | 提交、轮询、断点续跑、下载、质量重试、manifest | `HappyHorseLegacyPort` 使用 manifest reference 和 idempotency key；不复制实现、密钥或请求体。 |
| `generate_happyhorse_video_edit_once.py` | 单批 non-retry 编辑任务 | adapter 明确 `no_auto_retry`，失败进入人工 queue。 |
| `prepare_video_assets.py`、`assemble_final_video.py` | 素材准备、FFmpeg 合成 | `PostProcessPort` 只读输入，输出新 artifact reference，不覆盖历史。 |
| `build_video_execution_report.py` | 执行结果汇总 | 作为 QC/报告参考，业务真值不从 report 倒灌。 |

## 3. manifest、状态与模型替换

video manifest 包含 `video_task_id`、fact/policy/asset versions、provider adapter/model alias、prompt hash、input asset hashes、task ID、attempt、cost approval、QC result、artifact hash/location 和 human decision。状态：`draft → fact_checked → approval_pending → submitted → running → downloaded → qc_pending → needs_review/approved/rejected/failed`。provider-specific ID 仅在 adapter metadata；替换模型需通过同一 `VideoPort` fake/contract，不能改变 content truth 或 approval 逻辑。

提交前 fact checker 失败关闭：未批准 SKU/规格/价格/库存、素材权利不明、禁用表达、健康功效、未成年人、文化优越、平台边界未验证、fixture 试图进入公开发布。AI 画面和真实商品画面都必须有 `asset_origin=ai_generated|supplier_authorized|unknown`；`unknown` 不能导出。

## 4. QC、审批与回退

自动 QC 包含解码、时长、纵横比、音画/字幕存在、素材 hash、fact/policy recheck 和水印/来源标识；它不替代人审。人工审批后仅可 internal export；publish adapter 直到 Phase 9 不存在/关闭。provider 失败、额度不足、事实过期、QC 不过或人工拒绝时停止下游、保留 manifest/QC/audit，必要时创建新修订；不自动换模型、重投成本或覆盖原输出。
