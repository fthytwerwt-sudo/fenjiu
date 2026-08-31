"""Local capability-first CLI for video orchestration."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Sequence, TextIO

from core.application.video_orchestrator import (
    CapabilityRegistry,
    ErrorCode,
    OrchestratorContractError,
    OrchestratorRequest,
    PresetName,
    ProviderAdapterError,
    TaskType,
    VideoOrchestrator,
    build_preset_plan,
)
from core.application.video_orchestrator.contracts import safe_ref
from core.application.video_orchestrator.security import resolve_output_path
from adapters.video.runtime import VideoRuntimeAdapter
from adapters.video.providers.common import download_binary
from workflows.video_pipeline import VideoPipelineRunner


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="videoctl", description="Capability-first Video Orchestrator")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor")
    sub.add_parser("capabilities")

    probe_aidge = sub.add_parser("probe-aidge")
    probe_aidge.add_argument(
        "--image",
        default="https://help-static-aliyun-doc.aliyuncs.com/file-manage-files/zh-CN/20260713/dtnctw/ad-1.png",
    )
    probe_aidge.add_argument("--title", default="Synthetic Aidge SDK probe")
    probe_aidge.add_argument("--output", default="outputs/video_orchestrator/aidge_probe.mp4")
    _add_execution_flags(probe_aidge)

    generate = sub.add_parser("generate")
    generate.add_argument("--task", required=True, choices=[
        TaskType.PRODUCT_AD.value,
        TaskType.STORY_VIDEO.value,
        TaskType.FAST_STORY_VIDEO.value,
        TaskType.SHORT_PRODUCT_SCENE.value,
    ])
    _add_generation_arguments(generate)

    product_ad = sub.add_parser("product_ad")
    _add_generation_arguments(product_ad)
    story_video = sub.add_parser("story_video")
    _add_generation_arguments(story_video)

    voice = sub.add_parser("voice")
    voice.add_argument("--language", required=True)
    voice.add_argument("--text", required=True)
    voice.add_argument("--output")
    _add_execution_flags(voice)

    translate = sub.add_parser("translate")
    translate.add_argument("--source-language", default="zh")
    translate.add_argument("--target-language", default="ne", choices=["ne", "ne-np", "nepali"])
    translate.add_argument("--text", required=True)
    _add_execution_flags(translate)

    asr = sub.add_parser("asr")
    asr.add_argument("--source", required=True)
    asr.add_argument("--approve-media-upload", action="store_true")
    _add_execution_flags(asr)

    lip_sync = sub.add_parser("lip-sync")
    lip_sync.add_argument("--video", required=True)
    lip_sync.add_argument("--audio", required=True)
    lip_sync.add_argument("--reference-image")
    lip_sync.add_argument("--output")
    lip_sync.add_argument("--approve-media-upload", action="store_true")
    _add_execution_flags(lip_sync)

    assembly = sub.add_parser("final-assembly")
    assembly.add_argument("--video", required=True)
    assembly.add_argument("--audio")
    assembly.add_argument("--subtitle")
    assembly.add_argument("--output", required=True)
    assembly.add_argument("--execute", action="store_true")

    pipeline = sub.add_parser("pipeline")
    pipeline.add_argument("--preset", required=True, choices=[item.value for item in PresetName])
    pipeline.add_argument("--language", default="ne")
    pipeline.add_argument("--talking-person", action="store_true")
    pipeline.add_argument("--image", action="append", default=[])
    pipeline.add_argument("--title", default="")
    pipeline.add_argument("--prompt", default="")
    pipeline.add_argument("--script", default="")
    pipeline.add_argument("--source-video")
    pipeline.add_argument("--reference-image")
    pipeline.add_argument("--approve-media-upload", action="store_true")
    pipeline.add_argument("--approve-fallback", action="store_true")
    pipeline.add_argument("--approved-provider", action="append", default=[])
    pipeline.add_argument("--step-cost-cny", action="append", default=[])
    _add_execution_flags(pipeline)
    return parser


def _add_generation_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--image", action="append", default=[])
    parser.add_argument("--reference-video", action="append", default=[])
    parser.add_argument("--title", default="")
    parser.add_argument("--prompt", default="")
    parser.add_argument("--duration", type=int)
    parser.add_argument("--ratio")
    parser.add_argument("--quality")
    parser.add_argument("--output")
    parser.add_argument("--speed-priority", action="store_true")
    parser.add_argument("--approve-media-upload", action="store_true")
    parser.add_argument("--approve-fallback", action="store_true")
    parser.add_argument("--approved-provider", action="append", default=[])
    parser.add_argument("--fallback-estimated-cost-cny", type=float)
    _add_execution_flags(parser)


def _add_execution_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--approve-cost", action="store_true")
    parser.add_argument("--estimated-cost-cny", type=float)
    parser.add_argument("--max-cost-cny", type=float)


def main(argv: Sequence[str] | None = None, *, stdout: TextIO | None = None) -> int:
    stream = stdout or sys.stdout
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    runtime = VideoRuntimeAdapter()
    orchestrator = VideoOrchestrator(runtime=runtime)
    try:
        if args.command == "doctor":
            result = orchestrator.doctor()
        elif args.command == "capabilities":
            result = {
                "schema_version": "video_orchestrator.capabilities.cli.v1",
                "capabilities": CapabilityRegistry.default().safe_summary(),
            }
        elif args.command == "probe-aidge":
            if not args.execute:
                result = {
                    "provider": "aidge_video_generation",
                    "execution": "PLAN_ONLY",
                    "request": {
                        "image_count": 1,
                        "title_present": True,
                        "duration": 5,
                        "ratio": "9:16",
                        "quality": "720p",
                        "estimated_max_cost_cny": 7.0,
                    },
                    "doctor": runtime.aidge.doctor().safe_summary(),
                }
            else:
                if not args.approve_cost:
                    raise ProviderAdapterError(
                        ErrorCode.COST_BLOCKED,
                        "explicit Aidge probe cost approval required",
                        provider="aidge_video_generation",
                    )
                if not isinstance(args.max_cost_cny, (int, float)) or args.max_cost_cny < 7.0:
                    raise ProviderAdapterError(
                        ErrorCode.COST_BLOCKED,
                        "Aidge probe requires a maximum cost of at least CNY 7.0",
                        provider="aidge_video_generation",
                    )
                doctor = runtime.aidge.doctor()
                if not doctor.available:
                    raise ProviderAdapterError(
                        doctor.error_code or ErrorCode.PROVIDER_NOT_ENABLED,
                        doctor.probe_status,
                        provider="aidge_video_generation",
                    )
                request_map = runtime.aidge.build_request(
                    images=(args.image,),
                    title=args.title,
                    duration=5,
                    ratio="9:16",
                    quality="720p",
                )
                submitted = runtime.aidge.submit(request_map)
                task_id = submitted.task_id or ""
                _write_aidge_probe_state(task_id=task_id, status="SUBMITTED")
                completed = runtime.aidge.wait(task_id)
                _write_aidge_probe_state(
                    task_id=task_id,
                    status=completed.status,
                    output_ref=safe_ref(completed.output_url),
                )
                output = resolve_output_path(args.output, provider="aidge_video_generation")
                download_binary(completed.output_url or "", output)
                media_qc = runtime.ffmpeg.validate_media(output)
                result = {
                    "provider": "aidge_video_generation",
                    "execution": "TECH_QC_PASSED",
                    "result": completed.safe_summary(),
                    "output_ref": safe_ref(str(output)),
                    "media_qc": media_qc,
                    "human_review_required": True,
                }
        elif args.command == "pipeline":
            result = VideoPipelineRunner(orchestrator).run(
                PresetName(args.preset),
                execute=args.execute,
                cost_approved=args.approve_cost,
                media_upload_approved=args.approve_media_upload,
                product_images=tuple(args.image),
                product_title=args.title,
                prompt=args.prompt,
                script=args.script,
                source_video=args.source_video,
                reference_image=args.reference_image,
                language=args.language,
                has_talking_person=args.talking_person,
                fallback_approved=args.approve_fallback,
                approved_providers=tuple(args.approved_provider),
                max_cost_cny=args.max_cost_cny,
                step_costs=_parse_step_costs(args.step_cost_cny),
            )
        else:
            request = _request_from_args(args)
            result = orchestrator.execute(request)
        json.dump(result, stream, ensure_ascii=False, sort_keys=True)
        stream.write("\n")
        return 0
    except (ProviderAdapterError, OrchestratorContractError, ValueError) as exc:
        if isinstance(exc, ProviderAdapterError):
            error = exc.safe_summary()
        else:
            error = {"code": ErrorCode.INVALID_INPUT.value, "message": str(exc)[:300]}
        json.dump({"error": error}, stream, ensure_ascii=False, sort_keys=True)
        stream.write("\n")
        return 2


def _request_from_args(args: argparse.Namespace) -> OrchestratorRequest:
    if args.command == "voice":
        metadata = {
            "estimated_provider_cost_cny": args.estimated_cost_cny,
            "max_cost_cny": args.max_cost_cny,
        }
        if args.output:
            metadata["output_path"] = args.output
        return OrchestratorRequest(
            task=TaskType.NEPALI_VOICE,
            language=args.language,
            script=args.text,
            execute=args.execute,
            cost_approved=args.approve_cost,
            metadata=metadata,
        )
    if args.command == "translate":
        return OrchestratorRequest(
            task=TaskType.TRANSLATE_NEPALI,
            language=args.target_language,
            script=args.text,
            execute=args.execute,
            cost_approved=args.approve_cost,
            metadata={
                "return_text": True,
                "source_language": args.source_language,
                "estimated_provider_cost_cny": args.estimated_cost_cny,
                "max_cost_cny": args.max_cost_cny,
            },
        )
    if args.command == "asr":
        source_is_audio = args.source.lower().endswith(
            (".wav", ".mp3", ".aac", ".m4a", ".flac", ".ogg", ".opus")
        )
        return OrchestratorRequest(
            task=TaskType.SOURCE_ASR,
            source_audio=args.source if source_is_audio else None,
            source_video=None if source_is_audio else args.source,
            execute=args.execute,
            cost_approved=args.approve_cost,
            metadata={
                "return_text": True,
                "media_upload_approved": args.approve_media_upload,
                "estimated_provider_cost_cny": args.estimated_cost_cny,
                "max_cost_cny": args.max_cost_cny,
            },
        )
    if args.command == "lip-sync":
        metadata = {
            "media_upload_approved": args.approve_media_upload,
            "estimated_provider_cost_cny": args.estimated_cost_cny,
            "max_cost_cny": args.max_cost_cny,
        }
        if args.output:
            metadata["output_path"] = args.output
        return OrchestratorRequest(
            task=TaskType.LIP_SYNC,
            source_video=args.video,
            source_audio=args.audio,
            reference_image=args.reference_image,
            execute=args.execute,
            cost_approved=args.approve_cost,
            metadata=metadata,
        )
    if args.command == "final-assembly":
        metadata = {"output_path": args.output}
        if args.subtitle:
            metadata["subtitle_path"] = args.subtitle
        return OrchestratorRequest(
            task=TaskType.FINAL_ASSEMBLY,
            source_video=args.video,
            source_audio=args.audio,
            execute=args.execute,
            cost_approved=True,
            metadata=metadata,
        )
    if args.command == "product_ad":
        task = TaskType.PRODUCT_AD
    elif args.command == "story_video":
        task = TaskType.STORY_VIDEO
    else:
        task = TaskType(args.task)
    metadata = {"output_path": args.output} if args.output else {}
    metadata.update(
        {
            "media_upload_approved": args.approve_media_upload,
            "fallback_approved": args.approve_fallback,
            "approved_providers": tuple(args.approved_provider),
            "max_cost_cny": args.max_cost_cny,
            "estimated_provider_cost_cny": args.estimated_cost_cny,
            "fallback_estimated_cost_cny": args.fallback_estimated_cost_cny,
        }
    )
    return OrchestratorRequest(
        task=task,
        product_images=tuple(args.image),
        product_title=args.title,
        prompt=args.prompt,
        reference_images=tuple(args.image),
        reference_videos=tuple(args.reference_video),
        duration=args.duration,
        ratio=args.ratio,
        quality=args.quality,
        speed_priority=args.speed_priority,
        execute=args.execute,
        cost_approved=args.approve_cost,
        metadata=metadata,
    )


def _parse_step_costs(values: Sequence[str]) -> dict[str, float]:
    result: dict[str, float] = {}
    for value in values:
        if "=" not in value:
            raise ValueError("step cost must use capability=amount")
        capability, amount_text = value.split("=", 1)
        amount = float(amount_text)
        if not capability or amount <= 0:
            raise ValueError("step cost must use a positive amount")
        result[capability] = amount
    return result


def _write_aidge_probe_state(
    *,
    task_id: str,
    status: str,
    output_ref: str | None = None,
) -> None:
    state_path = resolve_output_path("aidge_probe_state.json", provider="aidge_video_generation")
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps(
            {
                "schema_version": "video_orchestrator.aidge_probe_state.v1",
                "provider": "aidge_video_generation",
                "task_id": task_id,
                "status": status,
                "output_ref": output_ref,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    try:
        os.chmod(state_path, 0o600)
    except OSError:
        pass


if __name__ == "__main__":
    raise SystemExit(main())
