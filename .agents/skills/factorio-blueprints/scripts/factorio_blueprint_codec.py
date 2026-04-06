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
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    result = encode_blueprint(payload)
    if args.output:
        write_text(args.output, result + "\n")
        return
    print(result)


if __name__ == "__main__":
    main()
