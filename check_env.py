#!/usr/bin/env python3
"""Check local DashScope configuration without calling any external service."""

from __future__ import annotations

from pathlib import Path
import sys


KEY_NAME = "DASHSCOPE_API_KEY"
BAD_QUOTE_CHARS = set("\"'“”‘’「」『』")
PLACEHOLDER_HINTS = (
    "your_api_key",
    "your-api-key",
    "api_key",
    "apikey",
    "placeholder",
    "replace",
    "example",
    "xxxx",
    "你的",
    "示例",
    "占位",
    "替换",
)


def mask_secret(value: str) -> str:
    if len(value) <= 6:
        return "*" * len(value)
    if len(value) <= 10:
        return f"{value[:2]}****{value[-2:]}"
    return f"{value[:3]}****{value[-4:]}"


def read_env_value(env_path: Path) -> tuple[list[str], str | None, int | None]:
    warnings: list[str] = []
    value: str | None = None
    value_line: int | None = None
    seen_count = 0

    for line_number, line in enumerate(env_path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        parse_line = line.lstrip()
        if parse_line.startswith("export "):
            parse_line = parse_line[len("export ") :].lstrip()
        if "=" not in parse_line:
            continue

        name_part, raw_value = parse_line.split("=", 1)
        name = name_part.strip()
        if name != KEY_NAME:
            continue

        seen_count += 1
        if name_part != KEY_NAME:
            warnings.append(f"第{line_number}行等号左侧有多余空格，请改为 {KEY_NAME}=...")

        value = raw_value
        value_line = line_number

    if seen_count > 1:
        warnings.append(f"发现{seen_count}个{KEY_NAME}，建议只保留一个。")

    return warnings, value, value_line


def find_format_issues(value: str, line_number: int) -> list[str]:
    issues: list[str] = []
    trimmed = value.strip()
    lower_value = trimmed.lower()

    if value != trimmed:
        issues.append(f"第{line_number}行API Key前后有空格，请删除。")
    if any(char in BAD_QUOTE_CHARS for char in trimmed):
        issues.append(f"第{line_number}行API Key不需要引号，请删除引号。")
    if any(char.isspace() for char in trimmed):
        issues.append(f"第{line_number}行API Key中包含空格或换行，请检查粘贴内容。")
    if any(hint in lower_value for hint in PLACEHOLDER_HINTS):
        issues.append(f"第{line_number}行看起来仍是占位符，请粘贴真实API Key。")

    return issues


def print_empty_key_help() -> None:
    print("[WARN] DASHSCOPE_API_KEY尚未填写")
    print()
    print("请打开项目根目录中的.env文件，")
    print("将API Key填写到下面这一行的等号后面：")
    print()
    print("DASHSCOPE_API_KEY=你的API_Key")


def main() -> int:
    project_root = Path(__file__).resolve().parent
    env_path = project_root / ".env"

    if not env_path.exists():
        print("[WARN] 未找到.env文件")
        print("请先在项目根目录创建.env，并填写DASHSCOPE_API_KEY。")
        print("本次仅检查本地配置，没有调用模型，也没有产生费用。")
        return 1

    print("[OK] 已找到.env文件")

    warnings, value, line_number = read_env_value(env_path)
    if value is None or line_number is None:
        print(f"[WARN] 未找到{KEY_NAME}")
        print(f"请在.env中添加一行：{KEY_NAME}=你的API_Key")
        print("本次仅检查本地配置，没有调用模型，也没有产生费用。")
        return 1

    if value.strip() == "":
        for warning in warnings:
            print(f"[WARN] {warning}")
        print_empty_key_help()
        print("本次仅检查本地配置，没有调用模型，也没有产生费用。")
        return 1

    issues = warnings + find_format_issues(value, line_number)
    safe_value = value.strip()

    print("[OK] DASHSCOPE_API_KEY已填写")
    print(f"[SAFE] 密钥长度：{len(safe_value)}字符")
    print(f"[SAFE] 密钥预览：{mask_secret(safe_value)}")

    if issues:
        for issue in issues:
            print(f"[WARN] {issue}")
        print("本次仅检查本地配置，没有调用模型，也没有产生费用。")
        return 1

    print("[OK] 配置格式正常")
    print("本次仅检查本地配置，没有调用模型，也没有产生费用。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
