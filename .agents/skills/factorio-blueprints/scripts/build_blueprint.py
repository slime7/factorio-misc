from __future__ import annotations

import argparse
from pathlib import Path

from factorio_blueprint_builders import build_named_blueprint, get_builder, list_builders


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="构建仓库内登记的 Factorio 蓝图")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="列出可构建的蓝图")

    build_parser = subparsers.add_parser("build", help="构建一个已登记蓝图")
    build_parser.add_argument("name", help="蓝图构建名，可先用 list 查看")
    build_parser.add_argument("--output", type=Path, help="覆盖默认输出路径")

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.command == "list":
        for builder in list_builders():
            print(f"{builder.name}\t{builder.output}\t{builder.summary}")
        return

    builder = get_builder(args.name)
    output_path = build_named_blueprint(builder.name, args.output)
    print(f"已生成 {builder.name}: {output_path}")


if __name__ == "__main__":
    main()
