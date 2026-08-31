# Video Orchestrator｜视频总控调度层

## 定位

Video Orchestrator 让上层按“要做什么”选择能力，不直接依赖 Model ID。它是本地 application layer，不改变 Sales-First 业务状态，也不授权发布、投放、报价或外发。

所有真实云调用都要求：

```text
--execute --approve-cost --max-cost-cny <总上限>
```

对当前无法从公开刊例自动计算的 Provider，还必须提供 `--estimated-cost-cny`。Pipeline 会在首次 Provider 调用前检查各步估算和累计上限；没有明确费用数字时使用 `COST_BLOCKED`停止。

默认命令只返回脱敏计划。生成后状态固定进入 `HUMAN_REVIEW_REQUIRED`，不会自动发布。

## 实现设计层

```yaml
primary_route:
  product_ad: Aidge VideoGeneration
  story_video: Wan3.0
  fast_story_video: Wan3.0 Prime
  short_product_scene: HappyHorse 1.1
  nepali_voice: MiniMax/speech-2.8-hd
  translate_nepali: Qwen-MT
  source_asr: Paraformer
  lip_sync: VideoRetalk
  final_assembly: FFmpeg
fallback_route:
  product_ad: Wan3.0
capability_status:
  minimax_nepali: PROBE_PASSED
  videoretalk_paraformer_happyhorse: PREVIOUSLY_TESTED
  ffmpeg: CURRENTLY_AVAILABLE
  wan3_qwen_mt: PROBE_REQUIRED
  aidge: BLOCKED_AIDGE_CREDENTIALS_ABSENT
probe_required: true
allowed_codex_autonomy: [request_building, doctor, one_cost_approved_probe, local_qc]
forbidden_codex_guessing: [product_facts, asset_rights, price, provider_success, permission, cost]
required_inputs: [task_specific_inputs, credential_presence, explicit_cost_approval]
required_outputs: [safe_plan_or_result, technical_qc, human_review_handoff]
execution_entrypoints: [videoctl]
validation_commands: [unit_tests, architecture_tests, compileall, videoctl_doctor]
blocked_if_missing: [credential, permission, provider_enablement, asset_access, cost_approval]
```

## 能力与状态

| Capability | Primary | Status | Fallback |
|---|---|---|---|
| `product_video` | Aidge `VideoGeneration` | `BLOCKED_AIDGE_OUTPUT_DOWNLOAD_URL_POLICY` | Wan3.0 |
| `story_video` | `wan3.0-video` | `PROBE_REQUIRED` | — |
| `fast_story_video` | `wan3.0-video-prime` | `PROBE_REQUIRED` | Wan3.0 |
| `short_reference_video` | HappyHorse 1.1 t2v/i2v/r2v | `PREVIOUSLY_TESTED` | Wan3.0 |
| `nepali_tts` | `MiniMax/speech-2.8-hd` | `PROBE_PASSED` | — |
| `fast_nepali_tts` | `MiniMax/speech-2.8-turbo` | `PROBE_REQUIRED` | — |
| `translate_nepali` | `qwen-mt-flash` | `PROBE_REQUIRED` | — |
| `source_asr` | `paraformer-v1` | `PREVIOUSLY_TESTED` | — |
| `lip_sync` | VideoRetalk | `PREVIOUSLY_TESTED` | — |
| `final_assembly` | FFmpeg/FFprobe | `CURRENTLY_AVAILABLE` | — |

Machine-readable registry：`core/application/video_orchestrator/capabilities.json`。

## Aidge 状态

- API：`Aidge/2026-04-28:VideoGeneration`，不是 DashScope Model ID。
- 权限：`aidge:VideoGeneration`。
- 官方 SDK：`alibabacloud_aidge20260428==5.3.1`，SDK import 与 request model 已验证。
- 输入：1–6 个公网图片 URL、商品标题；当前输出 gate 为 5–15 秒、9:16、720p/1080p。
- 费用：720p 为人民币 1.4 元/秒；最小 5 秒 probe 的刊例价上限为人民币 7 元。当前公开免费额度表未列出电商视频生成。
- 当前状态：用户已授权并完成 1 次 5 秒、720p、9:16 物理 probe。Aidge 接受任务，轮询进入 completed 且返回输出 URL，因此 credentials、`aidge:VideoGeneration` 权限和上游生成均已验证。但 Provider 输出 URL 不满足本地 credential-free HTTPS policy，下载在写入 MP4 前被拒绝；本地无输出，未做 ffprobe/解码/内容验收。当前为 `BLOCKED_AIDGE_OUTPUT_DOWNLOAD_URL_POLICY`。
- Asset Bridge：只使用 private OSS object + 30–60 分钟 signed GET URL；绝不自动改 public bucket。
- 本地商品图只允许来自 `inputs/video_orchestrator/`，并要求 `--approve-media-upload`；输出只允许写入 `outputs/video_orchestrator/`。

## 使用命令

```bash
./videoctl doctor
./videoctl capabilities
./videoctl product_ad --image https://example.com/product.png --title '商品标题'
./videoctl story_video --prompt '故事简述'
./videoctl voice --language ne --text 'नमस्कार'
./videoctl translate --source-language zh --target-language ne --text '中文口播'
./videoctl asr --source https://example.com/source.wav
./videoctl lip-sync --video https://example.com/source.mp4 --audio https://example.com/nepali.wav
./videoctl final-assembly --video inputs/video_orchestrator/source.mp4 --output final.mp4
./videoctl pipeline --preset nepali_talking_video
```

Aidge 最小 probe 先看计划和费用：

```bash
./videoctl probe-aidge
```

只有用户明确同意费用且本地凭据已配置时才执行：

```bash
./videoctl probe-aidge --execute --approve-cost --max-cost-cny 7
```

## Presets

- `nepali_product_ad`：Aidge → MiniMax Nepali → 可选 VideoRetalk → FFmpeg。
- `nepali_talking_video`：Paraformer → Qwen-MT → MiniMax → VideoRetalk → FFmpeg。
- `story_video`：Wan3.0 → 可选 MiniMax Nepali → FFmpeg。

## 边界

- Provider credential、signed URL、raw payload、真实本地路径不会进入 safe summary 或 Git。
- Provider endpoint override 只允许 HTTPS 的阿里官方 `aliyuncs.com` 主机；远程 URL 的 DNS 结果若指向本机、内网或保留地址将被拒绝，下载结果也只接受阿里官方输出主机。
- `product_ad` 只有在 Aidge unavailable/permission/unsupported input 时才允许走 Wan3 fallback；fallback 还必须单独提供 `--approve-fallback --approved-provider wan3_video --fallback-estimated-cost-cny ... --max-cost-cny ...`。主路由刊例估算，主路加 fallback 必须不超过上限。限流和质量不佳不会自动切换或重试。
- 旧 P07 `VideoPort` 继续保持 synthetic-only、`external_call_count=0`；真实 runtime 使用独立 `VideoRuntimePort`，不破坏既有 no-publish 合同。
- Provider 输出只能到 `GENERATED → TECH_QC_PASSED → HUMAN_REVIEW_REQUIRED`。人工批准前不得发布或发送。
- 本地 bridge 支持图片 `jpg/jpeg/png/webp/bmp`，视频 `mp4/mov/avi/webm`，音频 `wav/mp3/aac/m4a/flac/ogg/opus`；扩展名和文件签名都必须通过。

本地完整链必须显式授权本地媒体上传和费用，例如：

```bash
./videoctl pipeline \
  --preset nepali_talking_video \
  --source-video inputs/video_orchestrator/source.mp4 \
  --execute --approve-cost --approve-media-upload \
  --max-cost-cny 10 \
  --step-cost-cny source_asr=1 \
  --step-cost-cny translate_nepali=1 \
  --step-cost-cny nepali_tts=3 \
  --step-cost-cny lip_sync=5
```

上述金额只是 CLI 格式示例，不是当前 Provider 报价或成本承诺；正式执行前要以当时账号与官方价格填写。
