#!/usr/bin/env python3
"""项目信息与推送守护辅助脚本。

维护 .push-guard-state.json 状态文件，并提供：
- init         初始化/补全状态文件
- set          写入字段
- get          读取字段（密码脱敏）
- bump-version 版本号 +0.1
- missing      检查 session / push 场景下缺失的字段
- show         查看完整状态（密码脱敏）
"""

import argparse
import json
import sys
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

DEFAULT_STATE = ".push-guard-state.json"

DEFAULTS = {
    "project_name": "",
    "project_author": "",
    "project_description": "",
    "project_name_en": "",
    "body_username": "",
    "body_password": "",
    "push_path": "",
    "version": "0.0",
}

SESSION_KEYS = ["project_name", "project_author", "project_description"]
PUSH_KEYS = ["body_username", "body_password", "push_path", "project_name_en"]
VALID_KEYS = set(DEFAULTS)

SECRET_KEYS = {"body_password"}


def state_path_or_default(path: str | None) -> str:
    return path or DEFAULT_STATE


def load_state(path: str) -> dict:
    state_file = Path(path)
    if state_file.exists():
        try:
            with state_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            print(f"错误：状态文件读取失败：{exc}", file=sys.stderr)
            sys.exit(1)
        if not isinstance(data, dict):
            print("错误：状态文件内容必须是 JSON 对象。", file=sys.stderr)
            sys.exit(1)
    else:
        data = {}

    for key, value in DEFAULTS.items():
        data.setdefault(key, value)
    return data


def save_state(path: str, data: dict) -> None:
    state_file = Path(path)
    state_file.parent.mkdir(parents=True, exist_ok=True)
    with state_file.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def mask_value(key: str, value: str) -> str:
    if key in SECRET_KEYS and value:
        return "******"
    return value


def cmd_init(args) -> int:
    path = state_path_or_default(args.state)
    data = load_state(path)
    save_state(path, data)
    print(f"状态文件已就绪：{path}")
    return 0


def cmd_set(args) -> int:
    key = args.key
    if key not in VALID_KEYS:
        print(f"错误：未知字段 {key}。可选字段：{', '.join(sorted(VALID_KEYS))}", file=sys.stderr)
        return 1

    path = state_path_or_default(args.state)
    data = load_state(path)
    data[key] = args.value
    save_state(path, data)

    if key in SECRET_KEYS:
        print(f"已写入 {key}=****** -> {path}")
    else:
        print(f"已写入 {key}={args.value!r} -> {path}")
    return 0


def cmd_get(args) -> int:
    key = args.key
    if key not in VALID_KEYS:
        print(f"错误：未知字段 {key}。可选字段：{', '.join(sorted(VALID_KEYS))}", file=sys.stderr)
        return 1

    path = state_path_or_default(args.state)
    data = load_state(path)
    print(mask_value(key, str(data.get(key, ""))))
    return 0


def bump_version(raw: str) -> str:
    value = (raw or "").strip()
    if not value:
        value = "0.0"
    try:
        current = Decimal(value)
    except InvalidOperation:
        print(f"警告：当前版本号 {value!r} 不是有效数字，按 0.0 处理。", file=sys.stderr)
        current = Decimal("0.0")

    new_value = (current + Decimal("0.1")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    return str(new_value)


def cmd_bump_version(args) -> int:
    path = state_path_or_default(args.state)
    data = load_state(path)

    old = str(data.get("version", "0.0") or "0.0")
    new = bump_version(old)
    data["version"] = new
    save_state(path, data)
    print(new)
    return 0


def cmd_missing(args) -> int:
    scope = args.scope
    if scope == "session":
        keys = SESSION_KEYS
    elif scope == "push":
        keys = PUSH_KEYS
    else:
        print("错误：--scope 只能是 session 或 push。", file=sys.stderr)
        return 1

    path = state_path_or_default(args.state)
    data = load_state(path)
    missing = [key for key in keys if not str(data.get(key, "")).strip()]
    print(json.dumps(missing, ensure_ascii=False))
    return 0


def cmd_show(args) -> int:
    path = state_path_or_default(args.state)
    data = load_state(path)
    masked = {key: mask_value(key, str(value)) for key, value in data.items()}
    print(json.dumps(masked, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    def add_state(p):
        p.add_argument("--state", default=DEFAULT_STATE, help="状态文件路径，默认 .push-guard-state.json")

    p_init = sub.add_parser("init", help="初始化/补全状态文件")
    add_state(p_init)
    p_init.set_defaults(func=cmd_init)

    p_set = sub.add_parser("set", help="写入字段")
    add_state(p_set)
    p_set.add_argument("--key", required=True, help="字段名")
    p_set.add_argument("--value", required=True, help="字段值")
    p_set.set_defaults(func=cmd_set)

    p_get = sub.add_parser("get", help="读取字段")
    add_state(p_get)
    p_get.add_argument("--key", required=True, help="字段名")
    p_get.set_defaults(func=cmd_get)

    p_bump = sub.add_parser("bump-version", help="版本号 +0.1")
    add_state(p_bump)
    p_bump.set_defaults(func=cmd_bump_version)

    p_missing = sub.add_parser("missing", help="检查缺失字段")
    add_state(p_missing)
    p_missing.add_argument("--scope", required=True, choices=["session", "push"], help="session 或 push")
    p_missing.set_defaults(func=cmd_missing)

    p_show = sub.add_parser("show", help="查看完整状态（密码脱敏）")
    add_state(p_show)
    p_show.set_defaults(func=cmd_show)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
