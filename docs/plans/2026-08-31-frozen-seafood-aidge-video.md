# Frozen Seafood Aidge Video Implementation Plan

**Goal:** 用纯合成海鲜素材生成一支流畅的 10 秒竖屏 Aidge 视频并完成技术 QC。

**Architecture:** 先生成可安全公开的冰冻海鲜合成主图，通过已验证的 private OSS signed URL 输入 Aidge。Aidge submit 后立即 checkpoint task ID，轮询完成后通过受控输出 URL 下载并用 FFmpeg/FFprobe 验证。

**Tech Stack:** `imagegen`, `oss2`, `alibabacloud_aidge20260428`, `videoctl`, `ffmpeg`, `ffprobe`

---

### Task 1: 合成冰冻海鲜主图

**Files:**
- Create locally: `inputs/video_orchestrator/frozen_seafood_premium.png`

1. 生成 9:16 高端冰冻海鲜棚拍图。
2. 确认无商标、价格、包装文字或真实客户资料。
3. 将本地图片保留在 ignored input 目录。

### Task 2: Aidge 10 秒生成

**Files:**
- Local checkpoint: `outputs/video_orchestrator/aidge_frozen_seafood_state.json`
- Local output: `outputs/video_orchestrator/aidge_frozen_seafood_10s.mp4`

1. 用 OSS bridge 上传合成图并获取 30–60 分钟 signed GET URL。
2. 构建 10 秒、720P、9:16 请求，title 不超过 60 字符。
3. 在 submit 后立即保存 task ID checkpoint。
4. 只轮询该 task；如下载失败，用 checkpoint 恢复，不重新生成。

### Task 3: 媒体 QC 与证据

1. 运行 `video-metadata-probe` 脚本。
2. 运行 `ffmpeg -v error -i <output> -f null -`。
3. 记录 duration、resolution、fps、codec、audio、file size 和 SHA-256。
4. 确认 input/output 媒体均被 Git ignore。
5. 只提交设计/执行记录和代码状态，不提交媒体。
