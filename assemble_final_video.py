#!/usr/bin/env python3
"""Normalize HappyHorse clips and assemble the clean and subtitled 30s films."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


SUBTITLES = (
    (0.0, 3.0, "尼泊尔，一个充满故事的国度。", "Nepal, a land of stories."),
    (3.0, 6.0, "在这里，待客之道，是真诚的心意。", "Hospitality begins with sincerity."),
    (6.0, 9.0, "一杯汾酒，清香纯正。", "A clear aroma, rooted in Chinese craft."),
    (9.0, 15.0, "从朋友聚会，到商务宴请。", "From friendly gatherings to business hospitality."),
    (15.0, 21.0, "不同文化，共同情谊。", "Different cultures. Shared friendship."),
    (21.0, 26.0, "中尼友谊，源远流长。\\N汾酒，敬美好未来。", "China and Nepal, connected by friendship."),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    return parser.parse_args()


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def probe(path: Path) -> dict[str, Any]:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_format",
            "-show_streams",
            "-of",
            "json",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def has_audio(path: Path) -> bool:
    return any(stream.get("codec_type") == "audio" for stream in probe(path)["streams"])


def ass_time(seconds: float) -> str:
    centiseconds = round(seconds * 100)
    hours, remainder = divmod(centiseconds, 360000)
    minutes, remainder = divmod(remainder, 6000)
    whole_seconds, fraction = divmod(remainder, 100)
    return f"{hours}:{minutes:02d}:{whole_seconds:02d}.{fraction:02d}"


def make_ass(path: Path) -> None:
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Main,Noto Sans CJK SC,58,&H00FFFFFF,&H000000FF,&H80000000,&H40000000,0,0,0,0,100,100,0,0,1,3,1,2,80,80,230,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    for start, end, chinese, english in SUBTITLES:
        text = f"{{\\fs58\\b1}}{chinese}\\N{{\\fs34\\b0}}{english}"
        events.append(
            f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Main,,0,0,0,,{text}"
        )
    final_text = (
        "{\\fs86\\b1}汾酒\\N"
        "{\\fs50\\b0}中国清香，世界共享\\N"
        "{\\fs34}Fenjiu · Share the Pure Aroma\\N"
        "{\\fs24}理性饮酒｜仅限达到当地法定饮酒年龄的成年人\\N"
        "{\\fs20}Enjoy responsibly. For adults of legal drinking age only."
    )
    events.append(f"Dialogue: 0,{ass_time(26)},{ass_time(30)},Main,,0,0,180,,{final_text}")
    path.write_text(header + "\n".join(events) + "\n", encoding="utf-8")


def make_narration(path: Path) -> None:
    lines = [
        "汾酒尼泊尔30秒旁白文稿（本版成片默认不含真人旁白）",
        "",
    ]
    for start, end, chinese, english in SUBTITLES:
        lines.extend(
            [
                f"{start:05.1f}-{end:05.1f}",
                f"中文：{chinese}",
                f"英文：{english}",
                "",
            ]
        )
    lines.extend(
        [
            "026.0-030.0",
            "中文：汾酒。中国清香，世界共享。理性饮酒，仅限达到当地法定饮酒年龄的成年人。",
            "英文：Fenjiu. Share the Pure Aroma. Enjoy responsibly. For adults of legal drinking age only.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def draw_centered(
    draw: ImageDraw.ImageDraw,
    text: str,
    y: int,
    font: ImageFont.FreeTypeFont,
    *,
    stroke_width: int = 4,
) -> None:
    draw.text(
        (540, y),
        text,
        font=font,
        fill=(255, 255, 255, 255),
        anchor="mm",
        align="center",
        stroke_width=stroke_width,
        stroke_fill=(0, 0, 0, 210),
    )


def make_subtitle_cards(edit_dir: Path, font_path: Path) -> list[Path]:
    fonts = {
        "zh": ImageFont.truetype(str(font_path), 58),
        "en": ImageFont.truetype(str(font_path), 34),
        "brand": ImageFont.truetype(str(font_path), 86),
        "tagline": ImageFont.truetype(str(font_path), 50),
        "small": ImageFont.truetype(str(font_path), 25),
        "tiny": ImageFont.truetype(str(font_path), 20),
    }
    cards: list[Path] = []
    for index, (_, _, chinese, english) in enumerate(SUBTITLES, start=1):
        image = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw_centered(draw, chinese.replace("\\N", "\n"), 1560, fonts["zh"])
        draw_centered(draw, english, 1630, fonts["en"], stroke_width=3)
        path = edit_dir / f"subtitle_card_{index:02d}.png"
        image.save(path)
        cards.append(path)

    image = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw_centered(draw, "汾酒", 190, fonts["brand"], stroke_width=5)
    draw_centered(draw, "中国清香，世界共享", 285, fonts["tagline"])
    draw_centered(draw, "Fenjiu · Share the Pure Aroma", 350, fonts["en"], stroke_width=3)
    draw.rounded_rectangle(
        (110, 1680, 970, 1835),
        radius=18,
        fill=(0, 0, 0, 150),
    )
    draw_centered(
        draw,
        "理性饮酒｜仅限达到当地法定饮酒年龄的成年人",
        1730,
        fonts["small"],
        stroke_width=2,
    )
    draw_centered(
        draw,
        "Enjoy responsibly. For adults of legal drinking age only.",
        1770,
        fonts["tiny"],
        stroke_width=2,
    )
    path = edit_dir / "subtitle_card_07.png"
    image.save(path)
    cards.append(path)
    return cards


def make_brand_safe_endcard(
    source: Path,
    destination: Path,
    edit_dir: Path,
    source_time_seconds: float = 2.0,
) -> None:
    source_frame = edit_dir / "shot_07_endcard_source.png"
    clean_frame = edit_dir / "shot_07_brand_safe_frame.png"
    run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-ss",
            str(source_time_seconds),
            "-i",
            str(source),
            "-frames:v",
            "1",
            str(source_frame),
        ]
    )
    cleanup_filter = (
        "[0:v]crop=703:1250:188:0,scale=1080:1920:flags=lanczos,"
        "eq=brightness=-0.08:contrast=0.96:saturation=0.88,"
        "format=yuv420p[out]"
    )
    run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(source_frame),
            "-filter_complex",
            cleanup_filter,
            "-map",
            "[out]",
            "-frames:v",
            "1",
            str(clean_frame),
        ]
    )

    zoom_filter = (
        "zoompan=z='min(zoom+0.00019,1.018)':"
        "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        "d=96:s=1080x1920:fps=24,format=yuv420p"
    )
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(clean_frame),
        "-i",
        str(source),
        "-filter_complex",
        f"[0:v]{zoom_filter}[v];[1:a]atrim=duration=4,asetpts=PTS-STARTPTS[a]",
        "-map",
        "[v]",
        "-map",
        "[a]",
        "-t",
        "4",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-ar",
        "48000",
        "-ac",
        "2",
        "-movflags",
        "+faststart",
        str(destination),
    ]
    if not has_audio(source):
        command = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(clean_frame),
            "-f",
            "lavfi",
            "-t",
            "4",
            "-i",
            "anullsrc=channel_layout=stereo:sample_rate=48000",
            "-filter_complex",
            f"[0:v]{zoom_filter}[v]",
            "-map",
            "[v]",
            "-map",
            "1:a",
            "-t",
            "4",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-movflags",
            "+faststart",
            str(destination),
        ]
    run(command)


def make_brand_safe_pour(source: Path, destination: Path) -> None:
    run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(source),
            "-vf",
            "crop=850:1511:0:250,scale=1080:1920:flags=lanczos,setsar=1,format=yuv420p",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-c:a",
            "copy",
            "-movflags",
            "+faststart",
            str(destination),
        ]
    )


def normalize_clip(source: Path, destination: Path, duration: int) -> None:
    video_filter = (
        "scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,"
        "crop=1080:1920,setsar=1,fps=24,"
        f"tpad=stop_mode=clone:stop_duration={duration},"
        f"trim=duration={duration},setpts=PTS-STARTPTS,format=yuv420p"
    )
    fade_out_start = max(0.0, duration - 0.12)
    audio_filter = (
        "aresample=48000,"
        "aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,"
        f"apad=pad_dur={duration},atrim=duration={duration},asetpts=PTS-STARTPTS,"
        f"afade=t=in:st=0:d=0.12,afade=t=out:st={fade_out_start:.2f}:d=0.12,"
        "volume=0.55"
    )
    command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(source)]
    if has_audio(source):
        command.extend(
            [
                "-filter_complex",
                f"[0:v]{video_filter}[v];[0:a]{audio_filter}[a]",
                "-map",
                "[v]",
                "-map",
                "[a]",
            ]
        )
    else:
        command.extend(
            [
                "-f",
                "lavfi",
                "-t",
                str(duration),
                "-i",
                "anullsrc=channel_layout=stereo:sample_rate=48000",
                "-filter_complex",
                f"[0:v]{video_filter}[v];[1:a]{audio_filter}[a]",
                "-map",
                "[v]",
                "-map",
                "[a]",
            ]
        )
    command.extend(
        [
            "-t",
            str(duration),
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-r",
            "24",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-movflags",
            "+faststart",
            str(destination),
        ]
    )
    run(command)


def main() -> int:
    args = parse_args()
    manifest_path = args.manifest.resolve()
    output_dir = manifest_path.parent
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise SystemExit("ffmpeg and ffprobe are required")

    edit_dir = output_dir / "07_edit"
    final_dir = output_dir / "final"
    edit_dir.mkdir(parents=True, exist_ok=True)
    final_dir.mkdir(parents=True, exist_ok=True)

    normalized_paths: list[Path] = []
    for shot in sorted(manifest["shots"], key=lambda item: int(item["number"])):
        number = int(shot["number"])
        source = output_dir / "05_raw_clips" / f"shot_{number:02d}.mp4"
        if not source.is_file():
            raise SystemExit(f"Missing raw clip: {source}")
        postprocess_type = shot.get("postprocess", {}).get("type")
        if postprocess_type == "brand_safe_pour":
            source = output_dir / shot["assembly_source"]
            make_brand_safe_pour(
                output_dir / "05_raw_clips" / f"shot_{number:02d}.mp4",
                source,
            )
            print(f"[OK] brand-safe pour: {source}")
        elif postprocess_type == "brand_safe_endcard":
            source = output_dir / shot["assembly_source"]
            postprocess = shot["postprocess"]
            make_brand_safe_endcard(
                output_dir
                / postprocess.get(
                    "source_clip", f"05_raw_clips/shot_{number:02d}.mp4"
                ),
                source,
                edit_dir,
                float(postprocess.get("source_time_seconds", 2.0)),
            )
            print(f"[OK] brand-safe end card: {source}")
        destination = edit_dir / f"shot_{number:02d}_normalized.mp4"
        normalize_clip(source, destination, int(shot["parameters"]["duration"]))
        normalized_paths.append(destination)
        print(f"[OK] normalized shot {number}")

    concat_path = edit_dir / "concat.txt"
    concat_path.write_text(
        "".join(f"file '{path.as_posix()}'\n" for path in normalized_paths),
        encoding="utf-8",
    )
    ass_path = edit_dir / "subtitles_zh_en.ass"
    make_ass(ass_path)
    make_narration(final_dir / "汾酒尼泊尔_30秒旁白文稿.txt")

    clean_path = final_dir / "汾酒尼泊尔_30秒竖屏干净版_无水印.mp4"
    run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_path),
            "-t",
            "30",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-r",
            "24",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-movflags",
            "+faststart",
            str(clean_path),
        ]
    )

    font_path = Path(__file__).resolve().parent / "qa" / "fonts" / "NotoSansCJKsc-Regular.otf"
    if not font_path.is_file():
        raise SystemExit(f"Subtitle font not found: {font_path}")
    subtitle_cards = make_subtitle_cards(edit_dir, font_path)
    final_path = final_dir / "汾酒尼泊尔_30秒竖屏成片_无水印.mp4"
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(clean_path),
    ]
    for card in subtitle_cards:
        command.extend(["-loop", "1", "-framerate", "24", "-i", str(card)])
    intervals = [(start, end) for start, end, _, _ in SUBTITLES] + [(26.0, 30.0)]
    filters = []
    previous = "[0:v]"
    for index, (start, end) in enumerate(intervals, start=1):
        output_label = f"[v{index}]"
        filters.append(
            f"{previous}[{index}:v]overlay=0:0:enable='between(t,{start},{end})'{output_label}"
        )
        previous = output_label
    command.extend(
        [
            "-filter_complex",
            ";".join(filters),
            "-map",
            previous,
            "-map",
            "0:a?",
            "-t",
            "30",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-r",
            "24",
            "-c:a",
            "copy",
            "-movflags",
            "+faststart",
            str(final_path),
        ]
    )
    run(command)

    report = {
        "clean_video": probe(clean_path),
        "subtitled_video": probe(final_path),
    }
    (output_dir / "06_qc" / "assembled_media_info.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"[OK] clean: {clean_path}")
    print(f"[OK] subtitled: {final_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
