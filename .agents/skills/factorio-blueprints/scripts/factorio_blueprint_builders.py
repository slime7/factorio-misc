from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import hashlib
import importlib.util
from pathlib import Path
import sys
from types import ModuleType
from typing import Any, Callable, Iterable

from factorio_blueprint_codec import encode_blueprint, load_json_document, strip_build_metadata, write_text


BLUEPRINT_VERSION = 562949954076673
BLUEPRINT_FILE_NAME = "蓝图.txt"
PYTHON_BUILDER_DEFINITION_FILE_NAME = "builder.py"
JSON_SOURCE_FILE_NAMES = ("蓝图.jsonc", "蓝图.json")
BUILD_METADATA_KEY = "_build"


def find_repo_root() -> Path:
    current = Path(__file__).resolve()
    for candidate in current.parents:
        if (
            (candidate / "blueprints").is_dir()
            and (candidate / ".agents" / "skills" / "factorio-blueprints").is_dir()
        ):
            return candidate
    raise FileNotFoundError(f"找不到仓库根目录：{current}")


ROOT = find_repo_root()
BLUEPRINTS_DIR = ROOT / "blueprints"


def signal(name: str, signal_type: str = "item") -> dict[str, str]:
    payload = {"name": name}
    if signal_type != "item":
        payload["type"] = signal_type
    return payload


def entity(
    entity_number: int,
    name: str,
    x: float,
    y: float,
    *,
    direction: int | None = None,
    control_behavior: dict[str, Any] | None = None,
    player_description: str | None = None,
    text: str | None = None,
    icon: dict[str, str] | None = None,
    always_show: bool | None = None,
    show_in_chart: bool | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "entity_number": entity_number,
        "name": name,
        "position": {"x": x, "y": y},
    }
    if direction is not None:
        payload["direction"] = direction
    if control_behavior is not None:
        payload["control_behavior"] = control_behavior
    if player_description:
        payload["player_description"] = player_description
    if text is not None:
        payload["text"] = text
    if icon is not None:
        payload["icon"] = icon
    if always_show is not None:
        payload["always_show"] = always_show
    if show_in_chart is not None:
        payload["show_in_chart"] = show_in_chart
    return payload


@dataclass(frozen=True)
class BlueprintBuilder:
    name: str
    output: Path
    summary: str
    build: Callable[[], dict[str, Any]]


def write_blueprint_file(payload: dict[str, Any], output_path: Path) -> Path:
    write_text(output_path, encode_blueprint(payload) + "\n")
    return output_path


def _blueprint_directories() -> list[Path]:
    return sorted(path for path in BLUEPRINTS_DIR.iterdir() if path.is_dir())


def _python_builder_path(blueprint_dir: Path) -> Path:
    return blueprint_dir / PYTHON_BUILDER_DEFINITION_FILE_NAME


def _json_source_paths(blueprint_dir: Path) -> list[Path]:
    return [blueprint_dir / file_name for file_name in JSON_SOURCE_FILE_NAMES if (blueprint_dir / file_name).is_file()]


def _load_builder_module(module_path: Path) -> ModuleType:
    digest = hashlib.sha1(str(module_path.resolve()).encode("utf-8")).hexdigest()
    module_name = f"_factorio_blueprint_builder_{digest}"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"无法加载蓝图定义文件：{module_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _iter_module_builders(module: ModuleType, module_path: Path) -> Iterable[BlueprintBuilder]:
    if not hasattr(module, "BUILDERS"):
        raise AttributeError(f"{module_path} 缺少 BUILDERS 定义")

    builders = getattr(module, "BUILDERS")
    try:
        items = list(builders)
    except TypeError as error:
        raise TypeError(f"{module_path} 的 BUILDERS 必须是可迭代对象") from error

    for item in items:
        if not isinstance(item, BlueprintBuilder):
            raise TypeError(f"{module_path} 的 BUILDERS 只能包含 BlueprintBuilder")
        yield item


def _load_json_source(source_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    document = load_json_document(source_path)
    if not isinstance(document, dict):
        raise TypeError(f"{source_path} 顶层必须是对象")

    metadata = document.get(BUILD_METADATA_KEY)
    if not isinstance(metadata, dict):
        raise KeyError(f"{source_path} 缺少 {BUILD_METADATA_KEY} 对象")

    payload = strip_build_metadata(document)
    if not payload:
        raise ValueError(f"{source_path} 缺少蓝图内容")
    return metadata, payload


def _json_source_builder(source_path: Path) -> BlueprintBuilder:
    metadata, payload = _load_json_source(source_path)
    name = metadata.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ValueError(f"{source_path} 的 {BUILD_METADATA_KEY}.name 必须是非空字符串")

    summary = metadata.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        blueprint = payload.get("blueprint")
        label = blueprint.get("label") if isinstance(blueprint, dict) else None
        summary = label if isinstance(label, str) and label.strip() else source_path.parent.name

    def build_from_json_source() -> dict[str, Any]:
        _, current_payload = _load_json_source(source_path)
        return current_payload

    return BlueprintBuilder(
        name=name,
        output=source_path.parent / BLUEPRINT_FILE_NAME,
        summary=summary,
        build=build_from_json_source,
    )


@lru_cache(maxsize=1)
def _builder_registry() -> dict[str, BlueprintBuilder]:
    registry: dict[str, BlueprintBuilder] = {}
    for blueprint_dir in _blueprint_directories():
        module_path = _python_builder_path(blueprint_dir)
        json_source_paths = _json_source_paths(blueprint_dir)

        if module_path.is_file() and json_source_paths:
            raise ValueError(f"{blueprint_dir} 同时存在 builder.py 和 蓝图.json/jsonc，请保留一种来源")
        if len(json_source_paths) > 1:
            joined = ", ".join(path.name for path in json_source_paths)
            raise ValueError(f"{blueprint_dir} 同时存在多个 JSON 来源：{joined}")

        builders: Iterable[BlueprintBuilder] = []
        if module_path.is_file():
            module = _load_builder_module(module_path)
            builders = _iter_module_builders(module, module_path)
        elif json_source_paths:
            builders = [_json_source_builder(json_source_paths[0])]

        for builder in builders:
            if builder.name in registry:
                raise KeyError(f"重复的蓝图构建名：{builder.name}")
            registry[builder.name] = builder
    return registry


def list_builders() -> list[BlueprintBuilder]:
    registry = _builder_registry()
    return [registry[name] for name in sorted(registry)]


def get_builder(name: str) -> BlueprintBuilder:
    registry = _builder_registry()
    try:
        return registry[name]
    except KeyError as error:
        known = ", ".join(sorted(registry))
        raise KeyError(f"未知蓝图构建名：{name}。可用项：{known}") from error


def build_named_blueprint(name: str, output_path: Path | None = None) -> Path:
    builder = get_builder(name)
    payload = builder.build()
    return write_blueprint_file(payload, output_path or builder.output)
