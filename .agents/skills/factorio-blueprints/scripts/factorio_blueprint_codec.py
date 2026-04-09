from __future__ import annotations

import argparse
import base64
import json
import zlib
from pathlib import Path
from typing import Any


def encode_blueprint(payload: dict[str, Any], *, pretty: bool = False) -> str:
    separators = None if pretty else (",", ":")
    raw = json.dumps(payload, ensure_ascii=False, separators=separators).encode("utf-8")
    return "0" + base64.b64encode(zlib.compress(raw, level=9)).decode("ascii")


def decode_blueprint(text: str) -> dict[str, Any]:
    content = text.strip()
    if not content:
        raise ValueError("蓝图内容为空")

    if content[0] == "0":
        raw = zlib.decompress(base64.b64decode(content[1:]))
        return json.loads(raw.decode("utf-8"))

    return json.loads(content)


def _strip_json_comments(text: str) -> str:
    result: list[str] = []
    in_string = False
    escaped = False
    in_line_comment = False
    in_block_comment = False
    index = 0

    while index < len(text):
        char = text[index]
        next_char = text[index + 1] if index + 1 < len(text) else ""

        if in_line_comment:
            if char == "\n":
                in_line_comment = False
                result.append(char)
            index += 1
            continue

        if in_block_comment:
            if char == "*" and next_char == "/":
                in_block_comment = False
                index += 2
                continue
            index += 1
            continue

        if in_string:
            result.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
            continue

        if char == "/" and next_char == "/":
            in_line_comment = True
            index += 2
            continue

        if char == "/" and next_char == "*":
            in_block_comment = True
            index += 2
            continue

        result.append(char)
        if char == '"':
            in_string = True
        index += 1

    return "".join(result)


def _strip_trailing_commas(text: str) -> str:
    result: list[str] = []
    in_string = False
    escaped = False
    index = 0

    while index < len(text):
        char = text[index]

        if in_string:
            result.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
            continue

        if char == '"':
            in_string = True
            result.append(char)
            index += 1
            continue

        if char == ",":
            lookahead = index + 1
            while lookahead < len(text) and text[lookahead] in " \t\r\n":
                lookahead += 1
            if lookahead < len(text) and text[lookahead] in "}]":
                index += 1
                continue

        result.append(char)
        index += 1

    return "".join(result)


def load_json_document(path: Path) -> Any:
    content = path.read_text(encoding="utf-8-sig")
    if path.suffix.lower() == ".jsonc":
        content = _strip_json_comments(content)
        content = _strip_trailing_commas(content)
    return json.loads(content)


def strip_build_metadata(payload: Any) -> Any:
    if not isinstance(payload, dict):
        return payload
    if "_build" not in payload:
        return payload

    normalized = dict(payload)
    normalized.pop("_build", None)
    return normalized


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Factorio 蓝图字符串编解码工具")
    subparsers = parser.add_subparsers(dest="command", required=True)

    decode_parser = subparsers.add_parser("decode", help="把蓝图字符串解码为 JSON")
    decode_parser.add_argument("input", type=Path, help="输入蓝图字符串文件")
    decode_parser.add_argument("output", type=Path, nargs="?", help="输出 JSON 文件，可省略")
    decode_parser.add_argument("--pretty", action="store_true", help="美化 JSON 输出")

    encode_parser = subparsers.add_parser("encode", help="把 JSON 编码为蓝图字符串")
    encode_parser.add_argument("input", type=Path, help="输入 JSON 文件")
    encode_parser.add_argument("output", type=Path, nargs="?", help="输出蓝图字符串文件，可省略")

    return parser.parse_args()


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)


def resolve_path(path: Path) -> Path:
    if path.exists():
        return path

    matches = sorted(Path.cwd().glob(str(path)))
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise FileNotFoundError(f"路径未唯一匹配，请改用更精确的模式：{path}")
    raise FileNotFoundError(f"找不到文件：{path}")


def main() -> None:
    args = _parse_args()

    if args.command == "decode":
        input_path = resolve_path(args.input)
        payload = decode_blueprint(input_path.read_text(encoding="utf-8"))
        indent = 2 if args.pretty else None
        separators = None if args.pretty else (",", ":")
        result = json.dumps(payload, ensure_ascii=False, indent=indent, separators=separators)
        if args.output:
            write_text(args.output, result + "\n")
            return
        print(result)
        return

    input_path = resolve_path(args.input)
    payload = strip_build_metadata(load_json_document(input_path))
    result = encode_blueprint(payload)
    if args.output:
        write_text(args.output, result + "\n")
        return
    print(result)


if __name__ == "__main__":
    main()
