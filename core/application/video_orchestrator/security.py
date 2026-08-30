"""Fail-closed path, URL, endpoint, and media-transfer validation."""

from __future__ import annotations

import ipaddress
from pathlib import Path
import socket
from typing import Callable, Any
from urllib.parse import urlparse

from core.application.video_orchestrator.contracts import ErrorCode, ProviderAdapterError


_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
_VIDEO_SUFFIXES = {".mp4", ".mov", ".avi", ".webm"}
_AUDIO_SUFFIXES = {".wav", ".mp3", ".aac", ".m4a", ".flac", ".ogg", ".opus"}
_OUTPUT_SUFFIXES = {".mp4", ".mov", ".webm", ".mp3", ".wav", ".aac", ".flac", ".srt", ".json"}
_TRUSTED_OUTPUT_SUFFIXES = (".aliyuncs.com", ".alibabacloud.com")


def validate_remote_url(
    value: str,
    *,
    provider: str,
    trusted_output: bool = False,
    resolver: Callable[..., list[tuple[Any, ...]]] | None = None,
) -> str:
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ProviderAdapterError(ErrorCode.INVALID_INPUT, "only credential-free HTTPS URLs are allowed", provider=provider)
    host = parsed.hostname.lower().rstrip(".")
    if host == "localhost" or host.endswith((".localhost", ".local")):
        raise ProviderAdapterError(ErrorCode.PERMISSION_DENIED, "local or private URL is forbidden", provider=provider)
    if trusted_output and not any(host.endswith(suffix) for suffix in _TRUSTED_OUTPUT_SUFFIXES):
        raise ProviderAdapterError(ErrorCode.ASSET_ACCESS_FAILED, "provider output host is not allowlisted", provider=provider)
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address and _address_is_forbidden(address):
        raise ProviderAdapterError(ErrorCode.PERMISSION_DENIED, "local or private URL is forbidden", provider=provider)
    if address is None:
        try:
            resolved = (resolver or socket.getaddrinfo)(
                host,
                parsed.port or 443,
                type=socket.SOCK_STREAM,
            )
        except OSError as exc:
            raise ProviderAdapterError(
                ErrorCode.ASSET_ACCESS_FAILED,
                "remote URL host could not be resolved safely",
                provider=provider,
            ) from exc
        if not resolved:
            raise ProviderAdapterError(
                ErrorCode.ASSET_ACCESS_FAILED,
                "remote URL host returned no addresses",
                provider=provider,
            )
        for item in resolved:
            try:
                resolved_address = ipaddress.ip_address(item[4][0])
            except (IndexError, TypeError, ValueError) as exc:
                raise ProviderAdapterError(
                    ErrorCode.ASSET_ACCESS_FAILED,
                    "remote URL DNS response is invalid",
                    provider=provider,
                ) from exc
            if _address_is_forbidden(resolved_address):
                raise ProviderAdapterError(
                    ErrorCode.PERMISSION_DENIED,
                    "remote URL resolves to a local or private address",
                    provider=provider,
                )
    return value


def _address_is_forbidden(address: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    return (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_reserved
        or address.is_multicast
        or address.is_unspecified
    )


def endpoint_allowed(value: str, *, service: str) -> bool:
    if not value:
        return True
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        return False
    host = parsed.hostname.lower().rstrip(".")
    if service == "dashscope":
        return host == "dashscope.aliyuncs.com" or host.endswith(".maas.aliyuncs.com")
    if service == "aidge":
        return host == "aidge.cn-beijing.aliyuncs.com" or host.endswith(".aidge.aliyuncs.com")
    if service == "oss":
        return host.endswith(".aliyuncs.com")
    return False


def validate_local_product_image(value: str, *, provider: str) -> Path:
    return validate_local_media(value, provider=provider, asset_kind="image")


def validate_local_media(value: str, *, provider: str, asset_kind: str) -> Path:
    allowed_root = (Path.cwd() / "inputs" / "video_orchestrator").resolve()
    generated_root = (Path.cwd() / "outputs" / "video_orchestrator").resolve()
    raw_path = Path(value)
    if raw_path.is_symlink():
        raise ProviderAdapterError(ErrorCode.INVALID_INPUT, "local media symlinks are forbidden", provider=provider)
    path = raw_path.resolve()
    allowed_roots = (allowed_root,) if asset_kind == "image" else (allowed_root, generated_root)
    if not any(path != root and root in path.parents for root in allowed_roots):
        raise ProviderAdapterError(ErrorCode.PERMISSION_DENIED, "local asset is outside the allowlisted input root", provider=provider)
    suffixes = {"image": _IMAGE_SUFFIXES, "video": _VIDEO_SUFFIXES, "audio": _AUDIO_SUFFIXES}.get(asset_kind)
    limits = {"image": 20, "video": 300, "audio": 30}
    if suffixes is None or path.suffix.lower() not in suffixes:
        raise ProviderAdapterError(ErrorCode.INVALID_INPUT, "unsupported local media type", provider=provider)
    if not path.is_file():
        raise ProviderAdapterError(ErrorCode.INVALID_INPUT, "local media is missing or unsafe", provider=provider)
    if path.stat().st_size <= 0 or path.stat().st_size > limits[asset_kind] * 1024 * 1024:
        raise ProviderAdapterError(ErrorCode.INVALID_INPUT, "local media size is invalid", provider=provider)
    header = path.read_bytes()[:16]
    if asset_kind == "image":
        valid_signature = (
            header.startswith(b"\xff\xd8\xff")
            or header.startswith(b"\x89PNG\r\n\x1a\n")
            or (header.startswith(b"RIFF") and header[8:12] == b"WEBP")
            or header.startswith(b"BM")
        )
    elif asset_kind == "video":
        valid_signature = (len(header) >= 8 and header[4:8] == b"ftyp") or (
            header.startswith(b"RIFF") and header[8:12] == b"AVI "
        ) or header.startswith(b"\x1aE\xdf\xa3")
    else:
        valid_signature = (
            header.startswith(b"RIFF") and header[8:12] == b"WAVE"
        ) or header.startswith(b"ID3") or (
            len(header) >= 2 and header[0] == 0xFF and header[1] & 0xF0 == 0xF0
        ) or (len(header) >= 8 and header[4:8] == b"ftyp") or header.startswith(
            (b"fLaC", b"OggS")
        )
    if not valid_signature:
        raise ProviderAdapterError(ErrorCode.INVALID_INPUT, "local media signature is invalid", provider=provider)
    return path


def resolve_output_path(value: str, *, provider: str) -> Path:
    output_root = (Path.cwd() / "outputs" / "video_orchestrator").resolve()
    raw = Path(value)
    if raw.is_absolute():
        path = raw.resolve()
    elif raw.parts[:2] == ("outputs", "video_orchestrator"):
        path = (Path.cwd() / raw).resolve()
    else:
        path = (output_root / raw).resolve()
    if path == output_root or output_root not in path.parents:
        raise ProviderAdapterError(ErrorCode.PERMISSION_DENIED, "output path is outside the orchestrator output root", provider=provider)
    if path.suffix.lower() not in _OUTPUT_SUFFIXES:
        raise ProviderAdapterError(ErrorCode.INVALID_INPUT, "output file type is not allowed", provider=provider)
    return path
