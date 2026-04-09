---
name: factorio-blueprints
description: 在本项目中创建、修改、解码、重建和排查 Factorio 蓝图。用于处理 blueprints 目录内的蓝图字符串、组合器/连线/显示器逻辑、阈值锁存与配方选择问题，以及维护与蓝图相关的项目文档和脚本。
---

# Factorio Blueprints

## Overview

使用这个 skill 维护本项目里的 Factorio 蓝图工作流。把当前 skill 目录下的 `scripts/` 视为脚本源码。

## Workflow

1. 先读现有文档，再改蓝图。
2. 优先修改本 skill 自带的脚本，再通过脚本重建成品蓝图。
3. 每次查到新的 wiki / API 信息，都同步更新项目文档。
4. 每次改动蓝图逻辑、接线方式或使用方法，都同步更新对应蓝图目录下的说明文档。

## Read First

按需先读这些文件：

- 项目级 wiki / API 复查笔记：
  [factorio-wiki-notes.md](../../../docs/factorio-wiki-notes.md)
- 具体蓝图的使用说明：
  `blueprints/<蓝图名>/README.md`
- 具体蓝图的设计说明：
  `blueprints/<蓝图名>/设计与维护.md`

如果这次查询到了新的外部信息：

- 先把结论压缩成可复查的短笔记
- 写入 [factorio-wiki-notes.md](../../../docs/factorio-wiki-notes.md)
- 不要只把结论留在对话里

## Script Source Of Truth

核心脚本在这里：

- [build_blueprint.py](scripts/build_blueprint.py)
- [factorio_blueprint_builders.py](scripts/factorio_blueprint_builders.py)
- [factorio_blueprint_codec.py](scripts/factorio_blueprint_codec.py)

修改逻辑时：

- 通用构建、发现、编解码逻辑改 `.agents/skills/factorio-blueprints/scripts/`
- 优先把具体蓝图真源放在 `blueprints/<蓝图名>/蓝图.json` 或 `blueprints/<蓝图名>/蓝图.jsonc`
- 只有确实需要脚本生成时，才使用 `blueprints/<蓝图名>/builder.py`
- 不要把具体蓝图逻辑继续塞回通用脚本
- 不要在仓库其他位置复制同名脚本

## Commands

列出已登记蓝图：

```powershell
python .agents/skills/factorio-blueprints/scripts/build_blueprint.py list
```

重建某个蓝图：

```powershell
python .agents/skills/factorio-blueprints/scripts/build_blueprint.py build recipe-signal-switch
```

解码蓝图字符串：

```powershell
python .agents/skills/factorio-blueprints/scripts/factorio_blueprint_codec.py decode "blueprints/配方信号阈值锁存开关/蓝图.txt" --pretty
```

## Update Rules

新增或修改蓝图时，保持这些约定：

- 成品蓝图放在 `blueprints/<蓝图名>/蓝图.txt`
- 蓝图真源优先放在 `blueprints/<蓝图名>/蓝图.json` 或 `blueprints/<蓝图名>/蓝图.jsonc`
- 使用说明放在 `blueprints/<蓝图名>/README.md`
- 设计说明放在 `blueprints/<蓝图名>/设计与维护.md`
- 只有需要脚本生成时，蓝图构建定义才放在 `blueprints/<蓝图名>/builder.py`
- 外部资料结论放在 [factorio-wiki-notes.md](../../../docs/factorio-wiki-notes.md)

如果新增了新的可复用蓝图流程：

- 先补脚本
- 再补 skill 说明
- 最后补项目文档
