"""Runtime provider adapters for the Video Orchestrator."""

from adapters.video.providers.aidge import AidgeVideoGenerationAdapter
from adapters.video.providers.dashscope import (
    HappyHorseVideoAdapter,
    MiniMaxSpeechAdapter,
    ParaformerAsrAdapter,
    QwenMtAdapter,
    VideoRetalkAdapter,
    Wan3VideoAdapter,
)
from adapters.video.providers.ffmpeg import FfmpegAssemblyAdapter
from adapters.video.providers.oss_bridge import BridgedAsset, OssAssetBridge

__all__ = [
    "AidgeVideoGenerationAdapter",
    "BridgedAsset",
    "FfmpegAssemblyAdapter",
    "HappyHorseVideoAdapter",
    "MiniMaxSpeechAdapter",
    "OssAssetBridge",
    "ParaformerAsrAdapter",
    "QwenMtAdapter",
    "VideoRetalkAdapter",
    "Wan3VideoAdapter",
]
