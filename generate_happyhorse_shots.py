#!/usr/bin/env python3
"""Submit, resume, poll, and download HappyHorse video-generation tasks."""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import ssl
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any


DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com"
CREATE_PATH = "/api/v1/services/aigc/video-generation/video-synthesis"
ALLOWED_MODELS = {
    "happyhorse-1.1-t2v",
    "happyhorse-1.1-i2v",
    "happyhorse-1.1-r2v",
}
TERMINAL_STATUSES = {"SUCCEEDED", "FAILED", "CANCELED", "UNKNOWN"}
MANIFEST_LOCK = threading.Lock()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--shots", help="Comma-separated shot numbers; defaults to all")
    parser.add_argument("--parallel", type=int, default=1)
    parser.add_argument("--poll-interval", type=int, default=15)
    parser.add_argument("--timeout", type=int, default=1200)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="Archive a terminal failed task and submit one corrected attempt",
    )
    parser.add_argument(
        "--regenerate",
        action="store_true",
        help="Archive one successful shot and submit its single quality retry",
    )
    parser.add_argument(
        "--max-quality-retries",
        type=int,
        default=1,
        help="Maximum archived quality retry attempts allowed for --regenerate",
    )
    return parser.parse_args()


def load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key] = value
    return values


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def data_uri(path: Path) -> str:
    mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def resolve_media(manifest_dir: Path, item: dict[str, str]) -> tuple[Path, str]:
    path = Path(item["path"])
    if not path.is_absolute():
        path = manifest_dir / path
    return path.resolve(), item["type"]


def validate_shot(manifest_dir: Path, shot: dict[str, Any]) -> None:
    model = shot.get("model")
    if model not in ALLOWED_MODELS:
        raise ValueError(f"shot {shot.get('number')}: unsupported model {model}")
    parameters = shot.get("parameters", {})
    if parameters.get("resolution") != "1080P":
        raise ValueError(f"shot {shot.get('number')}: resolution must be 1080P")
    if parameters.get("watermark") is not False:
        raise ValueError(f"shot {shot.get('number')}: watermark must be false")
    duration = parameters.get("duration")
    if not isinstance(duration, int) or not 3 <= duration <= 15:
        raise ValueError(f"shot {shot.get('number')}: duration must be 3-15 seconds")
    if model.endswith(("-t2v", "-r2v")) and parameters.get("ratio") != "9:16":
        raise ValueError(f"shot {shot.get('number')}: ratio must be 9:16")
    media = shot.get("media", [])
    if model.endswith("-t2v") and media:
        raise ValueError(f"shot {shot.get('number')}: t2v must not include media")
    if model.endswith(("-i2v", "-r2v")) and not media:
        raise ValueError(f"shot {shot.get('number')}: media is required")
    for item in media:
        path, media_type = resolve_media(manifest_dir, item)
        if not path.is_file():
            raise ValueError(f"shot {shot.get('number')}: media not found: {path}")
        if path.stat().st_size > 20 * 1024 * 1024:
            raise ValueError(f"shot {shot.get('number')}: media exceeds 20 MB: {path}")
        if model.endswith("-i2v") and media_type != "first_frame":
            raise ValueError(f"shot {shot.get('number')}: i2v media must be first_frame")
        if model.endswith("-r2v") and media_type != "reference_image":
            raise ValueError(f"shot {shot.get('number')}: r2v media must be reference_image")


def build_payload(manifest_dir: Path, shot: dict[str, Any]) -> dict[str, Any]:
    input_data: dict[str, Any] = {"prompt": shot["prompt"]}
    if shot.get("media"):
        input_data["media"] = []
        for item in shot["media"]:
            path, media_type = resolve_media(manifest_dir, item)
            input_data["media"].append({"type": media_type, "url": data_uri(path)})
    parameters = dict(shot["parameters"])
    if shot["model"].endswith("-i2v"):
        parameters.pop("ratio", None)
    return {"model": shot["model"], "input": input_data, "parameters": parameters}


def safe_request_record(manifest_dir: Path, shot: dict[str, Any]) -> dict[str, Any]:
    return {
        "model": shot["model"],
        "input": {
            "prompt": shot["prompt"],
            "media": [
                {
                    "type": item["type"],
                    "path": str(resolve_media(manifest_dir, item)[0]),
                }
                for item in shot.get("media", [])
            ],
        },
        "parameters": shot["parameters"],
    }


def request_json(
    url: str,
    api_key: str,
    *,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "fenjiu-nepal-video/1.0",
    }
    if method == "POST":
        headers["X-DashScope-Async"] = "enable"
    for attempt in range(3):
        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(
                request,
                timeout=90,
                context=ssl.create_default_context(),
            ) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            try:
                details = json.loads(body)
            except json.JSONDecodeError:
                details = {"code": f"HTTP_{exc.code}", "message": body[:2000]}
            raise RuntimeError(json.dumps(details, ensure_ascii=False)) from exc
        except (urllib.error.URLError, ConnectionResetError, TimeoutError):
            if attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))
    raise RuntimeError("unreachable network retry state")


def download_file(url: str, destination: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "fenjiu-nepal-video/1.0"})
    temporary = destination.with_suffix(destination.suffix + ".part")
    with urllib.request.urlopen(request, timeout=180) as response, temporary.open("wb") as output:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            output.write(chunk)
    if temporary.stat().st_size == 0:
        temporary.unlink(missing_ok=True)
        raise RuntimeError("downloaded file is empty")
    temporary.replace(destination)


def set_manifest_status(
    manifest_path: Path,
    shot_number: int,
    status: str,
    task_id: str | None = None,
    output_file: str | None = None,
) -> None:
    with MANIFEST_LOCK:
        manifest = read_json(manifest_path)
        for item in manifest["shots"]:
            if int(item["number"]) == shot_number:
                item["status"] = status
                if task_id:
                    item["task_id"] = task_id
                if output_file:
                    item["output_file"] = output_file
                break
        write_json(manifest_path, manifest)


def reset_manifest_status(manifest_path: Path, shot_number: int, status: str) -> None:
    with MANIFEST_LOCK:
        manifest = read_json(manifest_path)
        for item in manifest["shots"]:
            if int(item["number"]) == shot_number:
                item["status"] = status
                item.pop("task_id", None)
                item.pop("output_file", None)
                break
        write_json(manifest_path, manifest)


def handle_shot(
    manifest_path: Path,
    shot: dict[str, Any],
    api_key: str,
    base_url: str,
    poll_interval: int,
    timeout: int,
    dry_run: bool,
    retry_failed: bool,
    regenerate: bool,
    max_quality_retries: int,
) -> dict[str, Any]:
    manifest_dir = manifest_path.parent
    shot_number = int(shot["number"])
    shot_label = f"shot_{shot_number:02d}"
    task_dir = manifest_dir / "04_tasks" / shot_label
    task_state_path = task_dir / "state.json"
    response_path = task_dir / "latest_response.json"
    output_path = manifest_dir / "05_raw_clips" / f"{shot_label}.mp4"
    request_record_path = task_dir / "request.json"

    validate_shot(manifest_dir, shot)
    if dry_run:
        return {"shot": shot_number, "status": "DRY_RUN_OK", "model": shot["model"]}

    state = read_json(task_state_path)
    response = read_json(response_path)
    if regenerate:
        if not output_path.is_file() or state.get("task_status") != "SUCCEEDED":
            raise RuntimeError(f"shot {shot_number}: only a downloaded successful shot can be regenerated")
        attempts_dir = task_dir / "quality_attempts"
        attempt_number = len(list(attempts_dir.glob("attempt_*"))) + 1 if attempts_dir.exists() else 1
        if attempt_number > max_quality_retries:
            raise RuntimeError(f"shot {shot_number}: quality retry limit reached")
        archive_dir = attempts_dir / f"attempt_{attempt_number:02d}"
        archive_dir.mkdir(parents=True, exist_ok=False)
        for path in (request_record_path, task_state_path, response_path, output_path):
            if path.exists():
                path.replace(archive_dir / path.name)
        state = {}
        response = {}
        reset_manifest_status(manifest_path, shot_number, "QUALITY_RETRY_PENDING")
        print(f"[ARCHIVED] shot {shot_number}: quality attempt {attempt_number}", flush=True)
    elif output_path.is_file() and output_path.stat().st_size > 0:
        set_manifest_status(manifest_path, shot_number, "SUCCEEDED", output_file=str(output_path))
        return {"shot": shot_number, "status": "ALREADY_DOWNLOADED", "file": str(output_path)}

    previous_status = str(state.get("task_status", ""))
    if state.get("task_id") and previous_status in {"FAILED", "CANCELED", "UNKNOWN"} and retry_failed:
        attempts_dir = task_dir / "attempts"
        attempt_number = len(list(attempts_dir.glob("attempt_*"))) + 1 if attempts_dir.exists() else 1
        if attempt_number > 2:
            raise RuntimeError(f"shot {shot_number}: technical retry limit reached")
        archive_dir = attempts_dir / f"attempt_{attempt_number:02d}"
        archive_dir.mkdir(parents=True, exist_ok=False)
        for path in (request_record_path, task_state_path, response_path):
            if path.exists():
                path.replace(archive_dir / path.name)
        state = {}
        response = {}
        reset_manifest_status(manifest_path, shot_number, "RETRY_PENDING")
        print(f"[ARCHIVED] shot {shot_number}: failed attempt {attempt_number}", flush=True)

    write_json(request_record_path, safe_request_record(manifest_dir, shot))

    task_id = state.get("task_id")
    if not task_id:
        payload = build_payload(manifest_dir, shot)
        response = request_json(
            base_url + CREATE_PATH,
            api_key,
            method="POST",
            payload=payload,
        )
        write_json(response_path, response)
        output = response.get("output", {})
        task_id = output.get("task_id")
        if not task_id:
            raise RuntimeError(json.dumps(response, ensure_ascii=False))
        state = {
            "task_id": task_id,
            "task_status": output.get("task_status", "PENDING"),
            "submitted_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "model": shot["model"],
            "duration": shot["parameters"]["duration"],
        }
        write_json(task_state_path, state)
        set_manifest_status(manifest_path, shot_number, state["task_status"], task_id=task_id)
        print(f"[SUBMITTED] shot {shot_number}: task saved", flush=True)
    else:
        print(f"[RESUME] shot {shot_number}: polling saved task", flush=True)

    started = time.monotonic()
    status = str(state.get("task_status", "PENDING"))
    while status not in TERMINAL_STATUSES:
        if time.monotonic() - started > timeout:
            raise TimeoutError(f"shot {shot_number}: polling timed out; rerun to resume")
        time.sleep(poll_interval)
        response = request_json(f"{base_url}/api/v1/tasks/{task_id}", api_key)
        write_json(response_path, response)
        output = response.get("output", {})
        status = str(output.get("task_status", "UNKNOWN"))
        state["task_status"] = status
        state["last_polled_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        error_code = response.get("code") or output.get("code")
        error_message = response.get("message") or output.get("message")
        if error_code or error_message:
            state["error"] = {
                "code": error_code,
                "message": error_message,
            }
        write_json(task_state_path, state)
        set_manifest_status(manifest_path, shot_number, status, task_id=task_id)
        print(f"[POLL] shot {shot_number}: {status}", flush=True)

    if status != "SUCCEEDED":
        error = {
            "shot": shot_number,
            "status": status,
            "code": response.get("code") or response.get("output", {}).get("code"),
            "message": response.get("message") or response.get("output", {}).get("message"),
        }
        return error

    video_url = response.get("output", {}).get("video_url")
    if not video_url:
        raise RuntimeError(f"shot {shot_number}: SUCCEEDED without video_url")
    download_file(video_url, output_path)
    state["downloaded_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    state["output_file"] = str(output_path)
    write_json(task_state_path, state)
    set_manifest_status(
        manifest_path,
        shot_number,
        "SUCCEEDED",
        task_id=task_id,
        output_file=str(output_path),
    )
    print(f"[DOWNLOADED] shot {shot_number}: {output_path}", flush=True)
    return {"shot": shot_number, "status": "SUCCEEDED", "file": str(output_path)}


def main() -> int:
    args = parse_args()
    manifest_path = args.manifest.resolve()
    manifest = read_json(manifest_path)
    if not manifest:
        raise SystemExit(f"Manifest not found or empty: {manifest_path}")

    project_root = Path(__file__).resolve().parent
    env = load_env(project_root / ".env")
    api_key = os.environ.get("DASHSCOPE_API_KEY") or env.get("DASHSCOPE_API_KEY", "")
    base_url = (
        os.environ.get("DASHSCOPE_BASE_URL")
        or env.get("DASHSCOPE_BASE_URL")
        or DEFAULT_BASE_URL
    ).rstrip("/")
    if not api_key:
        raise SystemExit("DASHSCOPE_API_KEY is missing")

    requested = None
    if args.shots:
        requested = {int(value.strip()) for value in args.shots.split(",") if value.strip()}
    shots = [
        shot for shot in manifest["shots"]
        if requested is None or int(shot["number"]) in requested
    ]
    if not shots:
        raise SystemExit("No shots selected")
    if args.regenerate and (requested is None or len(shots) != 1):
        raise SystemExit("--regenerate requires exactly one explicitly selected shot")

    print(
        f"[SAFE] selected={len(shots)} parallel={max(1, args.parallel)} "
        f"endpoint_region_hint={base_url.split('//', 1)[-1].split('/', 1)[0]}",
        flush=True,
    )

    results: list[dict[str, Any]] = []
    exit_code = 0
    with ThreadPoolExecutor(max_workers=max(1, args.parallel)) as executor:
        futures = {
            executor.submit(
                handle_shot,
                manifest_path,
                shot,
                api_key,
                base_url,
                args.poll_interval,
                args.timeout,
                args.dry_run,
                args.retry_failed,
                args.regenerate,
                args.max_quality_retries,
            ): int(shot["number"])
            for shot in shots
        }
        for future in as_completed(futures):
            shot_number = futures[future]
            try:
                result = future.result()
            except Exception as exc:  # Keep other independent shots running.
                result = {"shot": shot_number, "status": "ERROR", "message": str(exc)}
                exit_code = 1
            if result.get("status") not in {"SUCCEEDED", "ALREADY_DOWNLOADED", "DRY_RUN_OK"}:
                exit_code = 1
            results.append(result)

    results.sort(key=lambda item: int(item["shot"]))
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return exit_code


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Interrupted; rerun the same command to resume saved task IDs.", file=sys.stderr)
        raise SystemExit(130)
