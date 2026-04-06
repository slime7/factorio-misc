from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from factorio_blueprint_codec import encode_blueprint, write_text


BLUEPRINT_VERSION = 562949954076673
BLUEPRINT_FILE_NAME = "蓝图.txt"


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


def build_recipe_signal_switch() -> dict[str, Any]:
    always_true_condition = {
        "first_signal": signal("signal-1", "virtual"),
        "second_signal": signal("signal-1", "virtual"),
        "comparator": "=",
    }

    entities = [
        entity(
            1,
            "display-panel",
            0.5,
            -1,
            text="库存输入\n接当前库存信号",
            icon=signal("red-wire"),
            always_show=True,
            show_in_chart=True,
            control_behavior={
                "messages": [
                    {
                        "text": "库存输入",
                        "icon": signal("red-wire"),
                        "condition": always_true_condition,
                    }
                ]
            },
        ),
        entity(
            2,
            "constant-combinator",
            0.5,
            -3,
            control_behavior={"sections": {"sections": [{"index": 1}]}},
            player_description="低阈值。低于这个值才会启动该信号。",
        ),
        entity(
            3,
            "constant-combinator",
            0.5,
            -2,
            control_behavior={"sections": {"sections": [{"index": 1}]}},
            player_description="高阈值。锁存后会一直保持到库存达到这个值才释放。",
        ),
        entity(
            4,
            "arithmetic-combinator",
            2.5,
            -3,
            direction=4,
            control_behavior={
                "arithmetic_conditions": {
                    "first_signal": signal("signal-each", "virtual"),
                    "second_signal": signal("signal-each", "virtual"),
                    "operation": "-",
                    "output_signal": signal("signal-each", "virtual"),
                    "first_signal_networks": {"red": False, "green": True},
                    "second_signal_networks": {"red": True, "green": False},
                }
            },
            player_description="低阈值减当前库存，得到启动缺口。",
        ),
        entity(
            5,
            "decider-combinator",
            4.5,
            -3,
            direction=4,
            control_behavior={
                "decider_conditions": {
                    "conditions": [
                        {
                            "first_signal": signal("signal-each", "virtual"),
                            "comparator": ">",
                            "constant": 0,
                            "first_signal_networks": {"red": True, "green": False},
                        }
                    ],
                    "outputs": [
                        {
                            "signal": signal("signal-each", "virtual"),
                            "networks": {"red": True, "green": False},
                        }
                    ],
                }
            },
            player_description="只保留可启动的候选，并保留低阈值缺口大小。",
        ),
        entity(
            6,
            "arithmetic-combinator",
            2.5,
            -2,
            direction=4,
            control_behavior={
                "arithmetic_conditions": {
                    "first_signal": signal("signal-each", "virtual"),
                    "second_signal": signal("signal-each", "virtual"),
                    "operation": "-",
                    "output_signal": signal("signal-each", "virtual"),
                    "first_signal_networks": {"red": False, "green": True},
                    "second_signal_networks": {"red": True, "green": False},
                }
            },
            player_description="高阈值减当前库存。仍大于 0 说明还没到释放线。",
        ),
        entity(
            7,
            "decider-combinator",
            4.5,
            -2,
            direction=4,
            control_behavior={
                "decider_conditions": {
                    "conditions": [
                        {
                            "first_signal": signal("signal-each", "virtual"),
                            "comparator": ">",
                            "constant": 0,
                            "first_signal_networks": {"red": True, "green": False},
                        },
                        {
                            "first_signal": signal("signal-each", "virtual"),
                            "comparator": ">",
                            "constant": 0,
                            "first_signal_networks": {"red": False, "green": True},
                            "compare_type": "and",
                        }
                    ],
                    "outputs": [
                        {
                            "signal": signal("signal-each", "virtual"),
                            "constant": 1000000,
                            "copy_count_from_input": False,
                            "networks": {"red": False, "green": True},
                        }
                    ],
                }
            },
            player_description="若当前锁存目标还没到高阈值，则给它一个很高的保持优先级，防止中途切换。",
        ),
        entity(
            8,
            "selector-combinator",
            6.5,
            -3,
            direction=4,
            control_behavior={"operation": "select", "select_max": True, "index_constant": 0},
            player_description="从启动候选和保持优先级里只选一个最终目标。",
        ),
        entity(
            9,
            "decider-combinator",
            8.5,
            -3,
            direction=4,
            control_behavior={
                "decider_conditions": {
                    "conditions": [
                        {
                            "first_signal": signal("signal-each", "virtual"),
                            "comparator": ">",
                            "constant": 0,
                            "first_signal_networks": {"red": True, "green": False},
                        },
                    ],
                    "outputs": [
                        {
                            "signal": signal("signal-each", "virtual"),
                            "constant": 1,
                            "copy_count_from_input": False,
                        }
                    ],
                }
            },
            player_description="把选中的目标归一化为固定输出 each = 1，并作为锁存记忆反馈。",
        ),
        entity(
            10,
            "display-panel",
            12.5,
            -3,
            text="输出信号\n接后续转换或机器",
            icon=signal("green-wire"),
            always_show=True,
            show_in_chart=True,
            control_behavior={
                "messages": [
                    {
                        "text": "输出信号",
                        "icon": signal("green-wire"),
                        "condition": always_true_condition,
                    }
                ]
            },
        ),
    ]

    wires = [
        [1, 1, 4, 1],
        [1, 1, 6, 1],
        [2, 2, 4, 2],
        [3, 2, 6, 2],
        [4, 3, 5, 1],
        [5, 3, 8, 1],
        [6, 4, 7, 2],
        [7, 4, 8, 2],
        [8, 3, 9, 1],
        [9, 3, 7, 1],
        [9, 3, 10, 1],
    ]

    description = "\n".join(
        [
            "用途：按库存信号自动选择一个输出信号，并用低阈值启动、高阈值释放的方式保持稳定。",
            "接线：左侧显示器接当前库存信号，右侧显示器接后续转换逻辑或生产设备。",
            "配置：左上常量组合器填低阈值，左下常量组合器填高阈值，信号名就是最终输出的信号名。",
            "策略：只输出一个候选，默认选低阈值缺口最大的那个；锁存后直到高阈值满足才释放。",
            "注意：该蓝图不做配方信号映射，只锁存并输出被选中的原始信号。",
        ]
    )

    return {
        "blueprint": {
            "item": "blueprint",
            "label": "配方信号阈值锁存开关",
            "description": description,
            "icons": [
                {"signal": signal("display-panel"), "index": 1},
                {"signal": signal("selector-combinator"), "index": 2},
            ],
            "entities": entities,
            "wires": wires,
            "version": BLUEPRINT_VERSION,
        }
    }


BUILDERS = {
    "recipe-signal-switch": BlueprintBuilder(
        name="recipe-signal-switch",
        output=BLUEPRINTS_DIR / "配方信号阈值锁存开关" / BLUEPRINT_FILE_NAME,
        summary="库存驱动的单输出阈值锁存开关，低阈值启动，高阈值释放。",
        build=build_recipe_signal_switch,
    )
}


def list_builders() -> list[BlueprintBuilder]:
    return [BUILDERS[name] for name in sorted(BUILDERS)]


def get_builder(name: str) -> BlueprintBuilder:
    try:
        return BUILDERS[name]
    except KeyError as error:
        known = ", ".join(sorted(BUILDERS))
        raise KeyError(f"未知蓝图构建名：{name}。可用项：{known}") from error


def build_named_blueprint(name: str, output_path: Path | None = None) -> Path:
    builder = get_builder(name)
    payload = builder.build()
    return write_blueprint_file(payload, output_path or builder.output)
