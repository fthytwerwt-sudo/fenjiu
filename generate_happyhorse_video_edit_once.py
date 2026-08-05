#!/usr/bin/env python3
"""Submit one non-retry HappyHorse video-edit batch and download results.

This script is intentionally separate from ``generate_happyhorse_shots.py``:
the benchmark-remake tasks allow a formal non-retry generation batch only.
It can resume/poll existing task IDs, but it never archives and resubmits a
failed or low-quality result.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any


DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com"
CREATE_PATH = "/api/v1/services/aigc/video-generation/video-synthesis"
UPLOAD_PATH = "/api/v1/uploads"
MODEL = "happyhorse-1.0-video-edit"
TERMINAL_STATUSES = {"SUCCEEDED", "FAILED", "CANCELED", "UNKNOWN"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--submit", action="store_true", help="Create tasks. Omit for dry-run only.")
    parser.add_argument("--poll-interval", type=int, default=15)
    parser.add_argument("--timeout", type=int, default=1800)
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
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key.strip()] = value
    return values


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_path(manifest_dir: Path, value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = manifest_dir / path
    return path.resolve()


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
        "User-Agent": "fenjiu-nepal-video-edit/1.0",
    }
    if method == "POST":
        headers["X-DashScope-Async"] = "enable"
        headers["X-DashScope-OssResourceResolve"] = "enable"
    for attempt in range(3):
        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(
                request,
                timeout=120,
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
    raise RuntimeError("unreachable request retry state")


def get_upload_policy(base_url: str, api_key: str, model: str) -> dict[str, Any]:
    query = urllib.parse.urlencode({"action": "getPolicy", "model": model})
    return request_json(f"{base_url}{UPLOAD_PATH}?{query}", api_key, method="GET")


def extract_upload_fields(policy_response: dict[str, Any]) -> tuple[str, dict[str, str], str]:
    output = policy_response.get("output") or policy_response
    upload_url = output.get("upload_url") or output.get("url") or output.get("host")
    upload_body = output.get("upload_body") or output.get("form_data") or output.get("fields")
    uploaded_url = output.get("uploaded_url") or output.get("file_url") or output.get("oss_url")
    if not upload_url or not isinstance(upload_body, dict) or not uploaded_url:
        raise RuntimeError(f"Unexpected upload policy response: {json.dumps(policy_response, ensure_ascii=False)}")
    return str(upload_url), {str(k): str(v) for k, v in upload_body.items()}, str(uploaded_url)


def upload_file(base_url: str, api_key: str, model: str, path: Path) -> str:
    policy = get_upload_policy(base_url, api_key, model)
    mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    if isinstance(policy.get("data"), dict) and policy["data"].get("upload_dir"):
        data = policy["data"]
        key = f"{data['upload_dir']}/{path.name}"
        upload_url = str(data["upload_host"])
        fields = [
            ("OSSAccessKeyId", str(data["oss_access_key_id"])),
            ("Signature", str(data["signature"])),
            ("policy", str(data["policy"])),
            ("x-oss-object-acl", str(data["x_oss_object_acl"])),
            ("x-oss-forbid-overwrite", str(data["x_oss_forbid_overwrite"])),
            ("key", key),
            ("success_action_status", "200"),
        ]
        uploaded_url = f"oss://{key}"
    else:
        upload_url, raw_fields, uploaded_url = extract_upload_fields(policy)
        fields = [(key, value) for key, value in raw_fields.items()]
    upload_multipart(upload_url, fields, path, mime_type)
    return uploaded_url


def upload_multipart(
    upload_url: str,
    fields: list[tuple[str, str]],
    path: Path,
    mime_type: str,
) -> None:
    boundary = f"----fenjiu-nepal-{uuid.uuid4().hex}"
    chunks: list[bytes] = []
    for key, value in fields:
        chunks.append(f"--{boundary}\r\n".encode("utf-8"))
        chunks.append(
            f'Content-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'.encode("utf-8")
        )
    chunks.append(f"--{boundary}\r\n".encode("utf-8"))
    chunks.append(
        (
            f'Content-Disposition: form-data; name="file"; filename="{path.name}"\r\n'
            f"Content-Type: {mime_type}\r\n\r\n"
        ).encode("utf-8")
    )
    chunks.append(path.read_bytes())
    chunks.append(b"\r\n")
    chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
    body = b"".join(chunks)
    request = urllib.request.Request(
        upload_url,
        data=body,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Content-Length": str(len(body)),
            "User-Agent": "fenjiu-nepal-video-edit/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(
            request,
            timeout=240,
            context=ssl.create_default_context(),
        ) as response:
            if response.status not in {200, 201, 204}:
                payload = response.read().decode("utf-8", errors="replace")
                raise RuntimeError(f"upload failed for {path.name}: HTTP {response.status} {payload[:1000]}")
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"upload failed for {path.name}: HTTP {exc.code} {payload[:1000]}") from exc


def validate_chunk(manifest_dir: Path, chunk: dict[str, Any]) -> None:
    if chunk.get("model") != MODEL:
        raise ValueError(f"chunk {chunk.get('number')}: model must be {MODEL}")
    parameters = chunk.get("parameters", {})
    if parameters.get("resolution") != "1080P":
        raise ValueError(f"chunk {chunk.get('number')}: resolution must be 1080P")
    if parameters.get("watermark") is not False:
        raise ValueError(f"chunk {chunk.get('number')}: watermark must be false")
    if parameters.get("audio_setting") not in {"auto", "origin"}:
        raise ValueError(f"chunk {chunk.get('number')}: audio_setting must be auto or origin")
    duration = float(chunk.get("duration", 0))
    if duration < 3 or duration > 15:
        raise ValueError(f"chunk {chunk.get('number')}: input duration must be 3-15 seconds")
    video_path = resolve_path(manifest_dir, chunk["video_path"])
    if not video_path.is_file():
        raise ValueError(f"chunk {chunk.get('number')}: video not found: {video_path}")
    for image in chunk.get("reference_images", []):
        image_path = resolve_path(manifest_dir, image["path"])
        if not image_path.is_file():
            raise ValueError(f"chunk {chunk.get('number')}: reference image not found: {image_path}")


def safe_payload_record(chunk: dict[str, Any], video_url: str, image_urls: list[str]) -> dict[str, Any]:
    media = [{"type": "video", "url": video_url}]
    media.extend({"type": "reference_image", "url": image_url} for image_url in image_urls)
    return {
        "model": chunk["model"],
        "input": {
            "prompt": chunk["prompt"],
            "media": media,
        },
        "parameters": chunk["parameters"],
    }


def create_payload(chunk: dict[str, Any], video_url: str, image_urls: list[str]) -> dict[str, Any]:
    return safe_payload_record(chunk, video_url, image_urls)


def download_file(url: str, destination: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "fenjiu-nepal-video-edit/1.0"})
    temporary = destination.with_suffix(destination.suffix + ".part")
    with urllib.request.urlopen(request, timeout=240) as response, temporary.open("wb") as output:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            output.write(chunk)
    if temporary.stat().st_size == 0:
        temporary.unlink(missing_ok=True)
        raise RuntimeError("downloaded file is empty")
    temporary.replace(destination)


def handle_chunk(
    manifest_path: Path,
    chunk: dict[str, Any],
    api_key: str,
    base_url: str,
    submit: bool,
    poll_interval: int,
    timeout: int,
) -> dict[str, Any]:
    manifest_dir = manifest_path.parent
    number = int(chunk["number"])
    label = f"chunk_{number:02d}"
    task_dir = manifest_dir / "06_tasks" / label
    state_path = task_dir / "state.json"
    response_path = task_dir / "latest_response.json"
    request_path = task_dir / "request.json"
    upload_path = task_dir / "uploaded_inputs.json"
    output_path = manifest_dir / "07_raw_generations" / f"{label}.mp4"

    validate_chunk(manifest_dir, chunk)
    if output_path.is_file() and output_path.stat().st_size > 0:
        return {"chunk": number, "status": "ALREADY_DOWNLOADED", "file": str(output_path)}

    state = read_json(state_path)
    uploads = read_json(upload_path)
    if state.get("task_id") and state.get("task_status") in TERMINAL_STATUSES and state.get("task_status") != "SUCCEEDED":
        raise RuntimeError(f"chunk {number}: terminal {state.get('task_status')} saved; single-use mode forbids retry")

    if not submit:
        return {
            "chunk": number,
            "status": "DRY_RUN_OK",
            "duration": chunk["duration"],
            "video_path": str(resolve_path(manifest_dir, chunk["video_path"])),
        }

    if not uploads:
        video_url = upload_file(base_url, api_key, MODEL, resolve_path(manifest_dir, chunk["video_path"]))
        image_urls = [
            upload_file(base_url, api_key, MODEL, resolve_path(manifest_dir, image["path"]))
            for image in chunk.get("reference_images", [])
        ][:5]
        uploads = {
            "video_url": video_url,
            "image_urls": image_urls,
            "uploaded_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        }
        write_json(upload_path, uploads)

    payload = create_payload(chunk, uploads["video_url"], uploads.get("image_urls", []))
    write_json(request_path, safe_payload_record(chunk, uploads["video_url"], uploads.get("image_urls", [])))

    task_id = state.get("task_id")
    response = read_json(response_path)
    if not task_id:
        response = request_json(base_url + CREATE_PATH, api_key, method="POST", payload=payload)
        write_json(response_path, response)
        output = response.get("output", {})
        task_id = output.get("task_id")
        if not task_id:
            raise RuntimeError(json.dumps(response, ensure_ascii=False))
        state = {
            "task_id": task_id,
            "task_status": output.get("task_status", "PENDING"),
            "submitted_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "model": MODEL,
            "duration": chunk["duration"],
            "single_generation_batch": True,
        }
        write_json(state_path, state)
        print(f"[SUBMITTED] chunk {number}: task saved", flush=True)
    else:
        print(f"[RESUME] chunk {number}: polling saved task", flush=True)

    started = time.monotonic()
    status = str(state.get("task_status", "PENDING"))
    while status not in TERMINAL_STATUSES:
        if time.monotonic() - started > timeout:
            raise TimeoutError(f"chunk {number}: polling timed out; rerun to resume")
        time.sleep(poll_interval)
        response = request_json(f"{base_url}/api/v1/tasks/{task_id}", api_key)
        write_json(response_path, response)
        output = response.get("output", {})
        status = str(output.get("task_status", "UNKNOWN"))
        state["task_status"] = status
        state["last_polled_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        if response.get("code") or output.get("code"):
            state["error"] = {
                "code": response.get("code") or output.get("code"),
                "message": response.get("message") or output.get("message"),
            }
        write_json(state_path, state)
        print(f"[POLL] chunk {number}: {status}", flush=True)

    if status != "SUCCEEDED":
        return {
            "chunk": number,
            "status": status,
            "code": response.get("code") or response.get("output", {}).get("code"),
            "message": response.get("message") or response.get("output", {}).get("message"),
        }

    video_url = response.get("output", {}).get("video_url")
    if not video_url:
        raise RuntimeError(f"chunk {number}: SUCCEEDED without video_url")
    download_file(video_url, output_path)
    state["downloaded_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    state["output_file"] = str(output_path)
    write_json(state_path, state)
    print(f"[DOWNLOADED] chunk {number}: {output_path}", flush=True)
    return {"chunk": number, "status": "SUCCEEDED", "file": str(output_path)}


def main() -> int:
    args = parse_args()
    manifest_path = args.manifest.resolve()
    manifest = read_json(manifest_path)
    if not manifest:
        raise SystemExit(f"Manifest not found or empty: {manifest_path}")
    if manifest.get("generation_policy") != "single_batch_no_retry":
        raise SystemExit("Manifest must declare generation_policy=single_batch_no_retry")

    project_root = Path(__file__).resolve().parent
    env = load_env(project_root / ".env")
    api_key = os.environ.get("DASHSCOPE_API_KEY") or env.get("DASHSCOPE_API_KEY", "")
    if not api_key:
        raise SystemExit("DASHSCOPE_API_KEY is missing")
    base_url = (
        os.environ.get("DASHSCOPE_VIDEO_EDIT_BASE_URL")
        or env.get("DASHSCOPE_VIDEO_EDIT_BASE_URL")
        or os.environ.get("DASHSCOPE_BASE_URL")
        or env.get("DASHSCOPE_BASE_URL")
        or DEFAULT_BASE_URL
    ).rstrip("/")

    chunks = manifest.get("chunks", [])
    if not chunks:
        raise SystemExit("No chunks in manifest")

    print(
        f"[SAFE] mode={'SUBMIT' if args.submit else 'DRY_RUN'} chunks={len(chunks)} "
        f"single_batch_no_retry=true endpoint={base_url.split('//', 1)[-1].split('/', 1)[0]}",
        flush=True,
    )
    results: list[dict[str, Any]] = []
    exit_code = 0
    for chunk in chunks:
        try:
            result = handle_chunk(
                manifest_path,
                chunk,
                api_key,
                base_url,
                args.submit,
                args.poll_interval,
                args.timeout,
            )
        except Exception as exc:
            result = {"chunk": int(chunk.get("number", 0)), "status": "ERROR", "message": str(exc)}
            exit_code = 1
        if result.get("status") not in {"SUCCEEDED", "ALREADY_DOWNLOADED", "DRY_RUN_OK"}:
            exit_code = 1
        results.append(result)
        if exit_code and args.submit:
            break
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return exit_code


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Interrupted; rerun the same command to resume saved task IDs.", file=sys.stderr)
        raise SystemExit(130)
